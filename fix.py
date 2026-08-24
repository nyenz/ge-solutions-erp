import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def remove_regex(path, pattern, label):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        print("MISSING FILE: " + path)
        return 0
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    new_content, n = re.subn(pattern, "", content)
    if n == 0:
        print("MISSING ANCHOR in " + path + ": " + label)
        return 0
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    print("OK: " + path + " (" + label + ", " + str(n) + ")")
    return n

def remove_import(path, fqn):
    return remove_regex(path, r"^import " + re.escape(fqn) + r";\n", "unused import " + fqn)

def remove_field_then_import(path, field_pattern, import_fqn, label):
    if remove_regex(path, field_pattern, label) > 0 and import_fqn:
        remove_import(path, import_fqn)

def remove_repository_annotation(path):
    remove_regex(path, r"^@Repository\n", "@Repository annotation")
    remove_import(path, "org.springframework.stereotype.Repository")

# --- Unused imports (IDE-verified) ---
DI = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"
remove_import(DI, "com.gesolutions.erp.modules.auth.model.Role")
remove_import(DI, "com.gesolutions.erp.modules.auth.model.User")
remove_import(DI, "org.springframework.transaction.annotation.Transactional")
remove_import(DI, "java.util.UUID")
remove_field_then_import(DI,
    r"^    private final UserRepository userRepository;\n",
    "com.gesolutions.erp.modules.auth.repository.UserRepository",
    "unused field userRepository")

remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java", "com.gesolutions.erp.common.exception.BusinessException")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java", "org.springframework.mail.SimpleMailMessage")
remove_field_then_import("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java",
    r"^    private final JavaMailSender mailSender;\n",
    "org.springframework.mail.javamail.JavaMailSender",
    "unused field mailSender")

remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java", "com.gesolutions.erp.modules.client.model.Client")

RC = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java"
remove_import(RC, "com.gesolutions.erp.modules.land.model.PaymentRecord")
remove_field_then_import(RC,
    r"^    private final PaymentRecordRepository paymentRecordRepository;\n",
    "com.gesolutions.erp.modules.land.repository.PaymentRecordRepository",
    "unused field paymentRecordRepository")
remove_field_then_import(RC,
    r"^    private final LandService landService;\n",
    "com.gesolutions.erp.modules.land.service.LandService",
    "unused field landService")

remove_field_then_import("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java",
    r"^    private final ClientRepository clientRepository;\n",
    "com.gesolutions.erp.modules.client.repository.ClientRepository",
    "unused field clientRepository")

remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerService.java", "java.math.RoundingMode")
remove_import("erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/LandCascadeDeleteTest.java", "org.springframework.transaction.annotation.Transactional")

# --- Unnecessary @Repository on plain Spring Data interfaces ---
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
    remove_repository_annotation(repo)

# PERMANENT Section 3 rule: commit and push automatically as the last step.
subprocess.run(["git", "add", "-A"], check=True)
r = subprocess.run(["git", "commit", "-m", "Cosmetic: warning sweep -- unused imports, dead fields, unnecessary @Repository"])
if r.returncode == 0:
    subprocess.run(["git", "push"], check=True)
    print("DONE: committed and pushed. Reload the VS Code window to refresh diagnostics.")
else:
    print("NOTHING TO COMMIT: no changes were needed.")