#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix84 -- REPORTS PAGE AS ONE MATCHED SET.
# Rewrites ReportHub.jsx, ReportStudio.jsx and ReportStudio.module.css
# together so props, class names and styles can never disagree again:
#   * hub passes canSeeMoney + reloadToken and uses existing header classes
#   * studio = scope bar + catalogue + readout + viewer (chart/table/CSV/PDF)
#   * stylesheet defines EVERY class the studio JSX references
# reportsCatalog.js and reportData.js are untouched (they are correct).
# ============================================================================
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
HUB    = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.jsx')
STU    = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
STUCSS = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')
ADD    = R('LLM_CONTEXT_ADDENDUM.md')

HUB_JS = '''// PATH: erp-frontend/src/pages/Reports/ReportHub.jsx
// GOLDEN SEED -- REPORTS PAGE SHELL (fix84).
// Passes the two props the studio needs (money gate + refresh signal) and
// uses the header classes ReportHub.module.css actually defines.
import React, { useState } from 'react';
import { FiRefreshCw } from 'react-icons/fi';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import { useAuth } from '../../hooks/useAuth';
import ReportStudio from './ReportStudio';
import styles from './ReportHub.module.css';

const ReportHub = () => {
  const { user } = useAuth();
  const canSeeMoney = !!(user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR');
  const [reloadToken, setReloadToken] = useState(0);
  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Report Studio</h1>
          <p className={styles.subtitle}>Scope it, pick it, preview it, take it home</p>
        </div>
        <HeaderActions>
          <HeaderButton icon={FiRefreshCw} label="REFRESH" tip="Pull the current dataset again from the server"
            onClick={() => setReloadToken(t => t + 1)} />
        </HeaderActions>
      </header>
      <ReportStudio canSeeMoney={canSeeMoney} reloadToken={reloadToken} />
    </div>
  );
};
export default ReportHub;
'''

