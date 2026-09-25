#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix95:
# 1. Dropdown lists scroll but hide the scrollbar (prototype behaviour).
# 2. Scope who/what field gets the exact catalogue-search dimensions, both
#    rules now box-sizing: border-box so edits actually render.
# 3. Catalogue report titles use the theme soft grey, white on hover.
# Then adds, commits and pushes by itself.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CSS = os.path.join(ROOT, 'erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')


def replace(file_path, old, new):
    with open(file_path, 'r', encoding='utf-8') as f:
        src = f.read()
    if old not in src:
        print('FAIL: pattern not found in ' + os.path.relpath(file_path, ROOT))
        print('Old pattern:\n' + old)
        sys.exit(1)
    src = src.replace(old, new)
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src)
    print('patched: ' + os.path.relpath(file_path, ROOT))


# ── 1. scrollable dropdowns with hidden scrollbars ──
replace(CSS,
        ".ddScroll { padding: 0; }",
        ".ddScroll { max-height: 264px; overflow-y: auto; padding: 0; scrollbar-width: none; -ms-overflow-style: none; }")
replace(CSS,
        ".ddScroll::-webkit-scrollbar { width: 6px; }",
        ".ddScroll::-webkit-scrollbar { width: 0; height: 0; display: none; }")
replace(CSS,
        ".ddScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }",
        ".ddScroll::-webkit-scrollbar-thumb { background: transparent; }")

# ── 2. one shared dimension token set for both search fields, border-box ──
replace(CSS,
        ".entInput { height: 34px; width: clamp(220px, 26vw, 320px); padding: 0 12px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; transition: all 0.2s; }",
        ".entInput { box-sizing: border-box; flex: 0 0 auto; height: 36px; width: clamp(200px, 22vw, 260px); padding: 0 12px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; transition: border-color 0.2s, box-shadow 0.2s; }")
replace(CSS,
        ".searchBox { position: relative; display: flex; align-items: center; height: 36px; width: clamp(200px, 22vw, 260px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }",
        ".searchBox { box-sizing: border-box; position: relative; display: flex; align-items: center; height: 36px; width: clamp(200px, 22vw, 260px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }")

# ── 3. report titles on theme soft grey, white on hover/active ──
replace(CSS,
        ".r1 { display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }",
        ".r1 { display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #5b6f70; }")
replace(CSS,
        ".catRow:hover .r2, .catRowOn .r2 { color: rgba(255,255,255,0.85); }",
        ".catRow:hover .r1, .catRowOn .r1 { color: #fff; }\n"
        ".catRow:hover .r2, .catRowOn .r2 { color: rgba(255,255,255,0.85); }")


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
git('commit', '-m', 'fix95: hidden-scrollbar dropdowns, scope search mirrors catalogue search (border-box), report titles on theme grey')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix95 done: patched, committed and pushed to main.')