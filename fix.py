# fix.py -- fix97: restore scheduler fields for unlockSweep + final cleanup
import subprocess, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

# 1. ReceivableSchedulerService: Restore fields needed by unlockSweep, remove trash
rs = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
s = rs.read_text(encoding="utf-8", errors="replace")

# Restore imports if missing
imps = [
    "import com.gesolutions.erp.modules.client.model.Client;",
    "import com.gesolutions.erp.modules.client.model.RecoveryNote;",
    "import com.gesolutions.erp.modules.client.repository.ClientRepository;",
    "import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;",
    "import java.time.LocalDate;"
]
for imp in imps:
    if imp not in s:
        s = s.replace("package com.gesolutions.erp.modules.land.service;", "package com.gesolutions.erp.modules.land.service;\n" + imp)

# Restore fields if missing (inject after notificationService)
if "ClientRepository clientRepo;" not in s:
    s = s.replace("private final NotificationService notificationService;", 
                  "private final NotificationService notificationService;\n    private final ClientRepository clientRepo;\n    private final RecoveryNoteRepository recoveryNoteRepository;")

# Remove unused PaymentRecord & Optional
s = re.sub(r'import com\.gesolutions\.erp\.modules\.land\.model\.PaymentRecord;\n', '', s)
s = re.sub(r'import com\.gesolutions\.erp\.modules\.land\.repository\.PaymentRecordRepository;\n', '', s)
s = re.sub(r'    private final (?:com\.gesolutions\.erp\.modules\.land\.repository\.)?PaymentRecordRepository paymentRecordRepository;\n', '', s)
s = re.sub(r'import java\.util\.Optional;\n', '', s)

rs.write_text(s, encoding="utf-8", newline="\n")
print("OK ReceivableSchedulerService fixed")

# 2. DataInitializer: Remove unused notificationService field and import
di = BE / "config" / "DataInitializer.java"
s2 = di.read_text(encoding="utf-8", errors="replace")
s2 = re.sub(r'    private final (?:com\.gesolutions\.erp\.modules\.notification\.service\.)?NotificationService notificationService;\n', '', s2)
s2 = re.sub(r'import com\.gesolutions\.erp\.modules\.notification\.service\.NotificationService;\n', '', s2)
di.write_text(s2, encoding="utf-8", newline="\n")
print("OK DataInitializer cleaned")

# 3. RecoveryNoteController: Remove unused entryTypeOf method
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
s3 = rc.read_text(encoding="utf-8", errors="replace")
s3 = re.sub(r'    private String entryTypeOf\(List<LandProject> ps\) \{[\s\S]*?    \}\n', '', s3)
rc.write_text(s3, encoding="utf-8", newline="\n")
print("OK RecoveryNoteController cleaned")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix97: restore scheduler fields for unlockSweep + final cleanup"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")