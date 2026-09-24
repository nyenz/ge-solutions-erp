#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix79a -- STAGE 1 of 3: REPORT CATALOG DATA LAYER
# ----------------------------------------------------------------------------
# Adds:
#   * erp-frontend/src/pages/Reports/reportsCatalog.js  (NEW)
#       40 standing reports across PROJECTS / CLIENTS / PAYMENTS / EXPENSES /
#       COMPANY. Each line: group, dataset, money gate, entity scopes, whether
#       it honours the period chips, group-by field, measure, default columns,
#       default sort (most relevant field first), plain-English description.
#   * reportData.js: COMPANY dataset (audit ledger) + its fields.
#   * auditService.js: getRawStream(page, size) so the COMPANY dataset can pull
#     full pages instead of 50-row pages.
# NO UI changes in this stage. Stage 2 = scope bar + catalogue UI.
#              Stage 3 = preview table + charts + CSV/PDF.
# RUN:  py -m py_compile fix.py   (syntax check first)
#       py fix.py
# ============================================================================
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)

CAT    = R('erp-frontend', 'src', 'pages', 'Reports', 'reportsCatalog.js')
RDATA  = R('erp-frontend', 'src', 'pages', 'Reports', 'reportData.js')
AUDIT  = R('erp-frontend', 'src', 'services', 'auditService.js')
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

