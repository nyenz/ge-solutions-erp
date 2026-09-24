#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# GOLDEN SEED fix80 -- REPAIR: COMPANY_FIELDS ReferenceError blanks whole app
# ----------------------------------------------------------------------------
# reportData.js's COMPANY dataset block references COMPANY_FIELDS, a constant
# that was never written (the real array is named companyFields). The module
# throws at import time, so every route renders blank. This fix:
#   1. renames every COMPANY_FIELDS reference to companyFields
#      (inserting the companyFields const first if it is missing)
#   2. adds dateField to all five datasets so period chips can filter
#      event reports in stage 3 (Project Start / Last Contact / Date /
#      Date / Timestamp)
# No feature work here -- repair only.
# ============================================================================
import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, *p)
RDATA = R('erp-frontend', 'src', 'pages', 'Reports', 'reportData.js')
ADD   = R('LLM_CONTEXT_ADDENDUM.md')

with open(RDATA, 'r', encoding='utf-8', errors='replace') as f:
    rd = f.read()

COMPANY_CONST = '\n'.join([
    'const companyFields = [',
    "  f('timestamp', 'Timestamp', 'date', a => a.timestamp || null),",
    "  f('month', 'Month', 'text', a => monthKey(a.timestamp)),",
    "  f('operator', 'Operator', 'text', a => a.performedBy || ''),",
    "  f('action', 'Action', 'text', a => a.action || ''),",
    "  f('details', 'Details', 'text', a => a.details || ''),",
    '];',
    '',
])

print('=' * 72)
print(' GOLDEN SEED fix80 -- repair COMPANY_FIELDS ReferenceError')
print('=' * 72)

if 'COMPANY_FIELDS' in rd:
    if 'const companyFields' not in rd:
        rd = rd.replace('export const DATASETS', COMPANY_CONST + 'export const DATASETS', 1)
        print('OK      companyFields const inserted before DATASETS')
    else:
        print('OK      companyFields const already present')
    rd = rd.replace('COMPANY_FIELDS', 'companyFields')
    print('OK      COMPANY_FIELDS references renamed to companyFields')
else:
    print('SKIP    no COMPANY_FIELDS reference found (already repaired)')

def patch(old, new, tag):
    global rd
    if old in rd:
        rd = rd.replace(old, new, 1)
        print('OK      ' + tag)
    else:
        print('MISSING ' + tag)

patch("restricted: false,\n    fields: projectFields,",
      "restricted: false,\n    dateField: 'Project Start',\n    fields: projectFields,",
      'PROJECTS dateField added')
patch("restricted: false,\n    fields: clientFields,",
      "restricted: false,\n    dateField: 'Last Contact',\n    fields: clientFields,",
      'CLIENTS dateField added')
patch("restricted: true,\n    fields: paymentFields,",
      "restricted: true,\n    dateField: 'Date',\n    fields: paymentFields,",
      'PAYMENTS dateField added')
patch("restricted: true,\n    fields: expenseFields,",
      "restricted: true,\n    dateField: 'Date',\n    fields: expenseFields,",
      'EXPENSES dateField added')
patch("fields: companyFields,",
      "fields: companyFields,\n    dateField: 'Timestamp',",
      'COMPANY dateField added')

with open(RDATA, 'w', encoding='utf-8', newline='\n') as f:
    f.write(rd)
print('')
print('reportData.js written.')

ADDENDUM = '''
- fix80 (2026-09-24): REPAIR for the blank-app ReferenceError. The stage-1 COMPANY dataset block referenced a COMPANY_FIELDS constant that was never written (the fields array landed under the name companyFields), so reportData.js threw at module load and every route rendered blank. fix80 renames the reference to the existing companyFields const (inserting the const if it is ever missing), and adds a dateField label to all five datasets (Project Start / Last Contact / Date / Date / Timestamp) so the studio's period chips can filter event reports once stage 3 ships.
'''
with open(ADD, 'a', encoding='utf-8', newline='\n') as f:
    f.write(ADDENDUM)
print('OK      addendum appended')

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
MSG = 'fix80 repair: COMPANY_FIELDS ReferenceError fixed (companyFields const), dateField added to all datasets'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Repair pushed. Wait for the green tick -- the app should boot again.')
print('Then say go and I ship stage 3: results viewer (table + chart + CSV/PDF).')