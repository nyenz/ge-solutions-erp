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
        return m;
    }

    @GetMapping("/portfolio")
    @Transactional(readOnly = true)
    public List<Map<String, Object>> portfolio(@PathVariable UUID id) {
        LandProject current = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        List<Map<String, Object>> out = new ArrayList<>();
        if (current.getProprietors() == null) return out;
        for (LandProject other : projectRepository.findAll()) {
            if (other.getId().equals(id) || other.getProprietors() == null) continue;
            for (var owner : current.getProprietors()) {
                if (other.getProprietors().stream().anyMatch(c -> c.getId().equals(owner.getId()))) {
                    Map<String, Object> m = new HashMap<>();
                    m.put("projectId", other.getId());
                    m.put("index", other.getProjectIndex());
                    m.put("plot", other.getLandTitle() != null ? other.getLandTitle().getPlotNumber() : null);
                    m.put("titled", other.getLandTitle() != null);
                    m.put("receivable", other.isReceivable());
                    m.put("sharedOwner", owner.getFullName());
                    out.add(m);
                    break;
                }
            }
        }
        return out;
    }

    @PostMapping("/receivable/enter")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> enter(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setReceivable(true);
        p.setReceivableStartDate(LocalDateTime.now());
        p.setReceivableMonthsBilled(0);
        BigDecimal owed = (p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO)
                .add(p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO)
                .subtract(p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        p.setOriginalDebt(owed.max(BigDecimal.ZERO));
        p.setStatus("RECEIVABLE");
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_ENTER", "Operator [" + op() + "] moved project #" + p.getProjectIndex() + " into receivables.");
        return receivable(id);
    }

    @PostMapping("/receivable/exit")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> exit(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        String action = body.getOrDefault("action", "SET_ASIDE");
        BigDecimal fees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        String reason = body.get("reason") != null ? body.get("reason").trim() : "";
        if ("WAIVE".equals(action)) {
            if (reason.length() < 5) {
                throw new BusinessException("REASON_REQUIRED: Write why these fees are being waived (at least 5 characters).");
            }
            auditService.logAction("FEES_WAIVED", "Operator [" + op() + "] waived UGX " + fees + " on #" + p.getProjectIndex() + ". Reason: " + reason);
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
        } else if ("CAPITALIZE".equals(action)) {
            p.setTotalCost((p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO).add(fees));
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
            auditService.logAction("FEES_CAPITALIZED", "Operator [" + op() + "] capitalized UGX " + fees + " into total cost on #" + p.getProjectIndex() + ".");
        } else {
            auditService.logAction("RECEIVABLE_SET_ASIDE", "Operator [" + op() + "] set aside #" + p.getProjectIndex() + " (fees UGX " + fees + " retained, billing stopped).");
        }
        p.setReceivable(false);
        p.setStatus("ACTIVE");
        projectRepository.save(p);
        return receivable(id);
    }

    @PostMapping("/toggle-problem")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> toggleProblem(@PathVariable UUID id, @RequestParam(value = "note", required = false) String note) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setProblem(!p.isProblem());
        projectRepository.save(p);
        String why = (note != null && !note.isBlank()) ? note.trim() : "";
        String plot = (p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null)
                ? p.getLandTitle().getPlotNumber() : "project #" + p.getProjectIndex();
        auditService.logAction("PROBLEM_FLAG", "Operator [" + op() + "] " + (p.isProblem() ? "flagged" : "cleared") + " PROBLEM on #" + p.getProjectIndex() + (why.isEmpty() ? "" : ": " + why) + ".");
        if (p.isProblem()) {
            // fix135: only FLAGGING notifies (clearing is not news). emitRaw, not emit,
            // because emit() dedupes forever per type+entity and a plot can be flagged twice.
            notificationService.emitRaw("PROBLEM_FLAGGED", "CRITICAL",
                    "Plot " + plot + " flagged as a problem by " + op() + (why.isEmpty() ? "." : ": " + why),
                    "PROJECT", p.getId(), "ALL");
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
        p.setStorageFeesAccumulated(target);
        projectRepository.save(p);
        auditService.logAction("FEES_REDUCED", "Operator [" + op() + "] reduced storage fees on #" + p.getProjectIndex()
                + " from UGX " + current.toPlainString() + " to UGX " + target.toPlainString() + ". Reason: " + why);
        return receivable(id);
    }

    @PostMapping("/receivable/settings")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> settings(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        // fix164: a rate change or a NEW pause date needs a written reason and is audited as OLD -> NEW.
        // Clearing a pause (RESUME FEES) needs no reason.
        BigDecimal oldRate = p.getStorageFeeOverride();
        LocalDateTime oldDeadline = p.getNegotiationDeadline();
        BigDecimal newRate = oldRate;
        LocalDateTime newDeadline = oldDeadline;
        if (body.containsKey("rate")) {
            newRate = body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate"));
            if (newRate != null && newRate.signum() < 0) {
                throw new BusinessException("RATE_INVALID: The monthly storage rate cannot be negative.");
            }
        }
        if (body.containsKey("deadline")) {
            newDeadline = body.get("deadline") == null || body.get("deadline").isBlank() ? null : LocalDateTime.parse(body.get("deadline"));
        }
        boolean rateChanged = (oldRate == null) != (newRate == null)
                || (oldRate != null && newRate != null && oldRate.compareTo(newRate) != 0);
        boolean pauseSet = newDeadline != null && !newDeadline.equals(oldDeadline);
        String why = body.get("reason") == null ? "" : body.get("reason").trim();
        if ((rateChanged || pauseSet) && why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the rate or pause is changing (at least 5 characters).");
        }
        p.setStorageFeeOverride(newRate);
        p.setNegotiationDeadline(newDeadline);
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex()
                + " (monthly rate: " + (oldRate != null ? "UGX " + oldRate.toPlainString() : "default")
                + " -> " + (newRate != null ? "UGX " + newRate.toPlainString() : "default")
                + ", fees paused until: " + (oldDeadline != null ? oldDeadline.toString() : "not paused")
                + " -> " + (newDeadline != null ? newDeadline.toString() : "not paused") + ")"
                + (why.isEmpty() ? "" : ". Reason: " + why));
        return receivable(id);
    }
}
