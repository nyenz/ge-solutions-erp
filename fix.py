#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GOLDEN SEED fix79a (STAGE 1): scope bar + catalogue skeleton.
# Stage 2 = viewer (chart+table+CSV). Stage 3 = exports/PDF/advanced.
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
STU    = R('erp-frontend','src','pages','Reports','ReportStudio.jsx')
STUCSS = R('erp-frontend','src','pages','Reports','ReportStudio.module.css')
HUB    = R('erp-frontend','src','pages','Reports','ReportHub.jsx')
RDATA  = R('erp-frontend','src','pages','Reports','reportData.js')
CAT    = R('erp-frontend','src','pages','Reports','reportsCatalog.js')
AUDIT  = R('erp-frontend','src','services','auditService.js')
EA_JS  = R('erp-frontend','src','pages','Reports','ExpenseAnalysis.jsx')
EA_CSS = R('erp-frontend','src','pages','Reports','ExpenseAnalysis.module.css')
ADD    = R('LLM_CONTEXT_ADDENDUM.md')

BUF = {}
def get(p):
    if p not in BUF:
        with open(p,'r',encoding='utf-8',errors='replace') as f: BUF[p]=f.read()
    return BUF[p]
def save(p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p,'w',encoding='utf-8',newline='\n') as f: f.write(BUF[p])
def patch(p, old, new, tag):
    s=get(p)
    if old in s: BUF[p]=s.replace(old,new,1); print('OK      '+tag)
    else: print('MISSING '+tag)
def rpatch(p, pat, new, tag):
    s=get(p); out,n=re.subn(pat,new,s,count=1)
    if n: BUF[p]=out; print('OK      '+tag)
    else: print('MISSING '+tag)
def write(p, content, tag):
    BUF[p]=content; print('OK      '+tag)

