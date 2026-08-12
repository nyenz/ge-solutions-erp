# PATH: fix.py
# PHASE 1.5 OF THE ERP REVAMP: DATE TRACKING SYSTEM
#
# WHAT THIS DOES:
# Adds date tracking to record when projects start and when titles are issued.
# - Project Start Date: Auto-filled with today's date on intake (editable)
# - Title Issue Date: Optional, can be backdated for received titles
# - Both dates shown in Ledger table and Digital Folder
# - Helps track project timeline and processing duration
#
# THIS PATCH BUILDS ON TOP OF THE PROJECT INDEX SYSTEM.
# Run this AFTER the index system (fix.py Phase 1) is already applied.

import os

def patch(path, old, new, label):
    if not os.path.isfile(path):
        print("MISSING: " + path)
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    if old in content:
        content = content.replace(old, new)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print("OK: " + label)
    elif new in content:
        print("SKIP (already applied): " + label)
    else:
        print("FAIL: " + label)

def create_new(path, content, label):
    if os.path.isfile(path):
        print("SKIP (already exists): " + label)
        return
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: " + label)

# ============================================================
# 1/7: DATABASE MIGRATION - add date columns to land_titles
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
patch(DATA_INIT_PATH, OLD_MIGRATIONS, NEW_MIGRATIONS, "PATCH 1/7: DataInitializer.java - date tracking migration")

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
     * The date when the project was initiated/intake was done.
     * Auto-filled with today's date during intake, but can be edited.
     */
    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    /**
     * TITLE ISSUE DATE
     * The date when the land title was actually issued/received.
     * Optional field - can be set later when title is received.
     * Can be backdated to match the actual title issue date.
     */
    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    @Column(name = "survey_date")
    private LocalDate surveyDate;"""
patch(LAND_TITLE_PATH, OLD_TITLE_FIELDS, NEW_TITLE_FIELDS, "PATCH 2/7: LandTitle.java - add date fields")

# ============================================================
# 3/7: LandEntryRequest.java - add date fields to DTO
# ============================================================

LAND_ENTRY_REQUEST_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java"
OLD_REQUEST_FIELDS = """    private String physicalBoxNumber;
    private String district;
    private String blockRoad;
    private String county;
    private String volume;
    private String folio;
    private String instrumentNo;
    private LocalDate surveyDate;"""
NEW_REQUEST_FIELDS = """    private String physicalBoxNumber;
    private String district;
    private String blockRoad;
    private String county;
    private String volume;
    private String folio;
    private String instrumentNo;
    private LocalDate surveyDate;
    private LocalDate projectStartDate;
    private LocalDate titleIssueDate;"""
patch(LAND_ENTRY_REQUEST_PATH, OLD_REQUEST_FIELDS, NEW_REQUEST_FIELDS, "PATCH 3/7: LandEntryRequest.java - add date fields to DTO")

# ============================================================
# 4/7: LandService.java - auto-fill project start date with today
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
patch(LAND_SERVICE_PATH, OLD_TITLE_BUILD, NEW_TITLE_BUILD, "PATCH 4/7: LandService.java - auto-fill start date")

# ============================================================
# 5/7: IntakePage.jsx - add date pickers to the form
# ============================================================

INTAKE_PAGE_PATH = "erp-frontend/src/pages/LandIntake/IntakePage.jsx"

OLD_FORM_STATE = """        physicalBoxNumber: '',
        district: '',
        blockRoad: '',
        county: '',
        volume: '',
        folio: '',
        instrumentNo: '',
        surveyDate: '',"""
NEW_FORM_STATE = """        physicalBoxNumber: '',
        district: '',
        blockRoad: '',
        county: '',
        volume: '',
        folio: '',
        instrumentNo: '',
        surveyDate: '',
        projectStartDate: new Date().toISOString().split('T')[0],
        titleIssueDate: '',"""
patch(INTAKE_PAGE_PATH, OLD_FORM_STATE, NEW_FORM_STATE, "PATCH 5a/7: IntakePage.jsx - add date state")

OLD_FORM_FIELDS = """                    <div className={styles.formGroup}>
                        <label htmlFor="surveyDate">Survey Date</label>
                        <input
                            type="date"
                            id="surveyDate"
                            value={formData.surveyDate}
                            onChange={(e) => setFormData({ ...formData, surveyDate: e.target.value })}
                        />
                    </div>

                    <div className={styles.formActions}>"""
NEW_FORM_FIELDS = """                    <div className={styles.formGroup}>
                        <label htmlFor="surveyDate">Survey Date</label>
                        <input
                            type="date"
                            id="surveyDate"
                            value={formData.surveyDate}
                            onChange={(e) => setFormData({ ...formData, surveyDate: e.target.value })}
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label htmlFor="projectStartDate">Project Start Date *</label>
                        <input
                            type="date"
                            id="projectStartDate"
                            value={formData.projectStartDate}
                            onChange={(e) => setFormData({ ...formData, projectStartDate: e.target.value })}
                            required
                        />
                        <small>Auto-filled with today's date. Edit if project started earlier.</small>
                    </div>

                    <div className={styles.formGroup}>
                        <label htmlFor="titleIssueDate">Title Issue Date (Optional)</label>
                        <input
                            type="date"
                            id="titleIssueDate"
                            value={formData.titleIssueDate}
                            onChange={(e) => setFormData({ ...formData, titleIssueDate: e.target.value })}
                        />
                        <small>Leave blank if title not yet received. Can be backdated.</small>
                    </div>

                    <div className={styles.formActions}>"""
patch(INTAKE_PAGE_PATH, OLD_FORM_FIELDS, NEW_FORM_FIELDS, "PATCH 5b/7: IntakePage.jsx - add date inputs")

OLD_SUBMIT_PAYLOAD = """            physicalBoxNumber: formData.physicalBoxNumber,
            district: formData.district,
            blockRoad: formData.blockRoad,
            county: formData.county,
            volume: formData.volume,
            folio: formData.folio,
            instrumentNo: formData.instrumentNo,
            surveyDate: formData.surveyDate || null,"""
NEW_SUBMIT_PAYLOAD = """            physicalBoxNumber: formData.physicalBoxNumber,
            district: formData.district,
            blockRoad: formData.blockRoad,
            county: formData.county,
            volume: formData.volume,
            folio: formData.folio,
            instrumentNo: formData.instrumentNo,
            surveyDate: formData.surveyDate || null,
            projectStartDate: formData.projectStartDate || null,
            titleIssueDate: formData.titleIssueDate || null,"""
patch(INTAKE_PAGE_PATH, OLD_SUBMIT_PAYLOAD, NEW_SUBMIT_PAYLOAD, "PATCH 5c/7: IntakePage.jsx - include dates in submit")

# ============================================================
# 6/7: LedgerPage.jsx - add date columns to the table
# ============================================================

LEDGER_PAGE_PATH = "erp-frontend/src/pages/Ledger/LedgerPage.jsx"

OLD_TABLE_HEADER = """                                <th>DISTRICT</th>
                                <th>PLOT / BOX</th>
                                <th>STAGE</th>"""
NEW_TABLE_HEADER = """                                <th>DISTRICT</th>
                                <th>PLOT / BOX</th>
                                <th>START DATE</th>
                                <th>TITLE DATE</th>
                                <th>STAGE</th>"""
patch(LEDGER_PAGE_PATH, OLD_TABLE_HEADER, NEW_TABLE_HEADER, "PATCH 6a/7: LedgerPage.jsx - add date headers")

OLD_TABLE_CELL = """                                                <td>{proj.landTitle?.district || '---'}</td>
                                                <td>
                                                    <div>
                                                        <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                        {proj.landTitle?.projectIndex && (
                                                            <span className={styles.districtTag}> #{proj.landTitle.projectIndex}</span>
                                                        )}
                                                        <div className={styles.boxNumber}>{proj.landTitle?.physicalBoxNumber || ''}</div>
                                                    </div>
                                                </td>
                                                <td>"""
NEW_TABLE_CELL = """                                                <td>{proj.landTitle?.district || '---'}</td>
                                                <td>
                                                    <div>
                                                        <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                        {proj.landTitle?.projectIndex && (
                                                            <span className={styles.districtTag}> #{proj.landTitle.projectIndex}</span>
                                                        )}
                                                        <div className={styles.boxNumber}>{proj.landTitle?.physicalBoxNumber || ''}</div>
                                                    </div>
                                                </td>
                                                <td>{proj.landTitle?.projectStartDate || '---'}</td>
                                                <td>{proj.landTitle?.titleIssueDate || <em>Pending</em>}</td>
                                                <td>"""
patch(LEDGER_PAGE_PATH, OLD_TABLE_CELL, NEW_TABLE_CELL, "PATCH 6b/7: LedgerPage.jsx - add date cells")

# ============================================================
# 7/7: FolderPage.jsx - display dates in the header tags
# ============================================================

FOLDER_PAGE_PATH = "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"

OLD_ID_PLATE = """                <div className={styles.idPlate}>
                    <h1>{project.landTitle.plotNumber}</h1>
                    <div className={styles.metaLine}>
                        {project.landTitle?.projectIndex && (
                            <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                                PROJECT #{project.landTitle.projectIndex}
                            </span>
                        )}
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>"""
NEW_ID_PLATE = """                <div className={styles.idPlate}>
                    <h1>{project.landTitle.plotNumber}</h1>
                    <div className={styles.metaLine}>
                        {project.landTitle?.projectIndex && (
                            <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                                PROJECT #{project.landTitle.projectIndex}
                            </span>
                        )}
                        {project.landTitle?.projectStartDate && (
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
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>"""
patch(FOLDER_PAGE_PATH, OLD_ID_PLATE, NEW_ID_PLATE, "PATCH 7/7: FolderPage.jsx - display dates as tags")

print("")
print("DONE.")
print("Next steps:")
print("1. git add -A && git commit -m 'feat: add date tracking system (start date + title date)' && git push")
print("2. Wait for Render to redeploy the backend (5-10 min on free tier)")
print("3. Create a NEW test plot at golden-seed.onrender.com/land/new")
print("4. You'll see both date fields - start date auto-filled with today")
print("5. Check Ledger page for new date columns")
print("6. Open Digital Folder to see dates as colored tags")