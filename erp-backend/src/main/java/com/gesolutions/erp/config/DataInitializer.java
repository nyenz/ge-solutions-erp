// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
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

        stageTemplateService.seedDefaultStagesIfEmpty();

        try {
            stageTemplateService.normalizeToDefaultStages();
            System.out.println(">>> [STAGE_TEMPLATE] Normalized master checklist to defaults.");
        } catch (Exception e) {
            System.err.println(">>> [STAGE_TEMPLATE] normalize warning: " + e.getMessage());
        }

        seedSampleProjects();
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

            ids.add(seedOne("SAMPLE-001", false, false, false, null, null, null, "2026-05-04",
                    5000000L, 2500000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER ONE", "SMPL00000001A", "0772000001" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection" }, idByName));

            ids.add(seedOne("SAMPLE-002", true, false, false, "SMPL-2002", "2026-03-01", "B-12", "2025-11-10",
                    8000000L, 8000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER TWO", "SMPL00000002A", "0772000002" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval", "Tax Assessment and Stamp Duty",
                                   "Registration and Title Issuance" }, idByName));

            ids.add(seedOne("SAMPLE-003", false, false, true, null, null, null, "2026-01-15",
                    6000000L, 1000000L, 50000L, 50000L,
                    new String[][] { { "SAMPLE OWNER THREE", "SMPL00000003A", "0772000003" } },
                    new String[] { "Field Work", "Deed Plan" }, idByName));

            ids.add(seedOne("SAMPLE-004", false, false, false, null, null, null, "2026-06-20",
                    10000000L, 1000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FOUR", "SMPL00000004A", "0772000004" },
                                     { "SAMPLE CO OWNER FOUR", "SMPL00000005A", "0772000005" } },
                    new String[] { "Field Work" }, idByName));

            ids.add(seedOne("SAMPLE-005", false, true, false, "SMPL-5005", "2026-07-20", "K-07", "2026-07-01",
                    4000000L, 3000000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER FIVE", "SMPL00000006A", "0772000006" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval" }, idByName));

            ids.add(seedOne("SAMPLE-006", false, false, false, null, null, null, "2026-08-20",
                    3000000L, 0L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER SIX", "SMPL00000007A", "0772000007" } },
                    new String[] { "Field Work" }, idByName));

            ids.add(seedOne("SAMPLE-007", true, false, false, "SMPL-7007", "2026-06-10", "W-03", "2026-02-02",
                    9000000L, 8100000L, 0L, 0L,
                    new String[][] { { "SAMPLE OWNER SEVEN", "SMPL00000008A", "0772000008" } },
                    new String[] { "Field Work", "Deed Plan", "LC Inspection",
                                   "District Land Board Approval", "Tax Assessment and Stamp Duty" }, idByName));

            int[] days = { 10, 200, 45, 60, 0, -1, 25 };
            try (java.sql.Connection conn = dataSource.getConnection()) {
                for (int i = 0; i < days.length && i < ids.size(); i++) {
                    if (ids.get(i) == null || days[i] < 0) continue;
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
            System.out.println(">>> [SAMPLE] Seeded 7 sample projects (district = SAMPLE DATA).");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] seed failed (non-fatal): " + e.getMessage());
        }
    }

    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake,
                                   boolean receivable, String titleId, String titleDate,
                                   String block, String startDate, long cost, long paid,
                                   long initFee, long monthlyFee, String[][] owners,
                                   String[] stages, java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
                .district("SAMPLE DATA").county("SAMPLE COUNTY")
                .subCounty("SAMPLE SUB").parish("SAMPLE PARISH")
                .village("SAMPLE VILLAGE").area("SAMPLE AREA")
                .tenure("FREEHOLD")
                .projectStartDate(java.time.LocalDate.parse(startDate))
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

            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_titles_project_index') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",

            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",

            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",

            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",

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

            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",

            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            "UPDATE land_projects lp SET district = lt.district, county = lt.county " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL " +
                "AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)",

            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",

            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",

            // PHASE G -- RETIRED TITLE DETAILS: dropped from DB
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
                                System.err.println(">>> [REGISTRY] FATAL: BCrypt verify FAILED after write!");
                            } else {
                                System.out.println(">>> [REGISTRY] SUCCESS: Password verified.");
                            }
                        }
                    }
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset.");
            }

        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
