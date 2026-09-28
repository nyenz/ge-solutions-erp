#!/usr/bin/env python3
# PATH: fix134.py
# GOLDEN SEED -- fix134: REMOVE OLD SEED DATA, ADD NEW REALISTIC DATASET.
#   The old scenario dataset (28 projects, owners MUGISHA JOHN ... with
#   national IDs CM9000000000xx, "Scenario seed" payment notes) is replaced.
#
#     1. ONE-TIME SWAP. seedScenarioDataOnce() is keyed on flag id = 2 in
#        scenario_seed_flag (the old seed used id = 1). Existing databases
#        run the swap once on next boot; fresh databases just get the new data.
#     2. TARGETED PURGE. The old purgeAll() wiped every business table. It is
#        replaced by purgeSeedRows(), which deletes ONLY rows that belong to
#        seed clients (national_id LIKE 'CM9000000000%' or 'CM99%') and their
#        projects, titles, payments, documents, stages, follow-ups and
#        recovery notes. Real clients and projects are never touched.
#     3. NO MORE SELF-HEAL RE-SEED. The old "flag set but ledger empty ->
#        re-seed" branch is gone, so emptying the ledger stays empty.
#     4. NEW DATASET. 22 projects, 24 clients with realistic Ugandan names,
#        LRV/Folio title ids, block + plot numbers, real district hierarchies,
#        round UGX amounts. Same scenario coverage as before (intake, in
#        progress, fully paid, released, legacy, receivable, frozen,
#        deadline passed, problem flag, custom storage rate, joint owners,
#        recovery histories, documents). Seed national IDs / phones come from
#        nin(i) / tel(i) so notes and owners can never drift apart.
#     5. Neutral audit text: 'Payment received', 'Uploaded by front desk',
#        'Released to client after full payment' replace the "Scenario ..." tags.
#
# Backend only (DataInitializer.java), no frontend, no schema change.
#
# Atomic: every patch is matched in memory first; if any one is MISSING
# nothing is written and nothing is committed. Runs `mvn -q -DskipTests
# compile` before committing if Maven is on PATH and refuses to commit on a
# red build.
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")

INIT_JAVA = os.path.join(
    BACKEND, "src", "main", "java", "com", "gesolutions", "erp", "config", "DataInitializer.java"
)

MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sub(text, old, new, desc):
    """Exact find/replace, first occurrence. Prints OK / SKIP / MISSING."""
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


def between(text, start, end, new, desc):
    """Replace everything from `start` up to (not including) `end`."""
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    i = text.find(start)
    j = text.find(end, i + 1) if i >= 0 else -1
    if i >= 0 and j > i:
        print("OK: " + desc)
        return text[:i] + new + text[j:]
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


# ======================================================================
# DataInitializer.java
# ======================================================================
java0 = read(INIT_JAVA)
java = java0

java = sub(java,
           "    // ---------- ONE-TIME SCENARIO SEED (wipe once, seed once, never again) ----------",
           "    // ---------- ONE-TIME DEMO DATASET v2 (remove old seed rows once, seed once, never again) ----------",
           "section comment")

