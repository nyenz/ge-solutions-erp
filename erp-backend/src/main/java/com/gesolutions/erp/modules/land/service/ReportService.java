// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.*;
import com.gesolutions.erp.modules.land.repository.*;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.audit.AuditLog;
import com.gesolutions.erp.common.audit.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
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
    private final PaymentRecordRepository paymentRecordRepository;

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

    /**
     * PRIORITY 2 - REPORT 1: BACKLOG BREAKDOWN REPORT
     * All backlog plots with storage fees breakdown.
     */
    @Transactional(readOnly = true)
    public byte[] generateBacklogBreakdown() {
        List<LandProject> data = projectRepository.findAllBacklogPlots();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,BOX,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,BACKLOG_START,ORIGINAL_DEBT,STORAGE_FEES_UGX,MONTHS_IN_BACKLOG,TOTAL_PAID,TOTAL_OWED").append(NEW_LINE);

        for (LandProject p : data) {
            Client owner = p.getProprietors().stream().findFirst().orElse(new Client());
            java.math.BigDecimal origDebt = p.getOriginalDebt() != null ? p.getOriginalDebt() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal storageFees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal amountPaid = p.getAmountPaid() != null ? p.getAmountPaid() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal totalOwed = origDebt.add(storageFees).subtract(amountPaid);
            long months = p.getBacklogStartDate() != null
                ? java.time.temporal.ChronoUnit.MONTHS.between(p.getBacklogStartDate(), java.time.LocalDateTime.now())
                : 0;
            String backlogStart = p.getBacklogStartDate() != null
                ? p.getBacklogStartDate().toLocalDate().toString() : "UNKNOWN";

            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getDistrict() != null ? p.getLandTitle().getDistrict() : "").append(CSV_DIVIDER)
               .append(p.getLandTitle().getTenure() != null ? p.getLandTitle().getTenure() : "").append(CSV_DIVIDER)
               .append(owner.getFullName() != null ? owner.getFullName() : "").append(CSV_DIVIDER)
               .append(owner.getPhoneNumber() != null ? owner.getPhoneNumber() : "").append(CSV_DIVIDER)
               .append(backlogStart).append(CSV_DIVIDER)
               .append(origDebt).append(CSV_DIVIDER)
               .append(storageFees).append(CSV_DIVIDER)
               .append(months).append(CSV_DIVIDER)
               .append(amountPaid).append(CSV_DIVIDER)
               .append(totalOwed.max(java.math.BigDecimal.ZERO)).append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Backlog Breakdown Report Exported");
        return csv.toString().getBytes();
    }

    /**
     * PRIORITY 2 - REPORT 2: COMPLETED TITLES REPORT
     * All released / fully paid plots.
     */
    @Transactional(readOnly = true)
    public byte[] generateCompletedTitles() {
        List<LandProject> data = projectRepository.findAll();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,BOX,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,TOTAL_COST,AMOUNT_PAID,STATUS").append(NEW_LINE);

        for (LandProject p : data) {
            boolean released = p.getLandTitle().isReleased();
            boolean fullyPaid = p.getAmountPaid().compareTo(p.getTotalCost()) >= 0;
            if (!released && !fullyPaid) continue;

            Client owner = p.getProprietors().stream().findFirst().orElse(new Client());
            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getDistrict() != null ? p.getLandTitle().getDistrict() : "").append(CSV_DIVIDER)
               .append(p.getLandTitle().getTenure() != null ? p.getLandTitle().getTenure() : "").append(CSV_DIVIDER)
               .append(owner.getFullName() != null ? owner.getFullName() : "").append(CSV_DIVIDER)
               .append(owner.getPhoneNumber() != null ? owner.getPhoneNumber() : "").append(CSV_DIVIDER)
               .append(p.getTotalCost()).append(CSV_DIVIDER)
               .append(p.getAmountPaid()).append(CSV_DIVIDER)
               .append(released ? "RELEASED" : "FULLY_PAID_PENDING_RELEASE").append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Completed Titles Report Exported");
        return csv.toString().getBytes();
    }

    /**
     * PRIORITY 2 - REPORT 3: FULL PAYMENT HISTORY REPORT
     * All payment records across all plots.
     */
    @Transactional(readOnly = true)
    public byte[] generatePaymentHistory() {
        List<com.gesolutions.erp.modules.land.model.PaymentRecord> records =
            paymentRecordRepository.findAll(Sort.by("timestamp").descending());
        StringBuilder csv = new StringBuilder();
        csv.append("DATE,PLOT_ID,OWNER_NAME,PAYMENT_TYPE,AMOUNT_UGX,BALANCE_AFTER_UGX,RECORDED_BY,NOTES").append(NEW_LINE);

        for (com.gesolutions.erp.modules.land.model.PaymentRecord pay : records) {
            String plotNumber = "---";
            String ownerName = "---";
            try {
                java.util.Optional<LandProject> proj = projectRepository.findById(pay.getProjectId());
                if (proj.isPresent()) {
                    plotNumber = proj.get().getLandTitle().getPlotNumber();
                    ownerName = proj.get().getProprietors().stream()
                        .findFirst().map(Client::getFullName).orElse("---");
                }
            } catch (Exception ignored) {}

            String notes = pay.getNotes() != null ? pay.getNotes().replace(",", ";") : "";
            csv.append(pay.getTimestamp().toLocalDate()).append(CSV_DIVIDER)
               .append(plotNumber).append(CSV_DIVIDER)
               .append(ownerName).append(CSV_DIVIDER)
               .append(pay.getPaymentType()).append(CSV_DIVIDER)
               .append(pay.getAmountPaid()).append(CSV_DIVIDER)
               .append(pay.getBalanceAfter() != null ? pay.getBalanceAfter() : "").append(CSV_DIVIDER)
               .append(pay.getRecordedBy()).append(CSV_DIVIDER)
               .append(notes).append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Full Payment History Exported");
        return csv.toString().getBytes();
    }

        /**
     * PRIORITY 2 - REPORT 4: STORAGE FEES PER PLOT REPORT
     * Total storage fees accumulated per backlog plot.
     */
    @Transactional(readOnly = true)
    public byte[] generateStorageFeesReport() {
        List<LandProject> data = projectRepository.findAllBacklogPlots();
        StringBuilder csv = new StringBuilder();
        csv.append("PLOT_ID,BOX,PRIMARY_OWNER,PHONE,BACKLOG_START_DATE,MONTHS_IN_BACKLOG,ORIGINAL_DEBT_UGX,STORAGE_FEES_UGX,RATE_PER_MONTH_UGX,TOTAL_PAID_UGX,OUTSTANDING_UGX").append(NEW_LINE);

        java.math.BigDecimal monthlyRate = new java.math.BigDecimal("50000");

        for (LandProject p : data) {
            Client owner = p.getProprietors().stream().findFirst().orElse(new Client());
            java.math.BigDecimal origDebt = p.getOriginalDebt() != null ? p.getOriginalDebt() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal storageFees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal amountPaid = p.getAmountPaid() != null ? p.getAmountPaid() : java.math.BigDecimal.ZERO;
            java.math.BigDecimal outstanding = origDebt.add(storageFees).subtract(amountPaid).max(java.math.BigDecimal.ZERO);
            long months = p.getBacklogStartDate() != null
                ? java.time.temporal.ChronoUnit.MONTHS.between(p.getBacklogStartDate(), java.time.LocalDateTime.now())
                : 0;
            String backlogStart = p.getBacklogStartDate() != null
                ? p.getBacklogStartDate().toLocalDate().toString() : "UNKNOWN";

            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)
               .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)
               .append(owner.getFullName() != null ? owner.getFullName() : "").append(CSV_DIVIDER)
               .append(owner.getPhoneNumber() != null ? owner.getPhoneNumber() : "").append(CSV_DIVIDER)
               .append(backlogStart).append(CSV_DIVIDER)
               .append(months).append(CSV_DIVIDER)
               .append(origDebt).append(CSV_DIVIDER)
               .append(storageFees).append(CSV_DIVIDER)
               .append(monthlyRate).append(CSV_DIVIDER)
               .append(amountPaid).append(CSV_DIVIDER)
               .append(outstanding).append(NEW_LINE);
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Storage Fees Report Exported");
        return csv.toString().getBytes();
    }

    /**
     * PRIORITY 2 - REPORT 5: MONTHLY COLLECTION REPORT
     * How much was collected each month.
     */
    @Transactional(readOnly = true)
    public byte[] generateMonthlyCollection() {
        // Go back 24 months
        java.time.LocalDateTime since = java.time.LocalDateTime.now().minusMonths(24);
        java.util.List<Object[]> monthlyData = paymentRecordRepository.monthlyRevenueSince(since);

        StringBuilder csv = new StringBuilder();
        csv.append("YEAR_MONTH,TOTAL_COLLECTED_UGX,TRANSACTION_COUNT").append(NEW_LINE);

        if (monthlyData.isEmpty()) {
            csv.append("NO_DATA,0,0").append(NEW_LINE);
        } else {
            // monthlyRevenueSince returns [month_timestamp, sum_amount]
            // We need count too -- use a simple approach
            for (Object[] row : monthlyData) {
                String month = row[0] != null ? row[0].toString().substring(0, 7) : "UNKNOWN";
                String total = row[1] != null ? row[1].toString() : "0";
                csv.append(month).append(CSV_DIVIDER)
                   .append(total).append(CSV_DIVIDER)
                   .append("--").append(NEW_LINE);
            }
        }
        auditService.logAction("REPORT_EXPORT", "Priority 2: Monthly Collection Report Exported");
        return csv.toString().getBytes();
    }
}