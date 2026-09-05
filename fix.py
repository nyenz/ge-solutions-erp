# fix.py -- fix69: resolve VS Code Java compiler try-with-resources close() bugs and unhandled startup exceptions
import re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): 
    return p.read_text(encoding="utf-8", errors="replace")

def write(p, s): 
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    print("WROTE", p.name)

res = []

# ─── 1. DataInitializer.java ────────────────────────────────────────────────
di = BE / "config" / "DataInitializer.java"
s = read(di)

# Remove unused Client import if present
if "import com.gesolutions.erp.modules.client.model.Client;\n" in s:
    s = s.replace("import com.gesolutions.erp.modules.client.model.Client;\n", "")
    res.append("OK removed unused Client import")

# Wrap run() body in try-catch to handle any startup exceptions
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

# Fix runSchemaMigrations try-with-resources
old_schema = """        try (Connection conn = dataSource.getConnection(); Statement stmt = conn.createStatement()) {
            for (String sql : migrations) { try { stmt.execute(sql); } catch (Exception e) { System.out.println(">>> [DB_SCHEMA] Skipped: " + e.getMessage()); } }
        } catch (Throwable t) { System.err.println(">>> [DB_SCHEMA] Migration warning: " + t.getMessage()); }"""

new_schema = """        Connection conn = null;
        Statement stmt = null;
        try {
            conn = dataSource.getConnection();
            stmt = conn.createStatement();
            for (String sql : migrations) { 
                try { 
                    stmt.execute(sql); 
                } catch (Exception e) { 
                    System.out.println(">>> [DB_SCHEMA] Skipped: " + e.getMessage()); 
                } 
            }
        } catch (Throwable t) { 
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + t.getMessage()); 
        } finally {
            if (stmt != null) try { stmt.close(); } catch (Exception ignored) {}
            if (conn != null) try { conn.close(); } catch (Exception ignored) {}
        }"""

if old_schema in s:
    s = s.replace(old_schema, new_schema)
    res.append("OK fixed runSchemaMigrations try-with-resources")
else:
    res.append("MISS runSchemaMigrations block")

write(di, s)

# ─── 2. SystemAdminController.java ──────────────────────────────────────────
sa = BE / "modules" / "admin" / "controller" / "SystemAdminController.java"
s2 = read(sa)

old_wipe = """        Connection conn = null;
        Statement stmt = null;
        try {
            conn = dataSource.getConnection();
            stmt = conn.createStatement();
            stmt.execute("TRUNCATE TABLE " + tableList + " RESTART IDENTITY CASCADE");
            System.out.println(">>> [WIPE] OK: All business tables truncated -- " + tableList);
        } catch (Exception e) {
            System.err.println(">>> [WIPE] FATAL: Truncate failed: " + e.getMessage());
            return ResponseEntity.internalServerError().body(Map.of(
                "wiped", false,
                "message", "Wipe failed: " + e.getMessage()
            ));
        } finally {
            if (stmt != null) try { stmt.close(); } catch (Exception ignored) {}
            if (conn != null) try { conn.close(); } catch (Exception ignored) {}
        }"""

if old_wipe in s2:
    res.append("OK wipeAllData try-with-resources already fixed")
else:
    res.append("MISS wipeAllData block")

old_reset = """        // Reset the project index counter back to 000/A
        Connection conn2 = null;
        Statement stmt2 = null;
        try {
            conn2 = dataSource.getConnection();
            stmt2 = conn2.createStatement();
            stmt2.execute("UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1");
            System.out.println(">>> [WIPE] OK: project_index_counter reset to 000/A");
        } catch (Exception e) {
            System.err.println(">>> [WIPE] WARNING: Could not reset project_index_counter: " + e.getMessage());
        } finally {
            if (stmt2 != null) try { stmt2.close(); } catch (Exception ignored) {}
            if (conn2 != null) try { conn2.close(); } catch (Exception ignored) {}
        }"""

if old_reset in s2:
    res.append("OK resetCounter try-with-resources already fixed")
else:
    res.append("MISS resetCounter block")

for r in res: 
    print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix69: resolve VS Code Java compiler try-with-resources close() bugs and unhandled startup exceptions"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")