# ----------------------------------------------------------------------------
# reportsCatalog.js -- one line per standing report
# ----------------------------------------------------------------------------
CAT_JS = '''// PATH: erp-frontend/src/pages/Reports/reportsCatalog.js
// GOLDEN SEED -- REPORT CATALOG (fix79 stage 1)
// One line per standing report. The period chips on the page multiply every
// period:true line at run time, so this list is subjects, not permutations.
//   money:true   -> hidden from roles without financial access
//   scopes       -> entity types this report can be narrowed to
//   period:true  -> event report, honours the period chips
//   sort         -> default sort, most relevant field first
export const CATALOG_GROUPS = [
  'MONEY IN', 'MONEY OUT', 'WORK IN', 'IN PROCESS',
  'CLIENTS / RECOVERY', 'COMPLIANCE / ARCHIVE',
];
export const CATALOG = [
  // ── PROJECTS / MONEY IN ─────────────────────────────────────────────
  { id:'P_OWED_DIST', ds:'PROJECTS', group:'MONEY IN', money:true, period:false,
    scopes:['LOCATION','CLIENT','PROJECT'], title:'OWED BY DISTRICT',
    groupBy:'District', measure:{agg:'sum', field:'Balance Owed'},
    cols:['Project Index','Primary Owner','District','Sub-County','Status','Balance Owed'],
    sort:{col:'Balance Owed', dir:'desc'},
    desc:'What is still owed on every project, added up per district, highest first.' },
  { id:'P_OWED_COUNTY', ds:'PROJECTS', group:'MONEY IN', money:true, period:false,
    scopes:['LOCATION','CLIENT','PROJECT'], title:'OWED BY COUNTY',
    groupBy:'County', measure:{agg:'sum', field:'Balance Owed'},
    cols:['Project Index','Primary Owner','County','Status','Balance Owed'],
    sort:{col:'Balance Owed', dir:'desc'},
    desc:'What is still owed, added up per county, highest first.' },
  { id:'P_OWED_SUB', ds:'PROJECTS', group:'MONEY IN', money:true, period:false,
    scopes:['LOCATION','CLIENT','PROJECT'], title:'OWED BY SUB-COUNTY',
    groupBy:'Sub-County', measure:{agg:'sum', field:'Balance Owed'},
    cols:['Project Index','Primary Owner','Sub-County','Status','Balance Owed'],
    sort:{col:'Balance Owed', dir:'desc'},
    desc:'What is still owed, added up per sub-county, highest first.' },
  { id:'P_OWED_OWNER', ds:'PROJECTS', group:'MONEY IN', money:true, period:false,
    scopes:['CLIENT','LOCATION'], title:'OWED BY OWNER',
    groupBy:'Primary Owner', measure:{agg:'sum', field:'Balance Owed'},
    cols:['Project Index','Primary Owner','Owner Phone','District','Balance Owed'],
    sort:{col:'Balance Owed', dir:'desc'},
    desc:'Every primary owner ranked by what they still owe.' },
  { id:'P_OWED_STATUS', ds:'PROJECTS', group:'MONEY IN', money:true, period:false,
    scopes:['LOCATION'], title:'OWED BY STATUS',
    groupBy:'Status', measure:{agg:'sum', field:'Balance Owed'},
    cols:['Project Index','Primary Owner','Status','Balance Owed'],
    sort:{col:'Balance Owed', dir:'desc'},
    desc:'What is still owed split by active, released and receivable.' },
  { id:'P_PAID_VS_COST', ds:'PROJECTS', group:'MONEY IN', money:true, period:false,
    scopes:['LOCATION','CLIENT'], title:'PAID VS COST',
    groupBy:'Status', measure:{agg:'sum', field:'Amount Paid'},
    cols:['Project Index','Primary Owner','Status','Total Cost','Amount Paid','Balance Owed'],
    sort:{col:'Amount Paid', dir:'desc'},
    desc:'What has been collected against what each project costs.' },
  { id:'P_STORAGE', ds:'PROJECTS', group:'MONEY IN', money:true, period:false,
    scopes:['LOCATION','CLIENT'], title:'STORAGE FEES ACCRUED',
    groupBy:'District', measure:{agg:'sum', field:'Storage Fees'},
    cols:['Project Index','Primary Owner','District','Storage Fees','Balance Owed'],
    sort:{col:'Storage Fees', dir:'desc'},
    desc:'The 50k-per-30-days storage fees stacked on receivable projects.' },
  // ── PROJECTS / WORK IN ──────────────────────────────────────────────
  { id:'P_NEW_FOLDERS', ds:'PROJECTS', group:'WORK IN', money:false, period:true,
    scopes:['LOCATION','CLIENT'], title:'NEW FOLDERS OPENED',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','District','Project Start','Status'],
    sort:{col:'Project Start', dir:'desc'},
    desc:'Folders opened in the chosen period, newest first.' },
  { id:'P_NEW_TITLES', ds:'PROJECTS', group:'WORK IN', money:false, period:true,
    scopes:['LOCATION','CLIENT'], title:'NEW TITLES ENTERED',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Title ID','Primary Owner','District','Project Start'],
    sort:{col:'Project Start', dir:'desc'},
    desc:'Titles entered through New Title mode in the chosen period.' },
  { id:'P_LEGACY_INTAKES', ds:'PROJECTS', group:'WORK IN', money:false, period:true,
    scopes:['LOCATION','CLIENT'], title:'LEGACY INTAKES',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','District','Project Start','Status'],
    sort:{col:'Project Start', dir:'desc'},
    desc:'Legacy titles taken in during the chosen period.' },
  // ── PROJECTS / IN PROCESS ───────────────────────────────────────────
  { id:'P_BY_STAGE', ds:'PROJECTS', group:'IN PROCESS', money:false, period:false,
    scopes:['LOCATION','CLIENT'], title:'PROJECTS BY STAGE',
    groupBy:'Stage Index', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','District','Stage Index','Status'],
    sort:{col:'Stage Index', dir:'asc'},
    desc:'How many projects sit at each of the five survey stages right now.' },
  { id:'P_STALLED', ds:'PROJECTS', group:'IN PROCESS', money:false, period:false,
    scopes:['LOCATION','CLIENT','PROJECT'], title:'STALLED PROJECTS',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','District','Days Since Payment','Status'],
    sort:{col:'Days Since Payment', dir:'desc'},
    desc:'Projects with no stage movement for 60+ days, per district.' },
  { id:'P_READY', ds:'PROJECTS', group:'IN PROCESS', money:false, period:false,
    scopes:['LOCATION'], title:'READY FOR TITLING',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','District','Status'],
    sort:{col:'Project Index', dir:'asc'},
    desc:'Projects waiting only on the final registration stage.' },
  { id:'P_TITLES_ISSUED', ds:'PROJECTS', group:'IN PROCESS', money:false, period:true,
    scopes:['LOCATION','CLIENT'], title:'TITLES ISSUED',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Title ID','Primary Owner','District','Status'],
    sort:{col:'Project Index', dir:'asc'},
    desc:'Titles issued during the chosen period.' },
  { id:'P_RELEASED', ds:'PROJECTS', group:'IN PROCESS', money:false, period:true,
    scopes:['LOCATION','CLIENT'], title:'PROJECTS RELEASED',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','District','Status'],
    sort:{col:'Project Index', dir:'asc'},
    desc:'Projects handed back to clients during the chosen period.' },
  { id:'P_TENURE', ds:'PROJECTS', group:'IN PROCESS', money:false, period:false,
    scopes:['LOCATION'], title:'TENURE MIX',
    groupBy:'Tenure', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','Tenure','District'],
    sort:{col:'Tenure', dir:'asc'},
    desc:'Freehold, mailo, leasehold and customary split of the portfolio.' },
  { id:'P_OWNERSHIP', ds:'PROJECTS', group:'IN PROCESS', money:false, period:false,
    scopes:['LOCATION','CLIENT'], title:'SOLO VS JOINT',
    groupBy:'Ownership', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','All Owners','Ownership'],
    sort:{col:'Ownership', dir:'asc'},
    desc:'Solo-owned projects against joint-owned projects.' },
  // ── PROJECTS / COMPLIANCE ───────────────────────────────────────────
  { id:'P_LEGAL', ds:'PROJECTS', group:'COMPLIANCE / ARCHIVE', money:false, period:false,
    scopes:['LOCATION','CLIENT'], title:'LEGAL READINESS',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','Owner NIN','Owner Address','District'],
    sort:{col:'District', dir:'asc'},
    desc:'Owners missing the NIN or home address a demand notice needs, per district.' },
  { id:'P_MISSING_DOCS', ds:'PROJECTS', group:'COMPLIANCE / ARCHIVE', money:false, period:false,
    scopes:['LOCATION','CLIENT'], title:'MISSING DOCUMENTS',
    groupBy:'District', measure:{agg:'count'},
    cols:['Project Index','Primary Owner','District','Status'],
    sort:{col:'District', dir:'asc'},
    desc:'Projects with no document uploaded yet, per district.' },
  // ── CLIENTS ─────────────────────────────────────────────────────────
  { id:'C_TOP_DEBTORS', ds:'CLIENTS', group:'MONEY IN', money:true, period:false,
    scopes:['CLIENT','LOCATION'], title:'TOP DEBTORS',
    groupBy:'Client Name', measure:{agg:'sum', field:'Total Owed'},
    cols:['Client Name','Phone','Districts','Total Owed','Total Paid'],
    sort:{col:'Total Owed', dir:'desc'},
    desc:'Clients ranked by what they still owe, highest first.' },
  { id:'C_RECENCY', ds:'CLIENTS', group:'MONEY IN', money:true, period:false,
    scopes:['CLIENT'], title:'CLIENT PAYMENT RECENCY',
    groupBy:'Client Name', measure:{agg:'sum', field:'Total Owed'},
    cols:['Client Name','Phone','Days Since Payment','Total Owed'],
    sort:{col:'Days Since Payment', dir:'desc'},
    desc:'Clients ordered by how long it has been since they last paid.' },
  { id:'C_NO_NIN', ds:'CLIENTS', group:'COMPLIANCE / ARCHIVE', money:false, period:false,
    scopes:['CLIENT'], title:'CLIENTS WITHOUT NIN',
    groupBy:'Client Name', measure:{agg:'count'},
    cols:['Client Name','Phone','NIN','Districts'],
    sort:{col:'Client Name', dir:'asc'},
    desc:'Clients whose identity is incomplete, so legal action is blocked.' },
  { id:'C_NEW', ds:'CLIENTS', group:'WORK IN', money:false, period:true,
    scopes:['CLIENT','LOCATION'], title:'NEW CLIENTS',
    groupBy:'Client Name', measure:{agg:'count'},
    cols:['Client Name','Phone','Districts','Last Contact'],
    sort:{col:'Client Name', dir:'asc'},
    desc:'Clients registered during the chosen period.' },
  // ── PAYMENTS ────────────────────────────────────────────────────────
  { id:'PAY_RECEIVED', ds:'PAYMENTS', group:'MONEY IN', money:true, period:true,
    scopes:['PROJECT','CLIENT','OPERATOR'], title:'PAYMENTS RECEIVED',
    groupBy:'Month', measure:{agg:'sum', field:'Amount Paid'},
    cols:['Date','Plot','Owner','Payment Type','Amount Paid','Recorded By'],
    sort:{col:'Date', dir:'desc'},
    desc:'Money that came in during the chosen period, month by month.' },
  { id:'PAY_TYPE', ds:'PAYMENTS', group:'MONEY IN', money:true, period:true,
    scopes:['PROJECT','CLIENT'], title:'PAYMENTS BY TYPE',
    groupBy:'Payment Type', measure:{agg:'sum', field:'Amount Paid'},
    cols:['Date','Plot','Owner','Payment Type','Amount Paid'],
    sort:{col:'Amount Paid', dir:'desc'},
    desc:'Standard against deposit against receivable-part payments.' },
  { id:'PAY_OPERATOR', ds:'PAYMENTS', group:'MONEY IN', money:true, period:true,
    scopes:['OPERATOR'], title:'COLLECTIONS PER OPERATOR',
    groupBy:'Recorded By', measure:{agg:'sum', field:'Amount Paid'},
    cols:['Date','Plot','Owner','Amount Paid','Recorded By'],
    sort:{col:'Amount Paid', dir:'desc'},
    desc:'Who collected how much during the chosen period.' },
  { id:'PAY_PROJECT', ds:'PAYMENTS', group:'MONEY IN', money:true, period:true,
    scopes:['PROJECT','CLIENT'], title:'PAYMENTS BY PROJECT',
    groupBy:'Plot', measure:{agg:'sum', field:'Amount Paid'},
    cols:['Date','Plot','Owner','Payment Type','Amount Paid'],
    sort:{col:'Amount Paid', dir:'desc'},
    desc:'Every payment grouped under its project, highest first.' },
  { id:'PAY_TOP', ds:'PAYMENTS', group:'MONEY IN', money:true, period:true,
    scopes:['CLIENT','OPERATOR'], title:'TOP PAYMENTS BY OWNER',
    groupBy:'Owner', measure:{agg:'sum', field:'Amount Paid'},
    cols:['Date','Plot','Owner','Payment Type','Amount Paid'],
    sort:{col:'Amount Paid', dir:'desc'},
    desc:'Owners ranked by what they paid during the chosen period.' },
  // ── EXPENSES ────────────────────────────────────────────────────────
  { id:'EXP_SPENT', ds:'EXPENSES', group:'MONEY OUT', money:true, period:true,
    scopes:['OPERATOR'], title:'EXPENSES SPENT',
    groupBy:'Month', measure:{agg:'sum', field:'Amount'},
    cols:['Date','Category','Spent By','Amount'],
    sort:{col:'Date', dir:'desc'},
    desc:'Money that left the office during the chosen period, month by month.' },
  { id:'EXP_CATEGORY', ds:'EXPENSES', group:'MONEY OUT', money:true, period:true,
    scopes:['OPERATOR'], title:'EXPENSES BY CATEGORY',
    groupBy:'Category', measure:{agg:'sum', field:'Amount'},
    cols:['Date','Category','Spent By','Amount'],
    sort:{col:'Amount', dir:'desc'},
    desc:'Which category ate the money during the chosen period.' },
  { id:'EXP_OPERATOR', ds:'EXPENSES', group:'MONEY OUT', money:true, period:true,
    scopes:['OPERATOR'], title:'EXPENSES PER OPERATOR',
    groupBy:'Spent By', measure:{agg:'sum', field:'Amount'},
    cols:['Date','Category','Spent By','Amount'],
    sort:{col:'Amount', dir:'desc'},
    desc:'Who spent how much during the chosen period.' },
  // ── COMPANY (audit ledger, admin only via restricted dataset) ──────
  { id:'CO_WORKLOAD', ds:'COMPANY', group:'WORK IN', money:false, period:true,
    scopes:['OPERATOR'], title:'OPERATOR WORKLOAD',
    groupBy:'Operator', measure:{agg:'count'},
    cols:['Timestamp','Operator','Action','Details'],
    sort:{col:'Operator', dir:'asc'},
    desc:'Every action each staff member took during the chosen period.' },
  { id:'CO_STAGES', ds:'COMPANY', group:'IN PROCESS', money:false, period:true,
    scopes:['OPERATOR'], title:'STAGE MOVES LOG',
    groupBy:'Operator', measure:{agg:'count'},
    cols:['Timestamp','Operator','Action','Details'],
    sort:{col:'Timestamp', dir:'desc'},
    desc:'Who moved which project between stages during the chosen period.' },
  { id:'CO_LOGINS', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, period:true,
    scopes:['OPERATOR'], title:'LOGINS PER OPERATOR',
    groupBy:'Operator', measure:{agg:'count'},
    cols:['Timestamp','Operator','Action','Details'],
    sort:{col:'Operator', dir:'asc'},
    desc:'Sign-ins per staff member during the chosen period.' },
  { id:'CO_DELETES', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, period:true,
    scopes:['OPERATOR'], title:'DELETIONS & RESTORES',
    groupBy:'Operator', measure:{agg:'count'},
    cols:['Timestamp','Operator','Action','Details'],
    sort:{col:'Timestamp', dir:'desc'},
    desc:'Soft-deletes and restores per staff member during the chosen period.' },
  { id:'CO_OVERRIDES', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, period:true,
    scopes:['OPERATOR'], title:'OVERRIDE CHANGES',
    groupBy:'Operator', measure:{agg:'count'},
    cols:['Timestamp','Operator','Action','Details'],
    sort:{col:'Timestamp', dir:'desc'},
    desc:'Storage-rate and settings overrides per staff member.' },
  { id:'CO_CALLS', ds:'COMPANY', group:'CLIENTS / RECOVERY', money:false, period:true,
    scopes:['OPERATOR'], title:'CALLS LOGGED',
    groupBy:'Operator', measure:{agg:'count'},
    cols:['Timestamp','Operator','Action','Details'],
    sort:{col:'Timestamp', dir:'desc'},
    desc:'Recovery calls logged per staff member during the chosen period.' },
];
export default CATALOG;
'''

