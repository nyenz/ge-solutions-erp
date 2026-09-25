#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix96:
# 1. Source row back to prototype format: solid slate band (#4d5c5a) hugging
#    flat text tabs, orange active pill inside, tight gaps.
# 2. Active filter chips (.pchipOn / .gtabOn) get the FULL pill spec -- they
#    previously only carried colours, so active chips rendered as square
#    default buttons. Now every active filter on the page matches the
#    prototype's rounded orange pill.
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


# ── 1. prototype slate band with flat tabs and orange pill inside ──
replace(CSS,
        ".sourcePanel {\n"
        "  flex: 0 1 auto; display: flex; align-items: center;\n"
        "  background: transparent;\n"
        "  border: none; border-radius: 0;\n"
        "  padding: 0; box-shadow: none;\n"
        "}\n",
        ".sourcePanel {\n"
        "  flex: 0 0 auto; display: flex; align-items: center;\n"
        "  background: #4d5c5a;\n"
        "  border: none; border-radius: 8px;\n"
        "  padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
        "}\n")
replace(CSS,
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
        "}\n",
        ".tileRow { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }\n"
        ".tile {\n"
        "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
        "  letter-spacing: 1.5px; text-transform: uppercase;\n"
        "  padding: 8px 12px; border-radius: 6px; outline: none;\n"
        "  border: 1.5px solid transparent; background: transparent;\n"
        "  color: rgba(255,255,255,0.92); transition: color 0.2s ease;\n"
        "}\n"
        ".tile:hover { color: #EE8C3A; }\n"
        ".tileActive {\n"
        "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
        "  letter-spacing: 1.5px; text-transform: uppercase;\n"
        "  padding: 8px 14px; border-radius: 6px; outline: none;\n"
        "  border: 1.5px solid #EE8C3A; background: #EE8C3A; color: #1a2e30;\n"
        "  box-shadow: 0 4px 16px rgba(238,140,58,0.3);\n"
        "}\n")

# ── 2. active filter chips carry the full pill spec, not just colours ──
replace(CSS,
        ".pchipOn { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }",
        ".pchipOn {\n"
        "  cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);\n"
        "  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 12px;\n"
        "  border-radius: 6px; border: 1.5px solid #EE8C3A; background: #EE8C3A;\n"
        "  color: #1a2e30; white-space: nowrap; outline: none;\n"
        "}")
replace(CSS,
        ".gtabOn { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }",
        ".gtabOn {\n"
        "  cursor: pointer; font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);\n"
        "  font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; padding: 7px 12px;\n"
        "  border-radius: 6px; border: 1.5px solid #EE8C3A; background: #EE8C3A;\n"
        "  color: #1a2e30; outline: none;\n"
        "}")


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
git('commit', '-m', 'fix96: prototype slate source band with flat tabs, active filter chips get full pill spec')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix96 done: patched, committed and pushed to main.')