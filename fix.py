# PATH: fix.py
# SMART PATCHER FOR DATE TRACKING SYSTEM (PHASE 1.5)
# This version uses flexible insertion logic instead of exact string matching.

import os
import re

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

print("Starting Smart Patching for Date Tracking System...")
print("-" * 50)

# 1. Backend: DataInitializer.java (Migration)
path_db = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"
content_db = read_file(path_db)
if content_db:
    anchor = 'ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index)",'
    new_migration = '''
            // PHASE 1.5 - DATE TRACKING
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",'''
    
    if anchor in content_db:
        if "project_start_date" in content_db:
            print("SKIP: 1/7 Database Migration (Already applied)")
        else:
            lines = content_db.split('\n')
            new_content = []
            for line in lines:
                new_content.append(line)
                if anchor in line:
                    new_content.append(new_migration)
            write_file(path_db, '\n'.join(new_content))
            print("OK: 1/7 Database Migration")
    else:
        print("FAIL: 1/7 Database Migration (Anchor not found)")

# 2. Backend: LandTitle.java (Entity Fields)
path_entity = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java"
content_entity = read_file(path_entity)
if content_entity:
    if "projectStartDate" in content_entity:
        print("SKIP: 2/7 LandTitle.java (Fields exist)")
    else:
        anchor = "private LocalDate surveyDate;"
        new_fields = '''
    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;
'''
        if anchor in content_entity:
            content_entity = content_entity.replace(anchor, anchor + new_fields)
            write_file(path_entity, content_entity)
            print("OK: 2/7 LandTitle.java")
        else:
            print("FAIL: 2/7 LandTitle.java")

# 3. Backend: LandEntryRequest.java (DTO Fields)
path_dto = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java"
content_dto = read_file(path_dto)
if content_dto:
    if "projectStartDate" in content_dto:
        print("SKIP: 3/7 LandEntryRequest.java")
    else:
        anchor = "private LocalDate surveyDate;"
        new_dto_fields = '''    private LocalDate projectStartDate;
    private LocalDate titleIssueDate;
'''
        if anchor in content_dto:
            content_dto = content_dto.replace(anchor, anchor + "\n" + new_dto_fields)
            write_file(path_dto, content_dto)
            print("OK: 3/7 LandEntryRequest.java")
        else:
            print("FAIL: 3/7 LandEntryRequest.java")

# 4. Backend: LandService.java (Auto-fill logic)
path_service = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"
content_service = read_file(path_service)
if content_service:
    if ".projectStartDate" in content_service:
        print("SKIP: 4/7 LandService.java")
    else:
        old_build = ".projectIndex(projectIndexService.generateNextIndex())\n                .build();"
        new_build = """.projectIndex(projectIndexService.generateNextIndex())
                .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())
                .titleIssueDate(request.getTitleIssueDate())
                .build();"""
        
        if old_build in content_service:
            content_service = content_service.replace(old_build, new_build)
            write_file(path_service, content_service)
            print("OK: 4/7 LandService.java")
        else:
            print("FAIL: 4/7 LandService.java")

# 5. Frontend: IntakePage.jsx
intake_paths = [
    "erp-frontend/src/pages/LandIntake/IntakePage.jsx",
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    "erp-frontend/src/pages/LandIntakePage.jsx"
]
path_intake = None
for p in intake_paths:
    if os.path.isfile(p):
        path_intake = p
        break

if path_intake:
    content_intake = read_file(path_intake)
    
    # 5a: State
    if "projectStartDate:" in content_intake:
        print("SKIP: 5a/7 Intake State")
    else:
        anchor_state = "surveyDate: '',"
        new_state = """
        projectStartDate: new Date().toISOString().split('T')[0],
        titleIssueDate: '',"""
        if anchor_state in content_intake:
            content_intake = content_intake.replace(anchor_state, anchor_state + new_state)
            print("OK: 5a/7 Intake State")
        else:
            print("FAIL: 5a/7 Intake State")

    # 5b: Form Inputs
    if 'id="projectStartDate"' in content_intake:
        print("SKIP: 5b/7 Intake Form")
    else:
        anchor_actions = '<div className={styles.formActions}>'
        new_inputs = """
                    <div className={styles.formGroup}>
                        <label htmlFor="projectStartDate">Project Start Date *</label>
                        <input
                            type="date"
                            id="projectStartDate"
                            value={formData.projectStartDate}
                            onChange={(e) => setFormData({ ...formData, projectStartDate: e.target.value })}
                            required
                        />
                        <small>Auto-filled with today. Edit if started earlier.</small>
                    </div>

                    <div className={styles.formGroup}>
                        <label htmlFor="titleIssueDate">Title Issue Date (Optional)</label>
                        <input
                            type="date"
                            id="titleIssueDate"
                            value={formData.titleIssueDate}
                            onChange={(e) => setFormData({ ...formData, titleIssueDate: e.target.value })}
                        />
                        <small>Leave blank if not received. Can be backdated.</small>
                    </div>
"""
        if anchor_actions in content_intake:
            content_intake = content_intake.replace(anchor_actions, new_inputs + "\n                    " + anchor_actions)
            print("OK: 5b/7 Intake Form")
        else:
            print("FAIL: 5b/7 Intake Form")

    # 5c: Submit Payload
    if "projectStartDate:" in content_intake and "payload" in content_intake.lower():
        print("SKIP: 5c/7 Intake Submit")
    else:
        anchor_payload = "surveyDate: formData.surveyDate || null,"
        new_payload = """
            projectStartDate: formData.projectStartDate || null,
            titleIssueDate: formData.titleIssueDate || null,"""
        if anchor_payload in content_intake:
            content_intake = content_intake.replace(anchor_payload, anchor_payload + new_payload)
            write_file(path_intake, content_intake)
            print("OK: 5c/7 Intake Submit")
        else:
            write_file(path_intake, content_intake)
            print("WARN: 5c/7 Intake Submit (Payload anchor missing)")