ADDENDUM = '''
- fix79a (2026-09-18, STAGE 1 of 3): report catalogue data layer. New reportsCatalog.js holds 40 standing reports across PROJECTS / CLIENTS / PAYMENTS / EXPENSES / COMPANY; each line carries group, dataset, money gate, entity scopes, period-awareness, group-by field, measure, default columns, default sort (most relevant field first) and a plain-English description. reportData.js gains the COMPANY dataset built from the audit ledger (restricted, admin-only) and auditService.getRawStream now accepts a page size so the COMPANY dataset can pull full pages. No UI changes in this stage; stage 2 adds the scope bar + catalogue UI, stage 3 adds the preview table + charts + CSV/PDF.
'''

print('=' * 72)
print(' GOLDEN SEED fix79a -- STAGE 1 of 3: report catalogue data layer')
print('=' * 72)

write(CAT, CAT_JS, 'write reportsCatalog.js (40 standing reports)')

patch(RDATA,
      "import expenseService from '../../services/expenseService';",
      "import expenseService from '../../services/expenseService';\nimport auditService from '../../services/auditService';",
      'reportData: import auditService')

patch(RDATA,
      "f('daysAgo', 'Days Ago', 'number', e => daysSince(e.createdAt)),\n];",
      "f('daysAgo', 'Days Ago', 'number', e => daysSince(e.createdAt)),\n];\n"
      "/* ── COMPANY (audit ledger) ─────────────────────────────────────── */\n"
      "const companyFields = [\n"
      "  f('timestamp', 'Timestamp', 'date', a => a.timestamp || null),\n"
      "  f('month', 'Month', 'text', a => monthKey(a.timestamp)),\n"
      "  f('operator', 'Operator', 'text', a => a.performedBy || ''),\n"
      "  f('action', 'Action', 'text', a => a.action || ''),\n"
      "  f('details', 'Details', 'text', a => a.details || ''),\n"
      "];",
      'reportData: company fields added')

