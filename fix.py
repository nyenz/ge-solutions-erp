#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix90: prototype color theme + field proportions.
# Panel bodies go flat prototype teal (#4a6a6c) with a subtle light edge;
# orange remains only as the separator under panel heads. The catalogue
# search box joins the 36px compact-field height family used by every other
# input in the code.
# Then adds, commits and pushes by itself.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def path(*parts):
    return os.path.join(ROOT, *parts)


def patch(file_path, old, new, count=1):
    with open(file_path, 'r', encoding='utf-8') as f:
        src = f.read()
    found = src.count(old)
    if found != count:
        print('FAIL: pattern found %d time(s), expected %d in %s' % (found, count, file_path))
        print('Nothing was changed. Fix the pattern and run again.')
        sys.exit(1)
    src = src.replace(old, new)
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src)
    print('patched: ' + os.path.relpath(file_path, ROOT))


CSS = path('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')

# ── 1. flat prototype teal panel bodies, orange only as head separator ──
patch(CSS,
      ".scopePanel, .catPanel, .viewerPanel {\n"
      "  background: linear-gradient(135deg, #4a6a6c 0%, #3a5a5c 55%, #2f4c4e 100%);\n"
      "  border: 1.5px solid rgba(238, 140, 58, 0.22);\n"
      "  border-radius: 12px;\n"
      "  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);\n"
      "  overflow: visible;\n"
      "}\n",
      ".scopePanel, .catPanel, .viewerPanel {\n"
      "  background: #4a6a6c;\n"
      "  border: 1.5px solid rgba(255, 255, 255, 0.10);\n"
      "  border-radius: 12px;\n"
      "  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);\n"
      "  overflow: visible;\n"
      "}\n")
patch(CSS,
      ".sourcePanel {\n"
      "  flex: 0 0 auto; display: flex; align-items: center;\n"
      "  background: linear-gradient(135deg, #4a6a6c 0%, #3a5a5c 55%, #2f4c4e 100%);\n"
      "  border: 1.5px solid rgba(238, 140, 58, 0.22); border-radius: 8px;\n"
      "  padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
      "}\n",
      ".sourcePanel {\n"
      "  flex: 0 0 auto; display: flex; align-items: center;\n"
      "  background: #4a6a6c;\n"
      "  border: 1.5px solid rgba(255, 255, 255, 0.10); border-radius: 8px;\n"
      "  padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
      "}\n")

# ── 2. catalogue search box joins the 36px compact-field family ──
patch(CSS,
      ".searchBox { position: relative; height: 32px; width: clamp(180px, 20vw, 260px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }",
      ".searchBox { position: relative; height: 36px; width: clamp(180px, 20vw, 260px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }")


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
git('commit', '-m', 'fix90: prototype color theme -- flat teal panel bodies, subtle edges, search box at field-standard 36px')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix90 done: patched, committed and pushed to main.')