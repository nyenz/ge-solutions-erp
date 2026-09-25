#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix97b: state-tolerant completion of fix97.
# Rewrites whole CSS rules by selector (immune to previous partial runs) and
# guards every JSX/CSS change: already applied -> skip, old form -> replace,
# unknown -> stop with a clear message. Safe to re-run.
# Then adds, commits and pushes by itself.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(ROOT, 'erp-frontend', 'src', 'pages', 'Reports')
CSS = os.path.join(REPORTS, 'ReportStudio.module.css')
JSX = os.path.join(REPORTS, 'ReportStudio.jsx')


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


css = read(CSS)

# ── search field family: whole-rule rewrite, any prior variant normalised ──
css, m = rule_replace(css, '.searchIcon',
                      "position: absolute; left: 12px; top: 50%; transform: translateY(-50%); "
                      "width: 15px; height: 15px; color: #EE8C3A; pointer-events: none;")
print(m)
css, m = rule_replace(css, '.searchBox',
                      "box-sizing: border-box; position: relative; display: flex; align-items: center; "
                      "height: 36px; width: clamp(200px, 22vw, 260px); background: #fff; "
                      "border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto;")
print(m)
css, m = rule_replace(css, '.searchBox input',
                      "flex: 1; width: 100%; height: 34px; border: none; outline: none; "
                      "background: transparent; padding: 0 12px 0 40px; font-family: 'Inter', sans-serif; "
                      "font-size: 12px; font-weight: 700; color: #1a2e30; line-height: 34px;")
print(m)

# ── selected report row contrast splits (guarded, soft) ──
splits = [
    (".catRow:hover, .catRowOn { background: #EE8C3A; color: #fff; }",
     ".catRow:hover { background: #EE8C3A; color: #fff; }\n.catRowOn { background: #d97e2f; color: #1a2e30; }",
     ".catRowOn { background: #d97e2f;"),
    (".catRow:hover .r1, .catRowOn .r1 { color: #fff; }",
     ".catRow:hover .r1 { color: #fff; }\n.catRowOn .r1 { color: #1a2e30; }",
     ".catRowOn .r1 { color: #1a2e30; }"),
    (".catRow:hover .r2, .catRowOn .r2 { color: rgba(255,255,255,0.85); }",
     ".catRow:hover .r2 { color: rgba(255,255,255,0.85); }\n.catRowOn .r2 { color: rgba(26,46,48,0.72); }",
     ".catRowOn .r2 { color: rgba(26,46,48,0.72); }"),
    (".catRowDef:hover, .catRowDef.catRowOn { background: #EE8C3A; }",
     ".catRowDef:hover { background: #EE8C3A; }\n.catRowDef.catRowOn { background: #d97e2f; }",
     ".catRowDef.catRowOn { background: #d97e2f; }"),
]
for old, new, mark in splits:
    if mark in css:
        print('skip (already applied): ' + old[:40] + '...')
    elif old in css:
        css = css.replace(old, new)
        print('patched: ' + old[:40] + '...')
    else:
        print('note: pattern not present (skipped): ' + old[:40] + '...')

