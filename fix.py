#!/usr/bin/env python3
"""
fix5.py — repair broken deploy.
1) FolderPage.jsx: collapse duplicate BackToTopButton import/render.
2) StageTemplateService.java: FULL rewrite (original + Part-3 bulk
   methods + normalizeToDefaultStages).
3) DataInitializer.java: FULL rewrite (Part-1 base + PHASE G drops +
   normalize call + seedSampleProjects/seedOne).
Run: py fix5.py
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
# 1) FolderPage.jsx — de-duplicate the self-applied patches
# =====================================================================
p = ROOT / "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"
try:
    t = p.read_text(encoding="utf-8")
    imp = "import BackToTopButton from '../../components/common/BackToTopButton';\n"
    while (imp + imp) in t: t = t.replace(imp + imp, imp)
    if imp not in t:
        t = t.replace("import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\n",
                      "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\n" + imp)
    ren = "            <BackToTopButton />\n"
    while (ren + ren) in t: t = t.replace(ren + ren, ren)
    if "<BackToTopButton />" not in t:
        t = t.replace("            <SavingOverlay visible={committing || paying} />\n",
                      "            <SavingOverlay visible={committing || paying} />\n" + ren)
    p.write_text(t, encoding="utf-8"); WROTE.append("FolderPage.jsx (deduped)")
except Exception as e:
    FAILED.append(("FolderPage.jsx", str(e)))

# =====================================================================
# 2) StageTemplateService.java — FULL canonical rewrite
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
     * PASS 6: called once at boot. The Intake form no longer writes to the
     * master template (its stage edits are local-only), so the master must
     * always be exactly the 6 canonical defaults, in order, with no
     * duplicates. Repairs the junk/duplicate rows created by earlier buggy
     * passes and keeps the checklist canonical going forward.
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
                t.setActive(false); // non-default or duplicate -> retire
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
# 3) DataInitializer.java — FULL canonical rewrite
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

        // PHASE 4: Seed the default stage template checklist if empty
        stageTemplateService.seedDefaultStagesIfEmpty();

        // PASS 6: master checklist must always be exactly the 6 defaults
        try {
            stageTemplateService.normalizeToDefaultStages();
            System.out.println(">>> [STAGE_TEMPLATE] Normalized master checklist to defaults.");
        } catch (Exception e) {
            System.err.println(">>> [STAGE_TEMPLATE] normalize warning: " + e.getMessage());
        }

        // PASS 6: seed 5 unique SAMPLE projects for Ledger testing (once).
        seedSampleProjects();

        // EXPENSES REBUILD: Seed the default expense presets if empty
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
            expensePresetRepository.save(ExpensePreset.builder()
                    .name(name)
                    .createdBy("SYSTEM")
                    .build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    // PASS 6: 5 unique SAMPLE projects exercising different Ledger
    // scenarios. Guarded so it only ever runs once (district = SAMPLE DATA).
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

            // 1) ACTIVE, 50% paid, mid-pipeline (YELLOW badge after backdate)
            ids.add(seedOne("SAMPLE-001", false, false, false, "SMPL-1001", "2026-04-15", "B-10",
                    5000000L, 2500000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER ONE", "CM000000000001", "0772000001" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection" }, idByName));

            // 2) LEGACY title, FULLY PAID
            ids.add(seedOne("SAMPLE-002", true, false, false, "SMPL-2002", "2026-03-01", "B-12",
                    8000000L, 8000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER TWO", "CM000000000002", "0772000002" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval", "Tax Assessment and Stamp Duty",
                                   "Registration and Title Issuance" }, idByName));

            // 3) RECEIVABLE with storage fees running
            ids.add(seedOne("SAMPLE-003", false, false, true, "SMPL-3003", "2026-05-20", "C-03",
                    6000000L, 1000000L, 50000L, 50000L,
                    new String[][] { { "SAMPLE OWNER THREE", "CM000000000003", "0772000003" } },
                    new String[] { "Field Work", "Deed Plan" }, idByName));

            // 4) CRITICAL debtor (10% paid) with JOINT owners
            ids.add(seedOne("SAMPLE-004", false, false, false, null, null, null,
                    10000000L, 1000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FOUR", "CM000000000004", "0772000004" },
                                     { "SAMPLE CO OWNER FOUR", "CM000000000005", "0772000005" } },
                    new String[] { "Field Work" }, idByName));

            // 5) NEW TITLE at intake, 75% paid, fresh payment (GREEN badge)
            ids.add(seedOne("SAMPLE-005", false, true, false, "SMPL-5005", "2026-07-01", "K-07",
                    4000000L, 3000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FIVE", "CM000000000006", "0772000006" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval" }, idByName));

            // Backdate payments for badge variety (days ago): 10 / 200 / 45 / 60
            int[] days = { 10, 200, 45, 60 };
            try (java.sql.Connection conn = dataSource.getConnection()) {
                for (int i = 0; i < days.length && i < ids.size(); i++) {
                    if (ids.get(i) == null) continue;
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
            System.out.println(">>> [SAMPLE] Seeded 5 sample projects (district = SAMPLE DATA).");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] seed failed (non-fatal): " + e.getMessage());
        }
    }

    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake,
                                   boolean receivable, String titleId, String titleDate,
                                   String block, long cost, long paid, long initFee,
                                   long monthlyFee, String[][] owners, String[] stages,
                                   java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
                .district("SAMPLE DATA").county("SAMPLE COUNTY")
                .subCounty("SAMPLE SUB").parish("SAMPLE PARISH")
                .village("SAMPLE VILLAGE").area("SAMPLE AREA")
                .tenure("FREEHOLD")
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
                    .stageTemplateId(tid)
                    .stageName(s)
                    .isCustom(tid == null)
                    .isCompleted(true)
                    .build());
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

            // PHASE 1 - PROJECT INDEX SYSTEM
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_titles_project_index') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",

            // PHASE 1.5 - DATE TRACKING SYSTEM
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",

            // PHASE 2 - NIN-BASED IDENTITY
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",

            // PHASE C - national_id mandatory + unique
            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",

            // EXPENSES REBUILD
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

            // STAGE 3 -- SOFT DELETE
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",

            // PHASE A -- location fields on projects + backfill
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            "UPDATE land_projects lp SET district = lt.district, county = lt.county " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL " +
                "AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)",

            // PHASE B -- projectIndex on projects + backfill
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",

            // PHASE F -- plot_number nullable
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",

            // PHASE G -- RETIRED TITLE DETAILS (pass 6): removed app-wide.
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

                try (java.sql.PreparedStatement ps = conn.prepareStatement(
                        "SELECT password, is_active FROM users WHERE username = 'admin_root'")) {
                    try (java.sql.ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            String storedHash = rs.getString("password");
                            boolean active = rs.getBoolean("is_active");
                            boolean matches = passwordEncoder.matches(rawPassword, storedHash);
                            System.out.println(">>> [REGISTRY] Post-write verification:");
                            System.out.println(">>>   is_active in DB = " + active);
                            System.out.println(">>>   BCrypt.matches(rawPassword, storedHash) = " + matches);
                            if (!matches) {
                                System.err.println(">>> [REGISTRY] FATAL: BCrypt verify FAILED after write! Check encoder config.");
                            } else {
                                System.out.println(">>> [REGISTRY] SUCCESS: Password verified. Login WILL work.");
                            }
                        } else {
                            System.err.println(">>> [REGISTRY] FATAL: admin_root row not found after write!");
                        }
                    }
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
# Report + commit + push
# =====================================================================
print(f"\n=== fix5.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)}")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'fix5: repair deploy — dedupe FolderPage import, full rewrites of StageTemplateService + DataInitializer (normalize + samples)'], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit {e.returncode})")
    except FileNotFoundError:
        print("\n  Git: not found")
print()