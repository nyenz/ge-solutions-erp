#!/usr/bin/env python3
# PATH: fix102.py
# GOLDEN SEED -- fix102: fix101 invented its own bottom-corner-bracket +
# dot-row CSS/markup from scratch for Reports, so it never actually matched
# the rest of the app. The real deco is a single shared component,
# <CornerDecor>, already used by HardwarePanel and CollapsibleSection (the
# Intake page panels are CollapsibleSections). This patch removes fix101's
# bespoke .decoCornerBL/.decoCornerBR/.decoDots fragments and wires Reports'
# two panels (scopePanel, catPanel) to render the real <CornerDecor hideTop />
# -- same corner brackets + same bottom pin row every other page uses.
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


# ═══ 1. CSS: strip fix101's invented deco rules, keep position:relative ═══
css = read(CSS)
if '.decoCornerBL' in css:
    before = css
    css = css.replace(
        ".decoCornerBL, .decoCornerBR { position: absolute; bottom: -8px; width: 14px; height: 14px; pointer-events: none; }\n"
        ".decoCornerBL { left: -8px; border-left: 2px solid rgba(238, 140, 58, 0.55); border-bottom: 2px solid rgba(238, 140, 58, 0.55); }\n"
        ".decoCornerBR { right: -8px; border-right: 2px solid rgba(238, 140, 58, 0.55); border-bottom: 2px solid rgba(238, 140, 58, 0.55); }\n"
        ".decoDots { position: absolute; bottom: -16px; left: 50%; transform: translateX(-50%); width: 45px; height: 4px; "
        "pointer-events: none; background: radial-gradient(circle, #EE8C3A 1.5px, transparent 2px) repeat-x left center; background-size: 9px 4px; }\n",
        "")
    if css != before:
        print('undo: removed fix101 bespoke .decoCornerBL/.decoCornerBR/.decoDots CSS')
    else:
        print('FAIL: could not locate fix101 deco CSS block to remove')
        sys.exit(1)
else:
    print('skip: no bespoke deco CSS present')

if '.scopePanel, .catPanel { position: relative; }' not in css:
    print('FAIL: expected ".scopePanel, .catPanel { position: relative; }" anchor missing')
    sys.exit(1)
print('keep: .scopePanel, .catPanel { position: relative; } (CornerDecor needs a positioned ancestor)')
write(CSS, css)

# ═══ 2. JSX: swap the invented <i> deco trio for the real <CornerDecor> ═══
jsx = read(JSX)

if "import CornerDecor from '../../components/ui/CornerDecor';" not in jsx:
    jsx = jsx.replace(
        "import styles from './ReportStudio.module.css';",
        "import CornerDecor from '../../components/ui/CornerDecor';\n"
        "import styles from './ReportStudio.module.css';",
        1)
    print('patched: imported the real CornerDecor component')
else:
    print('skip (already applied): CornerDecor import')

deco_i_block = re.compile(
    r'[ \t]*<i className=\{styles\.decoCornerBL\}[^\n]*\n'
    r'[ \t]*<i className=\{styles\.decoCornerBR\}[^\n]*\n'
    r'[ \t]*<i className=\{styles\.decoDots\}[^\n]*\n'
)
jsx, n = deco_i_block.subn(lambda m: '        <CornerDecor hideTop />\n', jsx)
if n:
    print('patched: replaced invented deco markup with <CornerDecor hideTop /> in %d panel(s)' % n)
elif '<CornerDecor hideTop />' in jsx:
    print('skip (already applied): CornerDecor markup')
else:
    print('FAIL: could not locate invented deco markup to replace')
    sys.exit(1)

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
git('commit', '-m', 'fix102: Reports panel deco now reuses the real shared CornerDecor component (same as Intake/HardwarePanel), replacing fix101\'s bespoke bracket+dot CSS')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix102 done: patched, committed and pushed to main.')