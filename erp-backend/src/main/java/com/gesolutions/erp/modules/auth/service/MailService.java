// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java
package com.gesolutions.erp.modules.auth.service;

import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

/**
 * GE SOLUTIONS - COMMUNICATION HUB
 * Upgraded to propagate SMTP errors to the UI for diagnostic transparency.
 */
@Service
@RequiredArgsConstructor
public class MailService {

    private final JavaMailSender mailSender;

    /**
     * TRANSMIT RECOVERY TOKEN
     * Physically attempts to hit the Gmail relay.
     */
    public void sendRecoveryEmail(String recipientEmail, String token) {
        SimpleMailMessage message = new SimpleMailMessage();
        
        // --- VITAL: THE FROM ADDRESS ---
        // Gmail requires this to match the account in MailConfig exactly
        message.setFrom("nyenzdav@gmail.com"); 
        message.setTo(recipientEmail);
        message.setSubject("GE SOLUTIONS | Master Key Recovery Protocol");
        
        String body = "SYSTEM ALERT: A Master Key reset was requested.\n\n" +
                      "Your Temporary Access Token is: " + token + "\n\n" +
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
    }
}