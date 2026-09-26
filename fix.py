#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix104: repair the header glitch + notification styling.
# Concretises every design token in the header stylesheet (broken chain from
# fix103), then guarantees: sticky dark flex-row header bar, bell button,
# red badge, notification dropdown panel. Idempotent and re-runnable.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'erp-frontend', 'src')

TOKENS = {
    '--panel-bg': '#162a2c',
    '--panel-header': '#101f21',
    '--panel-head': '#101f21',
    '--accent': '#EE8C3A',
    '--accent-soft': 'rgba(238, 140, 58, 0.14)',
    '--accent-dim': 'rgba(238, 140, 58, 0.45)',
    '--ok': '#2ecc8f',
    '--warn': '#EE8C3A',
    '--bad': '#e5484d',
    '--info': '#38bdf8',
    '--on-panel': '#ffffff',
    '--on-panel-soft': 'rgba(255, 255, 255, 0.72)',
    '--on-panel-faint': 'rgba(255, 255, 255, 0.45)',
}

# ═══ 1. find the header stylesheet ═══
cands = []
for dirpath, _dirs, files in os.walk(SRC):
    for f in sorted(files):
        if f.endswith('.module.css'):
            fp = os.path.join(dirpath, f)
            cands.append((0 if 'header' in f.lower() else 1, fp))
cands.sort()
header_css = None
for _prio, fp in cands:
    with open(fp, 'r', encoding='utf-8') as fh:
        body = fh.read()
    if re.search(r'\.(header|appHeader|topBar|headerBar)\s*(,|\{)', body):
        header_css = fp
        break
if not header_css:
    print('FAIL: no header stylesheet found under erp-frontend/src')
    sys.exit(1)
print('header stylesheet: ' + os.path.relpath(header_css, ROOT))

with open(header_css, 'r', encoding='utf-8') as f:
    css = f.read()

# ═══ 2. concretise tokens (kill the broken var chain) ═══
def detok(m):
    return TOKENS.get(m.group(1), m.group(0))
css, nt = re.subn(r'var\(\s*(--[\w-]+)\s*(?:,[^)]*)?\)', detok, css)
print('tokens concretised: %d occurrence(s)' % nt)


def ensure_rule(css, sel_regex, canonical, label, needs):
    pat = re.compile(r'(' + sel_regex + r'\s*(?:,[^{]*)?\{)([^}]*)(\})')
    m = pat.search(css)
    if m and all(k in m.group(2) for k in needs):
        print('skip (already healthy): ' + label)
        return css
    if m:
        css = pat.sub(lambda mm: mm.group(1) + '\n  ' + canonical + '\n', css, count=1)
        print('rebuilt rule: ' + label)
    else:
        css += '\n.' + label.split(' ')[0] + ' {\n  ' + canonical + '\n}\n'
        print('added rule: ' + label)
    return css


HEADER_BODY = ("position: sticky; top: 0; left: 0; right: 0; z-index: 80; "
               "display: flex; align-items: center; gap: 12px; min-height: 64px; "
               "padding: 8px 18px; background: #162a2c; "
               "border-bottom: 1.5px solid rgba(238, 140, 58, 0.35); "
               "box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);")
css = ensure_rule(css, r'\.(header|appHeader|topBar|headerBar)', HEADER_BODY,
                  'header bar', ['display: flex', 'background'])

BELL_BODY = ("position: relative; display: inline-flex; align-items: center; "
             "justify-content: center; width: 40px; height: 40px; border-radius: 8px; "
             "border: 1.5px solid rgba(238, 140, 58, 0.45); background: rgba(238, 140, 58, 0.12); "
             "color: #EE8C3A; cursor: pointer; flex-shrink: 0;")
css = ensure_rule(css, r'\.(bell|notifBtn|bellBtn)\w*', BELL_BODY,
                  'bell button', ['position: relative', 'display: inline-flex'])

BADGE_BODY = ("position: absolute; top: -5px; right: -5px; min-width: 18px; height: 18px; "
              "border-radius: 9px; background: #e5484d; color: #fff; "
              "font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 700; "
              "display: inline-flex; align-items: center; justify-content: center; "
              "padding: 0 4px; border: 1.5px solid #162a2c;")
css = ensure_rule(css, r'\.(bellBadge|notifBadge|badge)\w*', BADGE_BODY,
                  'bell badge', ['position: absolute'])

DROP_BODY = ("position: absolute; top: calc(100% + 8px); right: 0; z-index: 90; "
             "min-width: 320px; max-width: 380px; background: #162a2c; "
             "border: 1.5px solid rgba(238, 140, 58, 0.35); border-radius: 10px; "
             "box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35); overflow: hidden;")
css = ensure_rule(css, r'\.(notif|bell)\w*(Panel|Drop|List|Menu|Box|Pop)\w*', DROP_BODY,
                  'notification dropdown', ['position: absolute'])

with open(header_css, 'w', encoding='utf-8', newline='\n') as f:
    f.write(css)
print('written: ' + os.path.relpath(header_css, ROOT))


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
git('commit', '-m', 'fix104: header bar restored (sticky dark flex row), tokens concretised, bell + badge + notification dropdown styling repaired')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix104 done: patched, committed and pushed to main.')