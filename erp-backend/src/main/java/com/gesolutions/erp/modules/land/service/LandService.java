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
    private final ClientRepository clientRepository;
    private final ClientService clientService;
    private final FileStorageService fileStorageService;
    private final AuditService auditService;
    private final PaymentRecordRepository paymentRecordRepository;
    private final ProjectIndexService projectIndexService;
    private final StageTemplateService stageTemplateService;

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

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        // STAGE 1 FIX: block overpayment -- work out what is still owed
        // using the same logic already used below for balanceAfter.
        BigDecimal currentlyOwed = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());
        if (amount.compareTo(currentlyOwed) > 0) {
            throw new BusinessException("OVERPAYMENT_BLOCKED: This project only owes UGX "
                    + currentlyOwed + ". You tried to record UGX " + amount + ".");
        }

        String operator = getCurrentOperator();
        String paymentType = project.isReceivable() ? "RECEIVABLE_PARTIAL" : "STANDARD";

        BigDecimal newAmountPaid = project.getAmountPaid().add(amount);
        project.setAmountPaid(newAmountPaid);
        project.setLastPaymentDate(LocalDateTime.now());

        BigDecimal balanceAfter;
        if (project.isReceivable()) {
            balanceAfter = project.receivableTotalOwed();
        } else {
            balanceAfter = project.getTotalCost().subtract(newAmountPaid);
        }

        PaymentRecord record = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(amount)
                .paymentType(paymentType)
                .recordedBy(operator)
                .notes(notes)
                .balanceAfter(balanceAfter)
                .build();
        paymentRecordRepository.save(record);

        // Auto-exit receivable if fully paid
        if (project.isReceivable() && balanceAfter.compareTo(BigDecimal.ZERO) <= 0) {
            project.setReceivable(false);
            project.setStatus("ACTIVE");
            projectRepository.save(project);
            auditService.logAction("RECEIVABLE_EXIT",
                "Operator [" + operator + "] — Plot " + plotLabel(project)
                + " EXITED RECEIVABLE after full payment clearance.");
        } else {
            projectRepository.save(project);
        }

        auditService.logAction("PAYMENT_RECORDED",
            "Operator [" + operator + "] recorded UGX " + amount
            + " for plot: " + plotLabel(project)
            + " | Type: " + paymentType
            + " | Amount owed after: UGX " + balanceAfter);
    }

    // ─── RECEIVABLE MANAGEMENT ───────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void moveToReceivable(UUID projectId) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        if (project.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot is already in receivable.");
        }

        BigDecimal outstanding = project.getTotalCost().subtract(project.getAmountPaid());
        if (outstanding.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot has no outstanding balance.");
        }

        project.setReceivable(true);
        project.setReceivableStartDate(LocalDateTime.now());
        project.setOriginalDebt(outstanding);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setStatus("RECEIVABLE");
        projectRepository.save(project);

        auditService.logAction("RECEIVABLE_TRIGGER",
            "Operator [" + getCurrentOperator() + "] manually moved plot "
            + plotLabel(project)
            + " to RECEIVABLE. Original debt frozen at: UGX " + outstanding);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void exitReceivable(UUID projectId, boolean capitalizeFees) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        if (!project.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot is not in receivable.");
        }

        BigDecimal titleCost   = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal totalPaid   = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        BigDecimal storageFees = project.getStorageFeesAccumulated() != null ? project.getStorageFeesAccumulated() : BigDecimal.ZERO;

        if (capitalizeFees && storageFees.compareTo(BigDecimal.ZERO) > 0) {
            // ADD TO TOTAL VALUE: client owes titleCost + storageFees going forward
            // amountPaid stays as-is; amount owed = (titleCost + fees) - paid
            project.setTotalCost(titleCost.add(storageFees));
        } else {
            // WAIVE FEES: reset amountPaid to only what was paid toward the title
            // Cap paid at titleCost so client cannot over-pay on exit
            BigDecimal titlePaymentPortion = totalPaid.min(titleCost);
            project.setAmountPaid(titlePaymentPortion);
        }

        project.setReceivable(false);
        project.setReceivableStartDate(null);
        project.setOriginalDebt(BigDecimal.ZERO);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setReceivableMonthsBilled(0);
        project.setStatus("ACTIVE");
        projectRepository.save(project);

        String feeAction = capitalizeFees ? "Storage fees ADDED TO TOTAL VALUE (UGX " + storageFees + ")" : "Storage fees WAIVED";
        auditService.logAction("RECEIVABLE_EXIT",
            "Operator [" + getCurrentOperator() + "] removed plot "
            + plotLabel(project)
            + " from RECEIVABLE. " + feeAction
            + ". Title total value: UGX " + project.getTotalCost() + ".");
    }

    // ─── INTAKE ───────────────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {
        // PHASE B (Section 18.10): LandProject is now built FIRST --
        // projectIndex, owners, location, and stage all exist
        // independently of a title. A LandTitle is only built and
        // attached SECOND, and only if title fields were actually
        // submitted. Using a non-blank plotNumber as that signal for
        // now -- a real "attach title later, on the final stage
        // checkbox" trigger is Phase D's job, not this phase's.
        boolean hasTitleFields = request.getPlotNumber() != null && !request.getPlotNumber().isBlank();
        String projectIndex = projectIndexService.generateNextIndex();

        BigDecimal initialPayment = request.getInitialPayment() != null
                ? request.getInitialPayment() : BigDecimal.ZERO;
        BigDecimal totalCost = request.getTotalCost() != null
                ? request.getTotalCost() : BigDecimal.ZERO;
        BigDecimal outstanding = totalCost.subtract(initialPayment);

        boolean startAsReceivable = request.isStartAsReceivable();

        LandTitle title = null;
        if (hasTitleFields) {
            title = LandTitle.builder()
                    .tenure(request.getTenure())
                    .plotNumber(request.getPlotNumber())
                    .physicalBoxNumber(request.getPhysicalBoxNumber())
                    .district(request.getDistrict())
                    .blockRoad(request.getBlockRoad())
                    .county(request.getCounty())
                    .volume(request.getVolume())
                    .folio(request.getFolio())
                    .instrumentNo(request.getInstrumentNo())
                    .surveyDate(request.getSurveyDate())
                    // Kept in sync on the deprecated LandTitle column too,
                    // for backward compatibility with anything still
                    // reading projectIndex off LandTitle instead of
                    // LandProject.
                    .projectIndex(projectIndex)
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
        }

        LandProject.LandProjectBuilder builder = LandProject.builder()
                .landTitle(title)
                .projectIndex(projectIndex)
                .district(request.getDistrict())
                .county(request.getCounty())
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

        if (request.getSelectedStages() != null && !request.getSelectedStages().isEmpty()) {
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

    @Transactional(rollbackFor = Exception.class)
    public LandProject updateProjectFull(UUID projectId, LandEntryRequest request) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("ARCHIVE_FAULT"));
        LandTitle title = project.getLandTitle();

        // PHASE B (Section 18.9.1): landTitle can now be null (a
        // titleless "folder" stage project). Skip the title-field
        // setters entirely when there is no title yet -- everything
        // else on this project (owners, cost, legacy flag) still
        // updates normally below. Real create-a-title-on-edit logic
        // is Phase D/E's job, not this phase's.
        if (title != null) {
            title.setPlotNumber(request.getPlotNumber());
            title.setTenure(request.getTenure());
            title.setBlockRoad(request.getBlockRoad());
            title.setDistrict(request.getDistrict());
            title.setCounty(request.getCounty());
            title.setVolume(request.getVolume());
            title.setFolio(request.getFolio());
            title.setInstrumentNo(request.getInstrumentNo());
            title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());
            title.setSurveyDate(request.getSurveyDate());
        }

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
                    person.setPhoneNumber(incoming.getPhone());
                }
                clientRepository.save(person);
                updatedRegistry.add(person);
            }
            project.setProprietors(updatedRegistry);
        }

        BigDecimal newTotalCost = request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO;
        project.setTotalCost(newTotalCost);
        project.setAmountPaid(request.getInitialPayment() != null ? request.getInitialPayment() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());

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
        return saved;
    }

    // ─── SOFT DELETE (formerly NUCLEAR DELETE) ───────────────────────────────
    // STAGE 3 FIX: this used to hard-delete the Cloudinary files, every payment
    // record, every note, and the DB row itself -- irreversible in one click.
    // It now only flags the row as deleted. Nothing else is touched, so a
    // mis-click is recoverable via restoreProject() below.

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void nuclearDelete(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = plotLabel(project);

        project.setDeleted(true);
        project.setDeletedAt(LocalDateTime.now());
        projectRepository.save(project);

        auditService.logAction("RECORD_DELETED",
            "Root user [" + getCurrentOperator() + "] deleted plot: " + plotNo);
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

    @Transactional
    public void logNewNote(UUID projectId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(content)
                .recordedBy(getCurrentOperator())
                .build();
        followUpRepository.save(entry);
        auditService.logAction("NOTE_ADDED",
            "Operator [" + getCurrentOperator() + "] added note to plot: "
            + project.getLandTitle().getPlotNumber());
    }

    @Transactional
    public void updateNote(UUID noteId, String content) {
        FollowUpLog log = followUpRepository.findById(noteId).orElseThrow();
        log.setNotes(content);
        followUpRepository.save(log);
        auditService.logAction("NOTE_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated a log entry.");
    }

    @Transactional
    public void removeNote(UUID noteId) {
        followUpRepository.deleteById(noteId);
        auditService.logAction("NOTE_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted a log entry.");
    }

    // ─── DOCUMENTS ────────────────────────────────────────────────────────────

    @Transactional
    public void addScansToProject(UUID projectId, MultipartFile[] scans) throws Exception {
        for (MultipartFile file : scans) {
            String path = fileStorageService.storeFile(file, projectId.toString());
            ProjectDocument doc = ProjectDocument.builder()
                    .projectId(projectId)
                    .fileName(file.getOriginalFilename())
                    .fileType(file.getContentType())
                    .filePath(path)
                    .uploadedBy(getCurrentOperator())
                    .build();
            documentRepository.save(doc);
        }
        auditService.logAction("DOCUMENT_UPLOADED",
            "Operator [" + getCurrentOperator() + "] uploaded " + scans.length
            + " document(s) to plot: " + projectId);
    }

    @Transactional
    public void removeDocument(UUID docId) {
        ProjectDocument doc = documentRepository.findById(docId).orElseThrow();
        fileStorageService.deleteFile(doc.getFilePath());
        documentRepository.delete(doc);
        auditService.logAction("DOCUMENT_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted file: " + doc.getFileName());
    }

    // ─── STAGE / RELEASE ──────────────────────────────────────────────────────

    @Transactional
    public void manualRealityOverride(UUID id, int targetStage) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        int oldStage = project.getCurrentStageIndex();
        project.setCurrentStageIndex(targetStage);
        if (targetStage >= 5) project.setStatus("COMPLETED");
        projectRepository.save(project);
        auditService.logAction("STAGE_OVERRIDE",
            "Operator [" + getCurrentOperator() + "] shifted plot "
            + plotLabel(project)
            + " from stage " + oldStage + " to stage " + targetStage);
    }

    @Transactional
    public void authorizeRelease(UUID id, String managerNote) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: Arrears Detected.");
        }
        // PHASE B (Section 18.9.1): landTitle can now be null.
        // Releasing implies a title exists to hand over -- silently
        // succeeding when there is nothing to release would be
        // misleading to staff, so this fails loudly instead of NPE-ing.
        if (project.getLandTitle() == null) {
            throw new BusinessException("RELEASE DENIED: This project has no title to release yet.");
        }
        project.getLandTitle().setReleased(true);
        project.setStatus("RELEASED");
        projectRepository.save(project);
        auditService.logAction("TITLE_RELEASED",
            "Operator [" + getCurrentOperator() + "] authorized handover for Plot: "
            + project.getLandTitle().getPlotNumber());
    }

    // ─── READ METHODS ─────────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setStoragePaused(UUID projectId, boolean paused) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        project.setStoragePaused(paused);
        projectRepository.save(project);
        String action = paused ? "PAUSED" : "RESUMED";
        auditService.logAction("STORAGE_FEE_" + action,
            "Operator [" + getCurrentOperator() + "] " + action.toLowerCase() + " monthly storage fees for plot: "
            + plotLabel(project)
            + " (monthly rate: UGX " + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : "50000 (default)") + ")");
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setStorageFeeOverride(UUID projectId, java.math.BigDecimal rate) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        project.setStorageFeeOverride(rate);
        projectRepository.save(project);
        auditService.logAction("STORAGE_RATE_CHANGED",
            "Operator [" + getCurrentOperator() + "] changed monthly storage fee to UGX " + rate
            + " for plot: " + plotLabel(project)
            + " (previously UGX " + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : "50000 (default)") + ")");
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setAccumulatedFees(UUID projectId, java.math.BigDecimal amount) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        java.math.BigDecimal old = project.getStorageFeesAccumulated();
        project.setStorageFeesAccumulated(amount);
        projectRepository.save(project);
        auditService.logAction("STORAGE_FEES_ADJUSTED",
            "Operator [" + getCurrentOperator() + "] manually adjusted accumulated storage fees from UGX " + old
            + " to UGX " + amount + " for plot: " + plotLabel(project));
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setNegotiationDeadline(UUID projectId, String deadlineStr) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (deadlineStr == null || deadlineStr.isBlank()) {
            project.setNegotiationDeadline(null);
            // Resume fees if deadline cleared
            project.setStoragePaused(false);
            auditService.logAction("NEGOTIATION_DEADLINE_CLEARED",
                "Operator [" + getCurrentOperator() + "] cleared negotiation deadline for plot: "
                + plotLabel(project) + " -- storage fees resumed.");
        } else {
            java.time.LocalDateTime deadline = java.time.LocalDate.parse(deadlineStr)
                    .atTime(23, 59, 59);
            project.setNegotiationDeadline(deadline);
            // Auto-pause fees while negotiating
            project.setStoragePaused(true);
            auditService.logAction("NEGOTIATION_DEADLINE_SET",
                "Operator [" + getCurrentOperator() + "] set negotiation deadline to " + deadlineStr
                + " for plot: " + plotLabel(project)
                + " -- storage fees paused until then.");
        }
        projectRepository.save(project);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setReceivableStartOverride(UUID projectId, String startDateStr) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        java.time.LocalDateTime startDate = java.time.LocalDate.parse(startDateStr).atStartOfDay();
        project.setReceivableStartOverride(startDate);
        // Apply the override to the actual receivable start date so fees calculate from correct date
        project.setReceivableStartDate(startDate);
        projectRepository.save(project);
        auditService.logAction("RECEIVABLE_START_OVERRIDDEN",
            "Operator [" + getCurrentOperator() + "] set receivable start date to " + startDateStr
            + " for plot: " + plotLabel(project));
    }

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
        return projectRepository.findAll(pageable);
    }
}