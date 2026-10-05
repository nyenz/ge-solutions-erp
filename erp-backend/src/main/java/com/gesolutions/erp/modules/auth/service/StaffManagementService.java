// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/StaffManagementService.java
package com.gesolutions.erp.modules.auth.service;

import com.gesolutions.erp.modules.auth.model.*;
import com.gesolutions.erp.modules.auth.dto.*;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * GOLDEN SEED ERP - STAFF ACCOUNTS (fix181: rank model, LLM_CONTEXT_GUIDE.md Section 5)
 *
 * Who may do what (checked HERE, on the server; the page only hides buttons):
 *  - Nobody can create an Admin, promote anyone to Admin, or touch the Admin account (there is exactly one Admin).
 *  - Admin: creates and manages every other rank, including Director.
 *  - Director: creates and manages Manager, Secretary and Employee only (never a Director, never the Admin).
 *  - Nobody changes, suspends or resets THEMSELVES through these routes.
 * Suspending, resetting a key and changing a rank all sign that person out at once (session number goes up).
 * A temporary key is 10 random characters (SecureRandom) and stops working after 7 days.
 */
@Service
@RequiredArgsConstructor
public class StaffManagementService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuditService auditService;
    private final NotificationService notificationService;

    public static final int TEMP_KEY_DAYS = 7;
    private static final Pattern USERNAME = Pattern.compile("^[A-Za-z0-9._-]{3,30}$");
    private static final Pattern EMAIL = Pattern.compile("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$");
    private static final SecureRandom RANDOM = new SecureRandom();

    private User actor() {
        String name = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByUsername(name)
                .orElseThrow(() -> new BusinessException("SECURITY_FAULT: Your session is not valid. Sign in again."));
    }

    /** The actor may manage a person of this rank (strictly below their own). Admin is never managed here. */
    private static void requireCanManage(User actor, Role targetRank, String what) {
        if (targetRank == Role.ROLE_ADMIN) {
            throw new BusinessException("RANK_DENIED: The Admin account cannot be " + what + " here.");
        }
        if (!actor.getRole().isOwnerLevel() || !actor.getRole().outranks(targetRank)) {
            throw new BusinessException("RANK_DENIED: You can only manage ranks below your own.");
        }
    }

    private User target(String username) {
        return userRepository.findByUsernameIgnoreCase(username == null ? "" : username.trim())
                .orElseThrow(() -> new BusinessException("OPERATOR_NOT_FOUND: No account with that username."));
    }

    // ── OPERATOR PROVISIONING ───────────────────────────────────────────────
    @Transactional
    public UserCreateResponse createStaff(UserCreateRequest request) {
        User actor = actor();
        String username = request.getUsername() == null ? "" : request.getUsername().trim();
        String email = request.getEmail() == null ? "" : request.getEmail().trim().toLowerCase(Locale.ROOT);
        Role rank = request.getRole() != null ? request.getRole() : Role.ROLE_MANAGER;

        if (!USERNAME.matcher(username).matches()) {
            throw new BusinessException("USERNAME_INVALID: Use 3 to 30 letters, numbers, dot, dash or underscore (no spaces).");
        }
        if (!EMAIL.matcher(email).matches()) {
            throw new BusinessException("EMAIL_INVALID: Enter the full email address (for example name@company.com).");
        }
        requireCanManage(actor, rank, "created");
        if (userRepository.findByUsernameIgnoreCase(username).isPresent()) {
            throw new BusinessException("USERNAME_TAKEN: The username '" + username + "' is already used (capital letters do not count).");
        }
        if (userRepository.findByEmailIgnoreCase(email).isPresent()) {
            throw new BusinessException("EMAIL_TAKEN: Another account already uses this email.");
        }

        String tempKey = generateIndustrialKey();
        User saved = userRepository.save(User.builder()
                .id(UUID.randomUUID())
                .username(username)
                .email(email)
                .password(passwordEncoder.encode(tempKey))
                .role(rank)
                .isRoot(false)
                .isActive(true)
                .mustChangePassword(true)
                .tempKeyExpiresAt(LocalDateTime.now().plusDays(TEMP_KEY_DAYS))
                .notifySince(LocalDateTime.now())
                .build());

        auditService.logActionAfterCommit("OPERATOR_PROVISIONED", "New " + rank + " account created: " + username);
        notificationService.emitRaw("STAFF_PROVISIONED", "INFO",
                "Operator " + username + " provisioned as " + rank.label().toUpperCase(Locale.ROOT) + ".",
                "STAFF", saved.getId(), "ROLE_DIRECTOR");

        return UserCreateResponse.builder()
                .username(username)
                .temporaryPassword(tempKey)
                .role(rank.name())
                .build();
    }

    // ── RANK CHANGE ─────────────────────────────────────────────────────────
    @Transactional
    public void updateUserRole(String username, Role newRole) {
        User actor = actor();
        User target = target(username);
        if (target.getId().equals(actor.getId())) {
            throw new BusinessException("RANK_DENIED: You cannot change your own rank.");
        }
        if (target.isRoot()) {
            throw new BusinessException("RANK_DENIED: The Admin account cannot be changed.");
        }
        if (newRole == null) throw new BusinessException("RANK_REQUIRED: Choose the new rank.");
        if (newRole == target.getRole()) return;   // same rank: nothing to do, nothing to log
        requireCanManage(actor, target.getRole(), "changed");
        requireCanManage(actor, newRole, "given");

        Role old = target.getRole();
        target.setRole(newRole);
        target.setNotifySince(LocalDateTime.now());
        target.bumpSessionVersion();   // they sign in again and get the right menus
        userRepository.save(target);

        auditService.logActionAfterCommit("RANK_ADJUSTMENT", "Operator " + target.getUsername() + " rank changed from " + old + " to " + newRole);
        notificationService.emitRaw("STAFF_ROLE_CHANGED", "WARN",
                "Operator " + target.getUsername() + " is now " + newRole.label().toUpperCase(Locale.ROOT) + ".",
                "STAFF", target.getId(), "ROLE_DIRECTOR");
    }

    // ── SUSPEND / ACTIVATE ──────────────────────────────────────────────────
    @Transactional
    public void toggleOperatorStatus(String username, boolean active) {
        User actor = actor();
        User target = target(username);
        if (target.getId().equals(actor.getId())) {
            throw new BusinessException("RANK_DENIED: You cannot suspend or activate your own account.");
        }
        if (target.isRoot()) {
            throw new BusinessException("RANK_DENIED: The Admin account cannot be suspended.");
        }
        requireCanManage(actor, target.getRole(), active ? "activated" : "suspended");
        if (target.isActive() == active) return;

        target.setActive(active);
        target.bumpSessionVersion();   // a suspended person is signed out at once
        userRepository.save(target);

        String stateName = active ? "ACTIVATED" : "SUSPENDED";
        auditService.logActionAfterCommit("OPERATOR_STATUS_CHANGE", "Account [" + target.getUsername() + "] moved to " + stateName);
        notificationService.emitRaw(active ? "STAFF_ACTIVATED" : "STAFF_SUSPENDED", active ? "POSITIVE" : "WARN",
                "Operator " + target.getUsername() + " " + stateName.toLowerCase(Locale.ROOT) + ".",
                "STAFF", target.getId(), "ROLE_DIRECTOR");
    }

    // ── KEY RESET ───────────────────────────────────────────────────────────
    @Transactional
    public String resetOperatorPassword(String username) {
        User actor = actor();
        User target = target(username);
        if (target.getId().equals(actor.getId())) {
            throw new BusinessException("RANK_DENIED: Change your own key on the Security tab.");
        }
        if (target.isRoot()) {
            throw new BusinessException("RANK_DENIED: The Admin key cannot be reset here (use the owner recovery).");
        }
        requireCanManage(actor, target.getRole(), "reset");

        String newKey = generateIndustrialKey();
        target.setPassword(passwordEncoder.encode(newKey));
        target.setMustChangePassword(true);
        target.setTempKeyExpiresAt(LocalDateTime.now().plusDays(TEMP_KEY_DAYS));
        target.bumpSessionVersion();
        userRepository.save(target);

        auditService.logActionAfterCommit("CREDENTIAL_RESET", "Temporary key generated for: " + target.getUsername());
        notificationService.emitRaw("KEY_RESET", "WARN",
                "Security key reset for " + target.getUsername() + ". They must change it at next sign in.",
                "STAFF", target.getId(), "ROLE_DIRECTOR");
        return newKey;
    }

    /** Every account, as a small answer (never the password hash), highest rank first. */
    @Transactional(readOnly = true)
    public List<StaffDTO> getAllOperators() {
        return userRepository.findAll().stream()
                .sorted(Comparator.comparingInt((User u) -> u.getRole() == null ? 0 : -u.getRole().rank())
                        .thenComparing(u -> u.getUsername().toLowerCase(Locale.ROOT)))
                .map(StaffDTO::of)
                .toList();
    }

    /** "NY-" + 5 + "-" + 5 random characters, no look-alike letters (fix181: SecureRandom, about 10^15 possibilities). */
    static String generateIndustrialKey() {
        String chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        StringBuilder sb = new StringBuilder("NY-");
        for (int i = 0; i < 10; i++) {
            if (i == 5) sb.append('-');
            sb.append(chars.charAt(RANDOM.nextInt(chars.length())));
        }
        return sb.toString();
    }
}
