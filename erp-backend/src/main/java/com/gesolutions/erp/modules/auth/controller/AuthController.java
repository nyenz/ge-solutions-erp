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
    private static volatile boolean forwardedLogged = false;

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "ENGINE_ONLINE"));
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

    /**
     * fix181: email recovery is switched off (Render's free plan blocks mail, and the old code reset the Admin's key the
     * moment anyone typed the Admin's email). The answer is the same whatever is typed, and nothing is changed.
     * The Admin recovers through the ADMIN_RESET_ONCE setting (see LLM_CONTEXT_GUIDE.md Section 5).
     */
    @PostMapping("/recover-owner")
    public ResponseEntity<Map<String, String>> recoverOwner(@RequestBody(required = false) Map<String, String> request,
                                                            HttpServletRequest httpRequest) {
        String ip = clientIp(httpRequest);
        if (!rateLimiter.isOverLimit("recover|" + ip, 5)) {
            rateLimiter.recordOther("recover|" + ip);
            auditService.logActionAs("(unknown)", "RECOVERY_REQUESTED", "Owner recovery was requested from IP " + ip + ". Email recovery is off; nothing was changed.");
        }
        return ResponseEntity.ok(Map.of(
            "message", "Staff: ask the Director to reset your key. Director: ask the Admin. Admin: use the owner recovery setting."
        ));
    }
}
