#!/usr/bin/env python3
import os
import subprocess

# Ensure we are in the repo root (where .git exists)
if os.path.exists(".git"):
    pass # already in repo root
elif os.path.exists("ge-solutions-erp"):
    os.chdir("ge-solutions-erp")
else:
    print("Error: Run this script from inside the ge-solutions-erp repository.")
    exit(1)

def patch_file(path, old, new):
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        return
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    if old not in content:
        print(f"MISSING in {path}: {old[:50]}...")
        return
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

# 1. LandTitle.java - Make plot_number nullable for bulk empty titles
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java",
    '    @Column(name = "plot_number", unique = true, nullable = false, length = 100)',
    '    @Column(name = "plot_number", unique = true, length = 100)'
)

# 2. DataInitializer.java - Postgres migration for plot_number DROP NOT NULL
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
    '            "UPDATE land_projects lp SET project_index = lt.project_index " +\n                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +\n                "AND lt.project_index IS NOT NULL",',
    '            "UPDATE land_projects lp SET project_index = lt.project_index " +\n                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +\n                "AND lt.project_index IS NOT NULL",\n\n            // PHASE F -- FOLDER-TO-TITLE REDESIGN (Section 18.10)\n            // Make plot_number nullable so bulk title-produced action can\n            // attach an empty LandTitle record to unlock fields before\n            // the unique plot numbers are known.\n            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",'
)

# 3. LandProject.java - Add transient stages list
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java",
    '    @Column(length = 100)\n    private String area;\n\n    @Builder.Default\n    @ManyToMany(fetch = FetchType.EAGER)',
    '    @Column(length = 100)\n    private String area;\n\n    @Transient\n    @Builder.Default\n    private java.util.List<ProjectStage> stages = new java.util.ArrayList<>();\n\n    @Builder.Default\n    @ManyToMany(fetch = FetchType.EAGER)'
)

# 4. LandService.java - Inject repo, attach stages, bulk method
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
    '    private final ProjectIndexService projectIndexService;\n    private final StageTemplateService stageTemplateService;',
    '    private final ProjectIndexService projectIndexService;\n    private final StageTemplateService stageTemplateService;\n    private final ProjectStageRepository projectStageRepository;'
)

patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
    '    public Page<LandProject> getGlobalLedger(Pageable pageable) {\n        return projectRepository.findAll(pageable);\n    }',
    '    public Page<LandProject> getGlobalLedger(Pageable pageable) {\n        Page<LandProject> page = projectRepository.findAll(pageable);\n        page.getContent().forEach(p -> p.setStages(projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(p.getId())));\n        return page;\n    }\n\n    @Transactional\n    @PreAuthorize("hasAnyRole(\'ROLE_MANAGER\', \'ROLE_ADMIN\', \'ROLE_DIRECTOR\')")\n    public int bulkMarkTitleProduced(java.util.List<java.util.UUID> projectIds) {\n        if (projectIds == null || projectIds.isEmpty()) return 0;\n        int count = 0;\n        for (java.util.UUID id : projectIds) {\n            LandProject project = projectRepository.findById(id).orElse(null);\n            if (project != null && project.getLandTitle() == null) {\n                LandTitle title = LandTitle.builder()\n                        .tenure("FREEHOLD")\n                        .projectStartDate(java.time.LocalDate.now())\n                        .projectIndex(project.getProjectIndex())\n                        .build();\n                project.setLandTitle(title);\n                projectRepository.save(project);\n\n                java.util.List<ProjectStage> stages = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(id);\n                for (ProjectStage stage : stages) {\n                    if (stage.getStageName() != null && stage.getStageName().toLowerCase().contains("registration")) {\n                        stage.setCompleted(true);\n                        stage.setCompletedAt(java.time.LocalDateTime.now());\n                        projectStageRepository.save(stage);\n                    }\n                }\n                count++;\n            }\n        }\n        auditService.logAction("BULK_TITLE_PRODUCED", \n            "Operator [" + getCurrentOperator() + "] marked " + count + " projects as title-produced.");\n        return count;\n    }'
)

# 5. LandController.java - Add bulk endpoint
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
    '    @PatchMapping("/projects/{id}/release")',
    '    @PreAuthorize("hasAnyRole(\'ROLE_MANAGER\', \'ROLE_ADMIN\', \'ROLE_DIRECTOR\')")\n    @PostMapping("/projects/bulk-mark-title-produced")\n    public ResponseEntity<Integer> bulkMarkTitleProduced(@RequestBody List<UUID> projectIds) {\n        return ResponseEntity.ok(landService.bulkMarkTitleProduced(projectIds));\n    }\n\n    @PatchMapping("/projects/{id}/release")'
)

