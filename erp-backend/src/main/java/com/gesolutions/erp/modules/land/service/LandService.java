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
    private final StageTemplateService stageTemplateService;
    private final ProjectStageRepository projectStageRepository;
    private final LandTitleRepository landTitleRepository;
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
        auditService.logAction("EDIT_MODE_OPENED",
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

        return ProjectDeepDetailDTO.builder()
                .project(project)
                .notes(notes)
                .documents(documents)
                .payments(payments)
                .remainingBalance(remaining)
                .collectionPercentage(percent)
                .build();
    }

    // ─── PAYMENT RECORDING ────────────────────────────────────────────────────

    // fix167: a payment now says WHO paid (one owner of the project) and WHAT it pays for:
    //   TITLE   = the work (total cost). Cannot go over what is still owed on the work.
    //   STORAGE = storage fees. Only on a project in receivables, and never more than the fees not yet paid.
    // Joint owners: when a project has more than one owner the payer MUST be named, so each owner's money is tracked.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public PaymentRecord recordPayment(UUID projectId, BigDecimal amount, String notes, UUID payerId, String allocation) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
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
        Set<Client> owners = project.getProprietors() != null ? project.getProprietors() : new HashSet<>();
        if (payerId != null) {
            for (Client c : owners) if (c.getId().equals(payerId)) payer = c;
            if (payer == null) throw new BusinessException("PAYER_INVALID: The person who paid must be one of this project's owners.");
        } else if (owners.size() == 1) {
            payer = owners.iterator().next();
        } else if (owners.size() > 1) {
            throw new BusinessException("PAYER_REQUIRED: This project has " + owners.size() + " owners. Pick which owner paid.");
        }

        BigDecimal cost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal paidNow = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        BigDecimal titlePaid = paidNow.subtract(project.storagePaidSafe());
        if ("STORAGE".equals(kind)) {
            if (!project.isReceivable()) {
                throw new BusinessException("PAYMENT_FAULT: Storage fees can only be paid while the project is in receivables.");
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
        if ("STORAGE".equals(kind)) project.setStorageFeesPaid(project.storagePaidSafe().add(amount));
        project.setLastPaymentDate(LocalDateTime.now());

        BigDecimal balanceAfter = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());

        PaymentRecord record = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(amount)
                .paymentType(paymentType)
                .recordedBy(operator)
                .notes(notes)
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
            auditService.logAction("RECEIVABLE_EXIT",
                "Operator [" + operator + "] -- Plot " + plotLabel(project)
                + " EXITED RECEIVABLE after full payment clearance (UGX " + fees.toPlainString() + " of paid storage fees moved into the total cost).");
        } else {
            projectRepository.save(project);
        }

        if ("RECEIVABLE_PARTIAL".equals(paymentType)) {
            notificationService.emit("PAYMENT_ON_RECEIVABLE", "POSITIVE", "Payment UGX " + amount + " received on " + plotLabel(project) + ".", "PROJECT", projectId, "ROLE_DIRECTOR");
        }
        // fix167: the "payment received" line goes on the recovery card of the owner who PAID (not on every owner)
        java.util.List<Client> noteFor = new java.util.ArrayList<>();
        if (payer != null) noteFor.add(payer); else noteFor.addAll(owners);
        for (Client owner : noteFor) {
            recoveryNoteRepository.save(com.gesolutions.erp.modules.client.model.RecoveryNote.builder()
                .client(owner).author(null).tag("payment received").tone("INFO").countsAsAttempt(false)
                .text("Paid UGX " + amount + " on " + java.time.LocalDate.now() + ("STORAGE".equals(kind) ? " (storage fees)" : "")).build());
        }
        auditService.logAction("PAYMENT_RECORDED",
            "Operator [" + operator + "] recorded UGX " + amount
            + " for plot: " + plotLabel(project)
            + " | Type: " + paymentType
            + " | For: " + kind
            + (payer != null ? " | Paid by: " + payer.getFullName() : "")
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
        if (receipt == null || receipt.isEmpty()) {
            throw new BusinessException("RECEIPT_REQUIRED: A payment cannot be saved without its receipt. Attach the receipt scan (PDF, JPG, PNG or WEBP).");
        }
        if (receipt.getSize() > 10L * 1024L * 1024L) {
            throw new BusinessException("RECEIPT_TOO_LARGE: The receipt must be under 10 MB.");
        }
        requireScanFiles(new MultipartFile[] { receipt });
        PaymentRecord record = recordPayment(projectId, amount, notes, payerId, allocation);
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
    // individual saves (client, project, payment, stages, notes) each
    // committed on their own. A failure partway -- like the sample seed --
    // left an orphaned Client row that re-poisoned every later restart.
    // Now the whole intake is one all-or-nothing unit, same as every
    // other write method in this class.
    @Transactional(rollbackFor = Exception.class)
    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {
        // PHASE D (Section 18.10): LandProject is built FIRST. A LandTitle
        // is only built if the legacy preset is used or the final
        // processing stage ("Registration and Title Issuance") is checked.
        boolean hasFinalStage = request.getSelectedStages() != null && request.getSelectedStages().stream()
                .anyMatch(s -> s.isCompleted() && "Registration and Title Issuance".equalsIgnoreCase(s.getStageName()));
        boolean hasTitleFields = request.isLegacy() || hasFinalStage || request.isTitleAtIntake();
        String projectIndex = projectIndexService.generateNextIndex();

        BigDecimal initialPayment = request.getInitialPayment() != null
                ? request.getInitialPayment() : BigDecimal.ZERO;
        BigDecimal totalCost = request.getTotalCost() != null
                ? request.getTotalCost() : BigDecimal.ZERO;
        BigDecimal outstanding = totalCost.subtract(initialPayment);

        boolean startAsReceivable = request.isStartAsReceivable();

        LandTitle title = null;
        if (hasTitleFields) {
            if (request.getPlotNumber() == null || request.getPlotNumber().isBlank()) {
                throw new com.gesolutions.erp.common.exception.BusinessException("PLOT_NUMBER_REQUIRED: Plot number is required when using Legacy preset or completing the final stage.");
            }
            // STEP 4 (intake fix): Title Details is now fully required on the
            // frontend once shown -- mirror that here the same way
            // PLOT_NUMBER_REQUIRED already does, since this service validates
            // DTOs imperatively rather than via @Valid/bean-validation.
            if (request.getTitleId() == null || request.getTitleId().isBlank()) {
                throw new com.gesolutions.erp.common.exception.BusinessException("TITLE_ID_REQUIRED: Title ID is required when using Legacy preset or completing the final stage.");
            }
            if (request.getBlockRoad() == null || request.getBlockRoad().isBlank()) {
                throw new com.gesolutions.erp.common.exception.BusinessException("BLOCK_REQUIRED: Block is required when using Legacy preset or completing the final stage.");
            }
            if (request.getTitleIssueDate() == null) {
                throw new com.gesolutions.erp.common.exception.BusinessException("TITLE_DATE_REQUIRED: Title Date is required when using Legacy preset or completing the final stage.");
            }
            title = LandTitle.builder()
                    .titleId(request.getTitleId())
                    .tenure(request.getTenure() != null && !request.getTenure().isBlank() ? request.getTenure() : "FREEHOLD")
                    .plotNumber(request.getPlotNumber())
                    .blockRoad(request.getBlockRoad())
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
                .amountPaid(initialPayment)
                .isLegacy(request.isLegacy())
                .currentStageIndex(startAsReceivable ? 5 : 1)
                .status(startAsReceivable ? "RECEIVABLE" : "ACTIVE");

        if (startAsReceivable && outstanding.compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal initialFees = request.getInitialStorageFee() != null
                    ? request.getInitialStorageFee() : BigDecimal.ZERO;
            builder.isReceivable(true)
                   .receivableStartDate(LocalDateTime.now())
                   .originalDebt(outstanding)
                   .storageFeesAccumulated(initialFees);
            if (request.getMonthlyStorageFee() != null
                    && request.getMonthlyStorageFee().compareTo(BigDecimal.ZERO) > 0) {
                builder.storageFeeOverride(request.getMonthlyStorageFee());
            }
        }

        LandProject project = builder.build();

        if (request.getOwners() != null) {
            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {
                if (o.getNationalId() == null || o.getNationalId().isBlank()) {
                    throw new BusinessException("NIN_REQUIRED: Owner \"" + o.getFullName() + "\" is missing a National ID (NIN).");
                }
                Client c = clientService.findOrCreateClientByNin(o.getFullName(), o.getNationalId(), o.getPhone(), o.getEmail());
                c.setHomeAddress(o.getAddress());
                project.addProprietor(c);
            }
        }

        LandProject saved = projectRepository.save(project);

        // Record initial payment if any
        if (initialPayment.compareTo(BigDecimal.ZERO) > 0) {
            PaymentRecord initialRecord = PaymentRecord.builder()
                    .projectId(saved.getId())
                    .amountPaid(initialPayment)
                    .paymentType("INITIAL_DEPOSIT")
                    .recordedBy(getCurrentOperator())
                    .notes("Initial deposit at intake")
                    .balanceAfter(outstanding)
                    .build();
            paymentRecordRepository.save(initialRecord);
            saved.setLastPaymentDate(LocalDateTime.now());
            projectRepository.save(saved);
        }

        // fix167: New Title and Legacy Title projects have no stage checklist (guide 8.9.1). The page used to send
        // the whole default list for them too, so every titled entry got 6 stray stages.
        if (!request.isLegacy() && !request.isTitleAtIntake()
                && request.getSelectedStages() != null && !request.getSelectedStages().isEmpty()) {
            stageTemplateService.attachStagesToProject(saved.getId(), request.getSelectedStages());
        }

        if (scans != null) addScansToProject(saved.getId(), scans);

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
        String receivableNote = startAsReceivable ? " [ENTERED AS RECEIVABLE]" : "";
        notificationService.emit("NEW_INTAKE", "INFO", "New project " + projectIndex + " registered by " + getCurrentOperator() + ".", "PROJECT", saved.getId(), "ROLE_MANAGER");
        auditService.logAction("INTAKE",
            "Operator [" + getCurrentOperator() + "] ingested binder: "
            + plotOrIndex + receivableNote);

        if (startAsReceivable) {
            auditService.logAction("RECEIVABLE_TRIGGER",
                "Operator [" + getCurrentOperator() + "] flagged plot "
                + plotOrIndex + " as RECEIVABLE at intake. Debt: UGX " + outstanding);
        }

        return saved;
    }

    // ─── FULL UPDATE ──────────────────────────────────────────────────────────

    // fix166: one-line descriptions of the title and the owners, used to write OLD -> NEW into the audit log.
    private String fix166TitleLine(LandTitle t) {
        if (t == null) return "no title";
        return "plot " + t.getPlotNumber() + ", title ID " + t.getTitleId() + ", tenure " + t.getTenure() + ", block " + t.getBlockRoad();
    }

    private String fix166OwnersLine(LandProject p) {
        if (p.getProprietors() == null || p.getProprietors().isEmpty()) return "none";
        return p.getProprietors().stream()
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
        final String fix166OldTitle = fix166TitleLine(title);
        final String fix166OldOwners = fix166OwnersLine(project);

        // PHASE E (Section 18.9.4): Create LandTitle on edit if title fields
        // are provided but no title exists yet. Otherwise update existing title.
        boolean hasTitleFields = request.getPlotNumber() != null && !request.getPlotNumber().isBlank();
        if (title == null && hasTitleFields) {
            // fix167: a title saved from the folder page needs the same details as one typed on New Project
            if (request.getTitleId() == null || request.getTitleId().isBlank()) {
                throw new BusinessException("TITLE_ID_REQUIRED: Type the title ID before saving the title.");
            }
            title = LandTitle.builder()
                    .titleId(request.getTitleId())
                    .tenure(request.getTenure() != null && !request.getTenure().isBlank() ? request.getTenure() : "FREEHOLD")
                    .plotNumber(request.getPlotNumber())
                    .blockRoad(request.getBlockRoad())
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : java.time.LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
            project.setLandTitle(title);
        } else if (title != null) {
            title.setTitleId(request.getTitleId());
            title.setPlotNumber(request.getPlotNumber());
            title.setTenure(request.getTenure());
            title.setBlockRoad(request.getBlockRoad());
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
            if (newTotalCost.compareTo(currentPaid) < 0) {
                throw new BusinessException("COST_BELOW_PAID: The new cost (UGX " + newTotalCost.toPlainString()
                        + ") is lower than the UGX " + currentPaid.toPlainString()
                        + " already paid. Reverse the extra payment first.");
            }
            auditService.logAction("COST_CHANGED",
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
            project.setOriginalDebt(newTotalCost.subtract(amtPaid).max(BigDecimal.ZERO));
        }

        LandProject saved = projectRepository.save(project);
        auditService.logAction("RECORD_UPDATED",
            "Operator [" + getCurrentOperator() + "] modified Binder: "
            + plotLabel(project));
        // fix166: a change of plot / title ID / tenure / block, or of the owners, is written with OLD -> NEW.
        String fix166NewTitle = fix166TitleLine(project.getLandTitle());
        if (!fix166OldTitle.equals(fix166NewTitle)) {
            auditService.logAction("TITLE_FIELDS_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed the title details of project #" + project.getProjectIndex()
                + ". Old: " + fix166OldTitle + " -> New: " + fix166NewTitle);
        }
        String fix166NewOwners = fix166OwnersLine(project);
        if (!fix166OldOwners.equals(fix166NewOwners)) {
            auditService.logAction("OWNERS_CHANGED",
                "Operator [" + getCurrentOperator() + "] changed the owners of project #" + project.getProjectIndex()
                + ". Old: " + fix166OldOwners + " -> New: " + fix166NewOwners);
        }
        return saved;
    }

    // ─── SOFT DELETE (formerly NUCLEAR DELETE) ───────────────────────────────
    // STAGE 3 FIX: this used to hard-delete the Cloudinary files, every payment
    // record, every note, and the DB row itself -- irreversible in one click.
    // It now only flags the row as deleted. Nothing else is touched, so a
    // mis-click is recoverable via restoreProject() below.

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
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
        projectRepository.save(project);

        auditService.logAction("RECORD_DELETED",
            "Root user [" + getCurrentOperator() + "] deleted plot: " + plotNo + ". Reason: " + why);
        /* fix71: CRITICAL was a severity the frontend rendered and the backend
           never emitted. Deleting a plot is exactly what it is for. emitRaw,
           not emit: emit de-duplicates on (type, entityId) forever, so a plot
           deleted, restored and deleted again would have gone silent the
           second time. */
        notificationService.emitRaw("PROJECT_DELETED", "CRITICAL",
            "Plot " + plotNo + " deleted by " + getCurrentOperator()
            + ". Restore it from Settings -> Archive.",
            "PROJECT", project.getId(), "ROLE_DIRECTOR");
    }

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void restoreProject(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = plotLabel(project);

        project.setDeleted(false);
        project.setDeletedAt(null);
        projectRepository.save(project);

        auditService.logAction("RECORD_RESTORED",
            "Root user [" + getCurrentOperator() + "] restored plot: " + plotNo);
        notificationService.emitRaw("PROJECT_RESTORED", "POSITIVE",
            "Plot " + plotNo + " restored by " + getCurrentOperator() + ".",
            "PROJECT", project.getId(), "ROLE_DIRECTOR");
    }

    @Transactional(readOnly = true)
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
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

        boolean ownerIsProprietor = project.getProprietors() != null &&
                project.getProprietors().stream()
                        .anyMatch(o -> o != null && o.getId() != null && o.getId().equals(ownerId));
        if (!ownerIsProprietor) {
            throw new BusinessException(
                    "OWNER_NOT_ON_PROJECT: The selected owner is not a proprietor of this project.");
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
                Client coOwner = project.getProprietors().stream()
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

        auditService.logAction("RECOVERY_SYNC",
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
        auditService.logAction("NOTE_ADDED",
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
        auditService.logAction("NOTE_UPDATED",
            "Operator [" + getCurrentOperator() + "] edited a note. WAS: " + shortText(before) + " | NOW: " + shortText(text));
    }

    @Transactional
    public void removeNote(UUID noteId) {
        FollowUpLog log = followUpRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        requireNoteEditable(log);
        String before = log.getNotes();
        followUpRepository.delete(log);
        auditService.logAction("NOTE_DELETED",
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
        // fix167: nothing can be filed into a deleted project
        LandProject target = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND: This project no longer exists."));
        if (target.isDeleted()) {
            throw new BusinessException("UPLOAD_BLOCKED: This project is deleted. Restore it first.");
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
                    .filePath(path)
                    .uploadedBy(getCurrentOperator())
                    .build();
            saved.add(documentRepository.save(doc));
        }
        auditService.logAction("DOCUMENT_UPLOADED",
            "Operator [" + getCurrentOperator() + "] uploaded " + scans.length
            + " document(s) to plot: " + projectId
            + " [" + String.join(", ", java.util.Arrays.stream(cats)
                    .map(c -> c == null ? "UNCATEGORISED" : c).distinct().toList()) + "]");
        // This method only ever had the id, not the entity, so the label has to
        // be looked up -- and must not be allowed to fail the upload if the
        // row has gone missing underneath us.
        String docPlotLabel = projectRepository.findById(projectId)
                .map(this::plotLabel)
                .orElse("plot " + projectId);
        notificationService.emitRaw("DOC_UPLOADED", "INFO",
            scans.length + " document(s) attached to " + docPlotLabel
            + " by " + getCurrentOperator() + ".",
            "PROJECT", projectId, "ROLE_MANAGER");
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
        auditService.logAction("DOCUMENT_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted file: " + doc.getFileName()
            + (doc.getCategory() != null ? " (" + doc.getCategory() + ")" : "")
            + (docProject != null ? " from " + plotLabel(docProject) : ""));
    }

    // ─── STAGE / RELEASE ──────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void manualRealityOverride(UUID id, int targetStage) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        // fix166: any manager could push ANY number in (negative, 999) and overwrite the status of a
        // receivable / handed-over / deleted project. Now director-only, 1..5 only, and those projects are refused.
        if (targetStage < 1 || targetStage > 5) {
            throw new BusinessException("STAGE_INVALID: The stage must be a number from 1 to 5.");
        }
        if (project.isDeleted() || project.isReceivable()
                || (project.getLandTitle() != null && project.getLandTitle().isReleased())) {
            throw new BusinessException("STAGE_LOCKED: The stage of a deleted, receivable or handed-over project cannot be changed.");
        }
        int oldStage = project.getCurrentStageIndex();
        project.setCurrentStageIndex(targetStage);
        if (targetStage >= 5) project.setStatus("COMPLETED");
        projectRepository.save(project);
        auditService.logAction("STAGE_OVERRIDE",
            "Operator [" + getCurrentOperator() + "] shifted plot "
            + plotLabel(project)
            + " from stage " + oldStage + " to stage " + targetStage);
        notificationService.emitRaw("STAGE_ADVANCED", "POSITIVE",
            plotLabel(project) + " moved from stage " + oldStage
            + " to stage " + targetStage + " by " + getCurrentOperator() + ".",
            "PROJECT", project.getId(), "ROLE_MANAGER");
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void authorizeRelease(UUID id, String managerNote) {
        // fix167: a hand-over must say who collected the title and how (5+ characters). Saved on the title, as a note and in the audit log.
        String why = managerNote == null ? "" : managerNote.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write who collected the title and how they were identified (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(id).orElseThrow();
        // fix166: no hand-over of a deleted project, no second hand-over, and none while the plot is flagged as a PROBLEM.
        if (project.isDeleted()) {
            throw new BusinessException("RELEASE DENIED: This project is deleted. Restore it first.");
        }
        if (project.getLandTitle() != null && project.getLandTitle().isReleased()) {
            throw new BusinessException("RELEASE DENIED: This title has already been handed over.");
        }
        if (project.isProblem()) {
            throw new BusinessException("RELEASE DENIED: This plot is flagged as a PROBLEM. Clear the flag (with a reason) before handing over the title.");
        }
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: UGX " + project.getTotalCost().subtract(project.getAmountPaid()).toPlainString() + " is still owed on the title work.");
        }
        // fix162: storage fees still owed are arrears too.
        if (project.isReceivable() && project.receivableTotalOwed().compareTo(BigDecimal.ZERO) > 0) {
            throw new BusinessException("RELEASE DENIED: Storage fees are still owed on this project.");
        }
        // fix167: fees kept by SET ASIDE are still on the project even though it left receivables
        if (!project.isReceivable() && project.storageUnpaid().compareTo(BigDecimal.ZERO) > 0) {
            throw new BusinessException("RELEASE DENIED: UGX " + project.storageUnpaid().toPlainString()
                    + " of set-aside storage fees is still on this project. A director must WAIVE them or ADD them to the cost first.");
        }
        // PHASE B (Section 18.9.1): landTitle can now be null.
        if (project.getLandTitle() == null) {
            throw new BusinessException("RELEASE DENIED: This project has no title to release yet.");
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
        auditService.logAction("TITLE_RELEASED",
            "Operator [" + getCurrentOperator() + "] authorized handover for Plot: "
            + t.getPlotNumber() + ". Note: " + why);
        notificationService.emitRaw("TITLE_COMPLETED", "POSITIVE",
            "Title for " + plotLabel(project) + " released to the client.",
            "PROJECT", project.getId(), "ROLE_DIRECTOR");
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
        LandProject project = projectRepository.findById(projectId)
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
        }
        BigDecimal balanceAfter = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());
        PaymentRecord reversal = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(original.getAmountPaid().negate())
                .paymentType("REVERSAL")
                .recordedBy(getCurrentOperator())
                .notes(marker + " " + why)
                .balanceAfter(balanceAfter)
                .allocation(original.getAllocation())
                .payerClientId(original.getPayerClientId())
                .payerName(original.getPayerName())
                .build();
        paymentRecordRepository.save(reversal);
        projectRepository.save(project);
        auditService.logAction("PAYMENT_REVERSED",
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
        auditService.logAction("TITLE_RELEASE_UNDONE",
            "Operator [" + getCurrentOperator() + "] undid the hand-over of " + plotLabel(project) + ". Reason: " + why);
    }

    // fix163: REVERT A SAVED TITLE BACK TO STAGES.
    // Director/admin only. Needs a reason. Refused when the title was handed over, when the project is
    // Receivable or Legacy, and when the project was created as New Title / Legacy Title (it has no stages).
    // The title row is deleted (this frees the plot number); the old values are kept in the audit line.
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
            throw new BusinessException("REVERT_DENIED: A Receivable or Legacy project cannot be reverted to stages.");
        }
        java.util.List<com.gesolutions.erp.modules.land.model.ProjectStage> stages =
                projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(id);
        if (stages.isEmpty()) {
            throw new BusinessException("REVERT_DENIED: This project was created with its title (New Title / Legacy Title), so it has no stages to go back to.");
        }
        String oldValues = "plot " + title.getPlotNumber() + ", title ID " + title.getTitleId()
                + ", tenure " + title.getTenure() + ", block " + title.getBlockRoad()
                + ", title date " + title.getTitleIssueDate();
        project.setLandTitle(null);
        project.setStatus("ACTIVE");
        projectRepository.saveAndFlush(project);
        landTitleRepository.delete(title);
        com.gesolutions.erp.modules.land.model.ProjectStage last = stages.get(stages.size() - 1);
        if (last.isCompleted()) {
            last.setCompleted(false);
            last.setCompletedAt(null);
            projectStageRepository.save(last);
        }
        auditService.logAction("TITLE_REVERTED",
            "Operator [" + getCurrentOperator() + "] reverted the saved title of project " + project.getProjectIndex()
            + " back to stages. Old title: " + oldValues + ". Reason: " + why);
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
        Page<LandProject> page = projectRepository.findAll(pageable);
        // fix170: ONE query for every stage on the page (it was one query per project)
        List<UUID> ids = new ArrayList<>();
        for (LandProject p : page.getContent()) ids.add(p.getId());
        Map<UUID, List<ProjectStage>> byProject = new HashMap<>();
        if (!ids.isEmpty()) for (ProjectStage s : projectStageRepository.findByProjectIdIn(ids)) byProject.computeIfAbsent(s.getProjectId(), k -> new ArrayList<>()).add(s);
        for (LandProject p : page.getContent()) {
            List<ProjectStage> l = byProject.getOrDefault(p.getId(), new ArrayList<>());
            l.sort(Comparator.comparingInt(s -> s.getDisplayOrder() == null ? 0 : s.getDisplayOrder()));
            p.setStages(l);
        }
        return page;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public int bulkMarkTitleProduced(java.util.List<java.util.UUID> projectIds) {
        if (projectIds == null || projectIds.isEmpty()) return 0;
        int count = 0;
        for (java.util.UUID id : projectIds) {
            LandProject project = projectRepository.findById(id).orElse(null);
            if (project != null && project.getLandTitle() == null) {
                LandTitle title = LandTitle.builder()
                        .tenure("FREEHOLD")
                        .projectStartDate(java.time.LocalDate.now())
                        .build();
                project.setLandTitle(title);
                projectRepository.save(project);

                java.util.List<ProjectStage> stages = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(id);
                for (ProjectStage stage : stages) {
                    if (stage.getStageName() != null && stage.getStageName().toLowerCase().contains("registration")) {
                        stage.setCompleted(true);
                        stage.setCompletedAt(java.time.LocalDateTime.now());
                        projectStageRepository.save(stage);
                    }
                }
                count++;
            }
        }
        auditService.logAction("BULK_TITLE_PRODUCED", 
            "Operator [" + getCurrentOperator() + "] marked " + count + " projects as title-produced.");
        return count;
    }
}