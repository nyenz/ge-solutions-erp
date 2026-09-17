#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP -- fix75 PATCHER
================================================================================
 WHAT:
   1. Panel 1 is DATASETS and it is NOT a dropdown: Intake-style tiles
      (dark idle, solid orange selected, row count inside the selected tile).
   2. The builder panels after it are combined into ONE panel called BUILD
      (search + match + conditions + columns + group/compare + measures).
      Studio = DATASETS -> BUILD -> RESULTS. Table still last.
   3. Presets rethought against the updated app:
      - START FROM A PRESET: preset builder views generated from what the app
        actually tracks (owed by district/owner, paid vs cost, payments by
        type, spend by category, projects by district/stage, clients by
        district). Label-resolved at click time so they degrade, never crash.
      - ONE-CLICK CSV: the twelve server pillars as compact download chips
        grouped FINANCIAL / OPERATIONAL / SYSTEM / MORE, tooltip = what is
        inside. The black expandable drawers are gone.
      - Saved views live in the DATASETS panel now.
 HOW: run  py fix.py  from the project root (on a fresh clone of main).
      Prints OK / MISSING per patch. Commits and pushes at the end.
================================================================================
"""

import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

STU    = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
STUCSS = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')
HUB    = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.jsx')
HUBCSS = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.module.css')
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
# 1. The new DATASETS panel (tiles + presets + saved views + one-click CSV)
# ----------------------------------------------------------------------------
DATASETS_JSX = '''            <CollapsibleSection
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
                <span className={styles.rowLabel}>Start from a preset</span>
                <div className={styles.tileRow}>
                    {PRESET_VIEWS.filter(p => !p.money || canSeeMoney).map(p => (
                        <Tooltip key={p.name} label={p.blurb}>
                            <button className={styles.pChip} onClick={() => applyPreset(p)}>{p.name}</button>
                        </Tooltip>
                    ))}
                </div>
                <div className={styles.toolRow}>
                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Save as</span>
                        <span className={styles.viewBox}>
                            <FiSave className={styles.boxIcon} aria-hidden="true" />
                            <input
                                className={styles.viewInput}
                                placeholder="View name..."
                                value={viewName}
                                onChange={e => setViewName(e.target.value)}
                            />
                        </span>
                    </label>
                    <Tooltip label="Save the current dataset, filters, columns and grouping. Saved on this device.">
                        <button className={styles.chipActive} onClick={saveCurrentView} disabled={!viewName.trim()}>
                            <FiSave size={11} aria-hidden="true" /> SAVE VIEW
                        </button>
                    </Tooltip>
                </div>
                {views.length > 0 && (
                    <div className={styles.chipRow}>
                        {views.map(v => (
                            <span key={v.name} className={styles.viewChip}>
                                <button className={styles.viewChipName} onClick={() => applyView(v)}>{v.name}</button>
                                <button
                                    className={styles.viewChipDrop}
                                    onClick={() => persist(views.filter(x => x.name !== v.name))}
                                    aria-label={`Delete saved view ${v.name}`}
                                >
                                    <FiTrash2 size={10} aria-hidden="true" />
                                </button>
                            </span>
                        ))}
                    </div>
                )}
                {quickExports && (
                    <>
                        <span className={styles.rowLabel}>One-click CSV</span>
                        {quickExports}
                    </>
                )}
            </CollapsibleSection>'''

# ----------------------------------------------------------------------------
# 2. Preset views + the applier (label-resolved, degrades never crashes)
# ----------------------------------------------------------------------------
PRESET_JSX = '''    const PRESET_VIEWS = [
        { name: 'OWED BY DISTRICT', money: true, datasetKey: 'PROJECTS', group: 'District', agg: 'sum', measure: 'Balance Owed', blurb: 'Projects grouped by district with the total balance owed summed per district.' },
        { name: 'OWED BY OWNER', money: true, datasetKey: 'PROJECTS', group: 'Primary Owner', agg: 'sum', measure: 'Balance Owed', blurb: 'Every primary owner ranked by what they still owe.' },
        { name: 'PAID VS COST', money: true, datasetKey: 'PROJECTS', group: 'Status', agg: 'sum', measure: 'Amount Paid', blurb: 'What has been paid per project status, against the live cost columns.' },
        { name: 'PAYMENTS BY TYPE', money: true, datasetKey: 'PAYMENTS', group: 'Payment Type', agg: 'sum', measure: 'Amount', blurb: 'Every payment summed by payment type: standard, deposit, receivable part.' },
        { name: 'SPEND BY CATEGORY', money: true, datasetKey: 'EXPENSES', group: 'Category', agg: 'sum', measure: 'Amount', blurb: 'Company spend grouped by expense category.' },
        { name: 'PROJECTS BY DISTRICT', money: false, datasetKey: 'PROJECTS', group: 'District', agg: 'count', measure: '', blurb: 'How many projects sit in each district.' },
        { name: 'PROJECTS BY STAGE', money: false, datasetKey: 'PROJECTS', group: 'Stage', agg: 'count', measure: '', blurb: 'Pipeline shape: project count per current stage.' },
        { name: 'CLIENTS BY DISTRICT', money: false, datasetKey: 'CLIENTS', group: 'District', agg: 'count', measure: '', blurb: 'Registered clients per district.' },
    ];

    const applyPreset = (p) => {
        const ds = DATASETS[p.datasetKey];
        if (!ds) return;
        const flds = fieldsFor(ds, canSeeMoney);
        const gKey = (flds.find(f => f.label === p.group) || {}).key || '';
        const mKey = p.measure ? ((flds.find(f => f.label === p.measure) || {}).key || '') : '';
        setDatasetKey(p.datasetKey);
        // the dataset-change effect resets the builder, so the preset lands after it
        setTimeout(() => {
            setSearch('');
            setMergeMode('AND');
            setConditions([]);
            setColumns(ds.defaultColumns.filter(c => flds.some(f => f.key === c)));
            setGroupBy(gKey);
            setSplitBy('');
            setMeasures([{ agg: p.agg, field: mKey }]);
            setSort({ key: '', dir: 'desc' });
        }, 0);
    };

    const groupField = fieldByKey(dataset, groupBy);'''

# ----------------------------------------------------------------------------
# 3. Hub: the library becomes compact download chips (no more black drawers)
# ----------------------------------------------------------------------------
LIB_CHIPS_JSX = '''    const library = (
        <div className={styles.libWrap}>
            {hasFinancialAccess ? (
                <div className={styles.libGroup}>
                    <span className={styles.libLabel}>Financial</span>
                    <div className={styles.libChips}>
                        {FINANCIAL_GROUP.map(item => (
                            <Tooltip key={item.id} label={(REPORT_SCHEMA[item.id] || {}).desc || item.title}>
                                <button
                                    className={styles.libChip}
                                    disabled={status[item.id]}
                                    onClick={() => triggerPillarExport(item.id, item.action, item.title)}
                                >
                                    {status[item.id] ? 'STREAMING...' : item.title}
                                </button>
                            </Tooltip>
                        ))}
                    </div>
                </div>
            ) : (
                <div className={styles.restrictionHandbrake} role="alert">
                    <FiLock className={styles.lockIcon} aria-hidden="true" />
                    <div className={styles.warningText}>
                        <strong>SECURITY HANDBRAKE ACTIVE</strong>
                        <p>FINANCIAL PILLARS ARE ENCRYPTED. CONTACT ROOT OWNER FOR ACCESS.</p>
                    </div>
                </div>
            )}
            <div className={styles.libGroup}>
                <span className={styles.libLabel}>Operational</span>
                <div className={styles.libChips}>
                    {OPS_GROUP.map(item => (
                        <Tooltip key={item.id} label={(REPORT_SCHEMA[item.id] || {}).desc || item.title}>
                            <button
                                className={styles.libChip}
                                disabled={status[item.id]}
                                onClick={() => triggerPillarExport(item.id, item.action, item.title)}
                            >
                                {status[item.id] ? 'STREAMING...' : item.title}
                            </button>
                        </Tooltip>
                    ))}
                </div>
            </div>
            {hasFinancialAccess && (
                <div className={styles.libGroup}>
                    <span className={styles.libLabel}>System</span>
                    <div className={styles.libChips}>
                        {SYSTEM_GROUP.map(item => (
                            <Tooltip key={item.id} label={(REPORT_SCHEMA[item.id] || {}).desc || item.title}>
                                <button
                                    className={styles.libChip}
                                    disabled={status[item.id]}
                                    onClick={() => triggerPillarExport(item.id, item.action, item.title)}
                                >
                                    {status[item.id] ? 'STREAMING...' : item.title}
                                </button>
                            </Tooltip>
                        ))}
                    </div>
                </div>
            )}
            {hasFinancialAccess && (
                <div className={styles.libGroup}>
                    <span className={styles.libLabel}>More</span>
                    <div className={styles.libChips}>
                        {PRIORITY2_GROUP.map(item => (
                            <Tooltip key={item.id} label={(REPORT_SCHEMA[item.id] || {}).desc || item.title}>
                                <button
                                    className={styles.libChip}
                                    disabled={status[item.id]}
                                    onClick={() => triggerPillarExport(item.id, item.action, item.title)}
                                >
                                    {status[item.id] ? 'STREAMING...' : item.title}
                                </button>
                            </Tooltip>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    return ('''

STU_CSS = '''

/* fix75 -- DATASETS TILES + PRESET CHIPS (Intake / Recovery button language:
   dark idle, solid orange selected, orange tint on hover). Appended on
   purpose: cascade wins. */
.tileRow {
  display: flex; flex-wrap: wrap; align-items: center;
  gap: clamp(6px,0.9vw,10px);
  margin-bottom: clamp(8px,1.1vw,12px);
}
.tile, .tileActive {
  display: inline-flex; align-items: center; gap: 7px;
  font-family: 'Inter', sans-serif;
  font-size: clamp(9px,0.95vw,11px); font-weight: 900;
  letter-spacing: 1.5px; text-transform: uppercase;
  padding: clamp(8px,1.1vw,11px) clamp(14px,2vw,24px);
  border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.85);
  cursor: pointer; transition: all 0.2s ease;
}
.tile:hover { border-color: var(--orange); color: var(--orange); background: rgba(238,140,58,0.12); }
.tileActive {
  background: var(--orange); border-color: var(--orange); color: #1a2e30;
  box-shadow: 0 4px 16px rgba(238,140,58,0.3);
}
.tileCount { font-family: 'Space Mono', monospace; font-size: clamp(8px,0.85vw,10px); opacity: 0.75; }
.pChip {
  font-family: 'Inter', sans-serif; font-weight: 900;
  text-transform: uppercase; letter-spacing: 1.5px;
  font-size: clamp(8px,0.85vw,10px);
  padding: clamp(7px,0.95vw,10px) clamp(10px,1.4vw,16px);
  border-radius: var(--radius-sm);
  border: 1.5px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.85);
  cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
}
.pChip:hover { background: rgba(238,140,58,0.12); color: var(--orange); border-color: var(--orange); }
.rowLabel {
  display: block;
  font-size: clamp(8px,0.85vw,10px); font-weight: 900;
  letter-spacing: 1.5px; text-transform: uppercase;
  color: rgba(255,255,255,0.6);
  margin: clamp(4px,0.6vw,8px) 0 6px;
}
'''

HUB_CSS = '''

/* fix75 -- one-click CSV pillars as compact chips (filter-button spec on the
   dark panel body). The black expandable drawers are gone. */
.libChips { display: flex; flex-wrap: wrap; gap: 6px; }
.libChip {
  font-family: 'Inter', sans-serif; font-weight: 900;
  text-transform: uppercase; letter-spacing: 1.5px;
  font-size: clamp(8px,0.85vw,10px);
  padding: clamp(7px,0.95vw,10px) clamp(10px,1.4vw,16px);
  border-radius: 6px;
  border: 1.5px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.85);
  cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
}
.libChip:hover:not(:disabled) { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.libChip:disabled { opacity: 0.45; cursor: wait; }
'''

ADDENDUM = '''

- fix75 (2026-09-17): Report Studio is now three panels -- DATASETS, BUILD, RESULTS -- with Intake/Recovery as the design baseline. Panel 1 picks the dataset with Intake-mode tiles (dark idle, solid orange selected, live row count inside the selected tile), not a dropdown. The builder panels that followed are ONE panel called BUILD (search + match + conditions + columns + group/compare + measures). Presets rethought against the updated app: START FROM A PRESET chips configure the builder in one click from what the app actually tracks now (owed by district, owed by owner, paid vs cost, payments by type, spend by category, projects by district, projects by stage, clients by district); they resolve field labels at click time so a missing field degrades the preset instead of crashing it, and money presets hide from non-financial roles. ONE-CLICK CSV keeps the twelve server pillars but as compact download chips grouped FINANCIAL / OPERATIONAL / SYSTEM / MORE with a tooltip describing exactly what is inside; the black expandable forensic drawers are gone. Saved views (SAVE AS box + view chips) moved into the DATASETS panel because they are a what-am-I-looking-at control, not a builder control.
'''

# ============================================================================
# PATCHES
# ============================================================================
print('=' * 72)
print(' GOLDEN SEED fix75 -- DATASETS tiles, one BUILD panel, rethought presets')
print('=' * 72)

# -- ReportStudio.jsx --------------------------------------------------------
# a) the old PRESETS section (expandable library holder) is gone
rpatch(STU,
       r'<CollapsibleSection\s+icon=\{<FiDownloadCloud aria-hidden="true" />\}\s+title="PRESETS"[\s\S]*?</CollapsibleSection>',
       '',
       'Studio: old PRESETS section removed')

# b) SOURCE section becomes the DATASETS panel
rpatch(STU,
       r'<CollapsibleSection\s+icon=\{<FiDatabase aria-hidden="true" />\}\s+title="SOURCE"[\s\S]*?</CollapsibleSection>',
       lambda m: DATASETS_JSX,
       'Studio: DATASETS panel (tiles + presets + views + one-click CSV)')

# c) GROUPING folds into the FILTERS panel, which becomes BUILD
rpatch(STU,
       r'</CollapsibleSection>\s*<CollapsibleSection\s+icon=\{<FiBarChart2 aria-hidden="true" />\}\s+title="GROUPING"\s+defaultOpen=\{mode === .analysis.\}\s+right=\{<span className=\{styles\.badge\}>\{groupBy \? .GROUPED. : .ROW BY ROW.\}</span>\}\s*>([\s\S]*?)</CollapsibleSection>',
       lambda m: m.group(1) + '            </CollapsibleSection>',
       'Studio: GROUPING folded into the builder panel')
patch(STU, 'title="FILTERS"', 'title="BUILD"', 'Studio: builder panel renamed BUILD')

# d) preset views + applier land just before the render helpers
patch(STU,
      '    const groupField = fieldByKey(dataset, groupBy);',
      PRESET_JSX,
      'Studio: PRESET_VIEWS + applyPreset added')

# -- ReportHub.jsx -----------------------------------------------------------
# e) Tooltip import for the chip tooltips
patch(HUB,
      "import ReportStudio from './ReportStudio';",
      "import ReportStudio from './ReportStudio';\nimport { Tooltip } from '../../components/common/Tooltip';",
      'Hub: Tooltip imported')

# f) the expandable ReportRow component is gone (chips replace it)
rpatch(HUB,
       r'    const ReportRow = \(\{ item \}\) => \{[\s\S]*?\n    \};\n',
       '',
       'Hub: ReportRow component removed')

# g) library becomes chip groups
rpatch(HUB,
       r'    const library = \([\s\S]*?\n    \);\n\n    return \(',
       lambda m: LIB_CHIPS_JSX,
       'Hub: library rebuilt as download chips')

# -- CSS layers ---------------------------------------------------------------
append(STUCSS, STU_CSS, 'Studio CSS: tiles + preset chips layer appended')
append(HUBCSS, HUB_CSS, 'Hub CSS: lib chips layer appended')
append(ADD, ADDENDUM, 'Addendum: fix75 entry appended')

# ============================================================================
# WRITE + GIT
# ============================================================================
for rel in (STU, STUCSS, HUB, HUBCSS, ADD):
    save(rel)
print('')
print('All files written.')
print('')
print('git: staging, committing, pushing...')
MSG = ('fix75: studio is DATASETS tiles + one BUILD panel + RESULTS; presets '
       'rethought as one-click builder views and compact CSV chips')
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Wait for the green tick on Render, then test only once you say so.')