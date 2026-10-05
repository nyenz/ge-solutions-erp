package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/v1/land/portal/{id}")
@RequiredArgsConstructor
public class FolderPortalController {

    private final LandProjectRepository projectRepository;
    private final AuditService auditService;
    private final NotificationService notificationService;
    private final com.gesolutions.erp.modules.land.repository.FollowUpRepository followUpRepository;

    private String op() {
        var a = SecurityContextHolder.getContext().getAuthentication();
        return a != null ? a.getName() : "SYSTEM";
    }

    @GetMapping("/receivable")
    @Transactional(readOnly = true)
    public Map<String, Object> receivable(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        Map<String, Object> m = new HashMap<>();
        m.put("receivable", p.isReceivable());
        m.put("actual", p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO);
        m.put("storage", p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO);
        m.put("paid", p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        m.put("total", p.receivableTotalOwed());
        m.put("rate", p.getStorageFeeOverride());
        m.put("deadline", p.getNegotiationDeadline());
        m.put("startDate", p.getReceivableStartDate());
        m.put("backlog", p.getLandTitle() == null);
        m.put("problem", p.isProblem());
        m.put("storagePaid", p.storagePaidSafe());
        m.put("storageUnpaid", p.storageUnpaid());
        return m;
    }

    // fix167: one database query (it used to load EVERY project), deleted projects left out, and each row says
    // whether the plot is handed over or flagged as a problem.
    @GetMapping("/portfolio")
    @Transactional(readOnly = true)
    public List<Map<String, Object>> portfolio(@PathVariable UUID id) {
        LandProject current = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        List<Map<String, Object>> out = new ArrayList<>();
        if (current.getProprietors() == null || current.getProprietors().isEmpty()) return out;
        List<UUID> ownerIds = new ArrayList<>();
        for (var o : current.getProprietors()) ownerIds.add(o.getId());
        for (LandProject other : projectRepository.findRelatedByOwners(ownerIds, id)) {
            for (var owner : current.getProprietors()) {
                if (other.getProprietors().stream().anyMatch(c -> c.getId().equals(owner.getId()))) {
                    Map<String, Object> m = new HashMap<>();
                    m.put("projectId", other.getId());
                    m.put("index", other.getProjectIndex());
                    m.put("plot", other.getLandTitle() != null ? other.getLandTitle().getPlotNumber() : null);
                    m.put("titled", other.getLandTitle() != null);
                    m.put("released", other.getLandTitle() != null && other.getLandTitle().isReleased());
                    m.put("receivable", other.isReceivable());
                    m.put("problem", other.isProblem());
                    m.put("sharedOwner", owner.getFullName());
                    out.add(m);
                }
            }
        }
        return out;
    }

    @PostMapping("/receivable/enter")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> enter(@PathVariable UUID id, @RequestBody(required = false) Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        // fix166: starting storage fees is a money action -> director only (like every other receivable control), with a
        // written reason. Before: a manager could call it, it had no checks, and calling it AGAIN on a project already in
        // receivables restarted the billing clock; calling it on a handed-over or fully paid project overwrote its status.
        String enterWhy = (body != null && body.get("reason") != null) ? body.get("reason").trim() : "";
        if (enterWhy.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why this project is moving to receivables (at least 5 characters).");
        }
        if (p.isDeleted()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is deleted. Restore it first.");
        }
        if (p.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is already in receivables.");
        }
        if (p.getLandTitle() != null && p.getLandTitle().isReleased()) {
            throw new BusinessException("RECEIVABLE_FAULT: The title has been handed over. Undo the hand-over first.");
        }
        BigDecimal enterOwed = (p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO)
                .add(p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO)
                .subtract(p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        if (enterOwed.signum() <= 0) {
            throw new BusinessException("RECEIVABLE_FAULT: Nothing is owed on this project, so it cannot go to receivables.");
        }
        p.setReceivable(true);
        p.setReceivableStartDate(LocalDateTime.now());
        p.setReceivableMonthsBilled(0);
        BigDecimal owed = (p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO)
                .add(p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO)
                .subtract(p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        p.setOriginalDebt(owed.max(BigDecimal.ZERO));
        p.setStatus("RECEIVABLE");
        projectRepository.save(p);
        auditService.logActionAfterCommit("RECEIVABLE_ENTER", "Operator [" + op() + "] moved project #" + p.getProjectIndex() + " into receivables. Debt frozen at UGX " + owed.max(BigDecimal.ZERO).toPlainString() + ". Reason: " + enterWhy);
        return receivable(id);
    }

    @PostMapping("/receivable/exit")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> exit(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        String action = body.getOrDefault("action", "SET_ASIDE");
        BigDecimal fees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        BigDecimal feesPaid = p.storagePaidSafe();
        BigDecimal feesUnpaid = p.storageUnpaid();
        BigDecimal costBefore = p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO;
        String reason = body.get("reason") != null ? body.get("reason").trim() : "";
        // fix166: only the three known actions, only on a project in receivables, always with a reason.
        // fix167: WAIVE and ADD FEES TO COST also work on fees kept by an earlier SET ASIDE (before, those fees could
        // only be cleared by moving the project back into receivables, and a hand-over silently ignored them).
        if (!"WAIVE".equals(action) && !"CAPITALIZE".equals(action) && !"SET_ASIDE".equals(action)) {
            throw new BusinessException("ACTION_INVALID: Unknown receivable action.");
        }
        if (p.isDeleted()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is deleted. Restore it first.");
        }
        boolean keptFees = !p.isReceivable() && feesUnpaid.signum() > 0;
        if (!p.isReceivable() && !(keptFees && !"SET_ASIDE".equals(action))) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is not in receivables.");
        }
        if (reason.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why (at least 5 characters).");
        }
        // fix167 money rule: once a project is out of receivables its storage-fee PAYMENTS count toward the total cost
        // (the paid fees are moved into the cost), so "owed = cost - paid" stays right. Only UNPAID fees are waived,
        // added to the cost, or kept aside.
        if ("WAIVE".equals(action)) {
            p.setTotalCost(costBefore.add(feesPaid));
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
            p.setStorageFeesPaid(BigDecimal.ZERO);
            auditService.logActionAfterCommit("FEES_WAIVED", "Operator [" + op() + "] waived UGX " + feesUnpaid.toPlainString() + " of unpaid storage fees on #" + p.getProjectIndex()
                    + (feesPaid.signum() > 0 ? " (UGX " + feesPaid.toPlainString() + " already paid toward fees stays counted: total cost UGX " + costBefore.toPlainString() + " -> UGX " + costBefore.add(feesPaid).toPlainString() + ")" : "")
                    + ". Reason: " + reason);
        } else if ("CAPITALIZE".equals(action)) {
            p.setTotalCost(costBefore.add(fees));
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
            p.setStorageFeesPaid(BigDecimal.ZERO);
            auditService.logActionAfterCommit("FEES_CAPITALIZED", "Operator [" + op() + "] capitalized UGX " + fees.toPlainString() + " of storage fees into total cost on #" + p.getProjectIndex()
                    + " (total cost UGX " + costBefore.toPlainString() + " -> UGX " + costBefore.add(fees).toPlainString() + "). Reason: " + reason);
        } else {
            p.setTotalCost(costBefore.add(feesPaid));
            p.setStorageFeesAccumulated(feesUnpaid);
            p.setStorageFeesPaid(BigDecimal.ZERO);
            auditService.logActionAfterCommit("RECEIVABLE_SET_ASIDE", "Operator [" + op() + "] set aside #" + p.getProjectIndex() + " (UGX " + feesUnpaid.toPlainString()
                    + " of unpaid fees kept, billing stopped"
                    + (feesPaid.signum() > 0 ? "; UGX " + feesPaid.toPlainString() + " of paid fees moved into the total cost" : "") + "). Reason: " + reason);
        }
        if (p.getStoragePausedAt() != null || p.getNegotiationDeadline() != null || p.isStoragePaused()) p.endStoragePause(LocalDateTime.now());
        p.setReceivable(false);
        if (!(p.getLandTitle() != null && p.getLandTitle().isReleased())) p.setStatus("ACTIVE");
        projectRepository.save(p);
        return receivable(id);
    }

    // fix167: the page says what it WANTS (flag=true to flag, flag=false to clear). Before, two people clicking at the
    // same time made the second click silently clear the first person's flag. Who flagged it, when and why is stored.
    @PostMapping("/toggle-problem")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> toggleProblem(@PathVariable UUID id,
                                             @RequestParam(value = "note", required = false) String note,
                                             @RequestParam(value = "flag", required = false) Boolean flag) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        if (p.isDeleted()) {
            throw new BusinessException("PLOT_DELETED: This project is deleted. Restore it first.");
        }
        boolean want = flag != null ? flag : !p.isProblem();
        if (want == p.isProblem()) {
            throw new BusinessException(want
                    ? "ALREADY_FLAGGED: Someone else flagged this plot as a PROBLEM a moment ago. Reload the page."
                    : "ALREADY_CLEARED: Someone else cleared this PROBLEM flag a moment ago. Reload the page.");
        }
        if (note == null || note.trim().length() < 5) {
            throw new BusinessException(p.isProblem()
                    ? "REASON_REQUIRED: Write why the problem flag is being cleared (at least 5 characters)."
                    : "REASON_REQUIRED: Write what the problem is (at least 5 characters).");
        }
        String why = note.trim();
        p.setProblem(want);
        if (want) {
            p.setProblemBy(op());
            p.setProblemAt(LocalDateTime.now());
            p.setProblemNote(why);
        } else {
            p.setProblemBy(null);
            p.setProblemAt(null);
            p.setProblemNote(null);
        }
        projectRepository.save(p);
        // fix167: the note is written in the SAME step as the flag (it used to be a second call from the page that could fail alone)
        followUpRepository.save(com.gesolutions.erp.modules.land.model.FollowUpLog.builder().projectId(p.getId())
                .notes((want ? "[PROBLEM] " : "[PROBLEM CLEARED] ") + why).recordedBy(op()).build());
        String plot = (p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null)
                ? p.getLandTitle().getPlotNumber() : "project #" + p.getProjectIndex();
        auditService.logActionAfterCommit("PROBLEM_FLAG", "Operator [" + op() + "] " + (want ? "flagged" : "cleared") + " PROBLEM on #" + p.getProjectIndex() + ": " + why + ".");
        if (want) {
            // fix181 (17.5): the alert never carries the typed reason (it can hold names, phones, family matters);
            // the reason stays in the Notes timeline of the folder.
            notificationService.emitToAudience("PROBLEM_FLAGGED",
                    "Plot " + plot + " flagged as a problem by " + op() + ". Open the folder to read the reason.",
                    "PROJECT", p.getId());
        } else {
            // fix181 (3.2g): the Director hears when a problem is cleared
            notificationService.emitToAudience("PROBLEM_CLEARED",
                    "Problem on plot " + plot + " cleared by " + op() + ".", "PROJECT", p.getId());
        }
        return receivable(id);
    }

    // fix162: REDUCE the accumulated storage fees to an agreed lower total (negotiation). Reason required, audited.
    @PostMapping("/receivable/reduce-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> reduceFees(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        String why = body.get("reason") != null ? body.get("reason").trim() : "";
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the fees are being reduced (at least 5 characters).");
        }
        if (!p.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is not in receivables.");
        }
        BigDecimal current = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        BigDecimal target;
        try {
            target = new BigDecimal(String.valueOf(body.get("newFees")).trim());
        } catch (Exception e) {
            throw new BusinessException("FEES_INVALID: Enter the new total storage fees as a number.");
        }
        if (target.compareTo(BigDecimal.ZERO) < 0) {
            throw new BusinessException("FEES_INVALID: The new total cannot be below zero.");
        }
        if (target.compareTo(current) >= 0) {
            throw new BusinessException("FEES_INVALID: The new total must be lower than the current UGX " + current.toPlainString() + ".");
        }
        // fix167: fees the client already paid cannot be reduced away (reverse that payment first)
        if (target.compareTo(p.storagePaidSafe()) < 0) {
            throw new BusinessException("FEES_INVALID: UGX " + p.storagePaidSafe().toPlainString()
                    + " of storage fees is already paid, so the new total cannot be lower than that.");
        }
        p.setStorageFeesAccumulated(target);
        projectRepository.save(p);
        auditService.logActionAfterCommit("FEES_REDUCED", "Operator [" + op() + "] reduced storage fees on #" + p.getProjectIndex()
                + " from UGX " + current.toPlainString() + " to UGX " + target.toPlainString() + ". Reason: " + why);
        return receivable(id);
    }

