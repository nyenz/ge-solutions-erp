# PATH: fix.py
import os

path = "erp-backend/src/main/java/com/gesolutions/erp/config/MailConfig.java"

if not os.path.isfile(path):
    print(f"MISSING: {path} not found")
else:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Normalize line endings
    content = content.replace("\r\n", "\n")

    old_config = """        mailSender.setHost("smtp.gmail.com");
        mailSender.setPort(587);
        mailSender.setUsername(mailUsername);
        mailSender.setPassword(mailPassword);

        Properties props = mailSender.getJavaMailProperties();
        props.put("mail.transport.protocol", "smtp");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");
        props.put("mail.debug", "false");"""

    new_config = """        mailSender.setHost("smtp.gmail.com");
        // BEST PRACTICE: Use Port 465 with strict SSL for cloud deployments.
        // Port 587 (STARTTLS) is frequently blocked by cloud firewalls.
        mailSender.setPort(465);
        mailSender.setUsername(mailUsername);
        mailSender.setPassword(mailPassword);

        Properties props = mailSender.getJavaMailProperties();
        props.put("mail.transport.protocol", "smtp");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.ssl.enable", "true");
        props.put("mail.debug", "false");"""

    if old_config in content:
        content = content.replace(old_config, new_config)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: Patched MailConfig.java to use Port 465 (SSL)")
    elif new_config in content:
        print(f"SKIP: MailConfig.java is already using Port 465")
    else:
        print(f"FAIL: Target block not found in MailConfig.java")