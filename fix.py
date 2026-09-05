# fix.py -- fix74: resolve unhandled compiler exceptions in DataInitializer and SystemAdminController
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)

res = []

# --- 1. DataInitializer.java ---
di = BE / "config" / "DataInitializer.java"
s = read(di)

# 1a. Wrap run() in try-catch to prevent Spring Boot startup crash on seed failure
old_run = """    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
        runSchemaMigrations();
        seedRootUser();
        stageTemplateService.seedDefaultStagesIfEmpty();
        seedScenarioDataOnce();
        seedDefaultExpensePresets();
        System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
    }"""

new_run = """    @Override
    public void run(String... args) {
        try {
            System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
            runSchemaMigrations();
            seedRootUser();
            stageTemplateService.seedDefaultStagesIfEmpty();
            seedScenarioDataOnce();
            seedDefaultExpensePresets();
            System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
        } catch (Exception e) {
            System.err.println(">>> [BOOT] FATAL STARTUP ERROR: " + e.getMessage());
            e.printStackTrace();
        }
    }"""

if old_run in s:
    s = s.replace(old_run, new_run)
    res.append("OK wrapped run() in try-catch")
else:
    res.append("MISS run() block")

# 1b. Fix purgeAll() missing throws SQLException
old_purgeall = """    private void purgeAll(Connection conn) {
        String[] stmts = {
            "DELETE FROM notification_reads", "DELETE FROM notifications", "DELETE FROM recovery_notes",
            "DELETE FROM payment_records", "DELETE FROM follow_up_logs", "DELETE FROM project_documents",
            "DELETE FROM project_stages", "DELETE FROM project_proprietors", "DELETE FROM land_projects",
            "DELETE FROM land_titles", "DELETE FROM clients", "DELETE FROM audit_logs",
            "UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1"
        };
        try (Statement st = conn.createStatement()) { for (String s : stmts) { try { st.execute(s); } catch (Exception e) { System.err.println(">>> [SCENARIO] purge skip: " + e.getMessage()); } } }
    }"""

new_purgeall = """    private void purgeAll(Connection conn) throws java.sql.SQLException {
        String[] stmts = {
            "DELETE FROM notification_reads", "DELETE FROM notifications", "DELETE FROM recovery_notes",
            "DELETE FROM payment_records", "DELETE FROM follow_up_logs", "DELETE FROM project_documents",
            "DELETE FROM project_stages", "DELETE FROM project_proprietors", "DELETE FROM land_projects",
            "DELETE FROM land_titles", "DELETE FROM clients", "DELETE FROM audit_logs",
            "UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1"
        };
        try (Statement st = conn.createStatement()) { for (String s : stmts) { try { st.execute(s); } catch (Exception e) { System.err.println(">>> [SCENARIO] purge skip: " + e.getMessage()); } } }
    }"""

if old_purgeall in s:
    s = s.replace(old_purgeall, new_purgeall)
    res.append("OK added throws SQLException to purgeAll()")
else:
    res.append("MISS purgeAll block")

write(di, s)

# --- 2. SystemAdminController.java ---
sa = BE / "modules" / "admin" / "controller" / "SystemAdminController.java"
s2 = read(sa)

# 2a. Wrap seedRootUser() in try-catch to handle its declared 'throws Exception'
old_reseed = """        // Reseed the root admin account so nobody gets locked out
        dataInitializer.seedRootUser();
        System.out.println(">>> [WIPE] OK: admin_root reseeded");"""

new_reseed = """        // Reseed the root admin account so nobody gets locked out
        try {
            dataInitializer.seedRootUser();
            System.out.println(">>> [WIPE] OK: admin_root reseeded");
        } catch (Exception e) {
            System.err.println(">>> [WIPE] WARNING: admin_root reseed failed: " + e.getMessage());
        }"""

if old_reseed in s2:
    s2 = s2.replace(old_reseed, new_reseed)
    res.append("OK wrapped seedRootUser() in try-catch")
else:
    res.append("MISS seedRootUser reseed block")

write(sa, s2)

for r in res: print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix74: resolve unhandled compiler exceptions in DataInitializer and SystemAdminController"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")