# fix.py -- fix73: seed-data recovery (self-heal empty ledger, wipe list, wipe re-seed)
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
DI = BE / "config" / "DataInitializer.java"
SA = BE / "modules" / "admin" / "controller" / "SystemAdminController.java"

def read(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("WROTE", p.name)

res = []

# ---- 1. DataInitializer: self-heal seed guard ----
s = read(DI)
if "self-heal re-seed" in s:
    res.append("OK already applied: seed guard self-heal")
else:
    old = 'if (seeded) { System.out.println(">>> [SCENARIO] Already seeded -- skipping."); return; }'
    lines = s.split("\n")
    hit = False
    for i, ln in enumerate(lines):
        if ln.strip() == old:
            base = ln[:len(ln) - len(ln.lstrip())]
            block = [
                base + "if (seeded) {",
                base + "    int projectRows = 0;",
                base + '    try (java.sql.PreparedStatement ps2 = conn.prepareStatement("SELECT COUNT(*) FROM land_projects"); java.sql.ResultSet rs2 = ps2.executeQuery()) { rs2.next(); projectRows = rs2.getInt(1); }',
                base + '    if (projectRows > 0) { System.out.println(">>> [SCENARIO] Already seeded -- skipping."); return; }',
                base + '    System.out.println(">>> [SCENARIO] Flag set but ledger empty -- self-heal re-seed.");',
                base + "}",
            ]
            lines[i:i+1] = block
            hit = True
            break
    if hit:
        write(DI, "\n".join(lines))
        res.append("OK patched: seed guard self-heal")
    else:
        res.append("MISSING: seed guard line in DataInitializer")

# ---- 2. SystemAdminController: wipe list gains missing tables ----
s2 = read(SA)
extras = ["notification_reads", "recovery_notes", "project_proprietors", "scenario_seed_flag"]
missing = [t for t in extras if ('"' + t + '"') not in s2]
if not missing:
    res.append("OK already applied: wipe list extras")
else:
    lines = s2.split("\n")
    hit = False
    for i, ln in enumerate(lines):
        if ln.strip() == '"users"':
            base = ln[:len(ln) - len(ln.lstrip())]
            add = [base + '"' + t + '",' for t in missing]
            lines[i:i] = add
            hit = True
            break
    if hit:
        write(SA, "\n".join(lines))
        res.append("OK patched: wipe list += " + ", ".join(missing))
    else:
        res.append('MISSING: "users" line in TABLES_TO_WIPE')

# ---- 3. SystemAdminController: wipe re-seeds scenario data ----
s3 = read(SA)
if "seedScenarioDataOnce" in s3:
    res.append("OK already applied: wipe re-seed call")
else:
    old3 = 'System.out.println(">>> [WIPE] OK: default expense presets reseeded");'
    lines = s3.split("\n")
    hit = False
    for i, ln in enumerate(lines):
        if ln.strip() == old3:
            base = ln[:len(ln) - len(ln.lstrip())]
            lines[i+1:i+1] = [
                base + 'try { dataInitializer.seedScenarioDataOnce(); System.out.println(">>> [WIPE] OK: scenario re-seed attempted"); } catch (Exception e) { System.err.println(">>> [WIPE] scenario re-seed warning: " + e.getMessage()); }',
            ]
            hit = True
            break
    if hit:
        write(SA, "\n".join(lines))
        res.append("OK patched: wipe re-seed call")
    else:
        res.append("MISSING: expense presets reseed line in wipe endpoint")

for r in res:
    print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix73: seed-data recovery - self-heal empty ledger, wipe list gains seed flag, wipe re-seeds demo data"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")