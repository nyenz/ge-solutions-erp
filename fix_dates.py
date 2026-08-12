# PATH: fix_dates.py
# PHASE 1.5 - DATE TRACKING SYSTEM
#
# WHAT THIS DOES:
# Adds two critical dates to track project timeline:
# 1. project_start_date - The day the project was initiated/intake (auto-filled with today's date)
# 2. title_issue_date - The day the land title was issued (optional, can be backdated if received later)
#
# These dates help track:
# - How long a project has been in progress
# - When the actual title document was completed
# - Timeline reporting and client communication
#
# THIS PATCH UPDATES:
# - Database migration (add two date columns)
# - Backend entity (LandTitle.java)
# - Backend DTO (LandTitleDTO.java)
# - Backend service (LandService.java)
# - Frontend form (NewTitleForm.jsx or similar)
# - Frontend display (LedgerPage.jsx, FolderPage.jsx)

import os

def patch(path, old, new, label):
    if not os.path.isfile(path):
        print("MISSING: " + path)
        return False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    if old in content:
        content = content.replace(old, new)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print("OK: " + label)
        return True
    elif new in content:
        print("SKIP (already applied): " + label)
        return True
    else:
        print("FAIL: " + label)
        return False

def create_new(path, content, label):
    if os.path.isfile(path):
        print("SKIP (already exists): " + label)
        return True
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: " + label)
    return True

# ============================================================
# 1/7: DATABASE MIGRATION - add two date columns to land_titles
# ============================================================

DATA_INIT_PATH = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"
OLD_MIGRATIONS = """            // PHASE 1 - PROJECT INDEX SYSTEM
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index)",
        };"""
NEW_MIGRATIONS = """            // PHASE 1 - PROJECT INDEX SYSTEM
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index)",

            // PHASE 1.5 - DATE TRACKING SYSTEM
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",
        };"""
patch(DATA_INIT_PATH, OLD_MIGRATIONS, NEW_MIGRATIONS, "PATCH 1/7: DataInitializer.java - add date columns migration")

# ============================================================
# 2/7: LandTitle.java - add the two date fields
# ============================================================

LAND_TITLE_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java"
OLD_TITLE_FIELDS = """    /**
     * PROJECT INDEX
     * Short, never-repeating, searchable code shown to clients and staff.
     * Format: 001A, 002A ... 999A, 001B, 002B ... 999B, 001C ...
     * Generated automatically at intake by ProjectIndexService.
     */
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    @Column(name = "survey_date")
    private LocalDate surveyDate;"""
NEW_TITLE_FIELDS = """    /**
     * PROJECT INDEX
     * Short, never-repeating, searchable code shown to clients and staff.
     * Format: 001A, 002A ... 999A, 001B, 002B ... 999B, 001C ...
     * Generated automatically at intake by ProjectIndexService.
     */
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    /**
     * PROJECT START DATE
     * The date when the project was initiated/intake.
     * Auto-filled with today's date when creating a new project.
     */
    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    /**
     * TITLE ISSUE DATE
     * The date when the land title document was actually issued.
     * Can be backdated if the title was processed earlier but entered later.
     * Optional field - may be null until the title is received.
     */
    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    @Column(name = "survey_date")
    private LocalDate surveyDate;"""
patch(LAND_TITLE_PATH, OLD_TITLE_FIELDS, NEW_TITLE_FIELDS, "PATCH 2/7: LandTitle.java - add date fields")

# ============================================================
# 3/7: LandTitleDTO.java - add date fields to DTO
# ============================================================

LAND_TITLE_DTO_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandTitleDTO.java"
OLD_DTO_FIELDS = """    private String projectIndex;
    private LocalDate surveyDate;"""
NEW_DTO_FIELDS = """    private String projectIndex;
    private LocalDate projectStartDate;
    private LocalDate titleIssueDate;
    private LocalDate surveyDate;"""
patch(LAND_TITLE_DTO_PATH, OLD_DTO_FIELDS, NEW_DTO_FIELDS, "PATCH 3/7: LandTitleDTO.java - add date fields to DTO")

# Check if DTO file exists, if not try to find it
if not os.path.isfile(LAND_TITLE_DTO_PATH):
    # Try to find the DTO file
    import subprocess
    result = subprocess.run(["find", "erp-backend", "-name", "*DTO*.java"], capture_output=True, text=True)
    dto_files = [f for f in result.stdout.strip().split('\n') if 'Land' in f and 'DTO' in f]
    if dto_files:
        LAND_TITLE_DTO_PATH = dto_files[0]
        patch(LAND_TITLE_DTO_PATH, OLD_DTO_FIELDS, NEW_DTO_FIELDS, "PATCH 3/7: LandTitleDTO.java - add date fields to DTO (found)")

