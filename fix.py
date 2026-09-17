#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP -- fix78 PATCHER
================================================================================
 WHAT:
   1. DATASETS panel de-cluttered: presets and one-click CSV become two
      dropdowns on one row (CSV list carries group section headers inside).
      Dataset stays tiles, never a dropdown.
   2. Open dropdown lists restyled to the Intake white-control language.
   3. Hairline section separators inside panels.
   4. Save-view feature removed entirely (UI + state + functions).
   5. ANALYSIS tab = pure read-out of the REPORTS tab's current selection:
      one studio instance backs both tabs; analysis shows stat cards, chart
      and grouped table from the same state, with no settings of its own.
   6. Presets carry full column sets (index, sub-county, village, phone...).
   7. CollapsibleSection body gradient softened one notch app-wide.
 HOW: run  py fix.py  from the project root. Build-checks, commits, pushes.
================================================================================
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

STU    = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
STUCSS = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')
HUB    = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.jsx')
COLCSS = os.path.join('erp-frontend', 'src', 'components', 'ui', 'CollapsibleSection.module.css')
ADD    = 'LLM_CONTEXT_ADDENDUM.md'

BUF = {}


def get(rel):
    if rel not in BUF:
        with open(os.path.join(ROOT, rel), 'r', encoding='utf-8', errors='replace') as f:
            BUF[rel] = f.read()
    return BUF[rel]


def save(rel):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8', newline='\n') as f:
        f.write(BUF[rel])


def patch(rel, old, new, tag):
    s = get(rel)
    if old in s:
        BUF[rel] = s.replace(old, new, 1)
        print('OK      ' + tag)
    else:
        print('MISSING ' + tag)


def rpatch(rel, pat, new, tag):
    s = get(rel)
    out, n = re.subn(pat, new, s, count=1)
    if n:
        BUF[rel] = out
        print('OK      ' + tag)
    else:
        print('MISSING ' + tag)


def append(rel, block, tag):
    get(rel)
    BUF[rel] = BUF[rel] + block
    print('OK      ' + tag)


# ----------------------------------------------------------------------------
# 1. New DATASETS panel: tiles + divider + preset/CSV dropdown row
# ----------------------------------------------------------------------------
DATASETS2_JSX = '''            <CollapsibleSection
                icon={<FiDatabase aria-hidden="true" />}
                title="DATASETS"
                right={<span className={styles.badge}>{loading ? 'LOADING' : `${rows.length} ROWS`}</span>}
            >
                <div className={styles.tileRow}>
                    {available.map(ds => (
                        <button
                            key={ds.key}
                            className={ds.key === datasetKey ? styles.tileActive : styles.tile}
                            onClick={() => setDatasetKey(ds.key)}
                        >
                            {ds.label}
                            {ds.key === datasetKey && <span className={styles.tileCount}>{loading ? '...' : rows.length}</span>}
                        </button>
                    ))}
                    <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}>
                        <FiRefreshCw size={11} aria-hidden="true" /> RELOAD
                    </button>
                </div>
                <p className={styles.hint}>{dataset?.blurb}</p>
                {!canSeeMoney && (
                    <p className={styles.hint}>
                        <FiAlertCircle size={12} aria-hidden="true" />
                        Financial datasets and money columns are hidden on your role.
                    </p>
                )}
                {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden="true" /> {error}</div>}
                <span className={styles.divider} />
                <div className={styles.toolRow}>
                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Preset</span>
                        <Pick
                            className={styles.wDataset}
                            ariaLabel="Start from a preset"
                            value=""
                            placeholder="Choose a preset..."
                            options={PRESET_VIEWS.filter(p => !p.money || canSeeMoney).map(p => ({ value: p.name, label: p.name }))}
                            onChange={v => { const p = PRESET_VIEWS.find(x => x.name === v); if (p) applyPreset(p); }}
                        />
                    </label>
                    {quickExports && (
                        <label className={styles.toolField}>
                            <span className={styles.miniLabel}>One-click CSV</span>
                            <Pick
                                className={styles.wCsv}
                                ariaLabel="One-click CSV reports"
                                value=""
                                placeholder="Download a standing report..."
                                options={quickExports.options}
                                onChange={v => quickExports.onExport(v)}
                            />
                        </label>
                    )}
                </div>
            </CollapsibleSection>'''

