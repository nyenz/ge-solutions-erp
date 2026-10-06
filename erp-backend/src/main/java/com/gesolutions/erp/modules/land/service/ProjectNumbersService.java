// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ProjectNumbersService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectStatus;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.ProjectStatusRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix196: THE INVOICE NUMBER AND THE CONTRACT NUMBER -- every rule about them, in one place.
 *
 *  1. A project that is NOT Pending has both numbers. A project leaves Pending in ONE step that needs the invoice
 *     number, the contract number AND the prices together (PendingProjectService.graduatePending, or the office's own
 *     New Project). Until then it stays Pending.
 *  2. Any format is accepted (letters, digits, slashes...), 1 to 80 characters, spaces tidied.
 *  3. Each number is on ONE live project only (capitals do not matter; a deleted project does not hold its numbers).
 *  4. Anyone except an Employee may correct them later (correct()). Every change is audited with old and new values.
 *  5. The stage called "Invoice / Contract Number" is ticked by itself when the numbers are saved, and it cannot be
 *     ticked by hand while the numbers are missing.
 * Projects from before fix196 have no numbers; they keep working and the folder page offers to add them.
 */
@Service
@RequiredArgsConstructor
public class ProjectNumbersService {

    public static final int MAX_LENGTH = 80;

    private final LandProjectRepository projectRepository;
    private final ProjectStatusRepository statusRepository;
    private final AuditService auditService;

    /** Trimmed, inner spaces tidied; null when nothing was typed. */
    public static String clean(String v) {
        if (v == null) return null;
        String s = v.trim().replaceAll("\\s+", " ");
        return s.isEmpty() ? null : s;
    }

    /** true for the stage that stands for the invoice and contract numbers (same test as the page's projectStatus.js). */
    public static boolean isInvoiceContractStage(String stageName) {
        if (stageName == null) return false;
        String n = stageName.toLowerCase(java.util.Locale.ROOT);
        return n.contains("invoice") && n.contains("contract");
    }

    public static boolean hasBoth(LandProject p) {
        return p != null && clean(p.getInvoiceNumber()) != null && clean(p.getContractNumber()) != null;
    }

    /** Checks both numbers for a project (selfId = null for a project that is not saved yet). Returns { invoice, contract }. */
    public String[] check(UUID selfId, String invoice, String contract) {
        String inv = clean(invoice), con = clean(contract);
        if (inv == null || con == null) {
            throw new BusinessException("NUMBERS_REQUIRED: Enter the invoice number AND the contract number. A project needs both.");
        }
        if (inv.length() > MAX_LENGTH || con.length() > MAX_LENGTH) {
            throw new BusinessException("NUMBER_TOO_LONG: An invoice or contract number can be at most " + MAX_LENGTH + " characters.");
        }
        for (LandProject o : projectRepository.findLiveByInvoiceNumber(inv)) {
            if (!o.getId().equals(selfId)) {
                throw new BusinessException("INVOICE_NUMBER_TAKEN: Invoice number \"" + inv + "\" is already on project #" + o.getProjectIndex()
                        + ". Every project has its own invoice number.");
            }
        }
        for (LandProject o : projectRepository.findLiveByContractNumber(con)) {
            if (!o.getId().equals(selfId)) {
                throw new BusinessException("CONTRACT_NUMBER_TAKEN: Contract number \"" + con + "\" is already on project #" + o.getProjectIndex()
                        + ". Every project has its own contract number.");
            }
        }
        return new String[] { inv, con };
    }

    /** Checks and writes both numbers onto the project (the caller saves the project). */
    public void apply(LandProject p, String invoice, String contract) {
        String[] n = check(p.getId(), invoice, contract);
        p.setInvoiceNumber(n[0]);
        p.setContractNumber(n[1]);
    }

    /** Ticks the project's Invoice / Contract stage when it is there and not ticked yet. */
    public void tickStage(UUID projectId) {
        for (ProjectStatus s : statusRepository.findByProjectIdOrderByDisplayOrderAsc(projectId)) {
            if (isInvoiceContractStage(s.getStatusName()) && !s.isCompleted()) {
                s.setCompleted(true);
                s.setCompletedAt(LocalDateTime.now());
                s.setCompletedBy(AuditService.currentOperator());
                statusRepository.save(s);
            }
        }
    }

    /** Rule 4: correct the numbers of a started project (or add them to a project older than fix196). */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public LandProject correct(UUID projectId, String invoice, String contract) {
        LandProject p = projectRepository.findByIdForUpdate(projectId)
                .orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        if (p.isDeleted()) throw new BusinessException("PROJECT_DELETED: This project is deleted. Restore it first.");
        if (p.isPending()) {
            throw new BusinessException("STILL_PENDING: This project is still Pending. The numbers are entered together with the prices when the project is started.");
        }
        String oldInv = clean(p.getInvoiceNumber()), oldCon = clean(p.getContractNumber());
        apply(p, invoice, contract);
        boolean changed = !p.getInvoiceNumber().equals(oldInv) || !p.getContractNumber().equals(oldCon);
        LandProject saved = projectRepository.save(p);
        tickStage(saved.getId());
        if (changed) {
            auditService.logActionAfterCommit("PROJECT_NUMBERS_CHANGED", "Operator [" + AuditService.currentOperator() + "] set the numbers of project #"
                    + saved.getProjectIndex() + ". Invoice: " + (oldInv == null ? "(none)" : oldInv) + " -> " + saved.getInvoiceNumber()
                    + ". Contract: " + (oldCon == null ? "(none)" : oldCon) + " -> " + saved.getContractNumber() + ".");
        }
        return saved;
    }
}
