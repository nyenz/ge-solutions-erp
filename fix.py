#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix86 -- REPORTS PAGE DESIGN PARITY PASS
# Closes the gap between the approved Reports-page prototype and the live
# ReportStudio: chart-type picker becomes a dropdown chip (adds the missing
# AREA option), PDF export gets its own dark/secondary button so it reads as
# a different action from CSV, an export-model note explains what each file
# contains, the DEFAULT VIEW row gets a visible highlight, the catalogue
# groups into labelled sections while on the ALL tab, every catalogue row
# gets an explicit expand/collapse hint, and the "Who / what" entity picker
# becomes type-to-search instead of a plain scroll list. Also widens the
# global Inter font-weight import so the app's own "900" buttons render as
# true black weight instead of a synthetic bold.
# ============================================================================
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
STU = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
CSS = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')
IDX = R('erp-frontend', 'src', 'index.css')
ADD = R('LLM_CONTEXT_ADDENDUM.md')

BUF = {}
def get(p):
    if p not in BUF:
        with open(p, 'r', encoding='utf-8', errors='replace') as f: BUF[p] = f.read()
    return BUF[p]
def save(p):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(BUF[p])
def patch(p, old, new, tag):
    s = get(p)
    if old in s:
        BUF[p] = s.replace(old, new, 1); print('OK      ' + tag)
    else:
        print('MISSING ' + tag)

print('=' * 72)
print(' GOLDEN SEED fix86 -- reports page design parity pass')
print('=' * 72)

# ---------------------------------------------------------------------------
# 1. Global font weights -- app only imported Inter 300/400/600/800, so any
#    "font-weight: 900" rule (most buttons/chips/labels in this app) fell
#    back to a synthetic bold instead of true black, unlike the prototype.
# ---------------------------------------------------------------------------
patch(IDX,
      "@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Inter:wght@300;400;600;800&family=Space+Mono&display=swap');",
      "@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Inter:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');",
      'index.css: widen Inter/Space Mono weights to match every font-weight used in Reports')

# ---------------------------------------------------------------------------
# 2. ReportStudio.jsx -- state + refs: add chart-dropdown state and
#    entity-search state, wire both into the existing outside-click handler.
# ---------------------------------------------------------------------------
patch(STU,
      "  const [colOpen, setColOpen] = useState(false);\n"
      "  const [sortOpen, setSortOpen] = useState(false);\n"
      "  const [entOpen, setEntOpen] = useState(false);\n"
      "  const colRef = useRef(null);\n"
      "  const sortRef = useRef(null);\n"
      "  const entRef = useRef(null);\n"
      "  const chartRef = useRef(null);\n"
      "  useEffect(() => {\n"
      "    const h = (e) => {\n"
      "      if (colRef.current && !colRef.current.contains(e.target)) setColOpen(false);\n"
      "      if (sortRef.current && !sortRef.current.contains(e.target)) setSortOpen(false);\n"
      "      if (entRef.current && !entRef.current.contains(e.target)) setEntOpen(false);\n"
      "    };\n"
      "    document.addEventListener('mousedown', h);\n"
      "    return () => document.removeEventListener('mousedown', h);\n"
      "  }, []);\n",
      "  const [colOpen, setColOpen] = useState(false);\n"
      "  const [sortOpen, setSortOpen] = useState(false);\n"
      "  const [entOpen, setEntOpen] = useState(false);\n"
      "  const [chartOpen, setChartOpen] = useState(false);\n"
      "  const [entQuery, setEntQuery] = useState('');\n"
      "  const colRef = useRef(null);\n"
      "  const sortRef = useRef(null);\n"
      "  const entRef = useRef(null);\n"
      "  const chartRef = useRef(null);\n"
      "  const chartDdRef = useRef(null);\n"
      "  useEffect(() => {\n"
      "    const h = (e) => {\n"
      "      if (colRef.current && !colRef.current.contains(e.target)) setColOpen(false);\n"
      "      if (sortRef.current && !sortRef.current.contains(e.target)) setSortOpen(false);\n"
      "      if (entRef.current && !entRef.current.contains(e.target)) setEntOpen(false);\n"
      "      if (chartDdRef.current && !chartDdRef.current.contains(e.target)) setChartOpen(false);\n"
      "    };\n"
      "    document.addEventListener('mousedown', h);\n"
      "    return () => document.removeEventListener('mousedown', h);\n"
      "  }, []);\n",
      'studio: add chartOpen/entQuery state + chartDdRef, wire into outside-click handler')

