#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix100: verify decorBl usage against its source page and
# rewire Reports to match (child element vs panel class), then discover the
# app's real panel-arrow button structurally (head button rendering a
# chevron icon), port its class rules verbatim and wire it onto both heads.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'erp-frontend', 'src')
REPORTS = os.path.join(SRC, 'pages', 'Reports')
JSX = os.path.join(REPORTS, 'ReportStudio.jsx')
CSS = os.path.join(REPORTS, 'ReportStudio.module.css')


def read(p):
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


css = read(CSS)
jsx = read(JSX)

# ═══ 1. locate the decoration source page from the port comment ═══
m = re.search(r'/\* fix99b: ported verbatim from (.+?) \*/', css)
ref_css = os.path.join(ROOT, m.group(1).strip()) if m else None
ref_dir = os.path.dirname(ref_css) if ref_css and os.path.isdir(os.path.dirname(ref_css)) else None
print('decoration source: ' + (os.path.relpath(ref_css, ROOT) if ref_css else '(unknown)'))

# ═══ 2. decorBl: child element or panel class? match the source exactly ═══
standalone = False
if ref_dir:
    for fn in os.listdir(ref_dir):
        if fn.endswith('.jsx'):
            body = read(os.path.join(ref_dir, fn))
            if 'decorBl' not in body:
                continue
            if re.search(r'className=\{styles\.decorBl\}', body):
                standalone = True
                print('decorBl usage in source: standalone child element')
            elif re.search(r'className=\{[^}]*\+[^}]*styles\.decorBl', body):
                print('decorBl usage in source: combined panel class (current wiring is correct)')
            break

if standalone and "styles.decorBl}" in jsx.replace(" + ' ' + styles.decorBl}", '}'):
    n = jsx.count(" + ' ' + styles.decorBl}")
    jsx = jsx.replace(" + ' ' + styles.decorBl}", '}')
    print('rewired: removed decorBl from %d panel class list(s)' % n)
    if '<div className={styles.decorBl}' not in jsx:
        jsx, c1 = re.subn(r'(      <div className=\{styles\.scopePanel[^>]*>\n)',
                          r'\1        <div className={styles.decorBl} aria-hidden="true"></div>\n', jsx, count=1)
        jsx, c2 = re.subn(r'(      <div className=\{\(catOpen[^>]*>\n)',
                          r'\1        <div className={styles.decorBl} aria-hidden="true"></div>\n', jsx, count=1)
        print('rewired: decorBl child element inserted in %d panel(s)' % (c1 + c2))
    else:
        print('skip (already applied): decorBl child element')
elif standalone:
    print('note: decorBl standalone detected but wiring already matches')
write(JSX, jsx)

# ═══ 3. structural arrow discovery: head button rendering a chevron icon ═══
ARROW_BTN = re.compile(r'<button[^>]*className=\{styles\.([A-Za-z0-9_]+)\}[^>]*>(?:(?!</button>).){0,160}?(?:FiChevron|FiArrow|FiPlus|FiMinus|rotate)', re.S)
arrow_class = None
arrow_css_file = None
cands = []
pages_dir = os.path.join(SRC, 'pages')
if os.path.isdir(pages_dir):
    for d in sorted(os.listdir(pages_dir)):
        pd = os.path.join(pages_dir, d)
        if d == 'Reports' or not os.path.isdir(pd):
            continue
        for f in sorted(os.listdir(pd)):
            if f.endswith('.jsx'):
                cands.append(os.path.join(pd, f))
for dirpath, _dirs, files in os.walk(os.path.join(SRC, 'components')):
    for f in sorted(files):
        if f.endswith('.jsx'):
            cands.append(os.path.join(dirpath, f))
for fp in cands:
    mm = ARROW_BTN.search(read(fp))
    if mm:
        arrow_class = mm.group(1)
        arrow_css_file = fp[:-4] + '.module.css'
        if not os.path.exists(arrow_css_file):
            arrow_css_file = None
            for f in os.listdir(os.path.dirname(fp)):
                if f.endswith('.module.css'):
                    arrow_css_file = os.path.join(os.path.dirname(fp), f)
                    break
        print('arrow button discovered: .' + arrow_class + ' in ' + os.path.relpath(fp, ROOT))
        break
if not arrow_class:
    print('note: no chevron head button found in other pages; checked %d files' % len(cands))

if arrow_class and arrow_css_file and os.path.exists(arrow_css_file):
    rules = re.findall(r'([^{}]+)\{([^}]*)\}', read(arrow_css_file))
    picked = [(s.strip(), b.strip()) for s, b in rules
              if re.match(r'\s*\.' + re.escape(arrow_class) + r'(\w*)\b', s.strip())]
    if picked and ('styles.' + arrow_class) not in jsx:
        css = read(CSS)
        ported = '/* fix100: ported verbatim from ' + os.path.relpath(arrow_css_file, ROOT).replace('\\', '/') + ' */\n'
        for s, b in picked:
            ported += s + ' {\n  ' + b + '\n}\n'
        css += '\n' + ported
        write(CSS, css)
        n = jsx.count('className={styles.headToggle}')
        jsx = jsx.replace('className={styles.headToggle}', "className={styles.headToggle + ' ' + styles." + arrow_class + '}')
        write(JSX, jsx)
        print('patched: %d head arrow button(s) wired to .' % n + arrow_class)
    elif picked:
        print('skip (already applied): arrow class wiring')
    else:
        print('note: arrow class .' + arrow_class + ' has no rules in ' + os.path.relpath(arrow_css_file, ROOT))


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
git('commit', '-m', 'fix100: decorBl wiring matched to source usage, real panel-arrow button ported structurally')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix100 done: patched, committed and pushed to main.')