# 6. landService.js - Add bulk method
patch_file(
    "erp-frontend/src/services/landService.js",
    '    getGlobalLedger: async (page = 0, size = 50) => {\n        const response = await api.get(\'/land/ledger\', { params: { page, size } });\n        return response.data;\n    },',
    '    getGlobalLedger: async (page = 0, size = 50) => {\n        const response = await api.get(\'/land/ledger\', { params: { page, size } });\n        return response.data;\n    },\n\n    bulkMarkTitleProduced: async (projectIds) => {\n        const response = await api.post(\'/land/projects/bulk-mark-title-produced\', projectIds);\n        return response.data;\n    },'
)

# 7. LedgerPage.module.css - Status tags and bulk button styles
patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.module.css",
    '.pageBtn:disabled { opacity: 0.18; cursor: not-allowed; }',
    '.pageBtn:disabled { opacity: 0.18; cursor: not-allowed; }\n\n/* PHASE F: STATUS TAGS & BULK ACTIONS */\n.statusTagFolder {\n    display: inline-block;\n    font-family: \'DM Sans\', sans-serif;\n    font-size: var(--fs-tag);\n    font-weight: 900;\n    color: #EE8C3A;\n    background: rgba(238,140,58,0.12);\n    border: 1px solid rgba(238,140,58,0.3);\n    padding: 2px 6px;\n    border-radius: 4px;\n    text-transform: uppercase;\n    letter-spacing: 0.5px;\n    margin-left: 6px;\n}\n.statusTagTitled {\n    display: inline-block;\n    font-family: \'DM Sans\', sans-serif;\n    font-size: var(--fs-tag);\n    font-weight: 900;\n    color: #a78bfa;\n    background: rgba(139,92,246,0.12);\n    border: 1px solid rgba(139,92,246,0.3);\n    padding: 2px 6px;\n    border-radius: 4px;\n    text-transform: uppercase;\n    letter-spacing: 0.5px;\n    margin-left: 6px;\n}\n.bulkActionBtn {\n    display: inline-flex;\n    align-items: center;\n    gap: clamp(4px, 0.5vw, 6px);\n    padding: clamp(6px, 0.8vw, 8px) clamp(10px, 1.5vw, 14px);\n    background: rgba(139,92,246,0.12);\n    border: 1px solid rgba(139,92,246,0.4);\n    border-radius: 6px;\n    color: #a78bfa;\n    font-family: \'DM Sans\', sans-serif;\n    font-size: var(--fs-tag);\n    font-weight: 900;\n    text-transform: uppercase;\n    letter-spacing: 1px;\n    cursor: pointer;\n    transition: all 0.2s;\n}\n.bulkActionBtn:hover {\n    background: rgba(139,92,246,0.25);\n    border-color: rgba(139,92,246,0.6);\n    color: #c4b5fd;\n}\n.bulkActionBtn:disabled {\n    opacity: 0.4;\n    cursor: not-allowed;\n}'
)

# 8. LedgerPage.jsx - State, filter, logic, and UI updates
patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '    const [activeFilter, setActiveFilter] = useState(\'ALL\');',
    '    const [activeFilter, setActiveFilter] = useState(\'ALL\');\n    const [selectedIds, setSelectedIds] = useState(new Set());\n    const [bulkProcessing, setBulkProcessing] = useState(false);'
)

patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '    { key: \'CRITICAL\', label: \'CRITICAL\'       },\n];',
    '    { key: \'CRITICAL\', label: \'CRITICAL\'       },\n    { key: \'READY_FOR_TITLING\', label: \'READY FOR TITLING\' },\n];'
)

patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '    if (activeFilter === \'CRITICAL\') filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && (p.amountPaid / p.totalCost) < 0.25);',
    '    if (activeFilter === \'CRITICAL\') filtered = filtered.filter(p => !p.isReceivable && p.totalCost > 0 && (p.amountPaid / p.totalCost) < 0.25);\n    if (activeFilter === \'READY_FOR_TITLING\') {\n        filtered = filtered.filter(p => {\n            if (p.landTitle) return false;\n            const stages = p.stages || [];\n            if (stages.length === 0) return false;\n            const finalStage = stages.find(s => (s.stageName || \'\').toLowerCase().includes(\'registration\'));\n            if (!finalStage) return false;\n            const priorStages = stages.filter(s => s.id !== finalStage.id);\n            const allPriorComplete = priorStages.every(s => s.isCompleted);\n            const finalOutstanding = !finalStage.isCompleted;\n            const finalCheckedButEmpty = finalStage.isCompleted && !p.landTitle;\n            return (allPriorComplete && finalOutstanding) || finalCheckedButEmpty;\n        });\n    }'
)

patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '    const handleSort = (key) => {',
    '    const isReadyForTitling = (p) => {\n        if (p.landTitle) return false;\n        const stages = p.stages || [];\n        if (stages.length === 0) return false;\n        const finalStage = stages.find(s => (s.stageName || \'\').toLowerCase().includes(\'registration\'));\n        if (!finalStage) return false;\n        const priorStages = stages.filter(s => s.id !== finalStage.id);\n        const allPriorComplete = priorStages.every(s => s.isCompleted);\n        const finalOutstanding = !finalStage.isCompleted;\n        const finalCheckedButEmpty = finalStage.isCompleted && !p.landTitle;\n        return (allPriorComplete && finalOutstanding) || finalCheckedButEmpty;\n    };\n\n    const handleBulkMark = async () => {\n        setBulkProcessing(true);\n        try {\n            await landService.bulkMarkTitleProduced([...selectedIds]);\n            await fetchLedger();\n            setSelectedIds(new Set());\n        } catch (e) {\n            console.error(e);\n        } finally {\n            setBulkProcessing(false);\n        }\n    };\n\n    const toggleSelect = (id, e) => {\n        e.stopPropagation();\n        setSelectedIds(prev => {\n            const next = new Set(prev);\n            if (next.has(id)) next.delete(id);\n            else next.add(id);\n            return next;\n        });\n    };\n\n    const toggleSelectAll = () => {\n        const readyIds = new Set(processedData.map(p => p.id));\n        const allSelected = processedData.length > 0 && processedData.every(p => selectedIds.has(p.id));\n        if (allSelected) setSelectedIds(new Set());\n        else setSelectedIds(readyIds);\n    };\n\n    const handleSort = (key) => {'
)

patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '                </div>\n\n                {/* BADGE LEGEND */}',
    '                </div>\n\n                {activeFilter === \'READY_FOR_TITLING\' && selectedIds.size > 0 && (\n                    <div style={{ marginTop: \'12px\', display: \'flex\', alignItems: \'center\', gap: \'12px\' }}>\n                        <span style={{ fontFamily: "\'DM Sans\', sans-serif", fontSize: \'10px\', fontWeight: 900, color: \'#a78bfa\', textTransform: \'uppercase\', letterSpacing: \'1px\' }}>\n                            {selectedIds.size} RECORD{selectedIds.size > 1 ? \'S\' : \'\'} SELECTED\n                        </span>\n                        <button className={styles.bulkActionBtn} onClick={handleBulkMark} disabled={bulkProcessing}>\n                            {bulkProcessing ? \'PROCESSING...\' : \'MARK AS TITLE-PRODUCED\'}\n                        </button>\n                    </div>\n                )}\n\n                {/* BADGE LEGEND */}'
)

patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '                            <tr>\n                                <th onClick={() => handleSort(\'plotNumber\')} className={styles.sortable}',
    '                            <tr>\n                                {activeFilter === \'READY_FOR_TITLING\' && (\n                                    <th style={{width: \'30px\'}}>\n                                        <input \n                                            type="checkbox" \n                                            onChange={toggleSelectAll} \n                                            checked={processedData.length > 0 && processedData.every(p => selectedIds.has(p.id))} \n                                            onClick={e => e.stopPropagation()} \n                                        />\n                                    </th>\n                                )}\n                                <th onClick={() => handleSort(\'plotNumber\')} className={styles.sortable}'
)

patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '<td colSpan="5"',
    '<td colSpan={activeFilter === \'READY_FOR_TITLING\' ? 6 : 5}'
)

patch_file(
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    '                        >\n                            <td className={styles.plotCell}>\n                                <div style={{ display: \'flex\', alignItems: \'flex-start\', gap: 6 }}>\n                                    <PaymentDot proj={proj} />\n                                    <div>\n                                        <strong>{proj.landTitle?.plotNumber || \'---\'}</strong>\n                                        {proj.landTitle?.projectIndex && (\n                                            <span className={styles.districtTag}> #{proj.landTitle.projectIndex}</span>\n                                        )}',
    '                        >\n                            {activeFilter === \'READY_FOR_TITLING\' && (\n                                <td onClick={e => e.stopPropagation()}>\n                                    <input \n                                        type="checkbox" \n                                        checked={selectedIds.has(proj.id)} \n                                        onChange={(e) => toggleSelect(proj.id, e)} \n                                    />\n                                </td>\n                            )}\n                            <td className={styles.plotCell}>\n                                <div style={{ display: \'flex\', alignItems: \'flex-start\', gap: 6 }}>\n                                    <PaymentDot proj={proj} />\n                                    <div>\n                                        <strong>{proj.landTitle?.plotNumber || \'---\'}</strong>\n                                        {(proj.projectIndex || proj.landTitle?.projectIndex) && (\n                                            <span className={styles.districtTag}> #{proj.projectIndex || proj.landTitle.projectIndex}</span>\n                                        )}\n                                        <span className={proj.landTitle ? styles.statusTagTitled : styles.statusTagFolder}>\n                                            {proj.landTitle ? \'TITLED\' : \'FOLDER\'}\n                                        </span>'
)

# Git commit and push
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', 'Phase F: Ledger status tag + Ready for Titling view + bulk mark action'])
subprocess.run(['git', 'push'])