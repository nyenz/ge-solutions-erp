# PATH: fix.py
# PHASE B (Section 18.10 / 18.9.1): Null-safe the ~15 LandService.java call
# sites that read project.getLandTitle().getPlotNumber()/etc without a null
# check, rewrite atomicIntake() to build LandProject first and LandTitle only
# when title fields were submitted, and migrate projectIndex up from
# LandTitle to LandProject (deprecated in place on LandTitle, not deleted --
# same pattern as Phase A's district/county move) since Section 18.3 requires
# it on LandProject and the null-safe fallback needs it there to mean anything.
#
# Scope: LandProject.java, LandTitle.java, LandService.java,
# DataInitializer.java. No intake UI or DTO changes -- that's Phase D.
#
# Known gap, deliberately left alone: logNewNote() (line ~539) has the same
# unguarded project.getLandTitle().getPlotNumber() call as the 15 methods
# fixed here, but it was not in Section 18.9.1's list, so it is untouched.
# Flagging it for whoever picks up Phase C/D -- once titleless projects can
# actually be created (this phase makes that possible), adding a note to one
# will NPE the same way the fixed methods used to.

import os

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old not in content:
        print("MISSING: " + label + " (" + path + ")")
        return
    if content.count(old) > 1:
        print("MISSING: " + label + " -- old_str not unique in " + path)
        return
    content = content.replace(old, new)
    write_file(path, content)
    print("OK: " + label + " (" + path + ")")

LAND_PROJECT = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java"
LAND_TITLE = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java"
LAND_SERVICE = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"
DATA_INIT = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"

# =============================================================================
# 1. LandProject.java -- add projectIndex (moved up from LandTitle)
# =============================================================================

old_lp_field = "\n".join([
    "    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)",
    "    @JoinColumn(name = \"title_id\", nullable = true)",
    "    private LandTitle landTitle;",
    "",
    "    /**",
    "     * LOCATION (Section 18.4/18.9): permanent, not folder-only -- stays",
])

new_lp_field = "\n".join([
    "    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)",
    "    @JoinColumn(name = \"title_id\", nullable = true)",
    "    private LandTitle landTitle;",
    "",
    "    /**",
    "     * PROJECT INDEX (Section 18.3): short, never-repeating, searchable",
    "     * code shown to clients and staff (e.g. \"001A\"). Assigned at",
    "     * LandProject creation, before any title exists -- permanent and",
    "     * universal across a record's whole life, folder or titled. Moved up",
    "     * from LandTitle in Phase B (existing data migrated by",
    "     * DataInitializer below) because the null-safe audit-log fallback",
    "     * needs a project index that exists even when landTitle does not.",
    "     * LandTitle.projectIndex is deprecated, not deleted.",
    "     */",
    "    @Column(name = \"project_index\", unique = true, length = 10)",
    "    private String projectIndex;",
    "",
    "    /**",
    "     * LOCATION (Section 18.4/18.9): permanent, not folder-only -- stays",
])

patch(LAND_PROJECT, old_lp_field, new_lp_field,
      "LandProject: add projectIndex field")

# =============================================================================
# 2. LandTitle.java -- deprecate projectIndex in place, do NOT delete
# =============================================================================

old_title_index = "\n".join([
    "    @Column(name = \"project_index\", unique = true, length = 10)",
    "    private String projectIndex;",
])

new_title_index = "\n".join([
    "    // DEPRECATED (Phase B, Section 18.10/18.3): projectIndex now lives",
    "    // on LandProject and is assigned there at creation, before any title",
    "    // exists -- see LandProject.java. Kept here on purpose -- not",
    "    // deleted -- since atomicIntake() still writes the same value to",
    "    // both places for backward compatibility with anything still reading",
    "    // it off LandTitle. Safe to drop once nothing reads it from here.",
    "    @Deprecated",
    "    @Column(name = \"project_index\", unique = true, length = 10)",
    "    private String projectIndex;",
])

patch(LAND_TITLE, old_title_index, new_title_index,
      "LandTitle: mark projectIndex deprecated (not removed)")

# =============================================================================
# 3. DataInitializer.java -- migrate projectIndex to land_projects
# =============================================================================

