# PATH: fix.py
# PHASE 1.5 REPAIR PATCH - Fixes corrupted files + adds date tracking to Intake form
# Run this from the project root: py fix.py

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

print("Starting Phase 1.5 Repair Patch...")
print("-" * 50)

# ============================================================
# 1. FULL REWRITE: PaymentRecordRepository.java (was corrupted
#    with test-file content in a previous session, causing every
#    file that imports it to fail to compile)
# ============================================================
path_prr = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentRecordRepository.java"

content_prr = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentRecordRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.PaymentRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface PaymentRecordRepository extends JpaRepository<PaymentRecord, UUID> {

    List<PaymentRecord> findByProjectIdOrderByTimestampDesc(UUID projectId);

    @Query("SELECT COALESCE(SUM(p.amountPaid), 0) FROM PaymentRecord p WHERE p.projectId = :projectId")
    BigDecimal sumPaymentsByProjectId(UUID projectId);

    @Query("SELECT COALESCE(SUM(p.amountPaid), 0) FROM PaymentRecord p WHERE p.timestamp >= :since")
    BigDecimal sumAllPaymentsSince(LocalDateTime since);

    @Query(value = "SELECT DATE_TRUNC('month', timestamp) as month, SUM(amount_paid) as total " +
                   "FROM payment_records WHERE timestamp >= :since " +
                   "GROUP BY DATE_TRUNC('month', timestamp) ORDER BY month ASC", nativeQuery = true)
    List<Object[]> monthlyRevenueSince(LocalDateTime since);
}
"""

write_file(path_prr, content_prr)
print("OK: 1/6 PaymentRecordRepository.java (full rewrite - fixes PaymentController, ReportService, LandServiceTest)")

# ============================================================
# 2. FULL REWRITE: LandEntryRequest.java (had duplicate
#    projectStartDate / titleIssueDate fields from a bad patch)
# ============================================================
path_ler = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java"

content_ler = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java
package com.gesolutions.erp.modules.land.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LandEntryRequest {

    private String plotNumber;
    private String tenure;
    private String blockRoad;
    private String district;
    private String county;
    private String volume;
    private String folio;
    private String instrumentNo;
    private String physicalBoxNumber;
    private LocalDate surveyDate;
    private LocalDate projectStartDate;
    private LocalDate titleIssueDate;

    @Builder.Default
    private List<OwnerRequest> owners = new ArrayList<>();

    private BigDecimal totalCost;
    private BigDecimal initialPayment;

    // Legacy fields -- kept to avoid breaking existing data, no longer used in new logic
    private BigDecimal weeklyInstallment;
    private String planType;

    @Builder.Default
    private List<NoteRequest> notes = new ArrayList<>();

    private Integer currentStageIndex;

    @JsonProperty("isLegacy")
    private boolean isLegacy;

    // Staff can flag a plot as backlog right at intake (for old/existing cases)
    @JsonProperty("isStartAsBacklog")
    private boolean isStartAsBacklog;

    private java.math.BigDecimal monthlyStorageFee;
    private java.math.BigDecimal initialStorageFee;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OwnerRequest {
        private String fullName;
        private String phone;
        private String email;
        private String nationalId;
        private String address;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class NoteRequest {
        private UUID id;
        private String content;
    }
}
"""

write_file(path_ler, content_ler)
print("OK: 2/6 LandEntryRequest.java (full rewrite - removed duplicate fields)")

# ============================================================
# 3. PATCH: LandService.java - add missing java.time.LocalDate
#    import (LocalDate.now() is used in atomicIntake but the
#    import was never added, causing "LocalDate cannot be resolved")
# ============================================================
path_ls = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"
content_ls = read_file(path_ls)
if content_ls:
    if "import java.time.LocalDate;" in content_ls:
        print("SKIP: 3/6 LandService.java (import already present)")
    else:
        anchor = "import java.time.LocalDateTime;"
        if anchor in content_ls:
            content_ls = content_ls.replace(anchor, "import java.time.LocalDate;\nimport java.time.LocalDateTime;")
            write_file(path_ls, content_ls)
            print("OK: 3/6 LandService.java (added LocalDate import)")
        else:
            print("FAIL: 3/6 LandService.java (anchor not found -- add 'import java.time.LocalDate;' manually near the other java.time imports)")
else:
    print("FAIL: 3/6 LandService.java (file not found)")

# ============================================================
# 4. FRONTEND: IntakePage.jsx -- add Project Start Date and
#    Title Issue Date fields (auto-fills today, editable; title
#    date optional/backdatable for when the title is received)
# ============================================================
path_intake = "erp-frontend/src/pages/Intake/IntakePage.jsx"
content_intake = read_file(path_intake)

