import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

DC = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java"

changed = False

if not os.path.exists(DC):
    print("MISSING FILE: " + DC)
else:
    with open(DC, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Indentation-independent match of the dead getter call inside the stream.
    pattern = re.compile(r"\.map\(\s*p\s*->\s*p\.getLandTitle\(\)\.getPhysicalBoxNumber\(\)\s*\)")
    replacement = (".map(p -> p.getLandTitle() != null ? p.getLandTitle().getPlotNumber() : null)"
                   ".filter(pb -> pb != null)")

    new_content, n = pattern.subn(replacement, content)
    if n > 0:
        with open(DC, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)
        changed = True
        print("OK: " + DC + " (" + str(n) + " replacement(s))")
    else:
        print("MISSING ANCHOR in " + DC + ": .map(p -> p.getLandTitle().getPhysicalBoxNumber())")

# Safety net: report any remaining physicalBoxNumber reference in main sources.
for root, dirs, files in os.walk("erp-backend/src/main"):
    for name in files:
        if name.endswith(".java"):
            p = os.path.join(root, name)
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                c = f.read()
            if "physicalboxnumber" in c.lower():
                print("WARNING still references physicalBoxNumber: " + p)

# PERMANENT Section 3 rule: commit and push automatically as the last step.
subprocess.run(["git", "add", "-A"], check=True)
r = subprocess.run(["git", "commit", "-m", "Hotfix: null-safe plot-number stream in DashboardController (physicalBoxNumber drop)"])
if r.returncode == 0:
    subprocess.run(["git", "push"], check=True)
    print("DONE: committed and pushed.")
else:
    print("NOTHING TO COMMIT: no changes were needed.")