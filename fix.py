# PATH: fix.py
# PHASE C (Section 18.10 / 18.4): Client.nationalId becomes a true mandatory,
# unique-checked field, both at the DB column level and the service-validation
# level -- replacing the soft/optional column that the old guide incorrectly
# claimed was already enforced.
#
# Scope: Client.java, DataInitializer.java, ClientService.java. Nothing else.
# No intake UI changes (that's Phase D) and no changes to LandService.java --
# its two NIN_REQUIRED blank checks (atomicIntake, updateProjectFull) already
# route every owner through ClientService.findOrCreateClientByNin(), which
# already correctly implements the Section 17.3 duplicate-NIN behavior
# (block on same-NIN-different-name via NIN_NAME_MISMATCH, reuse-with-edit-
# allowed on same-NIN-same-name) -- that logic did not need fixing, it was
# only ever running against a column that could not actually back it up.
#
# WHAT WAS ACTUALLY BROKEN: DataInitializer already had an
# "ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id)"
# line under a PHASE 2 comment, and Client.java's javadoc already claimed
# "Unique at the DB level (see DataInitializer)". Both were aspirational, not
# real. Every migration statement in runSchemaMigrations() runs inside a
# blanket try/catch that logs ANY failure as "Skipped (already exists)" --
# so if that ADD CONSTRAINT ever failed for a real reason (duplicate NIN
# values already sitting in the table from before this was enforced, or
# blank-string NINs colliding with each other), it would fail silently on
# every single boot, forever, while the code and comments kept insisting the
# constraint existed. The Java entity did not even declare nullable=false,
# so nothing was mandatory at the column level either -- only the service
# layer (ClientService.findOrCreateClientByNin, LandService's two blank
# checks) was ever actually stopping a blank NIN, and only for the intake/
# edit code paths that route through it.
#
# THE FIX: DataInitializer now cleans the data BEFORE constraining it, so the
# constraint-creation step actually succeeds this time instead of silently
# failing again -- same "backfill guarded by IS NULL, safe to run every boot,
# no-op once already applied" pattern already used for the Phase A district/
# county backfill and the Phase B projectIndex backfill just above it in this
# same file:
#   1. Blank-string NINs ('') are normalized to real NULL first.
#   2. Any existing rows that already share a duplicate NIN (from back when
#      nothing stopped that) get every row after the first one disambiguated
#      with a "-DUPE-<id>" suffix, so the unique constraint has something
#      valid to apply to instead of failing on real collisions.
#   3. Legacy rows with NULL national_id (pre-Phase-2 clients "blank until
#      next edited," per the old Client.java comment) get backfilled with a
#      unique LEGACY-<id> placeholder, because a real NOT NULL constraint
#      cannot coexist with actual NULLs in the table.
#   4. Only THEN does "ALTER COLUMN national_id SET NOT NULL" run, followed
#      by the pre-existing ADD CONSTRAINT UNIQUE line (untouched) -- both of
#      which will now actually succeed and stay applied on every future boot.
# Client.java's @Column gets nullable = false, unique = true added, matching
# the exact precedent already used for LandProject/LandTitle.projectIndex
# (Hibernate's ddl-auto=update will attempt the same thing at startup before
# DataInitializer's CommandLineRunner runs; when the table isn't clean yet
# that attempt no-ops same as always, and DataInitializer's explicit
# raw-JDBC steps below are what actually land it).
#
# ClientService.findOrCreateClientByNin() itself is unchanged -- it already
# does the right thing. Only its javadoc is updated to note the constraint
# now genuinely exists underneath it, and the unused, dead
# findOrCreateClient(fullName, phone, email) legacy method (no callers
# anywhere in the codebase -- confirmed by search) gets a deprecation comment
# warning that calling it would now violate the NOT NULL constraint, since it
# never sets nationalId. It is not deleted (nothing calls it, no reason to
# risk touching more than necessary) and not rewired to require a NIN --
# that would just be turning it into a second copy of findOrCreateClientByNin,
# out of scope for this phase.

import os

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old not in content:
        print("MISSING: " + label + " (" + path + ")")
        return
    if content.count(old) > 1:
        print("MISSING: " + label + " -- old_str not unique in " + path)
        return
    content = content.replace(old, new)
    write_file(path, content)
    print("OK: " + label + " (" + path + ")")

