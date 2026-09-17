#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP -- fix76 PATCHER
================================================================================
 WHAT:
   1. Removes the hollow wrapper fix75 left behind in ReportStudio.jsx:
         {quickExports && (
         )}
      fix75's delete pattern removed the PRESETS panel but not the
      conditional wrapper around it, and that empty wrapper is the
      "Unexpected )" that killed the Render build at line 319.
   2. From now on every patcher runs a local npm build check (when
      node_modules is installed) BEFORE committing, so a red build never
      reaches Render again.
 HOW: run  py fix.py  from the project root. Prints OK / MISSING per patch.
      Builds, then commits and pushes.
================================================================================
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

STU = os.path.join('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
ADD = 'LLM_CONTEXT_ADDENDUM.md'

BUF = {}


def get(rel):
    if rel not in BUF:
        with open(os.path.join(ROOT, rel), 'r', encoding='utf-8', errors='replace') as f:
            BUF[rel] = f.read()
    return BUF[rel]


def save(rel):
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8', newline='\n') as f:
        f.write(BUF[rel])


def rpatch(rel, pat, new, tag):
    s = get(rel)
    out, n = re.subn(pat, new, s, count=1)
    if n:
        BUF[rel] = out
        print('OK      ' + tag)
    else:
        print('MISSING ' + tag)


def append(rel, block, tag):
    get(rel)
    BUF[rel] = BUF[rel] + block
    print('OK      ' + tag)


ADDENDUM = '''

- fix76 (2026-09-17): build-breaker cleanup from fix75. fix75's delete pattern removed the old PRESETS panel but left its empty conditional wrapper ({quickExports && ( )}) sitting in ReportStudio.jsx, which is the Unexpected ")" that failed the Render build at line 319. The hollow wrapper is deleted; the real one-click CSV block lives inside the DATASETS panel and is untouched. Permanent process change shipped with this fix: every patcher now runs a local npm run build (when erp-frontend/node_modules is installed) AFTER writing files and BEFORE git commit, and refuses to commit on a red build.
'''

print('=' * 72)
print(' GOLDEN SEED fix76 -- hollow wrapper removal + pre-commit build check')
print('=' * 72)

# the hollow wrapper: open paren, whitespace only, close paren
rpatch(STU,
       r'\{quickExports && \(\s*\)\}',
       '',
       'Studio: hollow quickExports wrapper removed')

append(ADD, ADDENDUM, 'Addendum: fix76 entry appended')

for rel in (STU, ADD):
    save(rel)
print('')
print('All files written.')
print('')

# ----------------------------------------------------------------------------
# build sanity check BEFORE any git operation
# ----------------------------------------------------------------------------
frontend = os.path.join(ROOT, 'erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=frontend, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print('')
        print('BUILD RED -- nothing was committed or pushed.')
        print('Send the output above and I will fix it before anything moves.')
        sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping build check)')

print('')
print('git: staging, committing, pushing...')
MSG = 'fix76: remove hollow quickExports wrapper left by fix75 (build breaker), patchers now build-check before commit'
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Render should go green on this push.')