# ---------------------------------------------------------------------------
# 3. CHART_OPTS / CHART_MAP -- restore the AREA chart type the prototype
#    offers (the app's LineChart already renders a filled area under the
#    line, so AREA reuses it rather than needing a new SVG component).
# ---------------------------------------------------------------------------
patch(STU,
      "const CHART_MAP = { BAR: 'bars', COLUMN: 'column', LINE: 'line', DONUT: 'donut' };\n"
      "const CHART_OPTS = ['NONE','BAR','COLUMN','LINE','DONUT'];",
      "const CHART_MAP = { BAR: 'bars', COLUMN: 'column', LINE: 'line', AREA: 'line', DONUT: 'donut' };\n"
      "const CHART_OPTS = ['NONE','BAR','COLUMN','LINE','AREA','DONUT'];",
      'studio: restore AREA as a selectable chart type')

# ---------------------------------------------------------------------------
# 4. restList + catRowNode -- shared row renderer so the ALL tab can group
#    rows under labelled sections instead of one long flat list, and so the
#    expand/collapse hint (rule 7) only needs to live in one place.
# ---------------------------------------------------------------------------
patch(STU,
      "  const listed = groupTab === 'ALL' ? searched : searched.filter(d => d.group === groupTab);\n"
      "  const appliedDef = CATALOGUE.find(d => d.id === appliedId) || null;\n"
      "  const defaultName = (DEFAULTS[datasetKey] || {})[entity ? entity.type : 'ALL'] || '';\n"
      "  const defaultDef = CATALOGUE.find(d => d.title === defaultName && d.ds === datasetKey && (!d.money || canSeeMoney)) || null;\n"
      "  const recentDefs = recent.map(id => CATALOGUE.find(d => d.id === id)).filter(Boolean);\n",
      "  const listed = groupTab === 'ALL' ? searched : searched.filter(d => d.group === groupTab);\n"
      "  const appliedDef = CATALOGUE.find(d => d.id === appliedId) || null;\n"
      "  const defaultName = (DEFAULTS[datasetKey] || {})[entity ? entity.type : 'ALL'] || '';\n"
      "  const defaultDef = CATALOGUE.find(d => d.title === defaultName && d.ds === datasetKey && (!d.money || canSeeMoney)) || null;\n"
      "  const recentDefs = recent.map(id => CATALOGUE.find(d => d.id === id)).filter(Boolean);\n"
      "  const restList = listed.filter(d => !defaultDef || d.id !== defaultDef.id);\n"
      "  const entMatches = useMemo(() => {\n"
      "    const q = entQuery.trim().toUpperCase();\n"
      "    if (!q) return [];\n"
      "    const out = [];\n"
      "    entityTypes.forEach(t => {\n"
      "      entityValues(t.type).forEach(v => {\n"
      "        if (String(v).toUpperCase().indexOf(q) >= 0) out.push({ type: t.type, label: t.label, value: v });\n"
      "      });\n"
      "    });\n"
      "    return out.slice(0, 15);\n"
      "    // eslint-disable-next-line react-hooks/exhaustive-deps\n"
      "  }, [entQuery, entityTypes, rows]);\n",
      'studio: compute restList (default row excluded) + type-to-search entMatches')

patch(STU,
      "  const readout = (def) => {\n"
      "    let text = def.desc;\n"
      "    text += entity ? (' For ' + entity.label.toLowerCase() + ' ' + entity.value + '.') : (' Whole company.');\n"
      "    text += def.period ? (' Period: ' + periodHuman() + '.') : (' Right-now snapshot.');\n"
      "    const sc = def.sort || { col: 'first column', dir: 'asc' };\n"
      "    text += ' Sorted by ' + sc.col + ' ' + (sc.dir === 'desc' ? 'highest first.' : 'A to Z.');\n"
      "    return text;\n"
      "  };\n",
      "  const readout = (def) => {\n"
      "    let text = def.desc;\n"
      "    text += entity ? (' For ' + entity.label.toLowerCase() + ' ' + entity.value + '.') : (' Whole company.');\n"
      "    text += def.period ? (' Period: ' + periodHuman() + '.') : (' Right-now snapshot.');\n"
      "    const sc = def.sort || { col: 'first column', dir: 'asc' };\n"
      "    text += ' Sorted by ' + sc.col + ' ' + (sc.dir === 'desc' ? 'highest first.' : 'A to Z.');\n"
      "    return text;\n"
      "  };\n"
      "  const catRowNode = (def) => (\n"
      "    <div key={def.id} className={styles.catWrap}>\n"
      "      <button className={styles.catRow + (appliedId === def.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === def.id ? null : def.id)} aria-expanded={readId === def.id}>\n"
      "        <span className={styles.r1}>{def.title}<span className={styles.tag}>{def.chart !== 'NONE' ? def.chart : 'TABLE'} &middot; {def.group}</span><span className={styles.toggleHint}>{readId === def.id ? 'CLOSE \\u25B2' : 'WHAT IS THIS? \\u25BC'}</span></span>\n"
      "        <span className={styles.r2}>{def.desc}</span>\n"
      "      </button>\n"
      "      {readId === def.id && (\n"
      "        <div className={styles.readout}>\n"
      "          <div className={styles.readoutText}>{readout(def)}</div>\n"
      "          <button className={styles.useBtn} onClick={() => applyDef(def)}>USE THIS REPORT</button>\n"
      "        </div>\n"
      "      )}\n"
      "    </div>\n"
      "  );\n",
      'studio: add catRowNode (shared row renderer with expand/collapse hint)')

