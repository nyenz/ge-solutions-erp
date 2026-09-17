// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/StaffManagementService.java
package com.gesolutions.erp.modules.auth.service;

import com.gesolutions.erp.modules.auth.model.*;
import com.gesolutions.erp.modules.auth.dto.*;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Random;
import java.util.UUID;

/**
 * GOLDEN SEED ERP - STAFF MANAGEMENT ENGINE (V5)
 * 
 * Physically manages the operator lifecycle.
 * Added: Dynamic Role Switching (Promotion/Demotion).
 */
@Service
@RequiredArgsConstructor
public class StaffManagementService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuditService auditService;

    /**
     * OPERATOR PROVISIONING
     */
    @Transactional
    public UserCreateResponse createStaff(UserCreateRequest request) {
        if (userRepository.findByUsername(request.getUsername()).isPresent()) {
            throw new BusinessException("REGISTRY_ERROR: Username '" + request.getUsername() + "' is already registered.");
        }

        String tempKey = generateIndustrialKey();
        
        // Default new users to the requested role (or Manager if null)
        Role initialRole = request.getRole() != null ? request.getRole() : Role.ROLE_MANAGER;

        User newUser = User.builder()
                .id(UUID.randomUUID())
                .username(request.getUsername())
                .email(request.getEmail())
                .password(passwordEncoder.encode(tempKey))
                .role(initialRole)
                .isRoot(false)
                .isActive(true)
                .mustChangePassword(true)
                .build();

        try {
            userRepository.save(newUser);
            auditService.logAction("OPERATOR_PROVISIONED", 
                "New " + initialRole + " account created: " + request.getUsername());
        } catch (Exception e) {
            throw new BusinessException("DATABASE_REJECTION: Email conflict.");
        }

        return UserCreateResponse.builder()
                .username(newUser.getUsername())
                .temporaryPassword(tempKey)
                .role(initialRole.name())
                .build();
    }

    /**
     * ROLE SWITCHING (PROMOTION/DEMOTION)
     * Allows Root to toggle an operator between ADMIN and MANAGER.
     */
    @Transactional
    public void updateUserRole(String username, Role newRole) {
        User target = userRepository.findByUsername(username)
                .orElseThrow(() -> new BusinessException("OPERATOR_NOT_FOUND"));

        // HANDBRAKE: Cannot change the Role of the Root Owner
        if (target.isRoot()) {
            throw new BusinessException("AUTHORITY_FAULT: ROOT_ROLE_IS_IMMUTABLE");
        }

        target.setRole(newRole);
        userRepository.save(target);

        auditService.logAction("RANK_ADJUSTMENT", 
            "Operator " + username + " rank shifted to " + newRole);
    }

    /**
     * ACCOUNT STATUS CONTROL
     */
    @Transactional
    public void toggleOperatorStatus(String username, boolean active) {
        User target = userRepository.findByUsername(username)
                .orElseThrow(() -> new BusinessException("OPERATOR_NOT_FOUND"));

        if (target.isRoot()) {
            throw new BusinessException("GOVERNANCE_FAULT: MASTER_ACCOUNTS_ARE_IMMUTABLE");
        }

        target.setActive(active);
        userRepository.save(target);

        String stateName = active ? "ACTIVATED" : "SUSPENDED";
        auditService.logAction("OPERATOR_STATUS_CHANGE", "Account [" + username + "] moved to " + stateName);
    }

    /**
     * EMERGENCY CREDENTIAL RESET
     */
    @Transactional
    public String resetOperatorPassword(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new BusinessException("OPERATOR_NOT_FOUND"));
        
        String newKey = generateIndustrialKey();
        user.setPassword(passwordEncoder.encode(newKey));
        user.setMustChangePassword(true);
        
        userRepository.save(user);
        auditService.logAction("CREDENTIAL_RESET", "Temporary key generated for: " + username);
        return newKey;
    }

    @Transactional(readOnly = true)
    public List<User> getAllOperators() {
        return userRepository.findAll();
    }

    private String generateIndustrialKey() {
        String chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        StringBuilder sb = new StringBuilder("NY-");
        Random rnd = new Random();
        for (int i = 0; i < 4; i++) {
            sb.append(chars.charAt(rnd.nextInt(chars.length())));
        }
        return sb.toString();
    }
}