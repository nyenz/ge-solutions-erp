// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java
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

/**
 * GE SOLUTIONS - STAGE TEMPLATE & PROJECT STAGE API (PHASE 4)
 *
 * Base gate: any authenticated Manager/Admin/Director can read. Specific
 * write endpoints are tightened further in StageTemplateService via method
 * security -- see Section 17.7 for the full permission table.
 */
@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class StageTemplateController {

    private final StageTemplateService stageTemplateService;

    // ─── MASTER TEMPLATE ─────────────────────────────────────────────────

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

    // ─── PER-PROJECT STAGES ──────────────────────────────────────────────

    // STAGE 2 FIX: Secretary can view a project's stage checklist
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

    // STAGE 2 FIX: "Changes Stages: Yes (stage only)" per the role table --
    // Secretary may toggle stage completion but NOT edit stage cost, attach
    // new stages, remove stages, or touch the master template (all below
    // stay on the class-level Manager/Admin/Director-only default).
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
    @org.springframework.web.bind.annotation.DeleteMapping("/{id}")
    public org.springframework.http.ResponseEntity<Void> deleteStage(
            @org.springframework.web.bind.annotation.PathVariable Long id) {
        stageTemplateService.deleteTemplateStage(id);
        return org.springframework.http.ResponseEntity.noContent().build();
    }
}
