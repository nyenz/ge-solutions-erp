# fix.py -- fix98: force expanded card sections full-width (kill leftover grid centering)
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = cssp.read_text(encoding="utf-8", errors="replace")
if "fix98" not in s:
    s += """
/* fix98: expanded card sections full-width, left-aligned (kill leftover grid centering) */
.rowBody { display: flex !important; flex-direction: column !important; align-items: stretch !important; grid-template-columns: none !important; }
.rowBody > * { width: 100%; box-sizing: border-box; }
.secBlock { width: 100%; box-sizing: border-box; align-items: flex-start; }
.secBlock > * { max-width: 100%; }
.rowActions { width: 100%; }
"""
    cssp.write_text(s, encoding="utf-8", newline="\n")
    print("OK fix98 css")
else:
    print("SKIP fix98 already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix98: force expanded card sections full-width"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")