# PATH: fix.py
# PHASE 4A - STAGE TEMPLATE SYSTEM (BACKEND FOUNDATION ONLY) - ADDITIVE
# Run from project root: py fix.py
#
# SCOPE OF THIS PATCH:
#
# Builds the master Stage Template checklist and per-project stage
# instances described in Section 17.5. This is BACKEND ONLY:
#   - New StageTemplate model (the reusable checklist: Field Work, Deed
#     Plan, LC Inspection, District Land Board Approval, Tax Assessment
#     and Stamp Duty, Registration and Title Issuance -- default cost 0,
#     fully editable).
#   - New ProjectStage model (the per-project instance of a stage, with
#     its own cost/notes, separate from the master template so editing
#     the template later never rewrites numbers already committed on a
#     live project).
#   - New tables are created automatically by Hibernate (ddl-auto=update)
#     since both models are plain @Entity classes -- no manual SQL needed.
#   - New service + controller for master template CRUD and per-project
#     stage management (attach, toggle complete, edit cost/notes, remove).
#   - Intake (LandEntryRequest / LandService.atomicIntake) can now
#     optionally accept a list of selected stages at intake time. This
#     field is OPTIONAL -- omitting it changes nothing about existing
#     intake behavior.
#   - DataInitializer seeds the 6 default stages once, on first startup
#     after this deploy, only if the stage_templates table is empty.
#
# This patch does NOT touch:
#   - IntakePage.jsx (no checkbox/"+" custom stage UI yet)
#   - FolderPage.jsx (still uses the old hardcoded 5-stage STAGE_LABELS
#     pipeline -- untouched, still works exactly as before)
#   That UI work is Phase 4B, a separate dedicated fix.py, because it is
#   large enough JSX restructuring that patching it blind via text
#   anchors carries real risk of a bad patch landing silently.
#
# DELIBERATELY NOT INCLUDED (and why):
#   ROLE_SECRETARY is still not wired into ANY @PreAuthorize check here,
#   consistent with the standing decision from Phase 3A/3B. The new
#   toggleStageCompletion() method in StageTemplateService is deliberately
#   kept separate from updateStageCostAndNotes() specifically so that a
#   future Secretary rollout can be wired to toggleStageCompletion() only
#   (stage change, no cost access) without touching the cost-edit method
#   at all. That wiring itself is not done in this patch.
#
# TEST PLAN (do this once you're ready, per your deferred testing plan):
#   1. After deploy, check Render logs for a line like:
#      ">>> [STAGE_TEMPLATE] Seeded 6 default stages."
#      (only appears once, on the first startup after this deploy)
#   2. Via Postman: GET /api/v1/stage-templates -- should return the 6
#      default stages, all with defaultCost 0.
#   3. Via Postman: POST /api/v1/land/projects/{existingProjectId}/stages
#      with a body like:
#      [{"stageTemplateId": "<uuid from step 2>", "cost": 50000, "notes": "test"}]
#      Then GET /api/v1/land/projects/{projectId}/stages to confirm it saved.
#   4. Confirm existing intake (IntakePage -> New Plot) still works exactly
#      as before -- selectedStages is optional and unused by the current
#      frontend, so this should be invisible.

import os

def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  -> Saved: {path}")

def patch_file(path, anchor, replacement, label):
    content = read_file(path)
    if content is None:
        print(f"FAIL: {label} ({path} not found)")
        return
    if anchor not in content:
        print(f"MISSING: {label} (anchor not found in {path} -- may already be patched, or file changed)")
        return
    if content.count(anchor) > 1:
        print(f"WARN: {label} (anchor appears more than once -- patching first occurrence only)")
    content = content.replace(anchor, replacement, 1)
    write_file(path, content)
    print(f"OK: {label}")

def create_new_file(path, content, label):
    if os.path.isfile(path):
        print(f"SKIPPED: {label} (file already exists at {path} -- not overwriting)")
        return
    write_file(path, content)
    print(f"OK: {label} (new file)")

print("Starting Phase 4A Patch - Stage Template Backend Foundation...")
print("-" * 60)

# ============================================================
# NEW FILE: StageTemplate.java
# ============================================================
stage_template_model = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/StageTemplate.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.util.UUID;

/**
 * GE SOLUTIONS - STAGE TEMPLATE (PHASE 4)
 *
 * The master, reusable checklist of processing stages (Field Work, Deed Plan,
 * LC Inspection, District Land Board Approval, Tax Assessment and Stamp Duty,
 * Registration and Title Issuance) with a default cost per stage.
 *
 * Per Section 17.5: everyone EXCEPT Secretary can edit this master template
 * (add/remove/rename stages, change default costs). Secretary can only pick
 * from it at intake -- template edit endpoints are gated accordingly in
 * StageTemplateController / StageTemplateService.
 *
 * Intentionally separate from ProjectStage, which stores the actual
 * per-project instance (with its own editable cost, since the same stage
 * can cost different amounts on different projects).
 */