# ============================================================
# 4/7: LandService.java - auto-fill project_start_date with today
# ============================================================

LAND_SERVICE_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"

OLD_TITLE_BUILD = """        LandTitle title = LandTitle.builder()
                .tenure(request.getTenure())
                .plotNumber(request.getPlotNumber())
                .physicalBoxNumber(request.getPhysicalBoxNumber())
                .district(request.getDistrict())
                .blockRoad(request.getBlockRoad())
                .county(request.getCounty())
                .volume(request.getVolume())
                .folio(request.getFolio())
                .instrumentNo(request.getInstrumentNo())
                .surveyDate(request.getSurveyDate())
                .projectIndex(projectIndexService.generateNextIndex())
                .build();"""
NEW_TITLE_BUILD = """        LandTitle title = LandTitle.builder()
                .tenure(request.getTenure())
                .plotNumber(request.getPlotNumber())
                .physicalBoxNumber(request.getPhysicalBoxNumber())
                .district(request.getDistrict())
                .blockRoad(request.getBlockRoad())
                .county(request.getCounty())
                .volume(request.getVolume())
                .folio(request.getFolio())
                .instrumentNo(request.getInstrumentNo())
                .surveyDate(request.getSurveyDate())
                .projectIndex(projectIndexService.generateNextIndex())
                .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())
                .titleIssueDate(request.getTitleIssueDate())
                .build();"""
patch(LAND_SERVICE_PATH, OLD_TITLE_BUILD, NEW_TITLE_BUILD, "PATCH 4/7: LandService.java - set date fields")

# ============================================================
# 5/7: Find and update the frontend form component
# ============================================================

# Search for the form file
import subprocess
result = subprocess.run(["find", "erp-frontend", "-name", "*.jsx"], capture_output=True, text=True)
form_files = [f for f in result.stdout.strip().split('\n') if 'new' in f.lower() or 'form' in f.lower() or 'create' in f.lower()]

# Try common patterns
possible_forms = [
    "erp-frontend/src/pages/Land/NewTitleForm.jsx",
    "erp-frontend/src/pages/Land/NewLandTitle.jsx",
    "erp-frontend/src/components/Land/TitleForm.jsx",
    "erp-frontend/src/pages/Ledger/NewProjectForm.jsx"
]

FORM_PATH = None
for candidate in possible_forms:
    if os.path.isfile(candidate):
        FORM_PATH = candidate
        break

if not FORM_PATH and form_files:
    # Use the first matching file
    FORM_PATH = form_files[0]

if FORM_PATH:
    # Add state variables for the dates
    OLD_IMPORTS = """import { useState } from 'react';"""
    NEW_IMPORTS = """import { useState, useEffect } from 'react';"""
    patch(FORM_PATH, OLD_IMPORTS, NEW_IMPORTS, "PATCH 5a/7: Form imports - add useEffect")

    # Add state for dates (look for existing useState declarations)
    OLD_STATE = """const [surveyDate, setSurveyDate] = useState('');"""
    NEW_STATE = """const [surveyDate, setSurveyDate] = useState('');
    const [projectStartDate, setProjectStartDate] = useState(new Date().toISOString().split('T')[0]);
    const [titleIssueDate, setTitleIssueDate] = useState('');"""
    
    if patch(FORM_PATH, OLD_STATE, NEW_STATE, "PATCH 5b/7: Form state - add date states"):
        pass
    else:
        # Try alternative pattern
        OLD_STATE_ALT = """const [formData, setFormData] = useState({"""
        NEW_STATE_ALT = """const [formData, setFormData] = useState({
        projectStartDate: new Date().toISOString().split('T')[0],
        titleIssueDate: '',"""
        patch(FORM_PATH, OLD_STATE_ALT, NEW_STATE_ALT, "PATCH 5b/7: Form state - add date states (alt)")

    # Add form inputs for the dates
    OLD_FORM_END = """</form>"""
    NEW_FORM_END = """{/* Project Start Date */}
                    <div className={styles.formGroup}>
                        <label htmlFor="projectStartDate">Project Start Date *</label>
                        <input
                            type="date"
                            id="projectStartDate"
                            value={projectStartDate}
                            onChange={(e) => setProjectStartDate(e.target.value)}
                            required
                        />
                        <small>Auto-filled with today's date. Adjust if needed.</small>
                    </div>

                    {/* Title Issue Date */}
                    <div className={styles.formGroup}>
                        <label htmlFor="titleIssueDate">Title Issue Date</label>
                        <input
                            type="date"
                            id="titleIssueDate"
                            value={titleIssueDate}
                            onChange={(e) => setTitleIssueDate(e.target.value)}
                        />
                        <small>Optional. Enter the date the title was issued (can be backdated).</small>
                    </div>

                </form>"""
    patch(FORM_PATH, OLD_FORM_END, NEW_FORM_END, "PATCH 5c/7: Form inputs - add date fields")

    # Update submit handler to include dates
    OLD_SUBMIT = """projectStartDate: surveyDate,"""
    NEW_SUBMIT = """projectStartDate: projectStartDate,
            titleIssueDate: titleIssueDate || null,"""
    patch(FORM_PATH, OLD_SUBMIT, NEW_SUBMIT, "PATCH 5d/7: Submit handler - include dates")