# ---------------------------------------------------------------- catalog data
CATALOG_JS = '''// PATH: erp-frontend/src/pages/Reports/reportsCatalog.js
// GOLDEN SEED -- REPORT CATALOG (stage 1).
// One line per report. groupBy/measure use field LABELS from reportData.js.
// scopes: which entity types this report makes sense for ('ALL' = no entity).
// entityFilter: field LABEL to pin to the picked entity value.
// filter: an extra fixed condition {field label, op, value}.
// periodAware: true = the scope-bar period window applies.
export const CATALOG = [
  // PROJECTS / MONEY IN
  {id:'P_OWED_DIST',title:'OWED BY DISTRICT',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['ALL','LOCATION','CLIENT'],periodAware:false,groupBy:'District',measure:{agg:'sum',field:'Balance Owed'},chart:'BAR',cols:['Project Index','Primary Owner','District','Sub-County','Village','Status','Total Cost','Amount Paid','Balance Owed'],desc:'What is still owed per project, added up per district.'},
  {id:'P_OWED_COUNTY',title:'OWED BY COUNTY',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'County',measure:{agg:'sum',field:'Balance Owed'},chart:'BAR',cols:['Project Index','Primary Owner','County','Status','Total Cost','Amount Paid','Balance Owed'],desc:'What is still owed per project, added up per county.'},
  {id:'P_OWED_SUB',title:'OWED BY SUB-COUNTY',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'Sub-County',measure:{agg:'sum',field:'Balance Owed'},chart:'BAR',cols:['Project Index','Primary Owner','Sub-County','Status','Total Cost','Amount Paid','Balance Owed'],desc:'What is still owed per project, added up per sub-county.'},
  {id:'P_OWED_OWNER',title:'OWED BY OWNER',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['ALL','CLIENT'],periodAware:false,groupBy:'Primary Owner',measure:{agg:'sum',field:'Balance Owed'},chart:'BAR',cols:['Project Index','Primary Owner','Owner Phone','District','Status','Total Cost','Amount Paid','Balance Owed'],desc:'Every primary owner ranked by what they still owe.'},
  {id:'P_OWED_STATUS',title:'OWED BY STATUS',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['ALL'],periodAware:false,groupBy:'Status',measure:{agg:'sum',field:'Balance Owed'},chart:'BAR',cols:['Project Index','Primary Owner','Status','Total Cost','Amount Paid','Balance Owed'],desc:'What is still owed, split by active / released / receivable.'},
  {id:'P_PAID_VS_COST',title:'PAID VS COST',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['ALL'],periodAware:false,groupBy:'Status',measure:{agg:'sum',field:'Amount Paid'},chart:'BAR',cols:['Project Index','Primary Owner','Status','Total Cost','Amount Paid','Balance Owed'],desc:'What has been collected per status, against live cost.'},
  {id:'P_STORAGE_DIST',title:'STORAGE FEES BY DISTRICT',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'District',measure:{agg:'sum',field:'Storage Fees'},chart:'BAR',cols:['Project Index','Primary Owner','District','Status','Storage Fees','Balance Owed'],desc:'Accumulated storage fees per district.'},
  // PROJECTS / WORK IN
  {id:'P_NEW_ENTRY',title:'NEW PROJECTS',dataset:'PROJECTS',group:'WORK IN',money:false,scopes:['ALL'],periodAware:true,groupBy:'Entry Mode',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','District','Entry Mode','Status'],desc:'Projects that came in during the window, by entry mode.'},
  {id:'P_INTAKE_DIST',title:'INTAKE BY DISTRICT',dataset:'PROJECTS',group:'WORK IN',money:false,scopes:['ALL','LOCATION'],periodAware:true,groupBy:'District',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','District','Status'],desc:'Projects that came in during the window, per district.'},
  {id:'P_INTAKE_MONTH',title:'INTAKE BY MONTH',dataset:'PROJECTS',group:'WORK IN',money:false,scopes:['ALL'],periodAware:false,groupBy:'Start Month',measure:{agg:'count'},chart:'LINE',cols:['Project Index','Primary Owner','District','Project Start'],desc:'Intake trend month by month, all time.'},
  // PROJECTS / IN PROCESS
  {id:'P_BY_STAGE',title:'PROJECTS BY STAGE',dataset:'PROJECTS',group:'IN PROCESS',money:false,scopes:['ALL','LOCATION','CLIENT'],periodAware:false,groupBy:'Stage Index',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','District','Status'],desc:'How many projects sit at each of the five survey stages.'},
  {id:'P_BY_STATUS',title:'PROJECTS BY STATUS',dataset:'PROJECTS',group:'IN PROCESS',money:false,scopes:['ALL','LOCATION','CLIENT'],periodAware:false,groupBy:'Status',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','District','Status'],desc:'Active vs released vs receivable counts.'},
  {id:'P_BY_TENURE',title:'PROJECTS BY TENURE',dataset:'PROJECTS',group:'IN PROCESS',money:false,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'Tenure',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','Tenure','District'],desc:'Freehold / mailo / leasehold / customary split.'},
  // PROJECTS / COMPLIANCE
  {id:'P_LEGAL_DIST',title:'LEGAL READINESS BY DISTRICT',dataset:'PROJECTS',group:'COMPLIANCE / ARCHIVE',money:false,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'District',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','Owner NIN','Owner Address','District'],desc:'Projects per district with the NIN and address columns attached for legal checks.'},
  // PROJECTS / entity-scoped
  {id:'P_PROJ_SNAPSHOT',title:'PROJECT SNAPSHOT',dataset:'PROJECTS',group:'IN PROCESS',money:true,scopes:['PROJECT'],entityFilter:'Project Index',periodAware:false,groupBy:null,measure:null,chart:'NONE',cols:['Project Index','Plot Number','Title ID','Tenure','District','Sub-County','Village','Primary Owner','Owner Phone','Owner NIN','Status','Entry Mode','Total Cost','Amount Paid','Balance Owed','Storage Fees'],desc:'Everything on one project: status, stage, owners, title, money.'},
  {id:'P_PROJ_STAGES',title:'PROJECT STAGE HISTORY',dataset:'PROJECTS',group:'IN PROCESS',money:false,scopes:['PROJECT'],entityFilter:'Project Index',periodAware:false,groupBy:'Stage Index',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','Status'],desc:'The five survey stages for one project, done or pending.'},
  {id:'P_CLIENT_PROJECTS',title:'ONE CLIENT PROJECTS',dataset:'PROJECTS',group:'CLIENTS / RECOVERY',money:true,scopes:['CLIENT'],entityFilter:'Primary Owner',periodAware:false,groupBy:'Status',measure:{agg:'sum',field:'Balance Owed'},chart:'BAR',cols:['Project Index','Primary Owner','District','Status','Total Cost','Amount Paid','Balance Owed'],desc:'One client\\'s projects grouped by status with what they owe.'},
  {id:'P_LOC_SUMMARY',title:'DISTRICT SUMMARY',dataset:'PROJECTS',group:'IN PROCESS',money:false,scopes:['LOCATION'],entityFilter:'District',periodAware:false,groupBy:'Status',measure:{agg:'count'},chart:'BAR',cols:['Project Index','Primary Owner','District','Status'],desc:'One district\\'s projects grouped by status.'},
  {id:'P_LOC_OWED',title:'DISTRICT OWED',dataset:'PROJECTS',group:'MONEY IN',money:true,scopes:['LOCATION'],entityFilter:'District',periodAware:false,groupBy:'District',measure:{agg:'sum',field:'Balance Owed'},chart:'BAR',cols:['Project Index','Primary Owner','District','Status','Balance Owed'],desc:'What one district still owes.'},
  // CLIENTS
  {id:'C_BY_DIST',title:'CLIENTS BY DISTRICT',dataset:'CLIENTS',group:'CLIENTS / RECOVERY',money:false,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'District',measure:{agg:'count'},chart:'BAR',cols:['Client Name','Phone','District','Sub-County'],desc:'Registered clients per district.'},
  {id:'C_BY_COUNTY',title:'CLIENTS BY COUNTY',dataset:'CLIENTS',group:'CLIENTS / RECOVERY',money:false,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'County',measure:{agg:'count'},chart:'BAR',cols:['Client Name','Phone','County'],desc:'Registered clients per county.'},
  {id:'C_BY_SUB',title:'CLIENTS BY SUB-COUNTY',dataset:'CLIENTS',group:'CLIENTS / RECOVERY',money:false,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'Sub-County',measure:{agg:'count'},chart:'BAR',cols:['Client Name','Phone','Sub-County'],desc:'Registered clients per sub-county.'},
  {id:'C_TOP_DEBTORS',title:'TOP DEBTORS',dataset:'CLIENTS',group:'MONEY IN',money:true,scopes:['ALL','LOCATION'],periodAware:false,groupBy:'Client Name',measure:{agg:'sum',field:'Total Owed'},chart:'BAR',cols:['Client Name','Phone','District','Total Owed','Total Paid'],desc:'Clients ranked by what they owe.'},
  {id:'C_RECENCY',title:'PAYMENT RECENCY',dataset:'CLIENTS',group:'MONEY IN',money:true,scopes:['ALL'],periodAware:false,groupBy:'Days Since Payment',measure:{agg:'count'},chart:'BAR',cols:['Client Name','Phone','Days Since Payment','Total Owed'],desc:'Clients bucketed by how long since they last paid.'},
  {id:'C_CLIENT_SUM',title:'CLIENT SUMMARY',dataset:'CLIENTS',group:'CLIENTS / RECOVERY',money:true,scopes:['CLIENT'],entityFilter:'Client Name',periodAware:false,groupBy:null,measure:null,chart:'NONE',cols:['Client Name','NIN','Phone','Email','District','Sub-County','Projects','Total Owed','Total Paid','Storage Fees'],desc:'One client: identity, projects, owed, paid, recency.'},
  // PAYMENTS
  {id:'PAY_RECEIVED',title:'PAYMENTS RECEIVED',dataset:'PAYMENTS',group:'MONEY IN',money:true,scopes:['ALL','CLIENT','OPERATOR'],periodAware:true,groupBy:'Month',measure:{agg:'sum',field:'Amount Paid'},chart:'LINE',cols:['Date','Project Index','Owner Name','Payment Type','Amount Paid','Recorded By'],desc:'Money in month by month for the window.'},
  {id:'PAY_BY_TYPE',title:'PAYMENTS BY TYPE',dataset:'PAYMENTS',group:'MONEY IN',money:true,scopes:['ALL','CLIENT'],periodAware:true,groupBy:'Payment Type',measure:{agg:'sum',field:'Amount Paid'},chart:'BAR',cols:['Date','Project Index','Owner Name','Payment Type','Amount Paid'],desc:'Standard vs deposit vs receivable-part totals.'},
  {id:'PAY_BY_OPER',title:'COLLECTIONS PER OPERATOR',dataset:'PAYMENTS',group:'MONEY IN',money:true,scopes:['ALL','OPERATOR'],periodAware:true,groupBy:'Recorded By',measure:{agg:'sum',field:'Amount Paid'},chart:'BAR',cols:['Date','Project Index','Owner Name','Amount Paid','Recorded By'],desc:'Who collected how much in the window.'},
  {id:'PAY_BY_PROJECT',title:'PAYMENTS BY PROJECT',dataset:'PAYMENTS',group:'MONEY IN',money:true,scopes:['ALL','CLIENT'],periodAware:true,groupBy:'Project Index',measure:{agg:'sum',field:'Amount Paid'},chart:'BAR',cols:['Date','Project Index','Owner Name','Payment Type','Amount Paid'],desc:'What each project paid in the window.'},
  {id:'PAY_CLIENT',title:'ONE CLIENT PAYMENTS',dataset:'PAYMENTS',group:'MONEY IN',money:true,scopes:['CLIENT'],entityFilter:'Owner Name',periodAware:true,groupBy:'Month',measure:{agg:'sum',field:'Amount Paid'},chart:'LINE',cols:['Date','Project Index','Owner Name','Payment Type','Amount Paid'],desc:'One client\\'s payments month by month.'},
  {id:'PAY_OPER',title:'ONE OPERATOR COLLECTIONS',dataset:'PAYMENTS',group:'MONEY IN',money:true,scopes:['OPERATOR'],entityFilter:'Recorded By',periodAware:true,groupBy:'Month',measure:{agg:'sum',field:'Amount Paid'},chart:'LINE',cols:['Date','Project Index','Owner Name','Amount Paid','Recorded By'],desc:'One operator\\'s collections month by month.'},
  // EXPENSES
  {id:'EXP_BY_CAT',title:'SPEND BY CATEGORY',dataset:'EXPENSES',group:'MONEY OUT',money:true,scopes:['ALL','CATEGORY'],periodAware:true,groupBy:'Category',measure:{agg:'sum',field:'Amount'},chart:'BAR',cols:['Date','Category','Item','Amount','Spent By'],desc:'Company spend per category in the window.'},
  {id:'EXP_BY_OPER',title:'SPEND BY OPERATOR',dataset:'EXPENSES',group:'MONEY OUT',money:true,scopes:['ALL','OPERATOR'],periodAware:true,groupBy:'Spent By',measure:{agg:'sum',field:'Amount'},chart:'BAR',cols:['Date','Category','Item','Amount','Spent By'],desc:'Who spent how much in the window.'},
  {id:'EXP_BY_MONTH',title:'SPEND BY MONTH',dataset:'EXPENSES',group:'MONEY OUT',money:true,scopes:['ALL'],periodAware:false,groupBy:'Month',measure:{agg:'sum',field:'Amount'},chart:'LINE',cols:['Date','Category','Item','Amount','Spent By'],desc:'Spend trend month by month, all time.'},
  // COMPANY (admin / director / root only)
  {id:'CO_OPER_WORK',title:'OPERATOR WORKLOAD',dataset:'COMPANY',group:'WORK IN',money:false,scopes:['ALL','OPERATOR'],periodAware:true,groupBy:'Operator',measure:{agg:'count'},chart:'BAR',cols:['Timestamp','Operator','Action','Details'],desc:'Actions per staff member in the window.'},
  {id:'CO_ACTIONS',title:'ACTIONS BY TYPE',dataset:'COMPANY',group:'COMPLIANCE / ARCHIVE',money:false,scopes:['ALL'],periodAware:true,groupBy:'Action',measure:{agg:'count'},chart:'BAR',cols:['Timestamp','Operator','Action','Details'],desc:'Every action type counted in the window.'},
  {id:'CO_LOGINS',title:'LOGIN ACTIVITY',dataset:'COMPANY',group:'COMPLIANCE / ARCHIVE',money:false,scopes:['ALL','OPERATOR'],periodAware:true,groupBy:'Operator',measure:{agg:'count'},filter:{field:'Action',op:'startsWith',value:'LOGIN'},chart:'BAR',cols:['Timestamp','Operator','Action','Details'],desc:'Sign-ins per staff member in the window.'},
  {id:'CO_DELETES',title:'DELETIONS & RESTORES',dataset:'COMPANY',group:'COMPLIANCE / ARCHIVE',money:false,scopes:['ALL','OPERATOR'],periodAware:true,groupBy:'Operator',measure:{agg:'count'},filter:{field:'Action',op:'contains',value:'RECORD_D'},chart:'BAR',cols:['Timestamp','Operator','Action','Details'],desc:'Deleted and restored records per staff member.'},
  {id:'CO_STORAGE',title:'STORAGE & OVERRIDES',dataset:'COMPANY',group:'MONEY IN',money:true,scopes:['ALL','OPERATOR'],periodAware:true,groupBy:'Operator',measure:{agg:'count'},filter:{field:'Action',op:'contains',value:'STORAGE'},chart:'BAR',cols:['Timestamp','Operator','Action','Details'],desc:'Storage fee changes and overrides per staff member.'},
  {id:'CO_STAGES',title:'STAGE MOVES',dataset:'COMPANY',group:'IN PROCESS',money:false,scopes:['ALL','OPERATOR'],periodAware:true,groupBy:'Operator',measure:{agg:'count'},filter:{field:'Action',op:'contains',value:'STAGE'},chart:'BAR',cols:['Timestamp','Operator','Action','Details'],desc:'Stage changes per staff member in the window.'},
  {id:'CO_OPER_ACT',title:'ONE OPERATOR ACTIVITY',dataset:'COMPANY',group:'WORK IN',money:false,scopes:['OPERATOR'],entityFilter:'Operator',periodAware:true,groupBy:'Action',measure:{agg:'count'},chart:'BAR',cols:['Timestamp','Operator','Action','Details'],desc:'One operator\\'s actions by type.'},
];
export default CATALOG;
'''