old_init_tail = "\n".join([
    "            \"UPDATE land_projects lp SET district = lt.district, county = lt.county \" +",
    "                \"FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL \" +",
    "                \"AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)\",",
    "        };",
])

new_init_tail = "\n".join([
    "            \"UPDATE land_projects lp SET district = lt.district, county = lt.county \" +",
    "                \"FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL \" +",
    "                \"AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)\",",
    "",
    "            // PHASE B -- FOLDER-TO-TITLE REDESIGN (Section 18.10 / 18.3)",
    "            // projectIndex moves up to LandProject: Section 18.3 requires it",
    "            // be assigned at LandProject creation, before any title exists,",
    "            // and Phase B's null-safe audit-log fallback needs it to exist",
    "            // even when landTitle does not. land_titles.project_index is",
    "            // left in place (deprecated, not dropped).",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)\",",
    "            \"ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index)\",",
    "            // Backfill: copy each project's existing projectIndex up from",
    "            // its LandTitle via the title_id FK. Same \"IS NULL\" guard as",
    "            // the district/county backfill above -- safe on every boot,",
    "            // no-op once already copied.",
    "            \"UPDATE land_projects lp SET project_index = lt.project_index \" +",
    "                \"FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL \" +",
    "                \"AND lt.project_index IS NOT NULL\",",
    "        };",
])

patch(DATA_INIT, old_init_tail, new_init_tail,
      "DataInitializer: migrate projectIndex to land_projects")

# =============================================================================
# 4. LandService.java -- add plotLabel() helper, use it everywhere, rewrite
#    atomicIntake(), guard authorizeRelease(), guard updateProjectFull()
# =============================================================================

# --- 4a. Add the null-safe plotLabel() helper next to getCurrentOperator() ---

old_operator = "\n".join([
    "    private String getCurrentOperator() {",
    "        if (SecurityContextHolder.getContext().getAuthentication() != null) {",
    "            return SecurityContextHolder.getContext().getAuthentication().getName();",
    "        }",
    "        return \"SYSTEM\";",
    "    }",
])

new_operator = "\n".join([
    "    private String getCurrentOperator() {",
    "        if (SecurityContextHolder.getContext().getAuthentication() != null) {",
    "            return SecurityContextHolder.getContext().getAuthentication().getName();",
    "        }",
    "        return \"SYSTEM\";",
    "    }",
    "",
    "    // PHASE B (Section 18.9.1): landTitle can now be null. Every audit-log",
    "    // call site that used to read project.getLandTitle().getPlotNumber()",
    "    // directly goes through this instead -- falls back to projectIndex",
    "    // (now on LandProject itself, see Phase B migration) when there is no",
    "    // title yet, instead of NPE-ing.",
    "    private String plotLabel(LandProject project) {",
    "        if (project.getLandTitle() != null && project.getLandTitle().getPlotNumber() != null) {",
    "            return project.getLandTitle().getPlotNumber();",
    "        }",
    "        return \"project #\" + project.getProjectIndex();",
    "    }",
])

patch(LAND_SERVICE, old_operator, new_operator,
      "LandService: add plotLabel() null-safe helper")

# --- 4b. logUnlockAction ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"EDIT_MODE_OPENED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] opened edit mode for plot: \"",
        "            + project.getLandTitle().getPlotNumber());",
    ]),
    "\n".join([
        "        auditService.logAction(\"EDIT_MODE_OPENED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] opened edit mode for plot: \"",
        "            + plotLabel(project));",
    ]),
    "LandService.logUnlockAction: null-safe log")

# --- 4c. recordPayment: RECEIVABLE_EXIT branch ---

patch(LAND_SERVICE,
    "\n".join([
        "            auditService.logAction(\"RECEIVABLE_EXIT\",",
        "                \"Operator [\" + operator + \"] \u2014 Plot \" + project.getLandTitle().getPlotNumber()",
        "                + \" EXITED RECEIVABLE after full payment clearance.\");",
    ]),
    "\n".join([
        "            auditService.logAction(\"RECEIVABLE_EXIT\",",
        "                \"Operator [\" + operator + \"] \u2014 Plot \" + plotLabel(project)",
        "                + \" EXITED RECEIVABLE after full payment clearance.\");",
    ]),
    "LandService.recordPayment: null-safe RECEIVABLE_EXIT log")