else:
    print("INFO: Could not auto-detect form file. Manual update may be needed for frontend form.")

# ============================================================
# 6/7: LedgerPage.jsx - display the dates in the table
# ============================================================

LEDGER_PAGE_PATH = "erp-frontend/src/pages/Ledger/LedgerPage.jsx"

# Add dates to the table columns (look for the table header)
OLD_TABLE_HEADER = """<th>Plot Number</th>
                                                    <th>Location</th>"""
NEW_TABLE_HEADER = """<th>Plot Number</th>
                                                    <th>Start Date</th>
                                                    <th>Title Date</th>
                                                    <th>Location</th>"""
patch(LEDGER_PAGE_PATH, OLD_TABLE_HEADER, NEW_TABLE_HEADER, "PATCH 6a/7: LedgerPage - add date column headers")

# Add dates to the table cells
OLD_TABLE_CELL = """<td>{proj.landTitle?.plotNumber || '---'}</td>
                                                    <td>"""
NEW_TABLE_CELL = """<td>{proj.landTitle?.plotNumber || '---'}</td>
                                                    <td>{proj.landTitle?.projectStartDate ? new Date(proj.landTitle.projectStartDate).toLocaleDateString() : '---'}</td>
                                                    <td>{proj.landTitle?.titleIssueDate ? new Date(proj.landTitle.titleIssueDate).toLocaleDateString() : 'Pending'}</td>
                                                    <td>"""
patch(LEDGER_PAGE_PATH, OLD_TABLE_CELL, NEW_TABLE_CELL, "PATCH 6b/7: LedgerPage - add date cells")

# ============================================================
# 7/7: FolderPage.jsx - display dates on the project header
# ============================================================

FOLDER_PAGE_PATH = "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"

OLD_META_LINE = """<div className={styles.metaLine}>
                        {project.landTitle?.projectIndex && (
                            <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                                PROJECT #{project.landTitle.projectIndex}
                            </span>
                        )}
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>"""
NEW_META_LINE = """<div className={styles.metaLine}>
                        {project.landTitle?.projectIndex && (
                            <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                                PROJECT #{project.landTitle.projectIndex}
                            </span>
                        )}
                        <span className={`${styles.metaTag} ${styles.tagGreen}`}>
                            STARTED: {project.landTitle?.projectStartDate ? new Date(project.landTitle.projectStartDate).toLocaleDateString() : '---'}
                        </span>
                        <span className={`${styles.metaTag} ${styles.tagPurple}`}>
                            TITLE: {project.landTitle?.titleIssueDate ? new Date(project.landTitle.titleIssueDate).toLocaleDateString() : 'Pending'}
                        </span>
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>"""
patch(FOLDER_PAGE_PATH, OLD_META_LINE, NEW_META_LINE, "PATCH 7/7: FolderPage - display dates in header")

print("")
print("=" * 60)
print("DONE - DATE TRACKING SYSTEM APPLIED")
print("=" * 60)
print("")
print("WHAT WAS CHANGED:")
print("1. Database: Added project_start_date and title_issue_date columns")
print("2. Backend: Updated entity, DTO, and service to handle dates")
print("3. Frontend Form: Added date pickers (start date auto-filled with today)")
print("4. Ledger Page: Shows both dates in the project table")
print("5. Folder Page: Displays dates as colored tags in the header")
print("")
print("NEXT STEPS:")
print("1. git add -A && git commit -m 'feat: add project date tracking system' && git push")
print("2. Wait for Render to redeploy (5-10 min)")
print("3. Test by creating a new project at /land/new")
print("   - Project Start Date will auto-fill with today")
print("   - Title Issue Date is optional (leave blank if not yet issued)")
print("4. View the project in Ledger and Digital Folder to see dates displayed")
print("")
