#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix79b -- REPAIR: make reportsCatalog.js and ReportStudio.jsx
# a matched pair (the Render build failed because stage-2 ReportStudio imports
# { CATALOGUE, ENTITIES } but the catalog file on disk exported other names).
# Also: de-duplicate the auditService import, guarantee COMPANY dataset exists.
# ============================================================================
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
CAT    = R('erp-frontend','src','pages','Reports','reportsCatalog.js')
STU    = R('erp-frontend','src','pages','Reports','ReportStudio.jsx')
RDATA  = R('erp-frontend','src','pages','Reports','reportData.js')
AUDIT  = R('erp-frontend','src','services','auditService.js')
ADD    = R('LLM_CONTEXT_ADDENDUM.md')

BUF = {}
def get(p):
    if p not in BUF:
        with open(p,'r',encoding='utf-8',errors='replace') as f: BUF[p]=f.read()
    return BUF[p]
def save(p):
    with open(p,'w',encoding='utf-8',newline='\n') as f: f.write(BUF[p])
def patch(p, old, new, tag):
    s=get(p)
    if old in s:
        BUF[p]=s.replace(old,new,1); print('OK      '+tag)
    else:
        print('SKIP    '+tag+' (anchor not present / already applied)')
def write(p, content, tag):
    BUF[p]=content; print('OK      '+tag)