@Entity
@Table(name = "stage_templates")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StageTemplate {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "stage_name", nullable = false, length = 200)
    private String stageName;

    @Builder.Default
    @Column(name = "default_cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal defaultCost = BigDecimal.ZERO;

    @Builder.Default
    @Column(name = "display_order", nullable = false)
    private Integer displayOrder = 0;

    /**
     * Soft-delete flag. Deactivated stages stay in the DB (so historical
     * ProjectStage rows that reference them by name remain meaningful) but
     * no longer appear in the checklist offered at intake.
     */
    @Builder.Default
    @Column(name = "is_active", nullable = false)
    private boolean isActive = true;
}
"""
create_new_file("erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/StageTemplate.java",
                 stage_template_model, "StageTemplate.java")

# ============================================================
# NEW FILE: ProjectStage.java
# ============================================================
project_stage_model = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectStage.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PER-PROJECT STAGE INSTANCE (PHASE 4)
 *
 * A single stage attached to a specific project. Created either by copying
 * a StageTemplate entry (at intake or later), or as a one-off custom stage
 * added directly on a project via the "+" button per Section 17.5.
 *
 * Stores its own copy of stageName and cost rather than a foreign key to
 * StageTemplate, so that editing or deactivating the master template later
 * never changes numbers already committed on a live project.
 *
 * Stages can move backward (e.g. Approved -> Refused, then resubmitted) --
 * modeled here simply as isCompleted toggling back to false, matching
 * Section 17.5's requirement that "Refused is not final -- can be
 * resubmitted."
 */
@Entity
@Table(name = "project_stages", indexes = {
    @Index(name = "idx_project_stage_project", columnList = "project_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProjectStage {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "stage_name", nullable = false, length = 200)
    private String stageName;

    @Builder.Default
    @Column(name = "cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal cost = BigDecimal.ZERO;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    /**
     * True if this stage was added ad-hoc on this project via the "+"
     * button, rather than picked from the master StageTemplate checklist.
     */
    @Builder.Default
    @Column(name = "is_custom", nullable = false)
    private boolean isCustom = false;

    @Builder.Default
    @Column(name = "is_completed", nullable = false)
    private boolean isCompleted = false;

    @Builder.Default
    @Column(name = "display_order", nullable = false)
    private Integer displayOrder = 0;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
"""
create_new_file("erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectStage.java",
                 project_stage_model, "ProjectStage.java")

# ============================================================
# NEW FILE: StageTemplateRepository.java
# ============================================================
stage_template_repo = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/StageTemplateRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.StageTemplate;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface StageTemplateRepository extends JpaRepository<StageTemplate, UUID> {

    List<StageTemplate> findByIsActiveTrueOrderByDisplayOrderAsc();
}
"""
create_new_file("erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/StageTemplateRepository.java",
                 stage_template_repo, "StageTemplateRepository.java")

# ============================================================
# NEW FILE: ProjectStageRepository.java
# ============================================================
project_stage_repo = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectStageRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.ProjectStage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ProjectStageRepository extends JpaRepository<ProjectStage, UUID> {

    List<ProjectStage> findByProjectIdOrderByDisplayOrderAsc(UUID projectId);

    void deleteByProjectId(UUID projectId);
}
"""
create_new_file("erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectStageRepository.java",
                 project_stage_repo, "ProjectStageRepository.java")

# ============================================================
# NEW FILE: ProjectStageRequest.java (DTO)
# ============================================================
project_stage_request_dto = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectStageRequest.java
package com.gesolutions.erp.modules.land.dto;

import lombok.*;
import java.math.BigDecimal;

/**
 * GE SOLUTIONS - PROJECT STAGE SELECTION (PHASE 4)
 *
 * One entry in the checklist a staff member submits when attaching stages
 * to a project. If stageTemplateId is set, cost defaults to that
 * template's defaultCost unless overridden here. If isCustom is true,
 * stageTemplateId is ignored and stageName/cost are used directly to
 * create a one-off stage.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProjectStageRequest {

    private String stageTemplateId;
    private String stageName;
    private BigDecimal cost;
    private String notes;
    private boolean isCustom;
}
"""
create_new_file("erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectStageRequest.java",
                 project_stage_request_dto, "ProjectStageRequest.java")

# ============================================================
# NEW FILE: StageTemplateService.java
# ============================================================
stage_template_service = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java
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
 *
 * Manages the master Stage Template checklist and the per-project stage
 * instances attached to each land project. See Section 17.5 of the LLM
 * context guide for the full business rules this implements.
 */