CLIENT_MODEL = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/model/Client.java"
DATA_INIT = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"
CLIENT_SERVICE = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/service/ClientService.java"

# ─── 1. Client.java -- nationalId becomes a true mandatory, unique column ──

patch(
    CLIENT_MODEL,
    "    /**\n"
    "     * NATIONAL ID (NIN) -- THE REAL IDENTITY ANCHOR (Phase 2)\n"
    "     * Mandatory for every project owner going forward. Unique at the DB level\n"
    "     * (see DataInitializer). Legacy client rows created before Phase 2 may\n"
    "     * have this blank until next edited.\n"
    "     */\n"
    "    @Column(name = \"national_id\", length = 100)\n"
    "    private String nationalId;",

    "    /**\n"
    "     * NATIONAL ID (NIN) -- THE REAL IDENTITY ANCHOR\n"
    "     * PHASE C (Section 18.4/18.10): a true mandatory, unique-checked column,\n"
    "     * not a soft convention -- nullable = false, unique = true, matching the\n"
    "     * same pattern already used for LandProject/LandTitle.projectIndex.\n"
    "     * DataInitializer backfills any pre-existing NULL, blank, or duplicate\n"
    "     * values with unique placeholders before applying these constraints, so\n"
    "     * old legacy rows never block the migration on boot. Also enforced at\n"
    "     * the service level in ClientService.findOrCreateClientByNin().\n"
    "     */\n"
    "    @Column(name = \"national_id\", length = 100, nullable = false, unique = true)\n"
    "    private String nationalId;",

    "Client.nationalId -- nullable=false, unique=true + updated javadoc"
)

# ─── 2. DataInitializer.java -- clean the data, then actually constrain it ──

patch(
    DATA_INIT,
    "            // PHASE 2 - NIN-BASED IDENTITY\n"
    "            // Unique constraint on national_id. Postgres allows multiple NULLs under\n"
    "            // a UNIQUE constraint, so old clients with no NIN yet are not affected.\n"
    "            \"ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id)\",\n"
    "            // Phone numbers are no longer required to be unique -- joint owners or\n"
    "            // family members can share one phone. NIN is now the real identity check.\n"
    "            \"ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key\",\n",

    "            // PHASE 2 - NIN-BASED IDENTITY\n"
    "            // Phone numbers are no longer required to be unique -- joint owners or\n"
    "            // family members can share one phone. NIN is now the real identity check.\n"
    "            \"ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key\",\n"
    "\n"
    "            // PHASE C - FOLDER-TO-TITLE REDESIGN (Section 18.10 / 18.4)\n"
    "            // national_id becomes a TRUE mandatory, unique column. The old\n"
    "            // \"ADD CONSTRAINT UNIQUE\" line above this comment (removed) had been\n"
    "            // silently failing on every boot since Phase 2 -- the blanket\n"
    "            // try/catch below logs any failure as \"already exists\" whether that\n"
    "            // was true or not, and there was nothing upstream cleaning duplicate\n"
    "            // or blank values first. These four steps run in order, each one\n"
    "            // guarded so it is a no-op once already applied -- same repeatable,\n"
    "            // safe-on-every-boot pattern as the district/county and projectIndex\n"
    "            // backfills above.\n"
    "            //\n"
    "            // Step 1: blank-string NINs are not the same as a real NULL -- fold\n"
    "            // them in first so step 3 catches them too.\n"
    "            \"UPDATE clients SET national_id = NULL WHERE national_id = ''\",\n"
    "            //\n"
    "            // Step 2: disambiguate any rows that already share a duplicate NIN\n"
    "            // (possible from before this was ever enforced) -- keep the oldest\n"
    "            // row's value untouched, suffix every later duplicate with its own\n"
    "            // id so the unique constraint below has something valid to apply to.\n"
    "            // Naturally idempotent: once every value is distinct, ROW_NUMBER()\n"
    "            // never produces rn > 1 for the same national_id again.\n"
    "            \"UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text \" +\n"
    "                \"FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn \" +\n"
    "                \"FROM clients WHERE national_id IS NOT NULL) ranked \" +\n"
    "                \"WHERE c.id = ranked.id AND ranked.rn > 1\",\n"
    "            //\n"
    "            // Step 3: legacy rows created before Phase 2 may still have a blank\n"
    "            // national_id (per the old Client.java comment, \"blank until next\n"
    "            // edited\") -- a real NOT NULL constraint cannot coexist with actual\n"
    "            // NULLs, so give each one a unique placeholder. Naturally idempotent:\n"
    "            // once set, national_id is no longer NULL so the WHERE clause skips it.\n"
    "            \"UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL\",\n"
    "            //\n"
    "            // Step 4: now safe to apply both constraints for real. SET NOT NULL is\n"
    "            // itself idempotent in Postgres (no error re-running it once already\n"
    "            // set). The UNIQUE constraint still goes through the blanket try/catch\n"
    "            // below like every other migration line, so on every boot after the\n"
    "            // first successful one it logs \"already exists\" and skips -- same as\n"
    "            // it always has, except now that log line is finally true.\n"
    "            \"ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL\",\n"
    "            \"ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id)\",\n",

    "DataInitializer -- clean NIN data before constraining it (NOT NULL + real UNIQUE)"
)

