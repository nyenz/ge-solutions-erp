// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/AuthService.java
package com.gesolutions.erp.modules.auth.service;

import com.gesolutions.erp.modules.auth.dto.LoginRequest;
import com.gesolutions.erp.modules.auth.dto.LoginResponse;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Random;

/**
 * NYENZ ERP - AUTHENTICATION & RECOVERY ENGINE
 * 
 * Manages Login Handshakes and the Root Owner's "Panic Button".
 */
@Service
@RequiredArgsConstructor
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final UserDetailsService userDetailsService;
    private final UserRepository userRepository; 
    private final JwtService jwtService;
    private final AuditService auditService;
    private final MailService mailService; // Link to Email Engine
    private final PasswordEncoder passwordEncoder;

    /**
     * AUTHORIZE OPERATOR (Login)
     */
    @Transactional
    public LoginResponse authenticate(LoginRequest request) {
        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
            );
        } catch (Exception e) {
            throw new BusinessException("IDENTIFICATION_FAILED: INVALID CREDENTIALS");
        }

        User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> new BusinessException("REGISTRY_ERROR: OPERATOR MISSING"));

        auditService.logAction("LOGIN_SUCCESS", 
            String.format("Operator [%s] authorized session. Role: %s", user.getUsername(), user.getRole()));

        final UserDetails userDetails = userDetailsService.loadUserByUsername(request.getUsername());
        String token = jwtService.generateToken(userDetails);

        return LoginResponse.builder()
                .token(token)
                .user(LoginResponse.UserData.builder()
                        .id(user.getId())
                        .username(user.getUsername())
                        .role(user.getRole())
                        .isRoot(user.isRoot()) 
                        .mustChangePassword(user.isMustChangePassword())
                        .build())
                .build();
    }

    /**
     * ROOT RECOVERY PROTOCOL (The Panic Button)
     * 
     * Logic:
     * 1. Check if email exists.
     * 2. SECURITY HANDBRAKE: Check if user is ROOT. 
     *    - If ROOT: Generate code, save to DB, send Email.
     *    - If MANAGER: Block request, tell them to contact Admin.
     */
    @Transactional
    public void initiateRootRecovery(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new BusinessException("IDENTITY_FAULT: EMAIL NOT FOUND IN REGISTRY"));

        // HANDBRAKE: Only Root can use self-service recovery
        if (!user.isRoot()) {
            throw new BusinessException("ACCESS_DENIED: Standard Operators must request reset from Root Owner.");
        }

        // Generate Temporary Access Code
        String recoveryToken = generateRecoveryCode();
        
        // Update User Record (Force password change on next login)
        user.setPassword(passwordEncoder.encode(recoveryToken));
        user.setMustChangePassword(true); 
        userRepository.save(user);

        // Physically transmit email
        mailService.sendRecoveryEmail(user.getEmail(), recoveryToken);

        auditService.logAction("ROOT_RECOVERY_TRIGGERED", "Emergency reset protocol initiated for: " + user.getUsername());
    }

    private String generateRecoveryCode() {
        return "NY-REC-" + (10000 + new Random().nextInt(90000)); // e.g., NY-REC-45892
    }
}