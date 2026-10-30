// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java
package com.gesolutions.erp.modules.auth.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

/**
 * GE SOLUTIONS - COMMUNICATION HUB
 * SMTP is behind a switch: ge.solutions.mail.enabled (default off,
 * because Render's free tier blocks SMTP ports). Off or on-failure we
 * fall back to the QA console log so the recovery flow always works.
 * Flip the switch in config to turn real email on later - no code change.
 */
@Service
@RequiredArgsConstructor
public class MailService {

    private final JavaMailSender mailSender;

    @Value("${ge.solutions.mail.enabled:false}")
    private boolean mailEnabled;

    @Value("${ge.solutions.mail.from:no-reply@gesolutions.com}")
    private String mailFrom;

    /**
     * TRANSMIT RECOVERY TOKEN
     * Real SMTP when enabled; QA console log otherwise. Never throws,
     * so the frontend always gets a success response.
     */
    public void sendRecoveryEmail(String recipientEmail, String token) {
        if (mailEnabled) {
            try {
                SimpleMailMessage message = new SimpleMailMessage();
                message.setFrom(mailFrom);
                message.setTo(recipientEmail);
                message.setSubject("GE Solutions - Password Recovery");
                message.setText("Your recovery token: " + token);
                mailSender.send(message);
                System.out.println(">>> [MAIL] Recovery email sent to " + recipientEmail);
                return;
            } catch (Exception e) {
                System.err.println(">>> [MAIL] SMTP send failed, using QA log instead: " + e.getMessage());
            }
        }

        // fix181: a recovery code is NEVER printed to the server log (anyone with log access could read it).
        System.out.println(">>> [MAIL] Mail is off; no recovery email sent to " + recipientEmail + ".");
    }

    /**
     * fix279: OWNER RECOVERY CODE. Returns true only when the mail was really handed to the mail server.
     * The code is never written to the server log.
     */
    public boolean sendOwnerCode(String recipientEmail, String code, int minutesValid) {
        if (!mailEnabled || recipientEmail == null || recipientEmail.isBlank()) {
            System.out.println(">>> [MAIL] Mail is off or the root has no email; no recovery code sent.");
            return false;
        }
        try {
            SimpleMailMessage message = new SimpleMailMessage();
            message.setFrom(mailFrom);
            message.setTo(recipientEmail);
            message.setSubject("Golden Seed - your recovery code");
            message.setText("Your Golden Seed recovery code is: " + code + "\n\n"
                    + "It works once and runs out in " + minutesValid + " minutes.\n"
                    + "If you did not ask for it, ignore this email: nothing was changed.");
            mailSender.send(message);
            System.out.println(">>> [MAIL] Recovery code sent.");
            return true;
        } catch (Exception e) {
            System.err.println(">>> [MAIL] The recovery code could not be sent: " + e.getClass().getSimpleName());
            return false;
        }
    }
}