# ----------------------------------------------------------------------------
# 2. Presets with full column sets
# ----------------------------------------------------------------------------
PRESET_VIEWS_JSX = '''    const PRESET_VIEWS = [
        { name: 'OWED BY DISTRICT', money: true, datasetKey: 'PROJECTS', group: 'District', agg: 'sum', measure: 'Balance Owed', cols: ['Project Index', 'Primary Owner', 'District', 'Sub-County', 'Village', 'Status', 'Total Cost', 'Amount Paid', 'Balance Owed'], blurb: 'Projects grouped by district with the total balance owed summed per district.' },
        { name: 'OWED BY OWNER', money: true, datasetKey: 'PROJECTS', group: 'Primary Owner', agg: 'sum', measure: 'Balance Owed', cols: ['Project Index', 'Primary Owner', 'Owner Phone', 'District', 'Sub-County', 'Status', 'Total Cost', 'Amount Paid', 'Balance Owed'], blurb: 'Every primary owner ranked by what they still owe.' },
        { name: 'PAID VS COST', money: true, datasetKey: 'PROJECTS', group: 'Status', agg: 'sum', measure: 'Amount Paid', cols: ['Project Index', 'Primary Owner', 'District', 'Status', 'Total Cost', 'Amount Paid', 'Balance Owed'], blurb: 'What has been paid per project status, against the live cost columns.' },
        { name: 'PAYMENTS BY TYPE', money: true, datasetKey: 'PAYMENTS', group: 'Payment Type', agg: 'sum', measure: 'Amount', cols: [], blurb: 'Every payment summed by payment type: standard, deposit, receivable part.' },
        { name: 'SPEND BY CATEGORY', money: true, datasetKey: 'EXPENSES', group: 'Category', agg: 'sum', measure: 'Amount', cols: [], blurb: 'Company spend grouped by expense category.' },
        { name: 'PROJECTS BY DISTRICT', money: false, datasetKey: 'PROJECTS', group: 'District', agg: 'count', measure: '', cols: ['Project Index', 'Plot Number', 'District', 'County', 'Sub-County', 'Parish', 'Village', 'Primary Owner', 'Status'], blurb: 'How many projects sit in each district, down to village level.' },
        { name: 'PROJECTS BY STAGE', money: false, datasetKey: 'PROJECTS', group: 'Stage', agg: 'count', measure: '', cols: ['Project Index', 'Primary Owner', 'District', 'Sub-County', 'Status'], blurb: 'Pipeline shape: project count per current stage.' },
        { name: 'CLIENTS BY DISTRICT', money: false, datasetKey: 'CLIENTS', group: 'District', agg: 'count', measure: '', cols: [], blurb: 'Registered clients per district.' },
    ];'''