# ---------------------------------------------------------------------------
# 5. Entity field -- swap the plain "Change..." dropdown for a type-to-search
#    box that filters as you type, Enter picks the top match.
# ---------------------------------------------------------------------------
patch(STU,
      "                <button className={styles.pickBtn} onClick={() => setEntOpen(o => !o)} aria-expanded={entOpen}>\n"
      "                  <span>{entity ? 'Change...' : 'Whole company'}</span>\n"
      "                  <FiChevronDown className={entOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
      "                </button>\n"
      "                {entOpen && (\n"
      "                  <div className={styles.pickList}>\n"
      "                    <div className={styles.ddScroll}>\n"
      "                      <button className={styles.pickOption} onClick={() => { setEntity(null); setEntOpen(false); }}>WHOLE COMPANY</button>\n"
      "                      {entityTypes.map(t => entityValues(t.type).slice(0, 12).map(v => (\n"
      "                        <button key={t.type + v} className={styles.pickOption} onClick={() => { setEntity({ type: t.type, label: t.label, value: v }); setEntOpen(false); }}>\n"
      "                          {t.label}: {v}\n"
      "                        </button>\n"
      "                      )))}\n"
      "                    </div>\n"
      "                  </div>\n"
      "                )}\n",
      "                <input\n"
      "                  className={styles.entInput}\n"
      "                  value={entQuery}\n"
      "                  placeholder={entity ? 'Change...' : 'Type to search this source...'}\n"
      "                  onFocus={() => setEntOpen(true)}\n"
      "                  onChange={e => { setEntQuery(e.target.value); setEntOpen(true); }}\n"
      "                  onKeyDown={e => {\n"
      "                    if (e.key === 'Enter') {\n"
      "                      if (entMatches[0]) { setEntity(entMatches[0]); setEntQuery(''); setEntOpen(false); }\n"
      "                      e.preventDefault();\n"
      "                    }\n"
      "                  }}\n"
      "                  aria-label=\"Search who / what\"\n"
      "                />\n"
      "                {entOpen && (\n"
      "                  <div className={styles.pickList}>\n"
      "                    <div className={styles.ddScroll}>\n"
      "                      {!entQuery && <button className={styles.pickOption} onClick={() => { setEntity(null); setEntQuery(''); setEntOpen(false); }}>WHOLE COMPANY</button>}\n"
      "                      {!entQuery && <div className={styles.ddFootMsg}>TYPE TO SEARCH THIS SOURCE -- ENTER PICKS THE FIRST MATCH</div>}\n"
      "                      {entQuery && entMatches.length === 0 && <div className={styles.ddFootMsg}>NO MATCH IN THIS SOURCE</div>}\n"
      "                      {entQuery && entMatches.map(m => (\n"
      "                        <button key={m.type + m.value} className={styles.pickOption} onClick={() => { setEntity(m); setEntQuery(''); setEntOpen(false); }}>\n"
      "                          {m.value}<span className={styles.pickOptionTag}>{m.label}</span>\n"
      "                        </button>\n"
      "                      ))}\n"
      "                    </div>\n"
      "                  </div>\n"
      "                )}\n",
      'studio: entity picker becomes type-to-search (was a static scroll list)')

