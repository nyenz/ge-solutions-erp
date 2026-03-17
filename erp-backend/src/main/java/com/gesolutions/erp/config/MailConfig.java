// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/MailConfig.java
package com.gesolutions.erp.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.JavaMailSenderImpl;

import java.util.Properties;

/**
 * NYENZ ERP - SMTP TRANSMISSION HUB
 * 
 * Physically manages the connection to Gmail's relay servers.
 * CREDENTIAL STATUS: ACTIVE (Key Integrated)
 */
@Configuration
public class MailConfig {

    @Bean
    public JavaMailSender javaMailSender() {
        JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
        
        // --- 1. TRANSMISSION TARGET ---
        mailSender.setHost("smtp.gmail.com");
        mailSender.setPort(587); // Standard TLS Port
        
        // --- 2. AUTHENTICATION CREDENTIALS ---
        mailSender.setUsername("nyenzdav@gmail.com"); 
        
        // THE GOOGLE APP PASSWORD (PERMISSION KEY)
        mailSender.setPassword("gfbf uszx pkkm arez"); 

        // --- 3. HARDWARE PROPERTIES ---
        Properties props = mailSender.getJavaMailProperties();
        props.put("mail.transport.protocol", "smtp");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true"); // CRITICAL: Encrypts the signal
        
        // DEBUG MODE: Prints email logs to your console (Disable in production)
        props.put("mail.debug", "true"); 

        return mailSender;
    }
}