# ----------------------------------------------------------------------------
# 3. ANALYSIS panel: read-only view of the REPORTS tab's selection
# ----------------------------------------------------------------------------
ANALYSIS_JSX = '''                <CollapsibleSection
                    icon={<FiBarChart2 aria-hidden="true" />}
                    title="ANALYSIS"
                    right={<span className={styles.badge}>{groupBy ? 'GROUPED' : 'ROW BY ROW'}</span>}
                >
                    <div className={styles.statStrip}>
                        <div className={styles.statCard}>
                            <label>ROWS MATCHED</label>
                            <strong>{filtered.length.toLocaleString()}</strong>
                            <span className={styles.statNote}>of {rows.length.toLocaleString()} loaded</span>
                        </div>
                        {measures.map((m, i) => (
                            <div key={i} className={styles.statCard}>
                                <label>{measureLabel(m, dataset)}</label>
                                <strong>{formatValue(totals[i], measureType(m, dataset))}</strong>
                                <span className={styles.statNote}>across the filtered set</span>
                            </div>
                        ))}
                    </div>
                    {grouped && grouped.length > 0 ? (
                        <>
                            <div className={styles.sectionLabel}>
                                {measureLabel(measures[0], dataset)} by {groupField?.label}
                                {splitField ? ' split by ' + splitField.label : ''}
                            </div>
                            <div className={styles.chart}>
                                {chartRows.map(g => (
                                    <div key={g.id} className={styles.chartRow}>
                                        <span className={styles.chartLabel} title={g.id}>{g.id}</span>
                                        <div className={styles.chartTrack}>
                                            <div
                                                className={styles.chartFill}
                                                style={{ width: chartMax ? `${Math.max(1, (Math.abs(num(g.values[0])) / chartMax) * 100)}%` : '1%' }}
                                            />
                                        </div>
                                        <span className={styles.chartValue}>
                                            {formatValue(g.values[0], measureType(measures[0], dataset))}
                                        </span>
                                    </div>
                                ))}
                            </div>
                            <div className={styles.tableScroll}>
                                <table className={styles.table}>
                                    <thead>
                                        <tr>
                                            <th>{groupField?.label || 'Group'}</th>
                                            {splitField && <th>{splitField.label}</th>}
                                            <th>Rows</th>
                                            {measures.map((m, i) => <th key={i}>{measureLabel(m, dataset)}</th>)}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {grouped.map(g => (
                                            <tr key={g.id}>
                                                <td className={styles.strong}>{g.path[0]}</td>
                                                {splitField && <td>{g.path[1] ?? '---'}</td>}
                                                <td className={styles.mono}>{g.count}</td>
                                                {g.values.map((v, i) => (
                                                    <td key={i} className={styles.mono}>{formatValue(v, measureType(measures[i], dataset))}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    ) : (
                        <p className={styles.hint}>
                            <FiAlertCircle size={12} aria-hidden="true" />
                            Nothing grouped yet. Pick a group field on the REPORTS tab and the charts light up here from exactly that selection.
                        </p>
                    )}
                </CollapsibleSection>'''

# ----------------------------------------------------------------------------
# 4. Hub: one studio instance backs both tabs; library becomes dropdown data
# ----------------------------------------------------------------------------
HUB_SINGLE_JSX = '''        <div className={styles.pillarStack}>
            <DrawerPanel open={drawers.studio} onToggle={() => toggleDrawer('studio')} label="REPORT STUDIO" icon={FiSliders} tall>
                <ReportStudio
                    canSeeMoney={hasFinancialAccess}
                    mode={tab === 'REPORTS' ? 'report' : 'analysis'}
                    reloadToken={reloadToken}
                    quickExports={tab === 'REPORTS' ? library : null}
                />
            </DrawerPanel>
        </div>'''

LIB_OBJ_JSX = '''    const library = {
        options: [
            ...(hasFinancialAccess ? [{ section: 'FINANCIAL' }, ...FINANCIAL_GROUP.map(g => ({ value: g.id, label: g.title }))] : []),
            { section: 'OPERATIONAL' },
            ...OPS_GROUP.map(g => ({ value: g.id, label: g.title })),
            ...(hasFinancialAccess ? [{ section: 'SYSTEM' }, ...SYSTEM_GROUP.map(g => ({ value: g.id, label: g.title }))] : []),
            ...(hasFinancialAccess ? [{ section: 'MORE' }, ...PRIORITY2_GROUP.map(g => ({ value: g.id, label: g.title }))] : []),
        ],
        onExport: (id) => {
            const item = [...FINANCIAL_GROUP, ...OPS_GROUP, ...SYSTEM_GROUP, ...PRIORITY2_GROUP].find(x => x.id === id);
            if (item) triggerPillarExport(id, item.action, item.title);
        },
    };

    return ('''

