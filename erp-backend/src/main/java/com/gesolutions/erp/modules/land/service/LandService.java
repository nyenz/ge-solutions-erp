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

/**
 * NYENZ ERP - MASTER CABINET ENGINE (V24.1 - PRODUCTION FINAL)
 * 
 * Physically replaces generic "MANAGER" identifiers with actual authenticated usernames.
 * FIXED: Restored wrapper methods missing in previous build.
 */
@Service
@RequiredArgsConstructor
public class LandService {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;
    private final ProjectDocumentRepository documentRepository;
    private final ClientRepository clientRepository;
    private final ClientService clientService;
    private final PaymentEngineService paymentEngine;
    private final FileStorageService fileStorageService;
    private final AuditService auditService;

    
    /**
     * INTERNAL HELPER: RECOVER CURRENT OPERATOR NAME
     */
    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    @Transactional
    public void logUnlockAction(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        String plotNo = project.getLandTitle().getPlotNumber();
        auditService.logAction("HARDWARE_UNLOCK", "Operator [" + getCurrentOperator() + "] initiated Master Hardware Override for plot: " + plotNo);
    }

    @Transactional(readOnly = true)
    public ProjectDeepDetailDTO getProjectDeepDetail(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow(() -> new BusinessException("VAULT FAULT"));
        List<FollowUpLog> notes = followUpRepository.findByProjectIdOrderByTimestampDesc(id);
        List<ProjectDocument> documents = documentRepository.findByProjectId(id);
        BigDecimal cost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal paid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        BigDecimal remaining = cost.subtract(paid);
        double percent = cost.compareTo(BigDecimal.ZERO) > 0 ? paid.divide(cost, 4, RoundingMode.HALF_UP).doubleValue() * 100 : 0;
        return ProjectDeepDetailDTO.builder().project(project).notes(notes).documents(documents).remainingBalance(remaining).collectionPercentage(percent).build();
    }