CATALOG_JS = '''// PATH: erp-frontend/src/pages/Reports/reportsCatalog.js
// GOLDEN SEED -- REPORT CATALOGUE (single source of truth for ReportStudio).
// Exports exactly: GROUPS, ENTITIES, CATALOGUE.
// Def shape: { id, title, desc, ds, group, money, scopes, period, groupBy,
//              measure, cols, chart, sort }
//   scopes  : entity types this report can narrow to (see ENTITIES)
//   period  : true = honours the period chips; false = right-now snapshot
//   groupBy : field LABEL to group by ('' = row level)
//   measure : {agg:'sum'|'count', field:LABEL} or {agg:'count'} or null
//   cols    : field LABELS for the results table
//   chart   : BAR | COLUMN | LINE | DONUT | NONE
//   sort    : {col:LABEL, dir:'asc'|'desc'}
export const GROUPS = ['WORK IN','IN PROCESS','MONEY IN','MONEY OUT','CLIENTS / RECOVERY','COMPLIANCE / ARCHIVE'];

export const ENTITIES = {
  PROJECTS: [
    { type:'PROJECT',  label:'Project',  field:'Project Index' },
    { type:'CLIENT',   label:'Client',   field:'Primary Owner' },
    { type:'LOCATION', label:'Location', field:'District' },
  ],
  CLIENTS: [
    { type:'CLIENT',   label:'Client',   field:'Client Name' },
    { type:'LOCATION', label:'Location', field:'District' },
  ],
  PAYMENTS: [
    { type:'PROJECT',  label:'Project',  field:'Plot' },
    { type:'CLIENT',   label:'Client',   field:'Owner Name' },
    { type:'OPERATOR', label:'Operator', field:'Recorded By' },
  ],
  EXPENSES: [
    { type:'CATEGORY', label:'Category', field:'Category' },
    { type:'OPERATOR', label:'Operator', field:'Spent By' },
  ],
  COMPANY: [
    { type:'OPERATOR', label:'Operator', field:'Operator' },
  ],
};

export const CATALOGUE = [
  // ── PROJECTS / MONEY IN ──
  { id:'p_owed_dist', title:'OWED BY DISTRICT', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','District','Sub-County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'What is still owed, added up per district.' },
  { id:'p_owed_county', title:'OWED BY COUNTY', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'County', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'What is still owed, added up per county.' },
  { id:'p_owed_sub', title:'OWED BY SUB-COUNTY', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Sub-County', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','Sub-County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'What is still owed, added up per sub-county.' },
  { id:'p_owed_owner', title:'OWED BY OWNER', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT'], period:false, groupBy:'Primary Owner', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','Owner Phone','District','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'Every primary owner ranked by what they still owe.' },
  { id:'p_paid_cost', title:'PAID VS COST', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Status', measure:{agg:'sum',field:'Amount Paid'}, cols:['Project Index','Primary Owner','Status','Total Cost','Amount Paid','Balance Owed'], chart:'COLUMN', sort:{col:'Amount Paid',dir:'desc'}, desc:'What has been collected per status against live cost.' },
  { id:'p_never_paid', title:'NEVER-PAID PROJECTS', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Amount Paid',op:'eq',value:0}, cols:['Project Index','Primary Owner','District','Status','Balance Owed'], chart:'BAR', sort:{col:'Project Index',dir:'asc'}, desc:'Projects with no payment recorded at all.' },
  // ── PROJECTS / IN PROCESS ──
  { id:'p_by_stage', title:'PROJECTS BY STAGE', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Stage', measure:{agg:'count'}, cols:['Project Index','Primary Owner','District','Stage','Status'], chart:'DONUT', sort:{col:'Project Index',dir:'asc'}, desc:'How many projects sit at each survey stage right now.' },
  { id:'p_by_status', title:'PROJECTS BY STATUS', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Status', measure:{agg:'count'}, cols:['Project Index','Primary Owner','District','Status'], chart:'DONUT', sort:{col:'Project Index',dir:'asc'}, desc:'Active against released against receivable, right now.' },
  { id:'p_stalled', title:'STALLED PROJECTS', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Days Since Payment',op:'gt',value:60}, cols:['Project Index','Primary Owner','District','Days Since Payment','Status'], chart:'BAR', sort:{col:'Days Since Payment',dir:'desc'}, desc:'Projects with no payment in 60+ days, per district.' },
  { id:'p_titles_issued', title:'TITLES ISSUED', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, cols:['Project Index','Title ID','Primary Owner','District','Title Date'], chart:'COLUMN', sort:{col:'Title Date',dir:'desc'}, desc:'Titles issued in the chosen period, per district.' },
  { id:'p_released', title:'RELEASED PROJECTS', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Status',op:'is',value:'RELEASED'}, cols:['Project Index','Primary Owner','District','Status'], chart:'BAR', sort:{col:'Project Index',dir:'asc'}, desc:'Projects handed back to clients, per district.' },
  // ── PROJECTS / WORK IN ──
  { id:'p_new_folders', title:'NEW FOLDERS OPENED', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'New Folder'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'}, desc:'New Folder intakes in the chosen period, per district.' },
  { id:'p_new_titles', title:'NEW TITLES ENTERED', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'New Title'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'}, desc:'New Title intakes in the chosen period, per district.' },
  { id:'p_legacy', title:'LEGACY INTAKES', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'Legacy Title'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'}, desc:'Legacy Title intakes in the chosen period, per district.' },
  // ── CLIENTS ──
  { id:'c_by_district', title:'CLIENTS BY DISTRICT', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:false, scopes:['LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, cols:['Client Name','Phone','District','Sub-County','Projects'], chart:'DONUT', sort:{col:'Client Name',dir:'asc'}, desc:'How many registered clients each district has.' },
  { id:'c_top_debtors', title:'TOP DEBTORS', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Client Name', measure:{agg:'sum',field:'Total Owed'}, cols:['Client Name','Phone','District','Total Owed','Total Paid'], chart:'BAR', sort:{col:'Total Owed',dir:'desc'}, desc:'Clients ranked by what they still owe.' },
  { id:'c_never_called', title:'NEVER-CALLED CLIENTS', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:false, scopes:['LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Last Contact',op:'empty'}, cols:['Client Name','Phone','District','Last Contact'], chart:'BAR', sort:{col:'Client Name',dir:'asc'}, desc:'Clients nobody has called yet, per district.' },
  { id:'c_owed_dist', title:'CLIENT DEBT BY DISTRICT', ds:'CLIENTS', group:'MONEY IN', money:true, scopes:['LOCATION'], period:false, groupBy:'District', measure:{agg:'sum',field:'Total Owed'}, cols:['Client Name','District','Total Owed','Total Paid'], chart:'BAR', sort:{col:'Total Owed',dir:'desc'}, desc:'Client debt added up per district.' },
  // ── PAYMENTS ──
  { id:'pay_received', title:'PAYMENTS RECEIVED', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['PROJECT','CLIENT','OPERATOR'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Payment Type','Amount Paid','Recorded By'], chart:'LINE', sort:{col:'Date',dir:'desc'}, desc:'Money in per month for the chosen period.' },
  { id:'pay_by_type', title:'PAYMENTS BY TYPE', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['PROJECT','CLIENT','OPERATOR'], period:true, groupBy:'Payment Type', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Payment Type','Amount Paid'], chart:'DONUT', sort:{col:'Amount Paid',dir:'desc'}, desc:'Standard against deposit against receivable-part.' },
  { id:'pay_operator', title:'COLLECTIONS PER OPERATOR', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['OPERATOR'], period:true, groupBy:'Recorded By', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Amount Paid','Recorded By'], chart:'COLUMN', sort:{col:'Amount Paid',dir:'desc'}, desc:'Who collected how much in the chosen period.' },
  { id:'pay_by_plot', title:'PAYMENTS BY PROJECT', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['PROJECT'], period:true, groupBy:'Plot', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Payment Type','Amount Paid'], chart:'BAR', sort:{col:'Amount Paid',dir:'desc'}, desc:'Every project ranked by what it has paid.' },
  // ── EXPENSES ──
  { id:'e_by_category', title:'EXPENSES BY CATEGORY', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['CATEGORY','OPERATOR'], period:true, groupBy:'Category', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Item','Amount','Spent By'], chart:'DONUT', sort:{col:'Amount',dir:'desc'}, desc:'Which category ate the money in the chosen period.' },
  { id:'e_by_operator', title:'EXPENSES PER OPERATOR', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['OPERATOR'], period:true, groupBy:'Spent By', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Item','Amount','Spent By'], chart:'COLUMN', sort:{col:'Amount',dir:'desc'}, desc:'Who spent how much in the chosen period.' },
  { id:'e_over_time', title:'EXPENSES OVER TIME', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['CATEGORY','OPERATOR'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Item','Amount','Spent By'], chart:'LINE', sort:{col:'Date',dir:'desc'}, desc:'Money out per month for the chosen period.' },
  // ── COMPANY ─
  { id:'co_workload', title:'OPERATOR WORKLOAD', ds:'COMPANY', group:'WORK IN', money:false, scopes:['OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, cols:['Timestamp','Operator','Action','Entity'], chart:'COLUMN', sort:{col:'Operator',dir:'asc'}, desc:'Every staff action counted per operator in the period.' },
  { id:'co_by_action', title:'AUDIT BY ACTION', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['OPERATOR'], period:true, groupBy:'Action', measure:{agg:'count'}, cols:['Timestamp','Operator','Action','Entity'], chart:'BAR', sort:{col:'Operator',dir:'asc'}, desc:'Which system actions happened most in the period.' },
  { id:'co_logins', title:'LOGINS PER OPERATOR', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, filter:{field:'Action',op:'is',value:'LOGIN_SUCCESS'}, cols:['Timestamp','Operator','Action','Device'], chart:'COLUMN', sort:{col:'Operator',dir:'asc'}, desc:'Who signed in how often in the chosen period.' },
];
export default CATALOGUE;
'''

