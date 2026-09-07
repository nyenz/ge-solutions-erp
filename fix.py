# fix.py -- fix70: drop obsolete is_read column from notifications table
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

old_migrations = """            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL\""""

new_migrations = """            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
            "ALTER TABLE notifications DROP COLUMN IF EXISTS is_read\""""

if old_migrations in s:
    s = s.replace(old_migrations, new_migrations)
    res.append("OK added is_read drop migration")
else:
    res.append("MISS migration block")

write(di, s)

for r in res:
    print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix70: drop obsolete is_read column from notifications table to fix seed insert fault"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")