# fix.py -- fix121: inconsistency sweep (racing chips effect, restore confirm, icon/tone fixes, dead code)
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"


try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix121: inconsistency sweep - single recovery chips effect, restore-defaults confirm, mail icon + tone dot fixes, dead code removal"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")