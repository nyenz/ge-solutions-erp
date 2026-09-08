# fix.py -- fix105: Ledger legend rhythm on Recovery, plain colored co-owner/plot links with white hover, Intake token-matched card buttons
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"

cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = cssp.read_text(encoding="utf-8", errors="replace")
if "fix105" not in s:
    s += """
/* fix105: Ledger legend rhythm + plain colored links with Intake white-hover + token-matched buttons */
.dotLegend { margin-bottom: clamp(10px, 1.2vw, 14px); }
.mono { font-size: clamp(11px, 1.2vw, 14px); }
.projLink { text-decoration: none; transition: color 0.18s ease; }
.projLink:hover { color: #ffffff; }
.coChip {
  background: none; border: none; padding: 0; border-radius: 0;
  font-family: 'Space Mono', monospace; font-size: clamp(11px, 1.2vw, 14px); font-weight: 400;
  color: #67e8f9; letter-spacing: 0.5px; transition: color 0.18s ease;
}
.coChip:hover { color: #ffffff; background: none; }
.coChip:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.cardBtn, .cardBtn2 {
  height: var(--input-height, clamp(34px, 4.3vw, 40px));
  padding: 0 clamp(12px, 1.5vw, 18px);
  font-size: var(--fs-btn, clamp(8px, 0.85vw, 10px));
  letter-spacing: 1.5px;
  border-radius: 6px;
}
"""
    cssp.write_text(s, encoding="utf-8", newline="\n")
    print("OK fix105 css")
else:
    print("SKIP fix105 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix105: Ledger legend rhythm on Recovery, plain colored co-owner/plot links with white hover, Intake token-matched card buttons"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")