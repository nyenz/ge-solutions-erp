# fix.py -- fix80: clean up unused imports and fields (VS Code warnings)
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)

# --- 1. DataInitializer.java ---
di = BE / "config" / "DataInitializer.java"
s = read(di)
s = s.replace("private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;\n", "")
s = s.replace("private final NotificationService notificationService;\n", "")
write(di, s)
print("OK cleaned DataInitializer")

# --- 2. ReceivableSchedulerService.java ---
rs = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
s2 = read(rs)

lines_to_remove = [
    "import com.gesolutions.erp.modules.client.model.RecoveryNote;",
    "import com.gesolutions.erp.modules.land.model.PaymentRecord;",
    "import java.util.Optional;",
    "import java.time.LocalDate;",
    "private final RecoveryNoteRepository recoveryNoteRepository;",
    "private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;",
    "private final PaymentRecordRepository paymentRecordRepository;",
    "private final com.gesolutions.erp.modules.land.repository.PaymentRecordRepository paymentRecordRepository;",
    "private final ClientRepository clientRepo;",
    "private final com.gesolutions.erp.modules.client.repository.ClientRepository clientRepo;"
]

for line in lines_to_remove:
    s2 = s2.replace(line + "\n", "")

write(rs, s2)
print("OK cleaned ReceivableSchedulerService")

# --- GIT PUSH ---
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix80: clean up unused imports and fields to resolve VS Code warnings"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")