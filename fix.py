#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix99b: repair fix99 (undo Charts.module.css mis-port), then
# re-discover the REAL panel deco + arrow code pages-first with word-boundary
# keywords, and finish: redundant line removed, search-before-arrow + icon
# gap, scope field inline dimensions, head margins, deco wiring.
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


# ═══ 1. UNDO the bad fix99 port ═══
css = read(CSS)
idx = css.find('/* fix99: ported verbatim from')
if idx >= 0:
    css = css[:idx].rstrip() + '\n'
    print('undo: removed mis-ported Charts block from Reports CSS')
else:
    print('undo: no ported block present (nothing to strip)')
write(CSS, css)

jsx = read(JSX)
bad = "className={styles.headToggle + ' ' + styles.barRows + ' ' + styles.barRow}"
n = jsx.count(bad)
if n:
    jsx = jsx.replace(bad, 'className={styles.headToggle}')
    print('undo: unwired barRows/barRow from %d button(s)' % n)
else:
    print('undo: buttons already clean')

# ═══ 2. RE-DISCOVER the real deco/arrow code (pages first, word boundaries) ═══
KEY_PANEL = re.compile(r'\b(corner|deco|frame)\b|::(before|after)', re.I)
KEY_ARROW = re.compile(r'\b(arrow|collapse|chevron|toggle)\b', re.I)
cands = []
pages_dir = os.path.join(SRC, 'pages')
if os.path.isdir(pages_dir):
    for d in sorted(os.listdir(pages_dir)):
        pd = os.path.join(pages_dir, d)
        if d == 'Reports' or not os.path.isdir(pd):
            continue
        for f in sorted(os.listdir(pd)):
            if f.endswith('.module.css'):
                cands.append(os.path.join(pd, f))
for dirpath, _dirs, files in os.walk(os.path.join(SRC, 'components')):
    for f in sorted(files):
        if f.endswith('.module.css'):
            cands.append(os.path.join(dirpath, f))

ref_file = None
panel_rules = []
arrow_rules = []
panel_classes = []
arrow_classes = []
for fp in cands:
    rules = re.findall(r'([^{}]+)\{([^}]*)\}', read(fp))
    pr = []
    ar = []
    for sel, body in rules:
        s = sel.strip()
        if not s or s.startswith('@'):
            continue
        if KEY_ARROW.search(s):
            ar.append((s, body.strip()))
        elif KEY_PANEL.search(s) and ('content:' in body or 'border' in body or 'background' in body):
            pr.append((s, body.strip()))
    if pr or ar:
        ref_file = fp
        panel_rules = pr
        arrow_rules = ar
        for s, _b in pr:
            base = re.findall(r'\.([A-Za-z0-9_-]+)', s)
            if base and base[0] not in panel_classes:
                panel_classes.append(base[0])
        for s, _b in ar:
            base = re.findall(r'\.([A-Za-z0-9_-]+)', s)
            if base and base[0] not in arrow_classes:
                arrow_classes.append(base[0])
        break

if ref_file:
    print('porting deco/arrow code verbatim from: ' + os.path.relpath(ref_file, ROOT))
    print('panel deco classes: ' + (', '.join(panel_classes) or '(none)'))
    print('arrow classes: ' + (', '.join(arrow_classes) or '(none)'))
    css = read(CSS)
    ported = '/* fix99b: ported verbatim from ' + os.path.relpath(ref_file, ROOT).replace('\\', '/') + ' */\n'
    for s, b in panel_rules + arrow_rules:
        ported += s + ' {\n  ' + b + '\n}\n'
    css += '\n' + ported
    write(CSS, css)
else:
    print('note: no deco/arrow rules discovered; checked %d stylesheets:' % len(cands))
    for fp in cands:
        print('  - ' + os.path.relpath(fp, ROOT))

# ═══ 3. redundant bottom line removed (correct guard this time) ═══
if 'No report applied yet' not in jsx:
    print('skip (already applied): redundant applied line removed')
else:
    old = ("      <div className={styles.appliedLine}>\n"
           "        {appliedDef\n"
           "          ? <>APPLIED: <b>{appliedDef.title}</b> &middot; {tableCols.length} columns &middot; sorted {sort.col || 'default'} {sort.dir} &middot; {entity ? entity.label + ' ' + entity.value : 'whole company'} &middot; {appliedDef.period ? periodHuman() : 'right now'}</>\n"
           "          : <>No report applied yet -- open a report above and press USE THIS REPORT.</>}\n"
           "      </div>\n")
    new = ("      {appliedDef && (\n"
           "        <div className={styles.appliedLine}>\n"
           "          APPLIED: <b>{appliedDef.title}</b> &middot; {tableCols.length} columns &middot; sorted {sort.col || 'default'} {sort.dir} &middot; {entity ? entity.label + ' ' + entity.value : 'whole company'} &middot; {appliedDef.period ? periodHuman() : 'right now'}\n"
           "        </div>\n"
           "      )}\n")
    if old not in jsx:
        print('FAIL: unknown state for redundant applied line')
        sys.exit(1)
    jsx = jsx.replace(old, new)
    print('patched: redundant applied line removed')

