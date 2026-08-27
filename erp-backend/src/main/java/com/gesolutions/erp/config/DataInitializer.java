// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
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

    @Value("${ADMIN_EMAIL}") private String adminEmail;
    @Value("${ADMIN_DEFAULT_PASSWORD}") private String adminDefaultPassword;

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
            expensePresetRepository.save(ExpensePreset.builder().name(name).createdBy("SYSTEM").build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    private void purgeSampleData() {
        String[] stmts = {
            "DELETE FROM payment_records WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM follow_up_logs WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_stages WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_proprietors WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM land_projects WHERE district = 'SAMPLE DATA'",
            "DELETE FROM land_titles WHERE plot_number LIKE 'SAMPLE-%'",
            "DELETE FROM clients WHERE national_id LIKE 'SMPL-%'",
        };
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) { try { st.execute(s); } catch (Exception ignore) {} }
            System.out.println(">>> [SAMPLE] Old sample data purged.");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] purge warning: " + e.getMessage());
        }
    }

    private java.util.UUID trySeed(String label, java.util.concurrent.Callable<java.util.UUID> supplier) {
        try { return supplier.call(); }
        catch (Exception e) {
            System.err.println(">>> [SAMPLE] " + label + " failed (skipped): " + e.getMessage());
            return null;
        }
    }

    private void seedSampleProjects() {
        purgeSampleData();
        java.util.List<com.gesolutions.erp.modules.land.model.StageTemplate> master = stageTemplateService.getActiveTemplate();
        java.util.Map<String, String> idByName = new java.util.HashMap<>();
        for (com.gesolutions.erp.modules.land.model.StageTemplate st : master) idByName.put(st.getStageName(), st.getId().toString());

        String FW = "Field Work", DP = "Deed Plan", LCI = "LC Inspection",
               DLB = "District Land Board Approval", TASD = "Tax Assessment and Stamp Duty",
               REG = "Registration and Title Issuance";

        java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();

        ids.add(trySeed("SAMPLE-101", () -> seedOne("SAMPLE-101", false, false, false, null, null, null, "2026-05-04",
                4000000L, 2000000L, 0L, 0L,
                new String[][] { { "JOHN SSERUGO", "SMPL-1001", "0772100100" } },
                new String[] { FW, DP }, null, null,
                new String[] { "WAKISO", "KYADONDO", "NAKAWA EAST", "BUKOTO", "KIIWA", "0.5 acres" },
                "Sample: fresh folder, paying well.", idByName)));

        ids.add(trySeed("SAMPLE-102", () -> seedOne("SAMPLE-102", false, false, false, null, null, null, "2026-07-10",
                6000000L, 0L, 0L, 0L,
                new String[][] { { "MARY NAKATO", "SMPL-1002", "0772100200" } },
                new String[] { FW }, null, null,
                new String[] { "MPIGI", "MPIGI COUNTY", "MPIGI TOWN", "CENTRAL", "KIZUNGU", "1 acre" },
                "Sample: folder, no payment yet.", idByName)));

        ids.add(trySeed("SAMPLE-103", () -> seedOne("SAMPLE-103", false, false, false, null, null, null, "2026-02-02",
                9000000L, 6000000L, 0L, 0L,
                new String[][] { { "PETER OPOK", "SMPL-1003", "0772100300" } },
                new String[] { FW, DP, LCI, DLB, TASD }, new String[] { REG }, null,
                new String[] { "MUKONO", "MUKONO COUNTY", "KATABI", "BULANGA", "NAGOGBE", "2 acres" },
                "Sample: all pre-stages done, awaiting registration.", idByName)));

        ids.add(trySeed("SAMPLE-104", () -> seedOne("SAMPLE-104", false, true, false, "SMPL-T-104", "2026-06-15", "KBL-77", "2026-06-01",
                15000000L, 11000000L, 0L, 0L,
                new String[][] { { "GRACE ACHENG", "SMPL-1004", "0772100400" } },
                new String[] { FW, DP, LCI, DLB }, null, null,
                new String[] { "KAMPALA", "KAMPALA CENTRAL", "MAKINDYE", "KABALAGALA", "GABA", "0.25 acres" },
                "Sample: new title in processing.", idByName)));

        ids.add(trySeed("SAMPLE-105", () -> seedOne("SAMPLE-105", true, false, false, "SMPL-T-105", "2025-12-01", "EBB-12", "2025-11-01",
                20000000L, 20000000L, 0L, 0L,
                new String[][] { { "DAVID KIGONGO", "SMPL-1005", "0772100500" } },
                new String[] { FW, DP, LCI, DLB, TASD, REG }, null, null,
                new String[] { "WAKISO", "ENTEBBE", "ENTEBBE TOWN", "KATABI", "LUGALA", "0.3 acres" },
                "Sample: legacy fully paid, awaiting release.", idByName)));

        ids.add(trySeed("SAMPLE-106", () -> seedOne("SAMPLE-106", true, false, false, "SMPL-T-106", "2025-06-20", "MSK-3", "2025-05-02",
                25000000L, 25000000L, 0L, 0L,
                new String[][] { { "SARAH NANSUBU", "SMPL-1006", "0772100600" } },
                new String[] { FW, DP, LCI, DLB, TASD, REG }, null, "RELEASE",
                new String[] { "MASAKA", "MASAKA CENTRAL", "MASAKA MUNICIPAL", "KIMAANYA", "KABOGA", "1.5 acres" },
                "Sample: released legacy title.", idByName)));

        ids.add(trySeed("SAMPLE-107", () -> seedOne("SAMPLE-107", true, false, true, "SMPL-T-107", "2025-09-10", "MBR-9", "2025-08-01",
                12000000L, 2000000L, 50000L, 50000L,
                new String[][] { { "JAMES TURYAHEREZA", "SMPL-1007", "0772100700" } },
                new String[] { FW, DP }, null, null,
                new String[] { "MBARARA", "MBARARA COUNTY", "MBARARA TOWN", "KAKIIKA", "NYAMITUKURA", "0.8 acres" },
                "Sample: receivable, storage fees accruing.", idByName)));

        ids.add(trySeed("SAMPLE-108", () -> seedOne("SAMPLE-108", false, true, true, "SMPL-T-108", "2026-02-14", "JIN-41", "2026-02-01",
                10000000L, 3000000L, 50000L, 50000L,
                new String[][] { { "RACHEL NABIRYE", "SMPL-1008", "0772100800" } },
                new String[] { FW, DP, LCI }, null, null,
                new String[] { "JINJA", "JINJA COUNTY", "JINJA MUNICIPAL", "WALUKUBA", "MPUMUDDE", "0.4 acres" },
                "Sample: receivable but paying recently.", idByName)));

        ids.add(trySeed("SAMPLE-109", () -> seedOne("SAMPLE-109", false, false, false, null, null, null, "2026-01-15",
                30000000L, 3000000L, 0L, 0L,
                new String[][] { { "SAMUEL KIBUKA", "SMPL-1091", "0772100901" },
                                 { "JOYCE NAKALEMA", "SMPL-1092", "0772100902" },
                                 { "BRIAN MUWANGA", "SMPL-1093", "0772100903" } },
                new String[] { FW }, null, null,
                new String[] { "KAYUNGA", "KAYUNGA COUNTY", "KAYUNGA TOWN", "BUKOMBE", "NAJJA", "5 acres" },
                "Sample: joint family plot, critical arrears.", idByName)));

        ids.add(trySeed("SAMPLE-110", () -> seedOne("SAMPLE-110", true, false, false, "SMPL-T-110", "2026-01-25", "LWR-5", "2026-01-05",
                18000000L, 16200000L, 0L, 0L,
                new String[][] { { "HENRY SSEMMAMBWA", "SMPL-1100", "0772101000" } },
                new String[] { FW, DP, LCI, DLB, TASD }, null, null,
                new String[] { "LUWERO", "LUWERO COUNTY", "LUWERO MUNICIPAL", "BAMUNU", "ZIWA", "3 acres" },
                "Sample: nearly paid legacy.", idByName)));

        int[] days = { 5, -1, 20, 3, 40, 200, 45, 12, 60, 25 };
        try (Connection conn = dataSource.getConnection()) {
            for (int i = 0; i < days.length && i < ids.size(); i++) {
                if (ids.get(i) == null || days[i] < 0) continue;
                java.sql.Timestamp ts = java.sql.Timestamp.valueOf(java.time.LocalDateTime.now().minusDays(days[i]));
                try (java.sql.PreparedStatement u1 = conn.prepareStatement("UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) {
                    u1.setTimestamp(1, ts); u1.setObject(2, ids.get(i)); u1.executeUpdate();
                }
                try (java.sql.PreparedStatement u2 = conn.prepareStatement("UPDATE payment_records SET timestamp = ? WHERE project_id = ?")) {
                    u2.setTimestamp(1, ts); u2.setObject(2, ids.get(i)); u2.executeUpdate();
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] backdate warning: " + e.getMessage());
        }

        long saved = ids.stream().filter(java.util.Objects::nonNull).count();
        System.out.println(">>> [SAMPLE] Seeded " + saved + " detailed sample projects (district = SAMPLE DATA).");
    }

    // 19 params, always called with 19 args.
    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake, boolean receivable,
                                   String titleId, String titleDate, String block, String startDate,
                                   long cost, long paid, long initFee, long monthlyFee,
                                   String[][] owners, String[] doneStages, String[] openStages,
                                   String releaseFlag, String[] loc, String note,
                                   java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
                .district(loc[0]).county(loc[1]).subCounty(loc[2]).parish(loc[3]).village(loc[4]).area(loc[5])
                .tenure("FREEHOLD")
                .projectStartDate(java.time.LocalDate.parse(startDate))
                .totalCost(java.math.BigDecimal.valueOf(cost))
                .initialPayment(java.math.BigDecimal.valueOf(paid))
                .isLegacy(legacy).titleAtIntake(titleAtIntake).isStartAsReceivable(receivable);
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
            os.add(LandEntryRequest.OwnerRequest.builder().fullName(o[0]).nationalId(o[1]).phone(o[2]).build());
        }
        b.owners(os);
        java.util.List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> ss = new java.util.ArrayList<>();
        for (String s : doneStages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid).stageName(s).isCustom(tid == null).isCompleted(true).build());
        }
        if (openStages != null) for (String s : openStages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid).stageName(s).isCustom(tid == null).isCompleted(false).build());
        }
        b.selectedStages(ss);
        if (note != null) {
            b.notes(java.util.List.of(LandEntryRequest.NoteRequest.builder().content(note).build()));
        }
        com.gesolutions.erp.modules.land.model.LandProject saved = landService.atomicIntake(b.build(), null);
        if ("RELEASE".equals(releaseFlag)) {
            try { landService.authorizeRelease(saved.getId(), "Sample release"); } catch (Exception ignore) {}
        }
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
            "DO $$ DECLARE cname text; BEGIN " +
                "SELECT tc.constraint_name INTO cname FROM information_schema.table_constraints tc " +
                "JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name " +
                "WHERE tc.table_name = 'clients' AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'phone_number' LIMIT 1; " +
                "IF cname IS NOT NULL THEN EXECUTE 'ALTER TABLE clients DROP CONSTRAINT ' || quote_ident(cname); END IF; " +
                "END $$",
            "ALTER TABLE land_projects ALTER COLUMN title_id DROP NOT NULL",
            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",
            "CREATE TABLE IF NOT EXISTS expense_presets (id UUID PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE, created_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT now())",
            "CREATE TABLE IF NOT EXISTS expenses (id UUID PRIMARY KEY, category VARCHAR(150) NOT NULL, amount NUMERIC(15,2) NOT NULL, note TEXT, recorded_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT now(), edited_at TIMESTAMP, edited_by VARCHAR(100))",
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
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS volume",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS folio",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS instrument_no",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS physical_box_number",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS survey_date",
        };
        try (Connection conn = dataSource.getConnection(); Statement stmt = conn.createStatement()) {
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
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) { if (rs.next()) exists = rs.getInt(1) > 0; }
            }
            if (!exists) {
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
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
