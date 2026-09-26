#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix107: one-pass header repair.
# 1. Brace-balance repair of Header.module.css (closes .notifDrop and any
#    other open block, verifies { } counts match before writing).
# 2. Wraps the dangling fix103 token declarations in a real :root { } block
#    so browsers actually apply them, and defines the missing --panel-edge.
# Then adds, commits and pushes by itself.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HEADER_CSS = os.path.join(ROOT, 'erp-frontend', 'src', 'components', 'layout', 'Header.module.css')

with open(HEADER_CSS, 'r', encoding='utf-8') as f:
    css = f.read()

# ═══ 1. brace-balance repair ═══
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
css = '\n'.join(out)
print('braces inserted: %d | balance: %d open / %d close' % (inserted, css.count('{'), css.count('}')))
if css.count('{') != css.count('}'):
    print('FAIL: still unbalanced -- aborting, nothing written')
    sys.exit(1)

# ═══ 2. wrap dangling tokens in :root and add --panel-edge ═══
m = re.search(r'([ \t]*/\* fix103: local overrides.*?\*/\n(?:[ \t]*--[\w-]+:[^;]*;\n)+)', css, re.S)
if m and ':root {' not in css:
    css = css[:m.start(1)] + ':root {\n' + m.group(1) + '}\n' + css[m.end(1):]
    print('patched: dangling tokens wrapped in :root')
elif m:
    print('skip (already wrapped): tokens in :root')
else:
    print('note: no dangling token block found (already clean or absent)')
if '--panel-edge' not in css:
    if ':root {' in css:
        css = css.replace(':root {', ':root {\n    --panel-edge: rgba(255, 255, 255, 0.10);', 1)
    else:
        css = ':root {\n    --panel-edge: rgba(255, 255, 255, 0.10);\n}\n' + css
    print('patched: --panel-edge fallback defined')
else:
    print('skip (already defined): --panel-edge')

with open(HEADER_CSS, 'w', encoding='utf-8', newline='\n') as f:
    f.write(css)
print('written: ' + os.path.relpath(HEADER_CSS, ROOT))


def git(*args):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or '').strip()
    if o:
        print(o)
    if r.returncode != 0:
        print('GIT FAIL: ' + (r.stderr or '').strip())
        sys.exit(1)
    return r


ident = subprocess.run(['git', 'config', 'user.email'], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or '').strip():
    git('config', 'user.name', 'nyenz')
    git('config', 'user.email', 'nyenz@users.noreply.github.com')

git('add', '-A')
git('commit', '-m', 'fix107: brace-balance repair + dangling header tokens wrapped in :root with --panel-edge fallback')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix107 done: patched, committed and pushed to main.')