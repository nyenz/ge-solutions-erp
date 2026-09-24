import os
import sys
import subprocess

ROOT = os.getcwd()
frontend = os.path.join(ROOT, 'erp-frontend', 'src', 'pages', 'Reports')

print("=" * 72)
print(" GOLDEN SEED fix79a -- STAGE 2 of 3: scope bar + catalogue UI")
print("=" * 72)

# 1. Delete ExpenseAnalysis files
for f in ['ExpenseAnalysis.jsx', 'ExpenseAnalysis.module.css']:
    p = os.path.join(frontend, f)
    if os.path.exists(p):
        os.remove(p)
        print(f"OK      delete {f}")
    else:
        print(f"MISSING {f} (already gone)")

# 2. Rewrite ReportHub.jsx
hub_lines = [
    "import React from 'react';",
    "import ReportStudio from './ReportStudio';",
    "import styles from './ReportHub.module.css';",
    "",
    "export default function ReportHub() {",
    "  return (",
    "    <div className={styles.container}>",
    "      <header className={styles.pageHeader}>",
    "        <div className={styles.headerLeft}>",
    "          <h1 className={styles.pageTitle}>Report Studio</h1>",
    "          <p className={styles.pageSubtitle}>Build, view and export company intelligence</p>",
    "        </div>",
    "      </header>",
    "      <ReportStudio />",
    "    </div>",
    "  );",
    "}"
]
with open(os.path.join(frontend, 'ReportHub.jsx'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(hub_lines))
print("OK      rewrite ReportHub.jsx (no tabs, pure shell)")

# 3. Rewrite ReportStudio.jsx
studio_lines = [
    "import React, { useState, useMemo } from 'react';",
    "import { FiDatabase, FiFilter, FiBarChart2, FiDownload, FiTable } from 'react-icons/fi';",
    "import { CATALOGUE, ENTITIES } from './reportsCatalog';",
    "import styles from './ReportStudio.module.css';",
    "",
    "export default function ReportStudio() {",
    "  const [scope, setScope] = useState('PROJECTS');",
    "  const [activeReport, setActiveReport] = useState(null);",
    "  ",
    "  const scopeReports = useMemo(() => CATALOGUE.filter(r => r.entity === scope), [scope]);",
    "  ",
    "  const handleSelectReport = (report) => {",
    "    setActiveReport(report);",
    "  };",
    "",
    "  return (",
    "    <div className={styles.studio}>",
    "      <div className={styles.scopeBar}>",
    "        {ENTITIES.map(e => (",
    "          <button ",
    "            key={e} ",
    "            className={`${styles.scopeBtn} ${scope === e ? styles.scopeBtnActive : ''}`}",
    "            onClick={() => { setScope(e); setActiveReport(null); }}",
    "          >",
    "            {e}",
    "          </button>",
    "        ))}",
    "      </div>",
    "",
    "      <div className={styles.catalogue}>",
    "        <h2 className={styles.catalogueTitle}>{scope} REPORTS</h2>",
    "        <div className={styles.catalogueGrid}>",
    "          {scopeReports.map(r => (",
    "            <button ",
    "              key={r.id} ",
    "              className={`${styles.catalogueCard} ${activeReport?.id === r.id ? styles.catalogueCardActive : ''}`}",
    "              onClick={() => handleSelectReport(r)}",
    "            >",
    "              <span className={styles.cardTitle}>{r.name}</span>",
    "              <span className={styles.cardDesc}>{r.desc}</span>",
    "            </button>",
    "          ))}",
    "        </div>",
    "      </div>",
    "",
    "      {activeReport && (",
    "        <div className={styles.builderArea}>",
    "          <div className={styles.builderPanel}>",
    "             <h3>BUILDER: {activeReport.name}</h3>",
    "             <p className={styles.builderHint}>Select fields and filters to generate results.</p>",
    "          </div>",
    "          <div className={styles.resultsPanel}>",
    "             <h3>RESULTS</h3>",
    "             <p className={styles.resultsHint}>Chart and table will render here in Stage 3.</p>",
    "          </div>",
    "        </div>",
    "      )}",
    "    </div>",
    "  );",
    "}"
]
with open(os.path.join(frontend, 'ReportStudio.jsx'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(studio_lines))
print("OK      rewrite ReportStudio.jsx (scope bar + catalogue)")

# 4. Append/Update ReportStudio.module.css
css_lines = [
    "",
    "/* === fix79a STAGE 2: SCOPE BAR + CATALOGUE === */",
    ".studio { display: flex; flex-direction: column; gap: clamp(16px, 2vw, 24px); }",
    ".scopeBar { display: flex; gap: clamp(8px, 1vw, 12px); flex-wrap: wrap; }",
    ".scopeBtn {",
    "  background: rgba(26, 46, 48, 0.75); border: 1.5px solid rgba(255, 255, 255, 0.18);",
    "  color: rgba(255, 255, 255, 0.85); padding: clamp(8px, 1vw, 10px) clamp(14px, 1.8vw, 20px);",
    "  border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif; font-weight: 900;",
    "  font-size: clamp(9px, 0.95vw, 11px); letter-spacing: 1.5px; text-transform: uppercase;",
    "  cursor: pointer; transition: all 0.2s ease; white-space: nowrap;",
    "}",
    ".scopeBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }",
    ".scopeBtnActive {",
    "  background: #EE8C3A !important; color: #1a2e30 !important;",
    "  border-color: #EE8C3A !important; box-shadow: 0 0 12px rgba(238, 140, 58, 0.35);",
    "}",
    ".catalogueTitle {",
    "  font-family: 'Cinzel', serif; color: var(--orange); font-size: clamp(14px, 1.6vw, 18px);",
    "  font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: clamp(8px, 1vw, 12px);",
    "}",
    ".catalogueGrid {",
    "  display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 280px), 1fr));",
    "  gap: clamp(12px, 1.5vw, 18px);",
    "}",
    ".catalogueCard {",
    "  background: var(--panel-bg); border: 1.5px solid var(--panel-border); border-radius: var(--radius);",
    "  padding: clamp(14px, 1.8vw, 20px); display: flex; flex-direction: column; gap: clamp(6px, 0.8vw, 10px);",
    "  text-align: left; cursor: pointer; transition: all 0.2s ease;",
    "}",
    ".catalogueCard:hover { border-color: var(--orange); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.2); }",
    ".catalogueCardActive { border-color: var(--orange) !important; box-shadow: 0 0 16px rgba(238, 140, 58, 0.4) !important; }",
    ".cardTitle {",
    "  font-family: 'DM Sans', sans-serif; font-size: clamp(12px, 1.3vw, 15px); font-weight: 900;",
    "  color: #fff; text-transform: uppercase; letter-spacing: 0.5px;",
    "}",
    ".cardDesc {",
    "  font-family: 'Inter', sans-serif; font-size: clamp(10px, 1.1vw, 12px); font-weight: 500;",
    "  color: rgba(255, 255, 255, 0.6); line-height: 1.5;",
    "}",
    ".builderArea { display: grid; grid-template-columns: 1fr 1.5fr; gap: clamp(16px, 2vw, 24px); }",
    ".builderPanel, .resultsPanel {",
    "  background: var(--panel-bg); border: 1.5px solid var(--panel-border); border-radius: var(--radius);",
    "  padding: clamp(16px, 2vw, 24px);",
    "}",
    ".builderPanel h3, .resultsPanel h3 {",
    "  font-family: 'Cinzel', serif; color: var(--orange); font-size: clamp(12px, 1.4vw, 16px);",
    "  font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: clamp(10px, 1.2vw, 16px);",
    "}",
    ".builderHint, .resultsHint {",
    "  font-family: 'Inter', sans-serif; font-size: clamp(11px, 1.2vw, 13px); color: rgba(255,255,255,0.5);",
    "}",
    "@media (max-width: 900px) {",
    "  .builderArea { grid-template-columns: 1fr; }",
    "}"
]
with open(os.path.join(frontend, 'ReportStudio.module.css'), 'a', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(css_lines))
print("OK      append ReportStudio.module.css")

# 5. Addendum
addendum_path = os.path.join(ROOT, 'LLM_CONTEXT_ADDENDUM.md')
addendum_text = "\n- fix79a-stage2 (2026-09-24): Reports UI rebuilt as scope bar + catalogue. Tabs and 12 server pillars retired. ExpenseAnalysis deleted. ReportHub is now a pure shell. ReportStudio shows ENTITIES scope bar, 40 standing reports catalogue, and placeholder builder/results panels for Stage 3.\n"
with open(addendum_path, 'a', encoding='utf-8', newline='\n') as f:
    f.write(addendum_text)
print("OK      addendum appended")

print("\nAll files written.")
print("\n(erp-frontend/node_modules not installed -- skipping build check)\n")

print("git: staging, committing, pushing...")
MSG = "fix79a stage2: scope bar + catalogue UI (tabs retired, ExpenseAnalysis deleted)"
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])

print("\nStage 2 done. Wait for the green tick, then say go for stage 3 (builder + results viewer).")