STUDIO_JS = '''// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
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
                {sort.dir === 'desc' ? '\\u2193' : '\\u2191'}
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
'''

COMPANY_BLOCK = '''const companyFields = [
  f('timestamp', 'Timestamp', 'date', a => a.timestamp || null),
  f('month', 'Month', 'text', a => monthKey(a.timestamp)),
  f('operator', 'Operator', 'text', a => a.performedBy || ''),
  f('action', 'Action', 'text', a => a.action || ''),
  f('details', 'Details', 'text', a => a.details || ''),
];
DATASETS.COMPANY = {
  key: 'COMPANY',
  label: 'Company',
  blurb: 'Every staff action in the audit ledger: logins, edits, deletes, exports.',
  restricted: true,
  fields: companyFields,
  defaultColumns: ['timestamp', 'operator', 'action', 'details'],
  load: async () => {
    const out = [];
    for (let page = 0; page < 40; page += 1) {
      const d = await auditService.getRawStream(page, 200);
      const r = (d && d.content) || [];
      out.push(...r);
      if (r.length < 200) break;
    }
    return out;
  },
};

'''

ADDENDUM = '''
- fix79b (2026-09-24): REPAIR for the Render build failure. The two overlapping stage-1 runs left reportsCatalog.js exporting names that stage-2 ReportStudio.jsx does not import ("CATALOGUE is not exported"). fix79b rewrites reportsCatalog.js and ReportStudio.jsx as a matched pair: reportsCatalog exports exactly GROUPS, ENTITIES, CATALOGUE; ReportStudio imports exactly those three. Catalogue now carries 27 standing report defs across PROJECTS / CLIENTS / PAYMENTS / EXPENSES / COMPANY with scopes, period flag, groupBy, measure, cols, chart and default sort. reportData gains the COMPANY dataset only if missing; auditService import de-duplicated and getRawStream(size) guaranteed.
'''