    // fix164 + fix167: change the monthly rate and / or pause the fees until a date, or resume them.
    //   rate: blank = the default 50,000; 0 = no more fees (it used to turn silently into 50,000).
    //   pause: must end in the future and within 365 days. Every change, RESUME included, needs a reason.
    //   A pause now really skips those months: when it ends the billing clock moves forward by the paused days.
    @PostMapping("/receivable/settings")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> settings(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        BigDecimal oldRate = p.getStorageFeeOverride();
        LocalDateTime oldDeadline = p.getNegotiationDeadline();
        boolean wasPaused = oldDeadline != null || p.isStoragePaused();
        BigDecimal newRate = oldRate;
        LocalDateTime newDeadline = oldDeadline;
        if (body.containsKey("rate")) {
            try {
                newRate = body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate").trim());
            } catch (NumberFormatException e) {
                throw new BusinessException("RATE_INVALID: Enter the monthly storage rate as a plain number.");
            }
            if (newRate != null && newRate.signum() < 0) {
                throw new BusinessException("RATE_INVALID: The monthly storage rate cannot be negative.");
            }
            if (newRate != null && newRate.stripTrailingZeros().scale() > 0) {
                throw new BusinessException("RATE_INVALID: Whole shillings only.");
            }
        }
        boolean resume = false;
        if (body.containsKey("deadline")) {
            String d = body.get("deadline");
            if (d == null || d.isBlank()) {
                newDeadline = null;
                resume = wasPaused;
            } else {
                try {
                    String t = d.trim();
                    newDeadline = t.length() == 10 ? java.time.LocalDate.parse(t).atTime(23, 59, 59) : LocalDateTime.parse(t);
                } catch (java.time.format.DateTimeParseException e) {
                    throw new BusinessException("PAUSE_INVALID: The pause date is not a valid date.");
                }
            }
        }
        boolean rateChanged = (oldRate == null) != (newRate == null)
                || (oldRate != null && newRate != null && oldRate.compareTo(newRate) != 0);
        boolean pauseSet = newDeadline != null && !newDeadline.equals(oldDeadline);
        if (pauseSet && !newDeadline.isAfter(LocalDateTime.now())) {
            throw new BusinessException("PAUSE_INVALID: The pause must end in the future.");
        }
        if (pauseSet && newDeadline.isAfter(LocalDateTime.now().plusDays(365))) {
            throw new BusinessException("PAUSE_INVALID: A pause cannot be longer than 365 days. Pause again later if more time is needed.");
        }
        if ((rateChanged || pauseSet || resume) && !p.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: This project is not in receivables.");
        }
        if (!rateChanged && !pauseSet && !resume) {
            throw new BusinessException("NOTHING_CHANGED: The rate and the pause are already set like that.");
        }
        String why = body.get("reason") == null ? "" : body.get("reason").trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the rate or pause is changing (at least 5 characters).");
        }
        p.setStorageFeeOverride(newRate);
        if (resume) {
            p.endStoragePause(LocalDateTime.now());
        } else if (pauseSet) {
            if (p.getStoragePausedAt() == null) p.setStoragePausedAt(LocalDateTime.now());
            p.setNegotiationDeadline(newDeadline);
        }
        projectRepository.save(p);
        auditService.logActionAfterCommit("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex()
                + " (monthly rate: " + (oldRate != null ? "UGX " + oldRate.toPlainString() : "default") + " -> " + (newRate != null ? "UGX " + newRate.toPlainString() : "default")
                + ", fees paused until: " + (oldDeadline != null ? oldDeadline.toLocalDate().toString() : (p.isStoragePaused() ? "paused" : "not paused"))
                + " -> " + (resume ? "RESUMED now" : (p.getNegotiationDeadline() != null ? p.getNegotiationDeadline().toLocalDate().toString() : "not paused")) + ")"
                + ". Reason: " + why);
        return receivable(id);
    }
}
