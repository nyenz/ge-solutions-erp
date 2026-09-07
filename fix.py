# fix.py -- fix82: recovery type scale, invisible sticky filter bar, payment dot legend
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

cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"

# 1. Filter bar: page-colour bg (looks invisible), stick at very top, full-bleed so cards hide behind it
patch(cssp,
".stickyTabs { position: sticky; top: 64px; z-index: 40; display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding: 8px 0; background: var(--bg, #f4efe8); }",
".stickyTabs { position: sticky; top: 0; z-index: 200; display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding: 10px clamp(12px, 2vw, 24px); background: #f4efe8; margin-left: clamp(-12px, -2vw, -24px); margin-right: clamp(-12px, -2vw, -24px); border-bottom: 1px solid rgba(26, 46, 48, 0.08); }",
"sticky bar invisible + top + full-bleed")

# 2. Unified type scale + dot legend styles
s = read(cssp)
if ".dotLegend" not in s:
    s += """
.dotLegend { display: flex; gap: clamp(10px, 1.4vw, 16px); flex-wrap: wrap; align-items: center; padding: 8px 2px 2px; }
.dotLegend span { display: inline-flex; align-items: center; gap: 6px; font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.9vw, 10px); font-weight: 700; color: rgba(26, 46, 48, 0.55); text-transform: uppercase; letter-spacing: 0.6px; }
.dotLegend i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
/* fix82: unified type scale - 3 text sizes + HUD display number only */
.cname { font-size: clamp(13px, 1.6vw, 16px); }
.nin, .mono, .loc, .coLine, .attemptLine, .histText, .lockBanner, .projLink { font-size: clamp(10px, 1.1vw, 12px); }
.callPos, .reason, .dayChip, .chipPos, .chipNeg, .chipNone, .wallLabel, .histMeta, .qTab, .countCard label { font-size: clamp(8px, 0.9vw, 10px); }
.countCard strong { font-size: clamp(15px, 1.8vw, 21px); }
"""
    write(cssp, s)
    print("OK type scale + legend css")
else:
    print("SKIP legend css already present")

# 3. Payment dot legend row (not sticky, scrolls away)
patch(jsxp,
"""        ))}
      </div>
      {loading ? (""",
"""        ))}
      </div>
      <div className={styles.dotLegend} aria-label="Payment dot legend">
        <span><i style={{ background: '#22c55e' }} /> paid in last 14 days</span>
        <span><i style={{ background: '#f59e0b' }} /> paid 15-30 days ago</span>
        <span><i style={{ background: '#ef4444' }} /> over 30 days or never</span>
      </div>
      {loading ? (""",
"dot legend row under filters")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix82: recovery type scale, invisible sticky filter bar, payment dot legend"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")