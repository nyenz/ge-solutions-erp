// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/ReportController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.service.ReportService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * NYENZ ERP - INTELLIGENCE COMMAND HUB (V16)
 * 
 * Physically manages the secure export of the 8 Pillars of Analytics.
 * SECURITY UPDATE: Financial Pillars unlocked for ROLE_ADMIN (Tier 2).
 */
@RestController
@RequestMapping("/api/v1/reports")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;
    private final DateTimeFormatter fileStamp = DateTimeFormatter.ofPattern("yyyyMMdd_HHmm");

    // ========================================================================
    // SECTION A: FINANCIAL & FORENSIC PILLARS (Restricted to ROLE_ADMIN)
    // Access: Root Owner & System Admin
    // ========================================================================

    /** Pillar 1: Master Debt Ledger */
    @GetMapping("/debt-ledger")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadDebtLedger() {
        return streamCsv(reportService.generateMasterDebtLedger(), "MASTER_DEBT_LEDGER");
    }

    /** Pillar 3: Recovery Throughput */
    @GetMapping("/performance")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadPerformanceReport() {
        return streamCsv(reportService.generateRecoveryThroughput(), "RECOVERY_PERFORMANCE");
    }

    /** Pillar 5: Legal Readiness */
    @GetMapping("/legal-readiness")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadLegalAudit() {
        return streamCsv(reportService.generateLegalReadiness(), "LEGAL_COMPLIANCE_AUDIT");
    }

    /** Pillar 7: Master Audit Log */
    @GetMapping("/audit-trail")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadAuditTrail() {
        return streamCsv(reportService.generateMasterAuditLog(), "SYSTEM_FORENSICS_LOG");
    }

    /** Pillar 8: Revenue History */
    @GetMapping("/revenue")
    @PreAuthorize("hasRole('ROLE_ADMIN')")
    public ResponseEntity<byte[]> downloadRevenueHistory() {
        return streamCsv(reportService.generateRevenueHistory(), "REVENUE_INFLOW_HISTORY");
    }


    // ========================================================================
    // SECTION B: OPERATIONAL PILLARS (Open to ALL Management)
    // Access: Root, Admin, and Standard Manager
    // ========================================================================

    /** Pillar 2: Physical Archive Map */
    @GetMapping("/archive-map")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER')")
    public ResponseEntity<byte[]> downloadArchiveMap() {
        return streamCsv(reportService.generateArchiveMap(), "PHYSICAL_ARCHIVE_MAP");
    }

    /** Pillar 4: Survey Stage Bottlenecks */
    @GetMapping("/bottlenecks")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER')")
    public ResponseEntity<byte[]> downloadStageAudit() {
        return streamCsv(reportService.generateStageAudit(), "SURVEY_PHASE_BOTTLENECKS");
    }

    /** Pillar 6: Reliability Scorecard */
    @GetMapping("/reliability")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_MANAGER')")
    public ResponseEntity<byte[]> downloadReliabilityRankings() {
        return streamCsv(reportService.generateReliabilityRankings(), "RELIABILITY_SCORECARD");
    }

    /**
     * INDUSTRIAL HELPER: Formats the byte stream with CSV headers.
     */
    private ResponseEntity<byte[]> streamCsv(byte[] data, String reportName) {
        String fileName = "NYENZ_" + reportName + "_" + LocalDateTime.now().format(fileStamp) + ".csv";
        
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + fileName)
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(data);
    }
}