import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def remove_regex(path, pattern, label):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        print("MISSING FILE: " + path)
        return
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    new_content, n = re.subn(pattern, "", content)
    if n == 0:
        print("MISSING ANCHOR in " + path + ": " + label)
        return
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    print("OK: " + path + " (" + label + ", " + str(n) + ")")

def remove_import(path, fqn):
    remove_regex(path, r"^import " + re.escape(fqn) + r";\n", "unused import " + fqn)

def remove_repository_annotation(path):
    remove_regex(path, r"^@Repository\n", "@Repository annotation")
    remove_import(path, "org.springframework.stereotype.Repository")

# --- Bucket 3: unused imports (verified by IDE diagnostics) ---
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "com.gesolutions.erp.modules.auth.model.Role")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "com.gesolutions.erp.modules.auth.model.User")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "org.springframework.transaction.annotation.Transactional")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "java.util.UUID")
# userRepository is dead (seedRootUser uses raw JDBC); remove field + its import.
remove_regex("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
             r"^    private final UserRepository userRepository;\n", "unused field userRepository")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", "com.gesolutions.erp.modules.auth.repository.UserRepository")

remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java", "com.gesolutions.erp.common.exception.BusinessException")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java", "org.springframework.mail.SimpleMailMessage")

remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java", "com.gesolutions.erp.modules.client.model.Client")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java", "com.gesolutions.erp.modules.land.model.PaymentRecord")
remove_import("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerService.java", "java.math.RoundingMode")
remove_import("erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/LandCascadeDeleteTest.java", "org.springframework.transaction.annotation.Transactional")

# --- Bucket 4: unnecessary @Repository on plain Spring Data interfaces ---
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
r = subprocess.run(["git", "commit", "-m", "Cosmetic: remove unused imports and unnecessary @Repository annotations"])
if r.returncode == 0:
    subprocess.run(["git", "push"], check=True)
    print("DONE: committed and pushed.")
else:
    print("NOTHING TO COMMIT: no changes were needed.")