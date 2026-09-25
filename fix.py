#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix87: reports top-of-page parity with the prototype.
# Drops the duplicate RELOAD button, gives data sources their own panel with
# the source-rows pill, scales the catalogue search bar down, restyles every
# dropdown list to the prototype row language, fixes the page title and the
# catalogue badge. Then adds, commits and pushes by itself.
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


HUB = path('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.jsx')
STUDIO = path('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
CSS = path('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')

# ── 1. page title + subtitle match the prototype ──
patch(HUB,
      "          <h1 className={styles.title}>Report Studio</h1>\n"
      "          <p className={styles.subtitle}>Scope it, pick it, preview it, take it home</p>\n",
      "          <h1 className={styles.title}>Reports</h1>\n"
      "          <p className={styles.subtitle}>Scope it, pick it, chart it, take it home</p>\n")

# ── 2. drop the duplicate RELOAD button in the scope head ──
patch(STUDIO,
      "import { FiSearch, FiX, FiChevronDown, FiAlertCircle, FiRefreshCw } from 'react-icons/fi';\n",
      "import { FiSearch, FiX, FiChevronDown, FiAlertCircle } from 'react-icons/fi';\n")
patch(STUDIO,
      "          <span className={styles.scopeTitle}>SCOPE</span>\n"
      "          <button className={styles.chip} onClick={() => load(datasetKey)} disabled={loading}>\n"
      "            <FiRefreshCw size={11} aria-hidden=\"true\" /> RELOAD\n"
      "          </button>\n"
      "        </div>\n",
      "          <span className={styles.scopeTitle}>SCOPE</span>\n"
      "        </div>\n")

# ── 3. data sources move out of the scope panel into their own panel ──
patch(STUDIO,
      "        <div className={styles.scopeBody}>\n"
      "          <div className={styles.tileRow}>\n"
      "            {available.map(ds => (\n"
      "              <button key={ds.key} className={ds.key === datasetKey ? styles.tileActive : styles.tile} onClick={() => setDatasetKey(ds.key)}>\n"
      "                {ds.label}\n"
      "                <span className={styles.tileCount}>{ds.key === datasetKey ? (loading ? '...' : rows.length) : ''}</span>\n"
      "              </button>\n"
      "            ))}\n"
      "          </div>\n"
      "          <p className={styles.hint}>{dataset?.blurb}</p>\n"
      "          {!canSeeMoney && (\n",
      "        <div className={styles.scopeBody}>\n"
      "          {!canSeeMoney && (\n")
patch(STUDIO,
      "          {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden=\"true\" /> {error}</div>}\n"
      "          <div className={styles.scopeRow}>\n",
      "          <div className={styles.scopeRow}>\n")
patch(STUDIO,
      "  return (\n"
      "    <div className={styles.studio}>\n"
      "      <div className={styles.scopePanel}>\n",
      "  return (\n"
      "    <div className={styles.studio}>\n"
      "      <div className={styles.sourceRow}>\n"
      "        <div className={styles.sourcePanel}>\n"
      "          <div className={styles.tileRow}>\n"
      "            {available.map(ds => (\n"
      "              <button key={ds.key} className={ds.key === datasetKey ? styles.tileActive : styles.tile} onClick={() => setDatasetKey(ds.key)}>\n"
      "                {ds.label}\n"
      "                <span className={styles.tileCount}>{ds.key === datasetKey ? (loading ? '...' : rows.length) : ''}</span>\n"
      "              </button>\n"
      "            ))}\n"
      "          </div>\n"
      "          <p className={styles.hint}>{dataset?.blurb}</p>\n"
      "          {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden=\"true\" /> {error}</div>}\n"
      "        </div>\n"
      "        <span className={styles.sourceCount}>{loading ? '...' : rows.length} SOURCE ROWS</span>\n"
      "      </div>\n"
      "      <div className={styles.scopePanel}>\n")

# ── 6. catalogue badge wording matches the prototype ──
patch(STUDIO,
      "<span className={styles.badge}>{searched.length} REPORTS</span>",
      "<span className={styles.badge}>{searched.length} MATCHES</span>")

# ── 3b. styles for the new source panel + rows pill ──
patch(CSS,
      ".scopeBody { padding: clamp(12px, 1.6vw, 18px); display: flex; flex-direction: column; gap: clamp(10px, 1.3vw, 14px); }\n",
      ".scopeBody { padding: clamp(12px, 1.6vw, 18px); display: flex; flex-direction: column; gap: clamp(10px, 1.3vw, 14px); }\n"
      ".sourceRow { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }\n"
      ".sourcePanel {\n"
      "  flex: 1 1 auto; display: flex; flex-direction: column; gap: 8px;\n"
      "  background: linear-gradient(135deg, #4a6a6c 0%, #3a5a5c 55%, #2f4c4e 100%);\n"
      "  border: 1.5px solid rgba(238, 140, 58, 0.22); border-radius: 10px;\n"
      "  padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 14px);\n"
      "  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
      "}\n"
      ".sourceCount {\n"
      "  flex-shrink: 0; font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px);\n"
      "  font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: rgba(26,46,48,0.55);\n"
      "  background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; padding: 8px 12px; white-space: nowrap;\n"
      "}\n")

# ── 4. search bar scaled down to match the other fields ──
patch(CSS,
      ".searchBox { position: relative; height: 36px; width: clamp(170px, 22vw, 280px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }",
      ".searchBox { position: relative; height: 32px; width: clamp(150px, 17vw, 230px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }")
patch(CSS,
      ".searchIcon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; color: #EE8C3A; pointer-events: none; }",
      ".searchIcon { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); width: 13px; height: 13px; color: #EE8C3A; pointer-events: none; }")
patch(CSS,
      ".searchBox input { width: 100%; height: 100%; border: none; outline: none; background: transparent; padding: 0 30px 0 32px; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; }",
      ".searchBox input { width: 100%; height: 100%; border: none; outline: none; background: transparent; padding: 0 26px 0 30px; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; color: #1a2e30; }")

# ── 5. dropdown lists restyled to the prototype row language ──
patch(CSS,
      ".pickList {\n"
      "  position: absolute; top: calc(100% + 4px); left: 0; z-index: 60;\n"
      "  width: max-content; min-width: 100%; max-width: 340px;\n"
      "  background: #fff; border: 2px solid #EE8C3A; border-radius: 8px;\n"
      "  box-shadow: 0 18px 40px rgba(26,46,48,0.28); overflow: hidden;\n"
      "}\n"
      ".ddScroll { max-height: 264px; overflow-y: auto; padding: 4px; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }\n",
      ".pickList {\n"
      "  position: absolute; top: calc(100% + 4px); left: 0; z-index: 60;\n"
      "  width: max-content; min-width: 100%; max-width: 340px;\n"
      "  background: #fff; border: 1px solid #dfd9d1; border-radius: 8px;\n"
      "  box-shadow: 0 18px 40px rgba(26,46,48,0.28); overflow: hidden;\n"
      "}\n"
      ".ddScroll { max-height: 264px; overflow-y: auto; padding: 0; scrollbar-width: thin; scrollbar-color: #EE8C3A transparent; }\n")
patch(CSS,
      ".pickOption {\n"
      "  display: flex; width: 100%; text-align: left; border: none; border-left: 3px solid transparent;\n"
      "  border-radius: 4px; background: transparent; color: #1a2e30;\n"
      "  font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; padding: 8px 10px; cursor: pointer;\n"
      "}\n"
      ".pickOption:hover { background: rgba(238,140,58,0.12); }\n"
      ".pickOptionActive { background: rgba(238,140,58,0.16); border-left-color: #EE8C3A; color: #b45309; }\n",
      ".pickOption {\n"
      "  display: flex; width: 100%; text-align: left; border: none; border-bottom: 1px solid #f1eeea;\n"
      "  border-radius: 0; background: transparent; color: #1a2e30;\n"
      "  font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; padding: 10px 12px; cursor: pointer;\n"
      "  transition: background 0.15s, color 0.15s;\n"
      "}\n"
      ".pickOption:last-child { border-bottom: none; }\n"
      ".pickOption:hover { background: #EE8C3A; color: #fff; }\n"
      ".pickOptionActive { background: #EE8C3A; color: #fff; }\n")
patch(CSS,
      ".pickCheck {\n"
      "  display: flex; align-items: center; gap: 9px; width: 100%; text-align: left;\n"
      "  border: none; border-left: 3px solid transparent; border-radius: 4px; background: transparent;\n"
      "  color: #1a2e30; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700;\n"
      "  padding: 8px 10px; cursor: pointer;\n"
      "}\n"
      ".pickCheck:hover { background: rgba(238,140,58,0.12); }\n"
      ".pickCheckOn { background: rgba(238,140,58,0.16); border-left-color: #EE8C3A; color: #b45309; }\n",
      ".pickCheck {\n"
      "  display: flex; align-items: center; gap: 9px; width: 100%; text-align: left;\n"
      "  border: none; border-bottom: 1px solid #f1eeea; border-radius: 0; background: transparent;\n"
      "  color: #1a2e30; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700;\n"
      "  padding: 10px 12px; cursor: pointer; transition: background 0.15s, color 0.15s;\n"
      "}\n"
      ".pickCheck:last-child { border-bottom: none; }\n"
      ".pickCheck:hover { background: #EE8C3A; color: #fff; }\n"
      ".pickCheck:hover input { accent-color: #fff; }\n"
      ".pickCheckOn { background: #fdf3e7; color: #b45309; }\n")


def git(*args):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout or '').strip()
    err = (r.stderr or '').strip()
    if out:
        print(out)
    if r.returncode != 0:
        print('GIT FAIL: ' + err)
        sys.exit(1)
    return r


# make sure a commit identity exists, then add + commit + push
ident = subprocess.run(['git', 'config', 'user.email'], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or '').strip():
    git('config', 'user.name', 'nyenz')
    git('config', 'user.email', 'nyenz@users.noreply.github.com')

git('add', '-A')
git('commit', '-m', 'fix87: reports top parity -- drop dupe reload, sources own panel + rows pill, search scaled, dropdown rows match prototype')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix87 done: patched, committed and pushed to main.')