# ---- seedScenarioDataOnce + purge (replaces purgeAll) -------------------
java = between(java,
               "    public void seedScenarioDataOnce() {\n",
               "    private String d(int daysAgo)",
               r'''    public void seedScenarioDataOnce() {
        try (Connection conn = dataSource.getConnection()) {
            try (Statement st = conn.createStatement()) {
                st.execute("CREATE TABLE IF NOT EXISTS scenario_seed_flag (id INTEGER PRIMARY KEY, seeded_at TIMESTAMP NOT NULL DEFAULT now())");
            }
            boolean done;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM scenario_seed_flag WHERE id = 2"); java.sql.ResultSet rs = ps.executeQuery()) { rs.next(); done = rs.getInt(1) > 0; }
            if (done) { System.out.println(">>> [SCENARIO] Dataset v2 already seeded -- skipping."); return; }
            purgeSeedRows(conn);
            seedScenarios();
            try (Statement st = conn.createStatement()) { st.execute("INSERT INTO scenario_seed_flag (id) VALUES (2) ON CONFLICT (id) DO NOTHING"); }
            System.out.println(">>> [SCENARIO] Dataset v2 seeded (22 projects).");
        } catch (Exception e) { System.err.println(">>> [SCENARIO] seed fault: " + e.getMessage()); }
    }
    private java.util.List<Object> idList(Connection conn, String sql, java.sql.Array arg) throws java.sql.SQLException {
        java.util.List<Object> out = new java.util.ArrayList<>();
        try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
            if (arg != null) ps.setArray(1, arg);
            try (java.sql.ResultSet rs = ps.executeQuery()) { while (rs.next()) out.add(rs.getObject(1)); }
        }
        return out;
    }
    private void purgeBy(Connection conn, String sql, java.sql.Array arg) {
        try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) { ps.setArray(1, arg); ps.executeUpdate(); }
        catch (Exception e) { System.err.println(">>> [SCENARIO] purge skip: " + e.getMessage()); }
    }
    // Deletes only rows that belong to seed clients (old CM9000000000xx ids and new CM99xxxxxxLLLL ids).
    private void purgeSeedRows(Connection conn) throws java.sql.SQLException {
        java.util.List<Object> clients = idList(conn, "SELECT id FROM clients WHERE national_id LIKE 'CM9000000000%' OR national_id LIKE 'CM99%'", null);
        if (clients.isEmpty()) return;
        java.sql.Array cArr = conn.createArrayOf("uuid", clients.toArray());
        java.util.List<Object> projects = idList(conn, "SELECT DISTINCT project_id FROM project_proprietors WHERE client_id = ANY(?)", cArr);
        java.sql.Array pArr = conn.createArrayOf("uuid", projects.toArray());
        java.util.List<Object> titles = idList(conn, "SELECT title_id FROM land_projects WHERE title_id IS NOT NULL AND id = ANY(?)", pArr);
        java.sql.Array tArr = conn.createArrayOf("uuid", titles.toArray());
        String[] byProject = { "payment_records", "follow_up_logs", "project_documents", "project_stages", "payment_schedules" };
        for (String t : byProject) purgeBy(conn, "DELETE FROM " + t + " WHERE project_id = ANY(?)", pArr);
        purgeBy(conn, "DELETE FROM recovery_notes WHERE client_id = ANY(?)", cArr);
        purgeBy(conn, "DELETE FROM project_proprietors WHERE client_id = ANY(?)", cArr);
        purgeBy(conn, "DELETE FROM land_projects WHERE id = ANY(?)", pArr);
        purgeBy(conn, "DELETE FROM land_titles WHERE id = ANY(?)", tArr);
        purgeBy(conn, "DELETE FROM clients WHERE id = ANY(?)", cArr);
        try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM land_projects"); java.sql.ResultSet rs = ps.executeQuery()) {
            rs.next();
            if (rs.getInt(1) == 0) { try (Statement st = conn.createStatement()) { st.execute("UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1"); } }
        }
        System.out.println(">>> [SCENARIO] Old seed rows removed.");
    }
    // Deterministic fake identifiers: 14-char national ID (CM99 + 6 digits + 4 letters) and 10-digit 07xx phone.
    private static String nin(int i) {
        String L = "ABCDEFGHJKLMNPRSTUWXYZ";
        return "CM99" + String.format("%06d", 120000 + (i * 3719) % 880000)
                + L.charAt(i % L.length()) + L.charAt((i * 5 + 3) % L.length())
                + L.charAt((i * 7 + 1) % L.length()) + L.charAt((i * 11 + 2) % L.length());
    }
    private static String tel(int i) { return "07" + (i % 2 == 0 ? "01" : "52") + String.format("%06d", 234000 + i * 173); }
''',
               "one-time swap (flag 2) + targeted purgeSeedRows + nin/tel helpers")

# ---- neutral audit text --------------------------------------------------
java = sub(java,
           "'SYSTEM', 'Scenario seed', ?",
           "'SYSTEM', 'Payment received', ?",
           "payment note text")
java = sub(java,
           "'Scenario doc'",
           "'Uploaded by front desk'",
           "document note text")
java = sub(java,
           "\"Scenario release\"",
           "\"Released to client after full payment\"",
           "release reason text")

