#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP -- fix77 PATCHER
================================================================================
 WHAT:
   The results-table row hover was too light for two reasons:
     1. the tint was rgba(238,140,58,0.12) -- a whisper on white rows;
     2. the orange left bar the hover promises is a border on <tr>, and the
        table uses border-collapse: separate, where row borders never paint.
   Now: tint at 0.22 alpha, and the left bar is drawn as an inset shadow on
        the first cell (which does paint), on both the row table and the
        grouped table.
 HOW: run  py fix.py  from the project root. Build-checks, commits, pushes.
================================================================================
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

STUCSS = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')
ADD    = 'LLM_CONTEXT_ADDENDUM.md'

BUF = {}


def get(rel):
    if rel not in BUF:
        with open(os.path.join(ROOT, rel), 'r', encoding='utf-8', errors='replace') as f:
            BUF[rel] = f.read()
    return BUF[rel]


def save(rel):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8', newline='\n') as f:
        f.write(BUF[rel])


def append(rel, block, tag):
    get(rel)
    BUF[rel] = BUF[rel] + block
    print('OK      ' + tag)


STU_CSS = '''

/* fix77 -- table hover with actual presence.
   0.12 alpha on white was invisible at arm's length, and the orange left
   bar never painted because row borders do not render under
   border-collapse: separate. The bar is an inset shadow on the first cell
   instead, which does paint. Appended: cascade wins over the zebra stripe
   and the old hover rule. */
.table tbody tr:hover { background: rgba(238,140,58,0.22); }
.table tbody tr:hover td { color: #1a2e30; }
.table tbody tr:hover td:first-child { box-shadow: inset 3px 0 0 0 var(--orange); }
.table tbody tr { transition: background 0.15s ease; }
'''

ADDENDUM = '''

- fix77 (2026-09-17): results-table row hover fixed for real. The old hover was rgba(238,140,58,0.12) on white (invisible at arm's length) and its orange left bar was a border on the row, which never paints because the table uses border-collapse: separate. Hover is now rgba(238,140,58,0.22) with the orange left bar drawn as an inset shadow on the first cell, on both the row-by-row table and the grouped table, with a 0.15s ease transition.
'''

print('=' * 72)
print(' GOLDEN SEED fix77 -- table hover presence')
print('=' * 72)

append(STUCSS, STU_CSS, 'Studio CSS: stronger table hover + painted left bar appended')
append(ADD, ADDENDUM, 'Addendum: fix77 entry appended')

for rel in (STUCSS, ADD):
    save(rel)
print('')
print('All files written.')
print('')

frontend = os.path.join(ROOT, 'erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=frontend, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print('')
        print('BUILD RED -- nothing was committed or pushed.')
        sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping build check)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix77: results table hover gets real presence (0.22 tint + painted orange left bar)'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Wait for the green tick, then hover a row and tell me if it still reads too light.')