STU_CSS = '''

/* fix78 -- separators, CSV pick width, list section headers, and the open
   dropdown lists back on the Intake white-control language. */
.divider {
  display: block; height: 1px; border-radius: 1px;
  background: rgba(255,255,255,0.10);
  margin: clamp(10px,1.4vw,16px) 0;
}
.wCsv { width: clamp(220px,26vw,320px); }
.pickSection {
  display: block; padding: 6px 10px 4px;
  font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 900;
  letter-spacing: 2px; text-transform: uppercase;
  color: rgba(26,46,48,0.45);
}
.pickList { background: #fff; border: 2px solid var(--orange); box-shadow: 0 18px 40px rgba(26,46,48,0.28); }
.pickOption, .pickOptionActive { color: var(--ink); }
.pickOption:hover { background: var(--orange-soft); }
.pickOptionActive { background: var(--orange-soft); border-left-color: var(--orange); color: #b45309; }
.dropdownList { background: #fff; border: 2px solid var(--orange); box-shadow: 0 18px 40px rgba(26,46,48,0.28); }
.dropdownActions { background: #fff; border-bottom: 1px solid var(--paper-edge); }
.dropdownOption { color: var(--ink); border-bottom: 1px solid #f1eeea; }
.dropdownOption:last-child { border-bottom: none; }
.dropdownOption:hover { background: var(--orange-soft); }
.miniBtn { background: #fff; border: 1.5px solid var(--paper-edge); color: var(--ink); }
.miniBtn:hover { border-color: var(--orange); color: var(--orange); background: var(--orange-soft); }
'''

ADDENDUM = '''

- fix78 (2026-09-17): Reports de-clutter pass per David's review. DATASETS panel: preset chips and one-click CSV chip groups replaced by two dropdowns on one row (PRESET, and ONE-CLICK CSV whose list carries FINANCIAL / OPERATIONAL / SYSTEM / MORE section headers inside it; picking one downloads immediately). Dataset picker stays tiles, never a dropdown. Open dropdown lists moved back to the Intake white-control language (white paper, ink text, orange border, orange-soft hover, orange left-bar on the chosen row). Hairline separators split sub-blocks inside panels. Save-view feature removed entirely: SAVE AS box, SAVE VIEW button, saved-view chips and the state/functions behind them are gone. ANALYSIS tab is now a pure read-out of the REPORTS tab: one studio instance backs both tabs, analysis shows stat cards + bar chart + grouped table computed from the report tab's live selection and has no settings of its own; with nothing grouped it says so in one line. Presets now carry full column sets (project index, plot, county, sub-county, parish, village, owner phone, status, cost/paid/owed) resolved by label at click time. CollapsibleSection body gradient softened one notch app-wide so panel bodies stop reading as a cave.
'''

# ============================================================================
# PATCHES
# ============================================================================
print('=' * 72)
print(' GOLDEN SEED fix78 -- de-clutter, analysis read-out, fuller presets')
print('=' * 72)

# -- ReportStudio.jsx --------------------------------------------------------
# a) DATASETS panel rebuilt (save view + chip rows out, dropdown row in)
rpatch(STU,
       r'<CollapsibleSection\s+icon=\{<FiDatabase aria-hidden="true" />\}\s+title="DATASETS"[\s\S]*?</CollapsibleSection>',
       lambda m: DATASETS2_JSX,
       'Studio: DATASETS panel rebuilt with preset + CSV dropdowns')

# b) save-view state gone
patch(STU,
      "    const [views, setViews] = useState(() => loadViews());\n    const [viewName, setViewName] = useState('');\n",
      '',
      'Studio: save-view state removed')

# c) save-view functions gone (persist -> end of applyView)
rpatch(STU,
       r'\n    const persist = \(next\) =>[\s\S]*?\}, 0\);\n    \};\n',
       '\n',
       'Studio: save-view functions removed')

# d) Pick learns section headers inside its list
patch(STU,
      '{options.map(o => (',
      '{options.map(o => (\n                o.section ? (\n                    <span key={o.section} className={styles.pickSection}>{o.section}</span>\n                ) : (',
      'Studio: Pick supports section headers (open)')
