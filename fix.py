# fix.py -- fix88: unify legend style, badge standard, and vertical rhythm with Ledger reference
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)

# 1. Recovery page: legend + badges + HUD labels match Ledger standard
rc = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(rc)
if "fix88" not in s:
    s += """
/* fix88: dot legend matches Ledger .legendItem exactly (sentence case, plain spacing) */
.dotLegend span { font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: normal; text-transform: none; color: rgba(26, 46, 48, 0.6); }
/* fix88: outcome badges use the app-wide underline badge standard (same family/size as Ledger textBadge) */
.chipPos, .chipNeg, .chipNone { background: none; border: none; border-bottom: 1px solid currentColor; border-radius: 0; padding: 2px 0; font-family: 'Space Mono', monospace; font-size: 10px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; white-space: nowrap; }
.chipPos { color: #34d399; }
.chipNeg { color: #fca5a5; }
.chipNone { color: rgba(255, 255, 255, 0.5); }
/* fix88: HUD tile labels match Ledger statLabel rhythm */
.countCard label { letter-spacing: 2px; color: rgba(255, 255, 255, 0.4); }
"""
    write(rc, s)
    print("OK recovery legend/badge/label unification")
else:
    print("SKIP recovery css already has fix88")

# 2. Ledger page: standard gap between legend row and table
lc = FE / "pages" / "Ledger" / "LedgerPage.module.css"
s2 = read(lc)
if "fix88" not in s2:
    s2 += """
/* fix88: standard vertical rhythm - legend breathes before the table */
.legendRow { margin-bottom: clamp(10px, 1.2vw, 14px); }
"""
    write(lc, s2)
    print("OK ledger rhythm")
else:
    print("SKIP ledger css already has fix88")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix88: unify legend style, badge standard, and vertical rhythm with Ledger reference"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")