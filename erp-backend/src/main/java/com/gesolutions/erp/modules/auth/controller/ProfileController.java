// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/ProfileController.java
package com.gesolutions.erp.modules.auth.controller;

import com.gesolutions.erp.config.LoginRateLimiter;
import com.gesolutions.erp.modules.auth.dto.LoginResponse;
import com.gesolutions.erp.modules.auth.dto.PasswordChangeRequest;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.auth.service.AuthService;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * GOLDEN SEED ERP - MY ACCOUNT (own key change, who am I)
 */
@RestController
@RequestMapping("/api/v1/profile")
@RequiredArgsConstructor
public class ProfileController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuditService auditService;
    private final AuthService authService;
    private final LoginRateLimiter rateLimiter;

    /**
     * SELF-SERVICE: CHANGE MY KEY.
     * fix181: it never switches a suspended account back on; it signs out every OTHER device of this account and hands
     * this device a fresh token (so the person who changed the key is not signed out by their own change).
     */
    @Transactional
    @PutMapping("/change-password")
    public ResponseEntity<LoginResponse> updateSecurityKey(@RequestBody PasswordChangeRequest request) {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new BusinessException("SECURITY_FAULT: Your session is not valid. Sign in again."));

        String limitKey = "oldkey|" + username.toLowerCase(Locale.ROOT);
        if (rateLimiter.isOverLimit(limitKey, 5)) {
            throw new BusinessException("TOO_MANY_ATTEMPTS: Too many wrong current keys. Wait 15 minutes and try again.");
        }
        if (request.getOldPassword() == null || !passwordEncoder.matches(request.getOldPassword(), user.getPassword())) {
            rateLimiter.recordOther(limitKey);
            throw new BusinessException("OLD_PASSWORD_INCORRECT: The current key is not right.");
        }

        String np = request.getNewPassword();
        com.gesolutions.erp.modules.auth.service.PasswordPolicy.check(np, username);   // fix279: shared rules
        if (passwordEncoder.matches(np, user.getPassword())) {
            throw new BusinessException("PASSWORD_POLICY: The new key must be different from the current one.");
        }
        rateLimiter.clearOther(limitKey);

        user.setPassword(passwordEncoder.encode(np));
        user.setMustChangePassword(false);
        user.setTempKeyExpiresAt(null);
        user.bumpSessionVersion();
        userRepository.save(user);

        auditService.logActionAfterCommit("SECURITY_KEY_UPDATE", "Operator " + username + " changed their own key. Other devices were signed out.");
        return ResponseEntity.ok(authService.buildResponse(user));
    }

    /**
     * fix279: the OWNER sets the real email that receives the recovery code. Only the root account, and only with its
     * current key. The email is also checked to look like an address and not the old placeholder.
     */
    @Transactional
    @PutMapping("/recovery-email")
    public ResponseEntity<Map<String, String>> setRecoveryEmail(@RequestBody Map<String, String> request) {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new BusinessException("SECURITY_FAULT: Your session is not valid. Sign in again."));
        if (!user.isRoot()) {
            throw new BusinessException("RANK_DENIED: Only the owner account can set the recovery email.");
        }
        String limitKey = "oldkey|" + username.toLowerCase(Locale.ROOT);
        if (rateLimiter.isOverLimit(limitKey, 5)) {
            throw new BusinessException("TOO_MANY_ATTEMPTS: Too many wrong current keys. Wait 15 minutes and try again.");
        }
        String pw = request == null ? null : request.get("password");
        if (pw == null || !passwordEncoder.matches(pw, user.getPassword())) {
            rateLimiter.recordOther(limitKey);
            throw new BusinessException("OLD_PASSWORD_INCORRECT: The current key is not right.");
        }
        rateLimiter.clearOther(limitKey);
        String email = request.get("email") == null ? "" : request.get("email").trim();
        if (!email.matches("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$") || email.length() > 120 || email.toLowerCase(Locale.ROOT).endsWith("@gesolutions.com")) {
            throw new BusinessException("EMAIL_NOT_VALID: Type a real email address that you can open.");
        }
        user.setEmail(email);
        user.setResetToken(null);
        userRepository.save(user);
        auditService.logActionAfterCommit("RECOVERY_EMAIL_CHANGED", "Operator " + username + " changed the owner recovery email.");
        return ResponseEntity.ok(Map.of("message", "Saved. Recovery codes will go to " + email + "."));
    }

    /** WHO AM I. fix181: a small answer (it used to send the whole account row, password hash included). */
    @GetMapping("/me")
    public ResponseEntity<Map<String, Object>> getMyProfile() {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User u = userRepository.findByUsername(username).orElseThrow();
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", u.getId());
        m.put("username", u.getUsername());
        m.put("role", u.getRole());
        m.put("isRoot", u.isRoot());
        m.put("active", u.isActive());
        m.put("mustChangePassword", u.isMustChangePassword());
        m.put("email", u.getEmail());
        m.put("showGuide", Boolean.TRUE.equals(u.getShowGuide()));   // fix262
        return ResponseEntity.ok(m);
    }

    /** fix262 (David): the first-visit guide was watched or skipped -- it is not offered again, on any device. */
    @PostMapping("/guide-seen")
    public ResponseEntity<Map<String, Object>> guideSeen() {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User u = userRepository.findByUsername(username).orElseThrow();
        if (Boolean.TRUE.equals(u.getShowGuide())) { u.setShowGuide(false); userRepository.save(u); }
        return ResponseEntity.ok(Map.of("ok", true));
    }
}
