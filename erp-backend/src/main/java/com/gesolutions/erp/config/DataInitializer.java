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

    @Value("${ADMIN_EMAIL}") private String adminEmail;
    @Value("${ADMIN_DEFAULT_PASSWORD}") private String adminDefaultPassword;

    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
        runSchemaMigrations();
        seedRootUser();
        stageTemplateService.seedDefaultStagesIfEmpty();
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

    // fix52: FULL demo reset -- wipe ALL business rows so every deploy starts clean.
    private void purgeSampleData() {
        String[] stmts = {
            "DELETE FROM project_documents",
            "DELETE FROM payment_records",
            "DELETE FROM follow_up_logs",
            "DELETE FROM project_stages",
            "DELETE FROM project_proprietors",
            "DELETE FROM land_projects",
            "DELETE FROM land_titles",
            "DELETE FROM clients",
            "DELETE FROM audit_logs",
        };
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) { try { st.execute(s); } catch (Exception e) { System.err.println(">>> [RESET] skip: " + e.getMessage()); } }
            System.out.println(">>> [RESET] Full demo wipe complete (users/presets/templates kept).");
        } catch (Exception e) { System.err.println(">>> [RESET] wipe warning: " + e.getMessage()); }
    }

    private java.util.UUID trySeed(String label, java.util.concurrent.Callable<java.util.UUID> s) {
        try { return s.call(); } catch (Exception e) { System.err.println(">>> [SAMPLE] " + label + " failed: " + e.getMessage()); return null; }
    }

    private void seedSampleProjects() {
        purgeSampleData();
        java.util.List<StageTemplate> master = stageTemplateService.getActiveTemplate();
        java.util.Map<String, String> idByName = new java.util.HashMap<>();
        for (StageTemplate t : master) idByName.put(t.getStageName(), t.getId().toString());
        String FW="Field Work", DP="Deed Plan", LCI="LC Inspection", DLB="District Land Board Approval",
               TASD="Tax Assessment and Stamp Duty", REG="Registration and Title Issuance";
        java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();

        // ===== BACKLOG (no title yet) =====
        ids.add(trySeed("BL-001", () -> seedOne("BL-001", false,false,false, null,null,"B-23", "2025-11-15", 3500000L,400000L,0,0,
            new String[][]{{"Mugisha John","CM880234567890","0772123456"}}, new String[]{FW}, new String[]{DP,LCI,DLB}, null,
            new String[]{"Wakiso","Busiro","Kira","Najja","Kiwafu","Residential"}, "Client hesitant, negotiating installment plan", idByName)));
        ids.add(trySeed("BL-002", () -> seedOne("BL-002", false,false,false, null,null,"B-45", "2025-12-01", 4200000L,2100000L,0,0,
            new String[][]{{"Nakato Sarah","CM890345678901","0703234567"}}, new String[]{FW,DP}, new String[]{LCI,DLB}, null,
            new String[]{"Kampala","Kampala","Kawempe","Bukoto","Kisalosalo","Mixed Use"}, null, idByName)));
        ids.add(trySeed("BL-003", () -> seedOne("BL-003", false,false,false, null,null,"B-67", "2026-01-10", 3800000L,950000L,0,0,
            new String[][]{{"Ssekandi Robert","CM900456789012","0752345678"}}, new String[]{FW,"Survey Camp Verification"}, new String[]{DP,LCI,DLB}, null,
            new String[]{"Mukono","Mukono","Mukono Town","Kikooza","Namave","Industrial"}, "Custom stage added for survey camp", idByName)));
        ids.add(trySeed("BL-004", () -> seedOne("BL-004", false,false,false, null,null,"B-89", "2026-02-05", 5000000L,1250000L,0,0,
            new String[][]{{"Achen Grace","CM910567890123","0778345678"},{"Otim Peter","CM920678901234","0782456789"}},
            new String[]{FW}, new String[]{DP,LCI,DLB,TASD,REG}, null,
            new String[]{"Gulu","Gulu","Laroo","Laroo Ward","Bardege","Residential"}, null, idByName)));

        // ===== TITLED in-progress =====
        ids.add(trySeed("TP-001", () -> seedOne("TP-001", false,true,false, "T2026-001","2026-01-20","B-12", "2026-01-15", 4500000L,2250000L,0,0,
            new String[][]{{"Okello James","CM930789012345","0756456789"}}, new String[]{FW,DP,LCI}, new String[]{DLB,TASD,REG}, null,
            new String[]{"Jinja","Jinja","Central","Mpumudde","Kagumba","Commercial"}, null, idByName)));
        ids.add(trySeed("TP-002", () -> seedOne("TP-002", false,true,false, "T2026-002","2026-01-25","B-34", "2026-01-20", 4800000L,2400000L,0,0,
            new String[][]{{"Nambatya Fatuma","CM940890123456","0701567890"}}, new String[]{FW,DP,LCI,DLB}, new String[]{TASD,REG}, null,
            new String[]{"Mbarara","Mbarara","Mbarara City","Kakoba","Buhimba","Residential"}, "Client paid 3 weeks ago", idByName)));
        ids.add(trySeed("TP-003", () -> seedOne("TP-003", false,true,false, "T2026-003","2025-12-10","B-56", "2025-12-05", 5200000L,1300000L,0,0,
            new String[][]{{"Tumwine Alex","CM950901234567","0789678901"}}, new String[]{FW,DP}, new String[]{LCI,DLB,TASD,REG}, null,
            new String[]{"Kabarole","Kabarole","Fort Portal","Central","Karambi","Agricultural"}, "Payment overdue 6 weeks", idByName)));
        ids.add(trySeed("TP-004", () -> seedOne("TP-004", false,true,false, "T2026-004","2026-02-01","B-78", "2026-01-28", 4700000L,2350000L,0,0,
            new String[][]{{"Adongo Mary","CM960012345678","0775789012"}}, new String[]{FW,DP,LCI,"Additional Verification"}, new String[]{DLB,TASD,REG}, null,
            new String[]{"Lira","Lira","Lira City","Ojwina","Adyel","Mixed Use"}, "Custom stage for additional verification", idByName)));
        ids.add(trySeed("TP-005", () -> seedOne("TP-005", false,true,false, "T2026-005","2026-02-05","B-90", "2026-01-30", 5100000L,3570000L,0,0,
            new String[][]{{"Byaruhanga Charles","CM970123456789","0708890123"}}, new String[]{FW,DP,LCI,DLB,TASD}, new String[]{REG}, null,
            new String[]{"Hoima","Hoima","Hoima City","Bujumbura","Kasingo","Residential"}, null, idByName)));
        ids.add(trySeed("TP-006", () -> seedOne("TP-006", false,true,false, "T2026-006","2026-02-10","B-23", "2026-02-05", 6000000L,3000000L,0,0,
            new String[][]{{"Opiyo Samuel","CM980234567890","0782901234"},{"Akello Janet","CM990345678901","0773012345"}},
            new String[]{FW,DP}, new String[]{LCI,DLB,TASD,REG}, null,
            new String[]{"Arua","Arua","Arua City","River Oli","Anyafio","Commercial"}, null, idByName)));

        // ===== LEGACY =====
        ids.add(trySeed("LG-001", () -> seedOne("LG-001", true,true,false, "L1985-001","1985-06-15","B-11", "2025-08-01", 3500000L,1750000L,0,0,
            new String[][]{{"Mukasa David","CM000456789012","0757123456"}}, new String[]{FW,DP,LCI,DLB}, new String[]{TASD,REG}, null,
            new String[]{"Masaka","Masaka","Masaka City","Kimaanya","Kyesiga","Residential"}, "Legacy title from 1985", idByName)));
        ids.add(trySeed("LG-002", () -> seedOne("LG-002", true,true,true, "L1990-002","1990-03-20","B-22", "2024-05-10", 4000000L,800000L,75000,25000,
            new String[][]{{"Nambi Christine","CM010567890123","0706234567"}}, new String[]{FW,DP}, new String[]{LCI,DLB,TASD,REG}, null,
            new String[]{"Mbale","Mbale","Mbale City","Industrial","Wanale","Industrial"}, "Receivable since 2024, storage fees accumulating", idByName)));
        ids.add(trySeed("LG-003", () -> seedOne("LG-003", true,true,true, "L1988-003","1988-09-12","B-33", "2024-03-15", 3800000L,380000L,100000,30000,
            new String[][]{{"Okiror Joseph","CM020678901234","0783345678"}}, new String[]{FW}, new String[]{DP,LCI,DLB,TASD,REG}, null,
            new String[]{"Soroti","Soroti","Soroti City","Gweri","Arapai","Agricultural"}, "Critical - less than 10% paid", idByName)));
        ids.add(trySeed("LG-004", () -> seedOne("LG-004", true,true,false, "L1992-004","1992-07-08","B-44", "2025-10-20", 4200000L,4200000L,0,0,
            new String[][]{{"Alupo Susan","CM030789012345","0758456789"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, null,
            new String[]{"Tororo","Tororo","Tororo Town","Molo","Kadama","Residential"}, "Fully paid, awaiting client collection", idByName)));
        ids.add(trySeed("LG-005", () -> seedOne("LG-005", true,true,false, "L1987-005","1987-11-25","B-55", "2025-09-05", 5500000L,2750000L,0,0,
            new String[][]{{"Odong Moses","CM040890123456","0705567890"},{"Atim Rebecca","CM050901234567","0780678901"}},
            new String[]{FW,DP,LCI}, new String[]{DLB,TASD,REG}, null,
            new String[]{"Iganga","Iganga","Iganga Town","Nakalama","Kigulu","Mixed Use"}, null, idByName)));

        // ===== FULLY PAID =====
        ids.add(trySeed("FP-001", () -> seedOne("FP-001", false,true,false, "T2026-101","2026-03-01","B-101", "2026-02-25", 4300000L,4300000L,0,0,
            new String[][]{{"Kabagambe Francis","CM060012345678","0771789012"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, null,
            new String[]{"Bushenyi","Bushenyi","Bushenyi Town","Kakoba","Ishaka","Residential"}, "Fully paid 2 days ago", idByName)));
        ids.add(trySeed("FP-002", () -> seedOne("FP-002", false,true,false, "T2026-102","2026-03-05","B-102", "2026-02-28", 4600000L,4600000L,0,0,
            new String[][]{{"Nakimera Diana","CM070123456789","0700890123"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, null,
            new String[]{"Rakai","Rakai","Rakai Town","Kalisizo","Kyotera","Agricultural"}, "Paid last week", idByName)));
        ids.add(trySeed("FP-003", () -> seedOne("FP-003", false,true,false, "T2026-103","2026-03-08","B-103", "2026-03-01", 5800000L,5800000L,0,0,
            new String[][]{{"Mwesigye Patrick","CM080234567890","0787901234"},{"Tumusiime Esther","CM090345678901","0754012345"}},
            new String[]{FW,DP,LCI,DLB,TASD,REG}, null, null,
            new String[]{"Kabarole","Kabarole","Fort Portal","Karambi","Kisimba","Residential"}, null, idByName)));
        ids.add(trySeed("FP-004", () -> seedOne("FP-004", false,true,false, "T2026-104","2026-03-10","B-104", "2026-03-05", 5200000L,5200000L,0,0,
            new String[][]{{"Atwijuka Martin","CM100456789012","0772123901"}}, new String[]{FW,DP,LCI,DLB,TASD,REG,"Final Quality Check"}, null, null,
            new String[]{"Sheema","Sheema","Sheema Town","Kitagata","Kazinga","Mixed Use"}, "Custom final QC stage completed", idByName)));
        ids.add(trySeed("FP-005", () -> seedOne("FP-005", false,true,false, "T2026-105","2026-03-12","B-105", "2025-11-15", 4800000L,4800000L,0,0,
            new String[][]{{"Nsubuga Ronald","CM110567890123","0701234012"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, null,
            new String[]{"Luweero","Luweero","Luweero Town","Bamunanika","Wobulenzi","Residential"}, "Was receivable, cleared balance", idByName)));

        // ===== RELEASED =====
        ids.add(trySeed("RL-001", () -> seedOne("RL-001", false,true,false, "T2026-201","2026-02-15","B-201", "2025-12-01", 4100000L,4100000L,0,0,
            new String[][]{{"Akello Grace","CM120678901234","0785345123"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, "RELEASE",
            new String[]{"Lira","Lira","Lira City","Ojwina","Adyel","Residential"}, "Released to client 2 weeks ago", idByName)));
        ids.add(trySeed("RL-002", () -> seedOne("RL-002", false,true,false, "T2026-202","2026-02-18","B-202", "2025-12-05", 5300000L,5300000L,0,0,
            new String[][]{{"Opio Daniel","CM130789012345","0756456234"},{"Auma Judith","CM140890123456","0707567345"}},
            new String[]{FW,DP,LCI,DLB,TASD,REG}, null, "RELEASE",
            new String[]{"Gulu","Gulu","Gulu","Laroo","Bardege","Residential"}, null, idByName)));
        ids.add(trySeed("RL-003", () -> seedOne("RL-003", true,true,false, "L1989-203","1989-04-10","B-203", "2025-10-01", 3900000L,3900000L,0,0,
            new String[][]{{"Okot Simon","CM150901234567","0788678456"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, "RELEASE",
            new String[]{"Kitgum","Kitgum","Kitgum Town","Pandongo","Paimol","Agricultural"}, "Legacy title released", idByName)));

        // ===== RECEIVABLE =====
        ids.add(trySeed("RV-001", () -> seedOne("RV-001", false,true,true, "T2026-301","2025-08-20","B-301", "2025-06-01", 4500000L,900000L,50000,20000,
            new String[][]{{"Adong Sharon","CM160012345678","0779789567"}}, new String[]{FW,DP}, new String[]{LCI,DLB,TASD,REG}, null,
            new String[]{"Arua","Arua","Arua","River Oli","Anyafio","Residential"}, "Client unresponsive for 3 months", idByName)));
        ids.add(trySeed("RV-002", () -> seedOne("RV-002", false,true,true, "T2026-302","2025-09-10","B-302", "2025-07-15", 5000000L,750000L,75000,25000,
            new String[][]{{"Ochola Brian","CM170123456789","0708890678"}}, new String[]{FW}, new String[]{DP,LCI,DLB,TASD,REG}, null,
            new String[]{"Nebbi","Nebbi","Nebbi Town","Paidha","Panyimur","Agricultural"}, "Excuses: harvest season, family emergency", idByName)));

        // backdate payments for realistic badges
        int[] days = { 3, 21, 45, 8, 5, 22, 42, 6, 2, 15, 10, 120, 180, 30, 25, 2, 7, 1, 4, 90, 14, 18, 40, 95, 105 };
        try (Connection conn = dataSource.getConnection()) {
            for (int i = 0; i < days.length && i < ids.size(); i++) {
                if (ids.get(i) == null) continue;
                java.sql.Timestamp ts = java.sql.Timestamp.valueOf(java.time.LocalDateTime.now().minusDays(days[i]));
                try (java.sql.PreparedStatement u1 = conn.prepareStatement("UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) { u1.setTimestamp(1, ts); u1.setObject(2, ids.get(i)); u1.executeUpdate(); }
                try (java.sql.PreparedStatement u2 = conn.prepareStatement("UPDATE payment_records SET timestamp = ? WHERE project_id = ?")) { u2.setTimestamp(1, ts); u2.setObject(2, ids.get(i)); u2.executeUpdate(); }
            }
        } catch (Exception e) { System.err.println(">>> [SAMPLE] backdate warning: " + e.getMessage()); }
        System.out.println(">>> [SAMPLE] Seeded " + ids.stream().filter(java.util.Objects::nonNull).count() + " demo projects.");
    }

    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake, boolean receivable,
            String titleId, String titleDate, String block, String startDate, long cost, long paid, long initFee, long monthlyFee,
            String[][] owners, String[] done, String[] open, String release, String[] loc, String note,
            java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
            .district(loc[0]).county(loc[1]).subCounty(loc[2]).parish(loc[3]).village(loc[4]).area(loc[5])
            .tenure("FREEHOLD").projectStartDate(java.time.LocalDate.parse(startDate))
            .totalCost(java.math.BigDecimal.valueOf(cost)).initialPayment(java.math.BigDecimal.valueOf(paid))
            .isLegacy(legacy).titleAtIntake(titleAtIntake).isStartAsReceivable(receivable);
        if (plot != null) b.plotNumber(plot);
        if (titleId != null) b.titleId(titleId);
        if (block != null) b.blockRoad(block);
        if (titleDate != null) b.titleIssueDate(java.time.LocalDate.parse(titleDate));
        if (receivable) { b.initialStorageFee(java.math.BigDecimal.valueOf(initFee>0?initFee:50000)); b.monthlyStorageFee(java.math.BigDecimal.valueOf(monthlyFee>0?monthlyFee:50000)); }
        java.util.List<LandEntryRequest.OwnerRequest> os = new java.util.ArrayList<>();
        for (String[] o : owners) os.add(LandEntryRequest.OwnerRequest.builder().fullName(o[0]).nationalId(o[1]).phone(o[2]).build());
        b.owners(os);
        java.util.List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> ss = new java.util.ArrayList<>();
        for (String s : done) { String t = idByName.get(s); ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder().stageTemplateId(t).stageName(s).isCustom(t==null).isCompleted(true).build()); }
        if (open != null) for (String s : open) { String t = idByName.get(s); ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder().stageTemplateId(t).stageName(s).isCustom(t==null).isCompleted(false).build()); }
        b.selectedStages(ss);
        if (note != null) b.notes(java.util.List.of(LandEntryRequest.NoteRequest.builder().content(note).build()));
        LandProject saved = landService.atomicIntake(b.build(), null);
        if ("RELEASE".equals(release)) { try { landService.authorizeRelease(saved.getId(), "Sample release"); } catch (Exception e) {} }
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
                try { stmt.execute(sql); System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length()))); }
                catch (Exception e) { System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage()); }
            }
        } catch (Exception e) { System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage()); }
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
                try (java.sql.PreparedStatement ps = conn.prepareStatement(
                        "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) " +
                        "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)")) {
                    ps.setObject(1, java.util.UUID.randomUUID()); ps.setString(2, email); ps.setString(3, encodedPassword);
                    ps.executeUpdate();
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset.");
            }
        } catch (Exception e) { System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:"); e.printStackTrace(); }
    }
}
