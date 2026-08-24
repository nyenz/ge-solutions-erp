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

        System.out.println("\n=======================================================");
        System.out.println(">>> RECOVERY TOKEN INTERCEPTED FOR QA TESTING");
        System.out.println(">>> (SMTP disabled or failed. Bypassing.)");
        System.out.println(">>> EMAIL TO: " + recipientEmail);
        System.out.println(">>> TOKEN:    " + token);
        System.out.println("=======================================================\n");
    }
}
