// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.service.ClientService;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.*;
import com.gesolutions.erp.modules.land.dto.*;
import com.gesolutions.erp.modules.land.repository.*;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
public class LandService {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;
    private final ProjectDocumentRepository documentRepository;
    private final DocumentCategoryService documentCategoryService;
    private final ClientRepository clientRepository;
    private final ClientService clientService;
    private final FileStorageService fileStorageService;
    private final AuditService auditService;
    private final PaymentRecordRepository paymentRecordRepository;
    private final ProjectIndexService projectIndexService;
    private final StatusTemplateService statusTemplateService;
    private final ProjectStatusRepository projectStatusRepository;
    private final LandTitleRepository landTitleRepository;
    private final ProjectNeighborRepository neighborRepository;
    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;
    private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    // PHASE B (Section 18.9.1): landTitle can now be null. Every audit-log
    // call site that used to read project.getLandTitle().getPlotNumber()
    // directly goes through this instead -- falls back to projectIndex
    // (now on LandProject itself, see Phase B migration) when there is no
    // title yet, instead of NPE-ing.
    private String plotLabel(LandProject project) {
        if (project.getLandTitle() != null && project.getLandTitle().getPlotNumber() != null) {
            return project.getLandTitle().getPlotNumber();
        }
        return "project #" + project.getProjectIndex();
    }

    // ─── UNLOCK LOG ───────────────────────────────────────────────────────────

    @Transactional
    public void logUnlockAction(UUID id) {
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        auditService.logActionAfterCommit("EDIT_MODE_OPENED",
            "Operator [" + getCurrentOperator() + "] opened edit mode for plot: "
            + plotLabel(project));
    }

