#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix94: source tabs become the app's deactivated filter chips.
# Other pages draw filter rows directly on the cream page: solid slate
# (#4d5c5a) chips for deactivated filters, orange chip for the active one.
# The Reports source row now matches that family 1-to-1: band removed,
# slate chips in, orange active chip, 10px gaps.
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


# 1. holder loses the band: row sits on the cream page like other filter rows
replace(CSS,
        ".sourcePanel {\n"
        "  flex: 0 0 auto; display: flex; align-items: center;\n"
        "  background: #3e595b;\n"
        "  border: 1.5px solid rgba(255, 255, 255, 0.08); border-radius: 8px;\n"
        "  padding: 4px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
        "}\n",
        ".sourcePanel {\n"
        "  flex: 0 1 auto; display: flex; align-items: center;\n"
        "  background: transparent;\n"
        "  border: none; border-radius: 0;\n"
        "  padding: 0; box-shadow: none;\n"
        "}\n")

# 2 + 3 + 4. deactivated slate chips, orange active chip, 10px gaps
replace(CSS,
        ".tileRow { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }\n"
        ".tile {\n"
        "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
        "  letter-spacing: 1.5px; text-transform: uppercase;\n"
        "  padding: 8px 12px; border-radius: 6px;\n"
        "  border: 1.5px solid transparent; background: transparent;\n"
        "  color: rgba(255,255,255,0.8); transition: color 0.2s ease;\n"
        "}\n"
        ".tile:hover { color: #EE8C3A; }\n"
        ".tileActive {\n"
        "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
        "  letter-spacing: 1.5px; text-transform: uppercase;\n"
        "  padding: 8px 14px; border-radius: 6px;\n"
        "  border: 1.5px solid #EE8C3A; background: #EE8C3A; color: #1a2e30;\n"
        "  box-shadow: 0 4px 16px rgba(238,140,58,0.3);\n"
        "}\n",
        ".tileRow { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }\n"
        ".tile {\n"
        "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
        "  letter-spacing: 1.5px; text-transform: uppercase;\n"
        "  padding: 12px 22px; border-radius: 8px;\n"
        "  border: 1.5px solid transparent; background: #4d5c5a;\n"
        "  color: rgba(255,255,255,0.92); transition: background 0.2s ease, color 0.2s ease;\n"
        "}\n"
        ".tile:hover { background: #5a6b68; color: #fff; }\n"
        ".tileActive {\n"
        "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
        "  letter-spacing: 1.5px; text-transform: uppercase;\n"
        "  padding: 12px 24px; border-radius: 8px;\n"
        "  border: 1.5px solid #EE8C3A; background: #EE8C3A; color: #1a2e30;\n"
        "  box-shadow: 0 4px 16px rgba(238,140,58,0.3);\n"
        "}\n")


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
git('commit', '-m', 'fix94: source tabs = deactivated filter chips from other pages (slate on cream, orange active), band removed')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix94 done: patched, committed and pushed to main.')