# ---------------------------------------------------------------------------
# 6. Preview head -- chart selector moves into the chip row as a dropdown
#    (adds AREA), PDF gets its own dark/secondary button, an export-model
#    note explains what CSV vs PDF actually contain.
# ---------------------------------------------------------------------------
patch(STU,
      "            <div className={styles.pvChips}>\n"
      "              <span className={styles.pvChip}>{entity ? entity.label.toUpperCase() + ' ' + entity.value : 'WHOLE SOURCE'}</span>\n"
      "              <span className={styles.pvChip}>{appliedDef.period ? periodHuman().toUpperCase() : 'AS AT TODAY'}</span>\n"
      "              <span className={styles.pvChip}>SORT {sort.col || 'DEFAULT'} {sort.dir.toUpperCase()}</span>\n"
      "              <span className={styles.pvChip}>{tableCols.length} COLUMNS</span>\n"
      "              <span className={styles.pvChip}>{sortedAll.length} ROWS MATCH</span>\n"
      "            </div>\n"
      "            <div className={styles.pvBtns}>\n"
      "              <button className={styles.useBtn} onClick={exportCSV} disabled={!sortedAll.length || !tableCols.length}>CSV -- THE DATA</button>\n"
      "              <button className={styles.useBtn} onClick={exportPDF} disabled={!sortedAll.length || !tableCols.length}>PDF -- THE DOCUMENT</button>\n"
      "            </div>\n"
      "          </div>\n"
      "          <div className={styles.chartChips}>\n"
      "            {CHART_OPTS.map(t => (\n"
      "              <button key={t} className={chartMode === t ? styles.cchipOn : styles.cchip} onClick={() => setChartMode(t)}>{t}</button>\n"
      "            ))}\n"
      "          </div>\n",
      "            <div className={styles.pvChips}>\n"
      "              <span className={styles.pvChip}>{entity ? entity.label.toUpperCase() + ' ' + entity.value : 'WHOLE SOURCE'}</span>\n"
      "              <span className={styles.pvChip}>{appliedDef.period ? periodHuman().toUpperCase() : 'AS AT TODAY'}</span>\n"
      "              <span className={styles.pvChip}>SORT {sort.col || 'DEFAULT'} {sort.dir.toUpperCase()}</span>\n"
      "              <span className={styles.pvChip}>{tableCols.length} COLUMNS</span>\n"
      "              <span className={styles.pvChip}>{sortedAll.length} ROWS MATCH</span>\n"
      "              <span className={styles.pvChipDd} ref={chartDdRef}>\n"
      "                CHART\n"
      "                <button className={styles.chartDdBtn} onClick={() => setChartOpen(o => !o)} aria-expanded={chartOpen}>\n"
      "                  {chartMode}<FiChevronDown className={chartOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
      "                </button>\n"
      "                {chartOpen && (\n"
      "                  <div className={styles.pickList}>\n"
      "                    <div className={styles.ddScroll}>\n"
      "                      {CHART_OPTS.map(t => (\n"
      "                        <button key={t} className={styles.pickOption + (chartMode === t ? ' ' + styles.pickOptionActive : '')} onClick={() => { setChartMode(t); setChartOpen(false); }}>{t}</button>\n"
      "                      ))}\n"
      "                    </div>\n"
      "                  </div>\n"
      "                )}\n"
      "              </span>\n"
      "            </div>\n"
      "            <div className={styles.pvBtns}>\n"
      "              <button className={styles.useBtn} onClick={exportCSV} disabled={!sortedAll.length || !tableCols.length}>CSV -- THE DATA</button>\n"
      "              <button className={styles.useBtnDark} onClick={exportPDF} disabled={!sortedAll.length || !tableCols.length}>PDF -- THE DOCUMENT</button>\n"
      "            </div>\n"
      "          </div>\n"
      "          <div className={styles.approachNote}>\n"
      "            CSV = every matching row, flat, for Excel. PDF = one document: cover with scope stamp and the chart, then all table pages in landscape with repeated headers. The screen table stays a sample so the page stays fast.\n"
      "          </div>\n",
      'studio: chart picker -> dropdown chip (+AREA), PDF -> secondary style, add export-model note')

