# fix.py -- fix100: align Recovery cards to Intake panel language (decs, hover, fonts, header, 3 tones)
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

# 1. Imports: add FiPhoneCall, drop unused FiChevronUp
patch(jsxp, "import { FiSearch, FiX, FiPhone, FiMapPin, FiClock, FiChevronDown, FiChevronUp, FiUser, FiFolderPlus } from 'react-icons/fi';",
"import { FiSearch, FiX, FiPhone, FiPhoneCall, FiMapPin, FiClock, FiChevronDown, FiUser, FiFolderPlus } from 'react-icons/fi';", "imports")

# 2. Pins top on every card
patch(jsxp, "              <article key={c.id} id={'rc-' + c.id} className={`${styles.rowCard} ${isOpen ? styles.rowOpen : ''}`}>",
"""              <article key={c.id} id={'rc-' + c.id} className={`${styles.rowCard} ${isOpen ? styles.rowOpen : ''}`}>
                <span className={styles.pinsTop} aria-hidden="true"><i /><i /><i /><i /></span>""", "pinsTop")

# 3. Header restructure: identity left, meta right, chevron last
patch(jsxp, """                <button type="button" className={styles.rowHead} onClick={() => setOpenId(isOpen ? null : c.id)} aria-expanded={isOpen}>
                  <span className={`${styles.callPos} ${styles['qp_' + tab]}`}>{c.position ? tab + ' #' + c.position + '/' + c.queueTotal : tab}</span>
                  <span className={styles.cname}>{c.name || c.nin || 'UNKNOWN CLIENT'}</span>
                  <span className={c.payBadge === 'GREEN' ? styles.payDotGreen : c.payBadge === 'YELLOW' ? styles.payDotYellow : styles.payDotRed} title={c.payBadge === 'GREEN' ? 'Recent payment' : c.payBadge === 'YELLOW' ? 'Payment 2-4 weeks ago' : 'No recent payment'} />
                  {c.lastTag && (<span className={c.lastTone === 'POSITIVE' ? styles.chipPos : c.lastTone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{c.lastTag}</span>)}
                  {c.dayMiss > 0 && <span className={styles.dayChip}>day {c.dayMiss}/30</span>}
                  <span className={styles.reason}>{c.reason}</span>
                  {isOpen ? <FiChevronUp aria-hidden="true" /> : <FiChevronDown aria-hidden="true" />}
                </button>""",
"""                <button type="button" className={styles.rowHead} onClick={() => setOpenId(isOpen ? null : c.id)} aria-expanded={isOpen}>
                  <span className={styles.headerLeft}>
                    <FiPhoneCall className={styles.headIcon} aria-hidden="true" />
                    <span className={styles.cname}>{c.name || c.nin || 'UNKNOWN CLIENT'}</span>
                  </span>
                  <span className={styles.headerRight}>
                    <span className={`${styles.callPos} ${styles['qp_' + tab]}`}>{c.position ? tab + ' #' + c.position + '/' + c.queueTotal : tab}</span>
                    <span className={c.payBadge === 'GREEN' ? styles.payDotGreen : c.payBadge === 'YELLOW' ? styles.payDotYellow : styles.payDotRed} title={c.payBadge === 'GREEN' ? 'Recent payment' : c.payBadge === 'YELLOW' ? 'Payment 2-4 weeks ago' : 'No recent payment'} />
                    {c.lastTag && (<span className={c.lastTone === 'POSITIVE' ? styles.chipPos : c.lastTone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{c.lastTag}</span>)}
                    {c.dayMiss > 0 && <span className={styles.dayChip}>day {c.dayMiss}/30</span>}
                    <span className={styles.reason}>{c.reason}</span>
                    <FiChevronDown className={`${styles.chev} ${isOpen ? styles.chevOpen : ''}`} aria-hidden="true" />
                  </span>
                </button>""", "header restructure")

# 4. CSS: Intake-exact tones, header, decs, hover
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix100" not in s:
    s += """
/* fix100: Intake-exact header, tones, decs, hover */
.rowCard { background: linear-gradient(135deg, #3a5a5c 0%, #2a4a4c 50%, #213E40 100%); border: 1px solid rgba(238, 140, 58, 0.2); border-radius: 10px; overflow: visible; box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25); transition: border-color 0.3s ease, box-shadow 0.3s ease; }
.rowCard:hover { border-color: var(--orange); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); transform: none; }
.rowHead { background: #162a2c; border-radius: 9px; padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 16px); border-bottom: 1.5px solid transparent; transition: border-bottom-color 0.25s ease, border-radius 0.25s ease; }
.rowHead:hover { background: #162a2c; }
.rowHead:hover .cname { color: #fff; }
.rowOpen .rowHead { border-radius: 9px 9px 0 0; border-bottom-color: var(--orange); }
.rowHead:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }
.headerLeft { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; color: var(--orange); }
.headIcon { color: var(--orange); filter: drop-shadow(0 0 4px rgba(238, 140, 58, 0.4)); font-size: clamp(12px, 1.4vw, 16px); flex-shrink: 0; }
.cname { font-family: 'Cinzel', serif; font-size: clamp(10px, 1.3vw, 13px); font-weight: 700; color: var(--orange); letter-spacing: 2px; text-transform: uppercase; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: color 0.18s ease; }
.headerRight { display: flex; align-items: center; gap: clamp(6px, 1vw, 12px); flex-shrink: 0; }
.chev { color: rgba(255, 255, 255, 0.4); font-size: 14px; transition: transform 0.2s ease, color 0.2s ease; flex-shrink: 0; }
.chevOpen { transform: rotate(180deg); color: var(--orange); }
.pinsTop, .pinsBottom { position: absolute; display: flex; gap: 7px; left: 50%; transform: translateX(-50%); pointer-events: none; z-index: 20; }
.pinsTop { top: -3px; }
.pinsBottom { bottom: -3px; }
.pinsTop i, .pinsBottom i { width: 4px; height: 4px; border-radius: 50%; background: var(--orange); opacity: 0.75; box-shadow: 0 0 6px rgba(238, 140, 58, 0.6); }
.decorBl, .decorBr { position: absolute; width: 16px; height: 16px; border: 1.5px solid var(--orange); opacity: 0.6; }
.decorBl { bottom: 8px; left: 8px; border-right: none; border-top: none; border-radius: 0 0 0 6px; }
.decorBl::after { content: ''; position: absolute; width: 5px; height: 5px; background: white; border-radius: 50%; bottom: -3px; left: -3px; box-shadow: 0 0 6px rgba(255, 255, 255, 0.4); }
.decorBr { bottom: 8px; right: 8px; border-left: none; border-top: none; border-radius: 0 0 6px 0; }
.decorBr::after { content: ''; position: absolute; width: 5px; height: 5px; background: white; border-radius: 50%; bottom: -3px; right: -3px; box-shadow: 0 0 6px rgba(255, 255, 255, 0.4); }
.secBlock { background: rgba(255, 255, 255, 0.05); border-color: rgba(255, 255, 255, 0.08); }
.rowBody { background: transparent; }
"""
    write(cssp, s)
    print("OK fix100 css")
else:
    print("SKIP fix100 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix100: align Recovery cards to Intake panel language (decs, hover, fonts, header, 3 tones)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")