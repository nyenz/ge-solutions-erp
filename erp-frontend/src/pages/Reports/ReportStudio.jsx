// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
// GOLDEN SEED -- REPORT STUDIO (stage 2): scope bar + catalogue + readout.
// Imports exactly { CATALOGUE, ENTITIES, GROUPS } from ./reportsCatalog.
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiChevronDown, FiAlertCircle, FiRefreshCw } from 'react-icons/fi';
import { DATASETS, datasetsFor, fieldsFor, fieldByKey, formatValue } from './reportData';
import { CATALOGUE, ENTITIES, GROUPS } from './reportsCatalog';
import styles from './ReportStudio.module.css';

const PERIODS = ['TODAY','THIS WEEK','LAST WEEK','THIS MONTH','LAST MONTH','THIS QUARTER','THIS YEAR','LAST YEAR','ALL TIME','CUSTOM'];

const ReportStudio = ({ canSeeMoney = false, reloadToken = 0 }) => {
  const available = useMemo(() => datasetsFor(canSeeMoney), [canSeeMoney]);
  const [datasetKey, setDatasetKey] = useState(available[0]?.key || 'PROJECTS');
  const dataset = DATASETS[datasetKey] || available[0];
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [entity, setEntity] = useState(null);           // {type,label,value}
  const [period, setPeriod] = useState('THIS MONTH');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [columns, setColumns] = useState([]);
  const [sort, setSort] = useState({ col: '', dir: 'asc' });
  const [search, setSearch] = useState('');
  const [groupTab, setGroupTab] = useState('ALL');
  const [readId, setReadId] = useState(null);
  const [appliedId, setAppliedId] = useState(null);
  const [colOpen, setColOpen] = useState(false);
  const [sortOpen, setSortOpen] = useState(false);
  const [entOpen, setEntOpen] = useState(false);
  const colRef = useRef(null); const sortRef = useRef(null); const entRef = useRef(null);
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
  const fieldByLabel = useMemo(() => {
    const m = {}; fields.forEach(f => { m[f.label] = f; }); return m;
  }, [fields]);
  const load = useCallback(async (key) => {
    const ds = DATASETS[key]; if (!ds) return;
    setLoading(true); setError('');
    try { const d = await ds.load(); setRows(Array.isArray(d) ? d : []); }
    catch { setRows([]); setError('Could not load ' + ds.label.toLowerCase() + '.'); }
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
    setEntity(null); setAppliedId(null); setReadId(null); setGroupTab('ALL'); setSearch('');
    setSort({ col: '', dir: 'asc' });
  }, [datasetKey, canSeeMoney]);

  const entityTypes = ENTITIES[datasetKey] || [];
  const entityValues = (type) => {
    const t = entityTypes.find(x => x.type === type); if (!t) return [];
    const fld = fieldByLabel[t.field]; if (!fld) return [];
    const seen = []; rows.forEach(r => { const v = fld.get(r); if (v && seen.indexOf(v) < 0) seen.push(v); });
    return seen.sort().slice(0, 40);
  };
  const periodHuman = () => {
    const m = { TODAY:'today','THIS WEEK':'this week','LAST WEEK':'last week','THIS MONTH':'this month','LAST MONTH':'last month','THIS QUARTER':'this quarter','THIS YEAR':'this year','LAST YEAR':'last year','ALL TIME':'since records began' };
    if (period !== 'CUSTOM') return m[period] || period;
    return 'between ' + (from || '..') + ' and ' + (to || '..');
  };
  const catalogue = useMemo(() => CATALOGUE.filter(d =>
    d.ds === datasetKey && (!d.money || canSeeMoney) &&
    (!entity || (d.scopes || []).indexOf(entity.type) >= 0)
  ), [datasetKey, canSeeMoney, entity]);
  const searched = useMemo(() => {
    const q = search.trim().toUpperCase();
    return catalogue.filter(d => !q || d.title.toUpperCase().indexOf(q) >= 0 || d.desc.toUpperCase().indexOf(q) >= 0);
  }, [catalogue, search]);
  useEffect(() => {
    if (groupTab !== 'ALL' && !searched.some(d => d.group === groupTab)) setGroupTab('ALL');
  }, [searched, groupTab]);
  const listed = groupTab === 'ALL' ? searched : searched.filter(d => d.group === groupTab);
  const appliedDef = CATALOGUE.find(d => d.id === appliedId) || null;
  const toggleColumn = (key) => setColumns(c => c.indexOf(key) >= 0 ? c.filter(k => k !== key) : [...c, key]);
  const applyDef = (def) => {
    setAppliedId(def.id); setReadId(null);
    const keys = (def.cols || []).map(l => (fieldByLabel[l] || {}).key).filter(Boolean);
    if (keys.length) setColumns(keys);
    if (def.sort) setSort({ col: def.sort.col, dir: def.sort.dir });
  };
  const readout = (def) => {
    let s = def.desc;
    s += entity ? (' For ' + entity.label.toLowerCase() + ' ' + entity.value + '.') : (' Whole company.');
    s += def.period ? (' Period: ' + periodHuman() + '.') : (' Right-now snapshot.');
    const sc = def.sort ? def.sort : { col: 'first column', dir: 'asc' };
    s += ' Sorted by ' + sc.col + ' ' + (sc.dir === 'desc' ? 'highest first.' : 'A to Z.');
    return s;
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
        <div className={styles.tileRow}>
          {available.map(ds => (
            <button key={ds.key} className={ds.key === datasetKey ? styles.tileActive : styles.tile} onClick={() => setDatasetKey(ds.key)}>
              {ds.label}<span className={styles.tileCount}>{ds.key === datasetKey && loading ? '...' : ''}</span>
            </button>
          ))}
        </div>
        <p className={styles.hint}>{dataset?.blurb}</p>
        {!canSeeMoney && (
          <p className={styles.hint}><FiAlertCircle size={12} aria-hidden="true" /> Financial datasets and money columns are hidden on your role.</p>
        )}
        {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden="true" /> {error}</div>}
        <div className={styles.scopeRow}>
          <div className={styles.scopeField} ref={entRef}>
            <span className={styles.miniLabel}>Who / what</span>
            <div className={styles.entWrap}>
              {entity && (
                <span className={styles.chipE}>{entity.label}: {entity.value}
                  <button onClick={() => setEntity(null)} aria-label="Clear entity"><FiX size={11} aria-hidden="true" /></button>
                </span>
              )}
              <button className={styles.pickBtn} onClick={() => setEntOpen(o => !o)} aria-expanded={entOpen}>
                <span>{entity ? 'Change...' : 'Whole company'}</span><FiChevronDown className={entOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
              </button>
              {entOpen && (
                <div className={styles.pickList}>
                  <div className={styles.ddScroll}>
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
            <div className={styles.perChips + (appliedDef && !appliedDef.period ? ' ' + styles.dim : '')}>
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
          </div>
          <div className={styles.scopeField} ref={colRef}>
            <span className={styles.miniLabel}>Columns</span>
            <button className={styles.pickBtn} onClick={() => setColOpen(o => !o)} aria-expanded={colOpen}>
              <span>{columns.length} OF {fields.length} COLUMNS</span><FiChevronDown className={colOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
            </button>
            {colOpen && (
              <div className={styles.pickList}>
                <div className={styles.ddScroll}>
                  {fields.map(f => (
                    <label key={f.key} className={styles.pickOption + (columns.indexOf(f.key) >= 0 ? ' ' + styles.pickOptionActive : '')}>
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
                <span>{sort.col || 'DEFAULT'}</span><FiChevronDown className={sortOpen ? styles.pickIconOpen : ''} aria-hidden="true" />
              </button>
              <button className={styles.dirBtn} onClick={() => setSort(s => ({ col: s.col, dir: s.dir === 'desc' ? 'asc' : 'desc' }))} aria-label="Flip sort direction">
                {sort.dir === 'desc' ? '\u2193' : '\u2191'}
              </button>
              {sortOpen && (
                <div className={styles.pickList}>
                  <div className={styles.ddScroll}>
                    <button className={styles.pickOption + (!sort.col ? ' ' + styles.pickOptionActive : '')} onClick={() => { setSort({ col: '', dir: 'asc' }); setSortOpen(false); }}>DEFAULT</button>
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
          <button className={groupTab === 'ALL' ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab('ALL')}>ALL<span className={styles.gcnt}>{searched.length}</span></button>
          {GROUPS.map(g => {
            const n = searched.filter(d => d.group === g).length;
            if (!n && g !== groupTab) return null;
            return <button key={g} className={groupTab === g ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab(g)}>{g}<span className={styles.gcnt}>{n}</span></button>;
          })}
        </div>
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
        <div className={styles.foot}>{listed.length} report{listed.length === 1 ? '' : 's'} in {groupTab === 'ALL' ? 'all groups' : groupTab}{search ? ' matching "' + search + '"' : ''}{entity ? ' for ' + entity.label.toLowerCase() + ' ' + entity.value : ' for the whole company'}</div>
      </div>

      <div className={styles.appliedLine}>
        {appliedDef
          ? <>APPLIED: <b>{appliedDef.title}</b> &middot; {columns.length} columns &middot; sorted {sort.col || 'default'} {sort.dir === 'desc' ? 'desc' : 'asc'} &middot; {entity ? entity.label + ' ' + entity.value : 'whole company'} &middot; {appliedDef.period ? periodHuman() : 'right now'}</>
          : <>No report applied yet &mdash; open a report above and press USE THIS REPORT.</>}
      </div>
    </div>
  );
};
export default ReportStudio;
