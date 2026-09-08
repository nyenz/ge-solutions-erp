# fix.py -- fix92: plain back-to-top arrow, tight rail rhythm, aligned search margin, sticky scrollable legend, hidden modal scrollbar, white history panel
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
def append(p, marker, block, label):
    s = read(p)
    if marker not in s:
        write(p, s + block); print("OK", label)
    else:
        print("SKIP", label)

jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"

# 1. Wrap rail + legend in one sticky wrapper
patch(jsxp, '      <div className={styles.stickyTabs} role="tablist" aria-label="Recovery queues">',
'      <div className={styles.stickyRail}>\n      <div className={styles.stickyTabs} role="tablist" aria-label="Recovery queues">', "open stickyRail")
patch(jsxp, """        <span><i className={styles.payDotRed} /> No recent payment</span>
      </div>""",
"""        <span><i className={styles.payDotRed} /> No recent payment</span>
      </div>
      </div>""", "close stickyRail after legend")

# 2. Recovery CSS: rhythm, alignment, sticky scrollable legend, white history panel
append(FE / "pages" / "Recovery" / "RecoveryPortal.module.css", "fix92", """
/* fix92: tight rhythm + Ledger-exact rail alignment + sticky scrollable legend + white history */
.countsHUD { margin-bottom: 4px; }
.stickyRail { position: sticky; top: 0; z-index: 200; background: transparent; margin-left: clamp(-12px, -2vw, -24px); margin-right: clamp(-12px, -2vw, -24px); padding-left: clamp(12px, 2vw, 24px); padding-right: clamp(12px, 2vw, 24px); }
.stickyTabs { position: static; padding: 4px 0; gap: 8px; align-items: center; }
.dotLegend { display: flex; flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; padding: 2px 0 4px; gap: 14px; }
.dotLegend::-webkit-scrollbar { display: none; }
.list { margin-top: 0; }
.rowHead svg { background: none; border: none; box-shadow: none; }
.histSection { background: #ffffff; border: 1px solid #cccccc; border-radius: 6px; padding: 10px 12px; }
.histSection .wallLabel { color: rgba(26, 46, 48, 0.6); }
.histSection .histMeta { color: #64748b; }
.histSection .histText { color: #333333; }
.histSection .chipPos { color: #047857; }
.histSection .chipNeg { color: #b91c1c; }
.histSection .chipNone { color: #64748b; }
.histSection .histDelete { color: #b91c1c; }
.histRow { border-bottom: 1px solid #eeeeee; padding: 6px 0; }
.histRow:last-child { border-bottom: none; }
""", "recovery fix92 css")

# 3. Modal: hide scrollbar but keep scrolling
append(FE / "components" / "common" / "HardwareModal.module.css", "fix92", """
/* fix92: popup keeps scrolling but shows no scrollbar */
.modalBody, [class*="modalBody"] { scrollbar-width: none; }
.modalBody::-webkit-scrollbar, [class*="modalBody"]::-webkit-scrollbar { display: none; }
""", "modal hidden scrollbar")

# 4. Back-to-top arrow: plain, bottom-right, never on a badge
append(FE / "index.css", "fix92", """
/* fix92: back-to-top arrow is a plain glyph pinned bottom-right */
[class*="backToTop"], [class*="BackToTop"], [class*="toTop"] {
  position: fixed !important;
  right: clamp(12px, 2vw, 24px) !important;
  bottom: clamp(12px, 2vw, 24px) !important;
  left: auto !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
""", "global plain back-to-top")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix92: plain back-to-top arrow, tight rail rhythm, aligned search margin, sticky scrollable legend, hidden modal scrollbar, white history panel"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")