#!/usr/bin/env python3
"""
fix12.py — make the deploy green + Ledger resilient.
1) Re-issues the 5 backend files my scripts touched as ONE consistent set
   (LandController index-fix, StageTemplate service+controller pair,
   LandTitle compile-safe shape, DataInitializer with normalize + 7 sample
   projects + sample docs + PHASE G drops of the 5 retired columns only).
2) LedgerPage: auto-retry once after 5s on sync fault (free-tier cold start)
   before showing LEDGER SYNC FAULT.
Run: py fix12.py
"""
import sys, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WROTE, FAILED = [], []

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    try: p.write_text(content, encoding="utf-8"); WROTE.append(rel)
    except Exception as e: FAILED.append((rel, str(e)))

def patch(rel, old, new):
    p = ROOT / rel
    try: text = p.read_text(encoding="utf-8")
    except Exception as e: FAILED.append((rel, "read: " + str(e))); return
    if old not in text:
        FAILED.append((rel, "ANCHOR NOT FOUND: " + old[:70].replace("\n", "\\n"))); return
    text = text.replace(old, new, 1)
    try: p.write_text(text, encoding="utf-8"); WROTE.append(rel + " (patched)")
    except Exception as e: FAILED.append((rel, str(e)))

# =====================================================================
# 1) LandController.java — one mapping per method (the index fix)
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.dto.*;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectDocument;
import com.gesolutions.erp.modules.land.service.LandService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/land")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class LandController {

    private final LandService landService;

    // FIX: was stacked with @PostMapping unlock-log on one method, so it
    // never registered and the Index field always 404'd. One mapping each.
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

    @PostMapping("/projects/{id}/unlock-log")
    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/notes")
    public ResponseEntity<List<FollowUpLog>> getProjectNotes(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectNotes(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/follow-up")
    public ResponseEntity<java.util.Map<String, Object>> logContact(@PathVariable UUID id,
                                            @RequestParam UUID ownerId,
                                            @RequestParam String content) {
        return ResponseEntity.ok(landService.logFollowUp(id, ownerId, content));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/ingest", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LandProject> ingestTitle(
            @RequestPart("data") String jsonData,
            @RequestPart(value = "scans", required = false) MultipartFile[] scans) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        LandEntryRequest request = mapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(landService.atomicIntake(request, scans));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/deep")
    public ResponseEntity<ProjectDeepDetailDTO> getProjectDeepDetail(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDeepDetail(id));
    }

    @PutMapping("/projects/{id}/full-update")
    public ResponseEntity<LandProject> updateProjectFull(
            @PathVariable UUID id, @RequestBody LandEntryRequest request) {
        return ResponseEntity.ok(landService.updateProjectFull(id, request));
    }

    @DeleteMapping("/projects/{id}")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id) {
        landService.nuclearDelete(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/projects/{id}/restore")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> restoreAsset(@PathVariable UUID id) {
        landService.restoreProject(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/deleted")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<List<LandProject>> getDeletedProjects() {
        return ResponseEntity.ok(landService.getDeletedProjects());
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/documents")
    public ResponseEntity<List<ProjectDocument>> getDocuments(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDocuments(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/projects/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> addExtraDocuments(
            @PathVariable UUID id,
            @RequestParam("scans") MultipartFile[] scans) throws Exception {
        landService.addScansToProject(id, scans);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/documents/{docId}")
    public ResponseEntity<Void> deleteDocument(@PathVariable UUID docId) {
        landService.removeDocument(docId);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/notes")
    public ResponseEntity<Void> addNote(@PathVariable UUID id, @RequestParam String content) {
        landService.logNewNote(id, content);
        return ResponseEntity.ok().build();
    }

    @PutMapping("/notes/{noteId}")
    public ResponseEntity<Void> updateNote(@PathVariable UUID noteId, @RequestParam String content) {
        landService.updateNote(noteId, content);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/notes/{noteId}")
    public ResponseEntity<Void> deleteNote(@PathVariable UUID noteId) {
        landService.removeNote(noteId);
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/projects/{id}/reality-override")
    public ResponseEntity<Void> manualRealityOverride(
            @PathVariable UUID id, @RequestParam int targetStage) {
        landService.manualRealityOverride(id, targetStage);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/ledger")
    public ResponseEntity<Page<LandProject>> getLedger(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(page, size)));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/bulk-mark-title-produced")
    public ResponseEntity<Integer> bulkMarkTitleProduced(@RequestBody List<UUID> projectIds) {
        return ResponseEntity.ok(landService.bulkMarkTitleProduced(projectIds));
    }

    @PatchMapping("/projects/{id}/release")
    public ResponseEntity<Void> authorizeRelease(
            @PathVariable UUID id,
            @RequestParam(required = false) String managerNote) {
        landService.authorizeRelease(id, managerNote);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/receivable")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> moveToReceivable(@PathVariable UUID id) {
        landService.moveToReceivable(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/exit-receivable")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitReceivable(@PathVariable UUID id,
                                            @RequestParam(defaultValue = "false") boolean capitalizeFees) {
        landService.exitReceivable(id, capitalizeFees);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/exit-receivable-capitalize")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitReceivableCapitalize(@PathVariable UUID id) {
        landService.exitReceivable(id, true);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }

    @PostMapping("/projects/{id}/payment")
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes) {
        landService.recordPayment(id, amount, notes);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-pause")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,
                                                   @RequestParam boolean paused) {
        landService.setStoragePaused(id, paused);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-rate")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal rate) {
        landService.setStorageFeeOverride(id, rate);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount) {
        landService.setAccumulatedFees(id, amount);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/negotiation-deadline")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setNegotiationDeadline(@PathVariable UUID id,
                                                        @RequestParam(required = false) String deadline) {
        landService.setNegotiationDeadline(id, deadline);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/receivable-start")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setReceivableStartOverride(@PathVariable UUID id,
                                                         @RequestParam String startDate) {
        landService.setReceivableStartOverride(id, startDate);
        return ResponseEntity.ok().build();
    }
}
""")

# =====================================================================
# 2) StageTemplateService.java — normalize + bulk, matched pair
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.ProjectStage;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.dto.ProjectStageRequest;
import com.gesolutions.erp.modules.land.repository.ProjectStageRepository;
import com.gesolutions.erp.modules.land.repository.StageTemplateRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class StageTemplateService {

    private final StageTemplateRepository templateRepository;
    private final ProjectStageRepository projectStageRepository;
    private final AuditService auditService;

    private static final String[] DEFAULT_STAGES = {
        "Field Work",
        "Deed Plan",
        "LC Inspection",
        "District Land Board Approval",
        "Tax Assessment and Stamp Duty",
        "Registration and Title Issuance"
    };

    private static final java.util.Set<String> DEFAULT_STAGE_NAMES =
            java.util.Set.of(DEFAULT_STAGES);

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    @Transactional
    public void seedDefaultStagesIfEmpty() {
        if (templateRepository.count() > 0) return;
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            templateRepository.save(StageTemplate.builder()
                    .stageName(name).defaultCost(BigDecimal.ZERO)
                    .displayOrder(order++).isActive(true).build());
        }
        System.out.println(">>> [STAGE_TEMPLATE] Seeded " + DEFAULT_STAGES.length + " default stages.");
    }

    @Transactional(readOnly = true)
    public List<StageTemplate> getActiveTemplate() {
        return templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public StageTemplate addTemplateStage(String stageName, BigDecimal defaultCost, Integer displayOrder) {
        if (stageName == null || stageName.isBlank()) {
            throw new BusinessException("STAGE_NAME_REQUIRED: A stage name is required.");
        }
        StageTemplate stage = StageTemplate.builder()
                .stageName(stageName.trim())
                .defaultCost(defaultCost != null ? defaultCost : BigDecimal.ZERO)
                .displayOrder(displayOrder != null ? displayOrder : (int) templateRepository.count() + 1)
                .isActive(true)
                .build();
        StageTemplate saved = templateRepository.save(stage);
        auditService.logAction("STAGE_TEMPLATE_ADDED",
            "Operator [" + getCurrentOperator() + "] added master stage: " + stage.getStageName());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public StageTemplate updateTemplateStage(UUID id, String stageName, BigDecimal defaultCost, Integer displayOrder) {
        StageTemplate stage = templateRepository.findById(id)
                .orElseThrow(() -> new BusinessException("STAGE_TEMPLATE_NOT_FOUND"));
        if (stageName != null && !stageName.isBlank()) stage.setStageName(stageName.trim());
        if (defaultCost != null) stage.setDefaultCost(defaultCost);
        if (displayOrder != null) stage.setDisplayOrder(displayOrder);
        StageTemplate saved = templateRepository.save(stage);
        auditService.logAction("STAGE_TEMPLATE_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated master stage: " + stage.getStageName());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void deactivateTemplateStage(UUID id) {
        StageTemplate stage = templateRepository.findById(id)
                .orElseThrow(() -> new BusinessException("STAGE_TEMPLATE_NOT_FOUND"));
        stage.setActive(false);
        templateRepository.save(stage);
        auditService.logAction("STAGE_TEMPLATE_REMOVED",
            "Operator [" + getCurrentOperator() + "] removed master stage from checklist: " + stage.getStageName());
    }

    @Transactional(readOnly = true)
    public List<ProjectStage> getProjectStages(UUID projectId) {
        return projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
    }

    @Transactional
    public List<ProjectStage> attachStagesToProject(UUID projectId, List<ProjectStageRequest> requests) {
        if (requests == null || requests.isEmpty()) return List.of();
        int startOrder = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId).size();
        java.util.List<ProjectStage> created = new java.util.ArrayList<>();
        int i = 0;
        for (ProjectStageRequest req : requests) {
            String name; BigDecimal cost;
            if (req.isCustom()) {
                if (req.getStageName() == null || req.getStageName().isBlank()) {
                    throw new BusinessException("STAGE_NAME_REQUIRED: Custom stage needs a name.");
                }
                name = req.getStageName().trim();
                cost = req.getCost() != null ? req.getCost() : BigDecimal.ZERO;
            } else {
                if (req.getStageTemplateId() == null) throw new BusinessException("STAGE_TEMPLATE_ID_REQUIRED");
                StageTemplate template = templateRepository.findById(UUID.fromString(req.getStageTemplateId()))
                        .orElseThrow(() -> new BusinessException("STAGE_TEMPLATE_NOT_FOUND"));
                name = template.getStageName();
                cost = req.getCost() != null ? req.getCost() : template.getDefaultCost();
            }
            created.add(projectStageRepository.save(ProjectStage.builder()
                    .projectId(projectId).stageName(name).cost(cost).notes(req.getNotes())
                    .isCustom(req.isCustom()).isCompleted(req.isCompleted())
                    .displayOrder(startOrder + (i++))
                    .build()));
        }
        auditService.logAction("PROJECT_STAGES_ATTACHED",
            "Operator [" + getCurrentOperator() + "] attached " + created.size()
            + " stage(s) to project: " + projectId);
        return created;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStage toggleStageCompletion(UUID stageId, boolean completed) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        stage.setCompleted(completed);
        stage.setCompletedAt(completed ? LocalDateTime.now() : null);
        ProjectStage saved = projectStageRepository.save(stage);
        auditService.logAction("PROJECT_STAGE_STATUS_CHANGED",
            "Operator [" + getCurrentOperator() + "] marked stage \"" + stage.getStageName()
            + "\" as " + (completed ? "COMPLETE" : "NOT COMPLETE") + " on project: " + stage.getProjectId());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStage updateStageCostAndNotes(UUID stageId, BigDecimal cost, String notes) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        if (cost != null) stage.setCost(cost);
        if (notes != null) stage.setNotes(notes);
        ProjectStage saved = projectStageRepository.save(stage);
        auditService.logAction("PROJECT_STAGE_COST_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated cost/notes on stage \"" + stage.getStageName()
            + "\" for project: " + stage.getProjectId());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void removeProjectStage(UUID stageId) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        projectStageRepository.delete(stage);
        auditService.logAction("PROJECT_STAGE_REMOVED",
            "Operator [" + getCurrentOperator() + "] removed stage \"" + stage.getStageName()
            + "\" from project: " + stage.getProjectId());
    }

    @Transactional
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }

    /** Boot-time: master checklist = exactly the 6 defaults, in order, no dupes. */
    @Transactional
    public void normalizeToDefaultStages() {
        List<StageTemplate> active = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
        java.util.Map<String, StageTemplate> kept = new java.util.LinkedHashMap<>();
        for (StageTemplate t : active) {
            String name = t.getStageName();
            boolean isDefault = name != null && DEFAULT_STAGE_NAMES.contains(name);
            if (!isDefault || kept.containsKey(name)) {
                t.setActive(false);
                templateRepository.save(t);
            } else {
                kept.put(name, t);
            }
        }
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = kept.get(name);
            if (stage == null) {
                templateRepository.save(StageTemplate.builder()
                        .stageName(name).defaultCost(BigDecimal.ZERO)
                        .displayOrder(order).isActive(true).build());
            } else if (stage.getDisplayOrder() == null || stage.getDisplayOrder() != order) {
                stage.setDisplayOrder(order);
                templateRepository.save(stage);
            }
            order++;
        }
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> reorderTemplateStages(List<UUID> orderedIds) {
        if (orderedIds == null || orderedIds.isEmpty()) return List.of();
        List<StageTemplate> found = templateRepository.findAllById(orderedIds);
        java.util.Map<UUID, StageTemplate> byId = found.stream()
                .collect(java.util.stream.Collectors.toMap(StageTemplate::getId, s -> s));
        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (UUID id : orderedIds) {
            StageTemplate stage = byId.get(id);
            if (stage == null) continue;
            stage.setDisplayOrder(order++);
            toSave.add(stage);
        }
        return templateRepository.saveAll(toSave);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void bulkDeleteTemplateStages(List<UUID> ids) {
        if (ids == null || ids.isEmpty()) return;
        List<StageTemplate> toDelete = templateRepository.findAllById(ids);
        if (!toDelete.isEmpty()) templateRepository.deleteAllInBatch(toDelete);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> restoreDefaultStages() {
        List<StageTemplate> current = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
        List<StageTemplate> nonDefault = current.stream()
                .filter(s -> !DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .toList();
        if (!nonDefault.isEmpty()) templateRepository.deleteAllInBatch(nonDefault);
        java.util.Map<String, StageTemplate> keepByName = current.stream()
                .filter(s -> DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .collect(java.util.stream.Collectors.toMap(StageTemplate::getStageName, s -> s, (a, b) -> a));
        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = keepByName.get(name);
            if (stage == null) {
                stage = StageTemplate.builder().stageName(name).defaultCost(BigDecimal.ZERO)
                        .displayOrder(order).isActive(true).build();
            } else {
                stage.setDisplayOrder(order);
            }
            order++;
            toSave.add(stage);
        }
        return templateRepository.saveAll(toSave);
    }
}
""")

# =====================================================================
# 3) StageTemplateController.java — matched pair
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.ProjectStage;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.dto.ProjectStageRequest;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class StageTemplateController {

    private final StageTemplateService stageTemplateService;

    @GetMapping("/stage-templates")
    public ResponseEntity<List<StageTemplate>> getTemplate() {
        return ResponseEntity.ok(stageTemplateService.getActiveTemplate());
    }

    @PostMapping("/stage-templates")
    public ResponseEntity<StageTemplate> addTemplateStage(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("stageName");
        BigDecimal cost = body.get("defaultCost") != null
                ? new BigDecimal(body.get("defaultCost").toString()) : BigDecimal.ZERO;
        Integer order = body.get("displayOrder") != null
                ? Integer.valueOf(body.get("displayOrder").toString()) : null;
        return ResponseEntity.ok(stageTemplateService.addTemplateStage(name, cost, order));
    }

    @PutMapping("/stage-templates/{id}")
    public ResponseEntity<StageTemplate> updateTemplateStage(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        String name = (String) body.get("stageName");
        BigDecimal cost = body.get("defaultCost") != null
                ? new BigDecimal(body.get("defaultCost").toString()) : null;
        Integer order = body.get("displayOrder") != null
                ? Integer.valueOf(body.get("displayOrder").toString()) : null;
        return ResponseEntity.ok(stageTemplateService.updateTemplateStage(id, name, cost, order));
    }

    @DeleteMapping("/stage-templates/{id}")
    public ResponseEntity<Void> deactivateTemplateStage(@PathVariable UUID id) {
        stageTemplateService.deactivateTemplateStage(id);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/stage-templates/reorder")
    public ResponseEntity<List<StageTemplate>> reorderTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> orderedIds = (body.getOrDefault("orderedIds", List.of())).stream()
                .map(UUID::fromString).toList();
        return ResponseEntity.ok(stageTemplateService.reorderTemplateStages(orderedIds));
    }

    @DeleteMapping("/stage-templates/bulk")
    public ResponseEntity<Void> bulkDeleteTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> ids = (body.getOrDefault("ids", List.of())).stream()
                .map(UUID::fromString).toList();
        stageTemplateService.bulkDeleteTemplateStages(ids);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/stage-templates/restore-defaults")
    public ResponseEntity<List<StageTemplate>> restoreDefaultStages() {
        return ResponseEntity.ok(stageTemplateService.restoreDefaultStages());
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> getProjectStages(@PathVariable UUID projectId) {
        return ResponseEntity.ok(stageTemplateService.getProjectStages(projectId));
    }

    @PostMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> attachStages(
            @PathVariable UUID projectId, @RequestBody List<ProjectStageRequest> requests) {
        return ResponseEntity.ok(stageTemplateService.attachStagesToProject(projectId, requests));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PatchMapping("/land/projects/{projectId}/stages/{stageId}/complete")
    public ResponseEntity<ProjectStage> toggleStageCompletion(
            @PathVariable UUID projectId, @PathVariable UUID stageId,
            @RequestParam boolean completed) {
        return ResponseEntity.ok(stageTemplateService.toggleStageCompletion(stageId, completed));
    }

    @PatchMapping("/land/projects/{projectId}/stages/{stageId}/cost")
    public ResponseEntity<ProjectStage> updateStageCost(
            @PathVariable UUID projectId, @PathVariable UUID stageId,
            @RequestBody Map<String, Object> body) {
        BigDecimal cost = body.get("cost") != null ? new BigDecimal(body.get("cost").toString()) : null;
        String notes = (String) body.get("notes");
        return ResponseEntity.ok(stageTemplateService.updateStageCostAndNotes(stageId, cost, notes));
    }

    @DeleteMapping("/land/projects/{projectId}/stages/{stageId}")
    public ResponseEntity<Void> removeStage(@PathVariable UUID projectId, @PathVariable UUID stageId) {
        stageTemplateService.removeProjectStage(stageId);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteStage(@PathVariable UUID id) {
        stageTemplateService.deleteTemplateStage(id);
        return ResponseEntity.noContent().build();
    }
}
""")

# =====================================================================
# 4) LandTitle.java — compile-safe shape (deprecated district/county kept,
#    retired 5 stay removed)
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PHYSICAL ASSET REGISTRY
 * RETIRED (pass 6): volume / folio / instrument_no / physical_box_number /
 * survey_date removed app-wide and dropped from the DB (PHASE G).
 * district/county stay as deprecated columns for backwards compatibility.
 */
@Entity
@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number"),
    @Index(name = "idx_title_id", columnList = "title_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LandTitle {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 50)
    private String tenure;

    @Column(name = "plot_number", unique = true, length = 100)
    private String plotNumber;

    @Column(name = "block_road", length = 100)
    private String blockRoad;

    @Deprecated
    @Column(length = 100)
    private String district;

    @Deprecated
    @Column(length = 100)
    private String county;

    @Column(name = "title_id", length = 100)
    private String titleId;

    @Deprecated
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    @Builder.Default
    @Column(name = "is_released", nullable = false)
    private boolean isReleased = false;

    @Column(name = "created_at", updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}
""")

# =====================================================================
# 5) DataInitializer.java — normalize + 7 samples + docs + PHASE G
# =====================================================================
write("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java", r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.service.LandService;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;
    private final LandService landService;

    @Value("${ADMIN_EMAIL}")
    private String adminEmail;

    @Value("${ADMIN_DEFAULT_PASSWORD}")
    private String adminDefaultPassword;

    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
        runSchemaMigrations();
        seedRootUser();
        stageTemplateService.seedDefaultStagesIfEmpty();
        try {
            stageTemplateService.normalizeToDefaultStages();
            System.out.println(">>> [STAGE_TEMPLATE] Normalized master checklist to defaults.");
        } catch (Exception e) {
            System.err.println(">>> [STAGE_TEMPLATE] normalize warning: " + e.getMessage());
        }
        seedSampleProjects();
        seedSampleDocuments();
        seedDefaultExpensePresets();
        System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
    }

    public void seedDefaultExpensePresets() {
        if (expensePresetRepository.count() > 0) {
            System.out.println(">>> [EXPENSES] Presets already exist, skipping default seed.");
            return;
        }
        String[] defaults = { "Office", "Fieldwork", "Land Office" };
        for (String name : defaults) {
            expensePresetRepository.save(ExpensePreset.builder().name(name).createdBy("SYSTEM").build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    // 7 diverse SAMPLE projects (guarded: only when none exist yet)
    private void seedSampleProjects() {
        try (java.sql.Connection conn = dataSource.getConnection();
             java.sql.PreparedStatement ps = conn.prepareStatement(
                "SELECT COUNT(*) FROM land_projects WHERE district = 'SAMPLE DATA'")) {
            try (java.sql.ResultSet rs = ps.executeQuery()) {
                if (rs.next() && rs.getInt(1) > 0) {
                    System.out.println(">>> [SAMPLE] Sample projects already present -- skipping seed.");
                    return;
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] guard check failed: " + e.getMessage());
            return;
        }

        java.util.List<StageTemplate> master = stageTemplateService.getActiveTemplate();
        java.util.Map<String, String> idByName = new java.util.HashMap<>();
        for (StageTemplate t : master) idByName.put(t.getStageName(), t.getId().toString());

        try {
            java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();

            ids.add(seedOne("SAMPLE-001", false, false, false, null, null, null, "2026-05-04",
                    5000000L, 2500000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER ONE", "SMPL00000001A", "0772000001" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection" }, idByName));

            ids.add(seedOne("SAMPLE-002", true, false, false, "SMPL-2002", "2026-03-01", "B-12", "2025-11-10",
                    8000000L, 8000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER TWO", "SMPL00000002A", "0772000002" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval", "Tax Assessment and Stamp Duty",
                                   "Registration and Title Issuance" }, idByName));

            ids.add(seedOne("SAMPLE-003", false, false, true, null, null, null, "2026-01-15",
                    6000000L, 1000000L, 50000L, 50000L,
                    new String[][] { { "SAMPLE OWNER THREE", "SMPL00000003A", "0772000003" } },
                    new String[] { "Field Work", "Deed Plan" }, idByName));

            ids.add(seedOne("SAMPLE-004", false, false, false, null, null, null, "2026-06-20",
                    10000000L, 1000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FOUR", "SMPL00000004A", "0772000004" },
                                     { "SAMPLE CO OWNER FOUR", "SMPL00000005A", "0772000005" } },
                    new String[] { "Field Work" }, idByName));

            ids.add(seedOne("SAMPLE-005", false, true, false, "SMPL-5005", "2026-07-20", "K-07", "2026-07-01",
                    4000000L, 3000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FIVE", "SMPL00000006A", "0772000006" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval" }, idByName));

            ids.add(seedOne("SAMPLE-006", false, false, false, null, null, null, "2026-08-20",
                    3000000L, 0L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER SIX", "SMPL00000007A", "0772000007" } },
                    new String[] { "Field Work" }, idByName));

            ids.add(seedOne("SAMPLE-007", true, false, false, "SMPL-7007", "2026-06-10", "W-03", "2026-02-02",
                    9000000L, 8100000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER SEVEN", "SMPL00000008A", "0772000008" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval", "Tax Assessment and Stamp Duty" }, idByName));

            int[] days = { 10, 200, 45, 60, 0, -1, 25 };
            try (java.sql.Connection conn = dataSource.getConnection()) {
                for (int i = 0; i < days.length && i < ids.size(); i++) {
                    if (ids.get(i) == null || days[i] < 0) continue;
                    java.sql.Timestamp ts = java.sql.Timestamp.valueOf(
                            java.time.LocalDateTime.now().minusDays(days[i]));
                    try (java.sql.PreparedStatement u1 = conn.prepareStatement(
                            "UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) {
                        u1.setTimestamp(1, ts); u1.setObject(2, ids.get(i)); u1.executeUpdate();
                    }
                    try (java.sql.PreparedStatement u2 = conn.prepareStatement(
                            "UPDATE payment_records SET timestamp = ? WHERE project_id = ?")) {
                        u2.setTimestamp(1, ts); u2.setObject(2, ids.get(i)); u2.executeUpdate();
                    }
                }
            }
            System.out.println(">>> [SAMPLE] Seeded 7 sample projects (district = SAMPLE DATA).");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] seed failed (non-fatal): " + e.getMessage());
        }
    }

    // 2 viewable sample docs per SAMPLE project that has none
    private void seedSampleDocuments() {
        String[][] docs = {
            { "SAMPLE_DEED_PLAN.pdf",  "DEED_PLAN",  "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf" },
            { "SAMPLE_TITLE_CERT.pdf", "TITLE_CERT", "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf" },
        };
        try (java.sql.Connection conn = dataSource.getConnection();
             java.sql.PreparedStatement ps = conn.prepareStatement(
                "SELECT id FROM land_projects WHERE district = 'SAMPLE DATA'")) {
            int attached = 0;
            try (java.sql.ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Object pid = rs.getObject(1);
                    try (java.sql.PreparedStatement c = conn.prepareStatement(
                            "SELECT COUNT(*) FROM project_documents WHERE project_id = ?")) {
                        c.setObject(1, pid);
                        try (java.sql.ResultSet crs = c.executeQuery()) {
                            if (crs.next() && crs.getInt(1) > 0) continue;
                        }
                    }
                    for (String[] d : docs) {
                        try (java.sql.PreparedStatement ins = conn.prepareStatement(
                                "INSERT INTO project_documents (id, project_id, file_name, file_type, file_path, uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?)")) {
                            ins.setObject(1, java.util.UUID.randomUUID());
                            ins.setObject(2, pid);
                            ins.setString(3, d[0]);
                            ins.setString(4, d[1]);
                            ins.setString(5, d[2]);
                            ins.setString(6, "SYSTEM");
                            ins.setTimestamp(7, java.sql.Timestamp.valueOf(java.time.LocalDateTime.now()));
                            ins.executeUpdate();
                        }
                    }
                    attached++;
                }
            }
            System.out.println(">>> [SAMPLE] Documents attached to " + attached + " sample project(s).");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] document seed failed (non-fatal): " + e.getMessage());
        }
    }

    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake,
                                   boolean receivable, String titleId, String titleDate,
                                   String block, String startDate, long cost, long paid,
                                   long initFee, long monthlyFee, String[][] owners,
                                   String[] stages, java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
                .district("SAMPLE DATA").county("SAMPLE COUNTY")
                .subCounty("SAMPLE SUB").parish("SAMPLE PARISH")
                .village("SAMPLE VILLAGE").area("SAMPLE AREA")
                .tenure("FREEHOLD")
                .projectStartDate(java.time.LocalDate.parse(startDate))
                .totalCost(java.math.BigDecimal.valueOf(cost))
                .initialPayment(java.math.BigDecimal.valueOf(paid))
                .isLegacy(legacy)
                .titleAtIntake(titleAtIntake)
                .isStartAsReceivable(receivable);
        if (plot != null) b.plotNumber(plot);
        if (titleId != null) b.titleId(titleId);
        if (block != null) b.blockRoad(block);
        if (titleDate != null) b.titleIssueDate(java.time.LocalDate.parse(titleDate));
        if (receivable) {
            b.initialStorageFee(java.math.BigDecimal.valueOf(initFee > 0 ? initFee : 50000));
            b.monthlyStorageFee(java.math.BigDecimal.valueOf(monthlyFee > 0 ? monthlyFee : 50000));
        }
        java.util.List<LandEntryRequest.OwnerRequest> os = new java.util.ArrayList<>();
        for (String[] o : owners) {
            os.add(LandEntryRequest.OwnerRequest.builder()
                    .fullName(o[0]).nationalId(o[1]).phone(o[2]).build());
        }
        b.owners(os);
        java.util.List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> ss = new java.util.ArrayList<>();
        for (String s : stages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid).stageName(s).isCustom(tid == null).isCompleted(true).build());
        }
        b.selectedStages(ss);
        LandProject saved = landService.atomicIntake(b.build(), null);
        return saved.getId();
    }

    private void runSchemaMigrations() {
        String[] migrations = {
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS negotiation_deadline TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_titles_project_index') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",
            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",
            "CREATE TABLE IF NOT EXISTS expense_presets (" +
                "id UUID PRIMARY KEY, " +
                "name VARCHAR(100) NOT NULL UNIQUE, " +
                "created_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now())",
            "CREATE TABLE IF NOT EXISTS expenses (" +
                "id UUID PRIMARY KEY, " +
                "category VARCHAR(150) NOT NULL, " +
                "amount NUMERIC(15,2) NOT NULL, " +
                "note TEXT, " +
                "recorded_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now(), " +
                "edited_at TIMESTAMP, " +
                "edited_by VARCHAR(100))",
            "CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            "UPDATE land_projects lp SET district = lt.district, county = lt.county " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL " +
                "AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
            // PHASE G -- RETIRED TITLE DETAILS: dropped from DB
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS volume",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS folio",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS instrument_no",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS physical_box_number",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS survey_date",
        };

        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {
            for (String sql : migrations) {
                try {
                    stmt.execute(sql);
                    System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length())));
                } catch (Exception e) {
                    System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage());
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());
        }
    }

    public void seedRootUser() {
        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";
        String encodedPassword = passwordEncoder.encode(rawPassword);

        try (java.sql.Connection conn = dataSource.getConnection()) {
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) exists = rs.getInt(1) > 0;
                }
            }

            if (!exists) {
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) "
                           + "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset. Existing credentials remain in effect.");
            }

        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
