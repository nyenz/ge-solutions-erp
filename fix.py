# fix.py -- fix93: single scrollbar (page scrolls the cards) + legend pinned inside sticky rail
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)

jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
s = read(jsxp)
if 'styles.stickyRail' not in s:
    i_tabs = s.find('<div className={styles.stickyTabs}')
    if i_tabs >= 0:
        s = s[:i_tabs] + '<div className={styles.stickyRail}>\n      ' + s[i_tabs:]
        j = s.find('No recent payment</span>')
        if j >= 0:
            k = s.find('</div>', j)
            if k >= 0:
                k2 = k + len('</div>')
                s = s[:k2] + '\n      </div>' + s[k2:]
                write(jsxp, s)
                print("OK rail wrap (search+tabs+legend pinned together)")
            else:
                print("MISSING legend closing div")
        else:
            print("MISSING legend anchor")
    else:
        print("MISSING stickyTabs anchor")
else:
    print("SKIP rail already wrapped")

cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
c = read(cssp)
if "fix93" not in c:
    c += """
/* fix93: ONE scrollbar only - page scroll moves the cards; rail pins search+tabs+legend */
.stickyRail { position: sticky; top: 0; z-index: 200; background: transparent; margin-left: clamp(-12px, -2vw, -24px); margin-right: clamp(-12px, -2vw, -24px); padding-left: clamp(12px, 2vw, 24px); padding-right: clamp(12px, 2vw, 24px); }
.stickyTabs { position: static; padding: 4px 0; gap: 8px; align-items: center; background: transparent; border-bottom: none; }
.dotLegend { display: flex; flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; padding: 2px 0 4px; gap: 14px; }
.dotLegend::-webkit-scrollbar { display: none; }
.list { max-height: none !important; overflow: visible !important; margin-top: 2px; gap: 8px; }
.list::-webkit-scrollbar { display: none; width: 0; height: 0; }
.countsHUD { margin-bottom: 4px; }
"""
    write(cssp, c)
    print("OK fix93 css")
else:
    print("SKIP fix93 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix93: single scrollbar (page scrolls cards) + legend pinned inside sticky rail"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")