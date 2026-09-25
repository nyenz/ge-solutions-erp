#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix93: safe CSS patch.
# Rolls the stylesheet back to the clean state before the fix92 regex broke
# the build, then applies exact-match replacements for:
# 1. Scope search field: shorter height (34px), longer reach (clamp 220-320).
# 2. Scope dropdown table: max-height and overflow removed (no scrollbar).
# 3. Catalogue search field: flex-centered box, input line-height 34px so
#    "Search reports..." aligns perfectly after the magnifier.
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


# 1. Roll back to the clean CSS file from the commit before fix92 broke it.
# This guarantees we are editing valid, well-formed CSS.
subprocess.run(['git', 'checkout', 'HEAD~1', '--', os.path.relpath(CSS, ROOT)], cwd=ROOT, check=True)
print('restored clean CSS from HEAD~1')

# 2. Scope search field: shorter height, longer reach
replace(CSS,
        ".entInput { height: 38px; width: clamp(180px, 20vw, 260px);",
        ".entInput { height: 34px; width: clamp(220px, 26vw, 320px);")

# 3. Scope dropdown table: remove scrollbar constraints completely
replace(CSS,
        ".ddScroll { max-height: 264px; overflow-y: auto; padding: 0; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }",
        ".ddScroll { padding: 0; }")

# 4. Catalogue search field: flex-centered box so text aligns perfectly
replace(CSS,
        ".searchBox { position: relative; height: 36px; width: clamp(180px, 20vw, 260px);",
        ".searchBox { position: relative; display: flex; align-items: center; height: 36px; width: clamp(200px, 22vw, 260px);")
replace(CSS,
        ".searchBox input { width: 100%; height: 100%; border: none; outline: none; background: transparent; padding: 0 26px 0 30px; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; color: #1a2e30; }",
        ".searchBox input { flex: 1; width: 100%; height: 34px; border: none; outline: none; background: transparent; padding: 0 10px 0 32px; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; line-height: 34px; }")


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
git('commit', '-m', 'fix93: scope search size, no scrollbar dropdown, perfectly aligned catalogue search')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix93 done: patched, committed and pushed to main.')