// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerService.java
package com.gesolutions.erp.modules.land.service;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ReceivableSchedulerService {

    private final LandProjectRepository projectRepository;
    private final AuditService auditService;
    private final NotificationService notificationService;
    private final ClientRepository clientRepo;
    private final RecoveryNoteRepository recoveryNoteRepository;
                    
    private static final BigDecimal DEFAULT_MONTHLY_FEE = new BigDecimal("50000");

    // Runs every day at midnight
    // Adds 50,000 per 30-day period since receivable start date
    // Example: plot receivableged on Jan 1 — fee added Jan 31, Feb 28, etc.
    @Scheduled(cron = "0 0 0 * * *")
    @Transactional
    public void applyMonthlyStorageFees() {
        List<LandProject> receivablePlots = projectRepository.findAllReceivablePlots();
        LocalDateTime now = LocalDateTime.now();

        for (LandProject plot : receivablePlots) {
            if (plot.getReceivableStartDate() == null) continue;
            if (plot.isStoragePaused()) continue; // fees paused by admin

            // Auto-pause if negotiation deadline is in the future; auto-resume if it has passed
            if (plot.getNegotiationDeadline() != null) {
                if (now.isBefore(plot.getNegotiationDeadline())) {
                    continue; // still within negotiation window
                } else {
                    // Deadline has passed -- auto-resume fees and clear deadline
                    plot.setStoragePaused(false);
                    plot.setNegotiationDeadline(null);
                    projectRepository.save(plot);
                }
            }

            long daysSinceReceivable = ChronoUnit.DAYS.between(plot.getReceivableStartDate(), now);
            long periodsOwed = daysSinceReceivable / 30;

            if (periodsOwed <= 0) continue;

            // Use the counter (not division) to determine how many months remain to bill.
            // This is immune to rate changes mid-way through the receivable period.
            int alreadyBilled = plot.getReceivableMonthsBilled() != null ? plot.getReceivableMonthsBilled() : 0;

            if (alreadyBilled >= periodsOwed) continue;

            BigDecimal monthlyRate = (plot.getStorageFeeOverride() != null && plot.getStorageFeeOverride().compareTo(BigDecimal.ZERO) > 0)
                    ? plot.getStorageFeeOverride() : DEFAULT_MONTHLY_FEE;

            BigDecimal currentFees = plot.getStorageFeesAccumulated() != null
                    ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;

            long feesMissing = periodsOwed - alreadyBilled;
            BigDecimal toAdd = monthlyRate.multiply(BigDecimal.valueOf(feesMissing));

            plot.setStorageFeesAccumulated(currentFees.add(toAdd));
            plot.setReceivableMonthsBilled((int) periodsOwed);
            projectRepository.save(plot);

            auditService.logAction("STORAGE_FEE_APPLIED",
                "SYSTEM: Added UGX " + toAdd + " monthly storage fee to receivable plot: "
                + ownerLabel(plot)
                + " (" + feesMissing + " month(s) x UGX " + monthlyRate + ")"
                + " | Total accumulated fees: UGX " + plot.getStorageFeesAccumulated());
            if (!notificationService.existsToday("STORAGE_FEE_APPLIED", plot.getId())) notificationService.emitRaw("STORAGE_FEE_APPLIED", "INFO", "Storage fee UGX " + toAdd + " added to " + ownerLabel(plot) + ".", "PROJECT", plot.getId(), "ROLE_DIRECTOR");
        }
    }

    // Runs every day at 6am — auto-flags plots with no payment for 365+ days
    @Scheduled(cron = "0 0 6 * * *")
    @Transactional
    public void autoFlagStaleAsReceivable() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(365);
        // Pass cutoff for both lastPaymentDate AND registration date checks
        List<LandProject> candidates = projectRepository.findAutoReceivableCandidates(cutoff);

        for (LandProject plot : candidates) {
            BigDecimal outstanding = plot.getTotalCost().subtract(plot.getAmountPaid());
            if (outstanding.compareTo(BigDecimal.ZERO) <= 0) continue;

            plot.setReceivable(true);
            plot.setReceivableStartDate(LocalDateTime.now());
            plot.setOriginalDebt(outstanding);
            plot.setStorageFeesAccumulated(BigDecimal.ZERO);
            plot.setStatus("RECEIVABLE");
            projectRepository.save(plot);

            auditService.logAction("AUTO_RECEIVABLE",
                "SYSTEM: Plot " + ownerLabel(plot)
                + " auto-flagged as RECEIVABLE after 365 days of no payment. "
                + "Debt frozen at: UGX " + outstanding);
            notificationService.emit("AUTO_RECEIVABLE_365", "WARN", ownerLabel(plot) + " auto-flagged RECEIVABLE after 365 days silent.", "PROJECT", plot.getId(), "ROLE_DIRECTOR");
        }
    }

    private String ownerLabel(LandProject plot) {
        if (plot.getProprietors() != null && !plot.getProprietors().isEmpty()) {
            for (Client c : plot.getProprietors()) return c.getFullName();
        }
        return plot.getProjectIndex() != null ? ("project #" + plot.getProjectIndex()) : "untitled project";
    }
    @Scheduled(cron = "0 0 7 * * *")
    @Transactional
    public void dailyNotificationSweep() {
        return; // old promise/cooldown loops stay disabled
    }
    @Scheduled(cron = "0 0 7 * * *")
    @Transactional
    public void unlockSweep() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        java.time.LocalDateTime yesterday = now.minusDays(1);
        for (com.gesolutions.erp.modules.client.model.Client c : clientRepo.findAll()) {
            boolean lockedYesterday = lockedAt(c, yesterday) != null;
            boolean lockedToday = lockedAt(c, now) != null;
            if (lockedYesterday && !lockedToday) {
                notificationService.emitRaw("UNLOCK", "INFO", c.getFullName() + " is callable again.", "CLIENT", c.getId(), "ROLE_SECRETARY");
                notificationService.emitRaw("UNLOCK_M", "INFO", c.getFullName() + " is callable again.", "CLIENT", c.getId(), "ROLE_MANAGER");
            }
        }
    }
    private java.time.LocalDate lockedAt(com.gesolutions.erp.modules.client.model.Client c, java.time.LocalDateTime now) {
        java.time.LocalDate unlock = null;
        java.time.LocalDateTime pay = null;
        for (LandProject p : projectRepository.findAll()) {
            if (p.getProprietors() == null) continue;
            boolean mine = p.getProprietors().stream().anyMatch(o -> o != null && o.getId() != null && o.getId().equals(c.getId()));
            if (!mine) continue;
            if (p.getLastPaymentDate() != null && (pay == null || p.getLastPaymentDate().isAfter(pay))) pay = p.getLastPaymentDate();
        }
        if (pay != null && pay.plusDays(30).isAfter(now)) unlock = pay.plusDays(30).toLocalDate();
        java.time.LocalDateTime second = null; int count = 0;
        for (com.gesolutions.erp.modules.client.model.RecoveryNote n : recoveryNoteRepository.findByClientOrderByCreatedAtDesc(c)) {
            if ("POSITIVE".equals(n.getTone()) && n.isCountsAsAttempt() && n.getCreatedAt().isAfter(now.minusDays(30))) { count++; if (count == 2) second = n.getCreatedAt(); }
        }
        if (second != null) { java.time.LocalDate u2 = second.plusDays(30).toLocalDate(); if (unlock == null || u2.isAfter(unlock)) unlock = u2; }
        return unlock;
    }
}
