# fix.py -- fix94: mobile layout (search line + filter line), scrollable dots both versions, note input focus fix, remove duplicate no-contact chip
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)
def append(p, marker, block, label):
    s = read(p)
    if marker not in s:
        write(p, s + block); print("OK", label)
    else:
        print("SKIP", label)

jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"

# 1. Wrap the tab pills in their own row container (so mobile can stack search above filters)
patch(jsxp, """        {TABS.map((t) => (
          <button key={t.key} role="tab" aria-selected={tab === t.key} className={`${styles.qTab} ${tab === t.key ? styles.qTabActive : ''}`} onClick={() => setTab(t.key)}>
            {t.label} ({counts ? counts[t.key] : '-'})
          </button>
        ))}
      </div>""",
"""        <div className={styles.tabRow}>
          {TABS.map((t) => (
            <button key={t.key} role="tab" aria-selected={tab === t.key} className={`${styles.qTab} ${tab === t.key ? styles.qTabActive : ''}`} onClick={() => setTab(t.key)}>
              {t.label} ({counts ? counts[t.key] : '-'})
            </button>
          ))}
        </div>
      </div>""", "tabRow wrapper")

# 2. Remove the duplicate 'no contact yet' chip (reason column already says NEVER CALLED)
patch(jsxp, "<span className={c.lastTone === 'POSITIVE' ? styles.chipPos : c.lastTone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{c.lastTag || 'no contact yet'}</span>",
"{c.lastTag && (<span className={c.lastTone === 'POSITIVE' ? styles.chipPos : c.lastTone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{c.lastTag}</span>)}", "drop duplicate chip")

# 3. Recovery CSS: dots one line + scrollable everywhere, mobile stacks search and filters
append(FE / "pages" / "Recovery" / "RecoveryPortal.module.css", "fix94", """
/* fix94: dot legend one line + horizontal scroll on ALL screen sizes */
.dotLegend { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; }
.dotLegend::-webkit-scrollbar { display: none; }
.dotLegend span { white-space: nowrap; flex-shrink: 0; }
/* pill row scrolls horizontally inside the rail */
.tabRow { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; flex: 1 1 auto; min-width: 0; }
.tabRow::-webkit-scrollbar { display: none; }
/* mobile: search on its own line, filters on their own line */
@media (max-width: 640px) {
  .stickyTabs { flex-direction: column; align-items: stretch; gap: 6px; }
  .tabSearch { width: 100%; margin-right: 0; flex: none; }
  .tabRow { width: 100%; flex: none; }
  .countsHUD { grid-template-columns: repeat(2, 1fr); }
  .rowHead { flex-wrap: wrap; gap: 6px 8px; }
  .rowBody { grid-template-columns: 1fr; }
}
""", "recovery fix94 css")

# 4. Modal note input: never dark-on-dark, on focus or autofill
append(FE / "components" / "common" / "HardwareModal.module.css", "fix94", """
/* fix94: popup text fields stay readable in every state */
.modalInput, .modalTextarea, [class*="modalInput"], [class*="modalTextarea"] {
  color: rgba(255, 255, 255, 0.95) !important;
  -webkit-text-fill-color: rgba(255, 255, 255, 0.95) !important;
  caret-color: #ffffff;
  background: rgba(255, 255, 255, 0.08) !important;
}
.modalInput:focus, .modalTextarea:focus, [class*="modalInput"]:focus, [class*="modalTextarea"]:focus {
  color: rgba(255, 255, 255, 0.95) !important;
  -webkit-text-fill-color: rgba(255, 255, 255, 0.95) !important;
  background: rgba(255, 255, 255, 0.12) !important;
}
.modalInput:-webkit-autofill, .modalTextarea:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px rgba(33, 62, 64, 0.99) inset;
  -webkit-text-fill-color: #ffffff !important;
}
""", "modal input visibility fix")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix94: mobile stack (search line + filter line), scrollable dots both versions, note input focus fix, remove duplicate no-contact chip"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")