# --- 4d. recordPayment: PAYMENT_RECORDED ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"PAYMENT_RECORDED\",",
        "            \"Operator [\" + operator + \"] recorded UGX \" + amount",
        "            + \" for plot: \" + project.getLandTitle().getPlotNumber()",
        "            + \" | Type: \" + paymentType",
        "            + \" | Amount owed after: UGX \" + balanceAfter);",
    ]),
    "\n".join([
        "        auditService.logAction(\"PAYMENT_RECORDED\",",
        "            \"Operator [\" + operator + \"] recorded UGX \" + amount",
        "            + \" for plot: \" + plotLabel(project)",
        "            + \" | Type: \" + paymentType",
        "            + \" | Amount owed after: UGX \" + balanceAfter);",
    ]),
    "LandService.recordPayment: null-safe PAYMENT_RECORDED log")

# --- 4e. moveToReceivable ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"RECEIVABLE_TRIGGER\",",
        "            \"Operator [\" + getCurrentOperator() + \"] manually moved plot \"",
        "            + project.getLandTitle().getPlotNumber()",
        "            + \" to RECEIVABLE. Original debt frozen at: UGX \" + outstanding);",
    ]),
    "\n".join([
        "        auditService.logAction(\"RECEIVABLE_TRIGGER\",",
        "            \"Operator [\" + getCurrentOperator() + \"] manually moved plot \"",
        "            + plotLabel(project)",
        "            + \" to RECEIVABLE. Original debt frozen at: UGX \" + outstanding);",
    ]),
    "LandService.moveToReceivable: null-safe log")

# --- 4f. exitReceivable ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"RECEIVABLE_EXIT\",",
        "            \"Operator [\" + getCurrentOperator() + \"] removed plot \"",
        "            + project.getLandTitle().getPlotNumber()",
        "            + \" from RECEIVABLE. \" + feeAction",
        "            + \". Title total value: UGX \" + project.getTotalCost() + \".\");",
    ]),
    "\n".join([
        "        auditService.logAction(\"RECEIVABLE_EXIT\",",
        "            \"Operator [\" + getCurrentOperator() + \"] removed plot \"",
        "            + plotLabel(project)",
        "            + \" from RECEIVABLE. \" + feeAction",
        "            + \". Title total value: UGX \" + project.getTotalCost() + \".\");",
    ]),
    "LandService.exitReceivable: null-safe log")

# --- 4g. atomicIntake: build LandProject first, LandTitle only if submitted ---

old_intake = "\n".join([
    "    @Transactional(rollbackFor = Exception.class)",
    "    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {",
    "        LandTitle title = LandTitle.builder()",
    "                .tenure(request.getTenure())",
    "                .plotNumber(request.getPlotNumber())",
    "                .physicalBoxNumber(request.getPhysicalBoxNumber())",
    "                .district(request.getDistrict())",
    "                .blockRoad(request.getBlockRoad())",
    "                .county(request.getCounty())",
    "                .volume(request.getVolume())",
    "                .folio(request.getFolio())",
    "                .instrumentNo(request.getInstrumentNo())",
    "                .surveyDate(request.getSurveyDate())",
    "                .projectIndex(projectIndexService.generateNextIndex())",
    "                .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())",
    "                .titleIssueDate(request.getTitleIssueDate())",
    "                .build();",
    "",
    "        BigDecimal initialPayment = request.getInitialPayment() != null",
    "                ? request.getInitialPayment() : BigDecimal.ZERO;",
    "        BigDecimal totalCost = request.getTotalCost() != null",
    "                ? request.getTotalCost() : BigDecimal.ZERO;",
    "        BigDecimal outstanding = totalCost.subtract(initialPayment);",
    "",
    "        boolean startAsReceivable = request.isStartAsReceivable();",
    "",
    "        LandProject.LandProjectBuilder builder = LandProject.builder()",
    "                .landTitle(title)",
    "                .totalCost(totalCost)",
    "                .amountPaid(initialPayment)",
    "                .isLegacy(request.isLegacy())",
    "                .currentStageIndex(startAsReceivable ? 5 : 1)",
    "                .status(startAsReceivable ? \"RECEIVABLE\" : \"ACTIVE\");",
])

