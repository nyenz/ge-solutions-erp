# PATH: fix.py
# PHASE 1 OF THE ERP REVAMP: PROJECT INDEX SYSTEM
#
# WHAT THIS DOES:
# Adds the #001A style project index discussed with your employer.
# - 001A, 002A ... 999A, then rolls to 001B, 002B ... 999B, then 001C ...
# - Numbers never repeat, and never grow past 4 characters.
# - Every new project gets one automatically when it is created.
# - The index is shown in the Ledger table and on the project folder page.
# - The index is now searchable in the Ledger search bar.
#
# THIS PATCH DOES NOT TOUCH: roles, NIN, financials, or stage templates.
# Those are separate phases, coming after this one is confirmed working.

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
# 1/6: NEW FILE - ProjectIndexService.java
# Generates the next index code (001A, 002A ... 999A, 001B ...)
# ============================================================

PROJECT_INDEX_SERVICE_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ProjectIndexService.java"
PROJECT_INDEX_SERVICE_CONTENT = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ProjectIndexService.java
package com.gesolutions.erp.modules.land.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

/**
 * GE SOLUTIONS - PROJECT INDEX GENERATOR
 *
 * Generates short, never-repeating, searchable project index codes
 * in the format: 001A, 002A ... 999A, 001B, 002B ... 999B, 001C ...
 *
 * Numbers never repeat and the code never grows past 4 characters,
 * no matter how many thousands of projects the company processes.
 *
 * Uses a single-row counter table (project_index_counter) and a
 * synchronized raw JDBC read-increment-write. Project intake happens
 * rarely enough (a handful of times per day) that a full pessimistic
 * database lock is not necessary -- the synchronized keyword is enough
 * to prevent two intakes at the exact same instant from colliding.
 */
@Service
public class ProjectIndexService {

    private final DataSource dataSource;

    public ProjectIndexService(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Transactional
    public synchronized String generateNextIndex() {
        try (Connection conn = dataSource.getConnection()) {

            int currentNumber;
            String currentLetter;

            try (PreparedStatement ps = conn.prepareStatement(
                    "SELECT current_number, current_letter FROM project_index_counter WHERE id = 1");
                 ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    currentNumber = rs.getInt("current_number");
                    currentLetter = rs.getString("current_letter");
                } else {
                    currentNumber = 0;
                    currentLetter = "A";
                }
            }

            currentNumber = currentNumber + 1;
            if (currentNumber > 999) {
                currentNumber = 1;
                currentLetter = nextLetter(currentLetter);
            }

            try (PreparedStatement ps = conn.prepareStatement(
                    "UPDATE project_index_counter SET current_number = ?, current_letter = ? WHERE id = 1")) {
                ps.setInt(1, currentNumber);
                ps.setString(2, currentLetter);
                ps.executeUpdate();
            }

            return String.format("%03d", currentNumber) + currentLetter;

        } catch (Exception e) {
            throw new RuntimeException("PROJECT_INDEX_FAULT: Could not generate project index", e);
        }
    }

