import os

files = {}

# ── 1. LandProject.java — Boolean fix (already done but re-confirming) ──
files["erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java"] = """\
// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java
package com.gesolutions.erp.modules.land.model;

import com.gesolutions.erp.modules.client.model.Client;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

@Entity
@Table(name = "land_projects")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LandProject {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)
    @JoinColumn(name = "title_id", nullable = false)
    private LandTitle landTitle;

    @Builder.Default
    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "project_proprietors",
        joinColumns = @JoinColumn(name = "project_id"),
        inverseJoinColumns = @JoinColumn(name = "client_id")
    )
    private Set<Client> proprietors = new HashSet<>();

    @Column(name = "total_cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal totalCost;

    @Builder.Default
    @Column(name = "amount_paid", nullable = false, precision = 15, scale = 2)
    private BigDecimal amountPaid = BigDecimal.ZERO;

    @Column(name = "weekly_installment", precision = 15, scale = 2)
    private BigDecimal weeklyInstallment;

    @Column(name = "plan_type", length = 100)
    private String planType;

    // Boolean (object not primitive) so existing DB rows with NULL don't crash
    @Builder.Default
    @Column(name = "is_backlog")
    private Boolean isBacklog = false;

    @Column(name = "backlog_start_date")
    private LocalDateTime backlogStartDate;

    @Builder.Default
    @Column(name = "original_debt", precision = 15, scale = 2)
    private BigDecimal originalDebt = BigDecimal.ZERO;

    @Builder.Default
    @Column(name = "storage_fees_accumulated", precision = 15, scale = 2)
    private BigDecimal storageFeesAccumulated = BigDecimal.ZERO;

    @Column(name = "last_payment_date")
    private LocalDateTime lastPaymentDate;

    @Builder.Default
    @Column(name = "is_legacy", nullable = false)
    private boolean isLegacy = false;

    @Builder.Default
    @Column(name = "current_stage_index", nullable = false)
    private Integer currentStageIndex = 1;

    @Builder.Default
    @Column(length = 50, nullable = false)
    private String status = "ACTIVE";

    public void addProprietor(Client client) {
        if (this.proprietors == null) this.proprietors = new HashSet<>();
        if (client != null) this.proprietors.add(client);
    }

    // Safe null-check — old DB rows have NULL for isBacklog
    public boolean isBacklog() {
        return Boolean.TRUE.equals(this.isBacklog);
    }

    public void setBacklog(boolean value) {
        this.isBacklog = value;
    }

    public BigDecimal backlogTotalOwed() {
        BigDecimal base = originalDebt != null ? originalDebt : BigDecimal.ZERO;
        BigDecimal fees = storageFeesAccumulated != null ? storageFeesAccumulated : BigDecimal.ZERO;
        BigDecimal paid = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return base.add(fees).subtract(paid);
    }

    public BigDecimal activeTotalOwed() {
        BigDecimal cost = totalCost != null ? totalCost : BigDecimal.ZERO;
        BigDecimal paid = amountPaid != null ? amountPaid : BigDecimal.ZERO;
        return cost.subtract(paid);
    }
}
"""