""")

# =====================================================================
# 6) LedgerPage.jsx — auto-retry once on cold-start fault
# =====================================================================
patch("erp-frontend/src/pages/Ledger/LedgerPage.jsx",
"""    const fetchLedger = useCallback(async () => {
        setLoading(true);
        setLoadError(false);
        try {
            const data = await landService.getGlobalLedger(page, 50);
            setProjects(data.content || []);
        } catch {
            setLoadError(true);
        } finally {
            setLoading(false);
        }
    }, [page]);

    useEffect(() => { fetchLedger(); }, [fetchLedger]);""",
"""    // Free-tier cold start: the API can take ~a minute to wake. Retry once
    // after 5s before declaring a fault, so a waking backend no longer
    // shows LEDGER SYNC FAULT.
    const fetchLedger = useCallback(async (attempt = 0) => {
        setLoading(true);
        setLoadError(false);
        try {
            const data = await landService.getGlobalLedger(page, 50);
            setProjects(data.content || []);
            setLoading(false);
        } catch {
            if (attempt < 1) {
                setTimeout(() => fetchLedger(attempt + 1), 5000);
                return;
            }
            setLoadError(true);
            setLoading(false);
        }
    }, [page]);

    useEffect(() => { fetchLedger(); }, [fetchLedger]);""")

# =====================================================================
# Report + commit + push
# =====================================================================
print(f"\n=== fix12.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)}")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'fix12: consistent backend set (compile-safe) + Ledger cold-start auto-retry + samples/docs seed'], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit {e.returncode})")
    except FileNotFoundError:
        print("\n  Git: not found")
print()