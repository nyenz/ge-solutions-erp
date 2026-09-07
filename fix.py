import os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p):
    return p.read_text(encoding="utf-8", errors="replace")

def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("WROTE", p.name)

res = []

# ── 1. SystemAdminController.java: add missing tables to TABLES_TO_WIPE ──
sa = BE / "modules" / "admin" / "controller" / "SystemAdminController.java"
s = read(sa)

old_wipe = (
    '    private static final String[] TABLES_TO_WIPE = {\n'
    '        "audit_logs",\n'
    '        "notifications",\n'
    '        "payment_records",\n'
    '        "payment_schedules",\n'
    '        "follow_up_logs",\n'
    '        "project_documents",\n'
    '        "project_stages",\n'
    '        "land_titles",\n'
    '        "land_projects",\n'
    '        "clients",\n'
    '        "company_expenses",\n'
    '        "expenses",\n'
    '        "expense_presets",\n'
    '        "stage_templates",\n'
    '        "users"\n'
    '    };'
)

new_wipe = (
    '    private static final String[] TABLES_TO_WIPE = {\n'
    '        "audit_logs",\n'
    '        "notification_reads",\n'
    '        "notifications",\n'
    '        "recovery_notes",\n'
    '        "payment_records",\n'
    '        "payment_schedules",\n'
    '        "follow_up_logs",\n'
    '        "project_documents",\n'
    '        "project_stages",\n'
    '        "project_proprietors",\n'
    '        "land_titles",\n'
    '        "land_projects",\n'
    '        "clients",\n'
    '        "company_expenses",\n'
    '        "expenses",\n'
    '        "expense_presets",\n'
    '        "stage_templates",\n'
    '        "scenario_seed_flag",\n'
    '        "users"\n'
    '    };'
)

if old_wipe in s:
    s = s.replace(old_wipe, new_wipe)
    res.append("OK added missing tables to TABLES_TO_WIPE")
else:
    res.append("MISS TABLES_TO_WIPE block")

# ── 2. Add scenario reseed call after wipe ──
old_reseed = (
    '        // Reseed the default expense presets (Office, Fieldwork, Land Office)\n'
    '        dataInitializer.seedDefaultExpensePresets();\n'
    '        System.out.println(">>> [WIPE] OK: default expense presets reseeded");\n'
    '\n'
    '        // Purge every uploaded file from Cloudinary storage too'
)

new_reseed = (
    '        // Reseed the default expense presets (Office, Fieldwork, Land Office)\n'
    '        dataInitializer.seedDefaultExpensePresets();\n'
    '        System.out.println(">>> [WIPE] OK: default expense presets reseeded");\n'
    '\n'
    '        // Reseed scenario data (flag was cleared by the truncate above)\n'
    '        try {\n'
    '            dataInitializer.seedScenarioDataOnce();\n'
    '            System.out.println(">>> [WIPE] OK: scenario data reseeded");\n'
    '        } catch (Exception e) {\n'
    '            System.err.println(">>> [WIPE] WARNING: scenario reseed failed: " + e.getMessage());\n'
    '        }\n'
    '\n'
    '        // Purge every uploaded file from Cloudinary storage too'
)

if old_reseed in s:
    s = s.replace(old_reseed, new_reseed)
    res.append("OK added scenario reseed to wipe endpoint")
else:
    res.append("MISS scenario reseed insertion point")

write(sa, s)

for r in res:
    print(r)

# ── git ──
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m",
                    "fix72: add scenario_seed_flag + missing tables to wipe list, reseed demo data after wipe"],
                   cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")