rpatch(STU,
       r'\{o\.label\}\s*</button>\s*\)\)\}',
       lambda m: '{o.label}\n                        </button>\n                    )\n                ))}',
       'Studio: Pick supports section headers (close)')

# e) presets with full column sets
rpatch(STU,
       r'    const PRESET_VIEWS = \[[\s\S]*?\n    \];\n',
       lambda m: PRESET_VIEWS_JSX + '\n',
       'Studio: presets carry full column sets')

# f) preset applier uses the preset columns
patch(STU,
      '            setColumns(ds.defaultColumns.filter(c => flds.some(f => f.key === c)));',
      "            const presetCols = (p.cols || []).map(l => (flds.find(f => f.label === l) || {}).key).filter(Boolean);\n            setColumns(presetCols.length > 0 ? presetCols : ds.defaultColumns.filter(c => flds.some(f => f.key === c)));",
      'Studio: applyPreset honours preset columns')

# g) DATASETS + BUILD only on the report view
rpatch(STU,
       r'(<CollapsibleSection\s+icon=\{<FiDatabase aria-hidden="true" />\}\s+title="DATASETS"[\s\S]*?</CollapsibleSection>)',
       lambda m: "{mode === 'report' && (\n" + m.group(1) + "\n            )}",
       'Studio: DATASETS hidden on analysis view')
rpatch(STU,
       r'(<CollapsibleSection\s+icon=\{<FiFilter aria-hidden="true" />\}\s+title="BUILD"[\s\S]*?</CollapsibleSection>)',
       lambda m: "{mode === 'report' && (\n" + m.group(1) + "\n            )}",
       'Studio: BUILD hidden on analysis view')

# h) RESULTS report-only + ANALYSIS read-out panel
rpatch(STU,
       r'(<CollapsibleSection\s+icon=\{<FiBarChart2 aria-hidden="true" />\}\s+title="RESULTS"[\s\S]*?</CollapsibleSection>)',
       lambda m: "{mode === 'report' && (\n" + m.group(1) + "\n            )}\n\n            {mode === 'analysis' && (\n" + ANALYSIS_JSX + "\n            )}",
       'Studio: ANALYSIS read-out panel added')

# -- ReportHub.jsx -----------------------------------------------------------
# i) one studio instance backs both tabs
rpatch(HUB,
       r"\{tab === 'REPORTS' && \([\s\S]*?</DrawerPanel>\s*</div>\s*\)\}\s*\{tab === 'ANALYSIS' && \([\s\S]*?</DrawerPanel>\s*</div>\s*\)\}",
       lambda m: HUB_SINGLE_JSX,
       'Hub: single studio instance for both tabs')

# j) library becomes dropdown data + export handler
rpatch(HUB,
       r'    const library = \([\s\S]*?\n    \);\n\n    return \(',
       lambda m: LIB_OBJ_JSX,
       'Hub: library rebuilt as dropdown options + handler')

# -- CSS ----------------------------------------------------------------------
append(STUCSS, STU_CSS, 'Studio CSS: separators + white lists layer appended')
patch(COLCSS,
      'linear-gradient(135deg,#3a5a5c,#2a4a4c,#213E40)',
      'linear-gradient(135deg,#4a6a6c,#3a5a5c,#2f4c4e)',
      'CollapsibleSection: body gradient softened app-wide')
append(ADD, ADDENDUM, 'Addendum: fix78 entry appended')

# ============================================================================
# WRITE + BUILD CHECK + GIT
# ============================================================================
for rel in (STU, STUCSS, HUB, COLCSS, ADD):
    save(rel)
print('')
print('All files written.')
print('')

frontend = os.path.join(ROOT, 'erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=frontend, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print('')
        print('BUILD RED -- nothing was committed or pushed.')
        sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping build check)')

print('')
print('git: staging, committing, pushing...')
MSG = ('fix78: reports de-clutter -- preset + CSV dropdowns, save-view removed, '
       'analysis tab reads the report tab live, fuller preset columns, softer panels')
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Wait for the green tick, then walk both tabs and tell me what still fights you.')