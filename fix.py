#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix92: scope search field proportions, no scrollbar on the
# scope dropdown, catalogue search text alignment + prototype proportions.
# Rules are rewritten by selector (upsert), so nothing can be skipped.
# Then adds, commits and pushes by itself.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CSS = os.path.join(ROOT, 'erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')

ICON = ("url(\"data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20width='14'%20height='14'%20"
        "viewBox='0%200%2024%2024'%20fill='none'%20stroke='%23EE8C3A'%20stroke-width='2.5'%20stroke-linecap='round'%20"
        "stroke-linejoin='round'%3E%3Ccircle%20cx='11'%20cy='11'%20r='8'/%3E%3Cline%20x1='21'%20y1='21'%20"
        "x2='16.65'%20y2='16.65'/%3E%3C/svg%3E\") no-repeat left 10px center")


def upsert_rule(css, selector, body):
    pat = re.compile(re.escape(selector) + r'\s*\{[^}]*\}')
    repl = selector + ' {\n  ' + body + '\n}'
    if pat.search(css):
        return pat.sub(lambda m: repl, css, count=1), 'rewrote ' + selector
    return css + '\n' + repl + '\n', 'added ' + selector


def descroll(css, sel_regex):
    pat = re.compile(r'(' + sel_regex + r'\s*\{)([^}]*)(\})')
    hits = [0]

    def fix(m):
        body = m.group(2)
        new = re.sub(r'max-height:[^;]+;', '', body)
        new = re.sub(r'overflow(-y)?:\s*(auto|scroll)[^;]*;', 'overflow: visible;', new)
        if new != body:
            hits[0] += 1
        return m.group(1) + new + m.group(3)

    return pat.sub(fix, css), hits[0]


with open(CSS, 'r', encoding='utf-8') as f:
    css = f.read()

log = []

# 1. scope search field: shorter height, longer reach, prototype styling
css, m = upsert_rule(css, '.entInput',
                     "height: 34px; width: clamp(220px, 26vw, 320px); padding: 0 12px; border-radius: 6px; "
                     "border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; "
                     "font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; "
                     "transition: border-color 0.2s, box-shadow 0.2s;")
log.append(m)

# 2. scope dropdown table: no scrollbar, list grows to fit
css, n = descroll(css, r'\.(ddScroll|pickScroll|ddList|pickList|entList)\w*')
log.append('descolled %d dropdown rule(s)' % n)

# 3. catalogue search: prototype proportions + perfectly aligned words
css, m = upsert_rule(css, '.searchBox',
                     "position: relative; display: flex; align-items: center; height: 36px; "
                     "width: clamp(200px, 20vw, 264px); background: #fff; border: 1.5px solid #dfd9d1; "
                     "border-radius: 6px; margin-left: auto;")
log.append(m)
css, m = upsert_rule(css, '.searchBox input',
                     "flex: 1 1 auto; width: 100%; height: 34px; border: none; outline: none; "
                     "background: transparent " + ICON + "; padding: 0 10px 0 32px; "
                     "font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; "
                     "letter-spacing: 0.2px; color: #1a2e30; line-height: 34px;")
log.append(m)
css, m = upsert_rule(css, '.searchBox input::placeholder',
                     "color: rgba(26, 46, 48, 0.45); font-weight: 700;")
log.append(m)
css, m = upsert_rule(css, '.searchIcon', "display: none;")
log.append(m)

with open(CSS, 'w', encoding='utf-8', newline='\n') as f:
    f.write(css)
print('\n'.join(log))


def git(*args):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout or '').strip()
    if out:
        print(out)
    if r.returncode != 0:
        print('GIT FAIL: ' + (r.stderr or '').strip())
        sys.exit(1)
    return r


ident = subprocess.run(['git', 'config', 'user.email'], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or '').strip():
    git('config', 'user.name', 'nyenz')
    git('config', 'user.email', 'nyenz@users.noreply.github.com')

git('add', '-A')
git('commit', '-m', 'fix92: scope search proportions, scrollbar-free scope dropdown, aligned catalogue search at prototype size')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix92 done: patched, committed and pushed to main.')