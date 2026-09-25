#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix91: source tab holder uses the deactivated strip surface.
# The holder is a tab strip, not a panel: background = panel teal darkened by
# the app's tab-row overlay (rgba(0,0,0,0.16) over #4a6a6c = #3e595b).
# Inactive sources sit flat on that deactivated background, active = orange
# pill, and the holder padding is tightened so the pill hugs the holder.
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

# ── 1. holder = deactivated strip surface, tight padding ──
patch(CSS,
      ".sourcePanel {\n"
      "  flex: 0 0 auto; display: flex; align-items: center;\n"
      "  background: #4a6a6c;\n"
      "  border: 1.5px solid rgba(255, 255, 255, 0.10); border-radius: 8px;\n"
      "  padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
      "}\n",
      ".sourcePanel {\n"
      "  flex: 0 0 auto; display: flex; align-items: center;\n"
      "  background: #3e595b;\n"
      "  border: 1.5px solid rgba(255, 255, 255, 0.08); border-radius: 8px;\n"
      "  padding: 4px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
      "}\n")

# ── 2 + 3 + 4. flat deactivated links, orange active pill, snug gaps ──
patch(CSS,
      ".tileRow { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }\n"
      ".tile {\n"
      "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
      "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
      "  letter-spacing: 1.5px; text-transform: uppercase;\n"
      "  padding: 9px 14px; border-radius: 6px;\n"
      "  border: 1.5px solid transparent; background: transparent;\n"
      "  color: rgba(255,255,255,0.92); transition: color 0.2s ease;\n"
      "}\n"
      ".tile:hover { color: #EE8C3A; }\n"
      ".tileActive {\n"
      "  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
      "  font-family: 'Inter', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
      "  letter-spacing: 1.5px; text-transform: uppercase;\n"
      "  padding: 9px 16px; border-radius: 6px;\n"
      "  border: 1.5px solid #EE8C3A; background: #EE8C3A; color: #1a2e30;\n"
      "  box-shadow: 0 4px 16px rgba(238,140,58,0.3);\n"
      "}\n",
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
git('commit', '-m', 'fix91: source tab holder on deactivated strip surface #3e595b, flat inactive links, snug padding')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix91 done: patched, committed and pushed to main.')