# ---------------------------------------------------------------- studio (stage 1)
STUDIO_JS = '''// PATH: erp-frontend/src/pages/Reports/ReportStudio.jsx
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
'''

# ---------------------------------------------------------------- hub (stage 1)
HUB_JS = '''// PATH: erp-frontend/src/pages/Reports/ReportHub.jsx
// GOLDEN SEED -- REPORTS (stage 1). Tabs and the 12 server pillars are gone;
// the studio is the page. Viewer lands in stage 2, PDF/advanced in stage 3.
import React, { useState } from 'react';
import { FiRefreshCw } from 'react-icons/fi';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import { useAuth } from '../../hooks/useAuth';
import ReportStudio from './ReportStudio';
import styles from './ReportHub.module.css';

const ReportHub = () => {
  const { user } = useAuth();
  const canSeeMoney = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';
  const [reloadToken, setReloadToken] = useState(0);
  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Reports</h1>
          <p className={styles.subtitle}>Pick a scope, pick a report, take it home</p>
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

# ---------------------------------------------------------------- css append
STU_CSS = '''
/* fix79a -- STAGE 1: scope bar + catalogue. Appended: cascade wins. */
.scopePanel, .catPanel, .viewerPanel {
  background: linear-gradient(135deg,#4a6a6c 0%,#3a5a5c 50%,#2f4c4e 100%);
  border: 1.5px solid rgba(238,140,58,0.2); border-radius: 10px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.25); overflow: visible;
  margin-bottom: clamp(10px,1.4vw,16px);
}
.scopeHead, .catHead {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  background: #162a2c; border-bottom: 1.5px solid var(--orange);
  border-radius: 9px 9px 0 0; padding: clamp(8px,1.1vw,12px) clamp(10px,1.4vw,16px);
}
.scopeTitle { font-family: 'Cinzel', serif; color: var(--orange); font-size: clamp(10px,1.3vw,13px); font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
.catCount { font-family: 'Space Mono', monospace; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1px; color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14); border-radius: 20px; padding: 4px 12px; }
.scopeBody { padding: clamp(10px,1.4vw,16px) clamp(10px,1.4vw,16px); display: flex; flex-direction: column; gap: clamp(8px,1.1vw,12px); }
.scopeRow { display: flex; flex-wrap: wrap; gap: clamp(10px,1.6vw,20px); align-items: flex-start; }
.entWrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.entBox { position: relative; }
.entBtn { display: flex; align-items: center; justify-content: space-between; gap: 10px; height: 36px; min-width: clamp(180px,22vw,280px); padding: 0 12px; border-radius: 6px; border: 1.5px solid var(--paper-edge); background: #fff; cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(11px,1.05vw,12.5px); font-weight: 700; }
.entBtn:hover { border-color: var(--orange); }
.entVal { color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.entPh { color: rgba(26,46,48,0.42); font-weight: 600; }
.entBtn svg { color: var(--orange); flex-shrink: 0; transition: transform 0.2s; }
.entOpen { transform: rotate(180deg); }
.entList { position: absolute; top: calc(100% + 4px); left: 0; z-index: 500; width: max-content; min-width: 100%; max-width: 340px; max-height: 264px; overflow-y: auto; background: #fff; border: 2px solid var(--orange); border-radius: 6px; box-shadow: 0 18px 40px rgba(26,46,48,0.28); padding: 4px; scrollbar-width: thin; }
.entOpt { display: flex; width: 100%; text-align: left; border: none; border-left: 3px solid transparent; border-radius: 4px; background: transparent; color: var(--ink); font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; padding: 7px 10px; cursor: pointer; }
.entOpt:hover { background: var(--orange-soft); border-left-color: var(--orange); color: #b45309; }
.perWrap { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.perRow { display: flex; flex-wrap: wrap; gap: 6px; }
.customRange { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.customRange input { height: 36px; padding: 0 10px; border-radius: 6px; border: 1.5px solid var(--paper-edge); background: #fff; color: var(--ink); font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; }
.customRange span { color: rgba(255,255,255,0.6); font-weight: 900; font-size: 10px; }
.tabRow { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 14px; background: rgba(0,0,0,0.14); border-bottom: 1px solid rgba(255,255,255,0.08); }
.gtab, .gtabOn { display: inline-flex; align-items: center; font-family: 'Inter', sans-serif; font-size: clamp(8px,0.85vw,10px); font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 7px 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s ease; }
.gtab { border: 1.5px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.8); }
.gtab:hover { border-color: var(--orange); color: var(--orange); }
.gtabOn { border: 1.5px solid var(--orange); background: var(--orange); color: #1a2e30; }
.gcnt { font-family: 'Space Mono', monospace; margin-left: 6px; opacity: 0.75; }
.recentBar { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 8px 14px; background: #fff; border-bottom: 1px solid var(--paper-edge); }
.recentLabel { font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: rgba(26,46,48,0.45); margin-right: 4px; }
.rchip { font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; padding: 6px 10px; border-radius: 6px; border: 1.5px solid rgba(238,140,58,0.5); background: #fff; color: #b45309; cursor: pointer; }
.rchip:hover { background: var(--orange); border-color: var(--orange); color: #1a2e30; }
.defList { max-height: 380px; overflow-y: auto; background: #fff; scrollbar-width: thin; scrollbar-color: var(--orange) transparent; }
.defRow, .defRowOn { display: flex; flex-direction: column; gap: 3px; width: 100%; text-align: left; border: none; border-bottom: 1px solid #f1eeea; background: #fff; cursor: pointer; padding: 9px 14px; }
.defRow:hover { background: var(--orange-soft); }
.defRowOn { background: var(--orange-soft); border-left: 3px solid var(--orange); }
.defTitle { display: flex; align-items: center; gap: 10px; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: var(--ink); }
.defTags { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 8px; letter-spacing: 1px; color: rgba(26,46,48,0.5); white-space: nowrap; }
.defDesc { font-size: 10px; font-weight: 600; color: rgba(26,46,48,0.55); }
.viewerBody { padding: clamp(10px,1.4vw,16px); }
@media (max-width: 640px) {
  .entBtn { min-width: 100%; }
  .scopeRow { flex-direction: column; align-items: stretch; }
}
'''

ADDENDUM = '''
- fix79a (2026-09-17, STAGE 1 of 3): Reports page rebuilt as scope-bar + catalogue. ReportHub loses the REPORTS/ANALYSIS tabs and the 12 server CSV pillars entirely (retired per David); ExpenseAnalysis.jsx and its css deleted (ANALYSIS becomes the in-page viewer in stage 2). New reportsCatalog.js holds ~40 report definitions (id, title, dataset, group, money, scopes, entityFilter, filter, periodAware, groupBy, measure, chart, cols, desc) built from real app fields including derived Entry Mode (isLegacy -> Legacy Title, landTitle -> New Title, else New Folder) and Start Month. New COMPANY dataset (audit-log rows, restricted to root/admin/director so manager sees far less) loaded via auditService.getRawStream which now accepts a size param. Scope bar = dataset tiles + WHO/WHAT entity autocomplete (derived from loaded rows) + WHEN period chips with CUSTOM from/to. Catalogue = search + group tabs with live counts + rows showing title, plain-English desc, chart tag and live row count for the current scope. Recently-used chips persist per device in localStorage (per-account preferences deferred). Stage 2 = viewer (chart + table + CSV). Stage 3 = PDF + advanced settings.
'''

print('='*72)
print(' GOLDEN SEED fix79a (STAGE 1): scope bar + catalogue')
print('='*72)

write(CAT, CATALOG_JS, 'write reportsCatalog.js')
write(STU, STUDIO_JS, 'rewrite ReportStudio.jsx (stage 1)')
write(HUB, HUB_JS, 'rewrite ReportHub.jsx (no tabs, no pillars)')
patch(RDATA, "f('owner', 'Primary Owner', 'text', p => p.proprietors?.[0]?.fullName || ''),",
      "f('entryMode', 'Entry Mode', 'text', p => (p.isLegacy ? 'Legacy Title' : (p.landTitle ? 'New Title' : 'New Folder'))),\n  f('startMonth', 'Start Month', 'text', p => monthKey(p.projectStartDate)),\n  f('owner', 'Primary Owner', 'text', p => p.proprietors?.[0]?.fullName || ''),",
      'reportData: derived Entry Mode + Start Month fields')
patch(RDATA, "restricted: false,\n    fields: projectFields,",
      "restricted: false,\n    entityTypes: { PROJECT: 'Project Index', CLIENT: 'Primary Owner', LOCATION: 'District' },\n    dateField: 'Project Start',\n    fields: projectFields,",
      'reportData: PROJECTS entityTypes + dateField')
patch(RDATA, "restricted: false,\n    fields: clientFields,",
      "restricted: false,\n    entityTypes: { CLIENT: 'Client Name', LOCATION: 'District' },\n    dateField: 'Last Contact',\n    fields: clientFields,",
      'reportData: CLIENTS entityTypes + dateField')
patch(RDATA, "restricted: true,\n    fields: paymentFields,",
      "restricted: true,\n    entityTypes: { CLIENT: 'Owner Name', OPERATOR: 'Recorded By' },\n    dateField: 'Date',\n    fields: paymentFields,",
      'reportData: PAYMENTS entityTypes + dateField')
patch(RDATA, "restricted: true,\n    fields: expenseFields,",
      "restricted: true,\n    entityTypes: { OPERATOR: 'Spent By', CATEGORY: 'Category' },\n    dateField: 'Date',\n    fields: expenseFields,",
      'reportData: EXPENSES entityTypes + dateField')
patch(RDATA, "export const datasetsFor = (canSeeMoney) =>",
      """COMPANY_FIELDS = [
  f('timestamp', 'Timestamp', 'date', a => a.timestamp || null),
  f('month', 'Month', 'text', a => monthKey(a.timestamp)),
  f('operator', 'Operator', 'text', a => a.performedBy || ''),
  f('action', 'Action', 'text', a => a.action || ''),
  f('details', 'Details', 'text', a => a.details || ''),
];
DATASETS.COMPANY = {
  key: 'COMPANY',
  label: 'Company',
  blurb: 'Every staff action in the audit ledger: logins, edits, deletes, overrides, stage moves.',
  restricted: true,
  entityTypes: { OPERATOR: 'Operator' },
  dateField: 'Timestamp',
  fields: COMPANY_FIELDS,
  defaultColumns: ['timestamp', 'operator', 'action', 'details'],
  load: async () => {
    const out = [];
    for (let page = 0; page < 40; page += 1) {
      const data = await auditService.getRawStream(page, 200);
      const rows = data?.content || [];
      out.push(...rows);
      if (rows.length < 200) break;
    }
    return out;
  },
};
export const datasetsFor = (canSeeMoney) =>""",
      'reportData: COMPANY dataset (audit rows, restricted)')
patch(RDATA, "import expenseService from '../../services/expenseService';",
      "import expenseService from '../../services/expenseService';\nimport auditService from '../../services/auditService';",
      'reportData: import auditService')
patch(AUDIT, "getRawStream: async (page = 0) => {", "getRawStream: async (page = 0, size = 200) => {", 'auditService: getRawStream size param')
patch(AUDIT, "params: { page, size: 50 }\n      });\n      return response.data;\n    } catch {\n      throw new Error(\"STREAM_ERROR: DATABASE_SYNC_FAILED\");",
      "params: { page, size }\n      });\n      return response.data;\n    } catch {\n      throw new Error(\"STREAM_ERROR: DATABASE_SYNC_FAILED\");",
      'auditService: stream uses size param')
for f in (EA_JS, EA_CSS):
    if os.path.exists(f):
        os.remove(f); print('OK      delete ' + os.path.basename(f))
    else:
        print('MISSING delete ' + os.path.basename(f))
get(STUCSS); BUF[STUCSS] = BUF[STUCSS] + STU_CSS; print('OK      append ReportStudio.module.css')
get(ADD); BUF[ADD] = BUF[ADD] + ADDENDUM; print('OK      append addendum')

for p in (CAT, STU, HUB, RDATA, AUDIT, STUCSS, ADD):
    save(p)
print('')
print('All files written.')

frontend = R('erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=frontend, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print(''); print('BUILD RED -- nothing committed or pushed.'); sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping build check)')

print(''); print('git: staging, committing, pushing...')
MSG = 'fix79a stage1: reports rebuilt as scope bar + catalogue (tabs and 12 server pillars retired, ExpenseAnalysis deleted, COMPANY dataset added, derived Entry Mode)'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print(''); print('Stage 1 done. Wait for the green tick, then say go for stage 2 (viewer: chart + table + CSV).')