# 6. Frontend: LedgerPage.jsx
ledger_paths = [
    "erp-frontend/src/pages/Ledger/LedgerPage.jsx",
    "erp-frontend/src/pages/LedgerPage.jsx"
]
path_ledger = None
for p in ledger_paths:
    if os.path.isfile(p):
        path_ledger = p
        break

if path_ledger:
    content_ledger = read_file(path_ledger)
    
    # 6a: Headers
    if "START DATE" in content_ledger:
        print("SKIP: 6a/7 Ledger Headers")
    else:
        anchor_header = "<th>STAGE</th>"
        new_headers = """<th>START DATE</th>
                                <th>TITLE DATE</th>
                                """
        if anchor_header in content_ledger:
            content_ledger = content_ledger.replace(anchor_header, new_headers + anchor_header)
            print("OK: 6a/7 Ledger Headers")
        else:
            print("FAIL: 6a/7 Ledger Headers")

    # 6b: Cells
    if "projectStartDate" in content_ledger:
        print("SKIP: 6b/7 Ledger Cells")
    else:
        stage_patterns = ["proj.stage", "project.stage", "currentStage", "getStatus"]
        found_stage = False
        for pat in stage_patterns:
            if pat in content_ledger:
                idx = content_ledger.find(pat)
                start_td = content_ledger.rfind("<td>", 0, idx)
                if start_td != -1:
                    insert_point = start_td
                    new_cells = """<td>{proj.landTitle?.projectStartDate || '---'}</td>
                                                <td>{proj.landTitle?.titleIssueDate || <em>Pending</em>}</td>
                                                """
                    content_ledger = content_ledger[:insert_point] + new_cells + content_ledger[insert_point:]
                    found_stage = True
                    print("OK: 6b/7 Ledger Cells (Heuristic)")
                    break
        
        if not found_stage:
            print("WARN: 6b/7 Ledger Cells (Could not auto-locate Stage cell)")

    write_file(path_ledger, content_ledger)

# 7. Frontend: FolderPage.jsx
folder_paths = [
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    "erp-frontend/src/pages/FolderPage.jsx"
]
path_folder = None
for p in folder_paths:
    if os.path.isfile(p):
        path_folder = p
        break

if path_folder:
    content_folder = read_file(path_folder)
    if "projectStartDate" in content_folder:
        print("SKIP: 7/7 FolderPage Tags")
    else:
        anchor_collection = "COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%"
        new_tags = """{project.landTitle?.projectStartDate && (
                            <span className={`${styles.metaTag} ${styles.tagGreen}`}>
                                STARTED: {new Date(project.landTitle.projectStartDate).toLocaleDateString()}
                            </span>
                        )}
                        {project.landTitle?.titleIssueDate ? (
                            <span className={`${styles.metaTag} ${styles.tagPurple}`}>
                                TITLED: {new Date(project.landTitle.titleIssueDate).toLocaleDateString()}
                            </span>
                        ) : (
                            <span className={`${styles.metaTag} ${styles.tagOrange}`}>
                                TITLE: PENDING
                            </span>
                        )}
                        """
        
        if anchor_collection in content_folder:
            content_folder = content_folder.replace(anchor_collection, new_tags + anchor_collection)
            write_file(path_folder, content_folder)
            print("OK: 7/7 FolderPage Tags")
        else:
            print("FAIL: 7/7 FolderPage Tags")

print("-" * 50)
print("DONE. Check for FAIL messages above.")
print("\nIf no FAILs (or only WARNs), run:")
print("git add -A && git commit -m 'feat: add date tracking system' && git push")