@Service
@RequiredArgsConstructor
public class StageTemplateService {

    private final StageTemplateRepository templateRepository;
    private final ProjectStageRepository projectStageRepository;
    private final AuditService auditService;

    /**
     * DEFAULT STAGE LIST (Section 17.5)
     * Seeded once, on first startup, if the template table is empty.
     * Costs start at 0 and are fully editable by staff afterward.
     */
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

    // ─── MASTER TEMPLATE CRUD ────────────────────────────────────────────

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

    // ─── PER-PROJECT STAGE MANAGEMENT ────────────────────────────────────

    @Transactional(readOnly = true)
    public List<ProjectStage> getProjectStages(UUID projectId) {
        return projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
    }

    /**
     * Attaches a checklist of stages to a project. Called from intake, and
     * reusable later to add more stages to an existing project. Not
     * @PreAuthorize-gated directly here -- callers apply the appropriate
     * gate (intake itself stays open to Manager/Admin/Director for now).
     */
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
                    .isCompleted(false)
                    .displayOrder(startOrder + (i++))
                    .build();
            created.add(projectStageRepository.save(stage));
        }

        auditService.logAction("PROJECT_STAGES_ATTACHED",
            "Operator [" + getCurrentOperator() + "] attached " + created.size()
            + " stage(s) to project: " + projectId);

        return created;
    }

    /**
     * Toggles a stage's completion status only -- STAGE-CHANGE ACTION per
     * Section 17.7 (Secretary can eventually do this, once wired, without
     * ever touching cost). Deliberately does not touch cost or notes.
     */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStage toggleStageCompletion(UUID stageId, boolean completed) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        stage.setCompleted(completed);
        stage.setCompletedAt(completed ? LocalDateTime.now() : null);
        ProjectStage saved = projectStageRepository.save(stage);
        auditService.logAction("PROJECT_STAGE_STATUS_CHANGED",
            "Operator [" + getCurrentOperator() + "] marked stage \\"" + stage.getStageName()
            + "\\" as " + (completed ? "COMPLETE" : "NOT COMPLETE") + " on project: " + stage.getProjectId());
        return saved;
    }

    /**
     * Edits cost and/or notes on an already-attached project stage --
     * COST-EDIT ACTION, kept separate from toggleStageCompletion() per
     * Section 17.7 so a future Secretary role can be wired to the
     * stage-only toggle without ever reaching this method.
     */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStage updateStageCostAndNotes(UUID stageId, BigDecimal cost, String notes) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        if (cost != null) stage.setCost(cost);
        if (notes != null) stage.setNotes(notes);
        ProjectStage saved = projectStageRepository.save(stage);
        auditService.logAction("PROJECT_STAGE_COST_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated cost/notes on stage \\"" + stage.getStageName()
            + "\\" for project: " + stage.getProjectId());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void removeProjectStage(UUID stageId) {
        ProjectStage stage = projectStageRepository.findById(stageId)
                .orElseThrow(() -> new BusinessException("PROJECT_STAGE_NOT_FOUND"));
        projectStageRepository.delete(stage);
        auditService.logAction("PROJECT_STAGE_REMOVED",
            "Operator [" + getCurrentOperator() + "] removed stage \\"" + stage.getStageName()
            + "\\" from project: " + stage.getProjectId());
    }
}
"""
create_new_file("erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java",
                 stage_template_service, "StageTemplateService.java")

# ============================================================
# NEW FILE: StageTemplateController.java
# ============================================================
stage_template_controller = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java
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

    @GetMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> getProjectStages(@PathVariable UUID projectId) {
        return ResponseEntity.ok(stageTemplateService.getProjectStages(projectId));
    }

    @PostMapping("/land/projects/{projectId}/stages")
    public ResponseEntity<List<ProjectStage>> attachStages(
            @PathVariable UUID projectId, @RequestBody List<ProjectStageRequest> requests) {
        return ResponseEntity.ok(stageTemplateService.attachStagesToProject(projectId, requests));
    }

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
}
"""
create_new_file("erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java",
                 stage_template_controller, "StageTemplateController.java")