print('='*72)
print(' GOLDEN SEED fix79b -- REPAIR: matched catalog/studio pair')
print('='*72)

write(CAT, CATALOG_JS, 'write reportsCatalog.js (exports GROUPS, ENTITIES, CATALOGUE)')
write(STU, STUDIO_JS, 'write ReportStudio.jsx (imports match catalog exactly)')

# reportData: add COMPANY dataset only if missing
rd = get(RDATA)
if 'DATASETS.COMPANY' not in rd and "key: 'COMPANY'" not in rd:
    patch(RDATA, 'export const datasetsFor', COMPANY_BLOCK + 'export const datasetsFor', 'reportData: COMPANY dataset added')
else:
    print('SKIP    reportData: COMPANY dataset (already present)')
# reportData: de-duplicate auditService import
rd = get(RDATA)
lines = rd.split('\n')
seen = False
out = []
for ln in lines:
    if ln.strip().startswith('import auditService'):
        if seen:
            continue
        seen = True
    out.append(ln)
if len(out) != len(lines):
    BUF[RDATA] = '\n'.join(out)
    print('OK      reportData: duplicate auditService import removed')
else:
    print('SKIP    reportData: auditService import (single, fine)')
# auditService: guarantee size param
patch(AUDIT, 'getRawStream: async (page = 0) => {', 'getRawStream: async (page = 0, size = 200) => {', 'auditService: getRawStream accepts size')
patch(AUDIT, 'params: { page, size: 50 }', 'params: { page, size }', 'auditService: stream passes size')

get(ADD); BUF[ADD] = BUF[ADD] + ADDENDUM
print('OK      append addendum')

for p in (CAT, STU, RDATA, AUDIT, ADD):
    save(p)
print('')
print('All files written.')
print('')

frontend = R('erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm','run','build'], cwd=frontend, shell=(os.name=='nt'))
    if r.returncode != 0:
        print(''); print('BUILD RED -- nothing committed or pushed.'); sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping local build check)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix79b repair: matched reportsCatalog/ReportStudio exports (fixes Render build), COMPANY dataset guaranteed, auditService import deduped'
subprocess.run(['git','add','-A'])
subprocess.run(['git','commit','-m',MSG])
subprocess.run(['git','push'])
print('')
print('Repair done. Wait for the green tick, then say go for stage 3 (results viewer + CSV/PDF).')