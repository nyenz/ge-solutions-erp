#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix101: remove every mis-ported deco/arrow fragment, then
# build the Intake decoration spec directly: corner brackets bottom-left /
# bottom-right, orange dot row under each panel, and the Intake head-arrow
# button (30px dark square, orange border, orange chevron).
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(ROOT, 'erp-frontend', 'src', 'pages', 'Reports')
JSX = os.path.join(REPORTS, 'ReportStudio.jsx')
CSS = os.path.join(REPORTS, 'ReportStudio.module.css')


def read(p):
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


def rule_replace(css, selector, body):
    pat = re.compile(re.escape(selector) + r'\s*\{[^}]*\}')
    repl = selector + ' {\n  ' + body + '\n}'
    if pat.search(css):
        return pat.sub(lambda m: repl, css, count=1), 'rewrote rule ' + selector
    return css + '\n' + repl + '\n', 'added rule ' + selector


# ═══ 1. strip all ported fragments ═══
css = read(CSS)
cuts = [i for i in (css.find('/* fix99b: ported verbatim from'), css.find('/* fix100: ported verbatim from')) if i >= 0]
if cuts:
    css = css[:min(cuts)].rstrip() + '\n'
    print('undo: removed ported deco/arrow CSS blocks')
else:
    print('undo: no ported blocks present')
css, m = rule_replace(css, '.headToggle',
                      "margin-left: auto; display: inline-flex; align-items: center; justify-content: center; "
                      "width: 30px; height: 30px; border-radius: 6px; cursor: pointer; flex-shrink: 0; "
                      "border: 1.5px solid #EE8C3A; background: #162a2c; color: #EE8C3A; transition: all 0.2s ease;")
print(m)
css, m = rule_replace(css, '.headToggle svg',
                      "width: 14px; height: 14px; transition: transform 0.2s;")
print(m)

# ═══ 2. Intake decoration spec (brackets + dot row) ═══
if '.decoCornerBL' in css:
    print('skip (already applied): deco rules')
else:
    if '@media (max-width: 900px) {' not in css:
        print('FAIL: media query anchor missing')
        sys.exit(1)
    css = css.replace('@media (max-width: 900px) {',
                      ".scopePanel, .catPanel { position: relative; }\n"
                      ".decoCornerBL, .decoCornerBR { position: absolute; bottom: -8px; width: 14px; height: 14px; pointer-events: none; }\n"
                      ".decoCornerBL { left: -8px; border-left: 2px solid rgba(238, 140, 58, 0.55); border-bottom: 2px solid rgba(238, 140, 58, 0.55); }\n"
                      ".decoCornerBR { right: -8px; border-right: 2px solid rgba(238, 140, 58, 0.55); border-bottom: 2px solid rgba(238, 140, 58, 0.55); }\n"
                      ".decoDots { position: absolute; bottom: -16px; left: 50%; transform: translateX(-50%); width: 45px; height: 4px; "
                      "pointer-events: none; background: radial-gradient(circle, #EE8C3A 1.5px, transparent 2px) repeat-x left center; background-size: 9px 4px; }\n"
                      "@media (max-width: 900px) {", 1)
    print('patched: deco rules (brackets + dot row)')
write(CSS, css)

# ═══ 3. JSX: clean wirings, insert deco elements ═══
jsx = read(JSX)
jsx = re.sub(r'[ \t]*<div className=\{styles\.decorBl\}[^>]*></div>\n', '', jsx)
n = jsx.count(" + ' ' + styles.decorBl}")
if n:
    jsx = jsx.replace(" + ' ' + styles.decorBl}", '}')
    print('undo: removed decorBl from %d panel class list(s)' % n)
n = len(re.findall(r"className=\{styles\.headToggle \+ ' ' \+ styles\.\w+\}", jsx))
if n:
    jsx = re.sub(r"className=\{styles\.headToggle \+ ' ' \+ styles\.\w+\}", 'className={styles.headToggle}', jsx)
    print('undo: removed ported arrow class from %d button(s)' % n)

if 'decoCornerBL' in jsx:
    print('skip (already applied): deco elements')
else:
    deco = ("        <i className={styles.decoCornerBL} aria-hidden=\"true\"></i>\n"
            "        <i className={styles.decoCornerBR} aria-hidden=\"true\"></i>\n"
            "        <i className={styles.decoDots} aria-hidden=\"true\"></i>\n")
    jsx, c1 = re.subn(r'(      <div className=\{styles\.scopePanel[^>]*>\n)', r'\1' + deco, jsx, count=1)
    jsx, c2 = re.subn(r'(      <div className=\{\(catOpen[^>]*>\n)', r'\1' + deco, jsx, count=1)
    if c1 + c2 < 2:
        print('FAIL: could not locate both panel opening tags')
        sys.exit(1)
    print('patched: deco elements inserted in %d panels' % (c1 + c2))
write(JSX, jsx)


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
git('commit', '-m', 'fix101: Intake deco spec built directly -- corner brackets, dot row, proper head arrow; mis-ported fragments removed')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix101 done: patched, committed and pushed to main.')