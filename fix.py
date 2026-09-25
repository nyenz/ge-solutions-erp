import subprocess
import pathlib

DRY_RUN = True  # True = change nothing, just report what would happen

MSG = 'fix: reports top section matches prototype (drop dupe reload, data sources own panel, search field resized, dropdown restyle)'

FIXES = [
    # 1) drop unused FiRefreshCw import (RELOAD button goes away below)
    (
        "erp-frontend/src/pages/Reports/ReportStudio.jsx",
        "import { FiSearch, FiX, FiChevronDown, FiAlertCircle, FiRefreshCw } from 'react-icons/fi';",
        "import { FiSearch, FiX, FiChevronDown, FiAlertCircle } from 'react-icons/fi';",
    ),

    # 2) kill the redundant RELOAD chip (ReportHub's header REFRESH already
    #    does this via reloadToken) and pull the dataset tabs out of the
    #    SCOPE panel into their own bar above it, per prototype .segbar
    (
        "erp-frontend/src/pages/Reports/ReportStudio.jsx",
        """  return (
    <div className={styles.studio}>
      <div className={styles.scopePanel}>
        <div className={styles.panelHeadRow}>
          <span className={styles.scopeTitle}>SCOPE</span>
          <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}>
            <FiRefreshCw size={11} aria-hidden="true" /> RELOAD
          </button>
        </div>
        <div className={styles.scopeBody}>
          <div className={styles.tileRow}>
            {available.map(ds => (
              <button key={ds.key} className={ds.key === datasetKey ? styles.tileActive : styles.tile} onClick={() => setDatasetKey(ds.key)}>
                {ds.label}
                <span className={styles.tileCount}>{ds.key === datasetKey ? (loading ? '...' : rows.length) : ''}</span>
              </button>
            ))}
          </div>
          <p className={styles.hint}>{dataset?.blurb}</p>""",
        """  return (
    <div className={styles.studio}>
      <div className={styles.dsBar}>
        <div className={styles.dsRow}>
          {available.map(ds => (
            <button key={ds.key} className={ds.key === datasetKey ? styles.dsBtnOn : styles.dsBtn} onClick={() => setDatasetKey(ds.key)}>
              {ds.label}
              <span className={styles.dsCnt}>{ds.key === datasetKey ? (loading ? '...' : rows.length) : ''}</span>
            </button>
          ))}
        </div>
        <span className={styles.dsRowBadge}>{loading ? '...' : rows.length} SOURCE ROWS</span>
      </div>
      <div className={styles.scopePanel}>
        <div className={styles.panelHeadRow}>
          <span className={styles.scopeTitle}>SCOPE</span>
        </div>
        <div className={styles.scopeBody}>
          <p className={styles.hint}>{dataset?.blurb}</p>""",
    ),

    # 3) WHO/WHAT search field was wider than its row siblings (COLUMNS/SORT
    #    pick buttons) -- scale it down so proportions read closer together
    (
        "erp-frontend/src/pages/Reports/ReportStudio.module.css",
        ".entInput { height: 38px; width: clamp(180px, 22vw, 280px); padding: 0 12px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; transition: all 0.2s; }",
        ".entInput { height: 38px; width: clamp(150px, 18vw, 240px); padding: 0 12px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; transition: all 0.2s; }",
    ),

    # 4) replace the CSS class block powering the old tileRow tabs with the
    #    new dsBar/dsRow/dsBtn classes referenced by the JSX fix above
    (
        "erp-frontend/src/pages/Reports/ReportStudio.module.css",
        """.tileRow { display: flex; flex-wrap: wrap; gap: 8px; }
.tile, .tileActive {
  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;
  letter-spacing: 1.5px; text-transform: uppercase;
  padding: clamp(9px, 1.1vw, 12px) clamp(14px, 1.8vw, 22px); border-radius: 6px;
  border: 1.5px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.85); transition: all 0.2s ease;
}
.tile:hover { border-color: #EE8C3A; color: #EE8C3A; }
.tileActive { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; box-shadow: 0 4px 16px rgba(238,140,58,0.3); }
.tileCount { font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.8vw, 9px); opacity: 0.75; }""",
        """.dsBar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.dsRow {
  display: flex; overflow-x: auto; scrollbar-width: none;
  background: rgba(26,46,48,0.82); border: 1.5px solid rgba(255,255,255,0.14);
  border-radius: 8px; padding: 4px;
}
.dsRow::-webkit-scrollbar { display: none; }
.dsBtn, .dsBtnOn {
  display: flex; align-items: center; gap: 8px; white-space: nowrap; cursor: pointer;
  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;
  letter-spacing: 1.5px; text-transform: uppercase;
  padding: clamp(8px, 1vw, 10px) clamp(14px, 1.8vw, 22px); border-radius: 6px; border: none;
  background: transparent; color: rgba(255,255,255,0.8); transition: all 0.2s ease;
}
.dsBtn:hover { color: #EE8C3A; background: rgba(238,140,58,0.12); }
.dsBtnOn { background: #EE8C3A; color: #1a2e30; }
.dsCnt { font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.8vw, 9px); opacity: 0.75; }
.dsRowBadge {
  margin-left: auto; color: rgba(26,46,48,0.6); background: rgba(255,255,255,0.6);
  border: 1px solid rgba(26,46,48,0.2); border-radius: 20px; padding: 6px 14px;
  font-size: clamp(8px, 0.85vw, 10px); font-weight: 900; letter-spacing: 1px; font-family: 'Space Mono', monospace;
}""",
    ),

    # 5) dropdown menus (columns/sort/who-what/chart) used a thick orange
    #    border + tinted-highlight rows -- prototype's .ddList/.ddOpt uses a
    #    thin edge border and a solid-orange full-row hover/active state
    (
        "erp-frontend/src/pages/Reports/ReportStudio.module.css",
        """.pickList {
  position: absolute; top: calc(100% + 4px); left: 0; z-index: 60;
  width: max-content; min-width: 100%; max-width: 340px;
  background: #fff; border: 2px solid #EE8C3A; border-radius: 8px;
  box-shadow: 0 18px 40px rgba(26,46,48,0.28); overflow: hidden;
}
.ddScroll { max-height: 264px; overflow-y: auto; padding: 4px; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }
.ddScroll::-webkit-scrollbar { width: 6px; }
.ddScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }
.pickOption {
  display: flex; width: 100%; text-align: left; border: none; border-left: 3px solid transparent;
  border-radius: 4px; background: transparent; color: #1a2e30;
  font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; padding: 8px 10px; cursor: pointer;
}
.pickOption:hover { background: rgba(238,140,58,0.12); }
.pickOptionActive { background: rgba(238,140,58,0.16); border-left-color: #EE8C3A; color: #b45309; }
.pickCheck {
  display: flex; align-items: center; gap: 9px; width: 100%; text-align: left;
  border: none; border-left: 3px solid transparent; border-radius: 4px; background: transparent;
  color: #1a2e30; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700;
  padding: 8px 10px; cursor: pointer;
}
.pickCheck:hover { background: rgba(238,140,58,0.12); }
.pickCheckOn { background: rgba(238,140,58,0.16); border-left-color: #EE8C3A; color: #b45309; }
.pickCheck input { accent-color: #EE8C3A; width: 15px; height: 15px; cursor: pointer; flex-shrink: 0; }""",
        """.pickList {
  position: absolute; top: calc(100% + 4px); left: 0; z-index: 60;
  width: max-content; min-width: 100%; max-width: 360px;
  background: #fff; border: 1px solid #dfd9d1; border-radius: 8px;
  box-shadow: 0 16px 40px rgba(26,46,48,0.25); overflow: hidden;
}
.ddScroll { max-height: 270px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }
.ddScroll::-webkit-scrollbar { width: 6px; }
.ddScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }
.pickOption {
  display: flex; align-items: center; gap: 9px; width: 100%; text-align: left; border: none;
  border-bottom: 1px solid #f1eeea; background: #fff; color: #1a2e30;
  font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; padding: 10px 12px; cursor: pointer; transition: background 0.15s;
}
.pickOption:last-child { border-bottom: none; }
.pickOption:hover, .pickOptionActive { background: #EE8C3A; color: #fff; }
.pickCheck {
  display: flex; align-items: center; gap: 9px; width: 100%; text-align: left;
  border: none; border-bottom: 1px solid #f1eeea; background: #fff;
  color: #1a2e30; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700;
  padding: 10px 12px; cursor: pointer; transition: background 0.15s;
}
.pickCheck:last-child { border-bottom: none; }
.pickCheck:hover, .pickCheckOn { background: #EE8C3A; color: #fff; }
.pickCheck input { accent-color: #EE8C3A; width: 15px; height: 15px; cursor: pointer; flex-shrink: 0; }
.pickCheckOn input { accent-color: #fff; }""",
    ),
]

print("fix.py: start")
print("DRY_RUN:", DRY_RUN)
print("fix count:", len(FIXES))

for path, old, new in FIXES:
    p = pathlib.Path(path)

    if not p.exists():
        print("missing:", path)
        continue

    txt = p.read_text(encoding="utf-8")

    if old not in txt:
        print("not found:", path)
        continue

    print("would fix:", path)

    if not DRY_RUN:
        p.write_text(txt.replace(old, new, 1), encoding="utf-8")

if DRY_RUN:
    print("fix.py: dry run only, nothing changed")
    print("git commands skipped")
else:
    print('')
    print('git: staging, committing, pushing...')
    subprocess.run(['git', 'add', '-A'])
    subprocess.run(['git', 'commit', '-m', MSG])
    subprocess.run(['git', 'push'])