# ============================================================
# NEW FILE: stageTemplateService.js (frontend API wrapper only)
# ============================================================
stage_template_frontend_service = """// PATH: erp-frontend/src/services/stageTemplateService.js
import api from '../api/axios';

/**
 * GOLDEN SEED - STAGE TEMPLATE SERVICE (PHASE 4A)
 *
 * Backend API wrapper only. The Intake checkbox/cost UI and the FolderPage
 * dynamic stage display that consume this are built in Phase 4B.
 */
const stageTemplateService = {

    getTemplate: async () => {
        const response = await api.get('/stage-templates');
        return response.data;
    },

    addTemplateStage: async (stageName, defaultCost) => {
        const response = await api.post('/stage-templates', { stageName, defaultCost });
        return response.data;
    },

    updateTemplateStage: async (id, stageName, defaultCost) => {
        const response = await api.put(`/stage-templates/${id}`, { stageName, defaultCost });
        return response.data;
    },

    deactivateTemplateStage: async (id) => {
        await api.delete(`/stage-templates/${id}`);
    },

    getProjectStages: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/stages`);
        return response.data;
    },

    attachStages: async (projectId, stageRequests) => {
        const response = await api.post(`/land/projects/${projectId}/stages`, stageRequests);
        return response.data;
    },

    toggleStageCompletion: async (projectId, stageId, completed) => {
        const response = await api.patch(
            `/land/projects/${projectId}/stages/${stageId}/complete`,
            null,
            { params: { completed } }
        );
        return response.data;
    },

    updateStageCost: async (projectId, stageId, cost, notes) => {
        const response = await api.patch(
            `/land/projects/${projectId}/stages/${stageId}/cost`,
            { cost, notes }
        );
        return response.data;
    },

    removeStage: async (projectId, stageId) => {
        await api.delete(`/land/projects/${projectId}/stages/${stageId}`);
    },
};

export default stageTemplateService;
"""
create_new_file("erp-frontend/src/services/stageTemplateService.js",
                 stage_template_frontend_service, "stageTemplateService.js")

# ============================================================
# PATCH: DataInitializer.java -- import + field + seed call
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"

patch_file(path,
    """import com.gesolutions.erp.modules.auth.repository.UserRepository;
import lombok.RequiredArgsConstructor;""",
    """import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;""",
    "DataInitializer.java import StageTemplateService")

patch_file(path,
    """    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;""",
    """    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;""",
    "DataInitializer.java field StageTemplateService")

patch_file(path,
    """        // Seed root user if missing
        seedRootUser();

        System.out.println(">>> NYENZ SYSTEM: Identity Protocol Active. Registry Locked.");""",
    """        // Seed root user if missing
        seedRootUser();

        // PHASE 4: Seed the default stage template checklist if empty
        stageTemplateService.seedDefaultStagesIfEmpty();

        System.out.println(">>> NYENZ SYSTEM: Identity Protocol Active. Registry Locked.");""",
    "DataInitializer.java run() seed call")

# ============================================================
# PATCH: LandEntryRequest.java -- optional selectedStages field
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java"

patch_file(path,
    """    private java.math.BigDecimal monthlyStorageFee;
    private java.math.BigDecimal initialStorageFee;""",
    """    private java.math.BigDecimal monthlyStorageFee;
    private java.math.BigDecimal initialStorageFee;

    // PHASE 4: Optional stage checklist selected at intake. If omitted,
    // no stages are attached and staff can add them later from the
    // Folder page once Phase 4B ships.
    @Builder.Default
    private List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> selectedStages = new ArrayList<>();""",
    "LandEntryRequest.java selectedStages field")

# ============================================================
# PATCH: LandService.java -- inject service + attach stages at intake
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"

patch_file(path,
    """    private final PaymentRecordRepository paymentRecordRepository;
    private final ProjectIndexService projectIndexService;""",
    """    private final PaymentRecordRepository paymentRecordRepository;
    private final ProjectIndexService projectIndexService;
    private final StageTemplateService stageTemplateService;""",
    "LandService.java field StageTemplateService")

patch_file(path,
    """        if (scans != null) addScansToProject(saved.getId(), scans);""",
    """        if (request.getSelectedStages() != null && !request.getSelectedStages().isEmpty()) {
            stageTemplateService.attachStagesToProject(saved.getId(), request.getSelectedStages());
        }

        if (scans != null) addScansToProject(saved.getId(), scans);""",
    "LandService.java atomicIntake stage attachment")

print("-" * 60)
print("DONE. Check for FAIL / MISSING / SKIPPED messages above.")
print("")
print("If everything shows OK, run:")
print("git add -A && git commit -m 'feat: Phase 4A - Stage Template backend foundation' && git push")
print("")
print("REMINDER:")
print("  - This is backend only. No visible UI change for staff yet.")
print("  - Phase 4B (Intake checkbox UI + FolderPage dynamic stage display)")
print("    is a separate dedicated fix.py, written only when you say go.")
print("  - Per your testing plan, this stays unconfirmed until your")
print("    end-of-all-phases test pass.")