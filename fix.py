# fix.py -- fix99: Intake-matched tones, hover, pins+corner deco, plain colored position badges, aligned rail
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

# 1. Position badge: plain colored words per queue type (no bg/border)
patch(jsxp, "<span className={styles.callPos}>{c.position ? tab + ' #' + c.position + '/' + c.queueTotal : tab}</span>",
"<span className={`${styles.callPos} ${styles['qp_' + tab]}`}>{c.position ? tab + ' #' + c.position + '/' + c.queueTotal : tab}</span>", "colored plain position badge")

# 2. Move corner deco out of expanded body + add bottom pins to every card
patch(jsxp, """                    <span className={styles.decorBl} aria-hidden="true" />
                    <span className={styles.decorBr} aria-hidden="true" />
                  </div>
                )}
              </article>""",
"""                  </div>
                )}
                <span className={styles.pinsBottom} aria-hidden="true"><i /><i /><i /><i /></span>
                <span className={styles.decorBl} aria-hidden="true" />
                <span className={styles.decorBr} aria-hidden="true" />
              </article>""", "pins + corner deco on every card")

# 3. CSS: tones, hover, deco, badge colors, alignment
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix99" not in s:
    s += """
/* fix99: Intake-matched tones, hover, pins+corner deco, plain colored position badges, aligned rail */
.stickyRail, .countsHUD, .list { margin-left: 0; margin-right: 0; padding-left: 0; padding-right: 0; width: 100%; }
.rowCard { background: linear-gradient(160deg, #1c3335 0%, #213E40 100%); transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s; }
.rowCard:hover { border-color: rgba(238, 140, 58, 0.5); transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25); }
.rowHead { background: rgba(0, 0, 0, 0.22); }
.rowHead:hover { background: rgba(0, 0, 0, 0.3); }
.rowOpen .rowHead { background: rgba(0, 0, 0, 0.28); border-bottom: 1.5px solid var(--orange); }
.rowBody { background: transparent; }
.secBlock { background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.08); }
.pinsBottom { position: absolute; bottom: 4px; left: 50%; transform: translateX(-50%); display: flex; gap: 6px; pointer-events: none; }
.pinsBottom i { width: 4px; height: 4px; border-radius: 50%; background: var(--orange); opacity: 0.7; box-shadow: 0 0 4px rgba(238, 140, 58, 0.6); }
.decorBl, .decorBr { position: absolute; bottom: 6px; width: 14px; height: 14px; pointer-events: none; opacity: 0.6; }
.decorBl { left: 8px; border-left: 1.5px solid var(--orange); border-bottom: 1.5px solid var(--orange); border-right: none; border-top: none; }
.decorBr { right: 8px; border-right: 1.5px solid var(--orange); border-bottom: 1.5px solid var(--orange); border-left: none; border-top: none; }
.callPos { background: none !important; border: none !important; padding: 0 !important; border-radius: 0; font-family: 'Space Mono', monospace; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1px; text-transform: uppercase; }
.qp_ALL { color: #67e8f9; }
.qp_CONTACTED { color: #34d399; }
.qp_MISSED { color: #fca5a5; }
.qp_SITE { color: #fcd34d; }
.qp_LOCKED { color: #c4b5fd; }
"""
    write(cssp, s)
    print("OK fix99 css")
else:
    print("SKIP fix99 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix99: Intake-matched tones, hover, pins+corner deco, plain colored position badges, aligned rail"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")