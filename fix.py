# fix.py -- fix101: left-aligned one-line card header, rail margin lock, left grouped Intake-proportion buttons, deco only when open, tone fix
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

# 1. Card header gets its own row-layout class (icon + name, one line, left)
patch(jsxp, """                  <span className={styles.headerLeft}>
                    <FiPhoneCall className={styles.headIcon} aria-hidden="true" />
                    <span className={styles.cname}>{c.name || c.nin || 'UNKNOWN CLIENT'}</span>
                  </span>""",
"""                  <span className={styles.cardHeadLeft}>
                    <FiPhoneCall className={styles.headIcon} aria-hidden="true" />
                    <span className={styles.cname}>{c.name || c.nin || 'UNKNOWN CLIENT'}</span>
                  </span>""", "card header row class")

# 2. Top pins only when expanded
patch(jsxp, "                <span className={styles.pinsTop} aria-hidden=\"true\"><i /><i /><i /><i /></span>",
"                {isOpen && (<span className={styles.pinsTop} aria-hidden=\"true\"><i /><i /><i /><i /></span>)}", "pinsTop only when open")

# 3. Bottom pins + corner brackets only when expanded
patch(jsxp, """                <span className={styles.pinsBottom} aria-hidden="true"><i /><i /><i /><i /></span>
                <span className={styles.decorBl} aria-hidden="true" />
                <span className={styles.decorBr} aria-hidden="true" />""",
"""                {isOpen && (<>
                  <span className={styles.pinsBottom} aria-hidden="true"><i /><i /><i /><i /></span>
                  <span className={styles.decorBl} aria-hidden="true" />
                  <span className={styles.decorBr} aria-hidden="true" />
                </>)}""", "bottom deco only when open")

# 4. CSS: alignment lock, left-aligned header, tones, Intake button proportions
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix101" not in s:
    s += """
/* fix101: alignment lock + left one-line header + tones + Intake button proportions */
.stickyRail { margin: 0 !important; padding: 0 !important; }
.stickyTabs { margin: 0 !important; padding: 4px 0 !important; }
.tabSearch { margin: 0; }
.list, .rowCard { margin-left: 0; margin-right: 0; }
.cardHeadLeft { display: flex; flex-direction: row; align-items: center; gap: 8px; flex: 1; min-width: 0; text-align: left; }
.cname { text-align: left; }
.rowHead { background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%); text-align: left; }
.rowOpen .rowHead { background: #162a2c; }
.rowActions { justify-content: flex-start; gap: 8px; }
.cardBtn, .cardBtn2 { height: clamp(34px, 4vw, 40px); padding: 0 clamp(12px, 1.5vw, 18px); font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; }
.cardBtn2 { margin-left: 0; }
"""
    write(cssp, s)
    print("OK fix101 css")
else:
    print("SKIP fix101 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix101: left-aligned one-line card header, rail margin lock, left grouped Intake-proportion buttons, deco only when open, tone fix"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")