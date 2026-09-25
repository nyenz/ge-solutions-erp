#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix88: source band + search fields match the prototype exactly.
# Compact source panel (hugs tabs), live count on every tab, blurb dropped,
# professional subtitle, prototype search-field proportions and placeholders.
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


HUB = path('erp-frontend', 'src', 'pages', 'Reports', 'ReportHub.jsx')
STUDIO = path('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.jsx')
CSS = path('erp-frontend', 'src', 'pages', 'Reports', 'ReportStudio.module.css')

# ── 1. professional subtitle, no childish line ──
patch(HUB,
      "          <p className={styles.subtitle}>Scope it, pick it, chart it, take it home</p>\n",
      "          <p className={styles.subtitle}>Define the scope, preview the numbers, export the document.</p>\n")

# ── 2a. per-dataset placeholder hints like the prototype ──
patch(STUDIO,
      "const SAMPLE = 8;\n",
      "const SAMPLE = 8;\n"
      "const SEARCH_HINT = {\n"
      "  PROJECTS: 'Project index, plot, owner name, NIN...',\n"
      "  CLIENTS: 'Client name, NIN, phone...',\n"
      "  PAYMENTS: 'Receipt no, project, client...',\n"
      "  EXPENSES: 'Item, category, project...',\n"
      "  COMPANY: 'Any row across the company...',\n"
      "};\n")
patch(STUDIO,
      "                  placeholder={entity ? 'Change...' : 'Type to search this source...'}\n",
      "                  placeholder={entity ? 'Change...' : (SEARCH_HINT[datasetKey] || 'Type to search this source...')}\n")

# ── 2b. counts state + quiet background count fetch for every tab ──
patch(STUDIO,
      "  const [rows, setRows] = useState([]);\n"
      "  const [loading, setLoading] = useState(false);\n",
      "  const [rows, setRows] = useState([]);\n"
      "  const [counts, setCounts] = useState({});\n"
      "  const countsRef = useRef({});\n"
      "  const [loading, setLoading] = useState(false);\n")
patch(STUDIO,
      "  useEffect(() => { load(datasetKey); }, [datasetKey, load]);\n",
      "  useEffect(() => { load(datasetKey); }, [datasetKey, load]);\n"
      "  useEffect(() => {\n"
      "    let alive = true;\n"
      "    const put = (k, v) => { countsRef.current[k] = v; setCounts(c => ({ ...c, [k]: v })); };\n"
      "    available.forEach(ds => {\n"
      "      if (ds.key === datasetKey || countsRef.current[ds.key] != null) return;\n"
      "      ds.load().then(data => { if (alive) put(ds.key, Array.isArray(data) ? data.length : 0); })\n"
      "        .catch(() => { if (alive) put(ds.key, 0); });\n"
      "    });\n"
      "    return () => { alive = false; };\n"
      "    // eslint-disable-next-line react-hooks/exhaustive-deps\n"
      "  }, [available, datasetKey]);\n"
      "  useEffect(() => {\n"
      "    if (countsRef.current[datasetKey] !== rows.length) {\n"
      "      countsRef.current[datasetKey] = rows.length;\n"
      "      setCounts(c => ({ ...c, [datasetKey]: rows.length }));\n"
      "    }\n"
      "  }, [datasetKey, rows.length]);\n")

# ── 2c. every tab shows its count, like the prototype ──
patch(STUDIO,
      "                <span className={styles.tileCount}>{ds.key === datasetKey ? (loading ? '...' : rows.length) : ''}</span>\n",
      "                <span className={styles.tileCount}>{counts[ds.key] != null ? counts[ds.key] : (ds.key === datasetKey && loading ? '...' : '')}</span>\n")

# ── 2d. source panel keeps only the tabs; blurb + error leave it ──
patch(STUDIO,
      "          </div>\n"
      "          <p className={styles.hint}>{dataset?.blurb}</p>\n"
      "          {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden=\"true\" /> {error}</div>}\n"
      "        </div>\n"
      "        <span className={styles.sourceCount}>{loading ? '...' : rows.length} SOURCE ROWS</span>\n",
      "          </div>\n"
      "        </div>\n"
      "        <span className={styles.sourceCount}>{loading ? '...' : rows.length} SOURCE ROWS</span>\n")

# ── 4. error message lives at the top of the scope body instead ──
patch(STUDIO,
      "        <div className={styles.scopeBody}>\n"
      "          {!canSeeMoney && (\n",
      "        <div className={styles.scopeBody}>\n"
      "          {error && <div className={styles.error}><FiAlertCircle size={13} aria-hidden=\"true\" /> {error}</div>}\n"
      "          {!canSeeMoney && (\n")

# ── 2e. compact source panel CSS: hugs the tabs, pill pinned right ──
patch(CSS,
      ".sourcePanel {\n"
      "  flex: 1 1 auto; display: flex; flex-direction: column; gap: 8px;\n"
      "  background: linear-gradient(135deg, #4a6a6c 0%, #3a5a5c 55%, #2f4c4e 100%);\n"
      "  border: 1.5px solid rgba(238, 140, 58, 0.22); border-radius: 10px;\n"
      "  padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 14px);\n"
      "  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
      "}\n"
      ".sourceCount {\n"
      "  flex-shrink: 0; font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px);\n",
      ".sourcePanel {\n"
      "  flex: 0 0 auto; display: flex; align-items: center;\n"
      "  background: linear-gradient(135deg, #4a6a6c 0%, #3a5a5c 55%, #2f4c4e 100%);\n"
      "  border: 1.5px solid rgba(238, 140, 58, 0.22); border-radius: 10px;\n"
      "  padding: 8px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
      "}\n"
      ".sourceCount {\n"
      "  margin-left: auto; flex-shrink: 0; font-family: 'Space Mono', monospace; font-size: clamp(8px, 0.85vw, 10px);\n")

# ── 3. search fields at prototype proportions (max ~260px) ──
patch(CSS,
      ".entInput { height: 38px; width: clamp(180px, 22vw, 280px); padding: 0 12px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; transition: all 0.2s; }",
      ".entInput { height: 38px; width: clamp(180px, 20vw, 260px); padding: 0 12px; border-radius: 6px; border: 1.5px solid #dfd9d1; background: #fff; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700; color: #1a2e30; outline: none; transition: all 0.2s; }")
patch(CSS,
      ".searchBox { position: relative; height: 32px; width: clamp(150px, 17vw, 230px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }",
      ".searchBox { position: relative; height: 32px; width: clamp(180px, 20vw, 260px); background: #fff; border: 1.5px solid #dfd9d1; border-radius: 6px; margin-left: auto; }")


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
git('commit', '-m', 'fix88: source band matches prototype -- compact panel, counts on every tab, pro subtitle, prototype search proportions')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix88 done: patched, committed and pushed to main.')