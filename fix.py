# fix.py -- fix106: Intake-ADD-OWNER-sized card buttons, CALL LOG label, phone icon row, district-subcounty-village, thick mono phone + co-owner with hover
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

jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"

# 1. Rename button to CALL LOG
patch(jsxp, "<FiPhone aria-hidden=\"true\" /> OPEN CALL LOG", "<FiPhone aria-hidden=\"true\" /> CALL LOG", "CALL LOG label")

# 2. Phone gets an icon row so it aligns with location
patch(jsxp, "<span className={styles.mono}>{c.phone}</span>",
"<span className={styles.monoRow}><FiPhoneCall aria-hidden=\"true\" /><span className={styles.mono}>{c.phone}</span></span>", "phone icon row")

# 3. Location order district - subcounty - village
patch(jsxp, "<span className={styles.loc}><FiMapPin aria-hidden=\"true\" /> {c.district}{c.village ? ' - ' + c.village : ''}</span>",
"<span className={styles.loc}><FiMapPin aria-hidden=\"true\" /> {c.district}{c.subCounty ? ' - ' + c.subCounty : ''}{c.village ? ' - ' + c.village : ''}</span>", "location order")

# 4. Backend: send subCounty
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
patch(rc, "        m.put(\"district\", ps.isEmpty() ? null : ps.get(0).getDistrict());",
"        m.put(\"district\", ps.isEmpty() ? null : ps.get(0).getDistrict());\n        m.put(\"subCounty\", ps.isEmpty() ? null : ps.get(0).getSubCounty());", "subCounty in dto")

# 5. CSS: Intake-ADD-OWNER button size + thick mono phone/co-owner + phone hover
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "fix106" not in s:
    s += """
/* fix106: Intake ADD OWNER button proportions, thick mono phone + co-owner, phone hover */
.cardBtn, .cardBtn2 {
  height: clamp(30px, 3.6vw, 36px);
  padding: 0 clamp(9px, 1.2vw, 13px);
  font-size: clamp(8px, 0.85vw, 10px);
  letter-spacing: 1.5px;
  border-radius: 6px;
  gap: 6px;
}
.monoRow { display: flex; align-items: center; gap: 6px; }
.monoRow svg { color: rgba(255, 255, 255, 0.5); font-size: 12px; flex-shrink: 0; }
.mono {
  font-family: 'Space Mono', monospace; font-weight: 900; letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.85); transition: color 0.18s ease; cursor: default;
}
.mono:hover { color: #ffffff; }
.coChip { font-family: 'Space Mono', monospace; font-weight: 900; letter-spacing: 1px; }
"""
    write(cssp, s)
    print("OK fix106 css")
else:
    print("SKIP fix106 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix106: Intake-ADD-OWNER-sized card buttons, CALL LOG label, phone icon row, district-subcounty-village, thick mono phone + co-owner with hover"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")