new_intake = "\n".join([
    "    @Transactional(rollbackFor = Exception.class)",
    "    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {",
    "        // PHASE B (Section 18.10): LandProject is now built FIRST --",
    "        // projectIndex, owners, location, and stage all exist",
    "        // independently of a title. A LandTitle is only built and",
    "        // attached SECOND, and only if title fields were actually",
    "        // submitted. Using a non-blank plotNumber as that signal for",
    "        // now -- a real \"attach title later, on the final stage",
    "        // checkbox\" trigger is Phase D's job, not this phase's.",
    "        boolean hasTitleFields = request.getPlotNumber() != null && !request.getPlotNumber().isBlank();",
    "        String projectIndex = projectIndexService.generateNextIndex();",
    "",
    "        BigDecimal initialPayment = request.getInitialPayment() != null",
    "                ? request.getInitialPayment() : BigDecimal.ZERO;",
    "        BigDecimal totalCost = request.getTotalCost() != null",
    "                ? request.getTotalCost() : BigDecimal.ZERO;",
    "        BigDecimal outstanding = totalCost.subtract(initialPayment);",
    "",
    "        boolean startAsReceivable = request.isStartAsReceivable();",
    "",
    "        LandTitle title = null;",
    "        if (hasTitleFields) {",
    "            title = LandTitle.builder()",
    "                    .tenure(request.getTenure())",
    "                    .plotNumber(request.getPlotNumber())",
    "                    .physicalBoxNumber(request.getPhysicalBoxNumber())",
    "                    .district(request.getDistrict())",
    "                    .blockRoad(request.getBlockRoad())",
    "                    .county(request.getCounty())",
    "                    .volume(request.getVolume())",
    "                    .folio(request.getFolio())",
    "                    .instrumentNo(request.getInstrumentNo())",
    "                    .surveyDate(request.getSurveyDate())",
    "                    // Kept in sync on the deprecated LandTitle column too,",
    "                    // for backward compatibility with anything still",
    "                    // reading projectIndex off LandTitle instead of",
    "                    // LandProject.",
    "                    .projectIndex(projectIndex)",
    "                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())",
    "                    .titleIssueDate(request.getTitleIssueDate())",
    "                    .build();",
    "        }",
    "",
    "        LandProject.LandProjectBuilder builder = LandProject.builder()",
    "                .landTitle(title)",
    "                .projectIndex(projectIndex)",
    "                .district(request.getDistrict())",
    "                .county(request.getCounty())",
    "                .totalCost(totalCost)",
    "                .amountPaid(initialPayment)",
    "                .isLegacy(request.isLegacy())",
    "                .currentStageIndex(startAsReceivable ? 5 : 1)",
    "                .status(startAsReceivable ? \"RECEIVABLE\" : \"ACTIVE\");",
])

patch(LAND_SERVICE, old_intake, new_intake,
      "LandService.atomicIntake: build LandProject first, LandTitle only if submitted")

# --- 4h. atomicIntake: null-safe final audit logs (still refer to "title") ---

patch(LAND_SERVICE,
    "\n".join([
        "        String receivableNote = startAsReceivable ? \" [ENTERED AS RECEIVABLE]\" : \"\";",
        "        auditService.logAction(\"INTAKE\",",
        "            \"Operator [\" + getCurrentOperator() + \"] ingested binder: \"",
        "            + title.getPlotNumber() + receivableNote);",
        "",
        "        if (startAsReceivable) {",
        "            auditService.logAction(\"RECEIVABLE_TRIGGER\",",
        "                \"Operator [\" + getCurrentOperator() + \"] flagged plot \"",
        "                + title.getPlotNumber() + \" as RECEIVABLE at intake. Debt: UGX \" + outstanding);",
        "        }",
    ]),
    "\n".join([
        "        String plotOrIndex = title != null ? title.getPlotNumber() : \"project #\" + projectIndex;",
        "        String receivableNote = startAsReceivable ? \" [ENTERED AS RECEIVABLE]\" : \"\";",
        "        auditService.logAction(\"INTAKE\",",
        "            \"Operator [\" + getCurrentOperator() + \"] ingested binder: \"",
        "            + plotOrIndex + receivableNote);",
        "",
        "        if (startAsReceivable) {",
        "            auditService.logAction(\"RECEIVABLE_TRIGGER\",",
        "                \"Operator [\" + getCurrentOperator() + \"] flagged plot \"",
        "                + plotOrIndex + \" as RECEIVABLE at intake. Debt: UGX \" + outstanding);",
        "        }",
    ]),
    "LandService.atomicIntake: null-safe final audit logs")

