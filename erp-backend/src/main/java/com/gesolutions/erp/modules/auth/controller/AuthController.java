// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/AuthController.java
package com.gesolutions.erp.modules.auth.controller;

import com.gesolutions.erp.modules.auth.dto.LoginRequest;
import com.gesolutions.erp.modules.auth.dto.LoginResponse;
import com.gesolutions.erp.modules.auth.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * NYENZ ERP - AUTHENTICATION GATEWAY
 * 
 * Physically manages the authorization portal and emergency recovery.
 * Publicly accessible (no token required) to allow login and reset requests.
 */
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * OPERATOR AUTHORIZATION
     * Processes credentials and returns the Full Identity Handshake.
     */
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest request) {
        LoginResponse response = authService.authenticate(request);
        return ResponseEntity.ok(response);
    }

    /**
     * ROOT RECOVERY TRIGGER (The Panic Button)
     * 
     * Accepts an email address. If it matches the Root Owner, 
     * sends a reset code via SMTP.
     * 
     * Security: Logic inside AuthService prevents this from working 
     * for standard managers.
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