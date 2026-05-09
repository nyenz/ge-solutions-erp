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

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    // ─── UNLOCK LOG ───────────────────────────────────────────────────────────

    @Transactional
    public void logUnlockAction(UUID id) {
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        auditService.logAction("HARDWARE_UNLOCK",
            "Operator [" + getCurrentOperator() + "] initiated Master Hardware Override for plot: "
            + project.getLandTitle().getPlotNumber());
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
        if (project.isBacklog()) {
            remaining = project.backlogTotalOwed();
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
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        String operator = getCurrentOperator();
        String paymentType = project.isBacklog() ? "BACKLOG_PARTIAL" : "STANDARD";

        BigDecimal newAmountPaid = project.getAmountPaid().add(amount);
        project.setAmountPaid(newAmountPaid);
        project.setLastPaymentDate(LocalDateTime.now());

        BigDecimal balanceAfter;
        if (project.isBacklog()) {
            balanceAfter = project.backlogTotalOwed();
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

        // Auto-exit backlog if fully paid
        if (project.isBacklog() && balanceAfter.compareTo(BigDecimal.ZERO) <= 0) {
            project.setBacklog(false);
            project.setStatus("ACTIVE");
            projectRepository.save(project);
            auditService.logAction("BACKLOG_EXIT",
                "Operator [" + operator + "] — Plot " + project.getLandTitle().getPlotNumber()
                + " EXITED BACKLOG after full payment clearance.");
        } else {
            projectRepository.save(project);
        }

        auditService.logAction("PAYMENT_RECORDED",
            "Operator [" + operator + "] recorded UGX " + amount
            + " for plot: " + project.getLandTitle().getPlotNumber()
            + " | Type: " + paymentType
            + " | Balance after: UGX " + balanceAfter);
    }

    // ─── BACKLOG MANAGEMENT ───────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void moveToBacklog(UUID projectId) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        if (project.isBacklog()) {
            throw new BusinessException("BACKLOG_FAULT: Plot is already in backlog.");
        }

        BigDecimal outstanding = project.getTotalCost().subtract(project.getAmountPaid());
        if (outstanding.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("BACKLOG_FAULT: Plot has no outstanding balance.");
        }

        project.setBacklog(true);
        project.setBacklogStartDate(LocalDateTime.now());
        project.setOriginalDebt(outstanding);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setStatus("BACKLOG");
        projectRepository.save(project);

        auditService.logAction("BACKLOG_TRIGGER",
            "Operator [" + getCurrentOperator() + "] manually moved plot "
            + project.getLandTitle().getPlotNumber()
            + " to BACKLOG. Original debt frozen at: UGX " + outstanding);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void exitBacklog(UUID projectId) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        if (!project.isBacklog()) {
            throw new BusinessException("BACKLOG_FAULT: Plot is not in backlog.");
        }

        project.setBacklog(false);
        project.setBacklogStartDate(null);
        project.setOriginalDebt(BigDecimal.ZERO);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setStatus("ACTIVE");
        projectRepository.save(project);

        auditService.logAction("BACKLOG_EXIT",
            "Operator [" + getCurrentOperator() + "] manually removed plot "
            + project.getLandTitle().getPlotNumber()
            + " from BACKLOG. Storage fees cleared.");
    }

    // ─── INTAKE ───────────────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {
        LandTitle title = LandTitle.builder()
                .tenure(request.getTenure())
                .plotNumber(request.getPlotNumber())
                .physicalBoxNumber(request.getPhysicalBoxNumber())
                .district(request.getDistrict())
                .blockRoad(request.getBlockRoad())
                .county(request.getCounty())
                .volume(request.getVolume())
                .folio(request.getFolio())
                .instrumentNo(request.getInstrumentNo())
                .build();

        BigDecimal initialPayment = request.getInitialPayment() != null
                ? request.getInitialPayment() : BigDecimal.ZERO;
        BigDecimal totalCost = request.getTotalCost() != null
                ? request.getTotalCost() : BigDecimal.ZERO;
        BigDecimal outstanding = totalCost.subtract(initialPayment);

        boolean startAsBacklog = request.isStartAsBacklog();

        LandProject.LandProjectBuilder builder = LandProject.builder()
                .landTitle(title)
                .totalCost(totalCost)
                .amountPaid(initialPayment)
                .isLegacy(request.isLegacy())
                .status(startAsBacklog ? "BACKLOG" : "ACTIVE");

        if (startAsBacklog && outstanding.compareTo(BigDecimal.ZERO) > 0) {
            builder.isBacklog(true)
                   .backlogStartDate(LocalDateTime.now())
                   .originalDebt(outstanding)
                   .storageFeesAccumulated(BigDecimal.ZERO);
        }

        LandProject project = builder.build();

        if (request.getOwners() != null) {
            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {
                Client c = clientService.findOrCreateClient(o.getFullName(), o.getPhone(), o.getEmail());
                c.setNationalId(o.getNationalId());
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

        String backlogNote = startAsBacklog ? " [ENTERED AS BACKLOG]" : "";
        auditService.logAction("INTAKE",
            "Operator [" + getCurrentOperator() + "] ingested binder: "
            + title.getPlotNumber() + backlogNote);

        if (startAsBacklog) {
            auditService.logAction("BACKLOG_TRIGGER",
                "Operator [" + getCurrentOperator() + "] flagged plot "
                + title.getPlotNumber() + " as BACKLOG at intake. Debt: UGX " + outstanding);
        }

        return saved;
    }

    // ─── FULL UPDATE ──────────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public LandProject updateProjectFull(UUID projectId, LandEntryRequest request) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("ARCHIVE_FAULT"));
        LandTitle title = project.getLandTitle();

        title.setPlotNumber(request.getPlotNumber());
        title.setTenure(request.getTenure());
        title.setBlockRoad(request.getBlockRoad());
        title.setDistrict(request.getDistrict());
        title.setCounty(request.getCounty());
        title.setVolume(request.getVolume());
        title.setFolio(request.getFolio());
        title.setInstrumentNo(request.getInstrumentNo());
        title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());

        if (request.getOwners() != null) {
            Set<Client> updatedRegistry = new HashSet<>();
            for (LandEntryRequest.OwnerRequest incoming : request.getOwners()) {
                Client person = clientRepository.findByPhoneNumber(incoming.getPhone())
                        .orElseGet(() -> clientService.findOrCreateClient(
                                incoming.getFullName(), incoming.getPhone(), incoming.getEmail()));
                person.setFullName(incoming.getFullName().toUpperCase());
                person.setNationalId(incoming.getNationalId() != null
                        ? incoming.getNationalId().toUpperCase() : null);
                person.setEmail(incoming.getEmail() != null
                        ? incoming.getEmail().toLowerCase() : null);
                person.setHomeAddress(incoming.getAddress());
                clientRepository.save(person);
                updatedRegistry.add(person);
            }
            project.setProprietors(updatedRegistry);
        }

        project.setTotalCost(request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());

        LandProject saved = projectRepository.save(project);
        auditService.logAction("MASTER_REWRITE",
            "Operator [" + getCurrentOperator() + "] modified Binder: "
            + title.getPlotNumber());
        return saved;
    }

    // ─── NUCLEAR DELETE ───────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void nuclearDelete(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = project.getLandTitle().getPlotNumber();

        List<ProjectDocument> docs = documentRepository.findByProjectId(id);
        for (ProjectDocument doc : docs) {
            fileStorageService.deleteFile(doc.getFilePath());
        }

        try {
            fileStorageService.deleteFolder("ge_solutions/" + id.toString());
        } catch (Exception e) {
            System.err.println(">>> FOLDER DELETE WARNING: " + e.getMessage());
        }

        projectRepository.delete(project);
        auditService.logAction("NUCLEAR_PURGE",
            "ROOT USER [" + getCurrentOperator() + "] DELETED DOSSIER: " + plotNo);
    }

    // ─── FOLLOW-UP / NOTES ────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public void logFollowUp(UUID projectId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();
        if (project.getProprietors() != null) {
            for (Client owner : project.getProprietors()) {
                if (owner != null && owner.getId() != null) {
                    try { clientService.logManagerContact(owner.getId()); } catch (Exception e) {}
                }
            }
        }
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(content)
                .recordedBy(getCurrentOperator())
                .build();
        followUpRepository.save(entry);
        auditService.logAction("RECOVERY_SYNC",
            "Operator [" + getCurrentOperator() + "] logged call for plot: "
            + project.getLandTitle().getPlotNumber());
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
        auditService.logAction("INTEL_REWRITE",
            "Operator [" + getCurrentOperator() + "] updated a log entry.");
    }

    @Transactional
    public void removeNote(UUID noteId) {
        followUpRepository.deleteById(noteId);
        auditService.logAction("INTEL_DISPOSAL",
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
        auditService.logAction("VAULT_DISPOSAL",
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
            + project.getLandTitle().getPlotNumber()
            + " from stage " + oldStage + " to stage " + targetStage);
    }

    @Transactional
    public void authorizeRelease(UUID id, String managerNote) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: Arrears Detected.");
        }
        project.getLandTitle().setReleased(true);
        project.setStatus("RELEASED");
        projectRepository.save(project);
        auditService.logAction("FINAL_RELEASE",
            "Operator [" + getCurrentOperator() + "] authorized handover for Plot: "
            + project.getLandTitle().getPlotNumber());
    }

    // ─── READ METHODS ─────────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setStoragePaused(UUID projectId, boolean paused) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        project.setStoragePaused(paused);
        projectRepository.save(project);
        String action = paused ? "PAUSED" : "RESUMED";
        auditService.logAction("STORAGE_FEE_" + action,
            "Operator [" + getCurrentOperator() + "] " + action + " storage fees for plot: "
            + project.getLandTitle().getPlotNumber());
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setStorageFeeOverride(UUID projectId, java.math.BigDecimal rate) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        project.setStorageFeeOverride(rate);
        projectRepository.save(project);
        auditService.logAction("STORAGE_RATE_CHANGED",
            "Operator [" + getCurrentOperator() + "] set monthly storage fee to UGX " + rate
            + " for plot: " + project.getLandTitle().getPlotNumber());
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public void setAccumulatedFees(UUID projectId, java.math.BigDecimal amount) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        java.math.BigDecimal old = project.getStorageFeesAccumulated();
        project.setStorageFeesAccumulated(amount);
        projectRepository.save(project);
        auditService.logAction("STORAGE_FEES_ADJUSTED",
            "Operator [" + getCurrentOperator() + "] changed accumulated fees from UGX " + old
            + " to UGX " + amount + " for plot: " + project.getLandTitle().getPlotNumber());
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