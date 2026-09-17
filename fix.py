#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP -- fix73 PATCHER
================================================================================
 WHAT:
   1. Every native <select> in the Report Studio is replaced by one custom
      themed dropdown component (Pick): white button, ink text, orange
      chevron, popover list with orange border / orange-soft hover / orange
      left-bar on the chosen row. No browser-default styling left anywhere.
   2. Space efficiency, Intake-style: controls live in compact tool rows with
      the label above the control and fixed clamp() widths.
      - DATA SOURCE: dataset pick + RELOAD + save-view input + SAVE VIEW on
        one row (the save-view bar is folded into it and deleted).
      - NARROW IT DOWN: search box + MATCH ALL/ANY + ADD CONDITION +
        CLEAR ALL on one row; conditions stack tightly under it.
      - GROUP / COMPARE: group pick + VS + compare pick on one row.
   3. Phone rule kept: under 640px every control goes full-width per row.
 HOW: run  py fix.py  from the project root. Prints OK / MISSING per patch.
      Commits and pushes at the end.
================================================================================
"""

import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

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
    if callable(new):
        out, n = re.subn(pat, new, s, count=1)
    else:
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
# 1. The custom dropdown component (module scope, shared by every control)
# ----------------------------------------------------------------------------
PICK_JSX = '''const Pick = ({ value, options, onChange, placeholder = 'Choose...', disabled = false, ariaLabel = '', icon = null, className = '' }) => {
    const [open, setOpen] = useState(false);
    const ref = useRef(null);
    useEffect(() => {
        const onDown = (e) => {
            if (ref.current && !ref.current.contains(e.target)) setOpen(false);
        };
        document.addEventListener('mousedown', onDown);
        return () => document.removeEventListener('mousedown', onDown);
    }, []);
    const current = options.find(o => o.value === value);
    return (
        <div className={`${styles.pick} ${className}`} ref={ref}>
            <button
                type="button"
                className={styles.pickBtn}
                disabled={disabled}
                aria-expanded={open}
                aria-label={ariaLabel}
                onClick={() => setOpen(o => !o)}
            >
                {icon && <span className={styles.pickLead} aria-hidden="true">{icon}</span>}
                <span className={current ? styles.pickValue : styles.pickPlaceholder}>
                    {current ? current.label : placeholder}
                </span>
                <FiChevronDown className={open ? styles.pickIconOpen : ''} aria-hidden="true" />
            </button>
            {open && (
                <div className={styles.pickList} role="listbox" aria-label={ariaLabel}>
                    {options.map(o => (
                        <button
                            type="button"
                            key={String(o.value)}
                            role="option"
                            aria-selected={o.value === value}
                            className={o.value === value ? styles.pickOptionActive : styles.pickOption}
                            onClick={() => { onChange(o.value); setOpen(false); }}
                        >
                            {o.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

const ReportStudio = ({'''

# ----------------------------------------------------------------------------
# 2. DATA SOURCE: one compact tool row (dataset pick + reload + save view)
# ----------------------------------------------------------------------------
DATASET2_JSX = '''                <div className={styles.toolRow}>
                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Dataset</span>
                        <Pick
                            className={styles.wDataset}
                            icon={<FiDatabase size={13} aria-hidden="true" />}
                            ariaLabel="Dataset"
                            value={datasetKey}
                            options={available.map(ds => ({ value: ds.key, label: ds.label }))}
                            onChange={v => setDatasetKey(v)}
                        />
                    </label>
                    <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}>
                        <FiRefreshCw size={11} aria-hidden="true" /> RELOAD
                    </button>
                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Save view</span>
                        <input
                            className={styles.viewInput}
                            placeholder="Name this setup..."
                            value={viewName}
                            onChange={e => setViewName(e.target.value)}
                        />
                    </label>
                    <Tooltip label="Save the current dataset, filters, columns and grouping. Saved on this device.">
                        <button className={styles.chipActive} onClick={saveCurrentView} disabled={!viewName.trim()}>
                            <FiSave size={11} aria-hidden="true" /> SAVE VIEW
                        </button>
                    </Tooltip>
                </div>'''

# ----------------------------------------------------------------------------
# 3. NARROW IT DOWN: search + match + add/clear on one compact tool row
# ----------------------------------------------------------------------------
NARROW_TOP_JSX = '''                <div className={styles.toolRow}>
                    <div className={styles.searchBox}>
                        <FiSearch className={styles.searchIcon} aria-hidden="true" />
                        <input
                            className={styles.searchInput}
                            placeholder="Free text across every text column -- a name, a plot, a district..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                        />
                        {search && (
                            <button className={styles.searchClear} onClick={() => setSearch('')} aria-label="Clear search">
                                <FiX size={13} aria-hidden="true" />
                            </button>
                        )}
                    </div>
                    <span className={styles.miniLabel}>Match</span>
                    <Tooltip label="Every condition must be true">
                        <button className={mergeMode === 'AND' ? styles.chipActive : styles.chip} onClick={() => setMergeMode('AND')}>ALL</button>
                    </Tooltip>
                    <Tooltip label="Any one condition is enough">
                        <button className={mergeMode === 'OR' ? styles.chipActive : styles.chip} onClick={() => setMergeMode('OR')}>ANY</button>
                    </Tooltip>
                    <button className={styles.chip} onClick={addCondition}>
                        <FiPlus size={11} aria-hidden="true" /> ADD CONDITION
                    </button>
                    {conditions.length > 0 && (
                        <button className={styles.chip} onClick={() => setConditions([])}>
                            <FiX size={11} aria-hidden="true" /> CLEAR ALL
                        </button>
                    )}
                </div>'''

# ----------------------------------------------------------------------------
# 4. Condition row picks
# ----------------------------------------------------------------------------
COND_FIELD_JSX = '''                            <Pick
                                className={styles.wMid}
                                ariaLabel="Field"
                                value={c.field}
                                placeholder="Choose a field..."
                                options={fields.map(fl => ({ value: fl.key, label: fl.label }))}
                                onChange={v => patchCondition(c.uid, { field: v, op: '', value: '', value2: '' })}
                            />'''

COND_OP_JSX = '''                            <Pick
                                className={styles.wSm}
                                ariaLabel="Condition"
                                value={c.op}
                                placeholder="is..."
                                disabled={!fld}
                                options={ops.map(o => ({ value: o.key, label: o.label }))}
                                onChange={v => patchCondition(c.uid, { op: v })}
                            />'''

# ----------------------------------------------------------------------------
# 5. GROUP / COMPARE: one row, two picks, VS tag between
# ----------------------------------------------------------------------------
GROUP2_JSX = '''                <div className={styles.toolRow}>
                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Group by</span>
                        <Pick
                            className={styles.wDataset}
                            ariaLabel="Group by"
                            value={groupBy}
                            options={[{ value: '', label: '(no grouping -- show every row)' }, ...fields.map(fl => ({ value: fl.key, label: fl.label }))]}
                            onChange={v => setGroupBy(v)}
                        />
                    </label>
                    <span className={styles.compareVs} aria-hidden="true">VS</span>
                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Compare / split by</span>
                        <Pick
                            className={styles.wDataset}
                            ariaLabel="Compare or split by"
                            value={splitBy}
                            disabled={!groupBy}
                            options={[{ value: '', label: '(none)' }, ...fields.filter(fl => fl.key !== groupBy).map(fl => ({ value: fl.key, label: fl.key === groupBy ? fl.label : fl.label }))]}
                            onChange={v => setSplitBy(v)}
                        />
                    </label>
                </div>'''

# ----------------------------------------------------------------------------
# 6. Measure row picks
# ----------------------------------------------------------------------------
MEASURE_AGG_JSX = '''                            <Pick
                                className={styles.wSm}
                                ariaLabel="Measure"
                                value={m.agg}
                                options={AGGREGATIONS.map(a => ({ value: a.key, label: a.label }))}
                                onChange={v => patchMeasure(i, { agg: v })}
                            />'''

MEASURE_FIELD_JSX = '''                            <Pick
                                className={styles.wMid}
                                ariaLabel="Measure field"
                                value={m.field}
                                placeholder="Choose a field..."
                                options={fields
                                    .filter(fl => (m.agg === 'distinct' ? true : ['number', 'money', 'percent'].includes(fl.type)))
                                    .map(fl => ({ value: fl.key, label: fl.label }))}
                                onChange={v => patchMeasure(i, { field: v })}
                            />'''

# ----------------------------------------------------------------------------
# 7. CSS layer: the Pick dropdown + compact tool rows
# ----------------------------------------------------------------------------
STU_CSS = '''

/* fix73 -- CUSTOM DROPDOWNS + COMPACT TOOL ROWS (Intake is the reference:
   label above the control, controls sized to their content, nothing
   browser-default anywhere). Appended on purpose: cascade wins. */

/* -- the Pick dropdown -------------------------------------------------- */
.pick { position: relative; min-width: 0; }
.pickBtn {
  width: 100%; height: 36px; padding: 0 30px 0 10px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--paper-edge); background: #fff; color: var(--ink);
  font-family: 'Inter', sans-serif; font-size: clamp(11px,1.05vw,12.5px); font-weight: 700;
  cursor: pointer; display: flex; align-items: center; gap: 8px; text-align: left;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.pickBtn:hover:not(:disabled) { border-color: var(--orange); }
.pickBtn:focus-visible { outline: none; border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-soft); }
.pickBtn:disabled { cursor: not-allowed; background: #f1eeea; border-style: dashed; color: rgba(26,46,48,0.45); }
.pickBtn > svg { position: absolute; right: 10px; color: var(--orange); transition: transform 0.2s; }
.pickBtn:disabled > svg { color: rgba(26,46,48,0.35); }
.pickIconOpen { transform: rotate(180deg); }
.pickLead { color: var(--orange); display: flex; flex-shrink: 0; }
.pickValue { color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pickPlaceholder { color: rgba(26,46,48,0.42); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pickList {
  position: absolute; top: calc(100% + 4px); left: 0; z-index: 500;
  width: max-content; min-width: 100%; max-width: 340px;
  background: #fff; border: 2px solid var(--orange); border-radius: var(--radius-sm);
  box-shadow: 0 18px 40px rgba(0,0,0,0.35);
  max-height: 264px; overflow-y: auto; padding: 4px;
  scrollbar-width: thin; scrollbar-color: var(--orange) transparent;
}
.pickList::-webkit-scrollbar { width: 6px; }
.pickList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }
.pickList::-webkit-scrollbar-track { background: transparent; }
.pickOption, .pickOptionActive {
  display: flex; width: 100%; text-align: left;
  border: none; border-left: 3px solid transparent; border-radius: 4px;
  background: transparent; color: var(--ink);
  font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700;
  padding: 7px 10px; cursor: pointer; transition: background 0.15s;
}
.pickOption:hover { background: var(--orange-soft); }
.pickOptionActive { background: var(--orange-soft); border-left-color: var(--orange); color: #b45309; }

/* -- compact tool rows --------------------------------------------------- */
.toolRow {
  display: flex; flex-wrap: wrap; align-items: flex-end;
  gap: clamp(6px,0.9vw,10px);
  margin-bottom: clamp(8px,1.1vw,12px);
}
.toolRow:last-child { margin-bottom: 0; }
.toolField { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.toolField .pick { width: 100%; }
.wDataset { width: clamp(180px,22vw,260px); }
.wMid { width: clamp(150px,18vw,210px); }
.wSm { width: clamp(120px,15vw,170px); }

/* search box: capped, icon inside, no more full-width bar */
.searchBox {
  position: relative; width: clamp(200px,26vw,320px); height: 36px;
  background: #fff; border: 1.5px solid var(--paper-edge); border-radius: var(--radius-sm);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.searchBox:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-soft); }
.searchBox .searchIcon { left: 10px; font-size: 14px; }
.searchBox .searchInput { padding: 0 30px 0 32px; font-size: clamp(11px,1.05vw,12.5px); }
.searchBox .searchClear { right: 6px; }

/* save-view input: a field, not a banner */
.viewInput {
  height: 36px; width: clamp(160px,20vw,240px); padding: 0 10px;
  border-radius: var(--radius-sm); border: 1.5px solid var(--paper-edge);
  background: #fff; color: var(--ink);
  font-family: 'Inter', sans-serif; font-size: clamp(11px,1.05vw,12.5px); font-weight: 600;
}
.viewInput::placeholder { color: rgba(26,46,48,0.38); font-weight: 500; }
.viewInput:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-soft); }

/* condition + measure rows stay tight */
.condRow { padding: 6px; gap: 6px; }
.condRow + .condRow { margin-top: 6px; }
.toolRow + .condRow { margin-top: clamp(8px,1.1vw,12px); }
.condRow .input { flex: 0 1 auto; width: clamp(110px,12vw,150px); min-width: 0; }
.chipRow { margin-top: clamp(6px,0.9vw,10px); }

/* columns dropdown: same capped discipline */
.dropdown { max-width: 320px; }

@media (max-width: 640px) {
  .wDataset, .wMid, .wSm, .searchBox, .viewInput { width: 100%; flex: 1 1 100%; }
  .condRow .input { width: 100%; flex: 1 1 100%; }
}
'''

# ----------------------------------------------------------------------------
# 8. Addendum entry
# ----------------------------------------------------------------------------
ADDENDUM = '''

- fix73 (2026-09-17): Report Studio controls rebuilt against the Intake reference -- zero browser-default UI left. One custom themed dropdown component (Pick) replaces every native select in the studio (dataset, group by, compare/split, condition field, condition operator, measure type, measure field): white button with ink text and an orange chevron that rotates open, popover list with orange border, orange-soft hover and an orange left-bar on the chosen row instead of the browser blue. Space efficiency: controls now sit in compact tool rows with the label above the control and fixed clamp() widths -- DATA SOURCE is one row (dataset pick with an inline database icon + RELOAD + save-view input + SAVE VIEW, the old full-width save bar deleted), NARROW IT DOWN is one row (capped search box with the icon inside + MATCH ALL/ANY + ADD CONDITION + CLEAR ALL), GROUP/COMPARE is one row (group pick + VS tag + compare pick). Condition and measure rows stay tight with capped value inputs. Under 640px every control goes full-width on its own row. The ONE-CLICK REPORTS library and the RESULTS-last order from fix72 are unchanged.
'''

# ============================================================================
# PATCHES
# ============================================================================
print('=' * 72)
print(' GOLDEN SEED fix73 -- custom dropdowns + compact Intake-style rows')
print('=' * 72)

# a) Pick component lands just above the ReportStudio component
rpatch(STU,
       r'const ReportStudio = \(\{',
       lambda m: PICK_JSX,
       'Studio: Pick dropdown component added')

# b) DATA SOURCE bar -> compact tool row (also absorbs the save-view bar)
rpatch(STU,
       r'<div className=\{styles\.datasetBar\}>[\s\S]*?RELOAD\s*</button>\s*</div>',
       lambda m: DATASET2_JSX,
       'Studio: DATA SOURCE row rebuilt compact')

# c) old standalone save-view bar removed (folded into the row above)
rpatch(STU,
       r'<div className=\{styles\.viewBar\}>[\s\S]*?</Tooltip>\s*</div>',
       '',
       'Studio: old full-width save-view bar removed')

# d) search bar + match chips -> one compact tool row with add/clear
rpatch(STU,
       r'<div className=\{styles\.searchRow\}>[\s\S]*?</Tooltip>\s*</div>',
       lambda m: NARROW_TOP_JSX,
       'Studio: NARROW IT DOWN row rebuilt compact')

# e) the old add-condition row at the bottom is now redundant
rpatch(STU,
       r'<div className=\{styles\.chipRow\}>\s*<button className=\{styles\.chip\} onClick=\{addCondition\}>[\s\S]*?</div>',
       '',
       'Studio: duplicate add-condition row removed')

# f) condition field + operator selects -> Pick
rpatch(STU,
       r'<span className=\{styles\.selectWrap\}>\s*<select\s+className=\{styles\.select\}\s+value=\{c\.field\}[\s\S]*?</span>',
       lambda m: COND_FIELD_JSX,
       'Studio: condition field select -> Pick')
rpatch(STU,
       r'<span className=\{styles\.selectWrap\}>\s*<select\s+className=\{styles\.select\}\s+value=\{c\.op\}[\s\S]*?</span>',
       lambda m: COND_OP_JSX,
       'Studio: condition operator select -> Pick')

# g) group / compare selects -> Pick row
rpatch(STU,
       r'<div className=\{styles\.compareRow\}>[\s\S]*?</label>\s*</div>',
       lambda m: GROUP2_JSX,
       'Studio: GROUP / COMPARE row rebuilt with Picks')

# h) measure selects -> Pick
rpatch(STU,
       r'<span className=\{styles\.selectWrap\}>\s*<select\s+className=\{styles\.select\}\s+value=\{m\.agg\}[\s\S]*?</span>',
       lambda m: MEASURE_AGG_JSX,
       'Studio: measure type select -> Pick')
rpatch(STU,
       r'<span className=\{styles\.selectWrap\}>\s*<select\s+className=\{styles\.select\}\s+value=\{m\.field\}[\s\S]*?</span>',
       lambda m: MEASURE_FIELD_JSX,
       'Studio: measure field select -> Pick')

# i) CSS layer
append(STUCSS, STU_CSS, 'Studio CSS: Pick dropdown + tool row layer appended')
append(ADD, ADDENDUM, 'Addendum: fix73 entry appended')

# ============================================================================
# WRITE + GIT
# ============================================================================
for rel in (STU, STUCSS, ADD):
    save(rel)
print('')
print('All files written.')
print('')
print('git: staging, committing, pushing...')
MSG = ('fix73: studio controls rebuilt Intake-style -- one custom themed '
       'dropdown replaces every native select, dataset/search/save-view/'
       'match/add-condition share compact tool rows instead of full-width bars')
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Wait for the green tick on Render, then test only once you say so.')