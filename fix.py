# fix.py -- fix81: clean up remaining unused imports in ReceivableSchedulerService
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

rs = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
s = rs.read_text(encoding="utf-8", errors="replace")

lines_to_remove = [
    "import com.gesolutions.erp.modules.client.repository.ClientRepository;",
    "import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;",
    "import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;"
]

for line in lines_to_remove:
    s = s.replace(line + "\n", "")

rs.write_text(s, encoding="utf-8", newline="\n")
print("OK cleaned ReceivableSchedulerService remaining imports")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix81: clean up remaining unused imports in ReceivableSchedulerService"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")