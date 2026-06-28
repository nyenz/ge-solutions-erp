// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/AuthController.java
package com.gesolutions.erp.modules.auth.controller;

import com.gesolutions.erp.modules.auth.dto.LoginRequest;
import com.gesolutions.erp.modules.auth.dto.LoginResponse;
import com.gesolutions.erp.modules.auth.service.AuthService;
import com.gesolutions.erp.config.LoginRateLimiter;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

import java.util.Map;

/**
 * NYENZ ERP - AUTHENTICATION GATEWAY (V2.1 - HEALTH CHECK ADDED)
 *
 * Publicly accessible (no token required) to allow login, reset, and health checks.
 */
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;
    private final LoginRateLimiter rateLimiter;

    /**
     * RENDER HEALTH CHECK ENDPOINT
     *
     * Render's load balancer sends a GET request to this path every 30 seconds
     * to confirm the engine is alive. It must return HTTP 200 or Render will
     * kill the container and restart it — causing the "Timed out" failure.
     *
     * This endpoint requires no token, no body, no logic — just a 200 OK.
     * It is permitted in SecurityConfig under "/api/v1/auth/**".
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "ENGINE_ONLINE"));
    }

    /**
     * OPERATOR AUTHORIZATION
     * Processes credentials and returns the Full Identity Handshake.
     */
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest request,
                                               HttpServletRequest httpRequest) {
        // BEST PRACTICE: Read the standard X-Forwarded-For header to extract the 
        // real client IP when running behind a cloud proxy/load balancer like Render.
        String ip = httpRequest.getHeader("X-Forwarded-For");
        if (ip == null || ip.isBlank()) {
            ip = httpRequest.getRemoteAddr();
        } else {
            ip = ip.split(",")[0].trim();
        }
        if (rateLimiter.isBlocked(ip)) {
            throw new BusinessException("TOO_MANY_ATTEMPTS: Account locked for 10 minutes. Try again later.");
        }
        try {
            LoginResponse response = authService.authenticate(request);
            rateLimiter.clearRecord(ip);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            rateLimiter.recordFailure(ip);
            throw e;
        }
    }

    /**
     * ROOT RECOVERY TRIGGER (The Panic Button)
     *
     * Accepts an email address. If it matches the Root Owner,
     * sends a reset code via SMTP.
     */
    @PostMapping("/recover-owner")
    public ResponseEntity<Map<String, String>> recoverOwner(@RequestBody Map<String, String> request) {
        String email = request.get("email");
        authService.initiateRootRecovery(email);

        return ResponseEntity.ok(Map.of(
            "message", "PROTOCOL INITIATED: If this email is the Root Owner, a code has been sent."
        ));
    }
}