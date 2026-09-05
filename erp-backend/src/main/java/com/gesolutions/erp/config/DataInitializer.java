package com.gesolutions.erp.config;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
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
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {
    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;
    private final LandService landService;
    private final ClientRepository clientRepository;
    private final RecoveryNoteRepository recoveryNoteRepository;
    private final FollowUpRepository followUpRepository;
    @Value("${ADMIN_EMAIL}") private String adminEmail;
    @Value("${ADMIN_DEFAULT_PASSWORD}") private String adminDefaultPassword;
    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
        runSchemaMigrations();
        seedRootUser();
        stageTemplateService.seedDefaultStagesIfEmpty();
        seedScenarioDataOnce();
        seedDefaultExpensePresets();
        System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
    }
    public void seedDefaultExpensePresets() {
        if (expensePresetRepository.count() > 0) return;
        String[] defaults = { "Office", "Fieldwork", "Land Office" };
        for (String name : defaults) expensePresetRepository.save(ExpensePreset.builder().name(name).createdBy("SYSTEM").build());
    }
    // ---------- ONE-TIME SCENARIO SEED (wipe once, seed once, never again) ----------
    public void seedScenarioDataOnce() {
        try (Connection conn = dataSource.getConnection()) {
            try (Statement st = conn.createStatement()) {
                st.execute("CREATE TABLE IF NOT EXISTS scenario_seed_flag (id INTEGER PRIMARY KEY, seeded_at TIMESTAMP NOT NULL DEFAULT now())");
            }
            boolean seeded;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM scenario_seed_flag"); java.sql.ResultSet rs = ps.executeQuery()) { rs.next(); seeded = rs.getInt(1) > 0; }
            if (seeded) { System.out.println(">>> [SCENARIO] Already seeded -- skipping."); return; }
            purgeAll(conn);
            seedScenarios();
            try (Statement st = conn.createStatement()) { st.execute("INSERT INTO scenario_seed_flag (id) VALUES (1)"); }
            System.out.println(">>> [SCENARIO] Scenario dataset seeded (28 projects).");
        } catch (Exception e) { System.err.println(">>> [SCENARIO] seed fault: " + e.getMessage()); }
    }
    private void purgeAll(Connection conn) {
        String[] stmts = {
            "DELETE FROM notification_reads", "DELETE FROM notifications", "DELETE FROM recovery_notes",
            "DELETE FROM payment_records", "DELETE FROM follow_up_logs", "DELETE FROM project_documents",
            "DELETE FROM project_stages", "DELETE FROM project_proprietors", "DELETE FROM land_projects",
            "DELETE FROM land_titles", "DELETE FROM clients", "DELETE FROM audit_logs",
            "UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1"
        };
        try (Statement st = conn.createStatement()) { for (String s : stmts) { try { st.execute(s); } catch (Exception e) { System.err.println(">>> [SCENARIO] purge skip: " + e.getMessage()); } } }
    }
    private String d(int daysAgo) { return LocalDate.now().minusDays(daysAgo).toString(); }
    private void flag(UUID pid, String sql) {
        try (Connection conn = dataSource.getConnection(); java.sql.PreparedStatement ps = conn.prepareStatement("UPDATE land_projects SET " + sql + " WHERE id = ?")) { ps.setObject(1, pid); ps.executeUpdate(); } catch (Exception e) { System.err.println(">>> [SCENARIO] flag fault: " + e.getMessage()); }
    }
    private void backdatePayment(UUID pid, int daysAgo, long amount, String type) {
        try (Connection conn = dataSource.getConnection()) {
            java.sql.Timestamp ts = java.sql.Timestamp.valueOf(LocalDateTime.now().minusDays(daysAgo));
            try (java.sql.PreparedStatement ps = conn.prepareStatement("UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) { ps.setTimestamp(1, ts); ps.setObject(2, pid); ps.executeUpdate(); }
            try (java.sql.PreparedStatement ps = conn.prepareStatement("INSERT INTO payment_records (id, project_id, amount_paid, payment_type, recorded_by, notes, timestamp, balance_after) VALUES (?, ?, ?, ?, 'SYSTEM', 'Scenario seed', ?, 0)")) { ps.setObject(1, UUID.randomUUID()); ps.setObject(2, pid); ps.setBigDecimal(3, java.math.BigDecimal.valueOf(amount)); ps.setString(4, type); ps.setTimestamp(5, ts); ps.executeUpdate(); }
        } catch (Exception e) { System.err.println(">>> [SCENARIO] payment fault: " + e.getMessage()); }
    }
    private void doc(UUID pid, String type, String name) {
        try (Connection conn = dataSource.getConnection(); java.sql.PreparedStatement ps = conn.prepareStatement("INSERT INTO project_documents (id, project_id, file_name, file_type, file_path, internal_notes, uploaded_by, uploaded_at) VALUES (?, ?, ?, ?, ?, 'Scenario doc', 'SYSTEM', now())")) { ps.setObject(1, UUID.randomUUID()); ps.setObject(2, pid); ps.setString(3, name); ps.setString(4, type); ps.setString(5, "https://res.cloudinary.com/dfd115bnz/raw/upload/v1/ge_solutions/demo/" + name); ps.executeUpdate(); } catch (Exception e) { System.err.println(">>> [SCENARIO] doc fault: " + e.getMessage()); }
    }
    private void fup(UUID pid, String text, int daysAgo) {
        followUpRepository.save(FollowUpLog.builder().projectId(pid).notes(text).recordedBy("SYSTEM").timestamp(LocalDateTime.now().minusDays(daysAgo)).build());
    }
    private void note(String nin, String tag, String tone, boolean attempt, int daysAgo, String text, Integer promiseInDays) {
        clientRepository.findByNationalId(nin).ifPresent(c -> recoveryNoteRepository.save(RecoveryNote.builder().client(c).author(null).tag(tag).tone(tone).countsAsAttempt(attempt).text(text).promiseDate(promiseInDays == null ? null : LocalDate.now().plusDays(promiseInDays)).createdAt(LocalDateTime.now().minusDays(daysAgo)).build()));
    }
    private void touchClient(String nin, int daysAgo, Double reliability) {
        clientRepository.findByNationalId(nin).ifPresent(c -> { c.setLastContactedAt(LocalDateTime.now().minusDays(daysAgo)); if (reliability != null) c.setReliabilityScore(reliability); clientRepository.save(c); });
    }
    private void seedScenarios() throws Exception {
        List<StageTemplate> master = stageTemplateService.getActiveTemplate();
        Map<String, String> idByName = new HashMap<>();
        for (StageTemplate t : master) idByName.put(t.getStageName(), t.getId().toString());
        String FW = "Field Work", DP = "Deed Plan", LCI = "LC Inspection", DLB = "District Land Board Approval", TASD = "Tax Assessment and Stamp Duty", REG = "Registration and Title Issuance";
        String[] ALL = { FW, DP, LCI, DLB, TASD, REG };
        Map<String, UUID> S = new HashMap<>();
        // INTAKE + LEDGER coverage
        S.put("s1", seedOne(null, false, false, false, null, null, "B-101", d(40), 3500000, 0, 0, 0, new String[][] { { "MUGISHA JOHN", "CM900000000001", "0772000001" } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "WAKISO", "BUSIRO", "KIRA", "NAJJA", "KIWAFU", "Residential" }, "New folder, field work started", idByName));
        S.put("s2", seedOne(null, false, false, false, null, null, "B-102", d(60), 4200000, 2100000, 0, 0, new String[][] { { "NAKATO SARAH", "CM900000000002", "0772000002" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KAMPALA", "KAWEMPE", "BUKOTO", "KISALOSALO", "Mixed Use" }, null, idByName));
        S.put("s3", seedOne(null, false, false, false, null, null, "B-103", d(90), 3800000, 380000, 0, 0, new String[][] { { "SSEKANDI ROBERT", "CM900000000003", "0772000003" }, { "ACHEN GRACE", "CM900000000004", "0772000004" } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "MUKONO", "MUKONO", "MUKONO TOWN", "KIKOOZA", "NAMAVE", "Industrial" }, "Joint owners, critical progress", idByName));
        S.put("s4", seedOne(null, false, false, false, null, null, "B-104", d(30), 5000000, 1250000, 0, 0, new String[][] { { "OTIM PETER", "CM900000000005", "0772000005" } }, new String[] { FW, "Survey Camp Verification" }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "GULU", "GULU", "LAROO", "LAROO WARD", "BARDEGE", "Residential" }, "Custom stage added", idByName));
        S.put("s5", seedOne("P-201", false, true, false, "T2026-201", d(50), "B-105", d(70), 4500000, 3150000, 0, 0, new String[][] { { "OKELLO JAMES", "CM900000000006", "0772000006" } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "JINJA", "JINJA", "CENTRAL", "MPUMUDDE", "KAGUMBA", "Commercial" }, null, idByName));
        S.put("s6", seedOne("P-202", false, true, false, "T2026-202", d(45), "B-106", d(80), 4800000, 4800000, 0, 0, new String[][] { { "NAMBATYA FATUMA", "CM900000000007", "0772000007" }, { "TUMWINE ALEX", "CM900000000008", "0772000008" } }, ALL, null, null, new String[] { "MBARARA", "MBARARA", "MBARARA CITY", "KAKOBA", "BUHIMBA", "Residential" }, "Fully paid, awaiting release", idByName));
        S.put("s7", seedOne("P-203", false, true, false, "T2026-203", d(40), "B-107", d(85), 5200000, 5200000, 0, 0, new String[][] { { "ADONGO MARY", "CM900000000009", "0772000009" } }, ALL, null, "RELEASE", new String[] { "LIRA", "LIRA", "LIRA CITY", "OJWINA", "ADYEL", "Residential" }, "Released to client", idByName));
        S.put("s8", seedOne("L1985-301", true, true, false, "L1985-301", "1985-06-15", "B-108", d(400), 3500000, 1750000, 0, 0, new String[][] { { "BYARUHANGA CHARLES", "CM900000000010", "0772000010" } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "MASAKA", "MASAKA", "MASAKA CITY", "KIMAANYA", "KYESIGA", "Residential" }, "Legacy, 400 days silent, auto-receivable candidate", idByName));
        S.put("s9", seedOne("L1990-302", true, true, false, "L1990-302", "1990-03-20", "B-109", d(300), 4000000, 800000, 0, 0, new String[][] { { "OPIYO SAMUEL", "CM900000000011", "0772000011" }, { "AKELLO JANET", "CM900000000012", "0772000012" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "MBALE", "MBALE", "MBALE CITY", "INDUSTRIAL", "WANALE", "Industrial" }, "Legacy joint", idByName));
        // RECEIVABLE family
        S.put("s10", seedOne("P-301", false, true, true, "T2026-301", d(350), "B-110", d(360), 4500000, 900000, 50000, 50000, new String[][] { { "MUKASA DAVID", "CM900000000013", "0772000013" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "ARUA", "ARUA", "ARUA", "RIVER OLI", "ANYAFIO", "Residential" }, "Receivable, silent", idByName));
        S.put("s11", seedOne("P-302", false, true, true, "T2026-302", d(320), "B-111", d(330), 5000000, 750000, 50000, 50000, new String[][] { { "NAMBI CHRISTINE", "CM900000000014", "0772000014" } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "NEBBI", "NEBBI", "NEBBI TOWN", "PAIDHA", "PANYIMUR", "Agricultural" }, "Receivable, paying", idByName));
        S.put("s12", seedOne("P-303", false, true, true, "T2026-303", d(300), "B-112", d(310), 3800000, 380000, 50000, 50000, new String[][] { { "OKIROR JOSEPH", "CM900000000015", "0772000015" } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "SOROTI", "SOROTI", "SOROTI CITY", "GWERI", "ARAPAI", "Agricultural" }, "Receivable frozen (negotiation)", idByName));
        S.put("s13", seedOne("P-304", false, true, true, "T2026-304", d(290), "B-113", d(300), 4200000, 420000, 50000, 50000, new String[][] { { "ALUPO SUSAN", "CM900000000016", "0772000016" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "TORORO", "TORORO", "TORORO TOWN", "MOLO", "KADAMA", "Residential" }, "Receivable, deadline passed", idByName));
        S.put("s14", seedOne("P-305", false, true, false, "T2026-305", d(100), "B-114", d(120), 4700000, 2350000, 0, 0, new String[][] { { "ODONG MOSES", "CM900000000017", "0772000017" } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "HOIMA", "HOIMA", "HOIMA CITY", "BUJUMBURA", "KASINGO", "Residential" }, "Problem flag", idByName));
        S.put("s15", seedOne("P-306", false, true, true, "T2026-306", d(280), "B-115", d(290), 6000000, 3000000, 75000, 75000, new String[][] { { "ATIM REBECCA", "CM900000000018", "0772000018" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "ARUA", "ARUA", "ARUA CITY", "RIVER OLI", "ANYAFIO", "Commercial" }, "Custom storage rate 75k", idByName));
        // RECOVERY + NOTES coverage
        S.put("s16", seedOne("P-401", false, true, false, "T2026-401", d(90), "B-116", d(120), 4300000, 2150000, 0, 0, new String[][] { { "KABAGAMBE FRANCIS", "CM900000000019", "0772000019" } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "BUSHENYI", "BUSHENYI", "BUSHENYI TOWN", "KAKOBA", "ISHAKA", "Residential" }, null, idByName));
        S.put("s17", seedOne("P-402", false, true, false, "T2026-402", d(95), "B-117", d(130), 4600000, 2300000, 0, 0, new String[][] { { "NAKIMERA DIANA", "CM900000000020", "0772000020" } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "RAKAI", "RAKAI", "RAKAI TOWN", "KALISIZO", "KYOTERA", "Agricultural" }, null, idByName));
        S.put("s18", seedOne("P-403", false, true, false, "T2026-403", d(88), "B-118", d(140), 5800000, 2900000, 0, 0, new String[][] { { "MWESIGYE PATRICK", "CM900000000021", "0772000021" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KABAROLE", "KABAROLE", "FORT PORTAL", "KARAMBI", "KISIMBA", "Residential" }, null, idByName));
        S.put("s19", seedOne("P-404", false, true, false, "T2026-404", d(85), "B-119", d(150), 5200000, 2600000, 0, 0, new String[][] { { "ATWIJUKA MARTIN", "CM900000000022", "0772000022" } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "SHEEMA", "SHEEMA", "SHEEMA TOWN", "KITAGATA", "KAZINGA", "Mixed Use" }, null, idByName));
        S.put("s20", seedOne("P-405", false, true, false, "T2026-405", d(80), "B-120", d(160), 4800000, 2400000, 0, 0, new String[][] { { "NSUBUGA RONALD", "CM900000000023", "0772000023" } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "LUWEERO", "LUWEERO", "LUWEERO TOWN", "BAMUNANIKA", "WOBULENZI", "Residential" }, null, idByName));
        S.put("s21", seedOne("P-406", false, true, false, "T2026-406", d(75), "B-121", d(170), 4100000, 2050000, 0, 0, new String[][] { { "ADONG SHARON", "CM900000000024", "0772000024" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KAMPALA", "MAKINDYE", "KIBULI", "KIBULI", "Residential" }, null, idByName));
        S.put("s22", seedOne("P-407", false, true, false, "T2026-407", d(70), "B-122", d(180), 5300000, 2650000, 0, 0, new String[][] { { "OCHOLA BRIAN", "CM900000000025", "0772000025" } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "JINJA", "JINJA", "CENTRAL", "MPUMUDDE", "KAGUMBA", "Commercial" }, null, idByName));
        S.put("s23", seedOne("P-408", false, true, false, "T2026-408", d(65), "B-123", d(190), 3900000, 1950000, 0, 0, new String[][] { { "AKELLO GRACE", "CM900000000026", "0772000026" } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "GULU", "GULU", "LAROO", "LAROO WARD", "BARDEGE", "Residential" }, null, idByName));
        S.put("s24", seedOne("P-409", false, true, false, "T2026-409", d(60), "B-124", d(200), 4400000, 2200000, 0, 0, new String[][] { { "OPIO DANIEL", "CM900000000027", "0772000027" }, { "AUMA JUDITH", "CM900000000028", "0772000028" } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "WAKISO", "BUSIRO", "KIRA", "NAJJA", "KIWAFU", "Residential" }, "Joint - co-owner warning demo", idByName));
        S.put("s25", seedOne("P-410", false, true, false, "T2026-410", d(55), "B-125", d(210), 4900000, 2450000, 0, 0, new String[][] { { "OKOT SIMON", "CM900000000029", "0772000029" } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KITGUM", "KITGUM", "KITGUM TOWN", "PANDONGO", "PAIMOL", "Agricultural" }, null, idByName));
        S.put("s26", seedOne("P-411", false, true, false, "T2026-411", d(50), "B-126", d(220), 4000000, 2000000, 0, 0, new String[][] { { "NAMUYANJA RITA", "CM900000000030", "0772000030" } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "MUKONO", "MUKONO", "MUKONO TOWN", "KIKOOZA", "NAMAVE", "Industrial" }, null, idByName));
        S.put("s27", seedOne(null, false, false, false, null, null, "B-127", d(0), 3600000, 900000, 0, 0, new String[][] { { "KAGWA PETER", "CM900000000031", "0772000031" } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KAMPALA", "KAWEMPE", "BUKOTO", "KISALOSALO", "Mixed Use" }, "Intake today", idByName));
        S.put("s28", seedOne("P-412", false, true, false, "T2026-412", d(45), "B-128", d(230), 5100000, 3570000, 0, 0, new String[][] { { "NABIRYE MARY", "CM900000000032", "0772000032" } }, new String[] { FW, DP, LCI, DLB, TASD }, new String[] { REG }, null, new String[] { "KAMPALA", "KAMPALA", "NAKAWA", "BUGOLOBI", "BUGOLOBI", "Residential" }, "Documents demo", idByName));
        // payments + badges
        backdatePayment(S.get("s2"), 5, 1000000, "STANDARD");
        backdatePayment(S.get("s3"), 60, 380000, "STANDARD");
        backdatePayment(S.get("s5"), 20, 900000, "STANDARD");
        backdatePayment(S.get("s8"), 400, 500000, "STANDARD");
        backdatePayment(S.get("s10"), 300, 400000, "STANDARD");
        backdatePayment(S.get("s11"), 5, 500000, "RECEIVABLE_PARTIAL");
        // folder flags
        flag(S.get("s12"), "storage_paused = true, negotiation_deadline = now() + interval '30 days'");
        flag(S.get("s13"), "negotiation_deadline = now() - interval '5 days'");
        flag(S.get("s14"), "is_problem = true");
        flag(S.get("s15"), "storage_fee_override = 75000");
        // documents
        doc(S.get("s28"), "DEED_PLAN", "demo-deed-plan.pdf");
        doc(S.get("s28"), "NIN_SCAN", "demo-nin-scan.jpg");
        // folder notes
        fup(S.get("s1"), "Client visited office, asked about stage timeline", 2);
        fup(S.get("s10"), "Called about storage fees, requested statement", 12);
        fup(S.get("s24"), "Co-owner AUMA asked to be contacted separately", 1);
        // recovery histories
        note("CM900000000019", "answered call", "POSITIVE", true, 3, "Will pay after harvest", null);
        touchClient("CM900000000019", 3, 80.0);
        note("CM900000000020", "answered call", "POSITIVE", true, 1, "First contact this month", null);
        note("CM900000000020", "committed to pay", "POSITIVE", true, 0, "Promised Friday", null);
        touchClient("CM900000000020", 0, 85.0);
        note("CM900000000021", "answered call", "POSITIVE", true, 20, null, null);
        note("CM900000000021", "failed to pay", "NEGATIVE", false, 18, "Did not honour promise", null);
        touchClient("CM900000000021", 20, 60.0);
        note("CM900000000022", "committed to pay", "POSITIVE", true, 10, "Promise date passed", -1);
        touchClient("CM900000000022", 10, 70.0);
        note("CM900000000023", "committed to pay", "POSITIVE", true, 5, "Future promise", 7);
        touchClient("CM900000000023", 5, 75.0);
        note("CM900000000024", "not picking up", "NEGATIVE", true, 20, null, null);
        note("CM900000000024", "phone off", "NEGATIVE", true, 16, null, null);
        touchClient("CM900000000024", 16, 55.0);
        note("CM900000000025", "answered call", "POSITIVE", true, 35, null, null);
        note("CM900000000025", "needs site visit", "NEGATIVE", false, 20, "Boundary dispute", null);
        touchClient("CM900000000025", 35, 65.0);
        note("CM900000000026", "answered call", "POSITIVE", true, 45, null, null);
        touchClient("CM900000000026", 45, 70.0);
        note("CM900000000027", "answered call", "POSITIVE", true, 1, "Reached OPIO only", null);
        touchClient("CM900000000027", 1, 80.0);
        note("CM900000000029", "committed to pay", "POSITIVE", true, 30, "Old promise", -20);
        note("CM900000000029", "failed to pay", "NEGATIVE", false, 18, "Broke promise", null);
        touchClient("CM900000000029", 30, 35.0);
        note("CM900000000030", "not picking up", "NEGATIVE", true, 20, null, null);
        touchClient("CM900000000030", 20, 35.0);
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
        if (receivable) { b.initialStorageFee(java.math.BigDecimal.valueOf(initFee > 0 ? initFee : 50000)); b.monthlyStorageFee(java.math.BigDecimal.valueOf(monthlyFee > 0 ? monthlyFee : 50000)); }
        java.util.List<LandEntryRequest.OwnerRequest> os = new java.util.ArrayList<>();
        for (String[] o : owners) os.add(LandEntryRequest.OwnerRequest.builder().fullName(o[0]).nationalId(o[1]).phone(o[2]).build());
        b.owners(os);
        java.util.List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> ss = new java.util.ArrayList<>();
        for (String s : done) { String t = idByName.get(s); ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder().stageTemplateId(t).stageName(s).isCustom(t == null).isCompleted(true).build()); }
        if (open != null) for (String s : open) { String t = idByName.get(s); ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder().stageTemplateId(t).stageName(s).isCustom(t == null).isCompleted(false).build()); }
        b.selectedStages(ss);
        if (note != null) b.notes(java.util.List.of(LandEntryRequest.NoteRequest.builder().content(note).build()));
        LandProject saved = landService.atomicIntake(b.build(), null);
        if ("RELEASE".equals(release)) { try { landService.authorizeRelease(saved.getId(), "Scenario release"); } catch (Exception e) {} }
        return saved.getId();
    }
    // ---------- schema migrations (unchanged) ----------
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
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL"
        };
        try (Connection conn = dataSource.getConnection(); Statement stmt = conn.createStatement()) {
            for (String sql : migrations) { try { stmt.execute(sql); } catch (Exception e) { System.out.println(">>> [DB_SCHEMA] Skipped: " + e.getMessage()); } }
        } catch (Exception e) { System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage()); }
    }
    public void seedRootUser() {
        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";
        String encodedPassword = passwordEncoder.encode(rawPassword);
        try (Connection conn = dataSource.getConnection()) {
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM users WHERE username = ?")) { ps.setString(1, "admin_root"); try (java.sql.ResultSet rs = ps.executeQuery()) { if (rs.next()) exists = rs.getInt(1) > 0; } }
            if (!exists) {
                try (java.sql.PreparedStatement ps = conn.prepareStatement("INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)")) { ps.setObject(1, java.util.UUID.randomUUID()); ps.setString(2, email); ps.setString(3, encodedPassword); ps.executeUpdate(); }
            }
        } catch (Exception e) { System.err.println(">>> [REGISTRY] seed fault:"); e.printStackTrace(); }
    }
}
