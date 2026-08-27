#!/usr/bin/env python3
"""
fix8.py — repair backend compile: controller/service method mismatch.
Rewrites StageTemplateService.java (original + bulk trio + normalize)
and StageTemplateController.java (original + index fix + bulk trio)
so they always compile together.
Run: py fix8.py
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

# =====================================================================
# 1) StageTemplateService.java — FULL canonical version
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

/**
 * GE SOLUTIONS - STAGE TEMPLATE ENGINE (PHASE 4)
 */
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

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    // Called once from DataInitializer at startup.
    @Transactional
    public void seedDefaultStagesIfEmpty() {
        if (templateRepository.count() > 0) return;

        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = StageTemplate.builder()
                    .stageName(name)
                    .defaultCost(BigDecimal.ZERO)
                    .displayOrder(order++)
                    .isActive(true)
                    .build();
            templateRepository.save(stage);
        }
        System.out.println(">>> [STAGE_TEMPLATE] Seeded " + DEFAULT_STAGES.length + " default stages.");
    }

    // ─── MASTER TEMPLATE CRUD ────────────────────────────────────────

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

    // ─── PER-PROJECT STAGE MANAGEMENT ────────────────────────────────

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
            String name;
            BigDecimal cost;

            if (req.isCustom()) {
                if (req.getStageName() == null || req.getStageName().isBlank()) {
                    throw new BusinessException("STAGE_NAME_REQUIRED: Custom stage needs a name.");
                }
                name = req.getStageName().trim();
                cost = req.getCost() != null ? req.getCost() : BigDecimal.ZERO;
            } else {
                if (req.getStageTemplateId() == null) {
                    throw new BusinessException("STAGE_TEMPLATE_ID_REQUIRED");
                }
                StageTemplate template = templateRepository.findById(UUID.fromString(req.getStageTemplateId()))
                        .orElseThrow(() -> new BusinessException("STAGE_TEMPLATE_NOT_FOUND"));
                name = template.getStageName();
                cost = req.getCost() != null ? req.getCost() : template.getDefaultCost();
            }

            ProjectStage stage = ProjectStage.builder()
                    .projectId(projectId)
                    .stageName(name)
                    .cost(cost)
                    .notes(req.getNotes())
                    .isCustom(req.isCustom())
                    .isCompleted(req.isCompleted())
                    .displayOrder(startOrder + (i++))
                    .build();
            created.add(projectStageRepository.save(stage));
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

    // INTAKE REDESIGN: allow deleting middle stages from the template
    @Transactional
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }

    // ─── BULK OPERATIONS (PERF FIX) ──────────────────────────────────

    private static final java.util.Set<String> DEFAULT_STAGE_NAMES =
            java.util.Set.of(DEFAULT_STAGES);

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
        List<StageTemplate> saved = templateRepository.saveAll(toSave);
        auditService.logAction("STAGE_TEMPLATE_REORDERED",
            "Operator [" + getCurrentOperator() + "] reordered " + saved.size() + " master stage(s).");
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void bulkDeleteTemplateStages(List<UUID> ids) {
        if (ids == null || ids.isEmpty()) return;
        List<StageTemplate> toDelete = templateRepository.findAllById(ids);
        if (toDelete.isEmpty()) return;
        templateRepository.deleteAllInBatch(toDelete);
        auditService.logAction("STAGE_TEMPLATE_BULK_DELETED",
            "Operator [" + getCurrentOperator() + "] bulk-deleted " + toDelete.size() + " master stage(s).");
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> restoreDefaultStages() {
        List<StageTemplate> current = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();

        List<StageTemplate> nonDefault = current.stream()
                .filter(s -> !DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .toList();
        if (!nonDefault.isEmpty()) {
            templateRepository.deleteAllInBatch(nonDefault);
        }

        java.util.Map<String, StageTemplate> keepByName = current.stream()
                .filter(s -> DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .collect(java.util.stream.Collectors.toMap(
                        StageTemplate::getStageName, s -> s, (a, b) -> a));

        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = keepByName.get(name);
            if (stage == null) {
                stage = StageTemplate.builder()
                        .stageName(name)
                        .defaultCost(BigDecimal.ZERO)
                        .displayOrder(order)
                        .isActive(true)
                        .build();
            } else {
                stage.setDisplayOrder(order);
            }
            order++;
            toSave.add(stage);
        }
        List<StageTemplate> saved = templateRepository.saveAll(toSave);
        auditService.logAction("STAGE_TEMPLATE_DEFAULTS_RESTORED",
            "Operator [" + getCurrentOperator() + "] restored the default master stage list.");
        return saved;
    }

    /**
     * PASS 6: called once at boot. The master checklist must always be
     * exactly the 6 canonical defaults, in order, with no duplicates.
     * Repairs junk/duplicate rows created by earlier buggy passes.
     */
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
                        .stageName(name)
                        .defaultCost(BigDecimal.ZERO)
                        .displayOrder(order)
                        .isActive(true)
                        .build());
            } else if (stage.getDisplayOrder() == null || stage.getDisplayOrder() != order) {
                stage.setDisplayOrder(order);
                templateRepository.save(stage);
            }
            order++;
        }
    }
}
""")

# =====================================================================
# 2) StageTemplateController.java — FULL canonical version
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

    // ─── MASTER TEMPLATE ─────────────────────────────────────────────

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

    // PERF FIX: bulk reorder in one round trip.
    @PutMapping("/stage-templates/reorder")
    public ResponseEntity<List<StageTemplate>> reorderTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> orderedIds = (body.getOrDefault("orderedIds", List.of())).stream()
                .map(UUID::fromString)
                .toList();
        return ResponseEntity.ok(stageTemplateService.reorderTemplateStages(orderedIds));
    }

    // PERF FIX: bulk delete in one round trip.
    @DeleteMapping("/stage-templates/bulk")
    public ResponseEntity<Void> bulkDeleteTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> ids = (body.getOrDefault("ids", List.of())).stream()
                .map(UUID::fromString)
                .toList();
        stageTemplateService.bulkDeleteTemplateStages(ids);
        return ResponseEntity.noContent().build();
    }

    // PERF FIX: restore defaults in one transactional round trip.
    @PostMapping("/stage-templates/restore-defaults")
    public ResponseEntity<List<StageTemplate>> restoreDefaultStages() {
        return ResponseEntity.ok(stageTemplateService.restoreDefaultStages());
    }

    // ─── PER-PROJECT STAGES ──────────────────────────────────────────

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

    // INTAKE REDESIGN: delete a middle stage template
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteStage(@PathVariable UUID id) {
        stageTemplateService.deleteTemplateStage(id);
        return ResponseEntity.noContent().build();
    }
}
""")

# =====================================================================
# Report + commit + push
# =====================================================================
print(f"\n=== fix8.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)}")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'fix8: align StageTemplateService with controller (add reorder/bulkDelete/restoreDefaults) — fixes compile'], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit {e.returncode})")
    except FileNotFoundError:
        print("\n  Git: not found")
print()