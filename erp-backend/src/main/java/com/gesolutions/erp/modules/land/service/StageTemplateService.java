// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java
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
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }

    /**
     * PASS 6: called once at boot. The master checklist must always be
     * exactly the 6 canonical defaults, in order, with no duplicates.
     * Repairs junk/duplicate rows created by earlier buggy passes.
     */
    @Transactional
    public void normalizeToDefaultStages() {
        List<StageTemplate> active = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();
        java.util.Set<String> defaults = new java.util.LinkedHashSet<>(java.util.Arrays.asList(DEFAULT_STAGES));
        java.util.Map<String, StageTemplate> kept = new java.util.LinkedHashMap<>();

        for (StageTemplate t : active) {
            String name = t.getStageName();
            boolean isDefault = name != null && defaults.contains(name);
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
