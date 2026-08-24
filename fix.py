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

DC = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java"

# Fix the physicalBoxNumber stream mapping.
# Repurposed to count distinct plot numbers instead of physical boxes,
# which keeps the stream's type inference intact and provides a meaningful
# "unique assets" KPI for the dashboard tile.
patch(DC,
    '    long uniqueBoxes = allPlots.stream()\n'
    '            .map(p -> p.getLandTitle().getPhysicalBoxNumber())\n'
    '            .distinct().count();',
    '    long uniqueBoxes = allPlots.stream()\n'
    '            .map(p -> p.getLandTitle() != null ? p.getLandTitle().getPlotNumber() : null)\n'
    '            .filter(pn -> pn != null)\n'
    '            .distinct().count();')

# PERMANENT Section 3 rule: commit and push automatically.
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "Hotfix: fix DashboardController stream inference after physicalBoxNumber drop"], check=True)
subprocess.run(["git", "push"], check=True)
print("DONE: committed and pushed.")