# ── 2. Scheduler — 30 days from backlog start date ──────────────────
files["erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerService.java"] = """\
// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BacklogSchedulerService {

    private final LandProjectRepository projectRepository;
    private final AuditService auditService;

    private static final BigDecimal MONTHLY_STORAGE_FEE = new BigDecimal("50000");

    // Runs every day at midnight
    // Adds 50,000 per 30-day period since backlog start date
    // Example: plot backlogged on Jan 1 — fee added Jan 31, Feb 28, etc.
    @Scheduled(cron = "0 0 0 * * *")
    @Transactional
    public void applyMonthlyStorageFees() {
        List<LandProject> backlogPlots = projectRepository.findAllBacklogPlots();
        LocalDateTime now = LocalDateTime.now();

        for (LandProject plot : backlogPlots) {
            if (plot.getBacklogStartDate() == null) continue;

            long daysSinceBacklog = ChronoUnit.DAYS.between(plot.getBacklogStartDate(), now);
            long periodsOwed = daysSinceBacklog / 30;

            if (periodsOwed <= 0) continue;

            BigDecimal currentFees = plot.getStorageFeesAccumulated() != null
                    ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;

            long feesAlreadyApplied = currentFees
                    .divide(MONTHLY_STORAGE_FEE, 0, RoundingMode.DOWN)
                    .longValue();

            if (feesAlreadyApplied >= periodsOwed) continue;

            long feesMissing = periodsOwed - feesAlreadyApplied;
            BigDecimal toAdd = MONTHLY_STORAGE_FEE.multiply(BigDecimal.valueOf(feesMissing));

            plot.setStorageFeesAccumulated(currentFees.add(toAdd));
            projectRepository.save(plot);

            auditService.logAction("STORAGE_FEE_APPLIED",
                "SYSTEM: Added UGX " + toAdd + " storage fee to backlog plot: "
                + plot.getLandTitle().getPlotNumber()
                + " (" + feesMissing + " month(s) x UGX 50,000)"
                + " | Total fees: UGX " + plot.getStorageFeesAccumulated());
        }
    }

    // Runs every day at 6am — auto-flags plots with no payment for 365+ days
    @Scheduled(cron = "0 0 6 * * *")
    @Transactional
    public void autoFlagStaleAsBacklog() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(365);
        List<LandProject> candidates = projectRepository.findAutoBacklogCandidates(cutoff);

        for (LandProject plot : candidates) {
            BigDecimal outstanding = plot.getTotalCost().subtract(plot.getAmountPaid());
            if (outstanding.compareTo(BigDecimal.ZERO) <= 0) continue;

            plot.setBacklog(true);
            plot.setBacklogStartDate(LocalDateTime.now());
            plot.setOriginalDebt(outstanding);
            plot.setStorageFeesAccumulated(BigDecimal.ZERO);
            plot.setStatus("BACKLOG");
            projectRepository.save(plot);

            auditService.logAction("AUTO_BACKLOG",
                "SYSTEM: Plot " + plot.getLandTitle().getPlotNumber()
                + " auto-flagged as BACKLOG after 365 days of no payment. "
                + "Debt frozen at: UGX " + outstanding);
        }
    }
}
"""

# ── 3. New PaymentController — all payments endpoint ─────────────────
files["erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PaymentController.java"] = """\
// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PaymentController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/recovery/payments")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN')")
public class PaymentController {

    private final PaymentRecordRepository paymentRecordRepository;
    private final LandProjectRepository projectRepository;

    @GetMapping("/all")
    public ResponseEntity<List<Map<String, Object>>> getAllPayments(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "500") int size) {

        List<PaymentRecord> records = paymentRecordRepository.findAll(
                PageRequest.of(page, size, Sort.by("timestamp").descending())
        ).getContent();

        List<Map<String, Object>> result = new ArrayList<>();

        for (PaymentRecord pay : records) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id",           pay.getId());
            row.put("projectId",    pay.getProjectId());
            row.put("amountPaid",   pay.getAmountPaid());
            row.put("paymentType",  pay.getPaymentType());
            row.put("recordedBy",   pay.getRecordedBy());
            row.put("notes",        pay.getNotes());
            row.put("balanceAfter", pay.getBalanceAfter());
            row.put("timestamp",    pay.getTimestamp());

            try {
                LandProject project = projectRepository.findById(pay.getProjectId()).orElse(null);
                if (project != null) {
                    row.put("plotNumber", project.getLandTitle().getPlotNumber());
                    String ownerName = project.getProprietors().stream()
                            .findFirst()
                            .map(c -> c.getFullName())
                            .orElse("---");
                    row.put("ownerName", ownerName);
                } else {
                    row.put("plotNumber", "---");
                    row.put("ownerName",  "---");
                }
            } catch (Exception e) {
                row.put("plotNumber", "---");
                row.put("ownerName",  "---");
            }

            result.add(row);
        }

        return ResponseEntity.ok(result);
    }
}
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("All done.")