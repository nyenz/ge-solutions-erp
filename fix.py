#!/usr/bin/env python3
"""fix28.py — wipe all sample data (no re-seed) + sticky covered column header.
Idempotent + defensive (regex-based), safe to re-run. Run: py fix28.py"""
import re, subprocess
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
DONE=[]

def rd(rel): return (ROOT/rel).read_text(encoding="utf-8")
def wr(rel, t): (ROOT/rel).write_text(t, encoding="utf-8"); DONE.append(rel)

# ---------------- 1) DataInitializer: remove any sample seeding, add wipe ----------------
rel='erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java'
t = rd(rel)
# remove any sample-seed call so nothing re-seeds
t = re.sub(r"(?m)^\s*seedSampleProjects\(\);\s*\n", "", t)
# ensure a purge call exists in run()
if "purgeSampleData();" not in t:
    t = t.replace("seedDefaultExpensePresets();\n",
                  "seedDefaultExpensePresets();\n        purgeSampleData();\n", 1)
# ensure the purge method exists
if "private void purgeSampleData()" not in t:
    method = '''
    // CLEAN: wipe leftover sample/demo rows so the ledger starts clean (no re-seed).
    private void purgeSampleData() {
        String idsSql =
            "SELECT lp.id FROM land_projects lp " +
            "WHERE lp.district = 'SAMPLE DATA' " +
            "OR lp.id IN (SELECT lt.id FROM land_titles lt WHERE lt.plot_number LIKE 'SAMPLE-%') " +
            "OR lp.id IN (SELECT pp.project_id FROM project_proprietors pp JOIN clients c ON c.id = pp.client_id WHERE c.national_id LIKE 'SMPL-%')";
        String[] stmts = {
            "DELETE FROM payment_records WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM follow_up_logs WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM project_stages WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM project_proprietors WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM land_projects WHERE id IN (" + idsSql + ")",
            "DELETE FROM land_titles WHERE plot_number LIKE 'SAMPLE-%'",
            "DELETE FROM clients WHERE national_id LIKE 'SMPL-%'",
        };
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) { try { st.execute(s); } catch (Exception e) {} }
            System.out.println(">>> [SAMPLE] All sample data wiped.");
        } catch (Exception e) { System.err.println(">>> [SAMPLE] purge warning: " + e.getMessage()); }
    }
'''
    t = t.replace("    public void seedRootUser() {", method + "\n    public void seedRootUser() {", 1)
wr(rel, t)

# ---------------- 2) Ledger CSS: sticky covered column header ----------------
rel='erp-frontend/src/pages/Ledger/LedgerPage.module.css'
t = rd(rel)
thead = (
 ".ledgerTable thead th{"
 "position:sticky;top:64px;z-index:100;"
 "background:#162a2c;color:var(--orange);"
 "font-family:'Inter',sans-serif;font-size:var(--fs-th);font-weight:900;letter-spacing:2px;text-transform:uppercase;"
 "text-align:left;padding:clamp(11px,1.5vw,18px) clamp(12px,1.8vw,20px);"
 "border-bottom:3px solid var(--orange);white-space:nowrap;user-select:none;"
 "box-shadow:0 -300px 0 0 #f2ede4;"
 "}")
t = re.sub(r"\.ledgerTable thead th\{[^}]*\}", thead, t, count=1)
if ".ledgerTable thead th:first-child" not in t:
    t += "\n.ledgerTable thead th:first-child{border-radius:var(--radius) 0 0 0;}\n.ledgerTable thead th:last-child{border-radius:0 var(--radius) 0 0;}\n"
wr(rel, t)

subprocess.run(['git','add','.'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','commit','-m','fix28: wipe all sample data (no re-seed) + sticky covered column header'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','push'],check=False,cwd=ROOT,capture_output=True)
print("Done:", *DONE, sep="\n  ")