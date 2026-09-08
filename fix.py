# fix.py -- fix102: left-align page title, indent legend, remove top pins, brighter card text on darker wells, tighter vertical rhythm
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)

jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"

# 1. Remove top pins from cards entirely
patch(jsxp, "                {isOpen && (<span className={styles.pinsTop} aria-hidden=\"true\"><i /><i /><i /><i /></span>)}\n", "", "remove pinsTop")

# 2. CSS: title left, legend indent, top pins hidden, brighter text on darker wells, tighter rhythm
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix102" not in s:
    s += """
/* fix102: left title, legend indent, no top pins, brighter card text, tighter rhythm */
.pageHeader { justify-content: flex-start; margin-bottom: clamp(6px, 1vw, 10px); }
.pageHeader .headerLeft { text-align: left; align-items: flex-start; }
.pageHeader .title, .pageHeader .subtitle { text-align: left; margin: 0; }
.dotLegend { padding-left: clamp(6px, 1vw, 12px); }
.pinsTop { display: none !important; }
.countsHUD { margin-bottom: clamp(6px, 1vw, 10px); }
.stickyTabs { padding: 2px 0; }
.list { margin-top: 0; gap: 6px; }
.secBlock { background: rgba(0, 0, 0, 0.22); border-color: rgba(255, 255, 255, 0.10); }
.mono { color: rgba(255, 255, 255, 0.85); }
.loc { color: rgba(255, 255, 255, 0.8); }
.coLine { color: rgba(255, 255, 255, 0.85); }
.attemptLine { color: rgba(255, 255, 255, 0.85); }
.secLabel { color: #ffb46b; }
.nin { color: #ffb46b; }
.lockBanner { color: #fde68a; }
"""
    write(cssp, s)
    print("OK fix102 css")
else:
    print("SKIP fix102 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix102: left-align page title, indent legend, remove top pins, brighter card text on darker wells, tighter vertical rhythm"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")