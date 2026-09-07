# fix.py -- fix84: remove unused entryTypeOf helper from RecoveryNoteController
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RC = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules" / "client" / "controller" / "RecoveryNoteController.java"

s = RC.read_text(encoding="utf-8", errors="replace")

old = """    private String entryTypeOf(List<LandProject> ps) {
        for (LandProject p : ps) { if (p.isLegacy()) return "Legacy Title"; if (p.getLandTitle() != null) return "New Title"; }
        return ps.isEmpty() ? null : "New Folder";
    }
"""
if old in s:
    s = s.replace(old, "", 1)
    RC.write_text(s, encoding="utf-8", newline="\n")
    print("OK removed unused entryTypeOf method")
else:
    print("MISSING entryTypeOf block")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix84: remove unused entryTypeOf helper from RecoveryNoteController"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")