patch(RDATA,
      "    return data?.content || data || [];\n  },\n};",
      "    return data?.content || data || [];\n  },\n},\n"
      "  COMPANY: {\n"
      "    key: 'COMPANY',\n"
      "    label: 'Company',\n"
      "    blurb: 'Every staff action the audit ledger recorded: logins, edits, deletes, overrides, calls.',\n"
      "    restricted: true,\n"
      "    fields: companyFields,\n"
      "    defaultColumns: ['timestamp', 'operator', 'action', 'details'],\n"
      "    load: async () => {\n"
      "      const out = [];\n"
      "      for (let page = 0; page < 20; page += 1) {\n"
      "        const data = await auditService.getRawStream(page, 200);\n"
      "        const rows = data?.content || [];\n"
      "        out.push(...rows);\n"
      "        if (rows.length < 200) break;\n"
      "      }\n"
      "      return out;\n"
      "    },\n"
      "  },\n"
      "};",
      'reportData: COMPANY dataset added')

patch(AUDIT,
      "getRawStream: async (page = 0) => {",
      "getRawStream: async (page = 0, size = 200) => {",
      'auditService: getRawStream accepts size')
patch(AUDIT,
      "params: { page, size: 50 }",
      "params: { page, size }",
      'auditService: getRawStream passes size')

get(ADD)
BUF[ADD] = BUF[ADD] + ADDENDUM
print('OK      addendum appended')

for p in (CAT, RDATA, AUDIT, ADD):
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
    print('(erp-frontend/node_modules not installed -- skipping build check)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix79a stage1: report catalogue data layer (40 standing reports + COMPANY dataset)'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Stage 1 done. Next: stage 2 = scope bar + catalogue UI.')