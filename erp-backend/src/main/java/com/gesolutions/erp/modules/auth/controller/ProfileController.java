// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/ProfileController.java
package com.gesolutions.erp.modules.auth.controller;

import com.gesolutions.erp.modules.auth.dto.PasswordChangeRequest;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

/**
 * GOLDEN SEED ERP - PROFILE & SECURITY PANEL
 * 
 * Physically manages individual operator security settings.
 * Primary purpose: Handling the 'mustChangePassword' protocol.
 */
@RestController
@RequestMapping("/api/v1/profile")
@RequiredArgsConstructor
public class ProfileController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuditService auditService;

    /**
     * SELF-SERVICE: CHANGE SECURITY KEY
     * 
     * Verifies the old password against the BCrypt hash before 
     * committing the new key to the database.
     */
    @PutMapping("/change-password")
    public ResponseEntity<Void> updateSecurityKey(@RequestBody PasswordChangeRequest request) {
        // 1. Identify the current operator via the JWT Context
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new BusinessException("SECURITY_FAULT: SESSION_INVALID"));

        // 2. Enforce password policy
        String np = request.getNewPassword();
        if (np == null || np.length() < 8) {
            throw new BusinessException("PASSWORD_POLICY: Minimum 8 characters required.");
        }
        boolean hasUpper  = np.chars().anyMatch(Character::isUpperCase);
        boolean hasDigit  = np.chars().anyMatch(Character::isDigit);
        if (!hasUpper || !hasDigit) {
            throw new BusinessException("PASSWORD_POLICY: Must contain at least one uppercase letter and one number.");
        }

        // 3. Verify current credentials (Hardware check)
        if (!passwordEncoder.matches(request.getOldPassword(), user.getPassword())) {
            throw new BusinessException("IDENTIFICATION_FAILED: OLD_PASSWORD_INCORRECT");
        }

        // 3. Physical Rewrite
        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        
        // 4. Release the Handbrake
        // Once changed, the user is no longer restricted to the settings page.
        user.setMustChangePassword(false);
        user.setActive(true);

        userRepository.save(user);

        // 5. Audit the event
        auditService.logAction("SECURITY_KEY_UPDATE", "Operator " + username + " successfully updated their master password.");

        return ResponseEntity.ok().build();
    }

    /**
     * READOUT: GET CURRENT IDENTITY
     */
    @GetMapping("/me")
    public ResponseEntity<User> getMyProfile() {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User user = userRepository.findByUsername(username).orElseThrow();
        // We return the user object (minus password hash handled by JSON Ignore or DTO)
        return ResponseEntity.ok(user);
    }
}