// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
// GOLDEN SEED -- REPORT STUDIO (fix84): scope bar + catalogue + viewer.
// One chain: dataset -> entity -> period -> columns -> sort -> report ->
// chart + table + CSV + PDF. Every control recomputes the same row set, so
// chart, table and downloads can never disagree.
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiChevronDown, FiAlertCircle } from 'react-icons/fi';
import { jsPDF } from 'jspdf';
import { Chart } from '../../components/common/Charts';
import {
  DATASETS, datasetsFor, fieldsFor, fieldByKey, applyFilters,
  groupRows, formatValue, toCSV, downloadCSV,
} from './reportData';
import { CATALOGUE, ENTITIES, GROUPS, DEFAULTS } from './reportsCatalog';
import styles from './ReportStudio.module.css';

const PERIODS = ['TODAY','THIS WEEK','LAST WEEK','THIS MONTH','LAST MONTH','THIS QUARTER','THIS YEAR','LAST YEAR','ALL TIME','CUSTOM'];
const CHART_MAP = { BAR: 'bars', COLUMN: 'column', LINE: 'line', AREA: 'line', DONUT: 'donut' };
const CHART_OPTS = ['NONE','BAR','COLUMN','LINE','AREA','DONUT'];
const RECENT_KEY = 'gs.reports.recent.v1';
const SAMPLE = 8;
const SEARCH_HINT = {
  PROJECTS: 'Project index, plot, owner name, NIN...',
  CLIENTS: 'Client name, NIN, phone...',
  PAYMENTS: 'Receipt no, project, client...',
  EXPENSES: 'Item, category, project...',
  COMPANY: 'Any row across the company...',
};

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
  const [counts, setCounts] = useState({});
  const countsRef = useRef({});
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
  const [chartOpen, setChartOpen] = useState(false);
  const [scopeOpen, setScopeOpen] = useState(true);
  const [catOpen, setCatOpen] = useState(true);
  const [entQuery, setEntQuery] = useState('');
  const colRef = useRef(null);
  const sortRef = useRef(null);
  const entRef = useRef(null);
  const chartRef = useRef(null);
  const chartDdRef = useRef(null);
  useEffect(() => {
    const h = (e) => {
      if (colRef.current && !colRef.current.contains(e.target)) setColOpen(false);
      if (sortRef.current && !sortRef.current.contains(e.target)) setSortOpen(false);
      if (entRef.current && !entRef.current.contains(e.target)) setEntOpen(false);
      if (chartDdRef.current && !chartDdRef.current.contains(e.target)) setChartOpen(false);
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
  useEffect(() => {
    let alive = true;
    const put = (k, v) => { countsRef.current[k] = v; setCounts(c => ({ ...c, [k]: v })); };
    available.forEach(ds => {
      if (ds.key === datasetKey || countsRef.current[ds.key] != null) return;
      ds.load().then(data => { if (alive) put(ds.key, Array.isArray(data) ? data.length : 0); })
        .catch(() => { if (alive) put(ds.key, 0); });
    });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [available, datasetKey]);
  useEffect(() => {
    if (countsRef.current[datasetKey] !== rows.length) {
      countsRef.current[datasetKey] = rows.length;
      setCounts(c => ({ ...c, [datasetKey]: rows.length }));
    }
  }, [datasetKey, rows.length]);
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
  const defaultName = (DEFAULTS[datasetKey] || {})[entity ? entity.type : 'ALL'] || '';
  const defaultDef = CATALOGUE.find(d => d.title === defaultName && d.ds === datasetKey && (!d.money || canSeeMoney)) || null;
  const recentDefs = recent.map(id => CATALOGUE.find(d => d.id === id)).filter(Boolean);
  const restList = listed.filter(d => !defaultDef || d.id !== defaultDef.id);
  const entMatches = useMemo(() => {
    const q = entQuery.trim().toUpperCase();
    if (!q) return [];
    const out = [];
    entityTypes.forEach(t => {
      entityValues(t.type).forEach(v => {
        if (String(v).toUpperCase().indexOf(q) >= 0) out.push({ type: t.type, label: t.label, value: v });
      });
    });
    return out.slice(0, 15);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entQuery, entityTypes, rows]);

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
  const catRowNode = (def) => (
    <div key={def.id} className={styles.catWrap}>
      <button className={styles.catRow + (appliedId === def.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === def.id ? null : def.id)} aria-expanded={readId === def.id}>
        <span className={styles.r1}>{def.title}<span className={styles.tag}>{def.chart !== 'NONE' ? def.chart : 'TABLE'} &middot; {def.group}</span><span className={styles.toggleHint}>{readId === def.id ? 'CLOSE \u25B2' : 'WHAT IS THIS? \u25BC'}</span></span>
        <span className={styles.r2}>{def.desc}</span>
      </button>
      {readId === def.id && (
        <div className={styles.readout}>
          <div className={styles.readoutText}>{readout(def)}</div>
          <button className={styles.useBtn} onClick={() => applyDef(def)}>USE THIS REPORT</button>
        </div>
      )}
    </div>
  );

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
      <div className={styles.sourceRow}>
        <div className={styles.sourcePanel}>
          <div className={styles.tileRow}>
            {available.map(ds => (
              <button key={ds.key} className={ds.key === datasetKey ? styles.tileActive : styles.tile} onClick={() => setDatasetKey(ds.key)}>
                {ds.label}
                <span className={styles.tileCount}>{counts[ds.key] != null ? counts[ds.key] : (ds.key === datasetKey && loading ? '...' : '')}</span>
              </button>
            ))}
          </div>
        </div>
        <span className={styles.sourceCount}>{loading ? '...' : rows.length} SOURCE ROWS</span>
      </div>
      <div className={styles.scopePanel}>
        <div className={styles.panelHeadRow}>
          <span className={styles.scopeTitle}>SCOPE</span>
          <button className={styles.headToggle} onClick={() => setScopeOpen(o => !o)} aria-expanded={scopeOpen} aria-label="Collapse or expand scope panel">
            <FiChevronDown className={scopeOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
          </button>
        </div>
        <div className={scopeOpen ? styles.scopeBody : styles.panelClosed}>
          {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden="true" /> {error}</div>}
          {!canSeeMoney && (
            <p className={styles.hint}>
              <FiAlertCircle size={12} aria-hidden="true" /> Financial datasets, money columns and company reports are hidden on your role.
            </p>
          )}
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
                <input
                  className={styles.entInput}
                  value={entQuery}
                  placeholder={entity ? 'Change...' : (SEARCH_HINT[datasetKey] || 'Type to search this source...')}
                  onFocus={() => setEntOpen(true)}
                  onChange={e => { setEntQuery(e.target.value); setEntOpen(true); }}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      if (entMatches[0]) { setEntity(entMatches[0]); setEntQuery(''); setEntOpen(false); }
                      e.preventDefault();
                    }
                  }}
                  aria-label="Search who / what"
                />
                {entOpen && (
                  <div className={styles.pickList}>
                    <div className={styles.ddScroll}>
                      {!entQuery && <button className={styles.pickOption} onClick={() => { setEntity(null); setEntQuery(''); setEntOpen(false); }}>WHOLE COMPANY</button>}
                      {!entQuery && <div className={styles.ddFootMsg}>TYPE TO SEARCH THIS SOURCE -- ENTER PICKS THE FIRST MATCH</div>}
                      {entQuery && entMatches.length === 0 && <div className={styles.ddFootMsg}>NO MATCH IN THIS SOURCE</div>}
                      {entQuery && entMatches.map(m => (
                        <button key={m.type + m.value} className={styles.pickOption} onClick={() => { setEntity(m); setEntQuery(''); setEntOpen(false); }}>
                          {m.value}<span className={styles.pickOptionTag}>{m.label}</span>
                        </button>
                      ))}
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
                  {sort.dir === 'desc' ? '\u2193' : '\u2191'}
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

      <div className={catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.catPanelClosed}>
        <div className={styles.panelHeadRow}>
          <span className={styles.scopeTitle}>REPORT CATALOGUE</span>
          <span className={styles.badge}>{searched.length} MATCHES</span>
          <button className={styles.headToggle} onClick={() => setCatOpen(o => !o)} aria-expanded={catOpen} aria-label="Collapse or expand catalogue panel">
            <FiChevronDown className={catOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
          </button>
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
          {defaultDef && (
            <div className={styles.catWrap}>
              <button className={styles.catRow + ' ' + styles.catRowDef + (appliedId === defaultDef.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === defaultDef.id ? null : defaultDef.id)} aria-expanded={readId === defaultDef.id}>
                <span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.tag}>{defaultDef.chart !== 'NONE' ? defaultDef.chart : 'TABLE'} &middot; {defaultDef.group}</span><span className={styles.toggleHint}>{readId === defaultDef.id ? 'CLOSE \u25B2' : 'WHAT IS THIS? \u25BC'}</span></span>
                <span className={styles.r2}>{defaultDef.desc}</span>
              </button>
              {readId === defaultDef.id && (
                <div className={styles.readout}>
                  <div className={styles.readoutText}>{readout(defaultDef)}</div>
                  <button className={styles.useBtn} onClick={() => applyDef(defaultDef)}>USE THIS REPORT</button>
                </div>
              )}
            </div>
          )}
          {restList.length === 0 && !defaultDef && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}
          {groupTab === 'ALL'
            ? GROUPS.filter(g => restList.some(d => d.group === g)).map(g => (
              <div key={g}>
                <div className={styles.ddSec}>{g} ({restList.filter(d => d.group === g).length})</div>
                {restList.filter(d => d.group === g).map(catRowNode)}
              </div>
            ))
            : restList.map(catRowNode)}
        </div>
        <div className={styles.foot}>
          {listed.length} report{listed.length === 1 ? '' : 's'} in {groupTab === 'ALL' ? 'all groups' : groupTab}{defaultDef ? ' (+1 default)' : ''}
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
              <span className={styles.pvChipDd} ref={chartDdRef}>
                CHART
                <button className={styles.chartDdBtn} onClick={() => setChartOpen(o => !o)} aria-expanded={chartOpen}>
                  {chartMode}<FiChevronDown className={chartOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
                </button>
                {chartOpen && (
                  <div className={styles.pickList}>
                    <div className={styles.ddScroll}>
                      {CHART_OPTS.map(t => (
                        <button key={t} className={styles.pickOption + (chartMode === t ? ' ' + styles.pickOptionActive : '')} onClick={() => { setChartMode(t); setChartOpen(false); }}>{t}</button>
                      ))}
                    </div>
                  </div>
                )}
              </span>
            </div>
            <div className={styles.pvBtns}>
              <button className={styles.useBtn} onClick={exportCSV} disabled={!sortedAll.length || !tableCols.length}>CSV -- THE DATA</button>
              <button className={styles.useBtnDark} onClick={exportPDF} disabled={!sortedAll.length || !tableCols.length}>PDF -- THE DOCUMENT</button>
            </div>
          </div>
          <div className={styles.approachNote}>
            CSV = every matching row, flat, for Excel. PDF = one document: cover with scope stamp and the chart, then all table pages in landscape with repeated headers. The screen table stays a sample so the page stays fast.
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

      {!appliedDef && (
        <div className={styles.viewerEmpty}>
          PICK A REPORT ABOVE -- ITS LIVE CHART, PREVIEW, CSV AND PDF LAND HERE
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
