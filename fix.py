#!/usr/bin/env python3
# PATH: fix103.py
# GOLDEN SEED -- fix103: the notification dropdown isn't a layout bug, it's a
# broken design-token chain. fix71 rewrote the bell's CSS to reference
# --panel-bg, --panel-header, --accent, --accent-ink, --accent-soft, --warn,
# --warn-soft, --on-panel, --on-panel-soft and --on-panel-faint (and
# notificationCatalog.js reaches for --ok/--warn/--bad/--info too) -- but
# NONE of those names are ever defined in scope for <Header>. Every other
# page defines its own --panel-bg/--accent-style tokens on its own root
# `.container`, so those pages look fine; Header sits outside all of them,
# so every var() call silently fails and the dropdown paints with browser
# defaults -- which is exactly the washed-out, see-through, overlapping mess
# in the screenshot. Fix: (1) delete the dead fix70 duplicate rule block
# fix71 was appended alongside instead of replacing, keeping the one live
# rule (.notifWrap) it still held; (2) declare the missing tokens as local
# overrides on .header itself, using the same literal values the rest of
# the app already uses for panel surfaces / accent / status colors, so the
# bell finally matches every other panel in Golden Seed.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LAYOUT = os.path.join(ROOT, 'erp-frontend', 'src', 'components', 'layout')
CSS = os.path.join(LAYOUT, 'Header.module.css')


def read(p):
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


css = read(CSS)

# ═══ 1. remove the dead fix70 block, keep the one rule still in use ═══
old_block = (
    "/* NOTIFICATION DROPDOWN (fix70) */\n"
    ".notifWrap { position: relative; }\n"
    ".notifDrop {\n"
    "  position: absolute; top: calc(100% + 8px); right: 0; z-index: 500;\n"
    "  width: clamp(260px, 30vw, 360px);\n"
    "  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);\n"
    "  border: 1.5px solid rgba(238,140,58,0.35); border-radius: 10px;\n"
    "  box-shadow: 0 20px 50px rgba(0,0,0,0.55); overflow: hidden;\n"
    "  animation: dropIn 0.18s ease-out;\n"
    "}\n"
    "@keyframes dropIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }\n"
    ".notifHead { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.08); font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 900; letter-spacing: 2px; color: var(--orange); }\n"
    ".notifReadAll { display: inline-flex; align-items: center; gap: 4px; background: transparent; border: 1px solid rgba(255,255,255,0.15); color: rgba(255,255,255,0.6); border-radius: 6px; padding: 4px 8px; font-size: 8px; font-weight: 900; letter-spacing: 1px; cursor: pointer; }\n"
    ".notifReadAll:hover { color: #fff; border-color: var(--orange); }\n"
    ".notifEmpty { padding: 18px 12px; text-align: center; font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 900; letter-spacing: 2px; color: rgba(255,255,255,0.3); }\n"
    ".notifRow { display: flex; align-items: flex-start; gap: 8px; width: 100%; text-align: left; background: transparent; border: none; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 10px 12px; cursor: pointer; }\n"
    ".notifRow:hover { background: rgba(255,255,255,0.05); }\n"
    ".notifRead { opacity: 0.45; }\n"
    ".notifDot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }\n"
    ".notifMsg { font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.85); line-height: 1.4; word-break: break-word; }\n"
)
if old_block in css:
    css = css.replace(old_block, "/* NOTIFICATION DROPDOWN -- .notifWrap kept, dead fix70 rules removed by fix103 */\n.notifWrap { position: relative; }\n")
    print('undo: removed dead fix70 duplicate rule block (kept .notifWrap)')
elif '.notifWrap { position: relative; }' in css and '(fix70)' not in css:
    print('skip (already applied): fix70 block already removed')
else:
    print('FAIL: could not locate the fix70 block to remove')
    sys.exit(1)

# ═══ 2. give .header the local token overrides the bell actually needs ═══
if '--panel-bg:' in css.split('.notifWrap')[0] or re.search(r'\.header\s*\{[^}]*--panel-bg:', css):
    print('skip (already applied): .header token overrides')
else:
    anchor = (
        ".header {\n"
        "    height: var(--header-height, clamp(52px, 7vw, 64px));\n"
    )
    if anchor not in css:
        print('FAIL: .header rule anchor not found')
        sys.exit(1)
    tokens = (
        "    /* fix103: local overrides -- Header sits outside every page's\n"
        "       .container, so it can't inherit their page-scoped tokens. These\n"
        "       are the same literal values the rest of the app already uses. */\n"
        "    --panel-bg: linear-gradient(160deg, #1c3335 0%, #213E40 100%);\n"
        "    --panel-header: #162a2c;\n"
        "    --accent: var(--orange);\n"
        "    --accent-ink: var(--text-on-light, #1a2e30);\n"
        "    --accent-soft: rgba(238, 140, 58, 0.14);\n"
        "    --ok: #10b981;\n"
        "    --warn: #f59e0b;\n"
        "    --warn-soft: rgba(245, 158, 11, 0.12);\n"
        "    --bad: #ef4444;\n"
        "    --info: #06b6d4;\n"
        "    --on-panel: var(--text-on-dark, rgba(244, 242, 239, 0.82));\n"
        "    --on-panel-soft: var(--text-on-dark-soft, rgba(244, 242, 239, 0.72));\n"
        "    --on-panel-faint: rgba(244, 242, 239, 0.45);\n"
        + anchor
    )
    css = css.replace(anchor, tokens, 1)
    print('patched: declared --panel-bg/--panel-header/--accent*/--ok/--warn*/--bad/--info/--on-panel* on .header')

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
git('commit', '-m', 'fix103: notification dropdown was a broken token chain -- define --panel-bg/--panel-header/--accent*/--ok/--warn*/--bad/--info/--on-panel* locally on .header (Header inherits no page tokens), drop dead fix70 duplicate rules')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix103 done: patched, committed and pushed to main.')