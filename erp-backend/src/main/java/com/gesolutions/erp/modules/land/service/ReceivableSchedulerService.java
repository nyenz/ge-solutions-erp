// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReceivableSchedulerService.java
package com.gesolutions.erp.modules.land.service;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.service.RecoveryStateService;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionTemplate;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * THE NIGHTLY JOBS (storage fees 00:00, 365-day receivable 06:00, callable again 07:00; Kampala time).
 *
 * fix181 (17.16): each project is done in its OWN small transaction with its own try/catch. One bad project no longer
 * undoes the whole night; failures are counted and reported in one SYSTEM audit line and one alert. Alerts are written
 * only after the change is saved, and the fee job sends ONE summary alert per day (owner default) instead of one per
 * project.
 * fix181 (17.3): the server sleeps on the free plan, so every job is also run once a minute after start-up; the repeat
 * rules (NotificationTypes) make a second run harmless. The callable-again job no longer compares "yesterday with
 * today" (an edge missed while asleep was lost for good); it alerts every client who became callable in the last 7 days,
 * once per callable date.
 */
@Service
public class ReceivableSchedulerService {

    private static final String ZONE = "Africa/Kampala";

    private final LandProjectRepository projectRepository;
    private final AuditService auditService;
    private final NotificationService notificationService;
    private final ClientRepository clientRepo;
    private final RecoveryNoteRepository recoveryNoteRepository;
    private final RecoveryStateService recoveryState;
    private final TransactionTemplate itemTx;

    @Value("${ge.solutions.jobs.run-on-start:true}")
    private boolean runOnStart = true;

