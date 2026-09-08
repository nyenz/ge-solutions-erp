# fix.py -- fix96: resolve pm/nm scope error in clientDto + clean all unused imports/fields
import subprocess, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

# 1. Fix pm/nm scope in RecoveryNoteController
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
s = rc.read_text(encoding="utf-8", errors="replace")

s = s.replace(
    "private Map<String, Object> clientDto(Client c, LocalDateTime now, List<LandProject> ps, List<RecoveryNote> ns) {",
    "private Map<String, Object> clientDto(Client c, LocalDateTime now, List<LandProject> ps, List<RecoveryNote> ns, Map<UUID, List<LandProject>> pm, Map<UUID, List<RecoveryNote>> nm) {"
)
s = s.replace(
    "out.add(clientDto(c, now, ps, ns));",
    "out.add(clientDto(c, now, ps, ns, pm, nm));"
)

# Remove unused entryTypeOf if it's still lingering
if "private String entryTypeOf(List<LandProject> ps)" in s:
    s = re.sub(r'    private String entryTypeOf\(List<LandProject> ps\) \{[\s\S]*?    \}\n', '', s)

rc.write_text(s, encoding="utf-8", newline="\n")
print("OK fixed RecoveryNoteController pm/nm scope")

# 2. Clean ReceivableSchedulerService unused imports/fields
rs = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
s2 = rs.read_text(encoding="utf-8", errors="replace")
unused_rs = [
    "import com.gesolutions.erp.modules.client.model.RecoveryNote;",
    "import com.gesolutions.erp.modules.land.model.PaymentRecord;",
    "import java.util.Optional;",
    "import java.time.LocalDate;",
    "import com.gesolutions.erp.modules.client.repository.ClientRepository;",
    "import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;",
    "import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;",
    "private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;",
    "private final com.gesolutions.erp.modules.client.repository.ClientRepository clientRepo;",
    "private final com.gesolutions.erp.modules.land.repository.PaymentRecordRepository paymentRecordRepository;",
    "private final RecoveryNoteRepository recoveryNoteRepository;",
    "private final ClientRepository clientRepo;",
    "private final PaymentRecordRepository paymentRecordRepository;"
]
for line in unused_rs:
    s2 = s2.replace(line + "\n", "")
    s2 = s2.replace("    " + line + "\n", "")
rs.write_text(s2, encoding="utf-8", newline="\n")
print("OK cleaned ReceivableSchedulerService")

# 3. Clean DataInitializer unused fields
di = BE / "config" / "DataInitializer.java"
s3 = di.read_text(encoding="utf-8", errors="replace")
s3 = s3.replace("private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;\n", "")
s3 = s3.replace("private final NotificationService notificationService;\n", "")
s3 = s3.replace("    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;\n", "")
s3 = s3.replace("    private final NotificationService notificationService;\n", "")
di.write_text(s3, encoding="utf-8", newline="\n")
print("OK cleaned DataInitializer")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix96: resolve pm/nm scope error in clientDto + clean all unused imports/fields"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")