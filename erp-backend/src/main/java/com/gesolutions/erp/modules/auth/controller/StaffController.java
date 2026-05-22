// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/StaffController.java
package com.gesolutions.erp.modules.auth.controller;

import com.gesolutions.erp.modules.auth.dto.*;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.service.StaffManagementService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * NYENZ ERP - STAFF MASTERY CONTROLLER
 * 
 * Physically manages the operator registry and hierarchy.
 * SECURITY PROTOCOL: Strictly restricted to the ROOT FOUNDER.
 * Admins (Tier 2) are blocked from these endpoints to prevent coups.
 */
@RestController
@RequestMapping("/api/v1/staff")
@RequiredArgsConstructor
// Gate: Must be an Admin AND be the physical Root Owner
@PreAuthorize("hasRole('ROLE_ADMIN') and authentication.principal.isRoot")
public class StaffController {

    private final StaffManagementService staffService;

    /**
     * OPERATOR DIRECTORY
     * Returns the full list of staff for the Governance Ledger.
     * ACCESS: Root and Admin (Admins need this to filter audit logs).
     */
    @GetMapping("/all")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<List<User>> getAllOperators() {
        return ResponseEntity.ok(staffService.getAllOperators());
    }

    /**
     * REGISTRATION HANDSHAKE
     * Creates a new manager and returns the temporary 'NY-' password.
     */
    @PostMapping("/create")
    public ResponseEntity<UserCreateResponse> registerManager(@RequestBody UserCreateRequest request) {
        return ResponseEntity.ok(staffService.createStaff(request));
    }

    /**
     * HIERARCHY ADJUSTMENT (PROMOTION/DEMOTION)
     * Physically changes an operator's security clearance level.
     */
    @PatchMapping("/{username}/role")
    public ResponseEntity<Void> updateRole(
            @PathVariable String username, 
            @RequestParam Role newRole) {
        
        staffService.updateUserRole(username, newRole);
        return ResponseEntity.ok().build();
    }

    /**
     * THE KILL-SWITCH (DEACTIVATE)
     * Physically suspends a manager's access by username.
     */
    @PatchMapping("/{username}/toggle")
    public ResponseEntity<Void> toggleStatus(
            @PathVariable String username, 
            @RequestParam boolean active) {
        
        staffService.toggleOperatorStatus(username, active);
        return ResponseEntity.ok().build();
    }

    /**
     * EMERGENCY CREDENTIAL RESET
     * Resets a manager's security key and forces a change on next login.
     */
    @PostMapping("/reset-password")
    public ResponseEntity<Map<String, String>> resetPassword(@RequestBody PasswordResetRequest request) {
        String newTempKey = staffService.resetOperatorPassword(request.getUsername());
        return ResponseEntity.ok(Map.of("temporaryPassword", newTempKey));
    }
}