# --- 4i. updateProjectFull: skip title-field setters when landTitle is null ---

patch(LAND_SERVICE,
    "\n".join([
        "        LandTitle title = project.getLandTitle();",
        "",
        "        title.setPlotNumber(request.getPlotNumber());",
        "        title.setTenure(request.getTenure());",
        "        title.setBlockRoad(request.getBlockRoad());",
        "        title.setDistrict(request.getDistrict());",
        "        title.setCounty(request.getCounty());",
        "        title.setVolume(request.getVolume());",
        "        title.setFolio(request.getFolio());",
        "        title.setInstrumentNo(request.getInstrumentNo());",
        "        title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());",
        "        title.setSurveyDate(request.getSurveyDate());",
    ]),
    "\n".join([
        "        LandTitle title = project.getLandTitle();",
        "",
        "        // PHASE B (Section 18.9.1): landTitle can now be null (a",
        "        // titleless \"folder\" stage project). Skip the title-field",
        "        // setters entirely when there is no title yet -- everything",
        "        // else on this project (owners, cost, legacy flag) still",
        "        // updates normally below. Real create-a-title-on-edit logic",
        "        // is Phase D/E's job, not this phase's.",
        "        if (title != null) {",
        "            title.setPlotNumber(request.getPlotNumber());",
        "            title.setTenure(request.getTenure());",
        "            title.setBlockRoad(request.getBlockRoad());",
        "            title.setDistrict(request.getDistrict());",
        "            title.setCounty(request.getCounty());",
        "            title.setVolume(request.getVolume());",
        "            title.setFolio(request.getFolio());",
        "            title.setInstrumentNo(request.getInstrumentNo());",
        "            title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());",
        "            title.setSurveyDate(request.getSurveyDate());",
        "        }",
    ]),
    "LandService.updateProjectFull: skip title setters when landTitle is null")

# --- 4j. updateProjectFull: null-safe final log ---

patch(LAND_SERVICE,
    "\n".join([
        "        LandProject saved = projectRepository.save(project);",
        "        auditService.logAction(\"RECORD_UPDATED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] modified Binder: \"",
        "            + title.getPlotNumber());",
        "        return saved;",
        "    }",
    ]),
    "\n".join([
        "        LandProject saved = projectRepository.save(project);",
        "        auditService.logAction(\"RECORD_UPDATED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] modified Binder: \"",
        "            + plotLabel(project));",
        "        return saved;",
        "    }",
    ]),
    "LandService.updateProjectFull: null-safe final log")

# --- 4k. nuclearDelete ---

patch(LAND_SERVICE,
    "\n".join([
        "    public void nuclearDelete(UUID id) {",
        "        LandProject project = projectRepository.findById(id).orElseThrow();",
        "        String plotNo = project.getLandTitle().getPlotNumber();",
        "",
        "        project.setDeleted(true);",
        "        project.setDeletedAt(LocalDateTime.now());",
        "        projectRepository.save(project);",
        "",
        "        auditService.logAction(\"RECORD_DELETED\",",
        "            \"Root user [\" + getCurrentOperator() + \"] deleted plot: \" + plotNo);",
        "    }",
    ]),
    "\n".join([
        "    public void nuclearDelete(UUID id) {",
        "        LandProject project = projectRepository.findById(id).orElseThrow();",
        "        String plotNo = plotLabel(project);",
        "",
        "        project.setDeleted(true);",
        "        project.setDeletedAt(LocalDateTime.now());",
        "        projectRepository.save(project);",
        "",
        "        auditService.logAction(\"RECORD_DELETED\",",
        "            \"Root user [\" + getCurrentOperator() + \"] deleted plot: \" + plotNo);",
        "    }",
    ]),
    "LandService.nuclearDelete: null-safe log")

# --- 4l. restoreProject ---

