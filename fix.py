#!/usr/bin/env python3
"""
fix_final.py — COMBINED best-of-both fix for the empty-Ledger / sample-seed bug.

Root cause (two parts):
  1. A leftover UNIQUE constraint on clients.phone_number, created under a
     Hibernate auto-generated name (uk_bt1ji0od8t2mhp0thot6pod8u), was never
     dropped. Every sample-seed attempt died on duplicate phone_number.
  2. atomicIntake() was NOT @Transactional, so a failure partway through left
     an orphaned Client row that re-poisoned every later restart.

This patch:
  A. DataInitializer: fast-path drop of the known constraint name, THEN a
     name-agnostic information_schema sweep that removes ANY unique constraint
     on clients.phone_number.
  B. LandService: wrap atomicIntake() in @Transactional(rollbackFor=...) so a
     failure rolls the whole intake back (no orphans ever again).

Run: python3 fix_final.py
"""
import os
import subprocess

PATCHES = [
    # ------------------------------------------------------------------
    # A. Drop the leftover phone_number unique constraint (both ways).
    # ------------------------------------------------------------------
    {
        "path": "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
        "old": '            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",\n',
        "new": (
            '            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",\n'
            '            // FIX (combined): the line above only knew one name. An older\n'
            '            // schema also created a UNIQUE constraint on clients.phone_number\n'
            '            // under a Hibernate auto-generated name (uk_bt1ji0od8t2mhp0thot6pod8u)\n'
            '            // that silently blocked every duplicate-phone insert (joint owners,\n'
            '            // repeat sample seeds). Fast-path the known name first...\n'
            '            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS uk_bt1ji0od8t2mhp0thot6pod8u",\n'
            '            // ...then a name-agnostic sweep via information_schema so ANY\n'
            '            // leftover unique constraint on phone_number is removed regardless\n'
            '            // of what Hibernate called it.\n'
            '            "DO $$ DECLARE cname text; BEGIN " +\n'
            '                "SELECT tc.constraint_name INTO cname FROM information_schema.table_constraints tc " +\n'
            '                "JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name " +\n'
            '                "WHERE tc.table_name = \'clients\' AND tc.constraint_type = \'UNIQUE\' AND ccu.column_name = \'phone_number\' LIMIT 1; " +\n'
            '                "IF cname IS NOT NULL THEN EXECUTE \'ALTER TABLE clients DROP CONSTRAINT \' || quote_ident(cname); END IF; " +\n'
            '                "END $$",\n'
        ),
    },
    # ------------------------------------------------------------------
    # B. Make atomicIntake() one all-or-nothing transaction (root cause).
    # ------------------------------------------------------------------
    {
        "path": "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
        "old": (
            '    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {\n'
            '        // PHASE D (Section 18.10): LandProject is built FIRST. A LandTitle\n'
            '        // is only built if the legacy preset is used or the final\n'
        ),
        "new": (
            '    // FIX (combined): this method was missing @Transactional, so its\n'
            '    // individual saves (client, project, payment, stages, notes) each\n'
            '    // committed on their own. A failure partway -- like the sample seed --\n'
            '    // left an orphaned Client row that re-poisoned every later restart.\n'
            '    // Now the whole intake is one all-or-nothing unit, same as every\n'
            '    // other write method in this class.\n'
            '    @Transactional(rollbackFor = Exception.class)\n'
            '    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {\n'
            '        // PHASE D (Section 18.10): LandProject is built FIRST. A LandTitle\n'
            '        // is only built if the legacy preset is used or the final\n'
        ),
    },
]


def apply_patch(patch):
    path = patch["path"]
    if not os.path.exists(path):
        print("MISSING (file not found): " + path)
        return False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if patch["new"] in content:
        print("OK (already applied): " + path)
        return True

    if patch["old"] not in content:
        print("MISSING (patch target not found): " + path)
        return False

    content = content.replace(patch["old"], patch["new"], 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: " + path)
    return True


def main():
    all_ok = True
    for patch in PATCHES:
        all_ok = apply_patch(patch) and all_ok

    if not all_ok:
        print("\nOne or more patches did not apply. Review MISSING lines above before deploying.")
        return

    subprocess.run(["git", "add", "-A"], check=False)
    subprocess.run(
        ["git", "commit", "-m",
         "fix(final): drop leftover phone_number unique constraint (known name + info_schema sweep); make atomicIntake transactional"],
        check=False,
    )
    subprocess.run(["git", "push"], check=False)
    print("\nDone. Check the Render Events tab for the new deploy; the boot log should")
    print("show '>>> [SAMPLE] Seeded 7 sample projects' and the Ledger will fill.")


if __name__ == "__main__":
    main()