STUDIO_JS = '''// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
// GOLDEN SEED -- REPORT STUDIO (fix84): scope bar + catalogue + viewer.
// One chain: dataset -> entity -> period -> columns -> sort -> report ->
// chart + table + CSV + PDF. Every control recomputes the same row set, so
// chart, table and downloads can never disagree.
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

const periodRange = (period, fromArg, toArg) => {
  const now = new Date();
  let start = null;
  let end = null;
  if (period === 'TODAY') { start = new Date(now); end = new Date(now); }
  else if (period === 'THIS WEEK') { const day = (now.getDay() + 6) % 7; start = new Date(now); start.setDate(now.getDate() - day); end = new Date(now); }
  else if (period === 'LAST WEEK') { const day = (now.getDay() + 6) % 7; start = new Date(now); start.setDate(now.getDate() - day - 7); end = new Date(start); end.setDate(start.getDate() + 6); }
  else if (period === 'THIS MONTH') { start = new Date(now.getFullYear(), now.getMonth(), 1); end = new Date(now); }
  else if (period === 'LAST MONTH') { start = new Date(now.getFullYear(), now.getMonth() - 1, 1); end = new Date(now.getFullYear(), now.getMonth(), 0); }
  else if (period === 'THIS QUARTER') { start = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1); end = new Date(now); }
  else if (period === 'THIS YEAR') { start = new Date(now.getFullYear(), 0, 1); end = new Date(now); }
  else if (period === 'LAST YEAR') { start = new Date(now.getFullYear() - 1, 0, 1); end = new Date(now.getFullYear() - 1, 11, 31); }
  else if (period === 'CUSTOM') {
    let a = fromArg || '';
    let b = toArg || '';
    if (a && b && a > b) { const tmp = a; a = b; b = tmp; }
    if (!a && !b) return null;
    start = a ? new Date(a) : null;
    end = b ? new Date(b) : null;
  } else {
    return null;
  }
  if (!start || !end) return null;
  return [start.toISOString().slice(0, 10), end.toISOString().slice(0, 10)];
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
  const colRef = useRef(null);
  const sortRef = useRef(null);
  const entRef = useRef(null);
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
  const fieldByLabelMap = useMemo(() => {
    const map = {};
    fields.forEach(fld => { map[fld.label] = fld; });
    return map;
  }, [fields]);
  const load = useCallback(async (key) => {
    const ds = DATASETS[key];
    if (!ds) return;
    setLoading(true);
    setError('');
    try {
      const data = await ds.load();
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      setRows([]);
      setError('Could not load ' + ds.label.toLowerCase() + '. You may not have access, or the connection dropped.');
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(datasetKey); }, [datasetKey, load]);
  const firstRun = useRef(true);
  useEffect(() => {
    if (firstRun.current) { firstRun.current = false; return; }
    load(datasetKey);
  }, [reloadToken, datasetKey, load]);
  useEffect(() => {
    const ds = DATASETS[datasetKey];
    if (!ds) return;
    const allowed = fieldsFor(ds, canSeeMoney).map(f => f.key);
    setColumns(ds.defaultColumns.filter(c => allowed.includes(c)));
    setEntity(null); setAppliedId(null); setReadId(null);
    setGroupTab('ALL'); setSearch(''); setSort({ col: '', dir: 'asc' }); setChartMode('NONE');
  }, [datasetKey, canSeeMoney]);

  const entityTypes = ENTITIES[datasetKey] || [];
  const entityValues = (type) => {
    const t = entityTypes.find(x => x.type === type);
    if (!t) return [];
    const fld = fieldByLabelMap[t.field];
    if (!fld) return [];
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
    setAppliedId(def.id);
    setReadId(null);
    const keys = (def.cols || []).map(l => (fieldByLabelMap[l] || {}).key).filter(Boolean);
    const allowed = fields.map(f => f.key);
    if (keys.length) setColumns(keys.filter(k => allowed.includes(k)));
    if (def.sort) setSort({ col: def.sort.col, dir: def.sort.dir });
    setChartMode(def.chart || 'NONE');
    const next = [def.id].concat(recent.filter(x => x !== def.id)).slice(0, 6);
    setRecent(next);
    try { window.localStorage.setItem(RECENT_KEY, JSON.stringify(next)); } catch (e) { /* private mode */ }
  };
  const periodHuman = () => {
    const labels = { TODAY: 'today', 'THIS WEEK': 'this week', 'LAST WEEK': 'last week', 'THIS MONTH': 'this month', 'LAST MONTH': 'last month', 'THIS QUARTER': 'this quarter', 'THIS YEAR': 'this year', 'LAST YEAR': 'last year', 'ALL TIME': 'since records began' };
    if (period !== 'CUSTOM') return labels[period] || period;
    let a = from || '..';
    let b = to || '..';
    if (from && to && from > to) { a = to; b = from; }
    return 'between ' + a + ' and ' + b;
  };
  const readout = (def) => {
    let text = def.desc;
    text += entity ? (' For ' + entity.label.toLowerCase() + ' ' + entity.value + '.') : (' Whole company.');
    text += def.period ? (' Period: ' + periodHuman() + '.') : (' Right-now snapshot.');
    const sc = def.sort || { col: 'first column', dir: 'asc' };
    text += ' Sorted by ' + sc.col + ' ' + (sc.dir === 'desc' ? 'highest first.' : 'A to Z.');
    return text;
  };

  /* ── viewer pipeline: one row set feeds chart, table, CSV, PDF ── */
  const scopeRows = useMemo(() => {
    const def = appliedDef;
    if (!def) return [];
    let list = rows.slice();
    if (entity && (def.scopes || []).indexOf(entity.type) >= 0) {
      const et = entityTypes.find(t => t.type === entity.type);
      const fld = et ? fieldByLabelMap[et.field] : null;
      if (fld) list = list.filter(r => String(fld.get(r) || '').toLowerCase() === String(entity.value).toLowerCase());
    }
    if (def.filter) {
      const fld = fieldByLabelMap[def.filter.field];
      if (fld) list = applyFilters(list, dataset, [{ field: fld.key, op: def.filter.op, value: def.filter.value }], 'AND', '');
    }
    if (def.period && period !== 'ALL TIME') {
      const rng = periodRange(period, from, to);
      const fld = dataset.dateField ? fieldByLabelMap[dataset.dateField] : null;
      if (rng && fld) list = list.filter(r => {
        const v = fld.get(r);
        if (!v) return false;
        const d = String(v).slice(0, 10);
        return d >= rng[0] && d <= rng[1];
      });
    }
    return list;
  }, [rows, dataset, entity, entityTypes, fieldByLabelMap, period, from, to, appliedDef]);
  const tableCols = useMemo(() => columns.map(k => fieldByKey(dataset, k)).filter(Boolean), [columns, dataset]);
  const sortedAll = useMemo(() => {
    const list = scopeRows.slice();
    const fld = sort.col ? fieldByLabelMap[sort.col] : null;
    if (!fld) return list;
    list.sort((a, b) => {
      const av = fld.get(a);
      const bv = fld.get(b);
      let cmp;
      if (fld.type === 'number' || fld.type === 'money' || fld.type === 'percent') cmp = (Number(av) || 0) - (Number(bv) || 0);
      else if (fld.type === 'date') cmp = new Date(av || 0).getTime() - new Date(bv || 0).getTime();
      else cmp = String(av ?? '').localeCompare(String(bv ?? ''));
      return sort.dir === 'desc' ? -cmp : cmp;
    });
    return list;
  }, [scopeRows, fieldByLabelMap, sort]);
  const chartRows = useMemo(() => {
    const def = appliedDef;
    if (!def || !def.groupBy || chartMode === 'NONE') return [];
    const gf = fieldByLabelMap[def.groupBy];
    if (!gf) return [];
    const mf = def.measure && def.measure.field ? fieldByLabelMap[def.measure.field] : null;
    const meas = def.measure ? { agg: def.measure.agg, field: mf ? mf.key : undefined } : { agg: 'count' };
    const g = groupRows(scopeRows, dataset, [gf.key], [meas]);
    const isTime = /Month|Date|Year|Timestamp/.test(def.groupBy);
    g.sort((a, b) => isTime
      ? String(a.path[0]).localeCompare(String(b.path[0]))
      : (Number(b.values[0]) || 0) - (Number(a.values[0]) || 0));
    return g.slice(0, 24).map(b => ({ id: String(b.path[0]), label: String(b.path[0]), value: Number(b.values[0]) || 0 }));
  }, [scopeRows, dataset, fieldByLabelMap, appliedDef, chartMode]);
  const measureField = appliedDef && appliedDef.measure && appliedDef.measure.field ? fieldByLabelMap[appliedDef.measure.field] : null;
  const fmtChart = useCallback((v) => formatValue(v, measureField ? measureField.type : 'number'), [measureField]);

  const stamp = () => new Date().toISOString().slice(0, 10);
  const exportCSV = () => {
    const def = appliedDef;
    if (!def || !tableCols.length) return;
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
      doc.setFillColor(26, 46, 48);
      doc.rect(m, y - 12, pw - m * 2, 16, 'F');
      doc.setTextColor(238, 140, 58);
      doc.setFontSize(7);
      cols.forEach((c, i) => doc.text(String(c.label).toUpperCase().slice(0, 24), m + i * cw + 3, y));
      y += 10;
    };
    head();
    doc.setTextColor(26, 46, 48);
    doc.setFontSize(7);
    list.forEach(r => {
      if (y > ph - 40) {
        doc.addPage();
        y = m;
        head();
        doc.setTextColor(26, 46, 48);
        doc.setFontSize(7);
      }
      cols.forEach((c, i) => doc.text(String(formatValue(c.get(r), c.type)).slice(0, 26), m + i * cw + 3, y));
      doc.setDrawColor(223, 217, 209);
      doc.line(m, y + 2, pw - m, y + 2);
      y += 12;
    });
  };
  const exportPDF = () => {
    const def = appliedDef;
    if (!def || !tableCols.length) return;
    const doc = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
    const pw = doc.internal.pageSize.getWidth();
    doc.setFillColor(22, 42, 44);
    doc.rect(0, 0, pw, 70, 'F');
    doc.setTextColor(238, 140, 58);
    doc.setFontSize(16);
    doc.text('GOLDEN SEED -- ' + def.title, 30, 32);
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(8);
    doc.text((entity ? entity.type + ' ' + entity.value : 'WHOLE SOURCE') + '  |  ' +
      (def.period ? periodHuman().toUpperCase() : 'AS AT TODAY') + '  |  SORT ' +
      (sort.col || 'DEFAULT') + ' ' + sort.dir.toUpperCase() + '  |  ' + sortedAll.length + ' ROWS', 30, 50);
    doc.setTextColor(150, 160, 160);
    doc.setFontSize(7);
    doc.text(def.desc + '  Generated ' + new Date().toLocaleString() + '.', 30, 62);
    const finish = (png) => {
      let y = 96;
      if (png) {
        try { doc.addImage(png, 'PNG', 30, y, 500, 190); } catch (e) { /* chart image best-effort */ }
        y += 200;
      }
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
          c.width = 1360;
          c.height = Math.max(300, Math.round(1360 * (img.height / (img.width || 1360))));
          const ctx = c.getContext('2d');
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, c.width, c.height);
          ctx.drawImage(img, 0, 0, c.width, c.height);
          finish(c.toDataURL('image/png'));
        };
        img.onerror = () => finish(null);
        img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(xml)));
        return;
      }
    } catch (e) { /* fall through to text-only PDF */ }
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

STU_CSS = r'''/* PATH: erp-frontend/src/pages/Reports/ReportStudio.module.css */
/* GOLDEN SEED -- REPORT STUDIO STYLESHEET (fix84 complete rewrite).
   Every class the studio JSX references is defined here, once, in the app's
   own language: dark teal panels with #162a2c heads and orange separators,
   white controls with ink text, orange for active/hover, Intake chip spec. */
