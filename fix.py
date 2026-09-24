#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix81 (STAGE 3 of 3): RESULTS VIEWER + CSV + PDF
# ----------------------------------------------------------------------------
# Adds to the stage-2 studio (scope bar + catalogue + readout):
#   * USE THIS REPORT now opens a viewer under the catalogue: scope chips,
#     chart-type chips (NONE/BAR/COLUMN/LINE/DONUT, default = the report's
#     own type), the chart itself (shared Charts.jsx components), and a
#     sample table (first 8 rows, pinned first column, sideways scroll).
#   * CSV button downloads EVERY matching row (columns + sort as selected).
#   * PDF button downloads a real composed document (jsPDF): landscape cover
#     with title + scope stamp + the chart image, then all table pages with
#     the header repeated. Never a print dialog.
#   * Recently-used chips persist per device (localStorage).
#   * package.json gains jspdf so Render's npm install picks it up.
# Stage 3 completes the batch -- after the green tick David walks the page.
# ============================================================================
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
STU    = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
STUCSS = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')
PKG    = R('erp-frontend', 'package.json')
ADD    = R('LLM_CONTEXT_ADDENDUM.md')

BUF = {}
def get(p):
    if p not in BUF:
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            BUF[p] = f.read()
    return BUF[p]
def save(p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(BUF[p])
def patch(p, old, new, tag):
    s = get(p)
    if old in s:
        BUF[p] = s.replace(old, new, 1)
        print('OK      ' + tag)
    else:
        print('MISSING ' + tag)
def write(p, content, tag):
    BUF[p] = content
    print('OK      ' + tag)

STUDIO_JS = '''// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
// GOLDEN SEED -- REPORT STUDIO (stage 3): scope bar + catalogue + viewer.
// One chain: dataset -> entity -> period -> columns -> sort -> report ->
// chart + table + CSV + PDF. Every control below recomputes the same rows,
// so the chart, the table, the CSV and the PDF can never disagree.
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiChevronDown, FiAlertCircle, FiRefreshCw } from 'react-icons/fi';
import { jsPDF } from 'jspdf';
import { Chart } from '../../components/common/Charts';
import {
  DATASETS, datasetsFor, fieldsFor, fieldByKey, applyFilters,
  groupRows, formatValue, toCSV, downloadCSV,
} from './reportData';
import { CATALOGUE, ENTITIES, GROUPS } from './reportsCatalog';
import styles from './ReportStudio.module.css';

const PERIODS = ['TODAY','THIS WEEK','LAST WEEK','THIS MONTH','LAST MONTH','THIS QUARTER','THIS YEAR','LAST YEAR','ALL TIME','CUSTOM'];
const CHART_MAP = { BAR: 'bars', COLUMN: 'column', LINE: 'line', DONUT: 'donut' };
const CHART_OPTS = ['NONE','BAR','COLUMN','LINE','DONUT'];
const RECENT_KEY = 'gs.reports.recent.v1';
const SAMPLE = 8;

const fldByLabel = (dataset, label) => (dataset?.fields || []).find(f => f.label === label);

const periodRange = (period, from, to) => {
  const now = new Date();
  let s = null; let e = null;
  if (period === 'TODAY') { s = new Date(now); e = new Date(now); }
  else if (period === 'THIS WEEK') { const day = (now.getDay() + 6) % 7; s = new Date(now); s.setDate(now.getDate() - day); e = new Date(now); }
  else if (period === 'LAST WEEK') { const day = (now.getDay() + 6) % 7; s = new Date(now); s.setDate(now.getDate() - day - 7); e = new Date(s); e.setDate(s.getDate() + 6); }
  else if (period === 'THIS MONTH') { s = new Date(now.getFullYear(), now.getMonth(), 1); e = new Date(now); }
  else if (period === 'LAST MONTH') { s = new Date(now.getFullYear(), now.getMonth() - 1, 1); e = new Date(now.getFullYear(), now.getMonth(), 0); }
  else if (period === 'THIS QUARTER') { s = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1); e = new Date(now); }
  else if (period === 'THIS YEAR') { s = new Date(now.getFullYear(), 0, 1); e = new Date(now); }
  else if (period === 'LAST YEAR') { s = new Date(now.getFullYear() - 1, 0, 1); e = new Date(now.getFullYear() - 1, 11, 31); }
  else if (period === 'CUSTOM') {
    let a = from || ''; let b = to || '';
    if (a && b && a > b) { const t = a; a = b; b = t; }
    if (!a && !b) return null;
    s = a ? new Date(a) : null; e = b ? new Date(b) : null;
  } else return null;
  if (!s || !e) return null;
  return [s.toISOString().slice(0, 10), e.toISOString().slice(0, 10)];
};

const ReportStudio = ({ canSeeMoney = false, reloadToken = 0 }) => {
  const available = useMemo(() => datasetsFor(canSeeMoney), [canSeeMoney]);
  const [datasetKey, setDatasetKey] = useState(available[0]?.key || 'PROJECTS');
  const dataset = DATASETS[datasetKey] || available[0];
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [entity, setEntity] = useState(null);
  const [period, setPeriod] = useState('THIS MONTH');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [columns, setColumns] = useState([]);
  const [sort, setSort] = useState({ col: '', dir: 'asc' });
  const [search, setSearch] = useState('');
  const [groupTab, setGroupTab] = useState('ALL');
  const [readId, setReadId] = useState(null);
  const [appliedId, setAppliedId] = useState(null);
  const [chartMode, setChartMode] = useState('NONE');
  const [recent, setRecent] = useState(() => {
    try { return JSON.parse(window.localStorage.getItem(RECENT_KEY) || '[]'); } catch (e) { return []; }
  });
  const [colOpen, setColOpen] = useState(false);
  const [sortOpen, setSortOpen] = useState(false);
  const [entOpen, setEntOpen] = useState(false);
  const colRef = useRef(null); const sortRef = useRef(null); const entRef = useRef(null);
  const chartRef = useRef(null);
  useEffect(() => {
    const h = (e) => {
      if (colRef.current && !colRef.current.contains(e.target)) setColOpen(false);
      if (sortRef.current && !sortRef.current.contains(e.target)) setSortOpen(false);
      if (entRef.current && !entRef.current.contains(e.target)) setEntOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);
  const fields = useMemo(() => fieldsFor(dataset, canSeeMoney), [dataset, canSeeMoney]);
  const load = useCallback(async (key) => {
    const ds = DATASETS[key]; if (!ds) return;
    setLoading(true); setError('');
    try { const data = await ds.load(); setRows(Array.isArray(data) ? data : []); }
    catch (e) { setRows([]); setError('Could not load ' + ds.label.toLowerCase() + '. You may not have access, or the connection dropped.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(datasetKey); }, [datasetKey, load]);
  const firstRun = useRef(true);
  useEffect(() => {
    if (firstRun.current) { firstRun.current = false; return; }
    load(datasetKey);
  }, [reloadToken, datasetKey, load]);
  useEffect(() => {
    const ds = DATASETS[datasetKey]; if (!ds) return;
    const allowed = fieldsFor(ds, canSeeMoney).map(f => f.key);
    setColumns(ds.defaultColumns.filter(c => allowed.includes(c)));
    setEntity(null); setAppliedId(null); setReadId(null);
    setGroupTab('ALL'); setSearch(''); setSort({ col: '', dir: 'asc' }); setChartMode('NONE');
  }, [datasetKey, canSeeMoney]);

  const entityTypes = ENTITIES[datasetKey] || [];
  const entityValues = (type) => {
    const t = entityTypes.find(x => x.type === type); if (!t) return [];
    const fld = fldByLabel(dataset, t.field); if (!fld) return [];
    const seen = [];
    rows.forEach(r => { const v = fld.get(r); if (v && seen.indexOf(v) < 0) seen.push(v); });
    return seen.sort().slice(0, 40);
  };

  const catalogue = useMemo(() => CATALOGUE.filter(d =>
    d.ds === datasetKey && (!d.money || canSeeMoney) &&
    ((entity ? (d.scopes || []).indexOf(entity.type) >= 0 : (d.scopes || []).indexOf('ALL') >= 0))
  ), [datasetKey, canSeeMoney, entity]);
  const searched = useMemo(() => {
    const q = search.trim().toUpperCase();
    if (!q) return catalogue;
    return catalogue.filter(d => (d.title + ' ' + d.desc).toUpperCase().indexOf(q) >= 0);
  }, [catalogue, search]);
  useEffect(() => {
    if (groupTab !== 'ALL' && !searched.some(d => d.group === groupTab)) setGroupTab('ALL');
  }, [searched, groupTab]);
  const listed = groupTab === 'ALL' ? searched : searched.filter(d => d.group === groupTab);
  const appliedDef = CATALOGUE.find(d => d.id === appliedId) || null;
  const recentDefs = recent.map(id => CATALOGUE.find(d => d.id === id)).filter(Boolean);

  const toggleColumn = (key) => setColumns(c => (c.indexOf(key) >= 0 ? c.filter(k => k !== key) : [...c, key]));
  const applyDef = (def) => {
    setAppliedId(def.id); setReadId(null);
    const keys = (def.cols || []).map(l => (fldByLabel(dataset, l) || {}).key).filter(Boolean);
    const allowed = fields.map(f => f.key);
    if (keys.length) setColumns(keys.filter(k => allowed.includes(k)));
    if (def.sort) setSort({ col: def.sort.col, dir: def.sort.dir });
    setChartMode(def.chart || 'NONE');
    const next = [def.id, ...recent.filter(x => x !== def.id)].slice(0, 6);
    setRecent(next);
    try { window.localStorage.setItem(RECENT_KEY, JSON.stringify(next)); } catch (e) {}
  };

  const periodHuman = () => {
    const m = { TODAY: 'today', 'THIS WEEK': 'this week', 'LAST WEEK': 'last week', 'THIS MONTH': 'this month', 'LAST MONTH': 'last month', 'THIS QUARTER': 'this quarter', 'THIS YEAR': 'this year', 'LAST YEAR': 'last year', 'ALL TIME': 'since records began' };
    if (period !== 'CUSTOM') return m[period] || period;
    let a = from || '..'; let b = to || '..';
    if (from && to && from > to) { a = to; b = from; }
    return 'between ' + a + ' and ' + b;
  };
  const readout = (def) => {
    let s = def.desc;
    s += entity ? (' For ' + entity.label.toLowerCase() + ' ' + entity.value + '.') : (' Whole company.');
    s += def.period ? (' Period: ' + periodHuman() + '.') : (' Right-now snapshot.');
    const sc = def.sort || { col: 'first column', dir: 'asc' };
    s += ' Sorted by ' + sc.col + ' ' + (sc.dir === 'desc' ? 'highest first.' : 'A to Z.');
    return s;
  };

  /* ── the viewer pipeline: one row set feeds chart, table, CSV, PDF ── */
  const scopeRows = useMemo(() => {
    const def = appliedDef; if (!def) return [];
    let list = rows.slice();
    if (entity && (def.scopes || []).indexOf(entity.type) >= 0) {
      const et = entityTypes.find(t => t.type === entity.type);
      const fld = et ? fldByLabel(dataset, et.field) : null;
      if (fld) list = list.filter(r => String(fld.get(r) || '').toLowerCase() === String(entity.value).toLowerCase());
    }
    if (def.filter) {
      const fld = fldByLabel(dataset, def.filter.field);
      if (fld) list = applyFilters(list, dataset, [{ field: fld.key, op: def.filter.op, value: def.filter.value }], 'AND', '');
    }
    if (def.period && period !== 'ALL TIME') {
      const rng = periodRange(period, from, to);
      const fld = dataset.dateField ? fldByLabel(dataset, dataset.dateField) : null;
      if (rng && fld) list = list.filter(r => {
        const v = fld.get(r); if (!v) return false;
        const d = String(v).slice(0, 10);
        return d >= rng[0] && d <= rng[1];
      });
    }
    return list;
  }, [rows, dataset, entity, entityTypes, period, from, to, appliedDef]);

  const tableCols = useMemo(() => columns.map(k => fieldByKey(dataset, k)).filter(Boolean), [columns, dataset]);
  const sortedAll = useMemo(() => {
    const list = scopeRows.slice();
    const fld = sort.col ? fldByLabel(dataset, sort.col) : null;
    if (!fld) return list;
    list.sort((a, b) => {
      const av = fld.get(a); const bv = fld.get(b);
      let cmp;
      if (fld.type === 'number' || fld.type === 'money' || fld.type === 'percent') cmp = (Number(av) || 0) - (Number(bv) || 0);
      else if (fld.type === 'date') cmp = new Date(av || 0).getTime() - new Date(bv || 0).getTime();
      else cmp = String(av ?? '').localeCompare(String(bv ?? ''));
      return sort.dir === 'desc' ? -cmp : cmp;
    });
    return list;
  }, [scopeRows, dataset, sort]);

  const chartRows = useMemo(() => {
    const def = appliedDef;
    if (!def || !def.groupBy || chartMode === 'NONE') return [];
    const gf = fldByLabel(dataset, def.groupBy); if (!gf) return [];
    const mf = def.measure && def.measure.field ? fldByLabel(dataset, def.measure.field) : null;
    const meas = def.measure ? { agg: def.measure.agg, field: mf ? mf.key : undefined } : { agg: 'count' };
    const g = groupRows(scopeRows, dataset, [gf.key], [meas]);
    const isTime = /Month|Date|Year|Timestamp/.test(def.groupBy);
    g.sort((a, b) => isTime
      ? String(a.path[0]).localeCompare(String(b.path[0]))
      : (Number(b.values[0]) || 0) - (Number(a.values[0]) || 0));
    return g.slice(0, 24).map(b => ({ id: String(b.path[0]), label: String(b.path[0]), value: Number(b.values[0]) || 0 }));
  }, [scopeRows, dataset, appliedDef, chartMode]);
  const measureField = appliedDef && appliedDef.measure && appliedDef.measure.field ? fldByLabel(dataset, appliedDef.measure.field) : null;
  const fmtChart = useCallback((v) => formatValue(v, measureField ? measureField.type : 'number'), [measureField]);

  const stamp = () => new Date().toISOString().slice(0, 10);
  const exportCSV = () => {
    const def = appliedDef; if (!def || !tableCols.length) return;
    downloadCSV(
      'GOLDEN_SEED_' + def.id + '_' + stamp() + '.csv',
      toCSV(tableCols.map(c => c.label), sortedAll.map(r => tableCols.map(c => c.get(r)))),
    );
  };
  const pdfTablePages = (doc, cols, list) => {
    const pw = doc.internal.pageSize.getWidth();
    const ph = doc.internal.pageSize.getHeight();
    const m = 30;
    const cw = (pw - m * 2) / Math.max(cols.length, 1);
    let y = m;
    const head = () => {
      doc.setFillColor(26, 46, 48); doc.rect(m, y - 12, pw - m * 2, 16, 'F');
      doc.setTextColor(238, 140, 58); doc.setFontSize(7);
      cols.forEach((c, i) => doc.text(String(c.label).toUpperCase().slice(0, 24), m + i * cw + 3, y));
      y += 10;
    };
    head();
    doc.setTextColor(26, 46, 48); doc.setFontSize(7);
    list.forEach(r => {
      if (y > ph - 40) { doc.addPage(); y = m; head(); doc.setTextColor(26, 46, 48); doc.setFontSize(7); }
      cols.forEach((c, i) => doc.text(String(formatValue(c.get(r), c.type)).slice(0, 26), m + i * cw + 3, y));
      doc.setDrawColor(223, 217, 209); doc.line(m, y + 2, pw - m, y + 2);
      y += 12;
    });
  };
  const exportPDF = () => {
    const def = appliedDef; if (!def || !tableCols.length) return;
    const doc = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
    const pw = doc.internal.pageSize.getWidth();
    doc.setFillColor(22, 42, 44); doc.rect(0, 0, pw, 70, 'F');
    doc.setTextColor(238, 140, 58); doc.setFontSize(16);
    doc.text('GOLDEN SEED -- ' + def.title, 30, 32);
    doc.setTextColor(255, 255, 255); doc.setFontSize(8);
    doc.text((entity ? entity.type + ' ' + entity.value : 'WHOLE SOURCE') + '  |  ' +
      (def.period ? periodHuman().toUpperCase() : 'AS AT TODAY') + '  |  SORT ' +
      (sort.col || 'DEFAULT') + ' ' + sort.dir.toUpperCase() + '  |  ' + sortedAll.length + ' ROWS', 30, 50);
    doc.setTextColor(150, 160, 160); doc.setFontSize(7);
    doc.text(def.desc + '  Generated ' + new Date().toLocaleString() + '.', 30, 62);
    const finish = (png) => {
      let y = 96;
      if (png) { try { doc.addImage(png, 'PNG', 30, y, 500, 190); } catch (e) {} y += 200; }
      pdfTablePages(doc, tableCols, sortedAll);
      doc.save('GOLDEN_SEED_' + def.id + '_' + stamp() + '.pdf');
    };
    try {
      const svg = chartMode !== 'NONE' && chartRef.current ? chartRef.current.querySelector('svg') : null;
      if (svg) {
        const xml = new XMLSerializer().serializeToString(svg);
        const img = new Image();
        img.onload = () => {
          const c = document.createElement('canvas');
          c.width = 1360; c.height = Math.max(300, Math.round(1360 * (img.height / (img.width || 1360))));
          const ctx = c.getContext('2d');
          ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, c.width, c.height);
          ctx.drawImage(img, 0, 0, c.width, c.height);
          finish(c.toDataURL('image/png'));
        };
        img.onerror = () => finish(null);
        img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(xml)));
        return;
      }
    } catch (e) { /* chart image is best-effort */ }
    finish(null);
  };

  return (
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
          <p className={styles.hint}>{dataset?.blurb}</p>
          {!canSeeMoney && (
            <p className={styles.hint}>
              <FiAlertCircle size={12} aria-hidden="true" /> Financial datasets, money columns and company reports are hidden on your role.
            </p>
          )}
          {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden="true" /> {error}</div>}
          <div className={styles.scopeRow}>
            <div className={styles.scopeField} ref={entRef}>
              <span className={styles.miniLabel}>Who / what</span>
              <div className={styles.entWrap}>
                {entity && (
                  <span className={styles.chipE}>
                    {entity.label}: {entity.value}
                    <button onClick={() => setEntity(null)} aria-label="Clear entity"><FiX size={11} aria-hidden="true" /></button>
                  </span>
                )}
                <button className={styles.pickBtn} onClick={() => setEntOpen(o => !o)} aria-expanded={entOpen}>
                  <span>{entity ? 'Change...' : 'Whole company'}</span>
                  <FiChevronDown className={entOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
                </button>
                {entOpen && (
                  <div className={styles.pickList}>
                    <div className={styles.ddScroll}>
                      <button className={styles.pickOption} onClick={() => { setEntity(null); setEntOpen(false); }}>WHOLE COMPANY</button>
                      {entityTypes.map(t => entityValues(t.type).slice(0, 12).map(v => (
                        <button key={t.type + v} className={styles.pickOption} onClick={() => { setEntity({ type: t.type, label: t.label, value: v }); setEntOpen(false); }}>
                          {t.label}: {v}
                        </button>
                      )))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className={styles.scopeField}>
              <span className={styles.miniLabel}>When</span>
              <div className={(appliedDef && !appliedDef.period ? styles.perChipsDim : '') + ' ' + styles.perChips}>
                {PERIODS.map(p => (
                  <button key={p} className={period === p ? styles.pchipOn : styles.pchip} onClick={() => setPeriod(p)}>{p}</button>
                ))}
              </div>
              {period === 'CUSTOM' && (
                <div className={styles.customRange}>
                  <input type="date" value={from} onChange={e => setFrom(e.target.value)} aria-label="From date" />
                  <span>to</span>
                  <input type="date" value={to} onChange={e => setTo(e.target.value)} aria-label="To date" />
                </div>
              )}
              {appliedDef && !appliedDef.period && <span className={styles.snapHint}>snapshot -- as at today, period ignored</span>}
            </div>
            <div className={styles.scopeField} ref={colRef}>
              <span className={styles.miniLabel}>Columns</span>
              <button className={styles.pickBtn} onClick={() => setColOpen(o => !o)} aria-expanded={colOpen}>
                <span>{columns.length} OF {fields.length} COLUMNS</span>
                <FiChevronDown className={colOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
              </button>
              {colOpen && (
                <div className={styles.pickList}>
                  <div className={styles.ddScroll}>
                    {fields.map(f => (
                      <label key={f.key} className={styles.pickCheck + (columns.indexOf(f.key) >= 0 ? ' ' + styles.pickCheckOn : '')}>
                        <input type="checkbox" checked={columns.indexOf(f.key) >= 0} onChange={() => toggleColumn(f.key)} />{f.label}
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className={styles.scopeField} ref={sortRef}>
              <span className={styles.miniLabel}>Sort</span>
              <div className={styles.sortRow}>
                <button className={styles.pickBtn} onClick={() => setSortOpen(o => !o)} aria-expanded={sortOpen}>
                  <span>{sort.col || 'DEFAULT'}</span>
                  <FiChevronDown className={sortOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
                </button>
                <button className={styles.dirBtn} onClick={() => setSort(s => ({ col: s.col, dir: s.dir === 'desc' ? 'asc' : 'desc' }))} aria-label="Flip sort direction">
                  {sort.dir === 'desc' ? '\\u2193' : '\\u2191'}
                </button>
                {sortOpen && (
                  <div className={styles.pickList}>
                    <div className={styles.ddScroll}>
                      <button className={styles.pickOption + (!sort.col ? ' ' + styles.pickOptionActive : '')} onClick={() => { setSort({ col: '', dir: 'asc' }); setSortOpen(false); }}>DEFAULT (report's own)</button>
                      {fields.map(f => (
                        <button key={f.key} className={styles.pickOption + (sort.col === f.label ? ' ' + styles.pickOptionActive : '')} onClick={() => { setSort(s => ({ col: f.label, dir: s.dir })); setSortOpen(false); }}>
                          {f.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.catPanel}>
        <div className={styles.panelHeadRow}>
          <span className={styles.scopeTitle}>REPORT CATALOGUE</span>
          <span className={styles.badge}>{searched.length} REPORTS</span>
          <div className={styles.searchBox}>
            <FiSearch className={styles.searchIcon} aria-hidden="true" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search reports..." aria-label="Search reports" />
            {search && <button className={styles.searchClear} onClick={() => setSearch('')} aria-label="Clear search"><FiX size={13} aria-hidden="true" /></button>}
          </div>
        </div>
        <div className={styles.tabRow}>
          <button className={groupTab === 'ALL' ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab('ALL')}>
            ALL<span className={styles.gcnt}>{searched.length}</span>
          </button>
          {GROUPS.map(g => {
            const n = searched.filter(d => d.group === g).length;
            if (!n && g !== groupTab) return null;
            return (
              <button key={g} className={groupTab === g ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab(g)}>
                {g}<span className={styles.gcnt}>{n}</span>
              </button>
            );
          })}
        </div>
        {recentDefs.length > 0 && (
          <div className={styles.recentRow}>
            <span className={styles.recentLabel}>RECENTLY USED</span>
            {recentDefs.map(d => (
              <button key={d.id} className={styles.rchip} onClick={() => applyDef(d)}>{d.title}</button>
            ))}
          </div>
        )}
        <div className={styles.catList}>
          {listed.length === 0 && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}
          {listed.map(def => (
            <div key={def.id} className={styles.catWrap}>
              <button className={styles.catRow + (appliedId === def.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === def.id ? null : def.id)} aria-expanded={readId === def.id}>
                <span className={styles.r1}>{def.title}<span className={styles.tag}>{def.chart !== 'NONE' ? def.chart : 'TABLE'} &middot; {def.group}</span></span>
                <span className={styles.r2}>{def.desc}</span>
              </button>
              {readId === def.id && (
                <div className={styles.readout}>
                  <div className={styles.readoutText}>{readout(def)}</div>
                  <button className={styles.useBtn} onClick={() => applyDef(def)}>USE THIS REPORT</button>
                </div>
              )}
            </div>
          ))}
        </div>
        <div className={styles.foot}>
          {listed.length} report{listed.length === 1 ? '' : 's'} in {groupTab === 'ALL' ? 'all groups' : groupTab}
          {search ? ' matching "' + search + '"' : ''}
          {entity ? ' for ' + entity.label.toLowerCase() + ' ' + entity.value : ' for the whole company'}
        </div>
      </div>

      {appliedDef && (
        <div className={styles.viewerPanel}>
          <div className={styles.panelHeadRow}>
            <span className={styles.scopeTitle}>PREVIEW -- {appliedDef.title}</span>
            <div className={styles.pvChips}>
              <span className={styles.pvChip}>{entity ? entity.label.toUpperCase() + ' ' + entity.value : 'WHOLE SOURCE'}</span>
              <span className={styles.pvChip}>{appliedDef.period ? periodHuman().toUpperCase() : 'AS AT TODAY'}</span>
              <span className={styles.pvChip}>SORT {sort.col || 'DEFAULT'} {sort.dir.toUpperCase()}</span>
              <span className={styles.pvChip}>{tableCols.length} COLUMNS</span>
              <span className={styles.pvChip}>{sortedAll.length} ROWS MATCH</span>
            </div>
            <div className={styles.pvBtns}>
              <button className={styles.useBtn} onClick={exportCSV} disabled={!sortedAll.length || !tableCols.length}>CSV -- THE DATA</button>
              <button className={styles.useBtn} onClick={exportPDF} disabled={!sortedAll.length || !tableCols.length}>PDF -- THE DOCUMENT</button>
            </div>
          </div>
          <div className={styles.chartChips}>
            {CHART_OPTS.map(t => (
              <button key={t} className={chartMode === t ? styles.cchipOn : styles.cchip} onClick={() => setChartMode(t)}>{t}</button>
            ))}
          </div>
          {chartMode !== 'NONE' && chartRows.length > 0 && (
            <div className={styles.chartBox} ref={chartRef}>
              <Chart type={CHART_MAP[chartMode] || 'bars'} rows={chartRows} format={fmtChart} />
            </div>
          )}
          {chartMode !== 'NONE' && chartRows.length === 0 && (
            <div className={styles.pvNote}>NOTHING TO CHART FOR THIS SCOPE</div>
          )}
          <div className={styles.pvScroll}>
            <table className={styles.pvTable}>
              <thead>
                <tr>{tableCols.map(c => <th key={c.key}>{c.label}</th>)}</tr>
              </thead>
              <tbody>
                {sortedAll.length === 0 && (
                  <tr><td colSpan={Math.max(tableCols.length, 1)} className={styles.emptyCell}>NOTHING MATCHES THIS SCOPE</td></tr>
                )}
                {sortedAll.slice(0, SAMPLE).map((r, i) => (
                  <tr key={i}>
                    {tableCols.map(c => <td key={c.key}>{formatValue(c.get(r), c.type)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className={styles.pvNote}>
            SAMPLE: FIRST {Math.min(SAMPLE, sortedAll.length)} OF {sortedAll.length} ROWS -- CSV AND PDF CARRY ALL OF THEM.
            WIDE TABLE? SCROLL SIDEWAYS, THE FIRST COLUMN STAYS PINNED.
          </div>
        </div>
      )}

      <div className={styles.appliedLine}>
        {appliedDef
          ? <>APPLIED: <b>{appliedDef.title}</b> &middot; {tableCols.length} columns &middot; sorted {sort.col || 'default'} {sort.dir} &middot; {entity ? entity.label + ' ' + entity.value : 'whole company'} &middot; {appliedDef.period ? periodHuman() : 'right now'}</>
          : <>No report applied yet -- open a report above and press USE THIS REPORT.</>}
      </div>
    </div>
  );
};
export default ReportStudio;
'''

CSS_ADD = '''
/* fix81 -- STAGE 3: results viewer (chart + table + downloads). Appended:
cascade wins over everything above. */
.viewerPanel {
  --accent: #EE8C3A;
  --surface: #ffffff;
  --surface-3: #efe9e2;
  --surface-edge: #dfd9d1;
  --ink: #1a2e30;
  --ink-soft: #5b6f70;
  --ink-faint: rgba(26, 46, 48, 0.45);
  background: linear-gradient(135deg, #4a6a6c 0%, #3a5a5c 50%, #2f4c4e 100%);
  border: 1.5px solid rgba(238, 140, 58, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
  margin-bottom: clamp(10px, 1.4vw, 14px);
  overflow: visible;
  padding: clamp(10px, 1.4vw, 14px) clamp(12px, 1.6vw, 18px);
  display: flex; flex-direction: column; gap: clamp(8px, 1.2vw, 12px);
}
.viewerPanel .panelHeadRow { background: transparent; border-bottom: 1.5px solid var(--orange); border-radius: 0; padding: 0 0 10px 0; }
.pvChips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.pvChip {
  font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px); font-weight: 700;
  letter-spacing: 1px; text-transform: uppercase; color: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 4px; padding: 3px 8px;
  background: rgba(255, 255, 255, 0.05); white-space: nowrap;
}
.pvBtns { margin-left: auto; display: flex; gap: 8px; flex-wrap: wrap; }
.chartChips { display: flex; gap: 6px; flex-wrap: wrap; }
.cchip, .cchipOn {
  font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px); font-weight: 900;
  letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer;
  padding: 7px 12px; border-radius: 6px; transition: all 0.2s ease;
  border: 1.5px solid rgba(255, 255, 255, 0.18); background: rgba(255, 255, 255, 0.06); color: rgba(255, 255, 255, 0.8);
}
.cchip:hover { border-color: var(--orange); color: var(--orange); }
.cchipOn { background: var(--orange); border-color: var(--orange); color: #1a2e30; }
.chartBox {
  background: #ffffff; border: 1.5px solid var(--surface-edge); border-radius: 8px;
  padding: clamp(10px, 1.4vw, 14px);
}
.pvScroll {
  overflow-x: auto; background: #ffffff; border: 1.5px solid var(--surface-edge);
  border-radius: 8px; scrollbar-width: thin; scrollbar-color: var(--orange) transparent;
}
.pvScroll::-webkit-scrollbar { height: 8px; }
.pvScroll::-webkit-scrollbar-thumb { background: rgba(238, 140, 58, 0.45); border-radius: 4px; }
.pvTable { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 640px; }
.pvTable th {
  position: sticky; top: 0; z-index: 2; background: #162a2c; color: var(--orange);
  font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px); font-weight: 900;
  letter-spacing: 2px; text-transform: uppercase; text-align: left;
  padding: 9px 12px; white-space: nowrap;
}
.pvTable td {
  padding: 8px 12px; border-bottom: 1px solid #f1eeea; color: #1a2e30;
  font-size: clamp(10px, 1.05vw, 12px); font-weight: 600; white-space: nowrap;
}
.pvTable tbody tr:nth-child(even) td { background: #fbf9f7; }
.pvTable tbody tr:hover td { background: rgba(238, 140, 58, 0.22); }
.pvTable th:first-child, .pvTable td:first-child { position: sticky; left: 0; z-index: 3; }
.pvTable th:first-child { background: #162a2c; }
.pvTable td:first-child {
  background: #ffffff; font-family: 'Space Mono', monospace; font-weight: 700;
  border-right: 1px solid var(--surface-edge);
}
.pvTable tbody tr:nth-child(even) td:first-child { background: #fbf9f7; }
.pvTable tbody tr:hover td:first-child { background: rgba(238, 140, 58, 0.22); }
.pvNote {
  padding: 8px 4px 0; color: rgba(255, 255, 255, 0.6);
  font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px);
  font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; line-height: 1.7;
}
.perChipsDim { opacity: 0.45; pointer-events: none; }
'''

ADDENDUM = '''
- fix81 (2026-09-24, STAGE 3 of 3): results viewer lands on the Report Studio. USE THIS REPORT now opens a preview panel under the catalogue: scope chips (entity / period or as-at-today / sort / columns / rows matched), chart-type chips NONE-BAR-COLUMN-LINE-DONUT defaulting to each report's own type, the shared Charts.jsx chart fed by groupRows over the same scoped rows, and a sample table (first 8 rows, pinned first column, sideways scroll for wide tables). CSV downloads every matching row through reportData's toCSV/downloadCSV; PDF is a real jsPDF document (landscape cover with title + scope stamp + chart image rendered from the live SVG, then all table pages with the header repeated) -- never a print dialog. Recently-used chips persist per device in localStorage (gs.reports.recent.v1). package.json gains jspdf ^2.5.1 so Render's npm install provides it. Stage 3 completes the fix79 batch, so the whole Reports page is now testable end to end.
'''

print('=' * 72)
print(' GOLDEN SEED fix81 -- STAGE 3 of 3: viewer + CSV + PDF')
print('=' * 72)

write(STU, STUDIO_JS, 'write ReportStudio.jsx (stage 3: viewer + exports)')
get(STUCSS)
BUF[STUCSS] = BUF[STUCSS] + CSS_ADD
print('OK      append ReportStudio.module.css (viewer styles + chart vars)')
patch(PKG,
      '    "react-router-dom": "^7.13.0"',
      '    "react-router-dom": "^7.13.0",\n    "jspdf": "^2.5.1"',
      'package.json: jspdf dependency added')
get(ADD)
BUF[ADD] = BUF[ADD] + ADDENDUM
print('OK      append addendum')

for p in (STU, STUCSS, PKG, ADD):
    save(p)
print('')
print('All files written.')
print('')

frontend = R('erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=frontend, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print('')
        print('BUILD RED -- nothing committed or pushed.')
        sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping local build check; Render npm install will fetch jspdf)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix81 stage3: results viewer with chart, sample table, real CSV and composed PDF downloads, jspdf dependency'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Stage 3 done -- the fix79 batch is complete. After the green tick, walk Reports end to end:')
print('scope -> catalogue -> WHAT IS THIS? -> USE THIS REPORT -> chart chips -> CSV -> PDF.')