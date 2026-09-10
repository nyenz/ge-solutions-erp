# fix.py -- fix122: FiUsers crash fix via global icon-import audit + styled route error screen
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
APP = FE / "App.jsx"
ERR = FE / "components" / "common" / "RouteErrorScreen.jsx"
ERRCSS = FE / "components" / "common" / "RouteErrorScreen.module.css"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding="utf-8", newline="") as f: f.write(s)
    print("WROTE", p.name)
def find(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]: return i
    return -1

# ---------- 1. GLOBAL ICON-IMPORT AUDIT (auto-fix missing Fi* imports) ----------
for f in sorted(FE.rglob('*.jsx')):
    s = read(f)
    m = re.search(r"import\s*\{([^}]*)\}\s*from\s*'react-icons/fi';", s, re.S)
    if not m:
        continue
    imported = set(re.findall(r'\bFi[A-Za-z0-9_]+\b', m.group(1)))
    body = s[:m.start()] + s[m.end():]
    used = set(re.findall(r'\bFi[A-Z][A-Za-z0-9]*\b', body))
    missing = sorted(n for n in used if n not in imported)
    if not missing:
        continue
    names = m.group(1).strip()
    if names.endswith(','):
        names = names[:-1].rstrip()
    joined = names + ', ' + ', '.join(missing)
    multi = '\n' in m.group(1)
    out = ("import {\n" + joined + "\n} from 'react-icons/fi';") if multi else ("import { " + joined + " } from 'react-icons/fi';")
    s = s[:m.start()] + out + s[m.end():]
    write(f, s)
    print("OK added missing imports", missing, "to", f.name)

# ---------- 2. styled crash screen component ----------
ERR_JSX = """// PATH: erp-frontend/src/components/common/RouteErrorScreen.jsx
import React from 'react';
import { useRouteError, useNavigate } from 'react-router-dom';
import { FiAlertOctagon, FiRefreshCw, FiHome } from 'react-icons/fi';
import styles from './RouteErrorScreen.module.css';

const RouteErrorScreen = () => {
  const error = useRouteError();
  const navigate = useNavigate();
  const msg = error?.message || String(error || 'UNKNOWN FAULT');
  return (
    <div className={styles.wrap}>
      <div className={styles.hud} role="alert">
        <div className={styles.iconBox}><FiAlertOctagon aria-hidden="true" /></div>
        <div className={styles.body}>
          <h1 className={styles.title}>SYSTEM FAULT</h1>
          <p className={styles.msg}>{msg}</p>
          <p className={styles.hint}>The fault is contained to this screen. Your data is safe.</p>
          <div className={styles.actions}>
            <button type="button" className={styles.btn} onClick={() => window.location.reload()}><FiRefreshCw aria-hidden="true" /> RELOAD TERMINAL</button>
            <button type="button" className={styles.btnGhost} onClick={() => navigate('/dashboard')}><FiHome aria-hidden="true" /> BACK TO DASHBOARD</button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default RouteErrorScreen;
"""

ERR_CSS = """/* PATH: erp-frontend/src/components/common/RouteErrorScreen.module.css */
/* fix122: styled crash screen - app design language instead of router debug box */
.wrap {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: radial-gradient(circle at 50% 30%, #213E40 0%, #1a2e30 70%);
  padding: clamp(16px, 4vw, 40px);
}
.hud {
  display: flex; gap: clamp(12px, 2vw, 20px); align-items: flex-start;
  max-width: clamp(320px, 60vw, 560px); width: 100%;
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid rgba(239, 68, 68, 0.35);
  border-radius: 10px;
  padding: clamp(18px, 3vw, 30px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.45);
}
.iconBox {
  color: #ef4444; font-size: clamp(22px, 3vw, 30px);
  flex-shrink: 0;
  filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.5));
}
.body { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.title {
  font-family: 'Cinzel', serif;
  font-size: clamp(16px, 2.4vw, 22px);
  color: #EE8C3A; letter-spacing: 2px;
  text-shadow: 0 0 12px rgba(238, 140, 58, 0.45);
}
.msg {
  font-family: 'Space Mono', monospace;
  font-size: clamp(10px, 1.2vw, 13px);
  color: #fca5a5; letter-spacing: 0.4px;
  word-break: break-word;
}
.hint {
  font-family: 'DM Sans', sans-serif;
  font-size: clamp(9px, 1vw, 11px);
  color: rgba(255, 255, 255, 0.55); letter-spacing: 0.6px;
}
.actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
.btn, .btnGhost {
  font-family: 'DM Sans', sans-serif;
  font-size: 9px; font-weight: 800; letter-spacing: 1.2px;
  padding: 9px 14px; border-radius: 6px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
  transition: all 0.2s;
}
.btn { background: #EE8C3A; border: 1px solid #EE8C3A; color: #1a2e30; }
.btn:hover { background: #f0a050; border-color: #f0a050; }
.btnGhost { background: transparent; border: 1px solid rgba(238, 140, 58, 0.28); color: #EE8C3A; }
.btnGhost:hover { background: rgba(238, 140, 58, 0.12); }
.btn:focus-visible, .btnGhost:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 2px; }
"""

if not ERR.exists():
    write(ERR, ERR_JSX)
else:
    print("SKIP RouteErrorScreen.jsx already present")
if not ERRCSS.exists():
    write(ERRCSS, ERR_CSS)
else:
    print("SKIP RouteErrorScreen.module.css already present")

# ---------- 3. wire errorElement into the router ----------
al = read(APP).split("\n")
if 'RouteErrorScreen' not in "\n".join(al):
    i = find(al, "import Shell from './components/layout/Shell';")
    if i >= 0:
        al.insert(i + 1, "import RouteErrorScreen from './components/common/RouteErrorScreen';")
        print("OK App import RouteErrorScreen")
    else:
        print("MISSING App Shell import anchor")
    j = find(al, 'children: [')
    if j >= 0:
        indent = al[j][:len(al[j]) - len(al[j].lstrip())]
        al.insert(j, indent + 'errorElement: <RouteErrorScreen />,')
        print("OK App root errorElement")
    else:
        print("MISSING App children anchor")
    write(APP, "\n".join(al))
else:
    print("SKIP App errorElement already wired")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix122: global icon-import audit auto-fix (FiUsers crash), styled RouteErrorScreen as root errorElement"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")