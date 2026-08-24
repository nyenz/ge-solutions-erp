import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(path):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        print("MISSING FILE: " + path)
        return None
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write(path, content):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def remove_line(path, exact_line):
    """Remove a line whose content (no newline) equals exact_line."""
    content = read(path)
    if content is None:
        return
    needle = exact_line + "\n"
    if needle not in content:
        print("MISSING ANCHOR in " + path + ": " + exact_line.strip()[:60])
        return
    write(path, content.replace(needle, "", 1))
    print("OK: " + path + " removed: " + exact_line.strip()[:60])

def remove_import(path, fqn):
    remove_line(path, "import " + fqn + ";")

def remove_import_if_unused(path, fqn):
    """Remove the import only if its simple name appears nowhere else in the file."""
    content = read(path)
    if content is None:
        return
    line = "import " + fqn + ";\n"
    if line not in content:
        return
    simple = fqn.split(".")[-1]
    rest = content.replace(line, "", 1)
    if re.search(r"\b" + re.escape(simple) + r"\b", rest):
        print("KEPT import (still referenced) in " + path + ": " + fqn)
        return
    write(path, rest)
    print("OK: " + path + " removed now-unused import " + fqn)

# --- 1. Unused imports (IDE-verified, compile-safe by definition) ---
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "com.gesolutions.erp.modules.auth.model.Role")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "com.gesolutions.erp.modules.auth.model.User")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "org.springframework.transaction.annotation.Transactional")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "java.util.UUID")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java", "com.gesolutions.erp.common.exception.BusinessException")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java", "org.springframework.mail.SimpleMailMessage")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java", "com.gesolutions.erp.modules.client.model.Client")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java", "com.gesolutions.erp.modules.land.model.PaymentRecord")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerService.java", "java.math.RoundingMode")
remove_import("erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/LandCascadeDeleteTest.java", "org.springframework.transaction.annotation.Transactional")

# --- 2. Dead injected fields (IDE-verified unused; exact lines read from repo) ---
remove_line("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
            "    private final UserRepository userRepository;")
remove_line("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java",
            "    private final PaymentRecordRepository paymentRecordRepository;")
remove_line("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java",
            "    private final LandService landService;")
remove_line("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java",
            "    private final ClientRepository clientRepository;")
remove_line("erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerTest.java",
            "    @Autowired")
remove_line("erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerTest.java",
            "    private LandTitleRepository landTitleRepository;")

# Imports that become unused once those fields are gone (checked, not assumed).
remove_import_if_unused("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "com.gesolutions.erp.modules.auth.repository.UserRepository")
remove_import_if_unused("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java", "com.gesolutions.erp.modules.land.repository.PaymentRecordRepository")
remove_import_if_unused("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java", "com.gesolutions.erp.modules.land.service.LandService")
remove_import_if_unused("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java", "com.gesolutions.erp.modules.client.repository.ClientRepository")
remove_import_if_unused("erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerTest.java", "com.gesolutions.erp.modules.land.repository.LandTitleRepository")

# --- 3. Unnecessary @Repository on plain Spring Data interfaces ---
for repo in [
    "erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditLogRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/client/repository/ClientRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/ExpensePresetRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/ExpenseRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/FollowUpRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/LandProjectRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentRecordRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectDocumentRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectStageRepository.java",
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/StageTemplateRepository.java",
]:
    remove_line(repo, "@Repository")
    remove_import_if_unused(repo, "org.springframework.stereotype.Repository")

# PERMANENT Section 3 rule: commit and push automatically as the last step.
subprocess.run(["git", "add", "-A"], check=True)
r = subprocess.run(["git", "commit", "-m", "Cosmetic: full warning sweep -- unused imports, dead fields, unnecessary @Repository"])
if r.returncode == 0:
    subprocess.run(["git", "push"], check=True)
    print("DONE: committed and pushed.")
else:
    print("NOTHING TO COMMIT: no changes were needed.")