# ---- new dataset ---------------------------------------------------------
java = between(java,
               "    private void seedScenarios() throws Exception {\n",
               "    private java.util.UUID seedOne(",
               r'''    private void seedScenarios() throws Exception {
        List<StageTemplate> master = stageTemplateService.getActiveTemplate();
        Map<String, String> idByName = new HashMap<>();
        for (StageTemplate t : master) idByName.put(t.getStageName(), t.getId().toString());
        String FW = "Field Work", DP = "Deed Plan", LCI = "LC Inspection", DLB = "District Land Board Approval", TASD = "Tax Assessment and Stamp Duty", REG = "Registration and Title Issuance";
        String[] ALL = { FW, DP, LCI, DLB, TASD, REG };
        Map<String, UUID> S = new HashMap<>();
        // INTAKE + IN-PROGRESS
        S.put("s1", seedOne(null, false, false, false, null, null, "KYADONDO BLOCK 244", d(21), 3200000, 1000000, 0, 0, new String[][] { { "KATO HERBERT", nin(1), tel(1) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "WAKISO", "KYADONDO", "NANSANA MUNICIPALITY", "NANSANA EAST", "KYEBANDO", "Residential" }, "Deposit received at intake; field work scheduled", idByName));
        S.put("s2", seedOne(null, false, false, false, null, null, "KYADONDO BLOCK 118", d(55), 4200000, 2100000, 0, 0, new String[][] { { "NABUKENYA ROSE", nin(2), tel(2) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KYADONDO", "MAKINDYE DIVISION", "KANSANGA", "MUYENGA", "Residential" }, null, idByName));
        S.put("s3", seedOne(null, false, false, false, null, null, "MAWOKOTA BLOCK 302", d(85), 3800000, 1900000, 0, 0, new String[][] { { "SSEMWOGERERE ISAAC", nin(3), tel(3) }, { "NAMULI PROSSY", nin(4), tel(4) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "MPIGI", "MAWOKOTA", "MPIGI TOWN COUNCIL", "KAFUMU", "KAYABWE", "Agricultural" }, "Joint owners; both must sign the deed plan", idByName));
        S.put("s4", seedOne("2417", false, true, false, "LRV 3310 FOLIO 14", d(40), "KASHARI BLOCK 96", d(110), 4500000, 3150000, 0, 0, new String[][] { { "BYAMUGISHA INNOCENT", nin(5), tel(5) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "MBARARA", "KASHARI", "MBARARA CITY NORTH DIVISION", "KAKOBA", "NYAMITANGA", "Residential" }, null, idByName));
        // FULLY PAID + RELEASED
        S.put("s5", seedOne("781", false, true, false, "LRV 4102 FOLIO 3", d(35), "ASWA BLOCK 57", d(125), 4800000, 4800000, 0, 0, new String[][] { { "ACHIENG BEATRICE", nin(6), tel(6) } }, ALL, null, null, new String[] { "GULU", "ASWA", "LAYIBI DIVISION", "PECE", "LACOR", "Residential" }, "Fully paid; awaiting release to client", idByName));
        S.put("s6", seedOne("1204", false, true, false, "LRV 4188 FOLIO 21", d(30), "BUDIOPE BLOCK 88", d(140), 5200000, 5200000, 0, 0, new String[][] { { "TUMUSIIME JOSEPH", nin(7), tel(7) } }, ALL, null, "RELEASE", new String[] { "JINJA", "BUDIOPE", "JINJA CITY SOUTH DIVISION", "WALUKUBA", "MPUMUDDE", "Commercial" }, "Title released to client", idByName));
        // LEGACY
        S.put("s7", seedOne("355", true, true, false, "LRV 1120 FOLIO 7", "1985-06-15", "BUDDU BLOCK 61", d(400), 3500000, 1750000, 0, 0, new String[][] { { "LUBEGA MOSES", nin(8), tel(8) } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "MASAKA", "BUDDU", "MASAKA CITY", "KIMAANYA", "KYESIGA", "Residential" }, "Legacy file; client silent for over a year", idByName));
        S.put("s8", seedOne("412", true, true, false, "LRV 1584 FOLIO 22", "1990-03-20", "BUNGOKHO BLOCK 12", d(300), 4000000, 800000, 0, 0, new String[][] { { "NALUBEGA AGNES", nin(9), tel(9) }, { "KIIZA EMMANUEL", nin(10), tel(10) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "MBALE", "BUNGOKHO", "MBALE CITY", "NAMAKWEKWE", "WANALE", "Industrial" }, "Legacy joint file", idByName));
        // RECEIVABLE FAMILY
        S.put("s9", seedOne("1533", false, true, true, "LRV 3890 FOLIO 5", d(350), "AYIVU BLOCK 33", d(360), 4500000, 900000, 50000, 50000, new String[][] { { "APIO DOREEN", nin(11), tel(11) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "ARUA", "AYIVU", "ARUA CITY", "RIVER OLI", "ANYAFIO", "Residential" }, "Receivable; client silent since last payment", idByName));
        S.put("s10", seedOne("902", false, true, true, "LRV 3902 FOLIO 9", d(320), "PADYERE BLOCK 14", d(330), 5000000, 750000, 50000, 50000, new String[][] { { "MUGENYI STEPHEN", nin(12), tel(12) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "NEBBI", "PADYERE", "NEBBI TOWN COUNCIL", "PAIDHA", "PANYIMUR", "Agricultural" }, "Receivable; client paying in instalments", idByName));
        S.put("s11", seedOne("648", false, true, true, "LRV 3915 FOLIO 2", d(300), "SOROTI BLOCK 21", d(310), 3800000, 380000, 50000, 50000, new String[][] { { "NAKAMYA HARRIET", nin(13), tel(13) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "SOROTI", "SOROTI", "SOROTI CITY EAST DIVISION", "GWERI", "ARAPAI", "Agricultural" }, "Receivable; storage frozen during negotiation", idByName));
        S.put("s12", seedOne("2210", false, true, true, "LRV 3941 FOLIO 18", d(290), "TORORO BLOCK 45", d(300), 4200000, 420000, 50000, 50000, new String[][] { { "OPOLOT VINCENT", nin(14), tel(14) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "TORORO", "TORORO", "TORORO MUNICIPALITY", "MOLO", "KADAMA", "Residential" }, "Receivable; negotiation deadline passed", idByName));
        S.put("s13", seedOne("1875", false, true, false, "LRV 4021 FOLIO 11", d(95), "BUGAHYA BLOCK 72", d(115), 4700000, 2350000, 0, 0, new String[][] { { "BWIRE ALFRED", nin(15), tel(15) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "HOIMA", "BUGAHYA", "HOIMA CITY EAST DIVISION", "KIGOROBYA", "BUJUMBURA", "Residential" }, "Boundary dispute with neighbour; flagged as problem", idByName));
        S.put("s14", seedOne("3306", false, true, true, "LRV 3960 FOLIO 27", d(280), "AYIVU BLOCK 34", d(290), 6000000, 3000000, 75000, 75000, new String[][] { { "NANTONGO JULIET", nin(16), tel(16) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "ARUA", "AYIVU", "ARUA CITY", "RIVER OLI", "ANYAFIO", "Commercial" }, "Custom storage rate agreed at 75,000", idByName));
        // RECOVERY COVERAGE
        S.put("s15", seedOne("1421", false, true, false, "LRV 4050 FOLIO 6", d(85), "IGARA BLOCK 19", d(120), 4300000, 2150000, 0, 0, new String[][] { { "AHIMBISIBWE GILBERT", nin(17), tel(17) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "BUSHENYI", "IGARA", "BUSHENYI-ISHAKA MUNICIPALITY", "NYAKABIRIZI", "KATUNGURU", "Residential" }, null, idByName));
        S.put("s16", seedOne("3122", false, true, false, "LRV 4066 FOLIO 13", d(90), "KOOKI BLOCK 27", d(130), 4600000, 2300000, 0, 0, new String[][] { { "OJOK DENIS", nin(18), tel(18) } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "RAKAI", "KOOKI", "RAKAI TOWN COUNCIL", "KALISIZO", "KYOTERA", "Agricultural" }, null, idByName));
        S.put("s17", seedOne("540", false, true, false, "LRV 4071 FOLIO 1", d(88), "BURAHYA BLOCK 8", d(140), 5800000, 2900000, 0, 0, new String[][] { { "NAMATOVU ESTHER", nin(19), tel(19) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KABAROLE", "BURAHYA", "FORT PORTAL CITY EAST DIVISION", "KARAMBI", "KISIMBA", "Residential" }, null, idByName));
        S.put("s18", seedOne("2718", false, true, false, "LRV 4085 FOLIO 19", d(80), "SHEEMA BLOCK 41", d(150), 5200000, 2600000, 0, 0, new String[][] { { "MUGISHA ANDREW", nin(20), tel(20) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "SHEEMA", "SHEEMA", "SHEEMA MUNICIPALITY", "KITAGATA", "KAZINGA", "Mixed Use" }, null, idByName));
        S.put("s19", seedOne("963", false, true, false, "LRV 4090 FOLIO 24", d(75), "KATIKAMU BLOCK 62", d(160), 4800000, 2400000, 0, 0, new String[][] { { "NANKYA SYLVIA", nin(21), tel(21) } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "LUWEERO", "KATIKAMU", "LUWEERO TOWN COUNCIL", "BAMUNANIKA", "WOBULENZI", "Residential" }, null, idByName));
        S.put("s20", seedOne("1187", false, true, false, "LRV 4210 FOLIO 30", d(70), "KYADONDO BLOCK 205", d(170), 4100000, 2050000, 0, 0, new String[][] { { "KAWEESI TIMOTHY", nin(22), tel(22) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KYADONDO", "MAKINDYE DIVISION", "KIBULI", "KIBULI", "Residential" }, null, idByName));
        // INTAKE TODAY + DOCUMENTS
        S.put("s21", seedOne(null, false, false, false, null, null, "KYADONDO BLOCK 260", d(0), 3600000, 900000, 0, 0, new String[][] { { "KIGGUNDU SAMUEL", nin(23), tel(23) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KYADONDO", "KAWEMPE DIVISION", "MAKERERE III", "KIKONI", "Mixed Use" }, "Walk-in intake today", idByName));
        S.put("s22", seedOne("1954", false, true, false, "LRV 4233 FOLIO 12", d(45), "KYADONDO BLOCK 190", d(200), 5100000, 3570000, 0, 0, new String[][] { { "NAKIMULI JOAN", nin(24), tel(24) } }, new String[] { FW, DP, LCI, DLB, TASD }, new String[] { REG }, null, new String[] { "KAMPALA", "KYADONDO", "NAKAWA DIVISION", "BUGOLOBI", "BUGOLOBI", "Residential" }, "Only registration remaining; documents on file", idByName));
        // payments + badges
        backdatePayment(S.get("s2"), 5, 1000000, "STANDARD");
        backdatePayment(S.get("s3"), 60, 380000, "STANDARD");
        backdatePayment(S.get("s4"), 20, 900000, "STANDARD");
        backdatePayment(S.get("s7"), 400, 500000, "STANDARD");
        backdatePayment(S.get("s9"), 300, 400000, "STANDARD");
        backdatePayment(S.get("s10"), 5, 500000, "RECEIVABLE_PARTIAL");
        // folder flags
        flag(S.get("s11"), "storage_paused = true, negotiation_deadline = now() + interval '30 days'");
        flag(S.get("s12"), "negotiation_deadline = now() - interval '5 days'");
        flag(S.get("s13"), "is_problem = true");
        flag(S.get("s14"), "storage_fee_override = 75000");
        // documents
        doc(S.get("s22"), "DEED_PLAN", "deed-plan-nakimuli-joan.pdf");
        doc(S.get("s22"), "NIN_SCAN", "nin-scan-nakimuli-joan.jpg");
        // folder notes
        fup(S.get("s1"), "Client visited the office and asked about the stage timeline", 2);
        fup(S.get("s9"), "Called about storage fees and requested a statement", 12);
        fup(S.get("s3"), "Co-owner NAMULI PROSSY asked to be contacted separately", 1);
        // recovery histories
        note(nin(17), "answered call", "POSITIVE", true, 3, "Will pay after the coffee harvest", null);
        touchClient(nin(17), 3, 80.0);
        note(nin(18), "answered call", "POSITIVE", true, 1, "Confirmed he received the balance statement", null);
        note(nin(18), "committed to pay", "POSITIVE", true, 0, "Promised to pay on Friday", null);
        touchClient(nin(18), 0, 85.0);
        note(nin(19), "answered call", "POSITIVE", true, 20, null, null);
        note(nin(19), "failed to pay", "NEGATIVE", false, 18, "Did not honour the promise made on the call", null);
        touchClient(nin(19), 20, 60.0);
        note(nin(20), "committed to pay", "POSITIVE", true, 10, "Promise date has passed", -1);
        touchClient(nin(20), 10, 70.0);
        note(nin(21), "committed to pay", "POSITIVE", true, 5, "Will pay once salary comes in", 7);
        touchClient(nin(21), 5, 75.0);
        note(nin(22), "not picking up", "NEGATIVE", true, 20, null, null);
        note(nin(22), "phone off", "NEGATIVE", true, 16, null, null);
        touchClient(nin(22), 16, 55.0);
    }
''',
               "new realistic dataset (22 projects, 24 clients)")

# ======================================================================
# write (atomic) + build gate + commit
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix133).")
    sys.exit(1)

if java != java0:
    write(INIT_JAVA, java)
    print("written: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java")
else:
    print("note: nothing changed -- fix134 already applied")

# build gate (fix76): backend compile
mvn = shutil.which("mvn")
if mvn and os.path.isfile(os.path.join(BACKEND, "pom.xml")):
    build = subprocess.run([mvn, "-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        print("FAIL: build is red -- aborting, nothing committed")
        sys.exit(1)
    print("build OK")
else:
    print("note: Maven not found here -- skipping build gate (install mvn if you want it enforced)")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

git("add", "-A")
git("commit", "-m", "fix134: replace old scenario seed with new realistic dataset -- one-time targeted purge of seed clients (CM9000000000xx / CM99xx), 22 projects, flag id 2, no self-heal re-seed")
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip() or "pushed")