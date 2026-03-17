// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditController.java
package com.gesolutions.erp.common.audit;

import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

/**
 * NYENZ ERP - SYSTEM FORENSICS TERMINAL
 * 
 * Physically manages the interrogation of the Audit Ledger.
 * SECURITY UPDATE: Access extended to ROLE_ADMIN (Tier 2) for operational oversight.
 */
@RestController
@RequestMapping("/api/v1/admin/audit")
@RequiredArgsConstructor
// Base Gate: Must be at least a Manager to hit the API, but specific methods are tighter
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class AuditController {

    private final AuditLogRepository auditLogRepository;

    /**
     * PILLAR 7: MASTER AUDIT STREAM
     * Returns the raw chronological footprint of all system activities.
     * ACCESS: Locked to ADMIN and ROOT. Standard Managers cannot see this.
     */
    @GetMapping("/stream")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<Page<AuditLog>> getRawStream(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        
        return ResponseEntity.ok(auditLogRepository.findAll(
            PageRequest.of(page, size, Sort.by("timestamp").descending())
        ));
    }

    /**
     * THE TRUTH MACHINE (Search Hub)
     * Filters footprints by Operator, Action Type, or Date Range.
     * ACCESS: Locked to ADMIN and ROOT.
     */
    @GetMapping("/search")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<Page<AuditLog>> searchForensics(
            @RequestParam(required = false) String operator,
            @RequestParam(required = false) String action,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime start,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime end,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        
        return ResponseEntity.ok(auditLogRepository.findWithFilters(
            operator, action, start, end, 
            PageRequest.of(page, size, Sort.by("timestamp").descending())
        ));
    }

    /**
     * ASSET INVESTIGATION
     * Physically searches the details text for specific Plot IDs or Box Numbers.
     * ACCESS: Locked to ADMIN and ROOT.
     */
    @GetMapping("/investigate")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<Page<AuditLog>> investigateKeyword(
            @RequestParam String keyword,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        
        return ResponseEntity.ok(auditLogRepository.findByDetailsContainingIgnoreCase(
            keyword, 
            PageRequest.of(page, size, Sort.by("timestamp").descending())
        ));
    }
}