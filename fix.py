#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP -- fix74 PATCHER
================================================================================
 WHAT:
   1. Search icon centred inside the search bar (was pinned to the top).
   2. NARROW IT DOWN + COLUMNS TO SHOW merged into ONE panel; all panel
      names shortened: PRESETS / SOURCE / FILTERS / GROUPING / RESULTS.
   3. The save-view input in SOURCE restyled as a normal in-page search-style
      box (icon inside left, capped width, 36px) under a "SAVE AS" label;
      every control height in the tool rows locked to 36px.
   4. MATCH label sits above its ALL/ANY chips like a real field label.
   5. Every open dropdown list (Pick lists + columns checklist) restyled to
      the app's dark panel language: navy body, orange border, cream text,
      orange-soft hover, orange left-bar on the chosen row.
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
# 1. MATCH becomes a labelled field (label above the chips)
# ----------------------------------------------------------------------------
MATCH_JSX = '''                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Match</span>
                        <span className={styles.chipGroup}>
                            <Tooltip label="Every condition must be true">
                                <button className={mergeMode === 'AND' ? styles.chipActive : styles.chip} onClick={() => setMergeMode('AND')}>ALL</button>
                            </Tooltip>
                            <Tooltip label="Any one condition is enough">
                                <button className={mergeMode === 'OR' ? styles.chipActive : styles.chip} onClick={() => setMergeMode('OR')}>ANY</button>
                            </Tooltip>
                        </span>
                    </label>'''

# ----------------------------------------------------------------------------
# 2. SAVE AS field: a normal in-page search-style box
# ----------------------------------------------------------------------------
SAVE_JSX = '''                    <label className={styles.toolField}>
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
                    </label>'''

# ----------------------------------------------------------------------------
# 3. Columns picker folded into the FILTERS panel as one tool row
# ----------------------------------------------------------------------------
COLS_ROW_JSX = '''                <div className={styles.toolRow}>
                    <label className={styles.toolField}>
                        <span className={styles.miniLabel}>Columns</span>
                        <div className={styles.dropdown} ref={colMenuRef}>
                            <button
                                type="button"
                                className={styles.dropdownBtn}
                                onClick={() => setColMenuOpen(o => !o)}
                                aria-expanded={colMenuOpen}
                            >
                                <span>{columns.length === 0 ? 'No columns picked' : `${columns.length} of ${fields.length} columns`}</span>
                                <FiChevronDown className={colMenuOpen ? styles.dropdownIconOpen : ''} aria-hidden="true" />
                            </button>
                            {colMenuOpen && (
                                <div className={styles.dropdownList}>
                                    <div className={styles.dropdownActions}>
                                        <button className={styles.miniBtn} onClick={() => setColumns(fields.map(fl => fl.key))}>ALL</button>
                                        <button className={styles.miniBtn} onClick={() => setColumns([])}>NONE</button>
                                        <button className={styles.miniBtn} onClick={() => setColumns(dataset.defaultColumns.filter(k => fields.some(fl => fl.key === k)))}>RESET</button>
                                    </div>
                                    {fields.map(fl => (
                                        <label key={fl.key} className={styles.dropdownOption}>
                                            <input
                                                type="checkbox"
                                                checked={columns.includes(fl.key)}
                                                onChange={() => toggleColumn(fl.key)}
                                            />
                                            {fl.label}
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>
                    </label>
                    <p className={styles.hint}>Row-by-row table only -- grouped results show your measures.</p>
                </div>
            </CollapsibleSection>
            <CollapsibleSection
                icon={<FiColumns'''

# ----------------------------------------------------------------------------
# 4. CSS layer: centring, heights, chip group, save box, dark popovers
# ----------------------------------------------------------------------------
STU_CSS = '''

/* fix74 -- CENTRING, HEIGHTS, MERGED FILTERS PANEL, DARK POPOVERS.
   Appended on purpose: cascade wins over the earlier layers. */

/* 1. icons centred in their bars */
.searchBox .searchIcon,
.viewBox .boxIcon { top: 50%; transform: translateY(-50%); }

/* 2. heights locked so no control towers over its row again */
.pickBtn, .searchBox, .viewBox { height: 36px; }

/* 3. chip groups inside a labelled field */
.chipGroup { display: flex; flex-wrap: wrap; gap: 6px; }

/* 4. SAVE AS box: same anatomy as the search box, smaller */
.viewBox {
  position: relative; display: flex;
  width: clamp(150px,18vw,210px);
  background: #fff; border: 1.5px solid var(--paper-edge); border-radius: var(--radius-sm);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.viewBox:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-soft); }
.boxIcon { position: absolute; left: 10px; color: var(--orange); font-size: 13px; pointer-events: none; }
.viewBox .viewInput {
  height: 100%; width: 100%; border: none; background: transparent;
  padding: 0 10px 0 30px; box-shadow: none;
}
.viewBox .viewInput:focus { outline: none; box-shadow: none; }

/* 5. open dropdown lists = the app's dark panel language, not white popups */
.pickList {
  background: #162a2c;
  border: 2px solid var(--orange);
  box-shadow: 0 18px 40px rgba(0,0,0,0.5);
}
.pickOption, .pickOptionActive { color: rgba(255,255,255,0.85); }
.pickOption:hover { background: rgba(238,140,58,0.12); }
.pickOptionActive {
  background: rgba(238,140,58,0.16);
  border-left-color: var(--orange);
  color: var(--orange);
}
.dropdownList {
  background: #162a2c;
  border: 2px solid var(--orange);
  box-shadow: 0 18px 40px rgba(0,0,0,0.5);
}
.dropdownActions { background: #162a2c; border-bottom: 1px solid rgba(255,255,255,0.08); }
.dropdownOption { color: rgba(255,255,255,0.85); border-bottom: 1px solid rgba(255,255,255,0.05); }
.dropdownOption:last-child { border-bottom: none; }
.dropdownOption:hover { background: rgba(238,140,58,0.12); }
.miniBtn {
  background: rgba(255,255,255,0.06);
  border: 1.5px solid rgba(255,255,255,0.18);
  color: rgba(255,255,255,0.85);
}
.miniBtn:hover { border-color: var(--orange); color: var(--orange); background: rgba(238,140,58,0.12); }

/* 6. the columns hint shares its row with the picker */
.toolRow .hint { align-self: flex-end; padding-bottom: 9px; }
'''