    public ReceivableSchedulerService(LandProjectRepository projectRepository, AuditService auditService,
                                      NotificationService notificationService, ClientRepository clientRepo,
                                      RecoveryNoteRepository recoveryNoteRepository, RecoveryStateService recoveryState,
                                      PlatformTransactionManager txManager) {
        this.projectRepository = projectRepository;
        this.auditService = auditService;
        this.notificationService = notificationService;
        this.clientRepo = clientRepo;
        this.recoveryNoteRepository = recoveryNoteRepository;
        this.recoveryState = recoveryState;
        this.itemTx = new TransactionTemplate(txManager);
        this.itemTx.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);
    }

    private static final BigDecimal DEFAULT_MONTHLY_FEE = LandProject.DEFAULT_MONTHLY_STORAGE_FEE;   // fix173: one shared default

    /** A fixed id for the "one per day" summary alerts of the jobs. */
    private static UUID jobId(String name) {
        return UUID.nameUUIDFromBytes(("job|" + name).getBytes(StandardCharsets.UTF_8));
    }

    /** fix181 (17.3): catch up once after start-up (the free plan sleeps through the night runs). */
    @EventListener(ApplicationReadyEvent.class)
    public void catchUpAfterStart() {
        if (!runOnStart) return;
        Thread t = new Thread(() -> {
            try { Thread.sleep(60_000); } catch (InterruptedException e) { return; }
            try { applyMonthlyStorageFees(); } catch (Exception e) { System.err.println(">>> [JOBS] fees catch-up: " + e.getMessage()); }
            try { autoFlagStaleAsReceivable(); } catch (Exception e) { System.err.println(">>> [JOBS] 365 catch-up: " + e.getMessage()); }
            try { unlockSweep(); } catch (Exception e) { System.err.println(">>> [JOBS] unlock catch-up: " + e.getMessage()); }
            try { pendingStaleCheck(); } catch (Exception e) { System.err.println(">>> [JOBS] pending catch-up: " + e.getMessage()); }
        }, "jobs-catch-up");
        t.setDaemon(true);
        t.start();
    }

    // ── STORAGE FEES (00:00) ────────────────────────────────────────────────
    // Adds the monthly storage fee (the project's own rate, else the shared default) per 30-day period since the
    // receivable start date. Example: receivable on Jan 1 -- fee added Jan 31, Mar 2, etc.
    @Scheduled(cron = "0 0 0 * * *", zone = ZONE)
    public void applyMonthlyStorageFees() {
        List<UUID> ids = new ArrayList<>();
        for (LandProject p : projectRepository.findAllReceivablePlots()) ids.add(p.getId());
        int applied = 0;
        BigDecimal total = BigDecimal.ZERO;
        List<String> failed = new ArrayList<>();
        for (UUID id : ids) {
            try {
                BigDecimal added = itemTx.execute(status -> feesForOne(id, LocalDateTime.now()));
                if (added != null && added.signum() > 0) { applied++; total = total.add(added); }
            } catch (Exception e) {
                failed.add(indexOf(id));
                System.err.println(">>> [JOBS] storage fee failed for " + id + ": " + e.getMessage());
            }
        }
        if (applied > 0) {
            notificationService.emitToAudience("STORAGE_FEE_APPLIED",
                    "Storage fees were added to " + applied + " project(s) today, UGX " + total.toPlainString() + ".",
                    "SYSTEM", jobId("storage-fees"));
        }
        reportFailures("STORAGE_JOB_FAILED", "storage-fee", failed);
    }

    /** One project's fees in its own transaction. Returns what was added (0 when nothing was due). */
    BigDecimal feesForOne(UUID id, LocalDateTime now) {
        LandProject plot = projectRepository.findById(id).orElse(null);
        if (plot == null || plot.isDeleted() || plot.isPending() || !plot.isReceivable()) return BigDecimal.ZERO;
        if (plot.getReceivableStartDate() == null) return BigDecimal.ZERO;
        // fix167: a pause SKIPS the paused months. While paused nothing is billed; when the pause ends the billing clock
        // moves forward by the paused days (LandProject.endStoragePause).
        if (plot.isStoragePaused() && plot.getNegotiationDeadline() == null) {
            if (plot.getStoragePausedAt() == null) { plot.setStoragePausedAt(now); projectRepository.save(plot); }
            return BigDecimal.ZERO; // old open-ended pause: stays paused until a director resumes it
        }
        if (plot.getNegotiationDeadline() != null) {
            if (plot.getStoragePausedAt() == null) { plot.setStoragePausedAt(now); projectRepository.save(plot); }
            if (now.isBefore(plot.getNegotiationDeadline())) {
                // fix181 (17.15c): the Manager hears once when a negotiation deadline is 3 days away
                if (plot.getNegotiationDeadline().isBefore(now.plusDays(3))) {
                    notificationService.emitToAudience("NEGOTIATION_DEADLINE", "Negotiation deadline for " + ownerLabel(plot)
                            + " is on " + plot.getNegotiationDeadline().toLocalDate() + ".", "PROJECT", plot.getId(),
                            plot.getNegotiationDeadline().toLocalDate());
                }
                return BigDecimal.ZERO; // still paused
            }
            LocalDateTime ended = plot.getNegotiationDeadline();
            plot.endStoragePause(ended);
            projectRepository.save(plot);
            auditService.logActionAfterCommit("STORAGE_FEE_RESUMED", "SYSTEM: Storage-fee pause ended on " + ended.toLocalDate()
                    + " for " + ownerLabel(plot) + ". Billing restarts; the paused days are not charged.");
            notificationService.emitToAudience("STORAGE_FEE_RESUMED", "Storage fees are running again for " + ownerLabel(plot)
                    + ": the pause ended on " + ended.toLocalDate() + ".", "PROJECT", plot.getId());   // fix181 (17.15b)
        }

        long daysSinceReceivable = ChronoUnit.DAYS.between(plot.getReceivableStartDate(), now);
        long periodsOwed = daysSinceReceivable / 30;
        if (periodsOwed <= 0) return BigDecimal.ZERO;

        // the counter (not division) decides how many months remain to bill: immune to rate changes mid-way
        int alreadyBilled = plot.getReceivableMonthsBilled() != null ? plot.getReceivableMonthsBilled() : 0;
        if (alreadyBilled >= periodsOwed) return BigDecimal.ZERO;

        // fix167: a rate set to 0 means NO fee
        BigDecimal monthlyRate = plot.getStorageFeeOverride() != null ? plot.getStorageFeeOverride() : DEFAULT_MONTHLY_FEE;
        if (monthlyRate.signum() == 0) {
            plot.setReceivableMonthsBilled((int) periodsOwed);
            projectRepository.save(plot);
            return BigDecimal.ZERO;
        }

        BigDecimal currentFees = plot.getStorageFeesAccumulated() != null ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;
        long feesMissing = periodsOwed - alreadyBilled;
        BigDecimal toAdd = monthlyRate.multiply(BigDecimal.valueOf(feesMissing));

        plot.setStorageFeesAccumulated(currentFees.add(toAdd));
        plot.setReceivableMonthsBilled((int) periodsOwed);
        projectRepository.save(plot);

        auditService.logActionAfterCommit("STORAGE_FEE_APPLIED",
            "SYSTEM: Added UGX " + toAdd + " monthly storage fee to receivable plot: "
            + ownerLabel(plot)
            + " (" + feesMissing + " month(s) x UGX " + monthlyRate + ")"
            + " | Total accumulated fees: UGX " + plot.getStorageFeesAccumulated());
        return toAdd;
    }

    // ── 365 DAYS WITHOUT PAYMENT (06:00) ────────────────────────────────────
    @Scheduled(cron = "0 0 6 * * *", zone = ZONE)
    public void autoFlagStaleAsReceivable() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(365);
        List<UUID> ids = new ArrayList<>();
        for (LandProject p : projectRepository.findAutoReceivableCandidates(cutoff)) ids.add(p.getId());
        List<LandProject> flagged = new ArrayList<>();
        List<String> failed = new ArrayList<>();
        for (UUID id : ids) {
            try {
                LandProject done = itemTx.execute(status -> flagOne(id, cutoff));
                if (done != null) flagged.add(done);
            } catch (Exception e) {
                failed.add(indexOf(id));
                System.err.println(">>> [JOBS] 365-day flag failed for " + id + ": " + e.getMessage());
            }
        }
        // one alert per project (it freezes a debt), but a summary when a run flags more than 5 (no flood)
        if (flagged.size() > 5) {
            notificationService.emitToAudience("AUTO_RECEIVABLE_365",
                    flagged.size() + " projects were flagged receivable today (365 days without payment).",
                    "SYSTEM", jobId("auto-receivable"), LocalDate.now());
        } else {
            for (LandProject plot : flagged) {
                notificationService.emitToAudience("AUTO_RECEIVABLE_365",
                        ownerLabel(plot) + " auto-flagged RECEIVABLE after 365 days silent.", "PROJECT", plot.getId(),
                        LocalDate.now());   // fix181 (17.1): once per receivable start, so a second flag a year later is not silent
            }
        }
        reportFailures("AUTO_RECEIVABLE_FAILED", "365-day receivable", failed);
    }

    /** One project in its own transaction. Returns the project when it was flagged, else null. */
    LandProject flagOne(UUID id, LocalDateTime cutoff) {
        LandProject plot = projectRepository.findById(id).orElse(null);
        if (plot == null || plot.isDeleted() || plot.isPending() || plot.isReceivable()) return null;
        // fix181 (4.4): the clock starts at the later of the title date and the graduation date
        if (plot.getGraduatedAt() != null && plot.getGraduatedAt().isAfter(cutoff)) return null;
        BigDecimal outstanding = plot.titleOwed();
        if (outstanding.signum() <= 0) return null;
        if (plot.getLandTitle() != null && plot.getLandTitle().isReleased()) return null;

        // fix167: fees kept by an earlier SET ASIDE are kept, and the month counter starts again from 0
        plot.setReceivable(true);
        plot.setReceivableStartDate(LocalDateTime.now());
        plot.setReceivableMonthsBilled(0);
        plot.setOriginalDebt(outstanding);
        if (plot.getStorageFeesAccumulated() == null) plot.setStorageFeesAccumulated(BigDecimal.ZERO);
        plot.setStorageFeesPaid(BigDecimal.ZERO);
        plot.setStatus("RECEIVABLE");
        projectRepository.save(plot);

        auditService.logActionAfterCommit("AUTO_RECEIVABLE",
            "SYSTEM: Plot " + ownerLabel(plot)
            + " auto-flagged as RECEIVABLE after 365 days of no payment. "
            + "Debt frozen at: UGX " + outstanding);
        return plot;
    }

    // ── PENDING WAITING TOO LONG (08:00) ────────────────────────────────────
    /** fix181 (17.8): one reminder a day while any Pending project has waited more than 3 days for its prices. */
    @Scheduled(cron = "0 0 8 * * *", zone = ZONE)
    public void pendingStaleCheck() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(PendingProjectService.STALE_DAYS);
        long n = projectRepository.findAllIncludingPending().stream()
                .filter(p -> p.isPending() && p.getCreatedAt() != null && p.getCreatedAt().isBefore(cutoff)).count();
        if (n == 0) return;
        notificationService.emitToAudience("PENDING_STALE", n + " Pending project(s) have waited more than "
                + PendingProjectService.STALE_DAYS + " days for prices.", "SYSTEM", jobId("pending-stale"));
    }

    // ── CALLABLE AGAIN (07:00) ──────────────────────────────────────────────
    @Scheduled(cron = "0 0 7 * * *", zone = ZONE)
    public void unlockSweep() {
        LocalDateTime now = LocalDateTime.now();
        RecoveryStateService.Snapshot snap = recoveryState.load();
        for (UUID clientId : snap.projects().keySet()) {
            try {
                var ps = snap.projectsOf(clientId);
                var ns = snap.notesOf(clientId);
                // owes nothing that counts (paid up, only Pending, or in the first month after graduating): no alert
                if (!recoveryState.qualifies(ps, now)) continue;
                if (recoveryState.lockedUntil(ps, ns, now) != null) continue;   // still resting
                LocalDate since = callableSince(ps, ns, now);
                if (since == null) continue;
                Client c = clientRepo.findById(clientId).orElse(null);
                if (c == null) continue;
                // the key is the day they became callable: a second run (or the catch-up at start) writes nothing new
                notificationService.emitToAudience("UNLOCK", c.getFullName() + " is callable again.", "CLIENT", c.getId(), since);
            } catch (Exception e) {
                System.err.println(">>> [JOBS] callable-again failed for " + clientId + ": " + e.getMessage());
            }
        }
    }

    /** The day a rest ended within the last 7 days, or null. */
    LocalDate callableSince(List<LandProject> ps, List<com.gesolutions.erp.modules.client.model.RecoveryNote> ns, LocalDateTime now) {
        LocalDate best = null;
        for (int k = 1; k <= 7; k++) {
            LocalDate u = recoveryState.lockedUntil(ps, ns, now.minusDays(k));
            if (u != null && !u.isAfter(now.toLocalDate()) && (best == null || u.isAfter(best))) best = u;
        }
        return best;
    }

    // ── helpers ─────────────────────────────────────────────────────────────

    private void reportFailures(String code, String jobName, List<String> failed) {
        if (failed.isEmpty()) return;
        auditService.logAction(code, "SYSTEM: the " + jobName + " job could not process " + failed.size()
                + " project(s): " + String.join(", ", failed) + ". The other projects were done.");
        notificationService.emitToAudience("JOB_FAILED",
                "The " + jobName + " job could not process " + failed.size() + " project(s). See the Audit page (" + code + ").",
                "SYSTEM", jobId(code));
    }

    private String indexOf(UUID id) {
        try { return projectRepository.findById(id).map(p -> p.getProjectIndex() != null ? "#" + p.getProjectIndex() : id.toString()).orElse(id.toString()); }
        catch (Exception e) { return id.toString(); }
    }

    private String ownerLabel(LandProject plot) {
        if (plot.billingParties() != null && !plot.billingParties().isEmpty()) {
            for (Client c : plot.billingParties()) return c.getFullName();
        }
        return plot.getProjectIndex() != null ? ("project #" + plot.getProjectIndex()) : "untitled project";
    }
}
