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

    private static final BigDecimal DEFAULT_MONTHLY_FEE = new BigDecimal("50000");

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
            if (plot.isStoragePaused()) continue; // fees paused by admin

            long daysSinceBacklog = ChronoUnit.DAYS.between(plot.getBacklogStartDate(), now);
            long periodsOwed = daysSinceBacklog / 30;

            if (periodsOwed <= 0) continue;

            BigDecimal monthlyRate = (plot.getStorageFeeOverride() != null && plot.getStorageFeeOverride().compareTo(BigDecimal.ZERO) > 0)
                    ? plot.getStorageFeeOverride() : DEFAULT_MONTHLY_FEE;

            BigDecimal currentFees = plot.getStorageFeesAccumulated() != null
                    ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;

            long feesAlreadyApplied = monthlyRate.compareTo(BigDecimal.ZERO) > 0
                    ? currentFees.divide(monthlyRate, 0, RoundingMode.DOWN).longValue()
                    : 0L;

            if (feesAlreadyApplied >= periodsOwed) continue;

            long feesMissing = periodsOwed - feesAlreadyApplied;
            BigDecimal toAdd = monthlyRate.multiply(BigDecimal.valueOf(feesMissing));

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