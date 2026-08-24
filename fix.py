import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def patch(path, old, new):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        print("MISSING FILE: " + path)
        return
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print("MISSING ANCHOR in " + path + ": " + old[:60].replace("\n", " | "))
        return
    content = content.replace(old, new)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: " + path)

DI = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"

# 1. Phase 1 constraint: guard with pg_constraint so re-runs log OK, not red.
patch(DI,
    '            "ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index)",',
    '            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = \'uq_land_titles_project_index\') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",')

# 2. Phase C constraint: same guard.
patch(DI,
    '            "ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id)",',
    '            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = \'uq_clients_national_id\') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",')

# 3. Phase B constraint: same guard.
patch(DI,
    '            "ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index)",',
    '            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = \'uq_land_projects_project_index\') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",')

# 4. Refresh the stale Phase C comment that described the old red-line behavior.
patch(DI,
    '            // set). The UNIQUE constraint still goes through the blanket try/catch\n'
    '            // below like every other migration line, so on every boot after the\n'
    '            // first successful one it logs "already exists" and skips -- same as\n'
    '            // it always has, except now that log line is finally true.',
    '            // set). The UNIQUE constraint is wrapped in a DO block guarded by a\n'
    '            // pg_constraint lookup, so once it exists every later boot silently\n'
    '            // no-ops and logs OK instead of a red "already exists" skip.')

# PERMANENT Section 3 rule: commit and push automatically as the last step.
subprocess.run(["git", "add", "-A"], check=True)
r = subprocess.run(["git", "commit", "-m", "Cosmetic: pg_constraint-guarded DO blocks silence red already-exists boot lines"])
if r.returncode == 0:
    subprocess.run(["git", "push"], check=True)
    print("DONE: committed and pushed.")
else:
    print("NOTHING TO COMMIT: no changes were needed.")