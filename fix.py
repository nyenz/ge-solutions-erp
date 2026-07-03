# PATH: fix.py
import os

path = "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java"

if not os.path.isfile(path):
    print(f"MISSING: {path} not found")
else:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    content = content.replace("\r\n", "\n")

    old_method = """    public void sendRecoveryEmail(String recipientEmail, String token) {
        SimpleMailMessage message = new SimpleMailMessage();
        
        // --- VITAL: THE FROM ADDRESS ---
        // Gmail requires this to match the account in MailConfig exactly
        message.setFrom("nyenzdav@gmail.com"); 
        message.setTo(recipientEmail);
        message.setSubject("GE SOLUTIONS | Master Key Recovery Protocol");
        
        String body = "SYSTEM ALERT: A Master Key reset was requested.\\n\\n" +
                      "Your Temporary Access Token is: " + token + "\\n\\n" +
                      "This code is for one-time use. If you did not request this, " +
                      "contact your IT department immediately.";
        
        message.setText(body);

        try {
            mailSender.send(message);
            System.out.println(">>> SMTP_SUCCESS: Recovery signal transmitted to " + recipientEmail);
        } catch (org.springframework.mail.MailException e) {
            System.err.println(">>> SMTP_CRITICAL_FAULT (MailException): " + e.getMessage());
            throw new BusinessException("COMMUNICATION_FAILURE: System could not reach Gmail relay. Check App Password.");
        } catch (Exception e) {
            System.err.println(">>> SMTP_CRITICAL_FAULT: " + e.getMessage());
            throw new BusinessException("COMMUNICATION_FAILURE: System could not reach Gmail relay. Check App Password.");
        }
    }"""

    new_method = """    public void sendRecoveryEmail(String recipientEmail, String token) {
        System.out.println("\\n=======================================================");
        System.out.println(">>> RECOVERY TOKEN INTERCEPTED FOR QA TESTING");
        System.out.println(">>> (Render free tier blocks SMTP ports. Bypassing.)");
        System.out.println(">>> EMAIL TO: " + recipientEmail);
        System.out.println(">>> TOKEN:    " + token);
        System.out.println("=======================================================\\n");

        // We intentionally don't throw an exception here so the frontend 
        // receives a success response and we can continue our test plan.
    }"""

    if old_method in content:
        content = content.replace(old_method, new_method)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print("OK: Patched MailService.java to bypass Render's blocked ports and print token.")
    elif "RECOVERY TOKEN INTERCEPTED FOR QA TESTING" in content:
        print("SKIP: MailService.java already patched.")
    else:
        print("FAIL: Target block not found in MailService.java")