patch(LAND_SERVICE,
    "\n".join([
        "    public void restoreProject(UUID id) {",
        "        LandProject project = projectRepository.findById(id).orElseThrow();",
        "        String plotNo = project.getLandTitle().getPlotNumber();",
        "",
        "        project.setDeleted(false);",
        "        project.setDeletedAt(null);",
        "        projectRepository.save(project);",
        "",
        "        auditService.logAction(\"RECORD_RESTORED\",",
        "            \"Root user [\" + getCurrentOperator() + \"] restored plot: \" + plotNo);",
        "    }",
    ]),
    "\n".join([
        "    public void restoreProject(UUID id) {",
        "        LandProject project = projectRepository.findById(id).orElseThrow();",
        "        String plotNo = plotLabel(project);",
        "",
        "        project.setDeleted(false);",
        "        project.setDeletedAt(null);",
        "        projectRepository.save(project);",
        "",
        "        auditService.logAction(\"RECORD_RESTORED\",",
        "            \"Root user [\" + getCurrentOperator() + \"] restored plot: \" + plotNo);",
        "    }",
    ]),
    "LandService.restoreProject: null-safe log")

# --- 4m. manualRealityOverride ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"STAGE_OVERRIDE\",",
        "            \"Operator [\" + getCurrentOperator() + \"] shifted plot \"",
        "            + project.getLandTitle().getPlotNumber()",
        "            + \" from stage \" + oldStage + \" to stage \" + targetStage);",
    ]),
    "\n".join([
        "        auditService.logAction(\"STAGE_OVERRIDE\",",
        "            \"Operator [\" + getCurrentOperator() + \"] shifted plot \"",
        "            + plotLabel(project)",
        "            + \" from stage \" + oldStage + \" to stage \" + targetStage);",
    ]),
    "LandService.manualRealityOverride: null-safe log")

# --- 4n. authorizeRelease: guard + null-safe (title guaranteed non-null past guard) ---

patch(LAND_SERVICE,
    "\n".join([
        "        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {",
        "            throw new BusinessException(\"RELEASE DENIED: Arrears Detected.\");",
        "        }",
        "        project.getLandTitle().setReleased(true);",
    ]),
    "\n".join([
        "        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {",
        "            throw new BusinessException(\"RELEASE DENIED: Arrears Detected.\");",
        "        }",
        "        // PHASE B (Section 18.9.1): landTitle can now be null.",
        "        // Releasing implies a title exists to hand over -- silently",
        "        // succeeding when there is nothing to release would be",
        "        // misleading to staff, so this fails loudly instead of NPE-ing.",
        "        if (project.getLandTitle() == null) {",
        "            throw new BusinessException(\"RELEASE DENIED: This project has no title to release yet.\");",
        "        }",
        "        project.getLandTitle().setReleased(true);",
    ]),
    "LandService.authorizeRelease: guard against null landTitle")

# --- 4o. setStoragePaused ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"STORAGE_FEE_\" + action,",
        "            \"Operator [\" + getCurrentOperator() + \"] \" + action.toLowerCase() + \" monthly storage fees for plot: \"",
        "            + project.getLandTitle().getPlotNumber()",
        "            + \" (monthly rate: UGX \" + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : \"50000 (default)\") + \")\");",
    ]),
    "\n".join([
        "        auditService.logAction(\"STORAGE_FEE_\" + action,",
        "            \"Operator [\" + getCurrentOperator() + \"] \" + action.toLowerCase() + \" monthly storage fees for plot: \"",
        "            + plotLabel(project)",
        "            + \" (monthly rate: UGX \" + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : \"50000 (default)\") + \")\");",
    ]),
    "LandService.setStoragePaused: null-safe log")

# --- 4p. setStorageFeeOverride ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"STORAGE_RATE_CHANGED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] changed monthly storage fee to UGX \" + rate",
        "            + \" for plot: \" + project.getLandTitle().getPlotNumber()",
        "            + \" (previously UGX \" + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : \"50000 (default)\") + \")\");",
    ]),
    "\n".join([
        "        auditService.logAction(\"STORAGE_RATE_CHANGED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] changed monthly storage fee to UGX \" + rate",
        "            + \" for plot: \" + plotLabel(project)",
        "            + \" (previously UGX \" + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : \"50000 (default)\") + \")\");",
    ]),
    "LandService.setStorageFeeOverride: null-safe log")