# ─── 3. ClientService.java -- javadoc + deprecation note only, logic unchanged ──

patch(
    CLIENT_SERVICE,
    "    /**\n"
    "     * INTAKE: FIND OR CREATE\n"
    "     * Standard industrial deduplication based on Phone Number.\n"
    "     */\n"
    "    @Transactional\n"
    "    public Client findOrCreateClient(String fullName, String phone, String email) {",

    "    /**\n"
    "     * INTAKE: FIND OR CREATE (LEGACY, PHONE-BASED)\n"
    "     * Standard industrial deduplication based on Phone Number.\n"
    "     * DEPRECATED since PHASE C (Section 18.4/18.10): national_id is now\n"
    "     * NOT NULL at the DB level, and this method never sets it, so calling\n"
    "     * it would now fail with a DB integrity violation. Confirmed unused --\n"
    "     * no call sites anywhere in the codebase. Left in place rather than\n"
    "     * deleted since nothing calls it and this phase is scoped to the NIN\n"
    "     * constraint itself; use findOrCreateClientByNin() for anything new.\n"
    "     */\n"
    "    @Transactional\n"
    "    public Client findOrCreateClient(String fullName, String phone, String email) {",

    "ClientService.findOrCreateClient -- deprecation warning comment (dead code, unchanged behavior)"
)

patch(
    CLIENT_SERVICE,
    "    /**\n"
    "     * PHASE 2: NIN-BASED IDENTITY LOOKUP\n"
    "     * Finds an existing person by their National ID (NIN), or creates a new one.\n"
    "     * Per business rule (Section 17.3): if a person's NIN changes, they are\n"
    "     * treated as a brand new person record -- this method never merges by\n"
    "     * name or phone, only ever by NIN.\n"
    "     */",

    "    /**\n"
    "     * NIN-BASED IDENTITY LOOKUP\n"
    "     * Finds an existing person by their National ID (NIN), or creates a new one.\n"
    "     * Per business rule (Section 17.3): if a person's NIN changes, they are\n"
    "     * treated as a brand new person record -- this method never merges by\n"
    "     * name or phone, only ever by NIN.\n"
    "     * PHASE C (Section 18.4/18.10): the blank-NIN check and the\n"
    "     * NIN_NAME_MISMATCH guard below were already correct -- they did not\n"
    "     * rely on the column being optional. What changed is that\n"
    "     * Client.nationalId is now a genuinely enforced NOT NULL + UNIQUE\n"
    "     * column underneath this method (see DataInitializer), instead of the\n"
    "     * soft convention it used to be.\n"
    "     */",

    "ClientService.findOrCreateClientByNin -- javadoc updated to note the constraint is now real"
)

# ─── Commit and push ──────────────────────────────────────────────────────

import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m',
    'Phase C (Section 18.10): Client.nationalId becomes a true mandatory, '
    'unique-checked column (NOT NULL + UNIQUE), with a data-cleanup backfill '
    'so the constraint actually applies instead of silently failing'])
subprocess.run(['git', 'push'])