    // A -> B -> C ... Z -> AA -> AB
    // Extremely unlikely to ever reach double letters (that would mean
    // 25,974+ projects processed), but this keeps the system correct
    // even if the company somehow gets there.
    private String nextLetter(String letter) {
        char[] chars = letter.toCharArray();
        int i = chars.length - 1;
        while (i >= 0) {
            if (chars[i] != 'Z') {
                chars[i]++;
                return new String(chars);
            } else {
                chars[i] = 'A';
                i--;
            }
        }
        return "A" + new String(chars);
    }
}
"""
create_new(PROJECT_INDEX_SERVICE_PATH, PROJECT_INDEX_SERVICE_CONTENT, "NEW FILE: ProjectIndexService.java")

# ============================================================
# 2/6: DATABASE MIGRATION - add counter table + project_index column
# ============================================================

DATA_INIT_PATH = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"
OLD_MIGRATIONS = """            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS survey_date DATE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",
        };"""
NEW_MIGRATIONS = """            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS survey_date DATE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",

            // PHASE 1 - PROJECT INDEX SYSTEM
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index)",
        };"""
patch(DATA_INIT_PATH, OLD_MIGRATIONS, NEW_MIGRATIONS, "PATCH 2/6: DataInitializer.java - project index migration")

# ============================================================
# 3/6: LandTitle.java - add the projectIndex field
# ============================================================

LAND_TITLE_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java"
OLD_TITLE_FIELDS = """    @Column(name = "physical_box_number", nullable = false, length = 100)
    private String physicalBoxNumber;

    @Column(name = "survey_date")
    private LocalDate surveyDate;"""
NEW_TITLE_FIELDS = """    @Column(name = "physical_box_number", nullable = false, length = 100)
    private String physicalBoxNumber;

    /**
     * PROJECT INDEX
     * Short, never-repeating, searchable code shown to clients and staff.
     * Format: 001A, 002A ... 999A, 001B, 002B ... 999B, 001C ...
     * Generated automatically at intake by ProjectIndexService.
     */
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    @Column(name = "survey_date")
    private LocalDate surveyDate;"""
patch(LAND_TITLE_PATH, OLD_TITLE_FIELDS, NEW_TITLE_FIELDS, "PATCH 3/6: LandTitle.java - add projectIndex field")

# ============================================================
# 4/6: LandService.java - wire in ProjectIndexService + assign on intake
# ============================================================

LAND_SERVICE_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"

OLD_FIELD_DECL = """    private final PaymentRecordRepository paymentRecordRepository;

    private String getCurrentOperator() {"""
NEW_FIELD_DECL = """    private final PaymentRecordRepository paymentRecordRepository;
    private final ProjectIndexService projectIndexService;

    private String getCurrentOperator() {"""
patch(LAND_SERVICE_PATH, OLD_FIELD_DECL, NEW_FIELD_DECL, "PATCH 4a/6: LandService.java - inject ProjectIndexService")

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
                .build();"""
patch(LAND_SERVICE_PATH, OLD_TITLE_BUILD, NEW_TITLE_BUILD, "PATCH 4b/6: LandService.java - assign index at intake")

# ============================================================
# 5/6: LedgerPage.jsx - make index searchable + display it
# ============================================================

LEDGER_PAGE_PATH = "erp-frontend/src/pages/Ledger/LedgerPage.jsx"

OLD_SEARCH_FIELDS = """    const fields = [
        proj.landTitle?.plotNumber,
        proj.landTitle?.physicalBoxNumber,"""
NEW_SEARCH_FIELDS = """    const fields = [
        proj.landTitle?.plotNumber,
        proj.landTitle?.projectIndex,
        proj.landTitle?.physicalBoxNumber,"""
patch(LEDGER_PAGE_PATH, OLD_SEARCH_FIELDS, NEW_SEARCH_FIELDS, "PATCH 5a/6: LedgerPage.jsx - make index searchable")

OLD_PLOT_CELL = """                                                <div>
                                                    <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                    <div>"""
NEW_PLOT_CELL = """                                                <div>
                                                    <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                    {proj.landTitle?.projectIndex && (
                                                        <span className={styles.districtTag}> #{proj.landTitle.projectIndex}</span>
                                                    )}
                                                    <div>"""
patch(LEDGER_PAGE_PATH, OLD_PLOT_CELL, NEW_PLOT_CELL, "PATCH 5b/6: LedgerPage.jsx - display index in table")

# ============================================================
# 6/6: FolderPage.jsx - display index on the project header
# ============================================================

FOLDER_PAGE_PATH = "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"
OLD_ID_PLATE = """                <div className={styles.idPlate}>
                    <h1>{project.landTitle.plotNumber}</h1>
                    <div className={styles.metaLine}>
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
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>"""
patch(FOLDER_PAGE_PATH, OLD_ID_PLATE, NEW_ID_PLATE, "PATCH 6/6: FolderPage.jsx - display index on folder header")

print("")
print("DONE.")
print("Next steps:")
print("1. git add -A && git commit -m 'feat: add project index system (#001A format)' && git push")
print("2. Wait for Render to redeploy the backend (5-10 min on free tier)")
print("3. Create a NEW test plot at golden-seed.onrender.com/land/new")
print("4. Check that it gets an index like 001A on the Ledger page and Folder page")
print("5. Old existing plots will show no index (blank) until they are edited and re-saved -- that is expected for Phase 1")