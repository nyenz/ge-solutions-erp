# fix.py -- fix104: tighten the container flex gap (the real controller of the marked spaces) + re-assert dot glow
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = cssp.read_text(encoding="utf-8", errors="replace")
if "fix104" not in s:
    s += """
/* fix104: the marked gaps come from the container flex gap - tighten it here */
.container { gap: clamp(4px, 0.7vw, 8px); }
.pageHeader { margin: 0; }
.countsHUD { margin: 0; }
.stickyRail { margin: 0; padding: 0; }
.stickyTabs { padding: 2px 0 0 0; }
.dotLegend { margin: 0; padding: 4px 0 2px clamp(6px, 1vw, 12px); }
.list { margin: 0; }
/* re-assert Ledger double-glow on every payment dot */
.payDotGreen { box-shadow: 0 0 6px #22c55e, 0 0 2px #22c55e !important; }
.payDotYellow { box-shadow: 0 0 6px #f59e0b, 0 0 2px #f59e0b !important; }
.payDotRed { box-shadow: 0 0 6px #ef4444, 0 0 2px #ef4444 !important; }
.dotLegend i.payDotGreen { box-shadow: 0 0 6px #22c55e, 0 0 2px #22c55e !important; }
.dotLegend i.payDotYellow { box-shadow: 0 0 6px #f59e0b, 0 0 2px #f59e0b !important; }
.dotLegend i.payDotRed { box-shadow: 0 0 6px #ef4444, 0 0 2px #ef4444 !important; }
"""
    cssp.write_text(s, encoding="utf-8", newline="\n")
    print("OK fix104 css")
else:
    print("SKIP fix104 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix104: tighten container flex gap (marked spaces) + re-assert Ledger dot glow"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")