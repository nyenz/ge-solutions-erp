# fix.py -- fix89: locked-tab empty-row crash-proofing + longest-wait fallback
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

# ---------- 1. Frontend JSX: never render an empty position pill or empty name ----------
jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
patch(jsxp, "<span className={styles.callPos}>{tab} #{c.position}/{c.queueTotal}</span>",
"<span className={styles.callPos}>{c.position ? tab + ' #' + c.position + '/' + c.queueTotal : tab}</span>", "position chip fallback")
patch(jsxp, "<span className={styles.cname}>{c.name}</span>",
"<span className={styles.cname}>{c.name || c.nin || 'UNKNOWN CLIENT'}</span>", "name fallback")

# ---------- 2. Frontend CSS: guaranteed row height + explicit text sizes in every tab ----------
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix89" not in s:
    s += """
/* fix89: rows can never collapse to empty bars in any tab */
.rowCard { min-height: 46px; }
.rowHead { min-height: 46px; font-size: 12px; }
.rowHead .cname { font-size: clamp(13px, 1.6vw, 16px); font-weight: 900; color: #ffffff; }
.rowHead .callPos, .rowHead .chipPos, .rowHead .chipNeg, .rowHead .chipNone, .rowHead .reason, .rowHead .dayChip { font-size: clamp(8px, 0.9vw, 10px); }
"""
    write(cssp, s)
    print("OK row height guard css")
else:
    print("SKIP row guard css already present")

# ---------- 3. Backend: longest wait falls back to title dates, shows NEW when truly new ----------
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
patch(rc, """                else {
                    java.time.LocalDate oldest = null;
                    for (LandProject p : ps) if (p.getProjectStartDate() != null && (oldest == null || p.getProjectStartDate().isBefore(oldest))) oldest = p.getProjectStartDate();
                    d = oldest == null ? 0 : ChronoUnit.DAYS.between(oldest, now);
                }""",
"""                else {
                    java.time.LocalDate oldest = null;
                    for (LandProject p : ps) {
                        java.time.LocalDate cand = p.getProjectStartDate();
                        if (cand == null && p.getLandTitle() != null) cand = p.getLandTitle().getProjectStartDate() != null ? p.getLandTitle().getProjectStartDate() : p.getLandTitle().getTitleIssueDate();
                        if (cand != null && (oldest == null || cand.isBefore(oldest))) oldest = cand;
                    }
                    d = oldest == null ? 0 : ChronoUnit.DAYS.between(oldest, now);
                }""", "longest wait title fallback")
patch(rc, "        m.put(\"longestWait\", longest + \"d\");",
"        m.put(\"longestWait\", longest == 0 ? \"NEW\" : longest + \"d\");", "longest wait NEW label")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix89: locked-tab empty-row crash-proofing + longest-wait fallback"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")