# --- 4q. setAccumulatedFees ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"STORAGE_FEES_ADJUSTED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] manually adjusted accumulated storage fees from UGX \" + old",
        "            + \" to UGX \" + amount + \" for plot: \" + project.getLandTitle().getPlotNumber());",
    ]),
    "\n".join([
        "        auditService.logAction(\"STORAGE_FEES_ADJUSTED\",",
        "            \"Operator [\" + getCurrentOperator() + \"] manually adjusted accumulated storage fees from UGX \" + old",
        "            + \" to UGX \" + amount + \" for plot: \" + plotLabel(project));",
    ]),
    "LandService.setAccumulatedFees: null-safe log")

# --- 4r. setNegotiationDeadline: CLEARED branch ---

patch(LAND_SERVICE,
    "\n".join([
        "            auditService.logAction(\"NEGOTIATION_DEADLINE_CLEARED\",",
        "                \"Operator [\" + getCurrentOperator() + \"] cleared negotiation deadline for plot: \"",
        "                + project.getLandTitle().getPlotNumber() + \" -- storage fees resumed.\");",
    ]),
    "\n".join([
        "            auditService.logAction(\"NEGOTIATION_DEADLINE_CLEARED\",",
        "                \"Operator [\" + getCurrentOperator() + \"] cleared negotiation deadline for plot: \"",
        "                + plotLabel(project) + \" -- storage fees resumed.\");",
    ]),
    "LandService.setNegotiationDeadline: null-safe CLEARED log")

# --- 4s. setNegotiationDeadline: SET branch ---

patch(LAND_SERVICE,
    "\n".join([
        "            auditService.logAction(\"NEGOTIATION_DEADLINE_SET\",",
        "                \"Operator [\" + getCurrentOperator() + \"] set negotiation deadline to \" + deadlineStr",
        "                + \" for plot: \" + project.getLandTitle().getPlotNumber()",
        "                + \" -- storage fees paused until then.\");",
    ]),
    "\n".join([
        "            auditService.logAction(\"NEGOTIATION_DEADLINE_SET\",",
        "                \"Operator [\" + getCurrentOperator() + \"] set negotiation deadline to \" + deadlineStr",
        "                + \" for plot: \" + plotLabel(project)",
        "                + \" -- storage fees paused until then.\");",
    ]),
    "LandService.setNegotiationDeadline: null-safe SET log")

# --- 4t. setReceivableStartOverride ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"RECEIVABLE_START_OVERRIDDEN\",",
        "            \"Operator [\" + getCurrentOperator() + \"] set receivable start date to \" + startDateStr",
        "            + \" for plot: \" + project.getLandTitle().getPlotNumber());",
    ]),
    "\n".join([
        "        auditService.logAction(\"RECEIVABLE_START_OVERRIDDEN\",",
        "            \"Operator [\" + getCurrentOperator() + \"] set receivable start date to \" + startDateStr",
        "            + \" for plot: \" + plotLabel(project));",
    ]),
    "LandService.setReceivableStartOverride: null-safe log")

# --- 4u. logFollowUp ---

patch(LAND_SERVICE,
    "\n".join([
        "        auditService.logAction(\"RECOVERY_SYNC\",",
        "            \"Operator [\" + operator + \"] logged call for plot: \"",
        "            + project.getLandTitle().getPlotNumber() + \" (owner reached: \" + ownerId + \")\");",
    ]),
    "\n".join([
        "        auditService.logAction(\"RECOVERY_SYNC\",",
        "            \"Operator [\" + operator + \"] logged call for plot: \"",
        "            + plotLabel(project) + \" (owner reached: \" + ownerId + \")\");",
    ]),
    "LandService.logFollowUp: null-safe log")

# ---------------------------------------------------------------------------
# Commit and push (PERMANENT rule, Section 3)
# ---------------------------------------------------------------------------
import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m',
    'Phase B (Section 18.10): null-safe LandService audit logging for optional '
    'landTitle, rewrite atomicIntake to build LandProject first, migrate '
    'projectIndex up from LandTitle to LandProject'])
subprocess.run(['git', 'push'])