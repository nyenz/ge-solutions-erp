#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix106: generic brace-balance repair for Header.module.css.
# fix105 missed the fourth unclosed block (.notifDrop at line 283). This pass
# walks the stylesheet tracking block depth and inserts a closing brace
# wherever a top-level rule begins inside a still-open block, closes anything
# left open at end-of-file, and verifies the brace counts match before
# committing. Idempotent: if the file is already balanced, nothing changes.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HEADER_CSS = os.path.join(ROOT, 'erp-frontend', 'src', 'components', 'layout', 'Header.module.css')

with open(HEADER_CSS, 'r', encoding='utf-8') as f:
    css = f.read()

RULE_START = re.compile(r'^\.[A-Za-z][^{}]*\{')
lines = css.split('\n')
out = []
depth = 0
inserted = 0
for ln in lines:
    st = ln.strip()
    top_level = not ln[:1].isspace()
    if depth > 0 and top_level and (RULE_START.match(st) or st.startswith('@media')):
        out.append('}')
        depth -= 1
        inserted += 1
    out.append(ln)
    depth += ln.count('{') - ln.count('}')
while depth > 0:
    out.append('}')
    depth -= 1
    inserted += 1
fixed = '\n'.join(out)

opens = fixed.count('{')
closes = fixed.count('}')
print('braces inserted: %d | final balance: %d open / %d close' % (inserted, opens, closes))
if opens != closes:
    print('FAIL: stylesheet still unbalanced after repair -- aborting, nothing written')
    sys.exit(1)

if fixed == css:
    print('Header.module.css already balanced -- nothing to do')
    sys.exit(0)

with open(HEADER_CSS, 'w', encoding='utf-8', newline='\n') as f:
    f.write(fixed)
print('written: ' + os.path.relpath(HEADER_CSS, ROOT))


def git(*args):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)
    out2 = (r.stdout or '').strip()
    if out2:
        print(out2)
    if r.returncode != 0:
        print('GIT FAIL: ' + (r.stderr or '').strip())
        sys.exit(1)
    return r


ident = subprocess.run(['git', 'config', 'user.email'], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or '').strip():
    git('config', 'user.name', 'nyenz')
    git('config', 'user.email', 'nyenz@users.noreply.github.com')

git('add', '-A')
git('commit', '-m', 'fix106: brace-balance repair for Header.module.css -- closes .notifDrop and any other open block, verified counts')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix106 done: patched, committed and pushed to main.')