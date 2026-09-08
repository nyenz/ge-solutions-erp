# fix.py -- fix87: longest-wait real days, attempt line full width, ledger dots completion colours
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)

# ---------- 1. Backend: longest wait = real days (project start when never called) ----------
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
patch(rc, """                long d = c.getLastContactedAt() == null ? 999 : ChronoUnit.DAYS.between(c.getLastContactedAt(), now);""",
"""                long d;
                if (c.getLastContactedAt() != null) d = ChronoUnit.DAYS.between(c.getLastContactedAt(), now);
                else {
                    java.time.LocalDate oldest = null;
                    for (LandProject p : ps) if (p.getProjectStartDate() != null && (oldest == null || p.getProjectStartDate().isBefore(oldest))) oldest = p.getProjectStartDate();
                    d = oldest == null ? 0 : ChronoUnit.DAYS.between(oldest, now);
                }""", "longest wait real days")
patch(rc, """        m.put("longestWait", longest == 999 ? "NEW" : longest + "d");""",
"""        m.put("longestWait", longest + "d");""", "longest wait label")

# ---------- 2. Recovery CSS: attempt line spans full card width ----------
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if ".attemptLine { grid-column" not in s:
    s += """
/* fix87: attempt line reads on one full-width row */
.attemptLine { grid-column: 1 / -1; }
"""
    write(cssp, s)
    print("OK attempt line span")
else:
    print("SKIP attempt line already spanned")

# ---------- 3. Ledger stage dots: completion-based colours ----------
lj = FE / "pages" / "Ledger" / "LedgerPage.jsx"
patch(lj, "s.done ? styles.stageDotDone : si === curStageIdx ? styles.stageDotCurrent : ''",
"s.done ? (stages.every(x => x.done) ? styles.stageDotDone : styles.stageDotPart) : si === curStageIdx ? styles.stageDotCurrent : ''", "ledger dots completion logic")
lcss = FE / "pages" / "Ledger" / "LedgerPage.module.css"
c2 = read(lcss)
if "stageDotPart" not in c2:
    c2 += """
/* fix87: dots show how close the folder is to finishing */
.stageDotPart { background: var(--orange); box-shadow: 0 0 4px var(--orange); }
.stageDotCurrent { background: transparent; border: 1px solid var(--orange); box-shadow: none; }
"""
    write(lcss, c2)
    print("OK ledger dot css")
else:
    print("SKIP ledger dot css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix87: longest-wait real days, attempt line full width, ledger dots completion colours"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")