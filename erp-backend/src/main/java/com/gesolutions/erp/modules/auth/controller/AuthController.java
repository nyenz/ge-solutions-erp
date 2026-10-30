// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/AuthController.java
package com.gesolutions.erp.modules.auth.controller;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.auth.dto.LoginRequest;
import com.gesolutions.erp.modules.auth.dto.LoginResponse;
import com.gesolutions.erp.modules.auth.service.AuthService;
import com.gesolutions.erp.config.LoginRateLimiter;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

import java.util.Map;

/**
 * GOLDEN SEED ERP - SIGN-IN GATEWAY
 * Open without a token: health check, sign in, sign out, owner recovery request.
 */
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;
    private final LoginRateLimiter rateLimiter;
    private final AuditService auditService;
    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;
    private static volatile boolean forwardedLogged = false;

    /** fix278: true on the practice (DEMO) copy, false on the real server (GE_SOLUTIONS_SEED_DEMO_DATA=false). */
    @org.springframework.beans.factory.annotation.Value("${ge.solutions.seed-demo-data:true}")
    private boolean demoMode;

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        // fix278: "demo" tells the pages whether to show the DEMO strip and the FRESH START tick box.
        return ResponseEntity.ok(Map.of("status", "ENGINE_ONLINE", "demo", String.valueOf(demoMode)));
    }

    /**
     * fix181: the caller's address. X-Forwarded-For can be written by the caller, so its FIRST value can be faked; the
     * LAST value is the one added by Render's own proxy. Both are printed once at start so this can be checked in the
     * Render log.
     */
    public static String clientIp(HttpServletRequest req) {
        String xff = req.getHeader("X-Forwarded-For");
        if (xff == null || xff.isBlank()) return req.getRemoteAddr();
        String[] parts = xff.split(",");
        String last = parts[parts.length - 1].trim();
        if (!forwardedLogged) {
            forwardedLogged = true;
            System.out.println(">>> [IP] X-Forwarded-For first=" + parts[0].trim() + " last=" + last + " remote=" + req.getRemoteAddr());
        }
        return last.isEmpty() ? req.getRemoteAddr() : last;
    }

    /** The typed username is not trusted: cut to 50 characters, no control characters, "(unknown)" when empty. */
    private static String typedName(LoginRequest r) {
        String n = r == null || r.getUsername() == null ? "" : r.getUsername().replaceAll("[\\p{Cntrl}]", " ").trim();
        if (n.length() > 50) n = n.substring(0, 50);
        return n.isEmpty() ? "(unknown)" : n;
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest request, HttpServletRequest httpRequest) {
        String ip = clientIp(httpRequest);
        String name = typedName(request);
        if (rateLimiter.isBlocked(name, ip)) {
            throw new BusinessException("TOO_MANY_ATTEMPTS: Too many wrong tries for this username. Wait "
                    + rateLimiter.minutesLeft(name, ip) + " minutes, or ask the Director to reset your key.");
        }
        try {
            LoginResponse response = authService.authenticate(request, ip);
            rateLimiter.clearRecord(name, ip);
            return ResponseEntity.ok(response);
        } catch (BusinessException e) {
            boolean nowBlocked = rateLimiter.recordFailure(name, ip);
            String code = e.getMessage() == null ? "FAILED" : e.getMessage().split(":")[0];
            auditService.logActionAs(name, "LOGIN_FAILED", "Login refused from IP " + ip + ": " + code);
            if (nowBlocked) {
                auditService.logActionAs(name, "LOGIN_BLOCKED", "Too many wrong tries from IP " + ip + ". Sign-in paused for 15 minutes.");
                // fix181 (17.2): written at once (the request itself fails); entity = a fixed id per username so it groups
                notificationService.emitNow("LOGIN_BLOCKED", "Sign-in for '" + name + "' paused after too many wrong tries (IP " + ip + ").",
                        "SYSTEM", java.util.UUID.nameUUIDFromBytes(("login|" + name.toLowerCase()).getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            }
            throw e;
        }
    }

    /** fix181: sign out on the server too, so the token of this session stops working at once. */
    @PostMapping("/logout")
    public ResponseEntity<Map<String, String>> logout() {
        Authentication a = SecurityContextHolder.getContext().getAuthentication();
        if (a != null && !(a instanceof AnonymousAuthenticationToken)) {
            authService.logout(a.getName());
        }
        return ResponseEntity.ok(Map.of("status", "SIGNED_OUT"));
    }

    // ---- fix279: OWNER (ROOT) RECOVERY BY EMAIL -------------------------------------------------------------
    // Only the ONE root account can recover this way. The answer to the first call is always the same, so nobody can
    // learn whether mail is on or what the email is. A code works once, for 15 minutes, 5 tries. Staff keep asking the
    // Director; the emergency way in without email stays (ADMIN_RESET_ONCE).
    private static final int CODE_MINUTES = 15;
    private static final int CODE_TRIES = 5;
    private static final java.security.SecureRandom RANDOM = new java.security.SecureRandom();

    private final com.gesolutions.erp.modules.auth.repository.UserRepository userRepository;
    private final org.springframework.security.crypto.password.PasswordEncoder passwordEncoder;
    private final com.gesolutions.erp.modules.auth.service.MailService mailService;

    private static final String SENT_MESSAGE =
            "If the owner account has a working email, a 6-digit code was sent to it. It works once and runs out in "
                    + CODE_MINUTES + " minutes.";

    @PostMapping("/recover-owner")
    @org.springframework.transaction.annotation.Transactional
    public ResponseEntity<Map<String, String>> recoverOwner(@RequestBody(required = false) Map<String, String> request,
                                                            HttpServletRequest httpRequest) {
        String ip = clientIp(httpRequest);
        boolean tooMany = rateLimiter.isOverLimit("recover|" + ip, 5) || rateLimiter.isOverLimit("recover|root", 5);
        if (!tooMany) {
            rateLimiter.recordOther("recover|" + ip);
            rateLimiter.recordOther("recover|root");
            auditService.logActionAs("(unknown)", "RECOVERY_REQUESTED", "Owner recovery by email was requested from IP " + ip + ".");
            userRepository.findFirstByIsRootTrue().ifPresent(root -> {
                String email = root.getEmail();
                if (root.isActive() && email != null && email.contains("@") && !email.endsWith("@gesolutions.com")) {
                    String code = String.format("%06d", RANDOM.nextInt(1_000_000));
                    long expires = java.time.Instant.now().getEpochSecond() + CODE_MINUTES * 60L;
                    if (mailService.sendOwnerCode(email, code, CODE_MINUTES)) {
                        root.setResetToken(expires + "|0|" + passwordEncoder.encode(code));
                        userRepository.save(root);
                    }
                }
            });
        }
        return ResponseEntity.ok(Map.of("message", SENT_MESSAGE));
    }

    @PostMapping("/recover-owner/confirm")
    // noRollbackFor: a wrong try must still be COUNTED (and a dead code cleared) even though the answer is an error.
    @org.springframework.transaction.annotation.Transactional(noRollbackFor = BusinessException.class)
    public ResponseEntity<Map<String, String>> confirmOwnerRecovery(@RequestBody(required = false) Map<String, String> request,
                                                                    HttpServletRequest httpRequest) {
        String ip = clientIp(httpRequest);
        String code = request == null ? null : request.get("code");
        String newKey = request == null ? null : request.get("newPassword");
        String limitKey = "recoverconfirm|" + ip;
        if (rateLimiter.isOverLimit(limitKey, 10)) {
            throw new BusinessException("TOO_MANY_ATTEMPTS: Too many tries. Wait 15 minutes and ask for a new code.");
        }
        String wrong = "CODE_NOT_RIGHT: That code is not right, or it has run out. Ask for a new code.";
        com.gesolutions.erp.modules.auth.model.User root = userRepository.findFirstByIsRootTrue().orElse(null);
        String token = root == null ? null : root.getResetToken();
        if (code == null || !code.matches("\\d{6}") || token == null) {
            rateLimiter.recordOther(limitKey);
            throw new BusinessException(wrong);
        }
        String[] parts = token.split("\\|", 3);
        long expires; int tries;
        try { expires = Long.parseLong(parts[0]); tries = Integer.parseInt(parts[1]); }
        catch (Exception e) { root.setResetToken(null); userRepository.save(root); throw new BusinessException(wrong); }
        if (parts.length < 3 || java.time.Instant.now().getEpochSecond() > expires || tries >= CODE_TRIES) {
            root.setResetToken(null); userRepository.save(root);
            throw new BusinessException(wrong);
        }
        if (!passwordEncoder.matches(code, parts[2])) {
            root.setResetToken(expires + "|" + (tries + 1) + "|" + parts[2]);
            userRepository.save(root);
            rateLimiter.recordOther(limitKey);
            throw new BusinessException(wrong);
        }
        com.gesolutions.erp.modules.auth.service.PasswordPolicy.check(newKey, root.getUsername());
        root.setPassword(passwordEncoder.encode(newKey));
        root.setMustChangePassword(false);
        root.setTempKeyExpiresAt(null);
        root.setResetToken(null);
        root.bumpSessionVersion();
        userRepository.save(root);
        rateLimiter.clearOther(limitKey);
        rateLimiter.clearRecord(root.getUsername(), ip);
        auditService.logActionAs(root.getUsername(), "RECOVERY_USED", "The owner key was reset with an emailed code from IP " + ip + ". All devices were signed out.");
        return ResponseEntity.ok(Map.of("message", "Your new key is saved. Sign in with it."));
    }
}
