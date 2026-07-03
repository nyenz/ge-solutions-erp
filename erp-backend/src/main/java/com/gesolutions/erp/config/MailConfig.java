// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/MailConfig.java
package com.gesolutions.erp.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.JavaMailSenderImpl;

import java.util.Properties;

@Configuration
public class MailConfig {

    @Value("${MAIL_USERNAME}")
    private String mailUsername;

    @Value("${MAIL_PASSWORD}")
    private String mailPassword;

    @Bean
    public JavaMailSender javaMailSender() {
        JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
        mailSender.setHost("smtp.gmail.com");
        // BEST PRACTICE: Use Port 465 with strict SSL for cloud deployments.
        // Port 587 (STARTTLS) is frequently blocked by cloud firewalls.
        mailSender.setPort(465);
        mailSender.setUsername(mailUsername);
        mailSender.setPassword(mailPassword);

        Properties props = mailSender.getJavaMailProperties();
        props.put("mail.transport.protocol", "smtp");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.ssl.enable", "true");
        props.put("mail.debug", "false");

        // VITAL FIX: JavaMail's default timeout is INFINITE.
        // Without these, if Gmail's SMTP relay is slow to respond, the
        // request hangs until Render's own gateway kills it and returns
        // an HTML error page instead of JSON. That is why the frontend
        // shows "RECOVERY_FAULT: UNKNOWN" -- it cannot find a .message
        // field in a non-JSON response. With these limits, a real SMTP
        // failure surfaces within 10 seconds with a proper error message.
        props.put("mail.smtp.connectiontimeout", "10000");
        props.put("mail.smtp.timeout", "10000");
        props.put("mail.smtp.writetimeout", "10000");

        return mailSender;
    }
}