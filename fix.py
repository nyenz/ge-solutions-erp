#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix85 -- CATALOGUE REPAIR + DEFAULT VIEW PIN
# The live page showed "0 REPORTS" because the catalogue defs on disk and the
# studio filter disagreed on key names and on scopes containing 'ALL'.
# fix85 rewrites reportsCatalog.js as the single matched source (ds / period /
# scopes-with-ALL / groupBy / measure / cols / chart / sort / filter) with ~45
# reports incl. entity-scoped ones, exports DEFAULTS, and pins a DEFAULT VIEW
# row at the top of the catalogue list in ReportStudio.jsx.
# ============================================================================
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
CAT = R('erp-frontend', 'src', 'pages', 'Reports', 'reportsCatalog.js')
STU = R('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
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
def write(p, c, tag):
    BUF[p] = c; print('OK      ' + tag)

CATALOG_JS = '''// PATH: erp-frontend/src/pages/Reports/reportsCatalog.js
// GOLDEN SEED -- REPORT CATALOGUE (fix85, single matched source).
// Keys are exactly what ReportStudio.jsx reads: ds, group, money, scopes,
// period, groupBy, measure, cols, chart, sort, filter, desc.
// scopes must contain 'ALL' for a report to show with no entity picked.
export const GROUPS = ['WORK IN','IN PROCESS','MONEY IN','MONEY OUT','CLIENTS / RECOVERY','COMPLIANCE / ARCHIVE'];
export const ENTITIES = {
  PROJECTS: [ { type:'PROJECT', label:'Project', field:'Project Index' }, { type:'CLIENT', label:'Client', field:'Primary Owner' }, { type:'LOCATION', label:'Location', field:'District' } ],
  CLIENTS: [ { type:'CLIENT', label:'Client', field:'Client Name' }, { type:'LOCATION', label:'Location', field:'Districts' } ],
  PAYMENTS: [ { type:'PROJECT', label:'Project', field:'Plot' }, { type:'CLIENT', label:'Client', field:'Owner' }, { type:'OPERATOR', label:'Operator', field:'Recorded By' } ],
  EXPENSES: [ { type:'CATEGORY', label:'Category', field:'Category' }, { type:'OPERATOR', label:'Operator', field:'Spent By' } ],
  COMPANY: [ { type:'OPERATOR', label:'Operator', field:'Operator' } ],
};
export const DEFAULTS = {
  PROJECTS: { ALL:'OWED BY DISTRICT', PROJECT:'PROJECT SNAPSHOT', CLIENT:'ONE CLIENT PROJECTS', LOCATION:'DISTRICT OWED' },
  CLIENTS: { ALL:'TOP DEBTORS', CLIENT:'CLIENT SUMMARY', LOCATION:'CLIENTS BY DISTRICT' },
  PAYMENTS: { ALL:'PAYMENTS RECEIVED', PROJECT:'PROJECT PAYMENT HISTORY', CLIENT:'ONE CLIENT PAYMENTS', OPERATOR:'ONE OPERATOR COLLECTIONS' },
  EXPENSES: { ALL:'EXPENSES BY CATEGORY', CATEGORY:'ONE CATEGORY SPEND', OPERATOR:'EXPENSES PER OPERATOR' },
  COMPANY: { ALL:'OPERATOR WORKLOAD', OPERATOR:'ONE OPERATOR ACTIVITY' },
};
export const CATALOGUE = [
  // PROJECTS / MONEY IN
  { id:'p_owed_dist', title:'OWED BY DISTRICT', desc:'What is still owed, added up per district.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'District', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','District','Sub-County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'} },
  { id:'p_owed_county', title:'OWED BY COUNTY', desc:'What is still owed, added up per county.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL','LOCATION'], period:false, groupBy:'County', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'} },
  { id:'p_owed_sub', title:'OWED BY SUB-COUNTY', desc:'What is still owed, added up per sub-county.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL','LOCATION'], period:false, groupBy:'Sub-County', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','Sub-County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'} },
  { id:'p_owed_owner', title:'OWED BY OWNER', desc:'Every primary owner ranked by what they still owe.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL','CLIENT'], period:false, groupBy:'Primary Owner', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','Owner Phone','District','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'} },
  { id:'p_owed_status', title:'OWED BY STATUS', desc:'What is still owed split by active, released, receivable.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL'], period:false, groupBy:'Status', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'} },
  { id:'p_paid_cost', title:'PAID VS COST', desc:'What has been collected per status against live cost.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'Status', measure:{agg:'sum',field:'Amount Paid'}, cols:['Project Index','Primary Owner','Status','Total Cost','Amount Paid','Balance Owed'], chart:'COLUMN', sort:{col:'Amount Paid',dir:'desc'} },
  { id:'p_storage', title:'STORAGE FEES ACCRUED', desc:'The 50k-per-30-days fees stacked on receivable projects.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'District', measure:{agg:'sum',field:'Storage Fees'}, cols:['Project Index','Primary Owner','District','Storage Fees','Balance Owed'], chart:'BAR', sort:{col:'Storage Fees',dir:'desc'} },
  { id:'p_never_paid', title:'NEVER-PAID PROJECTS', desc:'Projects with no payment recorded at all.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['ALL','CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Amount Paid',op:'eq',value:0}, cols:['Project Index','Primary Owner','District','Status','Balance Owed'], chart:'BAR', sort:{col:'Project Index',dir:'asc'} },
  // PROJECTS / IN PROCESS
  { id:'p_by_stage', title:'PROJECTS BY STAGE', desc:'How many projects sit at each survey stage right now.', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'Stage Index', measure:{agg:'count'}, cols:['Project Index','Primary Owner','District','Stage Index','Status'], chart:'DONUT', sort:{col:'Project Index',dir:'asc'} },
  { id:'p_by_status', title:'PROJECTS BY STATUS', desc:'Active against released against receivable, right now.', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'Status', measure:{agg:'count'}, cols:['Project Index','Primary Owner','District','Status'], chart:'DONUT', sort:{col:'Project Index',dir:'asc'} },
  { id:'p_stalled', title:'STALLED PROJECTS', desc:'Projects with no payment in 60+ days, per district.', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Days Since Payment',op:'gt',value:60}, cols:['Project Index','Primary Owner','District','Days Since Payment','Status'], chart:'BAR', sort:{col:'Days Since Payment',dir:'desc'} },
  { id:'p_tenure', title:'TENURE MIX', desc:'Freehold, mailo, leasehold and customary split.', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['ALL','LOCATION'], period:false, groupBy:'Tenure', measure:{agg:'count'}, cols:['Project Index','Primary Owner','Tenure','District'], chart:'DONUT', sort:{col:'Tenure',dir:'asc'} },
  { id:'p_ownership', title:'SOLO VS JOINT', desc:'Solo-owned projects against joint-owned projects.', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'Ownership', measure:{agg:'count'}, cols:['Project Index','Primary Owner','All Owners','Ownership'], chart:'DONUT', sort:{col:'Ownership',dir:'asc'} },
  { id:'p_released', title:'TITLES RELEASED', desc:'Projects whose title has been released to the client.', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Title Released',op:'isTrue'}, cols:['Project Index','Title ID','Primary Owner','District','Status'], chart:'BAR', sort:{col:'Project Index',dir:'asc'} },
  // PROJECTS / WORK IN
  { id:'p_new_folders', title:'NEW FOLDERS OPENED', desc:'New Folder intakes inside the chosen period.', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['ALL','LOCATION','CLIENT'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'New Folder'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'} },
  { id:'p_new_titles', title:'NEW TITLES ENTERED', desc:'New Title intakes inside the chosen period.', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['ALL','LOCATION','CLIENT'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'New Title'}, cols:['Project Index','Title ID','Primary Owner','District','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'} },
  { id:'p_legacy', title:'LEGACY INTAKES', desc:'Legacy Title intakes inside the chosen period.', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['ALL','LOCATION','CLIENT'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'Legacy Title'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'} },
  // PROJECTS / COMPLIANCE
  { id:'p_legal', title:'LEGAL READINESS', desc:'Owners missing the NIN or address a demand notice needs.', ds:'PROJECTS', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'District', measure:{agg:'count'}, cols:['Project Index','Primary Owner','Owner NIN','Owner Address','District'], chart:'BAR', sort:{col:'District',dir:'asc'} },
  { id:'p_no_nin', title:'OWNERS MISSING NIN', desc:'Projects whose primary owner has no NIN on file.', ds:'PROJECTS', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['ALL','LOCATION','CLIENT'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Owner NIN',op:'empty'}, cols:['Project Index','Primary Owner','Owner NIN','District'], chart:'BAR', sort:{col:'District',dir:'asc'} },
  // PROJECTS / entity-scoped
  { id:'p_snapshot', title:'PROJECT SNAPSHOT', desc:'Everything on one project: identity, title, location, money.', ds:'PROJECTS', group:'IN PROCESS', money:true, scopes:['PROJECT'], period:false, groupBy:'', measure:null, cols:['Project Index','Plot Number','Title ID','Tenure','District','Sub-County','Village','Primary Owner','Owner Phone','Owner NIN','Status','Stage Index','Entry Mode','Total Cost','Amount Paid','Balance Owed','Storage Fees'], chart:'NONE', sort:{col:'Project Index',dir:'asc'} },
  { id:'p_client_projects', title:'ONE CLIENT PROJECTS', desc:'One client\\'s projects grouped by status with what they owe.', ds:'PROJECTS', group:'CLIENTS / RECOVERY', money:true, scopes:['CLIENT'], period:false, groupBy:'Status', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','District','Status','Total Cost','Amount Paid','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'} },
  { id:'p_district_owed', title:'DISTRICT OWED', desc:'What one district still owes, project by project.', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['LOCATION'], period:false, groupBy:'District', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','District','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'} },
  // CLIENTS
  { id:'c_by_district', title:'CLIENTS BY DISTRICT', desc:'How many registered clients each district has.', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:false, scopes:['ALL','LOCATION'], period:false, groupBy:'Districts', measure:{agg:'count'}, cols:['Client Name','Phone','Districts','Projects'], chart:'DONUT', sort:{col:'Client Name',dir:'asc'} },
  { id:'c_by_county', title:'CLIENTS BY COUNTY', desc:'Registered clients per county.', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:false, scopes:['ALL','LOCATION'], period:false, groupBy:'Districts', measure:{agg:'count'}, cols:['Client Name','Phone','Districts'], chart:'BAR', sort:{col:'Client Name',dir:'asc'} },
  { id:'c_top_debtors', title:'TOP DEBTORS', desc:'Clients ranked by what they still owe.', ds:'CLIENTS', group:'MONEY IN', money:true, scopes:['ALL','LOCATION'], period:false, groupBy:'Client Name', measure:{agg:'sum',field:'Total Owed'}, cols:['Client Name','Phone','Districts','Total Owed','Total Paid'], chart:'BAR', sort:{col:'Total Owed',dir:'desc'} },
  { id:'c_recency', title:'CLIENT PAYMENT RECENCY', desc:'Clients ordered by how long since they last paid.', ds:'CLIENTS', group:'MONEY IN', money:true, scopes:['ALL'], period:false, groupBy:'Client Name', measure:{agg:'sum',field:'Total Owed'}, cols:['Client Name','Phone','Days Since Payment','Total Owed'], chart:'BAR', sort:{col:'Days Since Payment',dir:'desc'} },
  { id:'c_no_nin', title:'CLIENTS WITHOUT NIN', desc:'Clients whose identity is incomplete.', ds:'CLIENTS', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['ALL'], period:false, groupBy:'Districts', measure:{agg:'count'}, filter:{field:'NIN',op:'empty'}, cols:['Client Name','Phone','NIN','Districts'], chart:'BAR', sort:{col:'Client Name',dir:'asc'} },
  { id:'c_recent_contact', title:'RECENTLY CONTACTED CLIENTS', desc:'Clients contacted inside the chosen period.', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:false, scopes:['ALL','LOCATION'], period:true, groupBy:'Districts', measure:{agg:'count'}, cols:['Client Name','Phone','Districts','Last Contact'], chart:'COLUMN', sort:{col:'Last Contact',dir:'desc'} },
  { id:'c_summary', title:'CLIENT SUMMARY', desc:'One client: identity, contact, portfolio totals.', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:true, scopes:['CLIENT'], period:false, groupBy:'', measure:null, cols:['Client Name','NIN','Phone','Email','Districts','Projects','Total Owed','Total Paid','Storage Fees'], chart:'NONE', sort:{col:'Client Name',dir:'asc'} },
  // PAYMENTS
  { id:'pay_received', title:'PAYMENTS RECEIVED', desc:'Money in per month for the chosen period.', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['ALL','PROJECT','CLIENT','OPERATOR'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner','Payment Type','Amount Paid','Recorded By'], chart:'LINE', sort:{col:'Date',dir:'desc'} },
  { id:'pay_type', title:'PAYMENTS BY TYPE', desc:'Standard against deposit against receivable-part.', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['ALL','PROJECT','CLIENT'], period:true, groupBy:'Payment Type', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner','Payment Type','Amount Paid'], chart:'DONUT', sort:{col:'Amount Paid',dir:'desc'} },
  { id:'pay_operator', title:'COLLECTIONS PER OPERATOR', desc:'Who collected how much in the chosen period.', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['ALL','OPERATOR'], period:true, groupBy:'Recorded By', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner','Amount Paid','Recorded By'], chart:'COLUMN', sort:{col:'Amount Paid',dir:'desc'} },
  { id:'pay_plot', title:'PAYMENTS BY PROJECT', desc:'Every project ranked by what it has paid.', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['ALL','PROJECT','CLIENT'], period:true, groupBy:'Plot', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner','Payment Type','Amount Paid'], chart:'BAR', sort:{col:'Amount Paid',dir:'desc'} },
  { id:'pay_project_hist', title:'PROJECT PAYMENT HISTORY', desc:'Every payment on one project, month by month.', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['PROJECT'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner','Payment Type','Amount Paid','Balance After'], chart:'LINE', sort:{col:'Date',dir:'desc'} },
  { id:'pay_client_hist', title:'ONE CLIENT PAYMENTS', desc:'One client\\'s payments month by month.', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['CLIENT'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner','Payment Type','Amount Paid'], chart:'LINE', sort:{col:'Date',dir:'desc'} },
  { id:'pay_operator_hist', title:'ONE OPERATOR COLLECTIONS', desc:'One operator\\'s collections month by month.', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['OPERATOR'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner','Amount Paid','Recorded By'], chart:'LINE', sort:{col:'Date',dir:'desc'} },
  // EXPENSES
  { id:'e_category', title:'EXPENSES BY CATEGORY', desc:'Which category ate the money in the chosen period.', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['ALL','CATEGORY','OPERATOR'], period:true, groupBy:'Category', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Note','Amount','Spent By'], chart:'DONUT', sort:{col:'Amount',dir:'desc'} },
  { id:'e_operator', title:'EXPENSES PER OPERATOR', desc:'Who spent how much in the chosen period.', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['ALL','OPERATOR'], period:true, groupBy:'Spent By', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Note','Amount','Spent By'], chart:'COLUMN', sort:{col:'Amount',dir:'desc'} },
  { id:'e_time', title:'EXPENSES OVER TIME', desc:'Money out per month for the chosen period.', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['ALL'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Note','Amount','Spent By'], chart:'LINE', sort:{col:'Date',dir:'desc'} },
  { id:'e_category_hist', title:'ONE CATEGORY SPEND', desc:'One category\\'s spend month by month.', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['CATEGORY'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Note','Amount','Spent By'], chart:'LINE', sort:{col:'Date',dir:'desc'} },
  // COMPANY
  { id:'co_workload', title:'OPERATOR WORKLOAD', desc:'Every staff action counted per operator in the period.', ds:'COMPANY', group:'WORK IN', money:false, scopes:['ALL','OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, cols:['Timestamp','Operator','Action','Details'], chart:'COLUMN', sort:{col:'Operator',dir:'asc'} },
  { id:'co_action', title:'AUDIT BY ACTION', desc:'Which system actions happened most in the period.', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['ALL','OPERATOR'], period:true, groupBy:'Action', measure:{agg:'count'}, cols:['Timestamp','Operator','Action','Details'], chart:'BAR', sort:{col:'Operator',dir:'asc'} },
  { id:'co_logins', title:'LOGINS PER OPERATOR', desc:'Who signed in how often in the chosen period.', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['ALL','OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, filter:{field:'Action',op:'is',value:'LOGIN_SUCCESS'}, cols:['Timestamp','Operator','Action','Details'], chart:'COLUMN', sort:{col:'Operator',dir:'asc'} },
  { id:'co_deletes', title:'DELETIONS & RESTORES', desc:'Deleted and restored records per staff member.', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['ALL','OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, filter:{field:'Action',op:'contains',value:'RECORD_D'}, cols:['Timestamp','Operator','Action','Details'], chart:'BAR', sort:{col:'Timestamp',dir:'desc'} },
  { id:'co_storage', title:'STORAGE & OVERRIDES', desc:'Storage fee changes and overrides per staff member.', ds:'COMPANY', group:'MONEY IN', money:true, scopes:['ALL','OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, filter:{field:'Action',op:'contains',value:'STORAGE'}, cols:['Timestamp','Operator','Action','Details'], chart:'BAR', sort:{col:'Timestamp',dir:'desc'} },
  { id:'co_stages', title:'STAGE MOVES', desc:'Stage changes per staff member in the period.', ds:'COMPANY', group:'IN PROCESS', money:false, scopes:['ALL','OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, filter:{field:'Action',op:'contains',value:'STAGE'}, cols:['Timestamp','Operator','Action','Details'], chart:'COLUMN', sort:{col:'Timestamp',dir:'desc'} },
  { id:'co_operator_hist', title:'ONE OPERATOR ACTIVITY', desc:'One operator\\'s actions by type.', ds:'COMPANY', group:'WORK IN', money:false, scopes:['OPERATOR'], period:true, groupBy:'Action', measure:{agg:'count'}, cols:['Timestamp','Operator','Action','Details'], chart:'BAR', sort:{col:'Timestamp',dir:'desc'} },
];
export default CATALOGUE;
'''

print('=' * 72)
print(' GOLDEN SEED fix85 -- catalogue repair + default view pin')
print('=' * 72)

write(CAT, CATALOG_JS, 'write reportsCatalog.js (matched keys + DEFAULTS + ~45 reports)')

patch(STU,
      "import { CATALOGUE, ENTITIES, GROUPS } from './reportsCatalog';",
      "import { CATALOGUE, ENTITIES, GROUPS, DEFAULTS } from './reportsCatalog';",
      'studio: import DEFAULTS')
patch(STU,
      "  const appliedDef = CATALOGUE.find(d => d.id === appliedId) || null;\n",
      "  const appliedDef = CATALOGUE.find(d => d.id === appliedId) || null;\n"
      "  const defaultName = (DEFAULTS[datasetKey] || {})[entity ? entity.type : 'ALL'] || '';\n"
      "  const defaultDef = CATALOGUE.find(d => d.title === defaultName && d.ds === datasetKey && (!d.money || canSeeMoney)) || null;\n",
      'studio: compute pinned default view')
patch(STU,
      """        <div className={styles.catList}>
          {listed.length === 0 && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}
          {listed.map(def => (""",
      """        <div className={styles.catList}>
          {defaultDef && (
            <div className={styles.catWrap}>
              <button className={styles.catRow + (appliedId === defaultDef.id ? ' ' + styles.catRowOn : '')} onClick={() => setReadId(readId === defaultDef.id ? null : defaultDef.id)} aria-expanded={readId === defaultDef.id}>
                <span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.tag}>{defaultDef.chart !== 'NONE' ? defaultDef.chart : 'TABLE'} &middot; {defaultDef.group}</span></span>
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
          {listed.filter(d => !defaultDef || d.id !== defaultDef.id).length === 0 && !defaultDef && <div className={styles.emptyCell}>NO REPORTS MATCH THIS SCOPE + SEARCH</div>}
          {listed.filter(d => !defaultDef || d.id !== defaultDef.id).map(def => (""",
      'studio: pin DEFAULT VIEW row at top of catalogue')

ADDENDUM = '''
- fix85 (2026-09-25): catalogue repair after the live page showed 0 REPORTS. Root cause: the catalogue defs on disk and the studio filter disagreed on key names (dataset/periodAware vs ds/period) and no def carried 'ALL' in scopes, so every report was filtered out before render. reportsCatalog.js rewritten as the single matched source with ~45 reports (incl. entity-scoped PROJECT SNAPSHOT / ONE CLIENT PAYMENTS / ONE OPERATOR ACTIVITY etc.), a DEFAULTS map, and ENTITIES whose field labels match reportData exactly (clients location = Districts, payments client = Owner). ReportStudio now pins a DEFAULT VIEW row at the top of the catalogue per dataset+entity, excluded from the普通 list to avoid a duplicate row.
'''
get(ADD); BUF[ADD] = BUF[ADD] + ADDENDUM
print('OK      addendum appended')

for p in (CAT, STU, ADD):
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
MSG = 'fix85: catalogue repaired (matched keys, ALL scopes, ~45 reports) + DEFAULT VIEW pin row'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. After the green tick + hard refresh, the catalogue must show ~20 rows for PROJECTS with a pinned DEFAULT VIEW.')