# ═══ 4. catalogue head: search first, arrow after, icon gap guaranteed ═══
if 'paddingLeft: 40' in jsx:
    print('skip (already applied): catalogue head order + icon gap')
else:
    old = ("          <button className={styles.headToggle} onClick={() => setCatOpen(o => !o)} aria-expanded={catOpen} aria-label=\"Collapse or expand catalogue panel\">\n"
           "            <FiChevronDown className={catOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
           "          </button>\n"
           "          <div className={styles.searchBox}>\n"
           "            <FiSearch className={styles.searchIcon} aria-hidden=\"true\" />\n"
           "            <input value={search} onChange={e => setSearch(e.target.value)} placeholder=\"Search reports...\" aria-label=\"Search reports\" />\n"
           "            {search && <button className={styles.searchClear} onClick={() => setSearch('')} aria-label=\"Clear search\"><FiX size={13} aria-hidden=\"true\" /></button>}\n"
           "          </div>\n")
    new = ("          <div className={styles.searchBox}>\n"
           "            <FiSearch className={styles.searchIcon} aria-hidden=\"true\" />\n"
           "            <input value={search} onChange={e => setSearch(e.target.value)} placeholder=\"Search reports...\" aria-label=\"Search reports\" style={{ paddingLeft: 40 }} />\n"
           "            {search && <button className={styles.searchClear} onClick={() => setSearch('')} aria-label=\"Clear search\"><FiX size={13} aria-hidden=\"true\" /></button>}\n"
           "          </div>\n"
           "          <button className={styles.headToggle} onClick={() => setCatOpen(o => !o)} aria-expanded={catOpen} aria-label=\"Collapse or expand catalogue panel\">\n"
           "            <FiChevronDown className={catOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
           "          </button>\n")
    if old not in jsx:
        print('FAIL: unknown state for catalogue head order')
        sys.exit(1)
    jsx = jsx.replace(old, new)
    print('patched: catalogue head order + icon gap')

# ═══ 5. scope field inline dimensions ═══
if 'boxSizing' in jsx:
    print('skip (already applied): scope field inline dimensions')
else:
    old = "                  className={styles.entInput}\n"
    new = ("                  className={styles.entInput}\n"
           "                  style={{ height: 36, width: 'clamp(200px, 22vw, 260px)', boxSizing: 'border-box' }}\n")
    if old not in jsx:
        print('FAIL: unknown state for scope field input')
        sys.exit(1)
    jsx = jsx.replace(old, new)
    print('patched: scope field inline dimensions')

# ═══ 6. wire discovered deco/arrow classes (after all reorders) ═══
if ref_file:
    psuf = ''.join(" + ' ' + styles." + c for c in panel_classes)
    asuf = ''.join(" + ' ' + styles." + c for c in arrow_classes)
    if psuf and 'styles.scopePanel +' not in jsx:
        jsx = jsx.replace("      <div className={styles.scopePanel}>\n",
                          "      <div className={styles.scopePanel" + psuf + "}>\n", 1)
        jsx = jsx.replace("      <div className={catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.catPanelClosed}>\n",
                          "      <div className={(catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.catPanelClosed)" + psuf + "}>\n", 1)
        print('patched: panel deco classes wired')
    elif psuf:
        print('skip (already applied): panel deco classes')
    if asuf and 'styles.headToggle +' not in jsx:
        n = jsx.count('className={styles.headToggle}')
        jsx = jsx.replace('className={styles.headToggle}', 'className={styles.headToggle' + asuf + '}')
        print('patched: %d head arrow button(s) wired' % n)
    elif asuf:
        print('skip (already applied): head arrow classes')
write(JSX, jsx)

# ═══ 7. catalogue head margins ═══
css = read(CSS)
if '.catPanel .searchBox { margin-left: auto; }' in css:
    print('skip (already applied): catalogue head margins')
elif '.catPanel .searchBox { margin-left: 10px; }' in css:
    css = css.replace('.catPanel .searchBox { margin-left: 10px; }',
                      '.catPanel .searchBox { margin-left: auto; }\n.catPanel .headToggle { margin-left: 10px; }')
    print('patched: catalogue head margins')
else:
    css += '\n.catPanel .searchBox { margin-left: auto; }\n.catPanel .headToggle { margin-left: 10px; }\n'
    print('added: catalogue head margins')
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
git('commit', '-m', 'fix99b: undo Charts mis-port, port real page deco + arrows, finish head order, icon gap, scope field, redundant line')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix99b done: patched, committed and pushed to main.')