    @Transactional(rollbackFor = Exception.class)
    public LandProject updateProjectFull(UUID projectId, LandEntryRequest request) {
        LandProject project = projectRepository.findById(projectId).orElseThrow(() -> new BusinessException("ARCHIVE_FAULT"));
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
                Client person = clientRepository.findByPhoneNumber(incoming.getPhone()).orElseGet(() -> clientService.findOrCreateClient(incoming.getFullName(), incoming.getPhone(), incoming.getEmail()));
                person.setFullName(incoming.getFullName().toUpperCase());
                person.setNationalId(incoming.getNationalId() != null ? incoming.getNationalId().toUpperCase() : null);
                person.setEmail(incoming.getEmail() != null ? incoming.getEmail().toLowerCase() : null);
                person.setHomeAddress(incoming.getAddress());
                clientRepository.save(person);
                updatedRegistry.add(person);
            }
            project.setProprietors(updatedRegistry);
        }

        project.setTotalCost(request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO);
        project.setAmountPaid(request.getInitialPayment() != null ? request.getInitialPayment() : BigDecimal.ZERO);
        project.setPlanType(request.getPlanType());
        project.setWeeklyInstallment(request.getWeeklyInstallment());
        project.setLegacy(request.isLegacy());

        LandProject saved = projectRepository.save(project);
        auditService.logAction("MASTER_REWRITE", "Operator [" + getCurrentOperator() + "] modified Binder: " + title.getPlotNumber());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void nuclearDelete(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = project.getLandTitle().getPlotNumber();
        List<ProjectDocument> docs = documentRepository.findByProjectId(id);
        for (ProjectDocument doc : docs) { fileStorageService.deleteFile(doc.getFilePath()); }
        projectRepository.delete(project);
        auditService.logAction("NUCLEAR_PURGE", "ROOT USER [" + getCurrentOperator() + "] DELETED DOSSIER: " + plotNo);
    }

    /* ───── NOTE LOGIC (RESTORED) ───── */

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
                .timestamp(LocalDateTime.now()).build();
        followUpRepository.save(entry);
    }

    @Transactional
    public void logNewNote(UUID projectId, String content) {
        logFollowUp(projectId, content);
    }

    @Transactional
    public void updateNote(UUID noteId, String content) {
        FollowUpLog log = followUpRepository.findById(noteId).orElseThrow();
        log.setNotes(content);
        followUpRepository.save(log);
        auditService.logAction("INTEL_REWRITE", "Operator [" + getCurrentOperator() + "] updated a log entry.");
    }

    @Transactional
    public void removeNote(UUID noteId) {
        followUpRepository.deleteById(noteId);
        auditService.logAction("INTEL_DISPOSAL", "Operator [" + getCurrentOperator() + "] deleted a log entry.");
    }

    /* ───── OPERATIONAL LOGIC ───── */

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
    }

    @Transactional
    public void removeDocument(UUID docId) {
        ProjectDocument doc = documentRepository.findById(docId).orElseThrow();
        fileStorageService.deleteFile(doc.getFilePath());
        documentRepository.delete(doc);
        auditService.logAction("VAULT_DISPOSAL", "Operator [" + getCurrentOperator() + "] deleted file: " + doc.getFileName());
    }

    @Transactional
    public void manualRealityOverride(UUID id, int targetStage) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        project.setCurrentStageIndex(targetStage);
        if (targetStage >= 5) project.setStatus("COMPLETED");
        projectRepository.save(project);
        auditService.logAction("STAGE_OVERRIDE", "Operator [" + getCurrentOperator() + "] shifted stage to: " + targetStage);
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
        auditService.logAction("FINAL_RELEASE", "Operator [" + getCurrentOperator() + "] authorized handover for Plot: " + project.getLandTitle().getPlotNumber());
    }

    @Transactional(rollbackFor = Exception.class)
    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {
        LandTitle title = LandTitle.builder().tenure(request.getTenure()).plotNumber(request.getPlotNumber()).physicalBoxNumber(request.getPhysicalBoxNumber()).district(request.getDistrict()).blockRoad(request.getBlockRoad()).county(request.getCounty()).volume(request.getVolume()).folio(request.getFolio()).instrumentNo(request.getInstrumentNo()).build();
        LandProject project = LandProject.builder().landTitle(title).totalCost(request.getTotalCost()).amountPaid(request.getInitialPayment()).weeklyInstallment(request.getWeeklyInstallment()).planType(request.getPlanType()).isLegacy(request.isLegacy()).status("ACTIVE").build();
        if (request.getOwners() != null) {
            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {
                Client c = clientService.findOrCreateClient(o.getFullName(), o.getPhone(), o.getEmail());
                c.setNationalId(o.getNationalId()); c.setHomeAddress(o.getAddress());
                project.addProprietor(c);
            }
        }
        LandProject saved = projectRepository.save(project);
        if (scans != null) addScansToProject(saved.getId(), scans); 
        if (request.getNotes() != null) {
            for (LandEntryRequest.NoteRequest noteReq : request.getNotes()) {
                if (noteReq.getContent() != null && !noteReq.getContent().trim().isEmpty()) {
                    logFollowUp(saved.getId(), "INTAKE NOTE: " + noteReq.getContent());
                }
            }
        }
        paymentEngine.generateSchedule(saved, request.getPlanType().contains("2") ? 24 : 12);
        auditService.logAction("INTAKE", "Operator [" + getCurrentOperator() + "] Ingested Binder: " + title.getPlotNumber());
        return saved;
    }

    @Transactional(readOnly = true)
    public List<ProjectDocument> getProjectDocuments(UUID projectId) { return documentRepository.findByProjectId(projectId); }
    @Transactional(readOnly = true)
    public List<FollowUpLog> getProjectNotes(UUID projectId) { return followUpRepository.findByProjectIdOrderByTimestampDesc(projectId); }
    @Transactional(readOnly = true)
    public Page<LandProject> getGlobalLedger(Pageable pageable) { return projectRepository.findAll(pageable); }
}