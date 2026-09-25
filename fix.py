#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix98b: completes fix98 (live row counters on report cards,
# footer scope line, counter styling). Corrected patterns (no phantom line
# breaks), fully guarded and re-runnable. Commits the already-applied fix98
# pipeline together with these last pieces and pushes.
import os
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


def guarded(src, old, new, marker, label):
    if marker in src:
        print('skip (already applied): ' + label)
        return src
    if old not in src:
        print('FAIL: unknown state for ' + label)
        print('Expected pattern:\n' + old)
        sys.exit(1)
    print('patched: ' + label)
    return src.replace(old, new)


jsx = read(JSX)
jsx = guarded(jsx,
              "<span className={styles.r1}>{def.title}<span className={styles.tag}>",
              "<span className={styles.r1}>{def.title}<span className={styles.liveCount}>{liveCount(def)} ROWS</span><span className={styles.tag}>",
              '{liveCount(def)} ROWS', 'report card live counter')
jsx = guarded(jsx,
              "<span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.tag}>",
              "<span className={styles.r1}>DEFAULT VIEW: {defaultDef.title}<span className={styles.liveCount}>{liveCount(defaultDef)} ROWS</span><span className={styles.tag}>",
              '{liveCount(defaultDef)} ROWS', 'default row live counter')
jsx = guarded(jsx,
              "          {entity ? ' for ' + entity.label.toLowerCase() + ' ' + entity.value : ' for the whole company'}\n",
              "          {entity ? ' for ' + entity.label.toLowerCase() + ' ' + entity.value : ' for the whole company'}\n"
              "          {' · ' + scopeRows.length + ' of ' + rows.length + ' rows in scope'}\n",
              'rows in scope', 'footer scope line')
write(JSX, jsx)

css = read(CSS)
if '.liveCount {' in css:
    print('skip (already applied): liveCount styling')
else:
    if '@media (max-width: 900px) {' not in css:
        print('FAIL: media query anchor missing in CSS')
        sys.exit(1)
    css = css.replace('@media (max-width: 900px) {',
                      ".liveCount { margin-left: 8px; font-family: 'Space Mono', monospace; font-size: 8px; "
                      "letter-spacing: 1px; color: rgba(26,46,48,0.55); white-space: nowrap; }\n"
                      ".catRow:hover .liveCount, .catRowOn .liveCount { color: rgba(255,255,255,0.85); }\n"
                      "@media (max-width: 900px) {", 1)
    print('patched: liveCount styling')
write(CSS, css)


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
git('commit', '-m', 'fix98b: complete fix98 -- live row counters on cards, footer scope line, counter styling (carries fix98 pipeline)')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix98b done: patched, committed and pushed to main.')