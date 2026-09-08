# fix.py -- fix90: lock Recovery styling to Ledger + Intake reference (legend, search-in-rail, rhythm, compact card buttons)
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

# 1. Move search INSIDE the sticky rail (Ledger filterBar pattern), delete separate controls row
patch(jsxp, """      <div className={styles.controls}>
        <div className={styles.searchInner}>
          <FiSearch className={styles.searchIcon} aria-hidden="true" />
          <input type="search" className={styles.searchInput} placeholder="Search name, NIN, phone, index..." value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search recovery queue" autoComplete="off" />
          {search && (<button type="button" className={styles.searchClearBtn} onClick={() => setSearch('')} aria-label="Clear search"><FiX aria-hidden="true" /></button>)}
        </div>
      </div>
      <div className={styles.stickyTabs} role="tablist" aria-label="Recovery queues">""",
"""      <div className={styles.stickyTabs} role="tablist" aria-label="Recovery queues">
        <div className={styles.tabSearch}>
          <FiSearch className={styles.searchIcon} aria-hidden="true" />
          <input type="search" className={styles.searchInput} placeholder="Search name, NIN, phone, index..." value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search recovery queue" autoComplete="off" />
          {search && (<button type="button" className={styles.searchClearBtn} onClick={() => setSearch('')} aria-label="Clear search"><FiX aria-hidden="true" /></button>)}
        </div>""", "search into sticky rail")

# 2. Compact card buttons (Ledger filter-button scale) so nothing gets cut off
patch(jsxp, """                    <div className={styles.rowActions}>
                      <HardwareButton type="button" icon={FiPhone} onClick={() => open(c)} disabled={c.state === 'LOCKED'}>OPEN CALL LOG</HardwareButton>
                      {(c.projectIds || []).length > 0 && (<a className={styles.projLink} href={'/folder/' + c.projectIds[0]}><FiFolderPlus aria-hidden="true" /> OPEN FOLDER</a>)}
                    </div>""",
"""                    <div className={styles.rowActions}>
                      <button type="button" className={styles.cardBtn} onClick={() => open(c)} disabled={c.state === 'LOCKED'}><FiPhone aria-hidden="true" /> OPEN CALL LOG</button>
                      {(c.projectIds || []).length > 0 && (<a className={styles.cardBtnLink} href={'/folder/' + c.projectIds[0]}><FiFolderPlus aria-hidden="true" /> OPEN FOLDER</a>)}
                    </div>""", "compact card buttons")

# 3. CSS: exact Ledger lock-in
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix90" not in s:
    s += """
/* fix90: locked to Ledger .legendItem / .filterBtn / .searchBlock + Intake panel rhythm */
.countsHUD { margin-bottom: 8px; }
.stickyTabs { padding: 6px clamp(12px, 2vw, 24px); gap: 8px; align-items: center; }
.tabSearch { position: relative; width: clamp(200px, 30vw, 380px); flex-shrink: 0; margin-right: 6px; }
.tabSearch .searchIcon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: rgba(26, 46, 48, 0.4); width: 13px; height: 13px; }
.tabSearch .searchInput { width: 100%; padding: 8px 30px; border-radius: 6px; border: 1.5px solid rgba(26, 46, 48, 0.15); background: #ffffff; font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 600; color: #1a2e30; }
.tabSearch .searchInput:focus { outline: 2px solid var(--orange); outline-offset: 1px; border-color: var(--orange); }
.tabSearch .searchClearBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgba(26, 46, 48, 0.4); cursor: pointer; }
.qTab { padding: 8px 14px; border-radius: 6px; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; }
.qTab:hover { background: rgba(238, 140, 58, 0.12); color: var(--orange); border-color: var(--orange); transform: none; }
.dotLegend { padding: 4px 2px 6px; gap: 14px; }
.dotLegend span { gap: 6px; font-size: 10px; font-weight: 700; letter-spacing: normal; color: rgba(26, 46, 48, 0.6); }
.dotLegend i { box-shadow: none !important; width: 8px; height: 8px; }
.list { gap: 8px; margin-top: 2px; }
.rowBody { padding: 8px 14px 12px; gap: 6px 20px; }
.rowActions { margin-top: 2px; display: flex; gap: 12px; align-items: center; }
.cardBtn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 6px; border: none; background: var(--orange); color: #1a2e30; font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; cursor: pointer; transition: background 0.15s ease; }
.cardBtn:hover:not(:disabled) { background: #f0a050; }
.cardBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.cardBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.cardBtnLink { display: inline-flex; align-items: center; gap: 6px; padding: 8px 10px; border-radius: 6px; background: none; border: none; color: var(--orange); font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; text-decoration: underline; cursor: pointer; }
.cardBtnLink:hover { color: #f0a050; }
"""
    write(cssp, s)
    print("OK fix90 css lock-in")
else:
    print("SKIP fix90 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix90: lock Recovery styling to Ledger + Intake reference (legend, search-in-rail, rhythm, compact card buttons)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")