    // ─── DEEP DETAIL ──────────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public ProjectDeepDetailDTO getProjectDeepDetail(UUID id) {
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("VAULT FAULT"));
        List<FollowUpLog> notes = followUpRepository.findByProjectIdOrderByTimestampDesc(id);
        List<ProjectDocument> documents = documentRepository.findByProjectId(id);
        List<PaymentRecord> payments = paymentRecordRepository.findByProjectIdOrderByTimestampDesc(id);

        BigDecimal cost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal paid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;

        BigDecimal remaining;
        if (project.isReceivable()) {
            remaining = project.receivableTotalOwed();
        } else {
            remaining = cost.subtract(paid);
        }

        double percent = cost.compareTo(BigDecimal.ZERO) > 0
                ? paid.divide(cost, 4, RoundingMode.HALF_UP).doubleValue() * 100 : 0;

        // fix180: neighbors, the subdivision plots (and which ones were transferred), and the parent of a transfer
        List<SubdivisionPlotDTO> plots = new ArrayList<>();
        if (ProjectType.of(project) == ProjectType.SUBDIVISION && project.getSubdivisionCount() != null) {
            Map<Integer, LandProject> byNo = new HashMap<>();
            for (LandProject t : projectRepository.findTransfersOf(id)) {
                if (t.getParentSubdivisionNo() != null) byNo.put(t.getParentSubdivisionNo(), t);
            }
            for (int n = 1; n <= project.getSubdivisionCount(); n++) {
                LandProject t = byNo.get(n);
                plots.add(SubdivisionPlotDTO.builder().number(n)
                        .transferProjectId(t != null ? t.getId() : null)
                        .transferProjectIndex(t != null ? t.getProjectIndex() : null)
                        .transferPlotNumber(t != null && t.getLandTitle() != null ? t.getLandTitle().getPlotNumber() : null)
                        .build());
            }
        }
        String parentIndex = project.getParentProjectId() == null ? null
                : projectRepository.findById(project.getParentProjectId()).map(LandProject::getProjectIndex).orElse(null);

        return ProjectDeepDetailDTO.builder()
                .project(project)
                .notes(notes)
                .documents(documents)
                .payments(payments)
                .remainingBalance(remaining)
                .collectionPercentage(percent)
                .neighbors(neighborRepository.findByProjectIdOrderByDisplayOrderAsc(id))
                .statuses(projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(id))
                .subdivisions(plots)
                .parentProjectIndex(parentIndex)
                .build();
    }

    // ─── PAYMENT RECORDING ────────────────────────────────────────────────────

    // fix167: a payment now says WHO paid (one owner of the project) and WHAT it pays for:
    //   TITLE   = the work (total cost). Cannot go over what is still owed on the work.
    //   STORAGE = storage fees. Only on a project in receivables, and never more than the fees not yet paid.
    // Joint owners: when a project has more than one owner the payer MUST be named, so each owner's money is tracked.
    // fix180: the payer is one of the project's CLIENTS (the people who pay and whom Recovery calls), not the owners.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public PaymentRecord recordPayment(UUID projectId, BigDecimal amount, String notes, UUID payerId, String allocation) {
        return recordPayment(projectId, amount, notes, payerId, allocation, null);
    }

    // fix181 (16.12): the project row is LOCKED while the payment is checked and saved, so two people paying at the same
    // moment are done one after the other (both used to pass the overpayment check, and one total could be lost).
    // clientRequestId: a payment window sends the same id on a retry; the second request is refused.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public PaymentRecord recordPayment(UUID projectId, BigDecimal amount, String notes, UUID payerId, String allocation,
                                       String clientRequestId) {
        return recordPayment(projectId, amount, notes, payerId, allocation, clientRequestId, null);
    }

    /** fix181 (16.9): how far back a "Date paid" may go (older money needs a Director note, not a silent backdate). */
    public static final int MAX_BACKDATE_DAYS = 60;

    // fix181 (16.9): paidOnDate = the day the money was received (optional; null = today). Not in the future, not more than
    // 60 days back, not before the project was entered. It is saved as paid_on; timestamp stays the entry time.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public PaymentRecord recordPayment(UUID projectId, BigDecimal amount, String notes, UUID payerId, String allocation,
                                       String clientRequestId, java.time.LocalDate paidOnDate) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }
        String requestId = clientRequestId == null || clientRequestId.isBlank() ? null
                : clientRequestId.trim().substring(0, Math.min(64, clientRequestId.trim().length()));

        LandProject project = projectRepository.findByIdForUpdate(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (requestId != null && paymentRecordRepository.existsByClientRequestIdAndRecordedBy(requestId, getCurrentOperator())) {
            throw new BusinessException("DUPLICATE_PAYMENT: This payment was already recorded.");
        }
        java.time.LocalDate today = java.time.LocalDate.now();
        if (paidOnDate != null) {
            if (paidOnDate.isAfter(today)) {
                throw new BusinessException("DATE_INVALID: The date paid cannot be in the future.");
            }
            if (paidOnDate.isBefore(today.minusDays(MAX_BACKDATE_DAYS))) {
                throw new BusinessException("DATE_INVALID: The date paid can be at most " + MAX_BACKDATE_DAYS
                        + " days ago. For older money, ask a Director to record it with a note.");
            }
            java.time.LocalDate entered = project.getCreatedAt() != null ? project.getCreatedAt().toLocalDate() : project.getEntryDate();
            if (entered != null && paidOnDate.isBefore(entered)) {
                throw new BusinessException("DATE_INVALID: The date paid cannot be before the project was entered (" + entered + ").");
            }
        }
        // fix165: no money can be recorded against a deleted project, and no fractions of a shilling.
        if (project.isDeleted()) {
            throw new BusinessException("PAYMENT_BLOCKED: This project is deleted. Restore it first.");
        }
        if (amount.stripTrailingZeros().scale() > 0) {
            throw new BusinessException("PAYMENT_FAULT: Enter whole shillings only (no decimals).");
        }

        String kind = allocation == null || allocation.isBlank() ? "TITLE" : allocation.trim().toUpperCase();
        if (!"TITLE".equals(kind) && !"STORAGE".equals(kind)) {
            throw new BusinessException("PAYMENT_FAULT: A payment is either for the TITLE work or for STORAGE fees.");
        }

        // who paid
        Client payer = null;
        Set<Client> owners = project.billingParties();
        if (payerId != null) {
            for (Client c : owners) if (c.getId().equals(payerId)) payer = c;
            if (payer == null) throw new BusinessException("PAYER_INVALID: The person who paid must be one of this project's clients.");
        } else if (owners.size() == 1) {
            payer = owners.iterator().next();
        } else if (owners.size() > 1) {
            throw new BusinessException("PAYER_REQUIRED: This project has " + owners.size() + " clients. Pick which client paid.");
        }

        BigDecimal cost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal paidNow = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        BigDecimal titlePaid = paidNow.subtract(project.storagePaidSafe());
        // fix173: a STORAGE payment is allowed in two cases: the project is in receivables, OR it was SET ASIDE and still carries
        // kept (unpaid) fees. The second case is "collecting set-aside fees": billing stays stopped, no new fees are added.
        boolean keptFeesPayment = "STORAGE".equals(kind) && !project.isReceivable();
        if ("STORAGE".equals(kind)) {
            if (keptFeesPayment && project.storageUnpaid().signum() <= 0) {
                throw new BusinessException("PAYMENT_FAULT: There are no storage fees to pay on this project. Storage fees can be paid while the project is in receivables, or while set-aside fees are still kept on it.");
            }
            BigDecimal feesLeft = project.storageUnpaid();
            if (amount.compareTo(feesLeft) > 0) {
                throw new BusinessException("OVERPAYMENT_BLOCKED: Only UGX " + feesLeft.toPlainString()
                        + " of storage fees is unpaid. You tried to record UGX " + amount.toPlainString() + ".");
            }
        } else {
            BigDecimal workLeft = cost.subtract(titlePaid).max(BigDecimal.ZERO);
            if (amount.compareTo(workLeft) > 0) {
                throw new BusinessException("OVERPAYMENT_BLOCKED: Only UGX " + workLeft.toPlainString()
                        + " is owed on the title work. You tried to record UGX " + amount.toPlainString()
                        + (project.isReceivable() ? ". Record the rest as a STORAGE FEE payment." : "."));
            }
        }

        String operator = getCurrentOperator();
        String paymentType = project.isReceivable() ? "RECEIVABLE_PARTIAL" : "STANDARD";

        project.setAmountPaid(paidNow.add(amount));
        if (keptFeesPayment) {
            // fix173: paid set-aside fees move into the total cost at once (the same rule SET ASIDE and WAIVE use for paid fees),
            // so "owed = total cost - amount paid" stays true and only the kept (unpaid) fees go down.
            project.setTotalCost(cost.add(amount));
            project.setStorageFeesAccumulated(project.getStorageFeesAccumulated().subtract(amount));
        } else if ("STORAGE".equals(kind)) {
            project.setStorageFeesPaid(project.storagePaidSafe().add(amount));
        }
        LocalDateTime now = LocalDateTime.now();
        // a past day is kept as 12:00 of that day; today is the real time
        LocalDateTime paidAt = paidOnDate == null || paidOnDate.equals(today) ? now : paidOnDate.atTime(12, 0);
        // the last payment date only moves FORWARD (a backdated payment never makes it older)
        if (project.getLastPaymentDate() == null || paidAt.isAfter(project.getLastPaymentDate())) project.setLastPaymentDate(paidAt);

        BigDecimal balanceAfter = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());

        PaymentRecord record = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(amount)
                .paymentType(paymentType)
                .recordedBy(operator)
                .notes(notes)
                .timestamp(now)
                .paidOn(paidAt)                   // fix181 (16.9): the day paid (today unless a date was given)
                .clientRequestId(requestId)
                .balanceAfter(balanceAfter)
                .allocation(kind)
                .payerClientId(payer != null ? payer.getId() : null)
                .payerName(payer != null ? payer.getFullName() : null)
                .build();
        record = paymentRecordRepository.save(record);

        // Auto-exit receivable if fully paid. fix167: the (now fully paid) fees move into the total cost, so the
        // project leaves receivables with total cost = everything it was charged and nothing owed.
        if (project.isReceivable() && balanceAfter.compareTo(BigDecimal.ZERO) <= 0) {
            BigDecimal fees = project.getStorageFeesAccumulated() != null ? project.getStorageFeesAccumulated() : BigDecimal.ZERO;
            project.setTotalCost(project.getTotalCost().add(fees));
            project.setStorageFeesAccumulated(BigDecimal.ZERO);
            project.setStorageFeesPaid(BigDecimal.ZERO);
            project.setReceivable(false);
            project.setStatus("ACTIVE");
            projectRepository.save(project);
            auditService.logActionAfterCommit("RECEIVABLE_EXIT",
                "Operator [" + operator + "] -- Plot " + plotLabel(project)
                + " EXITED RECEIVABLE after full payment clearance (UGX " + fees.toPlainString() + " of paid storage fees moved into the total cost).");
            notificationService.emitToAudience("RECEIVABLE_EXIT",   // fix181 (17.2)
                plotLabel(project) + " left receivables: fully paid.", "PROJECT", projectId);
        } else {
            projectRepository.save(project);
        }

        if ("RECEIVABLE_PARTIAL".equals(paymentType)) {
            notificationService.emitToAudience("PAYMENT_ON_RECEIVABLE", "Payment UGX " + amount + " received on " + plotLabel(project) + ".", "PROJECT", projectId);
        }
        // fix167: the "payment received" line goes on the recovery card of the client who PAID (not on every client)
        java.util.List<Client> noteFor = new java.util.ArrayList<>();
        if (payer != null) noteFor.add(payer); else noteFor.addAll(owners);
        for (Client owner : noteFor) {
            recoveryNoteRepository.save(com.gesolutions.erp.modules.client.model.RecoveryNote.builder()
                .client(owner).author(null).tag("payment received").tone("INFO").countsAsAttempt(false)
                .text("Paid UGX " + amount + " on " + paidAt.toLocalDate() + ("STORAGE".equals(kind) ? " (storage fees)" : "")).build());
        }
        auditService.logActionAfterCommit("PAYMENT_RECORDED",
            "Operator [" + operator + "] recorded UGX " + amount
            + " for plot: " + plotLabel(project)
            + " | Type: " + paymentType
            + " | For: " + kind + (keptFeesPayment ? " (set-aside fees)" : "")
            + (payer != null ? " | Paid by: " + payer.getFullName() : "")
            + (paidAt.toLocalDate().equals(today) ? "" : " | paid on " + paidAt.toLocalDate())
            + " | Amount owed after: UGX " + balanceAfter);
        return record;
    }

    // fix165: A PAYMENT CAN NEVER EXIST WITHOUT ITS RECEIPT. The receipt is checked first, the payment is recorded,
    // then the receipt is filed under Payment Receipts -- all in ONE transaction. If the receipt cannot be filed
    // (storage down, bad file) the payment is rolled back too, so there is never a payment with no receipt.
    // fix167: the payment line remembers its receipt document, so the page can open it from Payment History.
    @Transactional(rollbackFor = Exception.class)
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPaymentWithReceipt(UUID projectId, BigDecimal amount, String notes, MultipartFile receipt,
                                         UUID payerId, String allocation) throws Exception {
        recordPaymentWithReceipt(projectId, amount, notes, receipt, payerId, allocation, null, null);
    }

    @Transactional(rollbackFor = Exception.class)
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPaymentWithReceipt(UUID projectId, BigDecimal amount, String notes, MultipartFile receipt,
                                         UUID payerId, String allocation, String clientRequestId,
                                         java.time.LocalDate paidOnDate) throws Exception {
        if (receipt == null || receipt.isEmpty()) {
            throw new BusinessException("RECEIPT_REQUIRED: A payment cannot be saved without its receipt. Attach the receipt scan (PDF, JPG, PNG or WEBP).");
        }
        if (receipt.getSize() > 10L * 1024L * 1024L) {
            throw new BusinessException("RECEIPT_TOO_LARGE: The receipt must be under 10 MB.");
        }
        requireScanFiles(new MultipartFile[] { receipt });
        PaymentRecord record = recordPayment(projectId, amount, notes, payerId, allocation, clientRequestId, paidOnDate);
        List<ProjectDocument> filed = addScansToProject(projectId, new MultipartFile[] { receipt }, "PAYMENT_RECEIPT", null);
        if (!filed.isEmpty()) {
            record.setReceiptDocumentId(filed.get(0).getId());
            paymentRecordRepository.save(record);
        }
    }

    // fix165: only real scans (PDF / JPG / PNG / WEBP), never an empty file, can be filed into a folder.
    public void requireScanFiles(MultipartFile[] scans) {
        if (scans == null || scans.length == 0) {
            throw new BusinessException("FILE_REQUIRED: Choose at least one file.");
        }
        for (MultipartFile f : scans) {
            if (f == null || f.isEmpty()) {
                throw new BusinessException("FILE_EMPTY: One of the files is empty (0 bytes). Scan or photograph it again.");
            }
            String name = f.getOriginalFilename() == null ? "" : f.getOriginalFilename().toLowerCase();
            int dot = name.lastIndexOf('.');
            String ext = dot >= 0 ? name.substring(dot + 1) : "";
            if (!Set.of("pdf", "jpg", "jpeg", "png", "webp").contains(ext)) {
                throw new BusinessException("FILE_TYPE_BLOCKED: \"" + f.getOriginalFilename() + "\" is not allowed. Use PDF, JPG, PNG or WEBP.");
            }
        }
    }

    // fix167: moveToReceivable / exitReceivable are gone (their endpoints skipped every rule).
    // Receivable moves live in FolderPortalController (enter / exit / reduce-fees / settings).

    // ─── INTAKE ───────────────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public String previewNextIndex() {
        return projectIndexService.previewNextIndex();
    }


    // FIX (combined): this method was missing @Transactional, so its
    // individual saves (client, project, payment, statuses, notes) each
    // committed on their own. A failure partway -- like the sample seed --
    // left an orphaned Client row that re-poisoned every later restart.
    // Now the whole intake is one all-or-nothing unit, same as every
    // other write method in this class.
    @Transactional(rollbackFor = Exception.class)
    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {
        return atomicIntake(request, scans, null);
    }

    // fix174: the Intake page sends a document type (category code) for every file, same order as the files.
    // A file without a type is refused here because the server must not trust the page. A type that does not exist is refused
    // inside addScansToProject, which rolls the whole intake back.
    @Transactional(rollbackFor = Exception.class)
    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans, List<String> categories) throws Exception {
        if (categories != null && scans != null) {
            for (int i = 0; i < scans.length; i++) {
                String c = i < categories.size() ? categories.get(i) : null;
                if (c == null || c.isBlank()) {
                    throw new BusinessException("DOCUMENT_TYPE_MISSING: Pick a document type for every file (" + scans[i].getOriginalFilename() + ").");
                }
            }
        }
        // fix180: the PROJECT TYPE decides everything below. Title Details are kept for Subdivision, Legacy Titles,
        // Transfer of Title, Boundary Opening and Resurvey; for Topographic Survey only when staff switched them on;
        // never for Fresh Survey and Special Projects. An old page that sends no type is read from isLegacy.
        ProjectType type = ProjectType.from(request.getProjectType());
        if (type == null) {
            if (request.getProjectType() != null && !request.getProjectType().isBlank()) {
                throw new BusinessException("PROJECT_TYPE_INVALID: \"" + request.getProjectType() + "\" is not a project type.");
            }
            type = request.isLegacy() ? ProjectType.LEGACY_TITLES : ProjectType.FRESH_SURVEY;
        }
        boolean isLegacyType = type == ProjectType.LEGACY_TITLES;
        boolean titleSwitchedOn = type == ProjectType.TOPOGRAPHIC_SURVEY && request.isTitleDetailsEnabled();
        boolean hasTitleFields = type.showsTitle(titleSwitchedOn);

        // fix180: SUBDIVISION = how many plots it creates. TRANSFER FROM A SUBDIVISION PLOT = checked against the parent.
        Integer subdivisionCount = null;
        if (type == ProjectType.SUBDIVISION) {
            subdivisionCount = request.getSubdivisionCount();
            if (subdivisionCount == null || subdivisionCount < 1 || subdivisionCount > 1000) {
                throw new BusinessException("SUBDIVISIONS_REQUIRED: Enter how many subdivisions (plots) are being created (1 to 1000).");
            }
        }
        LandProject parent = null;
        if (request.getParentProjectId() != null) {
            parent = requireTransferableSubdivisionPlot(request.getParentProjectId(), request.getParentSubdivisionNo(), type);
        }
        String projectIndex = projectIndexService.generateNextIndex();

        BigDecimal initialPayment = request.getInitialPayment() != null
                ? request.getInitialPayment() : BigDecimal.ZERO;
        BigDecimal totalCost = request.getTotalCost() != null
                ? request.getTotalCost() : BigDecimal.ZERO;
        BigDecimal outstanding = totalCost.subtract(initialPayment);

        boolean startAsReceivable = request.isStartAsReceivable();

        // fix171: storage fees already charged / already paid at intake, checked here because the server must not trust the page
        BigDecimal initialFees = request.getInitialStorageFee() != null ? request.getInitialStorageFee() : BigDecimal.ZERO;
        BigDecimal initialFeesPaid = request.getInitialStorageFeePaid() != null ? request.getInitialStorageFeePaid() : BigDecimal.ZERO;
        if (initialPayment.signum() < 0 || initialFees.signum() < 0 || initialFeesPaid.signum() < 0) {
            throw new com.gesolutions.erp.common.exception.BusinessException("AMOUNT_INVALID: Payments and storage fees cannot be negative.");
        }
        if (initialPayment.compareTo(totalCost) > 0) {
            throw new com.gesolutions.erp.common.exception.BusinessException("INITIAL_PAYMENT_TOO_HIGH: The initial payment (UGX " + initialPayment.toPlainString()
                    + ") is more than the total cost (UGX " + totalCost.toPlainString() + ").");
        }
        if (initialFeesPaid.stripTrailingZeros().scale() > 0) {
            throw new com.gesolutions.erp.common.exception.BusinessException("STORAGE_PAID_INVALID: Enter whole shillings only for the storage fees already paid.");
        }
        // fix172: "in receivables since". The months that went by before today are billed NOW (counted the same way the nightly
        // fee job counts them: whole 30-day periods) and the billing clock starts at that date, so nothing is billed twice.
        LocalDate receivablesSince = request.getReceivablesSince();
        BigDecimal feeRate = (request.getMonthlyStorageFee() != null && request.getMonthlyStorageFee().signum() > 0)
                ? request.getMonthlyStorageFee() : LandProject.DEFAULT_MONTHLY_STORAGE_FEE;   // fix173: one shared default
        int backlogMonths = 0;
        LocalDateTime receivableClock = LocalDateTime.now();
        if (receivablesSince != null) {
            if (!(startAsReceivable && outstanding.signum() > 0)) {
                throw new com.gesolutions.erp.common.exception.BusinessException("SINCE_NOT_APPLICABLE: An In Receivables Since date only applies to a project that goes into receivables. "
                        + "This title work is already fully paid, so clear the date.");
            }
            if (receivablesSince.isAfter(LocalDate.now().plusDays(1))) {
                throw new com.gesolutions.erp.common.exception.BusinessException("SINCE_IN_FUTURE: The In Receivables Since date cannot be in the future.");
            }
            long daysGone = Math.max(0L, java.time.temporal.ChronoUnit.DAYS.between(receivablesSince, LocalDate.now()));
            if (daysGone > 10950L) {
                throw new com.gesolutions.erp.common.exception.BusinessException("SINCE_TOO_OLD: The In Receivables Since date is more than 30 years ago. Check the year.");
            }
            backlogMonths = (int) (daysGone / 30L);
            receivableClock = receivablesSince.atStartOfDay();
        }
        BigDecimal backlogFees = feeRate.multiply(BigDecimal.valueOf(backlogMonths));
        if (initialFeesPaid.compareTo(initialFees.add(backlogFees)) > 0) {
            throw new com.gesolutions.erp.common.exception.BusinessException("STORAGE_PAID_TOO_HIGH: Storage fees already paid (UGX " + initialFeesPaid.toPlainString()
                    + ") cannot be more than the fees charged (UGX " + initialFees.add(backlogFees).toPlainString() + ": initial storage fee UGX "
                    + initialFees.toPlainString() + " plus UGX " + backlogFees.toPlainString() + " backlog).");
        }

        // fix172: optional "date last paid" for the money entered as already paid. Empty keeps the old behaviour (paid today).
        LocalDate lastPaidDate = request.getLastPaidDate();
        LocalDateTime paidAt = null;
        if (lastPaidDate != null) {
            if (lastPaidDate.isAfter(LocalDate.now().plusDays(1))) {
                throw new com.gesolutions.erp.common.exception.BusinessException("DATE_PAID_IN_FUTURE: The date last paid cannot be in the future.");
            }
            if (initialPayment.signum() == 0 && initialFeesPaid.signum() == 0) {
                throw new com.gesolutions.erp.common.exception.BusinessException("DATE_PAID_NO_PAYMENT: A date last paid needs a payment amount. Enter the payment, or clear the date.");
            }
            paidAt = lastPaidDate.isBefore(LocalDate.now()) ? lastPaidDate.atTime(12, 0) : LocalDateTime.now();
        }
        if (!(startAsReceivable && outstanding.signum() > 0) && (initialFees.signum() > 0 || initialFeesPaid.signum() > 0)) {
            throw new com.gesolutions.erp.common.exception.BusinessException("STORAGE_NOT_APPLICABLE: Storage fees only exist on a project in receivables. "
                    + "This title work is already fully paid, so clear the storage fee boxes.");
        }

        LandTitle title = null;
        if (hasTitleFields) {
            // Title Details are fully required on the page once shown -- mirrored here, since this service validates
            // DTOs imperatively rather than via @Valid/bean-validation. fix180: Area (hectares) is required too.
            if (request.getPlotNumber() == null || request.getPlotNumber().isBlank()) {
                throw new BusinessException("PLOT_NUMBER_REQUIRED: Plot Number is required in Title Details.");
            }
            if (request.getBlock() == null || request.getBlock().isBlank()) {
                throw new BusinessException("BLOCK_REQUIRED: Block is required in Title Details.");
            }
            requireAreaHectares(request.getAreaHectares());
            if (request.getTitleIssueDate() == null) {
                throw new BusinessException("TITLE_DATE_REQUIRED: Title Date is required in Title Details.");
            }
            title = LandTitle.builder()
                    .tenure(request.getTenure() != null && !request.getTenure().isBlank() ? request.getTenure() : "FREEHOLD")
                    .plotNumber(request.getPlotNumber())
                    .block(request.getBlock())
                    .areaHectares(request.getAreaHectares())
                    .volume(blankToNull(request.getVolume()))
                    .folio(blankToNull(request.getFolio()))
                    // Date Started is editable again on the intake form (staff can
                    // backdate a project entered a few days after fieldwork began),
                    // so this trusts the client value when present and only falls
                    // back to today when it's missing. Entry Date (LandProject,
                    // below) is the one that stays server-set and non-editable.
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
        }

        LandProject.LandProjectBuilder builder = LandProject.builder()
                .landTitle(title)
                .projectIndex(projectIndex)
                // ENTRY DATE: automatic, server-set, never from the request.
                .entryDate(LocalDate.now())
                // DATE STARTED: editable on the intake form, defaults to today
                // on the client -- this was previously never wired up here at
                // all, so every project's start date landed NULL regardless of
                // what the form showed.
                .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())
                .district(request.getDistrict())
                .county(request.getCounty())
                .subCounty(request.getSubCounty())
                .parish(request.getParish())
                .village(request.getVillage())
                .area(request.getArea())
                .totalCost(totalCost)
                .amountPaid(initialPayment.add(initialFeesPaid))   // fix171: title money + storage-fee money (fees paid is 0 unless receivable)
                .projectType(type.name())                          // fix180
                .titleDetailsEnabled(titleSwitchedOn)
                .subdivisionCount(subdivisionCount)
                .parentProjectId(parent != null ? parent.getId() : null)
                .parentSubdivisionNo(parent != null ? request.getParentSubdivisionNo() : null)
                .isLegacy(isLegacyType)
                .currentStatusIndex(startAsReceivable ? 5 : 1)
                .status(startAsReceivable ? "RECEIVABLE" : "ACTIVE");

        if (startAsReceivable && outstanding.compareTo(BigDecimal.ZERO) > 0) {
            builder.isReceivable(true)
                   .receivableStartDate(receivableClock)   // fix172: the In Receivables Since date, or now
                   .receivableMonthsBilled(backlogMonths)   // fix172: those months are billed below, so the nightly job must not bill them again
                   .originalDebt(outstanding)
                   .storageFeesAccumulated(initialFees.add(backlogFees))   // fix172: typed fee + the backlog months
                   .storageFeesPaid(initialFeesPaid);   // fix171
            if (request.getMonthlyStorageFee() != null
                    && request.getMonthlyStorageFee().compareTo(BigDecimal.ZERO) > 0) {
                builder.storageFeeOverride(request.getMonthlyStorageFee());
            }
        }

        LandProject project = builder.build();

        // fix180: CLIENTS first (they pay, Recovery calls them), then OWNERS (the people on the title). Owners left empty
        // are a copy of the clients; an old page that sends only owners has those owners as its clients.
        List<LandEntryRequest.OwnerRequest> clientRows = request.getClients() != null && !request.getClients().isEmpty()
                ? request.getClients() : (request.getOwners() != null ? request.getOwners() : List.of());
        List<LandEntryRequest.OwnerRequest> ownerRows = request.getOwners() != null && !request.getOwners().isEmpty()
                ? request.getOwners() : clientRows;
        if (clientRows.isEmpty()) {
            throw new BusinessException("CLIENT_REQUIRED: Add at least one client.");
        }
        // fix172: the clients by NIN, so the client who paid the intake money can be named
        java.util.Map<String, Client> ownersByNin = new java.util.LinkedHashMap<>();
        for (LandEntryRequest.OwnerRequest o : clientRows) {
            Client c = personFromRow(o, "Client");
            project.addClient(c);
            ownersByNin.put(o.getNationalId().trim().toUpperCase(), c);   // fix172
        }
        for (LandEntryRequest.OwnerRequest o : ownerRows) {
            project.addProprietor(personFromRow(o, "Owner"));
        }

        // fix172: WHO paid the money entered at intake. Same rule as a normal payment: a single client is the payer,
        // joint clients must say which one paid. Checked before anything is saved.
        Client titlePayer = fix172ResolvePayer(ownersByNin, request.getInitialPaymentPayerNin(), initialPayment, "initial payment");
        Client feesPayer = fix172ResolvePayer(ownersByNin, request.getInitialStorageFeePaidPayerNin(), initialFeesPaid, "storage fees already paid");
        StringBuilder fix172Note = new StringBuilder();
        if (titlePayer != null) fix172Note.append(" | Initial payment paid by ").append(titlePayer.getFullName());
        if (feesPayer != null) fix172Note.append(" | Storage fees paid by ").append(feesPayer.getFullName());
        if (lastPaidDate != null) fix172Note.append(" | Date last paid ").append(lastPaidDate);
        if (receivablesSince != null) fix172Note.append(" | In receivables since ").append(receivablesSince)
                .append(" (").append(backlogMonths).append(" month(s) of fees billed at intake)");

        LandProject saved = projectRepository.save(project);

        // Record initial payment if any
        // fix171: the balance shown on the history lines includes the storage fees, and the money that was paid
        // toward fees gets its OWN line (allocation STORAGE) so the folder, payments page and reports can tell them apart.
        BigDecimal balanceAtIntake = saved.isReceivable() ? saved.receivableTotalOwed() : outstanding;
        if (initialPayment.compareTo(BigDecimal.ZERO) > 0) {
            PaymentRecord initialRecord = PaymentRecord.builder()
                    .projectId(saved.getId())
                    .amountPaid(initialPayment)
                    .paymentType("INITIAL_DEPOSIT")
                    .recordedBy(getCurrentOperator())
                    .notes(paidAt != null ? "Initial deposit at intake (paid on " + lastPaidDate + ")" : "Initial deposit at intake")
                    .balanceAfter(balanceAtIntake)
                    .allocation("TITLE")
                    .payerClientId(titlePayer != null ? titlePayer.getId() : null)   // fix172: which owner paid
                    .payerName(titlePayer != null ? titlePayer.getFullName() : null)
                    .timestamp(LocalDateTime.now())   // fix181 (16.0b): always the real entry time
                    .paidOn(paidAt)                   // fix181 (11.6): the day paid; NULL when the operator gave no date
                    .build();
            paymentRecordRepository.save(initialRecord);
            saved.setLastPaymentDate(paidAt != null ? paidAt : LocalDateTime.now());   // fix172: not always today any more
            projectRepository.save(saved);
        }
        if (initialFeesPaid.compareTo(BigDecimal.ZERO) > 0) {
            // deliberately NOT setting lastPaymentDate: this money was paid before the project was entered, on an
            // unknown date, so it must not turn the recovery badge green or lock the client from calls for 30 days.
            PaymentRecord feesRecord = PaymentRecord.builder()
                    .projectId(saved.getId())
                    .amountPaid(initialFeesPaid)
                    .paymentType("INITIAL_DEPOSIT")
                    .recordedBy(getCurrentOperator())
                    .notes(paidAt != null ? "Storage fees already paid before entry (paid on " + lastPaidDate + ")" : "Storage fees already paid before entry (recorded at intake)")
                    .balanceAfter(balanceAtIntake)
                    .allocation("STORAGE")
                    .payerClientId(feesPayer != null ? feesPayer.getId() : null)   // fix172: which owner paid
                    .payerName(feesPayer != null ? feesPayer.getFullName() : null)
                    .timestamp(LocalDateTime.now())   // fix181 (16.0b)
                    .paidOn(paidAt)
                    .build();
            paymentRecordRepository.save(feesRecord);
            if (paidAt != null) {
                // fix172: only when the operator gave a date. No date = still unknown = the recovery badge stays untouched.
                saved.setLastPaymentDate(paidAt);
                projectRepository.save(saved);
            }
        }

        // fix180: every project type has its own status list, so every project gets its statuses
        if (request.getSelectedStatuses() != null && !request.getSelectedStatuses().isEmpty()) {
            statusTemplateService.attachStatusesToProject(saved.getId(), request.getSelectedStatuses());
        }
        saveNeighbors(saved.getId(), request.getNeighbors());   // fix180

        if (scans != null) addScansToProject(saved.getId(), scans, null, categories);   // fix174: file each document under its type

        if (request.getNotes() != null) {
            for (LandEntryRequest.NoteRequest noteReq : request.getNotes()) {
                if (noteReq.getContent() != null && !noteReq.getContent().trim().isEmpty()) {
                    FollowUpLog entry = FollowUpLog.builder()
                            .projectId(saved.getId())
                            .notes("INTAKE NOTE: " + noteReq.getContent())
                            .recordedBy(getCurrentOperator())
                            .build();
                    followUpRepository.save(entry);
                }
            }
        }

        String plotOrIndex = title != null ? title.getPlotNumber() : "project #" + projectIndex;
        String receivableNote = (startAsReceivable ? " [ENTERED AS RECEIVABLE]" : "") + " [" + type.getLabel() + "]"
                + (parent != null ? " [TRANSFER OF SUBDIVISION PLOT " + request.getParentSubdivisionNo() + " OF PROJECT #" + parent.getProjectIndex() + "]" : "");
        notificationService.emitToAudience("NEW_INTAKE", "New project " + projectIndex + " registered by " + getCurrentOperator() + ".", "PROJECT", saved.getId());
        auditService.logActionAfterCommit("INTAKE",
            "Operator [" + getCurrentOperator() + "] ingested binder: "
            + plotOrIndex + receivableNote + fix172Note);

        if (startAsReceivable) {
            auditService.logActionAfterCommit("RECEIVABLE_TRIGGER",
                "Operator [" + getCurrentOperator() + "] flagged plot "
                + plotOrIndex + " as RECEIVABLE at intake. Title debt: UGX " + outstanding
                + ". Storage fees: UGX " + initialFees.add(backlogFees)
                + (backlogMonths > 0 ? " (incl. UGX " + backlogFees + " backlog for " + backlogMonths + " month(s) since " + receivablesSince + ")" : "")
                + " (UGX " + initialFeesPaid + " already paid).");
        }

        return saved;
    }

    // ─── FULL UPDATE ──────────────────────────────────────────────────────────

    // fix180: one Client / Owner row from the form -> the person (by NIN, the identity rule)
    private Client personFromRow(LandEntryRequest.OwnerRequest o, String what) {
        if (o.getNationalId() == null || o.getNationalId().isBlank()) {
            throw new BusinessException("NIN_REQUIRED: " + what + " \"" + o.getFullName() + "\" is missing a National ID (NIN).");
        }
        Client c = clientService.findOrCreateClientByNin(o.getFullName(), o.getNationalId(), o.getPhone(), o.getEmail());
        if (o.getAddress() != null && !o.getAddress().isBlank()) c.setHomeAddress(o.getAddress());
        return c;
    }

    private static String blankToNull(String v) {
        return v == null || v.isBlank() ? null : v.trim();
    }

    // fix180: Area (hectares) is required whenever Title Details are saved
    private static void requireAreaHectares(BigDecimal ha) {
        if (ha == null || ha.signum() <= 0) {
            throw new BusinessException("AREA_REQUIRED: Area (hectares) is required in Title Details and must be more than 0.");
        }
    }

    // fix180: NEIGHBORS -- the whole list is replaced by what the page sends (blank names are skipped)
    private void saveNeighbors(UUID projectId, List<LandEntryRequest.NeighborRequest> rows) {
        if (rows == null) return;
        neighborRepository.deleteAll(neighborRepository.findByProjectIdOrderByDisplayOrderAsc(projectId));
        neighborRepository.flush();
        int order = 0;
        for (LandEntryRequest.NeighborRequest r : rows) {
            if (r == null || r.getFullName() == null || r.getFullName().isBlank()) continue;
            String phone = r.getPhone() == null || r.getPhone().isBlank() ? null
                    : com.gesolutions.erp.common.util.PhoneUtil.normalizeList(r.getPhone());
            neighborRepository.save(ProjectNeighbor.builder().projectId(projectId)
                    .fullName(r.getFullName().trim()).phone(phone).side(blankToNull(r.getSide()))
                    .plotNumber(blankToNull(r.getPlotNumber())).notes(blankToNull(r.getNotes()))
                    .displayOrder(order++).build());
        }
    }

    // fix180: a Transfer of Title made from a subdivision plot. The parent must be a live Subdivision project, the plot
    // number one of its plots, and that plot not transferred already.
    private LandProject requireTransferableSubdivisionPlot(UUID parentId, Integer plotNo, ProjectType type) {
        if (type != ProjectType.TRANSFER_OF_TITLE) {
            throw new BusinessException("TRANSFER_TYPE_REQUIRED: A subdivision plot is transferred with a Transfer of Title project.");
        }
        LandProject parent = projectRepository.findById(parentId)
                .orElseThrow(() -> new BusinessException("SUBDIVISION_NOT_FOUND: The subdivision project no longer exists."));
        if (parent.isDeleted()) {
            throw new BusinessException("SUBDIVISION_DELETED: The subdivision project is deleted. Restore it first.");
        }
        if (ProjectType.of(parent) != ProjectType.SUBDIVISION) {
            throw new BusinessException("NOT_A_SUBDIVISION: Project #" + parent.getProjectIndex() + " is not a Subdivision project.");
        }
        int count = parent.getSubdivisionCount() != null ? parent.getSubdivisionCount() : 0;
        if (plotNo == null || plotNo < 1 || plotNo > count) {
            throw new BusinessException("SUBDIVISION_PLOT_INVALID: Pick a plot from 1 to " + count + " of project #" + parent.getProjectIndex() + ".");
        }
        for (LandProject t : projectRepository.findTransfersOf(parentId)) {
            if (plotNo.equals(t.getParentSubdivisionNo())) {
                throw new BusinessException("ALREADY_TRANSFERRED: Plot " + plotNo + " of project #" + parent.getProjectIndex()
                        + " was already transferred (project #" + t.getProjectIndex() + ").");
            }
        }
        return parent;
    }

    // fix172: finds the client who paid money entered at intake. One client = that client. Joint clients = the payer must be
    // named, and must be one of the clients typed on the form. No money entered = no payer needed.
    private Client fix172ResolvePayer(java.util.Map<String, Client> ownersByNin, String payerNin, BigDecimal amount, String what) {
        if (amount == null || amount.signum() <= 0) return null;
        String key = payerNin == null ? "" : payerNin.trim().toUpperCase();
        if (!key.isEmpty()) {
            Client hit = ownersByNin.get(key);
            if (hit == null) {
                throw new BusinessException("PAYER_INVALID: The client who paid the " + what + " must be one of the clients on this form.");
            }
            return hit;
        }
        if (ownersByNin.size() == 1) return ownersByNin.values().iterator().next();
        if (ownersByNin.size() > 1) {
            throw new BusinessException("PAYER_REQUIRED: This project has " + ownersByNin.size() + " clients. Pick which client paid the " + what + ".");
        }
        return null;
    }

    // fix166: one-line descriptions of the title and the owners, used to write OLD -> NEW into the audit log.
    private String fix166TitleLine(LandTitle t) {
        if (t == null) return "no title";
        return "plot " + t.getPlotNumber() + ", block " + t.getBlock() + ", area " + (t.getAreaHectares() == null ? "-" : t.getAreaHectares().stripTrailingZeros().toPlainString()) + " ha"
                + ", volume " + t.getVolume() + ", folio " + t.getFolio() + ", tenure " + t.getTenure();
    }

    private String fix166OwnersLine(LandProject p) {
        return peopleLine(p.getProprietors());
    }

    // fix180: same one-line form for the clients
    private String peopleLine(Set<Client> people) {
        if (people == null || people.isEmpty()) return "none";
        return people.stream()
                .map(c -> c.getFullName() + " (NIN " + c.getNationalId() + ")")
                .sorted()
                .collect(java.util.stream.Collectors.joining("; "));
    }

    @Transactional(rollbackFor = Exception.class)
    public LandProject updateProjectFull(UUID projectId, LandEntryRequest request) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("ARCHIVE_FAULT"));
        LandTitle title = project.getLandTitle();

        // fix166 EDIT GUARDS (the page checks these too, but the server must not trust the page):
        // a deleted project and a handed-over title cannot be edited; district, plot and tenure cannot be blanked;
        // a project cannot lose all its owners.
        if (project.isDeleted()) {
            throw new BusinessException("EDIT_BLOCKED: This project is deleted. Restore it first.");
        }
        if (title != null && title.isReleased()) {
            throw new BusinessException("EDIT_LOCKED: The title has been handed over, so this record is locked. A director must UNDO the hand-over (with a reason) before anything can be changed.");
        }
        if (request.getDistrict() == null || request.getDistrict().isBlank()) {
            throw new BusinessException("DISTRICT_REQUIRED: The district cannot be empty.");
        }
        if (title != null && (request.getPlotNumber() == null || request.getPlotNumber().isBlank())) {
            throw new BusinessException("PLOT_REQUIRED: A titled project must keep its plot number.");
        }
        if (title != null && (request.getTenure() == null || request.getTenure().isBlank())) {
            throw new BusinessException("TENURE_REQUIRED: A titled project must keep its tenure.");
        }
        if (request.getOwners() != null && request.getOwners().isEmpty()
                && project.getProprietors() != null && !project.getProprietors().isEmpty()) {
            throw new BusinessException("OWNER_REQUIRED: A project must keep at least one owner.");
        }
        if (request.getClients() != null && request.getClients().isEmpty()
                && project.getClients() != null && !project.getClients().isEmpty()) {
            throw new BusinessException("CLIENT_REQUIRED: A project must keep at least one client.");
        }
        final String fix166OldTitle = fix166TitleLine(title);
        final String fix166OldOwners = fix166OwnersLine(project);
        final String fix180OldClients = peopleLine(project.getClients());

        // fix180: Title Details follow the project type. Topographic Survey can switch them on (or off while none are
        // saved); Fresh Survey / Special Projects never get a new title. A title that already exists is always kept.
        ProjectType type = ProjectType.of(project);
        if (type == ProjectType.TOPOGRAPHIC_SURVEY) {
            project.setTitleDetailsEnabled(request.isTitleDetailsEnabled() || title != null);
        }
        boolean titleAllowed = title != null || type.showsTitle(project.isTitleDetailsEnabled());
        boolean hasTitleFields = titleAllowed && request.getPlotNumber() != null && !request.getPlotNumber().isBlank();
        if (title == null && hasTitleFields) {
            // fix167: a title saved from the folder page needs the same details as one typed on New Project
            if (request.getBlock() == null || request.getBlock().isBlank()) {
                throw new BusinessException("BLOCK_REQUIRED: Type the Block before saving the title.");
            }
            requireAreaHectares(request.getAreaHectares());
            title = LandTitle.builder()
                    .tenure(request.getTenure() != null && !request.getTenure().isBlank() ? request.getTenure() : "FREEHOLD")
                    .plotNumber(request.getPlotNumber())
                    .block(request.getBlock())
                    .areaHectares(request.getAreaHectares())
                    .volume(blankToNull(request.getVolume()))
                    .folio(blankToNull(request.getFolio()))
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : java.time.LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
            project.setLandTitle(title);
        } else if (title != null) {
            requireAreaHectares(request.getAreaHectares());
            title.setPlotNumber(request.getPlotNumber());
            title.setTenure(request.getTenure());
            title.setBlock(request.getBlock());
            title.setAreaHectares(request.getAreaHectares());
            title.setVolume(blankToNull(request.getVolume()));
            title.setFolio(blankToNull(request.getFolio()));
            if (request.getTitleIssueDate() != null) title.setTitleIssueDate(request.getTitleIssueDate());
        }

        // fix180: a Subdivision can change its number of plots, but never below a plot that was already transferred
        if (type == ProjectType.SUBDIVISION && request.getSubdivisionCount() != null) {
            int want = request.getSubdivisionCount();
            int highest = 0;
            for (LandProject t : projectRepository.findTransfersOf(projectId)) {
                if (t.getParentSubdivisionNo() != null) highest = Math.max(highest, t.getParentSubdivisionNo());
            }
            if (want < 1 || want > 1000) {
                throw new BusinessException("SUBDIVISIONS_REQUIRED: The number of subdivisions must be from 1 to 1000.");
            }
            if (want < highest) {
                throw new BusinessException("SUBDIVISIONS_TOO_FEW: Plot " + highest + " was already transferred, so there must be at least " + highest + " subdivisions.");
            }
            if (!Integer.valueOf(want).equals(project.getSubdivisionCount())) {
                auditService.logActionAfterCommit("SUBDIVISIONS_CHANGED", "Operator [" + getCurrentOperator() + "] changed the number of subdivisions of project #"
                        + project.getProjectIndex() + " from " + project.getSubdivisionCount() + " to " + want);
            }
            project.setSubdivisionCount(want);
        }

        // Save location fields on LandProject (Phase A/E)
        project.setDistrict(request.getDistrict());
        project.setCounty(request.getCounty());
        project.setSubCounty(request.getSubCounty());
        project.setParish(request.getParish());
        project.setVillage(request.getVillage());
        project.setArea(request.getArea());

        if (request.getOwners() != null) {
            Set<Client> updatedRegistry = new HashSet<>();
            for (LandEntryRequest.OwnerRequest incoming : request.getOwners()) {
                if (incoming.getNationalId() == null || incoming.getNationalId().isBlank()) {
                    throw new BusinessException("NIN_REQUIRED: Owner \"" + incoming.getFullName() + "\" is missing a National ID (NIN).");
                }
                // STAGE 8 FIX: this used to look the client up directly by NIN and,
                // when found, unconditionally overwrite its stored fullName with
                // whatever was typed on this form -- bypassing the NIN_NAME_MISMATCH
                // guard entirely, because that guard only ran inside
                // findOrCreateClientByNin(), which this code only called on the
                // NOT-FOUND branch (orElseGet). Reusing an existing NIN with a
                // different typed name silently renamed that person's identity
                // record everywhere they appear. Routing every owner through
                // findOrCreateClientByNin() unconditionally -- same as atomicIntake
                // does on Intake -- restores the mismatch check on Edit, and, like
                // Intake, leaves fullName untouched for a matching existing person
                // (full name is identity-level, not a per-project field; it only
                // changes via the explicit mismatch-confirmation flow).
                Client person = clientService.findOrCreateClientByNin(
                        incoming.getFullName(), incoming.getNationalId(), incoming.getPhone(), incoming.getEmail());
                person.setEmail(incoming.getEmail() != null
                        ? incoming.getEmail().toLowerCase() : null);
                person.setHomeAddress(incoming.getAddress());
                if (incoming.getPhone() != null && !incoming.getPhone().isBlank()) {
                    person.setPhoneNumber(com.gesolutions.erp.common.util.PhoneUtil.normalizeList(incoming.getPhone()));
                }
                clientRepository.save(person);
                updatedRegistry.add(person);
            }
            project.setProprietors(updatedRegistry);
        }

        // fix180: CLIENTS are edited the same way as the owners (NIN rules included)
        if (request.getClients() != null && !request.getClients().isEmpty()) {
            Set<Client> updatedClients = new HashSet<>();
            for (LandEntryRequest.OwnerRequest incoming : request.getClients()) {
                Client person = personFromRow(incoming, "Client");
                person.setEmail(incoming.getEmail() != null ? incoming.getEmail().toLowerCase() : null);
                if (incoming.getPhone() != null && !incoming.getPhone().isBlank()) {
                    person.setPhoneNumber(com.gesolutions.erp.common.util.PhoneUtil.normalizeList(incoming.getPhone()));
                }
                clientRepository.save(person);
                updatedClients.add(person);
            }
            project.setClients(updatedClients);
        }
        saveNeighbors(projectId, request.getNeighbors());   // fix180

        BigDecimal newTotalCost = request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO;
        BigDecimal oldTotalCost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal currentPaid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;

        // fix162 EDIT CONFLICT: the form remembers the cost it was loaded with. If somebody else changed the
        // cost in the meantime, refuse instead of silently overwriting their change.
        if (request.getExpectedTotalCost() != null && request.getExpectedTotalCost().compareTo(oldTotalCost) != 0) {
            throw new BusinessException("EDIT_CONFLICT: The total cost was changed by someone else (it is now UGX "
                    + oldTotalCost.toPlainString() + "). Reload this folder and try again.");
        }
        // fix162 COST CHANGE: needs a written reason, cannot go below what is already paid, and is audited.
        if (newTotalCost.compareTo(oldTotalCost) != 0) {
            String costWhy = request.getCostChangeReason() != null ? request.getCostChangeReason().trim() : "";
            if (costWhy.length() < 5) {
                throw new BusinessException("COST_REASON_REQUIRED: Write why the total cost is changing (at least 5 characters).");
            }
            // fix171: only the money paid toward the TITLE work counts here (paid storage fees are not part of the cost)
            BigDecimal titlePaidNow = currentPaid.subtract(project.storagePaidSafe()).max(BigDecimal.ZERO);
            if (newTotalCost.compareTo(titlePaidNow) < 0) {
                throw new BusinessException("COST_BELOW_PAID: The new cost (UGX " + newTotalCost.toPlainString()
                        + ") is lower than the UGX " + titlePaidNow.toPlainString()
                        + " already paid. Reverse the extra payment first.");
            }
            auditService.logActionAfterCommit("COST_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed total cost on " + plotLabel(project)
                + " from UGX " + oldTotalCost.toPlainString() + " to UGX " + newTotalCost.toPlainString()
                + ". Reason: " + costWhy);
        }
        project.setTotalCost(newTotalCost);
        // fix162 AMOUNT PAID is never taken from the edit form. It only moves through RECORD PAYMENT and REVERSE.
        // fix167: the entry mode (Legacy Title) is permanent. EDIT used to overwrite it with what the page sent,
        // and the page never received the flag, so every save wiped it.

        // FIX 1: If in receivable, keep originalDebt in sync with totalCost changes.
        // originalDebt = new title cost minus payments already made toward the title.
        if (project.isReceivable()) {
            BigDecimal amtPaid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
            project.setOriginalDebt(newTotalCost.subtract(amtPaid.subtract(project.storagePaidSafe())).max(BigDecimal.ZERO));   // fix171: title money only
        }

        LandProject saved = projectRepository.save(project);
        auditService.logActionAfterCommit("RECORD_UPDATED",
            "Operator [" + getCurrentOperator() + "] modified Binder: "
            + plotLabel(project));
        // fix166: a change of plot / title ID / tenure / block, or of the owners, is written with OLD -> NEW.
        String fix166NewTitle = fix166TitleLine(project.getLandTitle());
        if (!fix166OldTitle.equals(fix166NewTitle)) {
            auditService.logActionAfterCommit("TITLE_FIELDS_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed the title details of project #" + project.getProjectIndex()
                + ". Old: " + fix166OldTitle + " -> New: " + fix166NewTitle);
        }
        String fix166NewOwners = fix166OwnersLine(project);
        if (!fix166OldOwners.equals(fix166NewOwners)) {
            auditService.logActionAfterCommit("OWNERS_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed the owners of project #" + project.getProjectIndex()
                + ". Old: " + fix166OldOwners + " -> New: " + fix166NewOwners);
        }
        String fix180NewClients = peopleLine(project.getClients());
        if (!fix180OldClients.equals(fix180NewClients)) {
            auditService.logActionAfterCommit("CLIENTS_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed the clients of project #" + project.getProjectIndex()
                + ". Old: " + fix180OldClients + " -> New: " + fix180NewClients);
        }
        return saved;
    }

    // ─── SOFT DELETE (formerly NUCLEAR DELETE) ───────────────────────────────
    // STAGE 3 FIX: this used to hard-delete the Cloudinary files, every payment
    // record, every note, and the DB row itself -- irreversible in one click.
    // It now only flags the row as deleted. Nothing else is touched, so a
    // mis-click is recoverable via restoreProject() below.

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")   // fix181: Admin and Director (the owner)
    public void nuclearDelete(UUID id, String reason) {
        // fix166: deleting a project needs a written reason, and an already-deleted project cannot be "deleted" again.
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why this project is being deleted (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.isDeleted()) {
            throw new BusinessException("ALREADY_DELETED: This project is already deleted.");
        }
        String plotNo = plotLabel(project);

        project.setDeleted(true);
        project.setDeletedAt(LocalDateTime.now());
        project.setDeletedReason(why);                // fix181 (14.7a)
        project.setDeletedBy(getCurrentOperator());
        projectRepository.save(project);

        auditService.logActionAfterCommit("RECORD_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted plot: " + plotNo + ". Reason: " + why);
        /* fix71: CRITICAL was a severity the frontend rendered and the backend
           never emitted. Deleting a plot is exactly what it is for. emitRaw,
           not emit: emit de-duplicates on (type, entityId) forever, so a plot
           deleted, restored and deleted again would have gone silent the
           second time. */
        notificationService.emitToAudience("PROJECT_DELETED",
            "Plot " + plotNo + " deleted by " + getCurrentOperator()
            + ". Restore it from Settings -> Archive.",
            "PROJECT", project.getId());
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")   // fix181: Admin and Director (the owner)
    public void restoreProject(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = plotLabel(project);

        project.setDeleted(false);
        project.setDeletedAt(null);
        project.setDeletedReason(null);
        project.setDeletedBy(null);
        projectRepository.save(project);

        auditService.logActionAfterCommit("RECORD_RESTORED",
            "Operator [" + getCurrentOperator() + "] restored plot: " + plotNo);
        notificationService.emitToAudience("PROJECT_RESTORED",
            "Plot " + plotNo + " restored by " + getCurrentOperator() + ".",
            "PROJECT", project.getId());
    }

    @Transactional(readOnly = true)
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")   // fix181: Admin and Director (the owner)
    public List<LandProject> getDeletedProjects() {
        return projectRepository.findAllDeleted();
    }

    // ─── FOLLOW-UP / NOTES ────────────────────────────────────────────────────

    // STAGE 10 FIX: NIN_JOINT_OWNER_CONTACT_MISATTRIBUTION (design brief 3.3/3.4)
    // Previously this always logged the contact against whichever proprietor's
    // fullName sorted first alphabetically ("primary owner"), regardless of
    // which co-owner staff actually reached -- silently resetting the WRONG
    // person's 14-day cooldown clock while the person really contacted never
    // got their own record updated. It also auto-copied the note onto every
    // OTHER outstanding plot the resolved primary owner held, fabricating
    // contact history on unrelated projects. Both behaviors are removed.
    // The caller must now name the specific owner being logged (this is the
    // "merge log-a-call and add-a-note into one action" from open question
    // 3.4 #1 -- project + specific owner + timestamp + note, in one record).
    // STAGE 11 FIX: SOFT_DUPLICATE_CONTACT_WARNING (design brief 3.4, open
    // question #2 -- explicitly left undecided by Stage 10). Decision:
    //   - SOFT, never blocks: 3.3 already agreed staff must be able to call
    //     different joint owners independently, so a second co-owner call
    //     inside the window is normal and is never prevented.
    //   - 3-day look-back, not the full 14-day cooldown: this flags "we just
    //     called about this plot yesterday", not ordinary independent contact.
    //   - Surfaced on the existing endpoint's response, same pattern Stage 10
    //     used for merging log-a-call/add-a-note into one action.
    @Transactional(rollbackFor = Exception.class)
    public java.util.Map<String, Object> logFollowUp(UUID projectId, UUID ownerId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();

        // fix180: recovery calls are made to the CLIENTS of the project
        boolean ownerIsProprietor = project.billingParties().stream()
                        .anyMatch(o -> o != null && o.getId() != null && o.getId().equals(ownerId));
        if (!ownerIsProprietor) {
            throw new BusinessException(
                    "CLIENT_NOT_ON_PROJECT: The selected person is not a client of this project.");
        }

        // STAGE 11: advisory-only read -- does not touch any co-owner's state.
        String coOwnerWarning = null;
        LocalDateTime recentWindowStart = LocalDateTime.now().minusDays(3);
        java.util.List<FollowUpLog> recentProjectLogs =
                followUpRepository.findByProjectIdOrderByTimestampDesc(projectId);
        for (FollowUpLog log : recentProjectLogs) {
            if (log.getOwnerId() != null
                    && !log.getOwnerId().equals(ownerId)
                    && log.getTimestamp() != null
                    && log.getTimestamp().isAfter(recentWindowStart)) {
                Client coOwner = project.billingParties().stream()
                        .filter(o -> o != null && log.getOwnerId().equals(o.getId()))
                        .findFirst().orElse(null);
                String coOwnerName = coOwner != null ? coOwner.getFullName() : "another owner";
                coOwnerWarning = coOwnerName + " was already contacted about this plot on "
                        + log.getTimestamp().toLocalDate() + ".";
                break;
            }
        }

        // Update ONLY the specific owner who was actually reached. Cooldown
        // state lives on Client (per person), so this cannot touch any
        // co-owner who was not part of this call.
        clientService.logManagerContact(ownerId);

        String operator = getCurrentOperator();
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .ownerId(ownerId)
                .notes(content)
                .recordedBy(operator)
                .build();
        followUpRepository.save(entry);

        auditService.logActionAfterCommit("RECOVERY_SYNC",
            "Operator [" + operator + "] logged call for plot: "
            + plotLabel(project) + " (owner reached: " + ownerId + ")");

        java.util.Map<String, Object> result = new java.util.HashMap<>();
        result.put("ownerId", ownerId);
        result.put("coOwnerWarning", coOwnerWarning);
        return result;
    }

    // fix165: notes. A note on a project that has no title yet used to crash the server (it read the plot number of a
    // title that did not exist), so adding a note or flagging a PROBLEM on a folder failed. Text is now checked and
    // the audit line keeps the old words when a note is edited or deleted.
    private static final int NOTE_MAX_CHARS = 2000;

    private String cleanNoteText(String content) {
        String c = content == null ? "" : content.trim();
        if (c.length() < 2) {
            throw new BusinessException("NOTE_REQUIRED: Write the note first (at least 2 characters).");
        }
        if (c.length() > NOTE_MAX_CHARS) {
            throw new BusinessException("NOTE_TOO_LONG: A note can be at most " + NOTE_MAX_CHARS
                    + " characters (this one is " + c.length() + ").");
        }
        return c;
    }

    private String shortText(String s) {
        if (s == null) return "";
        String t = s.replace('\n', ' ').trim();
        return t.length() > 160 ? t.substring(0, 160) + "..." : t;
    }

    // fix167: notes the system writes for a PROBLEM flag, a cleared flag or a hand-over are evidence, like a receipt:
    // they cannot be edited or deleted (the audit log keeps them too).
    private static boolean isEvidenceNote(String text) {
        if (text == null) return false;
        String t = text.trim();
        return t.startsWith("[PROBLEM]") || t.startsWith("[PROBLEM CLEARED]") || t.startsWith("[HANDED OVER]") || t.startsWith("[HAND-OVER UNDONE]");
    }

    private void requireNoteEditable(FollowUpLog log) {
        if (isEvidenceNote(log.getNotes())) {
            throw new BusinessException("NOTE_LOCKED: This note was written by the system for a PROBLEM flag or a hand-over. It is kept as a record and cannot be changed.");
        }
        if (log.getProjectId() != null) {
            projectRepository.findById(log.getProjectId()).ifPresent(p -> {
                if (p.isDeleted()) throw new BusinessException("NOTE_LOCKED: This project is deleted. Restore it first.");
            });
        }
    }

    @Transactional
    public void logNewNote(UUID projectId, String content) {
        String text = cleanNoteText(content);
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND: This project no longer exists."));
        if (project.isDeleted()) {
            throw new BusinessException("NOTE_BLOCKED: This project is deleted. Restore it first.");
        }
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(text)
                .recordedBy(getCurrentOperator())
                .build();
        followUpRepository.save(entry);
        auditService.logActionAfterCommit("NOTE_ADDED",
            "Operator [" + getCurrentOperator() + "] added note to " + plotLabel(project) + ": " + shortText(text));
    }

    @Transactional
    public void updateNote(UUID noteId, String content) {
        String text = cleanNoteText(content);
        FollowUpLog log = followUpRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        requireNoteEditable(log);
        if (isEvidenceNote(text)) {
            throw new BusinessException("NOTE_INVALID: A note cannot start with a system label like [PROBLEM] or [HANDED OVER].");
        }
        String before = log.getNotes();
        log.setNotes(text);
        followUpRepository.save(log);
        auditService.logActionAfterCommit("NOTE_UPDATED",
            "Operator [" + getCurrentOperator() + "] edited a note. WAS: " + shortText(before) + " | NOW: " + shortText(text));
    }

    @Transactional
    public void removeNote(UUID noteId) {
        FollowUpLog log = followUpRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        requireNoteEditable(log);
        String before = log.getNotes();
        followUpRepository.delete(log);
        auditService.logActionAfterCommit("NOTE_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted a note: " + shortText(before));
    }

    // ─── DOCUMENTS ────────────────────────────────────────────────────────────

    @Transactional
    public List<ProjectDocument> addScansToProject(UUID projectId, MultipartFile[] scans) throws Exception {
        return addScansToProject(projectId, scans, null, null);
    }

    /**
     * fix136: every file lands in a document category. batchCategory is the
     * default for the whole upload; fileCategories (same order as scans) lets
     * the uploader override it per file. All categories are validated BEFORE
     * any file is stored so a bad name can never leave half a batch behind.
     */
    @Transactional
    public List<ProjectDocument> addScansToProject(UUID projectId, MultipartFile[] scans, String batchCategory, List<String> fileCategories) throws Exception {
        return addScansToProject(projectId, scans, batchCategory, fileCategories, null);
    }

    /** fix180: statusId = the project status these documents belong to (null = general project documents). */
    @Transactional
    public List<ProjectDocument> addScansToProject(UUID projectId, MultipartFile[] scans, String batchCategory, List<String> fileCategories, UUID statusId) throws Exception {
        // fix167: nothing can be filed into a deleted project
        LandProject target = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND: This project no longer exists."));
        if (target.isDeleted()) {
            throw new BusinessException("UPLOAD_BLOCKED: This project is deleted. Restore it first.");
        }
        String statusName = null;
        if (statusId != null) {
            ProjectStatus st = projectStatusRepository.findById(statusId)
                    .orElseThrow(() -> new BusinessException("PROJECT_STATUS_NOT_FOUND: That status no longer exists."));
            if (!projectId.equals(st.getProjectId())) {
                throw new BusinessException("STATUS_MISMATCH: That status does not belong to this project.");
            }
            statusName = st.getStatusName();
        }
        List<ProjectDocument> saved = new ArrayList<>();
        String batchCode = documentCategoryService.requireCode(batchCategory);
        String[] cats = new String[scans.length];
        for (int i = 0; i < scans.length; i++) {
            String own = (fileCategories != null && i < fileCategories.size())
                    ? documentCategoryService.requireCode(fileCategories.get(i)) : null;
            cats[i] = own != null ? own : batchCode;
        }
        for (int i = 0; i < scans.length; i++) {
            MultipartFile file = scans[i];
            String path = fileStorageService.storeFile(file, projectId.toString());
            ProjectDocument doc = ProjectDocument.builder()
                    .projectId(projectId)
                    .fileName(file.getOriginalFilename())
                    .fileType(file.getContentType())
                    .category(cats[i])
                    .statusId(statusId)
                    .filePath(path)
                    .uploadedBy(getCurrentOperator())
                    .build();
            saved.add(documentRepository.save(doc));
        }
        auditService.logActionAfterCommit("DOCUMENT_UPLOADED",
            "Operator [" + getCurrentOperator() + "] uploaded " + scans.length
            + " document(s) to plot: " + projectId
            + (statusName != null ? " (status: " + statusName + ")" : "")
            + " [" + String.join(", ", java.util.Arrays.stream(cats)
                    .map(c -> c == null ? "UNCATEGORISED" : c).distinct().toList()) + "]");
        // This method only ever had the id, not the entity, so the label has to
        // be looked up -- and must not be allowed to fail the upload if the
        // row has gone missing underneath us.
        String docPlotLabel = projectRepository.findById(projectId)
                .map(this::plotLabel)
                .orElse("plot " + projectId);
        notificationService.emitToAudience("DOC_UPLOADED",
            scans.length + " document(s) attached to " + docPlotLabel
            + " by " + getCurrentOperator() + ".",
            "PROJECT", projectId);
        return saved;
    }

    @Transactional
    public void removeDocument(UUID docId) {
        ProjectDocument doc = documentRepository.findById(docId)
                .orElseThrow(() -> new BusinessException("DOCUMENT_NOT_FOUND: This document no longer exists."));
        // fix165: a payment receipt is evidence of money received. It can never be deleted (reverse the payment instead).
        if ("PAYMENT_RECEIPT".equals(doc.getCategory())) {
            throw new BusinessException("RECEIPT_LOCKED: A payment receipt cannot be deleted. If the payment was a mistake, REVERSE it in Payment History; the receipt stays as proof.");
        }
        // fix166: documents of a deleted project or of a handed-over title are locked, and the audit line says whose folder.
        LandProject docProject = doc.getProjectId() == null ? null : projectRepository.findById(doc.getProjectId()).orElse(null);
        if (docProject != null && docProject.isDeleted()) {
            throw new BusinessException("DOCUMENT_LOCKED: This project is deleted. Restore it first.");
        }
        if (docProject != null && docProject.getLandTitle() != null && docProject.getLandTitle().isReleased()) {
            throw new BusinessException("DOCUMENT_LOCKED: The title has been handed over, so its documents cannot be deleted. A director must UNDO the hand-over first.");
        }
        fileStorageService.deleteFile(doc.getFilePath());
        documentRepository.delete(doc);
        auditService.logActionAfterCommit("DOCUMENT_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted file: " + doc.getFileName()
            + (doc.getCategory() != null ? " (" + doc.getCategory() + ")" : "")
            + (docProject != null ? " from " + plotLabel(docProject) : ""));
    }

    // ─── STATUS / RELEASE ──────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void manualRealityOverride(UUID id, int targetStatus) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        // fix166: any manager could push ANY number in (negative, 999) and overwrite the status of a
        // receivable / handed-over / deleted project. Now director-only, 1..5 only, and those projects are refused.
        if (targetStatus < 1 || targetStatus > 5) {
            throw new BusinessException("STATUS_INVALID: The status index must be a number from 1 to 5.");
        }
        if (project.isDeleted() || project.isReceivable()
                || (project.getLandTitle() != null && project.getLandTitle().isReleased())) {
            throw new BusinessException("STATUS_LOCKED: The status of a deleted, receivable or handed-over project cannot be changed.");
        }
        int oldStatus = project.getCurrentStatusIndex();
        project.setCurrentStatusIndex(targetStatus);
        if (targetStatus >= 5) project.setStatus("COMPLETED");
        projectRepository.save(project);
        auditService.logActionAfterCommit("STATUS_OVERRIDE",
            "Operator [" + getCurrentOperator() + "] shifted plot "
            + plotLabel(project)
            + " from status " + oldStatus + " to status " + targetStatus);
        notificationService.emitToAudience("STATUS_ADVANCED",
            plotLabel(project) + " moved from status " + oldStatus
            + " to status " + targetStatus + " by " + getCurrentOperator() + ".",
            "PROJECT", project.getId());
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void authorizeRelease(UUID id, String managerNote) {
        // fix167: a hand-over must say who collected the title and how (5+ characters). Saved on the title, as a note and in the audit log.
        String why = managerNote == null ? "" : managerNote.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write who collected the title and how they were identified (at least 5 characters).");
        }
        LandProject project = projectRepository.findByIdForUpdate(id).orElseThrow();
        // fix181 (11.3): one shared rule (deleted, pending, no title, already handed over, PROBLEM, title money owed,
        // receivable fees owed, kept fees). The Dashboard count and the Folder button use the same method.
        String blocker = project.releaseBlocker();
        if (blocker != null) {
            throw new BusinessException("RELEASE DENIED: " + blocker);
        }
        LandTitle t = project.getLandTitle();
        t.setReleased(true);
        t.setReleasedAt(LocalDateTime.now());
        t.setReleasedBy(getCurrentOperator());
        t.setReleaseNote(why);
        project.setStatus("RELEASED");
        projectRepository.save(project);
        followUpRepository.save(FollowUpLog.builder().projectId(project.getId())
                .notes("[HANDED OVER] " + why).recordedBy(getCurrentOperator()).build());
        auditService.logActionAfterCommit("TITLE_RELEASED",
            "Operator [" + getCurrentOperator() + "] authorized handover for Plot: "
            + t.getPlotNumber() + ". Note: " + why);
        notificationService.emitToAudience("TITLE_COMPLETED",
            "Title for " + plotLabel(project) + " released to the client.",
            "PROJECT", project.getId());
    }

    // fix162: REVERSE A PAYMENT. The original line stays in the history; a negative REVERSAL line is added,
    // so every total, report and the audit trail stay honest.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void reversePayment(UUID projectId, UUID paymentId, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why this payment is being reversed (at least 5 characters).");
        }
        LandProject project = projectRepository.findByIdForUpdate(projectId)   // fix181 (16.12a): row lock
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (project.isDeleted()) {
            throw new BusinessException("REVERSAL_BLOCKED: This project is deleted. Restore it first.");
        }
        PaymentRecord original = paymentRecordRepository.findById(paymentId)
                .orElseThrow(() -> new BusinessException("PAYMENT_NOT_FOUND"));
        if (!projectId.equals(original.getProjectId())) {
            throw new BusinessException("PAYMENT_NOT_FOUND: That payment does not belong to this project.");
        }
        if ("REVERSAL".equals(original.getPaymentType()) || original.getAmountPaid().compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("REVERSAL_BLOCKED: A reversal cannot be reversed. Record a new payment instead.");
        }
        String marker = "[REVERSAL OF " + paymentId + "]";
        for (PaymentRecord r : paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId)) {
            if (r.getNotes() != null && r.getNotes().startsWith(marker)) {
                throw new BusinessException("REVERSAL_BLOCKED: This payment was already reversed.");
            }
        }
        if (project.getLandTitle() != null && project.getLandTitle().isReleased()) {
            throw new BusinessException("REVERSAL_BLOCKED: The title has been handed over. Undo the hand-over first.");
        }
        BigDecimal paid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        if (original.getAmountPaid().compareTo(paid) > 0) {
            throw new BusinessException("REVERSAL_BLOCKED: Reversing UGX " + original.getAmountPaid().toPlainString()
                    + " would take the total paid below zero.");
        }
        project.setAmountPaid(paid.subtract(original.getAmountPaid()));
        // fix167: a reversed STORAGE payment while still in receivables makes those fees unpaid again
        if ("STORAGE".equals(original.getAllocation()) && project.isReceivable()) {
            project.setStorageFeesPaid(project.storagePaidSafe().subtract(original.getAmountPaid()).max(BigDecimal.ZERO));
        } else if ("STORAGE".equals(original.getAllocation()) && "STANDARD".equals(original.getPaymentType())) {
            // fix181 (11.5b): a kept-fees payment (after SET ASIDE) moved its amount into the cost; undo exactly that
            BigDecimal cost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
            BigDecimal fees = project.getStorageFeesAccumulated() != null ? project.getStorageFeesAccumulated() : BigDecimal.ZERO;
            project.setTotalCost(cost.subtract(original.getAmountPaid()).max(BigDecimal.ZERO));
            project.setStorageFeesAccumulated(fees.add(original.getAmountPaid()));
        }
        BigDecimal balanceAfter = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());
        PaymentRecord reversal = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(original.getAmountPaid().negate())
                .paymentType("REVERSAL")
                .paidOn(LocalDateTime.now())   // fix181 (16.0a): a reversal has its own date, so the month it was made nets out
                .recordedBy(getCurrentOperator())
                .notes(marker + " " + why)
                .balanceAfter(balanceAfter)
                .allocation(original.getAllocation())
                .payerClientId(original.getPayerClientId())
                .payerName(original.getPayerName())
                .build();
        paymentRecordRepository.save(reversal);

        // fix181 (4.2): the last payment date comes from the newest payment still standing (by the day PAID), so a
        // reversed payment no longer keeps the client LOCKED or the badge green. Undated intake deposits never count.
        java.util.Set<String> reversedIds = new java.util.HashSet<>();
        reversedIds.add(paymentId.toString());
        List<PaymentRecord> lines = paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId);
        for (PaymentRecord r : lines) {
            if (r.getNotes() != null && r.getNotes().startsWith("[REVERSAL OF ")) {
                int end = r.getNotes().indexOf(']');
                if (end > 13) reversedIds.add(r.getNotes().substring(13, end).trim());
            }
        }
        LocalDateTime newest = null;
        for (PaymentRecord r : lines) {
            if ("REVERSAL".equals(r.getPaymentType()) || r.getPaidOn() == null) continue;
            if (r.getAmountPaid() == null || r.getAmountPaid().signum() <= 0) continue;
            if (reversedIds.contains(String.valueOf(r.getId()))) continue;
            if (newest == null || r.getPaidOn().isAfter(newest)) newest = r.getPaidOn();
        }
        project.setLastPaymentDate(newest);
        projectRepository.save(project);

        // fix181 (11.5a): the "payment received" note on the Recovery card gets its counterpart
        java.util.List<Client> noteFor = new java.util.ArrayList<>();
        for (Client c : project.billingParties()) {
            if (original.getPayerClientId() == null || c.getId().equals(original.getPayerClientId())) noteFor.add(c);
        }
        LocalDateTime paidDay = original.getPaidOn() != null ? original.getPaidOn() : original.getTimestamp();
        for (Client c : noteFor) {
            recoveryNoteRepository.save(com.gesolutions.erp.modules.client.model.RecoveryNote.builder()
                .client(c).author(null).tag("payment reversed").tone("INFO").countsAsAttempt(false)
                .text("Payment of UGX " + original.getAmountPaid().toPlainString()
                        + (paidDay != null ? " on " + paidDay.toLocalDate() : "") + " was reversed: " + why).build());
        }
        notificationService.emitToAudience("PAYMENT_REVERSED",
            "UGX " + original.getAmountPaid().toPlainString() + " reversed on " + plotLabel(project) + " by " + getCurrentOperator() + ".",
            "PROJECT", projectId);
        auditService.logActionAfterCommit("PAYMENT_REVERSED",
            "Operator [" + getCurrentOperator() + "] reversed UGX " + original.getAmountPaid().toPlainString()
            + " on " + plotLabel(project) + ". Reason: " + why);
    }

    // fix162: UNDO A HAND-OVER (the title goes back to "not handed over"). Reason required, audited.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void undoRelease(UUID id, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the hand-over is being undone (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (project.isDeleted()) {
            throw new BusinessException("UNDO_DENIED: This project is deleted. Restore it first.");
        }
        if (project.getLandTitle() == null || !project.getLandTitle().isReleased()) {
            throw new BusinessException("UNDO_DENIED: This title has not been handed over.");
        }
        project.getLandTitle().setReleased(false);
        project.getLandTitle().setReleasedAt(null);
        project.getLandTitle().setReleasedBy(null);
        project.getLandTitle().setReleaseNote(null);
        project.setStatus(project.isReceivable() ? "RECEIVABLE" : "ACTIVE");
        projectRepository.save(project);
        followUpRepository.save(FollowUpLog.builder().projectId(project.getId())
                .notes("[HAND-OVER UNDONE] " + why).recordedBy(getCurrentOperator()).build());
        auditService.logActionAfterCommit("TITLE_RELEASE_UNDONE",
            "Operator [" + getCurrentOperator() + "] undid the hand-over of " + plotLabel(project) + ". Reason: " + why);
    }

    // fix163: REVERT A SAVED TITLE (take the Title Details off the project).
    // Director/admin only. Needs a reason. Refused when the title was handed over and when the project is Receivable or
    // Legacy. fix180: also refused for the project types that ALWAYS keep Title Details (Subdivision, Legacy Titles,
    // Transfer of Title, Boundary Opening, Resurvey) -- use EDIT to correct them. Topographic Survey switches its
    // optional panel off again. The title row is deleted (this frees the plot number); the old values are kept in the audit line.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void revertTitle(UUID id, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the title is being reverted (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        LandTitle title = project.getLandTitle();
        if (title == null) {
            throw new BusinessException("REVERT_DENIED: This project has no saved title to revert.");
        }
        if (title.isReleased()) {
            throw new BusinessException("REVERT_DENIED: The title was handed over. Undo the hand-over first.");
        }
        if (project.isReceivable() || project.isLegacy()) {
            throw new BusinessException("REVERT_DENIED: A Receivable or Legacy project cannot have its title taken off.");
        }
        ProjectType type = ProjectType.of(project);
        if (type.getTitleMode() == ProjectType.TitleMode.ALWAYS) {
            throw new BusinessException("REVERT_DENIED: A " + type.getLabel() + " project always keeps its Title Details. Use EDIT to correct them.");
        }
        java.util.List<ProjectStatus> statuses = projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(id);
        String oldValues = fix166TitleLine(title) + ", title date " + title.getTitleIssueDate();
        project.setLandTitle(null);
        project.setTitleDetailsEnabled(false);
        project.setStatus("ACTIVE");
        projectRepository.saveAndFlush(project);
        landTitleRepository.delete(title);
        // the "Titled" status goes back to not done, since the project has no title any more
        for (ProjectStatus st : statuses) {
            if (st.isCompleted() && isTitledStatus(st.getStatusName())) {
                st.setCompleted(false);
                st.setCompletedAt(null);
                st.setCompletedBy(null);
                projectStatusRepository.save(st);
            }
        }
        auditService.logActionAfterCommit("TITLE_REVERTED",
            "Operator [" + getCurrentOperator() + "] took the saved title off project " + project.getProjectIndex()
            + ". Old title: " + oldValues + ". Reason: " + why);
    }

    // ─── READ METHODS ─────────────────────────────────────────────────────────

    // fix167: setStoragePaused / setStorageFeeOverride / setAccumulatedFees / setNegotiationDeadline /
    // setReceivableStartOverride are gone with their endpoints. FolderPortalController.settings and reduceFees replace them.

    @Transactional(readOnly = true)
    public List<ProjectDocument> getProjectDocuments(UUID projectId) {
        return documentRepository.findByProjectId(projectId);
    }

    @Transactional(readOnly = true)
    public List<FollowUpLog> getProjectNotes(UUID projectId) {
        return followUpRepository.findByProjectIdOrderByTimestampDesc(projectId);
    }

    @Transactional(readOnly = true)
    public List<PaymentRecord> getProjectPayments(UUID projectId) {
        return paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId);
    }

    @Transactional(readOnly = true)
    public Page<LandProject> getGlobalLedger(Pageable pageable) {
        Page<LandProject> page = projectRepository.findAllIncludingPending(pageable);   // fix181 (8.9): the Pending tab reads this
        // fix170: ONE query for every status on the page (it was one query per project)
        List<UUID> ids = new ArrayList<>();
        for (LandProject p : page.getContent()) ids.add(p.getId());
        Map<UUID, List<ProjectStatus>> byProject = new HashMap<>();
        if (!ids.isEmpty()) for (ProjectStatus s : projectStatusRepository.findByProjectIdIn(ids)) byProject.computeIfAbsent(s.getProjectId(), k -> new ArrayList<>()).add(s);
        for (LandProject p : page.getContent()) {
            List<ProjectStatus> l = byProject.getOrDefault(p.getId(), new ArrayList<>());
            l.sort(Comparator.comparingInt(s -> s.getDisplayOrder() == null ? 0 : s.getDisplayOrder()));
            p.setStatuses(l);
        }
        return page;
    }

    // fix180: the final "Titled" status (old projects: "Registration and Title Issuance")
    public static boolean isTitledStatus(String name) {
        if (name == null) return false;
        String n = name.trim().toLowerCase();
        return n.equals("titled") || n.contains("registration");
    }

    // fix180: MARK TITLED (Ledger, Ready for Titling) ticks each project's "Titled" status. It no longer creates an
    // empty title: Title Details belong to the project type and are typed on the folder page.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public int bulkMarkTitleProduced(java.util.List<java.util.UUID> projectIds) {
        if (projectIds == null || projectIds.isEmpty()) return 0;
        int count = 0;
        for (java.util.UUID id : projectIds) {
            LandProject project = projectRepository.findById(id).orElse(null);
            if (project == null || project.isDeleted()) continue;
            boolean ticked = false;
            for (ProjectStatus st : projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(id)) {
                if (!st.isCompleted() && isTitledStatus(st.getStatusName())) {
                    st.setCompleted(true);
                    st.setCompletedAt(java.time.LocalDateTime.now());
                    st.setCompletedBy(getCurrentOperator());
                    projectStatusRepository.save(st);
                    ticked = true;
                }
            }
            if (ticked) count++;
        }
        auditService.logActionAfterCommit("BULK_TITLE_PRODUCED",
            "Operator [" + getCurrentOperator() + "] marked " + count + " projects as Titled.");
        return count;
    }
}