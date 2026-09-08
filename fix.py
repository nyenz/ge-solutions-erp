# fix.py -- fix103: tighten the three marked vertical gaps + restore Ledger double-glow on all payment dots
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = cssp.read_text(encoding="utf-8", errors="replace")
if "fix103" not in s:
    s += """
/* fix103: tight rhythm on the three marked gaps + Ledger double-glow dots */
.pageHeader { margin-bottom: clamp(4px, 0.6vw, 6px); }
.countsHUD { margin-bottom: clamp(4px, 0.6vw, 6px); }
.stickyTabs { padding: 2px 0 0 0; }
.dotLegend { padding: 4px 0 4px clamp(6px, 1vw, 12px); margin: 0; }
.list { margin-top: 4px; }
.payDotGreen { box-shadow: 0 0 6px #22c55e, 0 0 2px #22c55e !important; }
.payDotYellow { box-shadow: 0 0 6px #f59e0b, 0 0 2px #f59e0b !important; }
.payDotRed { box-shadow: 0 0 6px #ef4444, 0 0 2px #ef4444 !important; }
.dotLegend i.payDotGreen { box-shadow: 0 0 6px #22c55e, 0 0 2px #22c55e !important; }
.dotLegend i.payDotYellow { box-shadow: 0 0 6px #f59e0b, 0 0 2px #f59e0b !important; }
.dotLegend i.payDotRed { box-shadow: 0 0 6px #ef4444, 0 0 2px #ef4444 !important; }
"""
    cssp.write_text(s, encoding="utf-8", newline="\n")
    print("OK fix103 css")
else:
    print("SKIP fix103 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix103: tighten marked vertical gaps + restore Ledger double-glow on payment dots"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")