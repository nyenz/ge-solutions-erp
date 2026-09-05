# fix.py -- fix69: resolve VS Code Java compiler try-with-resources close() bugs and unhandled startup exceptions
import re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)

res = []

# ─── 1. DataInitializer.java ────────────────────────────────────────────────
di = BE / "config" / "DataInitializer.java"
s = read(di)

# Remove unused Client import if present
if "import com.gesolutions.erp.modules.client.model.Client;" in s:
    s = s.replace("import com.gesolutions.erp.modules.client.model.Client;\n", "")
    res.append("OK removed unused Client import")

# Wrap run() body in try-catch to handle any startup exceptions
old_run = """    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
        runSchemaMigrations();
        seedRootUser();
        stageTemplateService.seedDefaultStagesIfEmpty();
        seedSampleProjects();
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
            seedSampleProjects();
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

# Fix purgeSampleData try-with-resources
old_purge = """        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) { try { st.execute(s); } catch (Exception e) { System.err.println(">>> [RESET] skip: " + e.getMessage()); } }
            System.out.println(">>> [RESET] Full demo wipe complete (users/presets/templates kept).");
        } catch (Exception e) { System.err.println(">>> [RESET] wipe warning: " + e.getMessage()); }"""
new_purge = """        Connection conn = null;
        Statement st = null;
        try {
            conn = dataSource.getConnection();
            st = conn.createStatement();
            for (String s : stmts) { try { st.execute(s); } catch (Exception e) { System.err.println(">>> [RESET] skip: " + e.getMessage()); } }
            System.out.println(">>> [RESET] Full demo wipe complete (users/presets/templates kept).");
        } catch (Exception e) { System.err.println(">>> [RESET] wipe warning: " + e.getMessage()); }
        finally {
            if (st != null) try { st.close(); } catch (Exception ignored) {}
            if (conn != null) try { conn.close(); } catch (Exception ignored) {}
        }"""
if old_purge in s:
    s = s.replace(old_purge, new_purge)
    res.append("OK fixed purgeSampleData try-with-resources")
else:
    res.append("MISS purgeSampleData block")

# Fix runSchemaMigrations try-with-resources
old_schema = """        try (Connection conn = dataSource.getConnection(); Statement stmt = conn.createStatement()) {
            for (String sql : migrations) {
                try { stmt.execute(sql); System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length()))); }
                catch (Exception e) { System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage()); }
            }
        } catch (Exception e) { System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage()); }"""
new_schema = """        Connection conn = null;
        Statement stmt = null;
        try {
            conn = dataSource.getConnection();
            stmt = conn.createStatement();
            for (String sql : migrations) {
                try { stmt.execute(sql); System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length()))); }
                catch (Exception e) { System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage()); }
            }
        } catch (Exception e) { System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage()); }
        finally {
            if (stmt != null) try { stmt.close(); } catch (Exception ignored) {}
            if (conn != null) try { conn.close(); } catch (Exception ignored) {}
        }"""
if old_schema in s:
    s = s.replace(old_schema, new_schema)
    res.append("OK fixed runSchemaMigrations try-with-resources")
else:
    res.append("MISS runSchemaMigrations block")

# Fix seedRootUser try-with-resources
old_root = """        try (java.sql.Connection conn = dataSource.getConnection()) {
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) { if (rs.next()) exists = rs.getInt(1) > 0; }
            }
            if (!exists) {
                try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) " +
                    "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)")) {
                    ps.setObject(1, java.util.UUID.randomUUID()); ps.setString(2, email); ps.setString(3, encodedPassword);
                    ps.executeUpdate();
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset.");
            }
        } catch (Exception e) { System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:"); e.printStackTrace(); }"""
new_root = """        java.sql.Connection conn = null;
        try {
            conn = dataSource.getConnection();
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) { if (rs.next()) exists = rs.getInt(1) > 0; }
            }
            if (!exists) {
                try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) " +
                    "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)")) {
                    ps.setObject(1, java.util.UUID.randomUUID()); ps.setString(2, email); ps.setString(3, encodedPassword);
                    ps.executeUpdate();
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset.");
            }
        } catch (Exception e) { System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:"); e.printStackTrace(); }
        finally {
            if (conn != null) try { conn.close(); } catch (Exception ignored) {}
        }"""
if old_root in s:
    s = s.replace(old_root, new_root)
    res.append("OK fixed seedRootUser try-with-resources")
else:
    res.append("MISS seedRootUser block")

write(di, s)

# ─── 2. SystemAdminController.java ──────────────────────────────────────────
sa = BE / "modules" / "admin" / "controller" / "SystemAdminController.java"
s2 = read(sa)

old_wipe = """        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {
            stmt.execute("TRUNCATE TABLE " + tableList + " RESTART IDENTITY CASCADE");
            System.out.println(">>> [WIPE] OK: All business tables truncated -- " + tableList);
        } catch (Exception e) {
            System.err.println(">>> [WIPE] FATAL: Truncate failed: " + e.getMessage());
            return ResponseEntity.internalServerError().body(Map.of(
                "wiped", false,
                "message", "Wipe failed: " + e.getMessage()
            ));
        }"""
new_wipe = """        Connection conn = null;
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
    s2 = s2.replace(old_wipe, new_wipe)
    res.append("OK fixed wipeAllData try-with-resources")
else:
    res.append("MISS wipeAllData block")

old_reset = """        // Reset the project index counter back to 000/A
        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {
            stmt.execute("UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1");
            System.out.println(">>> [WIPE] OK: project_index_counter reset to 000/A");
        } catch (Exception e) {
            System.err.println(">>> [WIPE] WARNING: Could not reset project_index_counter: " + e.getMessage());
        }"""
new_reset = """        // Reset the project index counter back to 000/A
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
    s2 = s2.replace(old_reset, new_reset)
    res.append("OK fixed resetCounter try-with-resources")
else:
    res.append("MISS resetCounter block")

write(sa, s2)

for r in res: print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix69: resolve VS Code Java compiler try-with-resources close() bugs and unhandled startup exceptions"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")