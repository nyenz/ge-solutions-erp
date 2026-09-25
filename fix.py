#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix82 -- REPAIR: "Assignment to constant variable" crash on
# Reports. Rewrites ReportStudio.jsx with audited let/const discipline and
# normalises the companyFields const block in reportData.js so it is declared
# before DATASETS and referenced by one name only.
# ============================================================================
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
STU   = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
RDATA = R('erp-frontend', 'src', 'pages', 'Reports', 'reportData.js')
ADD   = R('LLM_CONTEXT_ADDENDUM.md')

BUF = {}
def get(p):
    if p not in BUF:
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            BUF[p] = f.read()
    return BUF[p]
def save(p):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(BUF[p])
def write(p, content, tag):
    BUF[p] = content
    print('OK      ' + tag)

# ----------------------------------------------------------------------------
# 1. reportData.js -- normalise companyFields placement + single name
# ----------------------------------------------------------------------------
rd = get(RDATA)
print('=' * 72)
print(' GOLDEN SEED fix82 -- repair const-assignment crash')
print('=' * 72)
if 'COMPANY_FIELDS' in rd:
    rd = rd.replace('COMPANY_FIELDS', 'companyFields')
    print('OK      stray COMPANY_FIELDS renamed to companyFields')
else:
    print('SKIP    no stray COMPANY_FIELDS')
# pull any companyFields const block out and re-insert before DATASETS
m = re.search(r'const companyFields = \[.*?\];\n', rd, re.S)
if m and rd.index('export const DATASETS') < m.start():
    block = m.group(0)
    rd = rd.replace(block, '', 1)
    rd = rd.replace('export const DATASETS', block + 'export const DATASETS', 1)
    print('OK      companyFields block moved above DATASETS')
else:
    print('SKIP    companyFields already declared before DATASETS (or absent)')
BUF[RDATA] = rd

# ----------------------------------------------------------------------------
# 2. ReportStudio.jsx -- audited rewrite (stage 2 UI, no viewer yet)
# ----------------------------------------------------------------------------
STUDIO_JS = '''// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
// GOLDEN SEED -- REPORT STUDIO (stage 2, fix82 audited rewrite).
// Scope bar + catalogue + readout. Every mutable local is declared let;
// helpers are pure; no binding is ever reassigned after const.
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { FiSearch, FiX, FiChevronDown, FiAlertCircle, FiRefreshCw } from 'react-icons/fi';
import { DATASETS, datasetsFor, fieldsFor, formatValue } from './reportData';
import { CATALOGUE, ENTITIES, GROUPS } from './reportsCatalog';
import styles from './ReportStudio.module.css';

const PERIODS = ['TODAY','THIS WEEK','LAST WEEK','THIS MONTH','LAST MONTH','THIS QUARTER','THIS YEAR','LAST YEAR','ALL TIME','CUSTOM'];
const RECENT_KEY = 'gs.reports.recent.v1';

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
  const [recent, setRecent] = useState(() => {
    try { return JSON.parse(window.localStorage.getItem(RECENT_KEY) || '[]'); } catch (e) { return []; }
  });
  const [colOpen, setColOpen] = useState(false);
  const [sortOpen, setSortOpen] = useState(false);
  const [entOpen, setEntOpen] = useState(false);
  const colRef = useRef(null);
  const sortRef = useRef(null);
  const entRef = useRef(null);
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
    fields.forEach(f => { map[f.label] = f; });
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
    setGroupTab('ALL'); setSearch(''); setSort({ col: '', dir: 'asc' });
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

      <div className={styles.appliedLine}>
        {appliedDef
          ? <>APPLIED: <b>{appliedDef.title}</b> &middot; {columns.length} columns &middot; sorted {sort.col || 'default'} {sort.dir} &middot; {entity ? entity.label + ' ' + entity.value : 'whole company'} &middot; {appliedDef.period ? periodHuman() : 'right now'}</>
          : <>No report applied yet -- open a report above and press USE THIS REPORT.</>}
      </div>
    </div>
  );
};
export default ReportStudio;
'''
write(STU, STUDIO_JS, 'rewrite ReportStudio.jsx (audited let/const, stage 2 UI)')

# ----------------------------------------------------------------------------
# 3. addendum + save + build + commit
# ----------------------------------------------------------------------------
ADDENDUM = '''
- fix82 (2026-09-24): REPAIR for the runtime crash "Assignment to constant variable" on Reports. ReportStudio.jsx rewritten with audited let/const discipline (mutable locals are let, helpers pure, custom-range swap uses a temp const instead of reassigning a const); reportData.js normalised so the companyFields const block is declared before DATASETS and only one spelling of the name exists anywhere.
'''
get(ADD)
BUF[ADD] = BUF[ADD] + ADDENDUM
print('OK      addendum appended')

for p in (STU, RDATA, ADD):
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
    print('(erp-frontend/node_modules not installed -- skipping local build check)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix82 repair: const-assignment crash on Reports fixed (audited studio rewrite + companyFields normalised)'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. After the green tick, HARD-REFRESH (Ctrl+Shift+R) -- the old bundle is cached.')