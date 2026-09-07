# fix.py -- fix74: recovery queue id-match fix + notification seed + safe seed self-heal + wipe reseeds
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
DI = BE / "config" / "DataInitializer.java"
SA = BE / "modules" / "admin" / "controller" / "SystemAdminController.java"
RC = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"

def read(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("WROTE", p.name)

res = []

def patch(path, old_strip, new_strips, mode):
    s = read(path)
    lines = s.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip() == old_strip:
            base = ln[:len(ln) - len(ln.lstrip())]
            block = [base + t if t else "" for t in new_strips]
            if mode == "replace":
                lines[i:i+1] = block
            elif mode == "after":
                lines[i+1:i+1] = block
            else:
                lines[i:i] = block
            write(path, "\n".join(lines))
            return True
    return False

# ---- 1. DataInitializer: NotificationService dependency ----
if "NotificationService notificationService" in read(DI):
    res.append("OK notificationService field already present")
elif patch(DI, "private final FollowUpRepository followUpRepository;",
    ["private final FollowUpRepository followUpRepository;",
     "private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;"],
    "replace"):
    res.append("OK added notificationService field")
else:
    res.append("MISS followUpRepository field line")

# ---- 2. DataInitializer: call notification seed on boot ----
if "seedNotificationsIfEmpty();" in read(DI):
    res.append("OK seedNotificationsIfEmpty call already present")
elif patch(DI, "seedScenarioDataOnce();",
    ["seedScenarioDataOnce();", "seedNotificationsIfEmpty();"],
    "replace"):
    res.append("OK wired seedNotificationsIfEmpty into boot")
else:
    res.append("MISS seedScenarioDataOnce call line")

# ---- 3. DataInitializer: self-heal gate (flag set but ledger empty -> reseed) ----
if "self-heal re-seed" in read(DI):
    res.append("OK self-heal gate already present")
elif patch(DI, 'if (seeded) { System.out.println(">>> [SCENARIO] Already seeded -- skipping."); return; }',
    ["if (seeded) {",
     "    int projectRows = 0;",
     '    try (java.sql.PreparedStatement ps2 = conn.prepareStatement("SELECT COUNT(*) FROM land_projects"); java.sql.ResultSet rs2 = ps2.executeQuery()) { rs2.next(); projectRows = rs2.getInt(1); }',
     '    if (projectRows > 0) { System.out.println(">>> [SCENARIO] Already seeded -- skipping."); return; }',
     '    System.out.println(">>> [SCENARIO] Flag set but ledger empty -- self-heal re-seed.");',
     "}"],
    "replace"):
    res.append("OK seed gate now self-heals")
else:
    res.append("MISS seed gate line")

# ---- 4. DataInitializer: notification seed method ----
NOTIF_METHOD = [
"// fix74: NOTIFICATION SEED -- the bell / notification center never had demo",
"// data before. Self-heals on any boot where projects exist but notifications",
"// do not. Targets include ROLE_ADMIN and ALL so the Root Owner bell shows them.",
"public void seedNotificationsIfEmpty() {",
"    try (Connection conn = dataSource.getConnection()) {",
"        int n = 0;",
'        try (Statement st = conn.createStatement(); java.sql.ResultSet rs = st.executeQuery("SELECT COUNT(*) FROM notifications")) { if (rs.next()) n = rs.getInt(1); }',
'        if (n > 0) { System.out.println(">>> [SCENARIO] Notifications already present -- skipping."); return; }',
"        java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();",
'        try (Statement st = conn.createStatement(); java.sql.ResultSet rs = st.executeQuery("SELECT id FROM land_projects WHERE deleted = false ORDER BY project_index NULLS LAST LIMIT 12")) { while (rs.next()) ids.add((java.util.UUID) rs.getObject(1)); }',
'        if (ids.isEmpty()) { System.out.println(">>> [SCENARIO] No projects for notification seed -- skipping."); return; }',
"        java.util.UUID id0 = ids.get(0), id1 = ids.get(1 % ids.size()), id2 = ids.get(2 % ids.size()), id3 = ids.get(3 % ids.size()), id4 = ids.get(4 % ids.size()), id5 = ids.get(5 % ids.size()), id6 = ids.get(6 % ids.size()), id7 = ids.get(7 % ids.size()), id8 = ids.get(8 % ids.size()), id9 = ids.get(9 % ids.size()), id10 = ids.get(10 % ids.size()), id11 = ids.get(11 % ids.size());",
'        notificationService.emitRaw("NEW_INTAKE", "INFO", "New project registered -- intake logged by SYSTEM seed.", "PROJECT", id0, "ROLE_MANAGER");',
'        notificationService.emitRaw("PAYMENT_ON_RECEIVABLE", "POSITIVE", "Payment received on a receivable project.", "PROJECT", id1, "ROLE_DIRECTOR");',
'        notificationService.emitRaw("STORAGE_FEE_APPLIED", "INFO", "Monthly storage fee applied to a receivable project.", "PROJECT", id2, "ROLE_DIRECTOR");',
'        notificationService.emitRaw("AUTO_RECEIVABLE_365", "WARN", "Project auto-flagged RECEIVABLE after 365 days silent.", "PROJECT", id3, "ROLE_DIRECTOR");',
'        notificationService.emitRaw("NEGOTIATION_DEADLINE", "WARN", "Negotiation deadline within 3 days on a receivable project.", "PROJECT", id4, "ROLE_MANAGER");',
'        notificationService.emitRaw("FAILED_AFTER_PROMISE", "CRITICAL", "Client failed to pay after committing to a promise date.", "PROJECT", id5, "ROLE_DIRECTOR");',
'        notificationService.emitRaw("FAILED_AFTER_PROMISE_ROOT", "CRITICAL", "Client failed to pay after committing -- Root escalation.", "PROJECT", id5, "ROLE_ADMIN");',
'        notificationService.emitRaw("RELIABILITY_LOW", "WARN", "Client reliability below 40 after negative contact.", "PROJECT", id6, "ROLE_ADMIN");',
'        notificationService.emitRaw("SITE_VISIT_TAGGED", "INFO", "Client tagged as needing a site visit.", "PROJECT", id7, "ROLE_ADMIN");',
'        notificationService.emitRaw("PROMISE_DUE", "CRITICAL", "Promised payment date passed with no payment received.", "PROJECT", id8, "ROLE_ADMIN");',
'        notificationService.emitRaw("COOLDOWN_EXPIRED", "INFO", "Client callable again -- cooldown expired.", "PROJECT", id9, "ROLE_SECRETARY");',
'        notificationService.emitRaw("MONTHLY_LIMIT", "INFO", "Client reached the 2-call monthly limit.", "PROJECT", id10, "ROLE_MANAGER");',
'        notificationService.emitRaw("SYSTEM_NOTICE", "INFO", "Demo dataset active -- ledger, recovery and notifications seeded.", "PROJECT", id11, "ALL");',
'        System.out.println(">>> [SCENARIO] Notification seed complete (13 demo notifications).");',
"    } catch (Exception e) { System.err.println(\">>> [SCENARIO] notification seed fault: \" + e.getMessage()); }",
"}",
]
if "seedNotificationsIfEmpty()" in read(DI):
    res.append("OK notification seed method already present")
elif patch(DI, "// ---------- schema migrations (unchanged) ----------", NOTIF_METHOD, "before"):
    res.append("OK added seedNotificationsIfEmpty method")
else:
    res.append("MISS schema migrations anchor comment")

# ---- 5. SystemAdminController: wipe list gains seed flag + child tables ----
sa = read(SA)
if "scenario_seed_flag" in sa:
    res.append("OK wipe list already includes scenario_seed_flag")
elif patch(SA, '"users"',
    ['"scenario_seed_flag",', '"notification_reads",', '"recovery_notes",', '"project_proprietors",', '"users"'],
    "replace"):
    res.append("OK wipe list now clears seed flag + child tables")
else:
    res.append("MISS users line in TABLES_TO_WIPE")

# ---- 6. SystemAdminController: wipe reseeds scenarios immediately ----
if "scenario dataset reseeded after wipe" in read(SA):
    res.append("OK wipe reseed already present")
elif patch(SA, 'System.out.println(">>> [WIPE] OK: default expense presets reseeded");',
    ['System.out.println(">>> [WIPE] OK: default expense presets reseeded");',
     "try {",
     "    dataInitializer.seedScenarioDataOnce();",
     '    System.out.println(">>> [WIPE] OK: scenario dataset reseeded after wipe");',
     "} catch (Exception e) {",
     '    System.err.println(">>> [WIPE] scenario reseed warning: " + e.getMessage());',
     "}"],
    "replace"):
    res.append("OK wipe now reseeds scenarios immediately")
else:
    res.append("MISS expense presets reseed line")

# ---- 7. RecoveryNoteController: match owners by ID, not object identity ----
if "anyMatch" in read(RC):
    res.append("OK recovery owner match already id-based")
elif patch(RC, "if (p.getProprietors() != null && p.getProprietors().contains(c)) out.add(p);",
    ["if (p.getProprietors() != null && p.getProprietors().stream().anyMatch(o -> o != null && o.getId() != null && o.getId().equals(c.getId()))) out.add(p);"],
    "replace"):
    res.append("OK recovery projectsOf now matches by client ID")
else:
    res.append("MISS projectsOf contains line")

for r in res:
    print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix74: recovery queue id-match fix, notification seed with root-visible targets, seed self-heal, wipe clears flag and reseeds"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")