#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP -- fix72 PATCHER
================================================================================
 WHAT:
   1. Reports tab: the four canned-report drawers (FINANCIAL / OPERATIONAL /
      SYSTEM / MORE) are removed from UNDER the studio and integrated at the
      TOP of the general reports system as one ONE-CLICK REPORTS section
      inside the studio. The RESULTS table becomes the last block on the tab.
   2. Every studio <select> loses its browser-default look: no native arrow,
      fixed 38px height (the old flex-basis made the dataset select ~150px
      tall), styled options, a real disabled state.
   3. DATA SOURCE panel rethought: icon frame + full-width dataset pick +
      RELOAD on one row.
   4. GROUP / COMPARE panel rethought: group-by and split-by on one row with
      a VS tag between them, plus an unlock hint.
   5. Contrast faults: hint / mini labels / section labels were ink-on-dark;
      now light-on-dark where they actually sit.
 HOW: run  py fix.py  from the project root. Prints OK / MISSING per patch.
      Commits and pushes at the end.
================================================================================
"""

import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

HUB    = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.jsx')
HUBCSS = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.module.css')
STU    = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
STUCSS = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')
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
# 1. ReportHub.jsx -- library node (the four groups, folded into one block)
# ----------------------------------------------------------------------------
LIB_JSX = '''    const library = (
        <div className={styles.libWrap}>
            {hasFinancialAccess ? (
                <div className={styles.libGroup}>
                    <span className={styles.libLabel}>Financial</span>
                    <div className={styles.libList}>
                        {FINANCIAL_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
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
                <div className={styles.libList}>
                    {OPS_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                </div>
            </div>
            {hasFinancialAccess && (
                <div className={styles.libGroup}>
                    <span className={styles.libLabel}>System</span>
                    <div className={styles.libList}>
                        {SYSTEM_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                    </div>
                </div>
            )}
            {hasFinancialAccess && (
                <div className={styles.libGroup}>
                    <span className={styles.libLabel}>More</span>
                    <div className={styles.libList}>
                        {PRIORITY2_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                    </div>
                </div>
            )}
        </div>
    );

    return (
        <div className={styles.container}>'''

# ----------------------------------------------------------------------------
# 2. ReportStudio.jsx -- the ONE-CLICK REPORTS section, first in the studio
# ----------------------------------------------------------------------------
QUICK_JSX = '''            {quickExports && (
                <CollapsibleSection
                    icon={<FiDownloadCloud aria-hidden="true" />}
                    title="ONE-CLICK REPORTS"
                    defaultOpen
                    right={<span className={styles.badge}>CANNED CSV</span>}
                >
                    <p className={styles.hint}>
                        The standing company reports, ready to pull. Open one to read exactly what is inside before you download it.
                    </p>
                    {quickExports}
                </CollapsibleSection>
            )}
'''

# ----------------------------------------------------------------------------
# 3. ReportStudio.jsx -- DATA SOURCE bar, rethought
# ----------------------------------------------------------------------------
DATASET_JSX = '''                <div className={styles.datasetBar}>
                    <span className={styles.datasetIcon} aria-hidden="true">
                        <FiDatabase aria-hidden="true" />
                    </span>
                    <label className={styles.datasetPick}>
                        <span className={styles.miniLabel}>Dataset</span>
                        <span className={styles.selectWrap}>
                            <select
                                className={styles.select}
                                value={datasetKey}
                                onChange={e => setDatasetKey(e.target.value)}
                                aria-label="Dataset"
                            >
                                {available.map(ds => <option key={ds.key} value={ds.key}>{ds.label}</option>)}
                            </select>
                        </span>
                    </label>
                    <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}>
                        <FiRefreshCw size={11} aria-hidden="true" /> RELOAD
                    </button>
                </div>'''

# ----------------------------------------------------------------------------
# 4. ReportStudio.jsx -- GROUP / COMPARE row, rethought
# ----------------------------------------------------------------------------
COMPARE_JSX = '''                <div className={styles.compareRow}>
                    <label className={styles.comparePick}>
                        <span className={styles.miniLabel}>Group by</span>
                        <span className={styles.selectWrap}>
                            <select className={styles.select} value={groupBy} onChange={e => setGroupBy(e.target.value)}>
                                <option value="">(no grouping -- show every row)</option>
                                {fields.map(fl => <option key={fl.key} value={fl.key}>{fl.label}</option>)}
                            </select>
                        </span>
                    </label>
                    <span className={styles.compareVs} aria-hidden="true">VS</span>
                    <label className={styles.comparePick}>
                        <span className={styles.miniLabel}>Compare / split by</span>
                        <span className={styles.selectWrap}>
                            <select className={styles.select} value={splitBy} onChange={e => setSplitBy(e.target.value)} disabled={!groupBy}>
                                <option value="">(none)</option>
                                {fields.filter(fl => fl.key !== groupBy).map(fl => <option key={fl.key} value={fl.key}>{fl.label}</option>)}
                            </select>
                        </span>
                    </label>
                </div>
                {!groupBy && (
                    <p className={styles.hint}>
                        <FiAlertCircle size={12} aria-hidden="true" />
                        Compare unlocks once a group field is picked -- the chart and the split columns light up with it.
                    </p>
                )}'''

# ----------------------------------------------------------------------------
# 5. ReportStudio.module.css -- appended override layer (cascade does the work)
# ----------------------------------------------------------------------------
STU_CSS = '''

/* fix72 -- DROPDOWN + PANEL RESTYLE LAYER (appended on purpose: every rule
   below overrides the same selector declared earlier in this file). */

/* 1. The native select, fully owned. No browser arrow, no browser height.
   The old flex: 1 1 150px became a 150px-TALL box inside column-flex
   wrappers, because in a column the basis is the height. Wrappers below
   are row-flex, so the basis is a width again. */
.select {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  height: 38px;
  padding-right: 32px;
  flex: 0 1 auto;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%23EE8C3A' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 11px center;
}
.select:disabled {
  cursor: not-allowed;
  background-color: #f1eeea;
  border-style: dashed;
  color: rgba(26,46,48,0.45);
  background-image: url("data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%23b9b2a9' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E");
}
.select option { background: #fff; color: var(--ink); font-weight: 600; }
.select option:disabled { color: rgba(26,46,48,0.35); }
.selectWrap { position: relative; display: flex; flex: 1 1 150px; min-width: 130px; max-width: 100%; }
.selectWrap .select { flex: 1 1 auto; width: 100%; min-width: 0; }

/* 2. DATA SOURCE rethink: icon frame + full-width pick + RELOAD, one row. */
.datasetBar { display: flex; flex-wrap: wrap; align-items: flex-end; gap: clamp(6px,0.9vw,10px); }
.datasetIcon {
  width: 38px; height: 38px; flex: 0 0 38px;
  border-radius: var(--radius-sm);
  background: rgba(238,140,58,0.16); border: 1.5px solid rgba(238,140,58,0.34);
  color: var(--orange); font-size: 16px;
  display: flex; align-items: center; justify-content: center;
}
.datasetPick { display: flex; flex-direction: column; gap: 5px; flex: 1 1 240px; min-width: 0; }

/* 3. COMPARE rethink: group and split on one row with a VS tag between,
   so the eye reads them as one decision instead of two orphan boxes. */
.compareRow { display: flex; flex-wrap: wrap; align-items: flex-end; gap: clamp(6px,0.9vw,10px); }
.comparePick { display: flex; flex-direction: column; gap: 5px; flex: 1 1 220px; min-width: 0; }
.compareVs {
  font-family: 'Space Mono', monospace; font-weight: 900;
  font-size: clamp(9px,0.95vw,11px); letter-spacing: 1px;
  color: var(--orange); background: rgba(238,140,58,0.16);
  border: 1.5px solid rgba(238,140,58,0.34); border-radius: var(--radius-sm);
  padding: clamp(7px,0.95vw,10px) clamp(8px,1vw,12px);
}

/* 4. Condition + measure rows: the wrapper owns the stretch now. */
.condRow .selectWrap { flex: 1 1 160px; }
.condRow .input { flex: 1 1 120px; }

/* 5. Contrast faults: these labels sit on the dark CollapsibleSection
   bodies, not on paper. Ink-grey on navy was a 2:1 whisper. */
.studio { color: #fff; }
.hint { color: rgba(255,255,255,0.66); }
.miniLabel { color: rgba(255,255,255,0.6); }
.sectionLabel { color: var(--orange); }

@media (max-width: 640px) {
  .selectWrap, .datasetPick, .comparePick { flex: 1 1 100%; min-width: 0; }
}
'''

# ----------------------------------------------------------------------------
# 6. ReportHub.module.css -- library-on-dark-panel styles
# ----------------------------------------------------------------------------
HUB_CSS = '''

/* fix72 -- REPORT LIBRARY INSIDE THE STUDIO.
   The canned pillars moved from four dark drawers under the studio into one
   library section at the TOP of the studio, so the rows become white cards
   on the dark panel body and the group labels read light-on-dark. */
.libWrap { display: flex; flex-direction: column; gap: clamp(10px,1.4vw,16px); }
.libGroup { display: flex; flex-direction: column; gap: 6px; }
.libLabel {
  font-family: 'DM Sans', sans-serif; font-weight: 900;
  font-size: clamp(8px,0.85vw,10px); letter-spacing: 2px; text-transform: uppercase;
  color: rgba(255,255,255,0.6);
}
.libList { display: flex; flex-direction: column; gap: 6px; }
.libList .reportRowWrap {
  border-bottom: none;
  background: #fff;
  border: 1.5px solid rgba(255,255,255,0.14);
  border-radius: 6px;
  overflow: hidden;
}
.libList .reportRow { padding: clamp(9px,1.2vw,13px) clamp(10px,1.4vw,15px); }
.libList .reportRow:hover { background: rgba(238,140,58,0.07); }
.libList .reportRowActive { background: rgba(238,140,58,0.09); border-left: 3px solid var(--orange); }
.libList .rptTitle { color: #1a2e30; }
.libList .rowChevron { color: rgba(26,46,48,0.35); }
.libList .reportRow:hover .rowChevron { color: var(--orange); }
.libList .iconFrame { background: rgba(238,140,58,0.12); }
/* the forensic detail drawer stays black on purpose -- it is the one object
   in the library that should look like a vault opening. */
.libList .detailBox { border-top: 1px solid rgba(255,255,255,0.08); }
'''

# ----------------------------------------------------------------------------
# 7. Addendum entry
# ----------------------------------------------------------------------------
ADDENDUM = '''

- fix72 (2026-09-17): Reports tab rebuilt around one rule -- the builder IS the reports system, everything else feeds it from the top. The four canned-report drawers (FINANCIAL / OPERATIONAL / SYSTEM / MORE) are gone from under the studio; their twelve pillars now live in ONE-CLICK REPORTS, the first section inside the studio on the REPORTS tab, grouped under FINANCIAL / OPERATIONAL / SYSTEM / MORE labels with the same expand-for-schema-and-download rows, restyled as white cards on the dark panel body (the black forensic detail drawer stays). Non-financial roles get the SECURITY HANDBRAKE card inside that library instead of a financial drawer. The RESULTS table is now the last block on the Reports tab. Dropdown faults: every studio select loses the browser arrow and the browser height (the old flex: 1 1 150px became a ~150px-tall box inside the column-flex picker), gains an orange chevron background, a fixed 38px height, styled options and a real disabled state (dashed border, grey chevron, not-allowed cursor). DATA SOURCE rethought: icon frame + full-width dataset pick + RELOAD on one row. GROUP / COMPARE rethought: group-by and split-by share one row with a VS tag between them plus an unlock hint; condition and measure selects sit in row-flex wrappers so they stretch instead of ballooning. Contrast faults: hint text, mini labels and section labels were ink-grey written for a light surface but sitting on dark panel bodies -- now light-on-dark.
'''

# ============================================================================
# PATCHES
# ============================================================================
print('=' * 72)
print(' GOLDEN SEED fix72 -- reports integration + dropdown/panel restyle')
print('=' * 72)

# -- ReportHub.jsx ----------------------------------------------------------
# a) delete the four drawers under the studio (financial ternary through the
#    MORE REPORTS closing brace). Lazy match: the tail markers are unique.
rpatch(HUB,
       r'\{hasFinancialAccess \? \([\s\S]*?label="MORE REPORTS"[\s\S]*?</DrawerPanel>\s*\)\}',
       '',
       'Hub: four canned drawers removed from under the studio')

# b) the library node is built just before the main return
rpatch(HUB,
       r'return \(\n\s*<div className=\{styles\.container\}>',
       LIB_JSX,
       'Hub: library node inserted before main return')

# c) hand the library to the studio on the REPORTS tab
rpatch(HUB,
       r'<ReportStudio\s+canSeeMoney=\{hasFinancialAccess\}\s+mode="report"\s+reloadToken=\{reloadToken\}\s*/>',
       r'<ReportStudio canSeeMoney={hasFinancialAccess} mode="report" reloadToken={reloadToken} quickExports={library} />',
       'Hub: studio receives quickExports on the REPORTS tab')

# d) the outer drawer is the whole system now, not just the builder
patch(HUB,
      'label="BUILD YOUR OWN REPORT"',
      'label="REPORT STUDIO"',
      'Hub: studio drawer renamed REPORT STUDIO')

# -- ReportStudio.jsx --------------------------------------------------------
# e) new prop
patch(STU,
      "const ReportStudio = ({ canSeeMoney = false, mode = 'report', reloadToken = 0 }) => {",
      "const ReportStudio = ({ canSeeMoney = false, mode = 'report', reloadToken = 0, quickExports = null }) => {",
      'Studio: quickExports prop added')

# f) ONE-CLICK REPORTS becomes the first section in the studio
rpatch(STU,
       r'<div className=\{styles\.studio\}>',
       lambda m: m.group(0) + '\n' + QUICK_JSX.rstrip('\n'),
       'Studio: ONE-CLICK REPORTS section inserted first')

# g) DATA SOURCE bar rebuild (old chipRow/picker block, comment included)
rpatch(STU,
       r'\{/\* A select, not a row of chips[\s\S]*?</div>',
       lambda m: DATASET_JSX,
       'Studio: DATA SOURCE bar rebuilt')

# h) GROUP / COMPARE row rebuild
rpatch(STU,
       r'<div className=\{styles\.pickerGrid\}>[\s\S]*?</div>',
       lambda m: COMPARE_JSX,
       'Studio: GROUP / COMPARE row rebuilt')

# i) every remaining bare select gets a row-flex wrapper (conditions+measures)
rpatch(STU,
       r'(<select\s+className=\{styles\.select\}\s+value=\{c\.field\}[\s\S]*?</select>)',
       r'<span className={styles.selectWrap}>\1</span>',
       'Studio: condition field select wrapped')
rpatch(STU,
       r'(<select\s+className=\{styles\.select\}\s+value=\{c\.op\}[\s\S]*?</select>)',
       r'<span className={styles.selectWrap}>\1</span>',
       'Studio: condition operator select wrapped')
rpatch(STU,
       r'(<select\s+className=\{styles\.select\}\s+value=\{m\.agg\}[\s\S]*?</select>)',
       r'<span className={styles.selectWrap}>\1</span>',
       'Studio: measure aggregation select wrapped')
rpatch(STU,
       r'(<select\s+className=\{styles\.select\}\s+value=\{m\.field\}[\s\S]*?</select>)',
       r'<span className={styles.selectWrap}>\1</span>',
       'Studio: measure field select wrapped')

# -- CSS layers (appended, cascade wins, zero anchor risk) -------------------
append(STUCSS, STU_CSS, 'Studio CSS: dropdown + panel restyle layer appended')
append(HUBCSS, HUB_CSS, 'Hub CSS: library-on-dark styles appended')
append(ADD, ADDENDUM, 'Addendum: fix72 entry appended')

# ============================================================================
# WRITE + GIT
# ============================================================================
for rel in (HUB, HUBCSS, STU, STUCSS, ADD):
    save(rel)
print('')
print('All files written.')
print('')
print('git: staging, committing, pushing...')
MSG = ('fix72: canned reports folded into a ONE-CLICK library at the top of '
       'the studio, results table last, native selects fully styled, '
       'dataset + compare panels rethought, dark-body contrast faults fixed')
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Wait for the green tick on Render, then test only once you say so.')