# ── fix97 block (placeholder, toggles, panel decor) inserted once ──
if '.viewerEmpty {' not in css:
    BLOCK = (
        "/* fix97: prototype parity -- canonical field dims last, empty preview\n"
        "   placeholder, head toggles, panel bottom edge + corner ticks. */\n"
        ".entInput, .searchBox { box-sizing: border-box; height: 36px; width: clamp(200px, 22vw, 260px); }\n"
        ".viewerEmpty {\n"
        "  border: 2px dashed rgba(26, 46, 48, 0.28); border-radius: 10px;\n"
        "  background: rgba(255, 255, 255, 0.35);\n"
        "  padding: clamp(24px, 4vw, 40px) 16px;\n"
        "  display: flex; align-items: center; justify-content: center; text-align: center;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 1vw, 11px); font-weight: 900;\n"
        "  letter-spacing: 2px; text-transform: uppercase; color: rgba(26, 46, 48, 0.45);\n"
        "}\n"
        ".headToggle {\n"
        "  margin-left: auto; display: inline-flex; align-items: center; justify-content: center;\n"
        "  width: 28px; height: 28px; border-radius: 6px; cursor: pointer; flex-shrink: 0;\n"
        "  border: 1.5px solid rgba(238, 140, 58, 0.45); background: rgba(238, 140, 58, 0.12);\n"
        "  color: #EE8C3A; transition: all 0.2s ease;\n"
        "}\n"
        ".headToggle:hover { background: #EE8C3A; color: #1a2e30; }\n"
        ".headToggle svg { transition: transform 0.2s; }\n"
        ".catPanel .searchBox { margin-left: 10px; }\n"
        ".panelClosed { display: none; }\n"
        ".catPanelClosed > *:not(.panelHeadRow) { display: none; }\n"
        ".scopePanel, .catPanel { position: relative; border-bottom: 1.5px solid #EE8C3A; }\n"
        ".scopePanel::before, .catPanel::before,\n"
        ".scopePanel::after, .catPanel::after {\n"
        "  content: ''; position: absolute; bottom: -1.5px; width: 14px; height: 14px;\n"
        "  border-bottom: 2.5px solid #EE8C3A; pointer-events: none;\n"
        "}\n"
        ".scopePanel::before, .catPanel::before { left: -1.5px; border-left: 2.5px solid #EE8C3A; border-bottom-left-radius: 12px; }\n"
        ".scopePanel::after, .catPanel::after { right: -1.5px; border-right: 2.5px solid #EE8C3A; border-bottom-right-radius: 12px; }\n"
        "@media (max-width: 900px) {")
    if '@media (max-width: 900px) {' not in css:
        print('FAIL: media query anchor missing in CSS')
        sys.exit(1)
    css = css.replace('@media (max-width: 900px) {', BLOCK, 1)
    print('patched: fix97 CSS block inserted')
else:
    print('skip (already applied): fix97 CSS block')
write(CSS, css)

# ── JSX changes, each guarded so partial states survive ──
jsx = read(JSX)
jsx = guarded(jsx,
              "  const [chartOpen, setChartOpen] = useState(false);\n",
              "  const [chartOpen, setChartOpen] = useState(false);\n"
              "  const [scopeOpen, setScopeOpen] = useState(true);\n"
              "  const [catOpen, setCatOpen] = useState(true);\n",
              'setScopeOpen', 'collapse states')
jsx = guarded(jsx,
              "        <div className={styles.panelHeadRow}>\n"
              "          <span className={styles.scopeTitle}>SCOPE</span>\n"
              "        </div>\n"
              "        <div className={styles.scopeBody}>\n",
              "        <div className={styles.panelHeadRow}>\n"
              "          <span className={styles.scopeTitle}>SCOPE</span>\n"
              "          <button className={styles.headToggle} onClick={() => setScopeOpen(o => !o)} aria-expanded={scopeOpen} aria-label=\"Collapse or expand scope panel\">\n"
              "            <FiChevronDown className={scopeOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
              "          </button>\n"
              "        </div>\n"
              "        <div className={scopeOpen ? styles.scopeBody : styles.panelClosed}>\n",
              'Collapse or expand scope panel', 'scope head toggle')
jsx = guarded(jsx,
              "      <div className={styles.catPanel}>\n",
              "      <div className={catOpen ? styles.catPanel : styles.catPanel + ' ' + styles.catPanelClosed}>\n",
              'catPanelClosed}>', 'catalogue collapse class')
jsx = guarded(jsx,
              "          <span className={styles.badge}>{searched.length} MATCHES</span>\n"
              "          <div className={styles.searchBox}>\n",
              "          <span className={styles.badge}>{searched.length} MATCHES</span>\n"
              "          <button className={styles.headToggle} onClick={() => setCatOpen(o => !o)} aria-expanded={catOpen} aria-label=\"Collapse or expand catalogue panel\">\n"
              "            <FiChevronDown className={catOpen ? styles.pickIconOpen : ''} aria-hidden=\"true\" />\n"
              "          </button>\n"
              "          <div className={styles.searchBox}>\n",
              'Collapse or expand catalogue panel', 'catalogue head toggle')
jsx = guarded(jsx,
              "      <div className={styles.appliedLine}>\n",
              "      {!appliedDef && (\n"
              "        <div className={styles.viewerEmpty}>\n"
              "          PICK A REPORT ABOVE -- ITS LIVE CHART, PREVIEW, CSV AND PDF LAND HERE\n"
              "        </div>\n"
              "      )}\n"
              "\n"
              "      <div className={styles.appliedLine}>\n",
              'styles.viewerEmpty', 'dashed empty preview placeholder')
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
git('commit', '-m', 'fix97b: state-tolerant completion of fix97 -- search field rules normalised, placeholder, toggles, panel decor, selected-row contrast')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix97b done: patched, committed and pushed to main.')