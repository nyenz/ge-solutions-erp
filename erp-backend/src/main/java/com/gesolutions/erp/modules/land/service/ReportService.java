// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.*;
import com.gesolutions.erp.modules.land.repository.*;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.audit.AuditLog;
import com.gesolutions.erp.common.audit.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * GE SOLUTIONS - INDUSTRIAL REPORTING ENGINE
 * 
 * Physically generates the 8 Pillars of Analytics in CSV format.
 * Designed for High-Density Excel consumption and Legal auditing.
 */
@Service
@RequiredArgsConstructor
public class ReportService {

    private final LandProjectRepository projectRepository;
    private final AuditLogRepository auditLogRepository;
    private final FollowUpRepository followUpRepository;
    private final AuditService auditService;

    private static final String CSV_DIVIDER = ",";
    private static final String NEW_LINE = "\n";

    /**
     * PILLAR 1: MASTER DEBT LEDGER
     */
    @Transactional(readOnly = true)
    public byte[] generateMasterDebtLedger() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,PRIMARY_OWNER,PHONE,TOTAL_VAL,PAID_VAL,ARREARS,BOX_LOC,STATUS").append(NEW_LINE);

        for (LandProject p : data) {
            BigDecimal balance = p.getTotalCost().subtract(p.getAmountPaid());
            if (balance.compareTo(BigDecimal.ZERO) > 0) {
                Client owner = p.getProprietors().stream().findFirst().orElse(new Client());
                csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
                   .append(owner.getFullName()).append(CSV_DIVIDER)
                   .append(owner.getPhoneNumber()).append(CSV_DIVIDER)
                   .append(p.getTotalCost()).append(CSV_DIVIDER)
                   .append(p.getAmountPaid()).append(CSV_DIVIDER)
                   .append(balance).append(CSV_DIVIDER)
                   .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
                   .append(p.getStatus()).append(NEW_LINE);
            }
        }
        auditService.logAction("REPORT_EXPORT", "Pillar 1: Debt Ledger Exported");
        return csv.toString().getBytes();
    }

    /**
     * PILLAR 2: PHYSICAL ARCHIVE MAP
     */
    @Transactional(readOnly = true)
    public byte[] generateArchiveMap() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("BOX_LOCATION,PLOT_ID,TENURE,DISTRICT,STAGE_INDEX,IS_LEGACY").append(NEW_LINE);

        data.stream()
            .sorted((a, b) -> a.getLandTitle().getPhysicalBoxNumber().compareTo(b.getLandTitle().getPhysicalBoxNumber()))
            .forEach(p -> {
                csv.append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
                   .append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
                   .append(p.getLandTitle().getTenure()).append(CSV_DIVIDER)
                   .append(p.getLandTitle().getDistrict()).append(CSV_DIVIDER)
                   .append(p.getCurrentStageIndex()).append(CSV_DIVIDER)
                   .append(p.isLegacy()).append(NEW_LINE);
            });
        return csv.toString().getBytes();
    }

    /**
     * PILLAR 3: RECOVERY THROUGHPUT
     */
    @Transactional(readOnly = true)
    public byte[] generateRecoveryThroughput() {
        List<FollowUpLog> logs = followUpRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("TIMESTAMP,OPERATOR,PLOT_ID,NOTE_SNIPPET").append(NEW_LINE);

        for (FollowUpLog log : logs) {
            csv.append(log.getTimestamp()).append(CSV_DIVIDER)
               .append(log.getRecordedBy()).append(CSV_DIVIDER)
               .append(log.getProjectId()).append(CSV_DIVIDER)
               .append("\"").append(log.getNotes()).append("\"")
               .append(NEW_LINE);
        }
        return csv.toString().getBytes();
    }

    /**
     * PILLAR 4: STAGE BOTTLENECK AUDIT
     */
    @Transactional(readOnly = true)
    public byte[] generateStageAudit() {
        List<LandProject> data = projectRepository.findAll();
        Map<Integer, Long> counts = data.stream()
                .collect(Collectors.groupingBy(LandProject::getCurrentStageIndex, Collectors.counting()));

        StringBuilder csv = new StringBuilder();
        csv.append("PHASE_NUMBER,TOTAL_FILES_IN_STAGE").append(NEW_LINE);
        counts.forEach((stage, count) -> {
            csv.append("STAGE_").append(stage).append(CSV_DIVIDER).append(count).append(NEW_LINE);
        });
        return csv.toString().getBytes();
    }

    /**
     * PILLAR 5: LEGAL READINESS REPORT
     */
    @Transactional(readOnly = true)
    public byte[] generateLegalReadiness() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT,OWNER,PHONE,NIN_STATUS,ADDRESS_STATUS,READINESS").append(NEW_LINE);

        for (LandProject p : data) {
            for (Client c : p.getProprietors()) {
                boolean hasNin = c.getNationalId() != null && !c.getNationalId().isBlank();
                boolean hasAddr = c.getHomeAddress() != null && !c.getHomeAddress().isBlank();
                String ready = (hasNin && hasAddr) ? "READY_FOR_LEGAL" : "INCOMPLETE";
                
                csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
                   .append(c.getFullName()).append(CSV_DIVIDER)
                   .append(c.getPhoneNumber()).append(CSV_DIVIDER)
                   .append(hasNin ? "VALID" : "MISSING").append(CSV_DIVIDER)
                   .append(hasAddr ? "VALID" : "MISSING").append(CSV_DIVIDER)
                   .append(ready).append(NEW_LINE);
            }
        }
        return csv.toString().getBytes();
    }

    /**
     * PILLAR 6: RELIABILITY RANKINGS
     */
    @Transactional(readOnly = true)
    public byte[] generateReliabilityRankings() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("OWNER_NAME,SCORE_PERCENT,LAST_CALL_DATE").append(NEW_LINE);

        for (LandProject p : data) {
            for (Client c : p.getProprietors()) {
                csv.append(c.getFullName()).append(CSV_DIVIDER)
                   .append(c.getReliabilityScore()).append("%").append(CSV_DIVIDER)
                   .append(c.getLastContactedAt() != null ? c.getLastContactedAt().format(DateTimeFormatter.ISO_DATE) : "NEVER")
                   .append(NEW_LINE);
            }
        }
        return csv.toString().getBytes();
    }

    /**
     * PILLAR 7: MASTER AUDIT FOOTPRINT
     */
    @Transactional(readOnly = true)
    public byte[] generateMasterAuditLog() {
        List<AuditLog> logs = auditLogRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("TIMESTAMP,OPERATOR,ACTION_CODE,HARDWARE_DETAILS").append(NEW_LINE);

        for (AuditLog log : logs) {
            csv.append(log.getTimestamp()).append(CSV_DIVIDER)
               .append(log.getPerformedBy()).append(CSV_DIVIDER)
               .append(log.getAction()).append(CSV_DIVIDER)
               .append("\"").append(log.getDetails()).append("\"").append(NEW_LINE);
        }
        return csv.toString().getBytes();
    }

    /**
     * PILLAR 8: REVENUE INFLOW HISTORY (NEW)
     * Lists actual financial intake movements.
     */
    @Transactional(readOnly = true)
    public byte[] generateRevenueHistory() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,PAID_AMOUNT,CUMULATIVE_COLLECTION,PROTOCOL_MODE").append(NEW_LINE);

        for (LandProject p : data) {
            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getAmountPaid()).append(CSV_DIVIDER)
               .append(p.getAmountPaid()).append(CSV_DIVIDER)
               .append(p.isLegacy() ? "BACKLOG_RECOVERY" : "STANDARD_INGESTION").append(NEW_LINE);
        }
        return csv.toString().getBytes();
    }
}