# ----------------------------------------------------------------------------
# 5. Addendum entry
# ----------------------------------------------------------------------------
ADDENDUM = '''

- fix74 (2026-09-17): Report Studio panel pass per David's review. NARROW IT DOWN and COLUMNS TO SHOW are ONE panel now; every panel name is one word: PRESETS (canned library), SOURCE, FILTERS (search + match + conditions + columns picker), GROUPING, RESULTS. The save-view input in SOURCE stopped being a mystery full-size bar: it is a normal in-page search-style box (icon inside left, capped width, 36px) under a SAVE AS label with a "View name..." placeholder. Search icon is vertically centred in its bar (the new bar is not a flex box like the old one, so absolute-without-top pinned it to the ceiling). MATCH is a labelled field with ALL/ANY under the label instead of floating at the row's bottom edge. Every open dropdown list (Pick lists and the columns checklist) now uses the app's dark panel language: navy #162a2c body, orange border, cream option text, orange-soft hover, orange left-bar and orange text on the chosen row, dark action row for ALL/NONE/RESET. Control heights in the tool rows locked to 36px.
'''

# ============================================================================
# PATCHES
# ============================================================================
print('=' * 72)
print(' GOLDEN SEED fix74 -- merged FILTERS panel, short names, dark popovers')
print('=' * 72)

# a) MATCH label above its chips
rpatch(STU,
       r'<span className=\{styles\.miniLabel\}>Match</span>[\s\S]*?Any one condition is enough">\s*<button[^>]*>ANY</button>\s*</Tooltip>',
       lambda m: MATCH_JSX,
       'Studio: MATCH becomes a labelled field')

# b) SAVE AS box replaces the plain tall input
rpatch(STU,
       r'<label className=\{styles\.toolField\}>\s*<span className=\{styles\.miniLabel\}>Save view</span>[\s\S]*?</label>',
       lambda m: SAVE_JSX,
       'Studio: SAVE AS search-style box')

# c) columns picker moves inside the FILTERS panel (insert row, reopen tag)
rpatch(STU,
       r'</CollapsibleSection>\s*<CollapsibleSection\s+icon=\{<FiColumns',
       lambda m: COLS_ROW_JSX,
       'Studio: columns row folded into FILTERS panel')

# d) the old standalone COLUMNS section is now gone
rpatch(STU,
       r'<CollapsibleSection\s+icon=\{<FiColumns[\s\S]*?</CollapsibleSection>',
       '',
       'Studio: standalone COLUMNS section removed')

# e) short panel names
patch(STU, 'title="ONE-CLICK REPORTS"', 'title="PRESETS"', 'Studio: panel renamed PRESETS')
patch(STU, 'title="DATA SOURCE"', 'title="SOURCE"', 'Studio: panel renamed SOURCE')
patch(STU, 'title="NARROW IT DOWN"', 'title="FILTERS"', 'Studio: panel renamed FILTERS')
patch(STU, 'title="GROUP, MEASURE & COMPARE"', 'title="GROUPING"', 'Studio: panel renamed GROUPING')

# f) CSS layer
append(STUCSS, STU_CSS, 'Studio CSS: centring + heights + dark popovers layer appended')
append(ADD, ADDENDUM, 'Addendum: fix74 entry appended')

# ============================================================================
# WRITE + GIT
# ============================================================================
for rel in (STU, STUCSS, ADD):
    save(rel)
print('')
print('All files written.')
print('')
print('git: staging, committing, pushing...')
MSG = ('fix74: FILTERS panel merged (narrow + columns), one-word panel names, '
       'SAVE AS box styled like in-page search, centred search icon, '
       'dark app-language dropdown lists, 36px control heights')
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Wait for the green tick on Render, then test only once you say so.')