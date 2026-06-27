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

/**
 * NYENZ ERP - AUTHENTICATION & RECOVERY ENGINE (V2.0 - REBOOT)
 * 
 * Manages the Secure Identity Handshake.
 */
@Service
@RequiredArgsConstructor
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final UserDetailsService userDetailsService;
    private final UserRepository userRepository; 
    private final JwtService jwtService;
    private final AuditService auditService;
    private final MailService mailService;
    private final PasswordEncoder passwordEncoder;

    /**
     * AUTHORIZE OPERATOR
     * Returns the full Identity Binder to the UI.
     */
    @Transactional
    public LoginResponse authenticate(LoginRequest request) {
        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
            );
        } catch (Exception e) {
            // DIAGNOSTIC: Log the REAL cause so we can see it in Render logs
            System.err.println(">>> [AUTH_FAULT] authenticate() threw: " + e.getClass().getName() + " -- " + e.getMessage());
            throw new BusinessException("IDENTIFICATION_FAILED: INVALID SECURITY KEY");
        }

        User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> new BusinessException("REGISTRY_ERROR: OPERATOR_MISSING"));

        if (!user.isActive()) {
            throw new BusinessException("AUTHORITY_REVOKED: ACCOUNT_SUSPENDED");
        }

        // Increment session version — invalidates all previously issued tokens
        user.setSessionVersion(user.getSessionVersion() + 1);
        userRepository.save(user);

        final UserDetails userDetails = userDetailsService.loadUserByUsername(request.getUsername());
        // Embed sessionVersion in JWT so we can validate it on every request
        java.util.Map<String, Object> extraClaims = new java.util.HashMap<>();
        extraClaims.put("sv", user.getSessionVersion());
        String token = jwtService.generateToken(extraClaims, userDetails);

        auditService.logAction("LOGIN_SUCCESS", "Operator session established: " + user.getUsername());

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
     * ROOT RECOVERY PROTOCOL
     * Fires SMTP reset and forces a password change.
     */
    @Transactional
    public void initiateRootRecovery(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new BusinessException("IDENTITY_FAULT: EMAIL_NOT_FOUND"));

        if (!user.isRoot()) {
            throw new BusinessException("ACCESS_DENIED: ONLY MASTER FOUNDER AUTHORIZED FOR SELF-RECOVERY.");
        }

        // Generate Code (Example: NY-REC-48291)
        String recoveryToken = "NY-REC-" + (10000 + (int)(Math.random() * 90000));
        
        // PHYSICALLY REWRITE HASH
        user.setPassword(passwordEncoder.encode(recoveryToken));
        user.setMustChangePassword(true); // RE-ENABLE THE TRAP
        userRepository.save(user);

        // Transmit Signal
        mailService.sendRecoveryEmail(user.getEmail(), recoveryToken);

        auditService.logAction("ROOT_RECOVERY_TRIGGERED", "Emergency token transmitted to Master Owner.");
    }
}