# ---------------------------------------------------------------------------
# 7. Catalogue list -- default row gets a visible highlight class, and the
#    rest of the list groups into labelled sections while on the ALL tab
#    (matching the prototype's sticky "MONEY IN (4)" style section heads).
# ---------------------------------------------------------------------------
patch(STU,
      "          {defaultDef && (\n"
      "            <div className={styles.catWrap}>\n"
      "              <button className={styles.catRow + (appliedId === defaultDef.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === defaultDef.id ? null : defaultDef.id)} aria-expanded={readId === defaultDef.id}>\n"
      "                <span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.tag}>{defaultDef.chart !== 'NONE' ? defaultDef.chart : 'TABLE'} &middot; {defaultDef.group}</span></span>\n"
      "                <span className={styles.r2}>{defaultDef.desc}</span>\n"
      "              </button>\n"
      "              {readId === defaultDef.id && (\n"
      "                <div className={styles.readout}>\n"
      "                  <div className={styles.readoutText}>{readout(defaultDef)}</div>\n"
      "                  <button className={styles.useBtn} onClick={() => applyDef(defaultDef)}>USE THIS REPORT</button>\n"
      "                </div>\n"
      "              )}\n"
      "            </div>\n"
      "          )}\n"
      "          {listed.filter(d => !defaultDef || d.id !== defaultDef.id).length === 0 && !defaultDef && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}\n"
      "          {listed.filter(d => !defaultDef || d.id !== defaultDef.id).map(def => (\n"
      "            <div key={def.id} className={styles.catWrap}>\n"
      "              <button className={styles.catRow + (appliedId === def.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === def.id ? null : def.id)} aria-expanded={readId === def.id}>\n"
      "                <span className={styles.r1}>{def.title}<span className={styles.tag}>{def.chart !== 'NONE' ? def.chart : 'TABLE'} &middot; {def.group}</span></span>\n"
      "                <span className={styles.r2}>{def.desc}</span>\n"
      "              </button>\n"
      "              {readId === def.id && (\n"
      "                <div className={styles.readout}>\n"
      "                  <div className={styles.readoutText}>{readout(def)}</div>\n"
      "                  <button className={styles.useBtn} onClick={() => applyDef(def)}>USE THIS REPORT</button>\n"
      "                </div>\n"
      "              )}\n"
      "            </div>\n"
      "          ))}\n",
      "          {defaultDef && (\n"
      "            <div className={styles.catWrap}>\n"
      "              <button className={styles.catRow + ' ' + styles.catRowDef + (appliedId === defaultDef.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === defaultDef.id ? null : defaultDef.id)} aria-expanded={readId === defaultDef.id}>\n"
      "                <span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.tag}>{defaultDef.chart !== 'NONE' ? defaultDef.chart : 'TABLE'} &middot; {defaultDef.group}</span><span className={styles.toggleHint}>{readId === defaultDef.id ? 'CLOSE \\u25B2' : 'WHAT IS THIS? \\u25BC'}</span></span>\n"
      "                <span className={styles.r2}>{defaultDef.desc}</span>\n"
      "              </button>\n"
      "              {readId === defaultDef.id && (\n"
      "                <div className={styles.readout}>\n"
      "                  <div className={styles.readoutText}>{readout(defaultDef)}</div>\n"
      "                  <button className={styles.useBtn} onClick={() => applyDef(defaultDef)}>USE THIS REPORT</button>\n"
      "                </div>\n"
      "              )}\n"
      "            </div>\n"
      "          )}\n"
      "          {restList.length === 0 && !defaultDef && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}\n"
      "          {groupTab === 'ALL'\n"
      "            ? GROUPS.filter(g => restList.some(d => d.group === g)).map(g => (\n"
      "              <div key={g}>\n"
      "                <div className={styles.ddSec}>{g} ({restList.filter(d => d.group === g).length})</div>\n"
      "                {restList.filter(d => d.group === g).map(catRowNode)}\n"
      "              </div>\n"
      "            ))\n"
      "            : restList.map(catRowNode)}\n",
      'studio: DEFAULT VIEW row highlighted + rest of list grouped by section on the ALL tab')

# ---------------------------------------------------------------------------
# 8. Footer count line -- was built off `listed`, keep it accurate now that
#    the default row is rendered separately via restList.
# ---------------------------------------------------------------------------
patch(STU,
      "        <div className={styles.foot}>\n"
      "          {listed.length} report{listed.length === 1 ? '' : 's'} in {groupTab === 'ALL' ? 'all groups' : groupTab}",
      "        <div className={styles.foot}>\n"
      "          {listed.length} report{listed.length === 1 ? '' : 's'} in {groupTab === 'ALL' ? 'all groups' : groupTab}{defaultDef ? ' (+1 default)' : ''}",
      'studio: footer count notes the pinned default row, matching the prototype foot line')

