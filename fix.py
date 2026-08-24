import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def patch(path, old, new, count=1):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        print("MISSING FILE: " + path)
        return
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print("MISSING ANCHOR in " + path + ": " + old[:60].replace("\n", " | "))
        return
    content = content.replace(old, new) if count == 0 else content.replace(old, new, count)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: " + path)

def write_file(path, text):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("OK (rewritten): " + path)

LS = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"

# 1. atomicIntake: stop copying district/county onto the title.
patch(LS,
    '                    .plotNumber(request.getPlotNumber())\n'
    '                    .district(request.getDistrict())\n'
    '                    .blockRoad(request.getBlockRoad())\n'
    '                    .county(request.getCounty())',
    '                    .plotNumber(request.getPlotNumber())\n'
    '                    .blockRoad(request.getBlockRoad())')

# 2. atomicIntake: stop copying projectIndex onto the title (and old comment).
patch(LS,
    '                    // Kept in sync on the deprecated LandTitle column too,\n'
    '                    // for backward compatibility with anything still\n'
    '                    // reading projectIndex off LandTitle instead of\n'
    '                    // LandProject.\n'
    '                    .projectIndex(projectIndex)\n',
    '')

# 3. updateProjectFull (create branch): no district/county on new titles.
patch(LS,
    '                    .plotNumber(request.getPlotNumber())\n'
    '                    .blockRoad(request.getBlockRoad())\n'
    '                    .district(request.getDistrict())\n'
    '                    .county(request.getCounty())\n'
    '                    .volume(request.getVolume())',
    '                    .plotNumber(request.getPlotNumber())\n'
    '                    .blockRoad(request.getBlockRoad())\n'
    '                    .volume(request.getVolume())')

# 4. updateProjectFull (update branch): stop syncing district/county.
patch(LS,
    '            title.setBlockRoad(request.getBlockRoad());\n'
    '            title.setDistrict(request.getDistrict());\n'
    '            title.setCounty(request.getCounty());\n'
    '            title.setVolume(request.getVolume());',
    '            title.setBlockRoad(request.getBlockRoad());\n'
    '            title.setVolume(request.getVolume());')

# 5. bulkMarkTitleProduced: no projectIndex copy onto the title.
patch(LS,
    '                        .projectStartDate(java.time.LocalDate.now())\n'
    '                        .projectIndex(project.getProjectIndex())\n'
    '                        .build();',
    '                        .projectStartDate(java.time.LocalDate.now())\n'
    '                        .build();')

# 6. ReportService: drop the fallback that reads the old district field.
patch("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java",
    '(lt != null && lt.getDistrict() != null ? lt.getDistrict() : "")',
    '""',
    count=0)

# 7. Test: stop setting the old fields on the title.
patch("erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerTest.java",
    '                .district("Kampala")\n                .county("Central")\n',
    '')

# 8. Ledger search: use the new location fields, not the old title ones.
LJ = "erp-frontend/src/pages/Ledger/LedgerPage.jsx"
patch(LJ, '        proj.landTitle?.county,\n', '')
patch(LJ, '        proj.landTitle?.projectIndex,\n', '        proj.projectIndex,\n')
patch(LJ, '        proj.landTitle?.district,\n', '        proj.district,\n        proj.county,\n')

# 9. Folder page: if anything still reads the old fields, point it at the new ones.
FJ = "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"
patch(FJ, 'project.landTitle?.district', 'project.district', count=0)
patch(FJ, 'project.landTitle.district', 'project.district', count=0)
patch(FJ, 'project.landTitle?.county', 'project.county', count=0)
patch(FJ, 'project.landTitle.county', 'project.county', count=0)

# 10. MailService: real mail behind an on/off switch, QA log when off.
mail_lines = [
    "// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java",
    "package com.gesolutions.erp.modules.auth.service;",
    "",
    "import lombok.RequiredArgsConstructor;",
    "import org.springframework.beans.factory.annotation.Value;",
    "import org.springframework.mail.SimpleMailMessage;",
    "import org.springframework.mail.javamail.JavaMailSender;",
    "import org.springframework.stereotype.Service;",
    "",
    "/**",
    " * GE SOLUTIONS - COMMUNICATION HUB",
    " * SMTP is behind a switch: ge.solutions.mail.enabled (default off,",
    " * because Render's free tier blocks SMTP ports). Off or on-failure we",
    " * fall back to the QA console log so the recovery flow always works.",
    " * Flip the switch in config to turn real email on later - no code change.",
    " */",
    "@Service",
    "@RequiredArgsConstructor",
    "public class MailService {",
    "",
    "    private final JavaMailSender mailSender;",
    "",
    "    @Value(\"${ge.solutions.mail.enabled:false}\")",
    "    private boolean mailEnabled;",
    "",
    "    @Value(\"${ge.solutions.mail.from:no-reply@gesolutions.com}\")",
    "    private String mailFrom;",
    "",
    "    /**",
    "     * TRANSMIT RECOVERY TOKEN",
    "     * Real SMTP when enabled; QA console log otherwise. Never throws,",
    "     * so the frontend always gets a success response.",
    "     */",
    "    public void sendRecoveryEmail(String recipientEmail, String token) {",
    "        if (mailEnabled) {",
    "            try {",
    "                SimpleMailMessage message = new SimpleMailMessage();",
    "                message.setFrom(mailFrom);",
    "                message.setTo(recipientEmail);",
    "                message.setSubject(\"GE Solutions - Password Recovery\");",
    "                message.setText(\"Your recovery token: \" + token);",
    "                mailSender.send(message);",
    "                System.out.println(\">>> [MAIL] Recovery email sent to \" + recipientEmail);",
    "                return;",
    "            } catch (Exception e) {",
    "                System.err.println(\">>> [MAIL] SMTP send failed, using QA log instead: \" + e.getMessage());",
    "            }",
    "        }",
    "",
    "        System.out.println(\"\\n=======================================================\");",
    "        System.out.println(\">>> RECOVERY TOKEN INTERCEPTED FOR QA TESTING\");",
    "        System.out.println(\">>> (SMTP disabled or failed. Bypassing.)\");",
    "        System.out.println(\">>> EMAIL TO: \" + recipientEmail);",
    "        System.out.println(\">>> TOKEN:    \" + token);",
    "        System.out.println(\"=======================================================\\n\");",
    "    }",
    "}",
]
write_file("erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java", "\n".join(mail_lines) + "\n")

# PERMANENT Section 3 rule: commit and push automatically as the last step.
subprocess.run(["git", "add", "-A"], check=True)
r = subprocess.run(["git", "commit", "-m", "Cleanup: repoint old LandTitle fields to LandProject, feature-flag real email"])
if r.returncode == 0:
    subprocess.run(["git", "push"], check=True)
    print("DONE: committed and pushed.")
else:
    print("NOTHING TO COMMIT: no changes were needed.")