if content_intake:

    # 4a: state hooks
    if "projectStartDate" in content_intake and "setProjectStartDate" in content_intake:
        print("SKIP: 4a/6 Intake date state (already present)")
    else:
        anchor_state = "    const [surveyDate,        setSurveyDate]        = useState('');"
        new_state = """    const [surveyDate,        setSurveyDate]        = useState('');
    const [projectStartDate,  setProjectStartDate]  = useState(() => new Date().toISOString().split('T')[0]);
    const [titleIssueDate,    setTitleIssueDate]    = useState('');"""
        if anchor_state in content_intake:
            content_intake = content_intake.replace(anchor_state, new_state)
            print("OK: 4a/6 Intake date state added")
        else:
            print("FAIL: 4a/6 Intake date state (anchor not found)")

    # 4b: isDirty tracking (only count projectStartDate as dirty if
    # the user actually changed it away from today's auto-filled value)
    if "DEFAULT_START_DATE" in content_intake:
        print("SKIP: 4b/6 Intake isDirty tracking (already present)")
    else:
        anchor_dirty = "        if (surveyDate !== '') return true;"
        new_dirty = """        if (surveyDate !== '') return true;
        if (titleIssueDate !== '') return true;
        if (projectStartDate !== DEFAULT_START_DATE) return true;"""
        if anchor_dirty in content_intake:
            content_intake = content_intake.replace(anchor_dirty, new_dirty)
            # Insert the DEFAULT_START_DATE constant near the top of the component
            anchor_const = "    const navigate = useNavigate();"
            new_const = """    const navigate = useNavigate();
    const DEFAULT_START_DATE = React.useMemo(() => new Date().toISOString().split('T')[0], []);"""
            if anchor_const in content_intake:
                content_intake = content_intake.replace(anchor_const, new_const)
                print("OK: 4b/6 Intake isDirty tracking added")
            else:
                print("WARN: 4b/6 Added dirty check but could not insert DEFAULT_START_DATE constant -- add manually")
        else:
            print("FAIL: 4b/6 Intake isDirty tracking (anchor not found)")

    # 4c: form inputs in Plot Details drawer
    if 'label="PROJECT START DATE"' in content_intake:
        print("SKIP: 4c/6 Intake date inputs (already present)")
    else:
        anchor_grid = """                            <div className={styles.grid3}>
                                <SmartInput label="INSTRUMENT NO." value={instrumentNo} showCaps
                                    onChange={e => setInstrumentNo(e.target.value.toUpperCase())} />
                                <SmartInput label="VOLUME" value={volume} inputMode="numeric"
                                    onChange={e => setVolume(e.target.value.replace(/\\D/g,''))} />
                                <SmartInput label="FOLIO" value={folio} inputMode="numeric"
                                    onChange={e => setFolio(e.target.value.replace(/\\D/g,''))} />
                            </div>"""
        new_date_inputs = """
                            <div className={styles.grid2}>
                                <div className={styles.inputWrap}>
                                    <div className={styles.labelRow}>
                                        <label className={styles.fieldLabel}>PROJECT START DATE</label>
                                    </div>
                                    <input type="date" className={styles.hwInput}
                                        value={projectStartDate}
                                        onChange={e => setProjectStartDate(e.target.value)} />
                                    <span className={styles.fieldHint}>Auto-filled with today. Edit if the project actually started earlier.</span>
                                </div>
                                <div className={styles.inputWrap}>
                                    <div className={styles.labelRow}>
                                        <label className={styles.fieldLabel}>TITLE ISSUE DATE (OPTIONAL)</label>
                                    </div>
                                    <input type="date" className={styles.hwInput}
                                        value={titleIssueDate}
                                        onChange={e => setTitleIssueDate(e.target.value)} />
                                    <span className={styles.fieldHint}>Leave blank if not yet received. Can be backdated.</span>
                                </div>
                            </div>"""
        if anchor_grid in content_intake:
            content_intake = content_intake.replace(anchor_grid, anchor_grid + new_date_inputs)
            print("OK: 4c/6 Intake date inputs added")
        else:
            print("FAIL: 4c/6 Intake date inputs (anchor not found)")

    # 4d: submit payload (handleSubmit)
    if content_intake.count("projectStartDate: projectStartDate || undefined") >= 1:
        print("SKIP: 4d/6 Intake handleSubmit payload (already present)")
    else:
        anchor_submit = """                surveyDate: surveyDate || undefined,
                isLegacy: false, // Always false for new plots - legacy is a historical flag only"""
        new_submit = """                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
                isLegacy: false, // Always false for new plots - legacy is a historical flag only"""
        if anchor_submit in content_intake:
            content_intake = content_intake.replace(anchor_submit, new_submit)
            print("OK: 4d/6 Intake handleSubmit payload updated")
        else:
            print("FAIL: 4d/6 Intake handleSubmit payload (anchor not found)")

    # 4e: duplicate-plot payload (handleDuplicatePlot)
    if content_intake.count("projectStartDate: projectStartDate || undefined") >= 2:
        print("SKIP: 4e/6 Intake handleDuplicatePlot payload (already present)")
    else:
        anchor_dup = """                surveyDate: surveyDate || undefined,
                isLegacy: false,
                owners: owners.map(o => ({"""
        new_dup = """                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
                isLegacy: false,
                owners: owners.map(o => ({"""
        if anchor_dup in content_intake:
            content_intake = content_intake.replace(anchor_dup, new_dup)
            print("OK: 4e/6 Intake handleDuplicatePlot payload updated")
        else:
            print("FAIL: 4e/6 Intake handleDuplicatePlot payload (anchor not found)")

    write_file(path_intake, content_intake)
else:
    print("FAIL: 4/6 IntakePage.jsx not found")

print("-" * 50)
print("DONE. Check for FAIL messages above.")
print("")
print("If no FAILs (or only WARNs), run:")
print("git add -A && git commit -m 'fix: repair corrupted files, add project/title dates to intake' && git push")
print("")
print("NOTE: The database migration, LandTitle.java fields, and LandService.java")
print("atomicIntake logic for projectStartDate/titleIssueDate were already correct")
print("in your codebase from the last session -- this patch did not need to touch them.")