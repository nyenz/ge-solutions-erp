package com.gesolutions.erp.config;
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
        try {
            System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
            runSchemaMigrations();
            seedRootUser();
            stageTemplateService.seedDefaultStagesIfEmpty();
            seedScenarioDataOnce();
                        seedDefaultExpensePresets();
            System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
        } catch (Exception e) {
            System.err.println(">>> [BOOT] FATAL STARTUP ERROR: " + e.getMessage());
            e.printStackTrace();
        }
    }
    public void seedDefaultExpensePresets() {
        if (expensePresetRepository.count() > 0) return;
        String[] defaults = { "Office", "Fieldwork", "Land Office" };
        for (String name : defaults) expensePresetRepository.save(ExpensePreset.builder().name(name).createdBy("SYSTEM").build());
    }
    // ---------- ONE-TIME DEMO DATASET v2 (remove old seed rows once, seed once, never again) ----------
    public void seedScenarioDataOnce() {
        try (Connection conn = dataSource.getConnection()) {
            try (Statement st = conn.createStatement()) {
                st.execute("CREATE TABLE IF NOT EXISTS scenario_seed_flag (id INTEGER PRIMARY KEY, seeded_at TIMESTAMP NOT NULL DEFAULT now())");
            }
            boolean done;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM scenario_seed_flag WHERE id = 2"); java.sql.ResultSet rs = ps.executeQuery()) { rs.next(); done = rs.getInt(1) > 0; }
            if (done) { System.out.println(">>> [SCENARIO] Dataset v2 already seeded -- skipping."); return; }
            purgeSeedRows(conn);
            seedScenarios();
            try (Statement st = conn.createStatement()) { st.execute("INSERT INTO scenario_seed_flag (id) VALUES (2) ON CONFLICT (id) DO NOTHING"); }
            System.out.println(">>> [SCENARIO] Dataset v2 seeded (22 projects).");
        } catch (Exception e) { System.err.println(">>> [SCENARIO] seed fault: " + e.getMessage()); }
    }
    private java.util.List<Object> idList(Connection conn, String sql, java.sql.Array arg) throws java.sql.SQLException {
        java.util.List<Object> out = new java.util.ArrayList<>();
        try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
            if (arg != null) ps.setArray(1, arg);
            try (java.sql.ResultSet rs = ps.executeQuery()) { while (rs.next()) out.add(rs.getObject(1)); }
        }
        return out;
    }
    private void purgeBy(Connection conn, String sql, java.sql.Array arg) {
        try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) { ps.setArray(1, arg); ps.executeUpdate(); }
        catch (Exception e) { System.err.println(">>> [SCENARIO] purge skip: " + e.getMessage()); }
    }
    // Deletes only rows that belong to seed clients (old CM9000000000xx ids and new CM99xxxxxxLLLL ids).
    private void purgeSeedRows(Connection conn) throws java.sql.SQLException {
        java.util.List<Object> clients = idList(conn, "SELECT id FROM clients WHERE national_id LIKE 'CM9000000000%' OR national_id LIKE 'CM99%'", null);
        if (clients.isEmpty()) return;
        java.sql.Array cArr = conn.createArrayOf("uuid", clients.toArray());
        java.util.List<Object> projects = idList(conn, "SELECT DISTINCT project_id FROM project_proprietors WHERE client_id = ANY(?)", cArr);
        java.sql.Array pArr = conn.createArrayOf("uuid", projects.toArray());
        java.util.List<Object> titles = idList(conn, "SELECT title_id FROM land_projects WHERE title_id IS NOT NULL AND id = ANY(?)", pArr);
        java.sql.Array tArr = conn.createArrayOf("uuid", titles.toArray());
        String[] byProject = { "payment_records", "follow_up_logs", "project_documents", "project_stages", "payment_schedules" };
        for (String t : byProject) purgeBy(conn, "DELETE FROM " + t + " WHERE project_id = ANY(?)", pArr);
        purgeBy(conn, "DELETE FROM recovery_notes WHERE client_id = ANY(?)", cArr);
        purgeBy(conn, "DELETE FROM project_proprietors WHERE client_id = ANY(?)", cArr);
        purgeBy(conn, "DELETE FROM land_projects WHERE id = ANY(?)", pArr);
        purgeBy(conn, "DELETE FROM land_titles WHERE id = ANY(?)", tArr);
        purgeBy(conn, "DELETE FROM clients WHERE id = ANY(?)", cArr);
        try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM land_projects"); java.sql.ResultSet rs = ps.executeQuery()) {
            rs.next();
            if (rs.getInt(1) == 0) { try (Statement st = conn.createStatement()) { st.execute("UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1"); } }
        }
        System.out.println(">>> [SCENARIO] Old seed rows removed.");
    }
    // Deterministic fake identifiers: 14-char national ID (CM99 + 6 digits + 4 letters) and 10-digit 07xx phone.
    private static String nin(int i) {
        String L = "ABCDEFGHJKLMNPRSTUWXYZ";
        return "CM99" + String.format("%06d", 120000 + (i * 3719) % 880000)
                + L.charAt(i % L.length()) + L.charAt((i * 5 + 3) % L.length())
                + L.charAt((i * 7 + 1) % L.length()) + L.charAt((i * 11 + 2) % L.length());
    }
    private static String tel(int i) { return "07" + (i % 2 == 0 ? "01" : "52") + String.format("%06d", 234000 + i * 173); }
    private String d(int daysAgo) { return LocalDate.now().minusDays(daysAgo).toString(); }
    private void flag(UUID pid, String sql) {
        try (Connection conn = dataSource.getConnection(); java.sql.PreparedStatement ps = conn.prepareStatement("UPDATE land_projects SET " + sql + " WHERE id = ?")) { ps.setObject(1, pid); ps.executeUpdate(); } catch (Exception e) { System.err.println(">>> [SCENARIO] flag fault: " + e.getMessage()); }
    }
    private void backdatePayment(UUID pid, int daysAgo, long amount, String type) {
        try (Connection conn = dataSource.getConnection()) {
            java.sql.Timestamp ts = java.sql.Timestamp.valueOf(LocalDateTime.now().minusDays(daysAgo));
            try (java.sql.PreparedStatement ps = conn.prepareStatement("UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) { ps.setTimestamp(1, ts); ps.setObject(2, pid); ps.executeUpdate(); }
            try (java.sql.PreparedStatement ps = conn.prepareStatement("INSERT INTO payment_records (id, project_id, amount_paid, payment_type, recorded_by, notes, timestamp, balance_after) VALUES (?, ?, ?, ?, 'SYSTEM', 'Payment received', ?, 0)")) { ps.setObject(1, UUID.randomUUID()); ps.setObject(2, pid); ps.setBigDecimal(3, java.math.BigDecimal.valueOf(amount)); ps.setString(4, type); ps.setTimestamp(5, ts); ps.executeUpdate(); }
        } catch (Exception e) { System.err.println(">>> [SCENARIO] payment fault: " + e.getMessage()); }
    }
    private void doc(UUID pid, String type, String name) {
        try (Connection conn = dataSource.getConnection(); java.sql.PreparedStatement ps = conn.prepareStatement("INSERT INTO project_documents (id, project_id, file_name, file_type, file_path, internal_notes, uploaded_by, uploaded_at) VALUES (?, ?, ?, ?, ?, 'Uploaded by front desk', 'SYSTEM', now())")) { ps.setObject(1, UUID.randomUUID()); ps.setObject(2, pid); ps.setString(3, name); ps.setString(4, type); ps.setString(5, "https://res.cloudinary.com/dfd115bnz/raw/upload/v1/ge_solutions/demo/" + name); ps.executeUpdate(); } catch (Exception e) { System.err.println(">>> [SCENARIO] doc fault: " + e.getMessage()); }
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
        // INTAKE + IN-PROGRESS
        S.put("s1", seedOne(null, false, false, false, null, null, "KYADONDO BLOCK 244", d(21), 3200000, 1000000, 0, 0, new String[][] { { "KATO HERBERT", nin(1), tel(1) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "WAKISO", "KYADONDO", "NANSANA MUNICIPALITY", "NANSANA EAST", "KYEBANDO", "Residential" }, "Deposit received at intake; field work scheduled", idByName));
        S.put("s2", seedOne(null, false, false, false, null, null, "KYADONDO BLOCK 118", d(55), 4200000, 2100000, 0, 0, new String[][] { { "NABUKENYA ROSE", nin(2), tel(2) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KYADONDO", "MAKINDYE DIVISION", "KANSANGA", "MUYENGA", "Residential" }, null, idByName));
        S.put("s3", seedOne(null, false, false, false, null, null, "MAWOKOTA BLOCK 302", d(85), 3800000, 1900000, 0, 0, new String[][] { { "SSEMWOGERERE ISAAC", nin(3), tel(3) }, { "NAMULI PROSSY", nin(4), tel(4) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "MPIGI", "MAWOKOTA", "MPIGI TOWN COUNCIL", "KAFUMU", "KAYABWE", "Agricultural" }, "Joint owners; both must sign the deed plan", idByName));
        S.put("s4", seedOne("2417", false, true, false, "LRV 3310 FOLIO 14", d(40), "KASHARI BLOCK 96", d(110), 4500000, 3150000, 0, 0, new String[][] { { "BYAMUGISHA INNOCENT", nin(5), tel(5) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "MBARARA", "KASHARI", "MBARARA CITY NORTH DIVISION", "KAKOBA", "NYAMITANGA", "Residential" }, null, idByName));
        // FULLY PAID + RELEASED
        S.put("s5", seedOne("781", false, true, false, "LRV 4102 FOLIO 3", d(35), "ASWA BLOCK 57", d(125), 4800000, 4800000, 0, 0, new String[][] { { "ACHIENG BEATRICE", nin(6), tel(6) } }, ALL, null, null, new String[] { "GULU", "ASWA", "LAYIBI DIVISION", "PECE", "LACOR", "Residential" }, "Fully paid; awaiting release to client", idByName));
        S.put("s6", seedOne("1204", false, true, false, "LRV 4188 FOLIO 21", d(30), "BUDIOPE BLOCK 88", d(140), 5200000, 5200000, 0, 0, new String[][] { { "TUMUSIIME JOSEPH", nin(7), tel(7) } }, ALL, null, "RELEASE", new String[] { "JINJA", "BUDIOPE", "JINJA CITY SOUTH DIVISION", "WALUKUBA", "MPUMUDDE", "Commercial" }, "Title released to client", idByName));
        // LEGACY
        S.put("s7", seedOne("355", true, true, false, "LRV 1120 FOLIO 7", "1985-06-15", "BUDDU BLOCK 61", d(400), 3500000, 1750000, 0, 0, new String[][] { { "LUBEGA MOSES", nin(8), tel(8) } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "MASAKA", "BUDDU", "MASAKA CITY", "KIMAANYA", "KYESIGA", "Residential" }, "Legacy file; client silent for over a year", idByName));
        S.put("s8", seedOne("412", true, true, false, "LRV 1584 FOLIO 22", "1990-03-20", "BUNGOKHO BLOCK 12", d(300), 4000000, 800000, 0, 0, new String[][] { { "NALUBEGA AGNES", nin(9), tel(9) }, { "KIIZA EMMANUEL", nin(10), tel(10) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "MBALE", "BUNGOKHO", "MBALE CITY", "NAMAKWEKWE", "WANALE", "Industrial" }, "Legacy joint file", idByName));
        // RECEIVABLE FAMILY
        S.put("s9", seedOne("1533", false, true, true, "LRV 3890 FOLIO 5", d(350), "AYIVU BLOCK 33", d(360), 4500000, 900000, 50000, 50000, new String[][] { { "APIO DOREEN", nin(11), tel(11) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "ARUA", "AYIVU", "ARUA CITY", "RIVER OLI", "ANYAFIO", "Residential" }, "Receivable; client silent since last payment", idByName));
        S.put("s10", seedOne("902", false, true, true, "LRV 3902 FOLIO 9", d(320), "PADYERE BLOCK 14", d(330), 5000000, 750000, 50000, 50000, new String[][] { { "MUGENYI STEPHEN", nin(12), tel(12) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "NEBBI", "PADYERE", "NEBBI TOWN COUNCIL", "PAIDHA", "PANYIMUR", "Agricultural" }, "Receivable; client paying in instalments", idByName));
        S.put("s11", seedOne("648", false, true, true, "LRV 3915 FOLIO 2", d(300), "SOROTI BLOCK 21", d(310), 3800000, 380000, 50000, 50000, new String[][] { { "NAKAMYA HARRIET", nin(13), tel(13) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "SOROTI", "SOROTI", "SOROTI CITY EAST DIVISION", "GWERI", "ARAPAI", "Agricultural" }, "Receivable; storage frozen during negotiation", idByName));
        S.put("s12", seedOne("2210", false, true, true, "LRV 3941 FOLIO 18", d(290), "TORORO BLOCK 45", d(300), 4200000, 420000, 50000, 50000, new String[][] { { "OPOLOT VINCENT", nin(14), tel(14) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "TORORO", "TORORO", "TORORO MUNICIPALITY", "MOLO", "KADAMA", "Residential" }, "Receivable; negotiation deadline passed", idByName));
        S.put("s13", seedOne("1875", false, true, false, "LRV 4021 FOLIO 11", d(95), "BUGAHYA BLOCK 72", d(115), 4700000, 2350000, 0, 0, new String[][] { { "BWIRE ALFRED", nin(15), tel(15) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "HOIMA", "BUGAHYA", "HOIMA CITY EAST DIVISION", "KIGOROBYA", "BUJUMBURA", "Residential" }, "Boundary dispute with neighbour; flagged as problem", idByName));
        S.put("s14", seedOne("3306", false, true, true, "LRV 3960 FOLIO 27", d(280), "AYIVU BLOCK 34", d(290), 6000000, 3000000, 75000, 75000, new String[][] { { "NANTONGO JULIET", nin(16), tel(16) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "ARUA", "AYIVU", "ARUA CITY", "RIVER OLI", "ANYAFIO", "Commercial" }, "Custom storage rate agreed at 75,000", idByName));
        // RECOVERY COVERAGE
        S.put("s15", seedOne("1421", false, true, false, "LRV 4050 FOLIO 6", d(85), "IGARA BLOCK 19", d(120), 4300000, 2150000, 0, 0, new String[][] { { "AHIMBISIBWE GILBERT", nin(17), tel(17) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "BUSHENYI", "IGARA", "BUSHENYI-ISHAKA MUNICIPALITY", "NYAKABIRIZI", "KATUNGURU", "Residential" }, null, idByName));
        S.put("s16", seedOne("3122", false, true, false, "LRV 4066 FOLIO 13", d(90), "KOOKI BLOCK 27", d(130), 4600000, 2300000, 0, 0, new String[][] { { "OJOK DENIS", nin(18), tel(18) } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "RAKAI", "KOOKI", "RAKAI TOWN COUNCIL", "KALISIZO", "KYOTERA", "Agricultural" }, null, idByName));
        S.put("s17", seedOne("540", false, true, false, "LRV 4071 FOLIO 1", d(88), "BURAHYA BLOCK 8", d(140), 5800000, 2900000, 0, 0, new String[][] { { "NAMATOVU ESTHER", nin(19), tel(19) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KABAROLE", "BURAHYA", "FORT PORTAL CITY EAST DIVISION", "KARAMBI", "KISIMBA", "Residential" }, null, idByName));
        S.put("s18", seedOne("2718", false, true, false, "LRV 4085 FOLIO 19", d(80), "SHEEMA BLOCK 41", d(150), 5200000, 2600000, 0, 0, new String[][] { { "MUGISHA ANDREW", nin(20), tel(20) } }, new String[] { FW, DP, LCI }, new String[] { DLB, TASD, REG }, null, new String[] { "SHEEMA", "SHEEMA", "SHEEMA MUNICIPALITY", "KITAGATA", "KAZINGA", "Mixed Use" }, null, idByName));
        S.put("s19", seedOne("963", false, true, false, "LRV 4090 FOLIO 24", d(75), "KATIKAMU BLOCK 62", d(160), 4800000, 2400000, 0, 0, new String[][] { { "NANKYA SYLVIA", nin(21), tel(21) } }, new String[] { FW, DP, LCI, DLB }, new String[] { TASD, REG }, null, new String[] { "LUWEERO", "KATIKAMU", "LUWEERO TOWN COUNCIL", "BAMUNANIKA", "WOBULENZI", "Residential" }, null, idByName));
        S.put("s20", seedOne("1187", false, true, false, "LRV 4210 FOLIO 30", d(70), "KYADONDO BLOCK 205", d(170), 4100000, 2050000, 0, 0, new String[][] { { "KAWEESI TIMOTHY", nin(22), tel(22) } }, new String[] { FW, DP }, new String[] { LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KYADONDO", "MAKINDYE DIVISION", "KIBULI", "KIBULI", "Residential" }, null, idByName));
        // INTAKE TODAY + DOCUMENTS
        S.put("s21", seedOne(null, false, false, false, null, null, "KYADONDO BLOCK 260", d(0), 3600000, 900000, 0, 0, new String[][] { { "KIGGUNDU SAMUEL", nin(23), tel(23) } }, new String[] { FW }, new String[] { DP, LCI, DLB, TASD, REG }, null, new String[] { "KAMPALA", "KYADONDO", "KAWEMPE DIVISION", "MAKERERE III", "KIKONI", "Mixed Use" }, "Walk-in intake today", idByName));
        S.put("s22", seedOne("1954", false, true, false, "LRV 4233 FOLIO 12", d(45), "KYADONDO BLOCK 190", d(200), 5100000, 3570000, 0, 0, new String[][] { { "NAKIMULI JOAN", nin(24), tel(24) } }, new String[] { FW, DP, LCI, DLB, TASD }, new String[] { REG }, null, new String[] { "KAMPALA", "KYADONDO", "NAKAWA DIVISION", "BUGOLOBI", "BUGOLOBI", "Residential" }, "Only registration remaining; documents on file", idByName));
        // payments + badges
        backdatePayment(S.get("s2"), 5, 1000000, "STANDARD");
        backdatePayment(S.get("s3"), 60, 380000, "STANDARD");
        backdatePayment(S.get("s4"), 20, 900000, "STANDARD");
        backdatePayment(S.get("s7"), 400, 500000, "STANDARD");
        backdatePayment(S.get("s9"), 300, 400000, "STANDARD");
        backdatePayment(S.get("s10"), 5, 500000, "RECEIVABLE_PARTIAL");
        // folder flags
        flag(S.get("s11"), "storage_paused = true, negotiation_deadline = now() + interval '30 days'");
        flag(S.get("s12"), "negotiation_deadline = now() - interval '5 days'");
        flag(S.get("s13"), "is_problem = true");
        flag(S.get("s14"), "storage_fee_override = 75000");
        // documents
        doc(S.get("s22"), "DEED_PLAN", "deed-plan-nakimuli-joan.pdf");
        doc(S.get("s22"), "NIN_SCAN", "nin-scan-nakimuli-joan.jpg");
        // folder notes
        fup(S.get("s1"), "Client visited the office and asked about the stage timeline", 2);
        fup(S.get("s9"), "Called about storage fees and requested a statement", 12);
        fup(S.get("s3"), "Co-owner NAMULI PROSSY asked to be contacted separately", 1);
        // recovery histories
        note(nin(17), "answered call", "POSITIVE", true, 3, "Will pay after the coffee harvest", null);
        touchClient(nin(17), 3, 80.0);
        note(nin(18), "answered call", "POSITIVE", true, 1, "Confirmed he received the balance statement", null);
        note(nin(18), "committed to pay", "POSITIVE", true, 0, "Promised to pay on Friday", null);
        touchClient(nin(18), 0, 85.0);
        note(nin(19), "answered call", "POSITIVE", true, 20, null, null);
        note(nin(19), "failed to pay", "NEGATIVE", false, 18, "Did not honour the promise made on the call", null);
        touchClient(nin(19), 20, 60.0);
        note(nin(20), "committed to pay", "POSITIVE", true, 10, "Promise date has passed", -1);
        touchClient(nin(20), 10, 70.0);
        note(nin(21), "committed to pay", "POSITIVE", true, 5, "Will pay once salary comes in", 7);
        touchClient(nin(21), 5, 75.0);
        note(nin(22), "not picking up", "NEGATIVE", true, 20, null, null);
        note(nin(22), "phone off", "NEGATIVE", true, 16, null, null);
        touchClient(nin(22), 16, 55.0);
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
        if ("RELEASE".equals(release)) { try { landService.authorizeRelease(saved.getId(), "Released to client after full payment"); } catch (Exception e) {} }
        return saved.getId();
    }
    // ---------- schema migrations (unchanged) ----------
    private void runSchemaMigrations() throws Exception {
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
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
            "ALTER TABLE notifications DROP COLUMN IF EXISTS is_read"
        };
        Connection conn = null;
        Statement stmt = null;
        try {
            conn = dataSource.getConnection();
            stmt = conn.createStatement();
            for (String sql : migrations) { 
                try { 
                    stmt.execute(sql); 
                } catch (Exception e) { 
                    System.out.println(">>> [DB_SCHEMA] Skipped: " + e.getMessage()); 
                } 
            }
        } catch (Throwable t) { 
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + t.getMessage()); 
        } finally {
            if (stmt != null) try { stmt.close(); } catch (Exception ignored) {}
            if (conn != null) try { conn.close(); } catch (Exception ignored) {}
        }
    }
    public void seedRootUser() throws Exception {
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