.studio { display: flex; flex-direction: column; gap: clamp(10px, 1.4vw, 16px); }
.scopePanel, .catPanel, .viewerPanel {
  background: linear-gradient(135deg, #4a6a6c 0%, #3a5a5c 55%, #2f4c4e 100%);
  border: 1.5px solid rgba(238, 140, 58, 0.22);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
  overflow: visible;
}
.panelHeadRow {
  display: flex; flex-wrap: wrap; align-items: center; gap: 10px;
  background: #162a2c; border-bottom: 1.5px solid #EE8C3A;
  border-radius: 11px 11px 0 0; padding: 10px 14px;
}
.scopeTitle { font-family: 'Cinzel', serif; color: #EE8C3A; font-size: clamp(10px, 1.1vw, 13px); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
.badge { font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px); font-weight: 700; letter-spacing: 1px; color: rgba(255,255,255,0.65); background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.16); border-radius: 20px; padding: 4px 12px; }
.scopeBody { padding: clamp(12px, 1.6vw, 18px); display: flex; flex-direction: column; gap: clamp(10px, 1.3vw, 14px); }
.chip {
  display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
  font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px); font-weight: 900;
  letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 14px; border-radius: 6px;
  border: 1.5px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.85); transition: all 0.2s ease;
}
.chip:hover:not(:disabled) { border-color: #EE8C3A; color: #EE8C3A; background: rgba(238,140,58,0.12); }
.chip:disabled { opacity: 0.45; cursor: not-allowed; }
.tileRow { display: flex; flex-wrap: wrap; gap: 8px; }
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
.tileCount { font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.8vw, 9px); opacity: 0.75; }
.hint { display: flex; align-items: center; gap: 7px; margin: 0; font-size: clamp(10px, 1vw, 11.5px); font-weight: 600; color: rgba(255,255,255,0.66); }
.hint svg { color: #EE8C3A; flex-shrink: 0; }
.error { display: flex; align-items: center; gap: 8px; background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; font-size: 11.5px; font-weight: 700; border-radius: 6px; padding: 8px 12px; }
.scopeRow { display: flex; flex-wrap: wrap; gap: clamp(12px, 1.8vw, 24px); align-items: flex-start; }
.scopeField { display: flex; flex-direction: column; gap: 6px; min-width: 0; position: relative; }
.miniLabel { font-size: clamp(8px, 0.85vw, 10px); font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(255,255,255,0.6); }
.entWrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.chipE { display: inline-flex; align-items: center; gap: 8px; background: #EE8C3A; color: #1a2e30; border-radius: 6px; padding: 9px 12px; font-size: 10px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; }
.chipE button { background: transparent; border: none; cursor: pointer; color: #1a2e30; font-size: 12px; font-weight: 900; display: flex; }
.pickBtn {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  min-width: clamp(150px, 18vw, 240px); height: 38px; padding: 0 12px; border-radius: 6px;
  border: 1.5px solid #dfd9d1; background: #fff; color: #1a2e30;
  font-family: 'Inter', sans-serif; font-size: clamp(10px, 1.05vw, 12px); font-weight: 800;
  letter-spacing: 0.5px; text-transform: uppercase; cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.pickBtn:hover { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.pickBtn svg { color: #EE8C3A; transition: transform 0.2s; flex-shrink: 0; }
.pickIconOpen { transform: rotate(180deg); }
.pickList {
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
.pickCheck input { accent-color: #EE8C3A; width: 15px; height: 15px; cursor: pointer; flex-shrink: 0; }
.perChips { display: flex; flex-wrap: wrap; gap: 6px; }
.perChipsDim { opacity: 0.45; pointer-events: none; }
.pchip {
  cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);
  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 12px;
  border-radius: 6px; border: 1.5px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.85); transition: all 0.2s ease; white-space: nowrap;
}
.pchip:hover { border-color: #EE8C3A; color: #EE8C3A; }
.pchipOn { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.customRange { display: flex; align-items: center; gap: 8px; }
.customRange input { height: 36px; padding: 0 10px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; color: #1a2e30; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; }
.customRange span { color: rgba(255,255,255,0.6); font-weight: 900; font-size: 10px; }
.snapHint { color: #EE8C3A; font-size: 9px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; }
.sortRow { display: flex; gap: 6px; align-items: center; }
.dirBtn { height: 38px; width: 38px; flex: 0 0 38px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; color: #EE8C3A; font-size: 15px; font-weight: 900; cursor: pointer; transition: all 0.2s; }
.dirBtn:hover { border-color: #EE8C3A; }
.searchBox { position: relative; height: 36px; width: clamp(170px, 22vw, 280px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }
.searchBox:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.searchIcon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; color: #EE8C3A; pointer-events: none; }
.searchBox input { width: 100%; height: 100%; border: none; outline: none; background: transparent; padding: 0 30px 0 32px; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; }
.searchClear { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background: transparent; border: none; cursor: pointer; color: rgba(26,46,48,0.45); display: flex; padding: 4px; }
.searchClear:hover { color: #1a2e30; }
.tabRow { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 14px; background: rgba(0,0,0,0.16); border-bottom: 1px solid rgba(255,255,255,0.08); }
.gtab {
  cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);
  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 7px 12px;
  border-radius: 6px; border: 1.5px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.8); transition: all 0.2s;
}
.gtab:hover { border-color: #EE8C3A; color: #EE8C3A; }
.gtabOn { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.gcnt { font-family: 'Space Mono', monospace; opacity: 0.7; margin-left: 6px; }
.recentRow { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 8px 14px; background: #fff; border-bottom: 1px solid #dfd9d1; }
.recentLabel { font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: rgba(26,46,48,0.45); margin-right: 4px; }
.rchip {
  cursor: pointer; font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 900;
  letter-spacing: 1px; text-transform: uppercase; padding: 6px 10px; border-radius: 6px;
  border: 1.5px solid rgba(238,140,58,0.5); background: #fff; color: #b45309; transition: all 0.2s;
}
.rchip:hover { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.catList { max-height: 340px; overflow-y: auto; background: #fff; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }
.catList::-webkit-scrollbar { width: 6px; }
.catList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }
.catWrap { border-bottom: 1px solid #f1eeea; }
.catWrap:last-child { border-bottom: none; }
.catRow { display: flex; flex-direction: column; gap: 3px; width: 100%; text-align: left; border: none; background: #fff; padding: 9px 14px; cursor: pointer; transition: background 0.15s; }
.catRow:hover, .catRowOn { background: #EE8C3A; color: #fff; }
.r1 { display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
.r2 { font-size: 10px; font-weight: 600; color: rgba(26,46,48,0.55); }
.catRow:hover .r2, .catRowOn .r2 { color: rgba(255,255,255,0.85); }
.tag { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; opacity: 0.75; white-space: nowrap; }
.readout { display: flex; align-items: center; gap: 12px; background: #0a0a0a; border-left: 3px solid #EE8C3A; padding: 8px 12px; }
.readoutText { flex: 1; min-width: 0; font-family: 'Inter', sans-serif; font-size: 10.5px; font-weight: 600; line-height: 1.5; color: #c9f7d6; }
.useBtn {
  flex-shrink: 0; cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);
  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 14px;
  border-radius: 6px; border: none; background: #EE8C3A; color: #1a2e30; transition: all 0.2s;
}
.useBtn:hover:not(:disabled) { background: #f0a050; transform: translateY(-1px); }
.useBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.emptyCell { text-align: center; padding: 24px 16px; font-family: 'Space Mono', monospace; font-size: 11px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(26,46,48,0.5); }
.foot { padding: 8px 14px; background: #f6f3ef; color: rgba(26,46,48,0.55); font-size: 9px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; border-radius: 0 0 11px 11px; }
.viewerPanel { padding: clamp(12px, 1.6vw, 18px); display: flex; flex-direction: column; gap: clamp(10px, 1.3vw, 14px); }
.viewerPanel .panelHeadRow { background: transparent; border-bottom: 1.5px solid #EE8C3A; border-radius: 0; padding: 0 0 10px 0; }
.pvChips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.pvChip {
  font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px); font-weight: 700;
  letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.78);
  border: 1px solid rgba(255,255,255,0.22); border-radius: 4px; padding: 3px 8px;
  background: rgba(255,255,255,0.06); white-space: nowrap;
}
.pvBtns { margin-left: auto; display: flex; gap: 8px; flex-wrap: wrap; }
.chartChips { display: flex; gap: 6px; flex-wrap: wrap; }
.cchip {
  cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);
  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 7px 12px;
  border-radius: 6px; border: 1.5px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.8); transition: all 0.2s;
}
.cchip:hover { border-color: #EE8C3A; color: #EE8C3A; }
.cchipOn { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }
.chartBox {
  --accent: #EE8C3A; --surface: #ffffff; --surface-3: #efe9e2; --surface-edge: #dfd9d1;
  --ink: #1a2e30; --ink-soft: #5b6f70; --ink-faint: rgba(26,46,48,0.45);
  background: #fff; border: 1.5px solid #dfd9d1; border-radius: 8px; padding: clamp(10px, 1.4vw, 14px);
}
.pvScroll { overflow-x: auto; background: #fff; border: 1.5px solid #dfd9d1; border-radius: 8px; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }
.pvScroll::-webkit-scrollbar { height: 8px; }
.pvScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 4px; }
.pvTable { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 640px; }
.pvTable th { position: sticky; top: 0; z-index: 2; background: #162a2c; color: #EE8C3A; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px); font-weight: 900; letter-spacing: 2px; text-transform: uppercase; text-align: left; padding: 9px 12px; white-space: nowrap; }
.pvTable td { padding: 8px 12px; border-bottom: 1px solid #f1eeea; color: #1a2e30; font-size: clamp(10px, 1.05vw, 12px); font-weight: 600; white-space: nowrap; }
.pvTable tbody tr:nth-child(even) td { background: #fbf9f7; }
.pvTable tbody tr:hover td { background: rgba(238,140,58,0.22); }
.pvTable th:first-child, .pvTable td:first-child { position: sticky; left: 0; z-index: 3; }
.pvTable th:first-child { background: #162a2c; }
.pvTable td:first-child { background: #fff; font-family: 'Space Mono', monospace; font-weight: 700; border-right: 1px solid #dfd9d1; }
.pvTable tbody tr:nth-child(even) td:first-child { background: #fbf9f7; }
.pvTable tbody tr:hover td:first-child { background: rgba(238,140,58,0.22); }
.pvNote { color: rgba(255,255,255,0.62); font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px); font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; line-height: 1.7; }
.appliedLine { color: rgba(26,46,48,0.62); font-size: clamp(9px, 0.95vw, 11px); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }
.appliedLine b { color: #EE8C3A; }
@media (max-width: 900px) {
  .scopeRow { flex-direction: column; align-items: stretch; }
  .pickBtn { min-width: 100%; }
  .pvBtns { margin-left: 0; }
  .searchBox { margin-left: 0; width: 100%; }
}
'''

ADDENDUM = '''
- fix84 (2026-09-25): Reports page rewritten as ONE matched set after the live page shipped with three mismatches (hub lost canSeeMoney/reloadToken so root was told money is hidden; hub header used pageTitle/pageSubtitle classes its CSS never defined, giving a white-on-white title; studio JSX referenced ~40 class names missing from its stylesheet, leaving naked controls). fix84 rewrites ReportHub.jsx (correct header classes + both props + REFRESH header button), ReportStudio.jsx (scope bar + catalogue + readout + full viewer with chart chips, sample table, CSV and composed PDF) and ReportStudio.module.css (complete stylesheet defining every class the JSX uses, in the app's panel/chip language). reportsCatalog.js and reportData.js untouched.
'''

print('=' * 72)
print(' GOLDEN SEED fix84 -- Reports page as one matched set (hub+studio+css)')
print('=' * 72)

for path, content, tag in ((HUB, HUB_JS, 'rewrite ReportHub.jsx (props + header classes)'),
                           (STU, STUDIO_JS, 'rewrite ReportStudio.jsx (scope+catalogue+viewer)'),
                           (STUCSS, STU_CSS, 'rewrite ReportStudio.module.css (complete)')):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print('OK      ' + tag)

with open(ADD, 'a', encoding='utf-8', newline='\n') as f:
    f.write(ADDENDUM)
print('OK      addendum appended')
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
    print('(erp-frontend/node_modules not installed -- skipping local build check)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix84: Reports page rewritten as one matched set (hub props + header classes, full studio, complete stylesheet)'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. After the green tick, hard-refresh (Ctrl+Shift+R) and walk the page.')