# ---------------------------------------------------------------------------
# 9. ReportStudio.module.css -- new classes for everything above: dark PDF
#    button, export-model note, dropdown-style chart chip, default-row
#    highlight, sticky group-section headers, entity search input, the
#    expand/collapse hint text and the entity-match type tag.
# ---------------------------------------------------------------------------
NEW_CSS = """.appliedLine b { color: #EE8C3A; }
.useBtnDark {
  flex-shrink: 0; cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);
  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 14px;
  border-radius: 6px; border: 1.5px solid #EE8C3A; background: #162a2c; color: #EE8C3A; transition: all 0.2s;
}
.useBtnDark:hover:not(:disabled) { background: #213E40; transform: translateY(-1px); }
.useBtnDark:disabled { opacity: 0.45; cursor: not-allowed; }
.approachNote { background: rgba(0,0,0,0.28); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 8px 12px; color: rgba(255,255,255,0.72); font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.8vw, 10px); line-height: 1.6; }
.pvChipDd {
  position: relative; display: inline-flex; align-items: center; gap: 6px;
  font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px); font-weight: 700;
  letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.78);
  border: 1px solid rgba(255,255,255,0.22); border-radius: 4px; padding: 3px 6px 3px 8px;
  background: rgba(255,255,255,0.06);
}
.chartDdBtn {
  display: flex; align-items: center; gap: 4px; cursor: pointer; height: 22px; padding: 0 8px;
  border-radius: 4px; border: none; background: #EE8C3A; color: #1a2e30;
  font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase;
}
.chartDdBtn svg { flex-shrink: 0; transition: transform 0.2s; }
.catRowDef { border-left: 3px solid #EE8C3A; background: #fdf3e7; }
.catRowDef:hover, .catRowDef.catRowOn { background: #EE8C3A; }
.ddSec { position: sticky; top: 0; background: #f6f3ef; color: rgba(26,46,48,0.55); font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; padding: 6px 14px; border-bottom: 1px solid #dfd9d1; z-index: 1; }
.toggleHint { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; opacity: 0.75; white-space: nowrap; }
.tag + .toggleHint { margin-left: 8px; }
.entInput { height: 38px; width: clamp(180px, 22vw, 280px); padding: 0 12px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; transition: all 0.2s; }
.entInput:focus { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.pickOptionTag { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; opacity: 0.7; }
.ddFootMsg { padding: 8px 10px; color: rgba(26,46,48,0.5); font-size: 10px; font-weight: 700; }
@media (max-width: 900px) {
"""
patch(CSS,
      ".appliedLine b { color: #EE8C3A; }\n@media (max-width: 900px) {\n",
      NEW_CSS,
      'css: add useBtnDark, approachNote, chart dropdown, catRowDef, ddSec, entInput, toggleHint, pickOptionTag, ddFootMsg')

ADDENDUM = '''
- fix86 (2026-09-25): Reports page brought into design parity with the approved prototype. Chart-type picker is now a dropdown chip inside the preview chip row (was a separate button row) and offers AREA again, reusing LineChart's existing filled-area rendering. PDF export now uses a dark/orange-outline button distinct from the solid-orange CSV button, plus a one-line note explaining CSV = flat data vs PDF = cover + chart + table pages. DEFAULT VIEW row gets a soft-orange highlight so it reads as different before it's clicked. Catalogue list groups into labelled sections (e.g. "MONEY IN (4)") while on the ALL tab instead of one flat list. Every catalogue row now shows an explicit "WHAT IS THIS? \\u25BC / CLOSE \\u25B2" hint alongside its chart/group tag. "Who / what" entity field is now type-to-search (was a static scroll list), Enter picks the top match. Global Inter font-weight import widened to include 500/700/900 so existing "font-weight: 900" rules across the app render as true black weight instead of synthetic bold.
'''
get(ADD); BUF[ADD] = BUF[ADD] + ADDENDUM
print('OK      addendum appended')

for p in (STU, CSS, IDX, ADD):
    save(p)
print('')
print('All files written.')
print('')

frontend = R('erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=frontend, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print(''); print('BUILD RED -- nothing committed or pushed.'); sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping local build check)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix86: Reports page design parity (chart dropdown+AREA, PDF secondary style, export note, default-row highlight, grouped catalogue, entity type-to-search, font-weight fix)'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. After the green tick + hard refresh: chart selector is a dropdown chip with AREA, PDF button is dark/outlined, an export note sits under it, DEFAULT VIEW is tinted, the ALL tab is grouped, every row shows WHAT IS THIS?, and Who/what is a live search box.')