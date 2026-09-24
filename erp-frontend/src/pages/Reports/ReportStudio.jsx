// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
// GOLDEN SEED -- REPORT STUDIO (stage 1: scope bar + catalogue).
// Stage 2 adds the viewer (chart + table + CSV). Stage 3 adds PDF/advanced.
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiChevronDown, FiRefreshCw, FiAlertCircle, FiEye, FiLock } from 'react-icons/fi';
import { DATASETS, datasetsFor, fieldsFor, fieldByKey, applyFilters } from './reportData';
import { CATALOG } from './reportsCatalog';
import styles from './ReportStudio.module.css';

const PERIODS = ['TODAY','THIS WEEK','LAST WEEK','THIS MONTH','LAST MONTH','THIS QUARTER','THIS YEAR','LAST YEAR','ALL TIME','CUSTOM'];

const periodRange = (period, from, to) => {
  const now = new Date();
  let s = null, e = null;
  if (period === 'TODAY') { s = new Date(now); e = new Date(now); }
  else if (period === 'THIS WEEK') { const day = (now.getDay() + 6) % 7; s = new Date(now); s.setDate(now.getDate() - day); e = new Date(now); }
  else if (period === 'LAST WEEK') { const day = (now.getDay() + 6) % 7; s = new Date(now); s.setDate(now.getDate() - day - 7); e = new Date(s); e.setDate(s.getDate() + 6); }
  else if (period === 'THIS MONTH') { s = new Date(now.getFullYear(), now.getMonth(), 1); e = new Date(now); }
  else if (period === 'LAST MONTH') { s = new Date(now.getFullYear(), now.getMonth() - 1, 1); e = new Date(now.getFullYear(), now.getMonth(), 0); }
  else if (period === 'THIS QUARTER') { s = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1); e = new Date(now); }
  else if (period === 'THIS YEAR') { s = new Date(now.getFullYear(), 0, 1); e = new Date(now); }
  else if (period === 'LAST YEAR') { s = new Date(now.getFullYear() - 1, 0, 1); e = new Date(now.getFullYear() - 1, 11, 31); }
  else if (period === 'CUSTOM') { s = from ? new Date(from) : null; e = to ? new Date(to) : null; }
  else return null;
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
  const [search, setSearch] = useState('');
  const [groupTab, setGroupTab] = useState('ALL');
  const [selected, setSelected] = useState(null);
  const [recent, setRecent] = useState(() => { try { return JSON.parse(window.localStorage.getItem('gs.reports.recent') || '[]'); } catch (e) { return []; } });
  const [entOpen, setEntOpen] = useState(false);
  const entRef = useRef(null);
  useEffect(() => {
    const h = (e) => { if (entRef.current && !entRef.current.contains(e.target)) setEntOpen(false); };
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
  useEffect(() => { if (firstRun.current) { firstRun.current = false; return; } load(datasetKey); }, [reloadToken, datasetKey, load]);
  useEffect(() => { setEntity(null); setSelected(null); setGroupTab('ALL'); }, [datasetKey]);

  const entityOptions = useMemo(() => {
    const types = dataset.entityTypes || {}; const out = [];
    Object.keys(types).forEach(t => {
      const fk = fieldByKey(dataset, types[t]); if (!fk) return;
      const vals = []; rows.forEach(r => { const v = fk.get(r); if (v && vals.indexOf(v) < 0) vals.push(v); });
      vals.sort(); out.push({ type: t, values: vals.slice(0, 40) });
    });
    return out;
  }, [rows, dataset]);

  const defs = useMemo(() => CATALOG.filter(d =>
    d.dataset === datasetKey && (!d.money || canSeeMoney) &&
    ((entity ? (d.scopes || []).indexOf(entity.type) >= 0 : (d.scopes || []).indexOf('ALL') >= 0))
  ), [datasetKey, canSeeMoney, entity]);
  const searchedDefs = useMemo(() => {
    const q = search.trim().toUpperCase(); if (!q) return defs;
    return defs.filter(d => (d.title + ' ' + d.desc).toUpperCase().indexOf(q) >= 0);
  }, [defs, search]);
  const groups = useMemo(() => { const seen = []; searchedDefs.forEach(d => { if (seen.indexOf(d.group) < 0) seen.push(d.group); }); return seen; }, [searchedDefs]);
  useEffect(() => { if (groupTab !== 'ALL' && groups.indexOf(groupTab) < 0) setGroupTab('ALL'); }, [groups, groupTab]);
  const listDefs = groupTab === 'ALL' ? searchedDefs : searchedDefs.filter(d => d.group === groupTab);

  const rowsForDef = useCallback((def) => {
    let list = rows.slice();
    if (def.entityFilter && entity) {
      const fk = fieldByKey(dataset, def.entityFilter);
      if (fk) list = list.filter(r => String(fk.get(r) || '').toLowerCase() === String(entity.value).toLowerCase());
    }
    if (def.filter) {
      const fk = fieldByKey(dataset, def.filter.field);
      if (fk) list = applyFilters(list, dataset, [{ field: fk.key, op: def.filter.op, value: def.filter.value }], 'AND', '');
    }
    if (def.periodAware && period !== 'ALL TIME') {
      const rng = periodRange(period, from, to);
      if (rng) {
        const fk = fieldByKey(dataset, dataset.dateField);
        if (fk) list = list.filter(r => { const v = fk.get(r); if (!v) return false; const d = String(v).slice(0, 10); return d >= rng[0] && d <= rng[1]; });
      }
    }
    return list;
  }, [rows, dataset, entity, period, from, to]);

  const pickEntity = (type, value) => { setEntity({ type, value }); setEntOpen(false); };
  const chooseDef = (def) => {
    setSelected(def.id);
    const next = [def.id, ...recent.filter(x => x !== def.id)].slice(0, 6);
    setRecent(next);
    try { window.localStorage.setItem('gs.reports.recent', JSON.stringify(next)); } catch (e) {}
  };
  const selectedDef = CATALOG.find(d => d.id === selected) || null;
  const selectedRows = selectedDef ? rowsForDef(selectedDef) : [];
  const recentDefs = recent.map(id => CATALOG.find(d => d.id === id)).filter(Boolean);

  return (
    <div className={styles.studio}>
      <div className={styles.scopePanel}>
        <div className={styles.scopeHead}><span className={styles.scopeTitle}>SCOPE</span>
          <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}><FiRefreshCw size={11} aria-hidden="true" /> RELOAD</button>
        </div>
        <div className={styles.scopeBody}>
          <div className={styles.tileRow}>
            {available.map(ds => (
              <button key={ds.key} className={ds.key === datasetKey ? styles.tileActive : styles.tile} onClick={() => setDatasetKey(ds.key)}>
                {ds.label}{ds.key === datasetKey && <span className={styles.tileCount}>{loading ? '...' : rows.length}</span>}
              </button>
            ))}
          </div>
          <p className={styles.hint}>{dataset?.blurb}</p>
          {!canSeeMoney && (
            <p className={styles.hint}><FiLock size={12} aria-hidden="true" /> Financial datasets, money columns and company reports are hidden on your role.</p>
          )}
          {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden="true" /> {error}</div>}
          <div className={styles.scopeRow}>
            <div className={styles.entWrap} ref={entRef}>
              <span className={styles.miniLabel}>Who / what</span>
              <div className={styles.entBox}>
                <button className={styles.entBtn} onClick={() => setEntOpen(o => !o)} aria-expanded={entOpen}>
                  <span className={entity ? styles.entVal : styles.entPh}>{entity ? entity.type + ': ' + entity.value : 'Whole company'}</span>
                  <FiChevronDown className={entOpen ? styles.entOpen : ''} aria-hidden="true" />
                </button>
                {entOpen && (
                  <div className={styles.entList}>
                    <button className={styles.entOpt} onClick={() => { setEntity(null); setEntOpen(false); }}>WHOLE COMPANY</button>
                    {entityOptions.map(t => t.values.map(v => (
                      <button key={t.type + v} className={styles.entOpt} onClick={() => pickEntity(t.type, v)}>{t.type + ': ' + v}</button>
                    )))}
                  </div>
                )}
              </div>
              {entity && <button className={styles.chip} onClick={() => setEntity(null)}><FiX size={11} aria-hidden="true" /> CLEAR</button>}
            </div>
            <div className={styles.perWrap}>
              <span className={styles.miniLabel}>When</span>
              <div className={styles.perRow}>
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
          </div>
        </div>
      </div>

      <div className={styles.catPanel}>
        <div className={styles.catHead}>
          <span className={styles.scopeTitle}>CATALOGUE</span>
          <span className={styles.catCount}>{searchedDefs.length} REPORTS</span>
          <div className={styles.barSearch}>
            <FiSearch className={styles.searchIcon} aria-hidden="true" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search reports..." aria-label="Search reports" />
            {search && <button className={styles.searchClear} onClick={() => setSearch('')} aria-label="Clear search"><FiX size={13} aria-hidden="true" /></button>}
          </div>
        </div>
        <div className={styles.tabRow}>
          <button className={groupTab === 'ALL' ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab('ALL')}>ALL<span className={styles.gcnt}>{searchedDefs.length}</span></button>
          {groups.map(g => (
            <button key={g} className={groupTab === g ? styles.gtabOn : styles.gtab} onClick={() => setGroupTab(g)}>
              {g}<span className={styles.gcnt}>{searchedDefs.filter(d => d.group === g).length}</span>
            </button>
          ))}
        </div>
        {recentDefs.length > 0 && (
          <div className={styles.recentBar}>
            <span className={styles.recentLabel}>RECENTLY USED</span>
            {recentDefs.map(d => (
              <button key={d.id} className={styles.rchip} onClick={() => chooseDef(d)}>{d.title}</button>
            ))}
          </div>
        )}
        <div className={styles.defList}>
          {listDefs.length === 0 && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}
          {listDefs.map(d => {
            const n = rowsForDef(d).length;
            return (
              <button key={d.id} className={selected === d.id ? styles.defRowOn : styles.defRow} onClick={() => chooseDef(d)}>
                <span className={styles.defTitle}>{d.title}<span className={styles.defTags}>{d.chart !== 'NONE' ? d.chart : 'TABLE'} &middot; {n} ROWS</span></span>
                <span className={styles.defDesc}>{d.desc}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className={styles.viewerPanel}>
        <div className={styles.catHead}><span className={styles.scopeTitle}>VIEWER</span>
          {selectedDef && <span className={styles.catCount}>{selectedRows.length} ROWS</span>}
        </div>
        {selectedDef ? (
          <div className={styles.viewerBody}>
            <p className={styles.hint}><FiEye size={12} aria-hidden="true" /> {selectedDef.title}: {selectedDef.desc} Chart + table + CSV land in stage 2.</p>
          </div>
        ) : (
          <div className={styles.viewerBody}><p className={styles.hint}>Pick a report above to preview it here.</p></div>
        )}
      </div>
    </div>
  );
};
export default ReportStudio;
