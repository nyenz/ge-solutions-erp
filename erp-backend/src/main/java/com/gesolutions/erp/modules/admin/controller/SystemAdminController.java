// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java
package com.gesolutions.erp.modules.admin.controller;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.config.DataInitializer;
import com.gesolutions.erp.modules.land.service.FileStorageService;
import com.gesolutions.erp.modules.land.service.StatusTemplateService;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.security.crypto.password.PasswordEncoder;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

/**
 * GOLDEN SEED ERP - SYSTEM RESET (the Danger Zone, Admin only).
 *
 * fix181 (14.4, 15.5), owner decision 14.4a = B (the default): the wipe deletes the BUSINESS data (projects, clients,
 * payments, expenses, documents and files, notes, notifications, custom status lists, expense presets) and KEEPS:
 *  - every staff account (users), so nobody is locked out and nobody has to be provisioned again;
 *  - the audit trail (audit_logs) -- the wipe itself is written there, before and after, with the counts;
 *  - the settings tables listed in KEPT_ON_PURPOSE.
 * The table list is checked against the database at run time: a table that does not exist (an old one, or a brand-new
 * database) is skipped instead of failing the whole wipe. WipeTableListTest fails when an entity table is in neither list.
 *
 * fix198: FRESH START (David, before the manual test rounds). The same wipe with "freshStart": true in the body ALSO
 *  - empties the audit trail (it then holds ONE line: who did the fresh start, when, and how many lines were cleared);
 *  - removes the demo staff accounts (username "demo. ..."); real staff accounts are still kept;
 *  - writes the app_flags row NO_DEMO_DATA, so the demo dataset never comes back (not after this wipe, not after a
 *    restart), whatever GE_SOLUTIONS_SEED_DEMO_DATA says. To get the demo data back, delete that row.
 * A wipe WITHOUT freshStart is unchanged: the audit trail is never touched. This option is for the time BEFORE real
 * data goes in; take the tick box off the Danger Zone at go-live (see the guide, DATA WIPE).
 */
@RestController
@RequestMapping("/api/v1/admin/system")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ROLE_ADMIN') and authentication.principal.isRoot")
public class SystemAdminController {

    private static final String CONFIRM_PHRASE = "WIPE-EVERYTHING";

    /** Business tables. TRUNCATE ... CASCADE resolves foreign-key order, so order does not matter. */
    public static final List<String> TABLES_TO_WIPE = List.of(
        "notification_reads",
        "notifications",
        "recovery_notes",
        "payment_records",
        "payment_schedules",      // old versions only; skipped when missing
        "follow_up_logs",
        "project_documents",
        "project_statuses",
        "project_proprietors",
        "project_clients",
        "project_neighbors",
        "land_titles",
        "land_projects",
        "clients",
        "company_expenses",       // old versions only; skipped when missing
        "expenses",
        "expense_presets",
        "status_templates",
        "scenario_seed_flag"
    );

    /** Tables the wipe never empties (see the class note). project_index_counter is reset to 000/A separately. */
    public static final List<String> KEPT_ON_PURPOSE = List.of(
        "users",
        "audit_logs",
        "app_flags",
        "project_index_counter",
        "document_categories"     // document types are settings, like the Appearance choices; kept
    );

    private final DataSource dataSource;
    private final DataInitializer dataInitializer;
    private final StatusTemplateService statusTemplateService;
    private final FileStorageService fileStorageService;
    private final AuditService auditService;
    private final NotificationService notificationService;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @PostMapping("/wipe-all-data")
    public ResponseEntity<Map<String, Object>> wipeAllData(@RequestParam(required = false) String confirm,
                                                           @RequestBody(required = false) Map<String, Object> body) {
        if (!CONFIRM_PHRASE.equals(confirm)) {
            auditService.logAction("WIPE_REFUSED", "Data wipe refused: the confirmation phrase was missing or wrong.");
            return ResponseEntity.badRequest().body(Map.of(
                "wiped", false,
                "message", "WIPE_REFUSED: The confirmation phrase is missing or wrong. Type " + CONFIRM_PHRASE + " exactly."
            ));
        }
        // fix181 (14.4f): the Admin's own key is asked again, so an open, unattended screen cannot wipe the system
        String password = body == null || body.get("password") == null ? null : String.valueOf(body.get("password"));
        boolean freshStart = body != null && "true".equalsIgnoreCase(String.valueOf(body.get("freshStart")));
        String me = AuditService.currentOperator();
        boolean keyOk = password != null && !password.isEmpty() && userRepository.findByUsername(me)
                .map(u -> passwordEncoder.matches(password, u.getPassword())).orElse(false);
        if (!keyOk) {
            auditService.logAction("WIPE_REFUSED", "Data wipe refused: the Admin key was missing or wrong.");
            return ResponseEntity.badRequest().body(Map.of(
                "wiped", false,
                "message", "WIPE_REFUSED: Your key is not right. Nothing was deleted."
            ));
        }

        Map<String, Long> before = counts();
        auditService.logAction("DATA_WIPED", "Data wipe STARTED. Existing records: " + before
                + (freshStart ? ". FRESH START: the audit trail and the demo staff accounts go too."
                              : ". Staff accounts and the audit trail are kept."));

        List<String> wiped = new ArrayList<>();
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String t : TABLES_TO_WIPE) if (tableExists(conn, t)) wiped.add(t);
            boolean postgres = conn.getMetaData().getDatabaseProductName().toLowerCase(Locale.ROOT).contains("postgres");
            if (postgres) {
                st.execute("TRUNCATE TABLE " + String.join(", ", wiped) + " RESTART IDENTITY CASCADE");
            } else {
                // H2 (tests): one table at a time with the key checks paused
                st.execute("SET REFERENTIAL_INTEGRITY FALSE");
                try { for (String t : wiped) st.execute("TRUNCATE TABLE " + t); }
                finally { st.execute("SET REFERENTIAL_INTEGRITY TRUE"); }
            }
            st.execute("UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1");
            if (freshStart) {
                // fix198: the demo dataset must not come back, and the demo staff accounts go with it
                st.execute("CREATE TABLE IF NOT EXISTS app_flags (name VARCHAR(60) PRIMARY KEY, set_at TIMESTAMP)");
                st.execute("DELETE FROM app_flags WHERE name = '" + DataInitializer.NO_DEMO_DATA_FLAG + "'");
                st.execute("INSERT INTO app_flags (name, set_at) VALUES ('" + DataInitializer.NO_DEMO_DATA_FLAG + "', CURRENT_TIMESTAMP)");
                st.execute("DELETE FROM users WHERE username LIKE 'demo.%' AND (is_root IS NULL OR is_root = false)");
            }
        } catch (Exception e) {
            System.err.println(">>> [WIPE] FATAL: " + e.getMessage());
            auditService.logAction("DATA_WIPED", "Data wipe FAILED: " + e.getMessage());
            return ResponseEntity.internalServerError().body(Map.of(
                "wiped", false,
                "message", "The wipe failed and nothing was deleted: " + e.getMessage()
            ));
        }

        // fix181 (14.4d): the Admin account must still exist, or nobody can sign in
        try { dataInitializer.seedRootUser(); } catch (Exception e) { System.err.println(">>> [WIPE] root reseed: " + e.getMessage()); }
        if (!rootExists()) {
            auditService.logAction("DATA_WIPED", "Data wipe finished but the Admin account is MISSING.");
            return ResponseEntity.internalServerError().body(Map.of(
                "wiped", true,
                "message", "The data was deleted but the Admin account could not be found. Restart the server (it creates the Admin) before signing in."
            ));
        }

        statusTemplateService.seedDefaultStatusesIfEmpty();
        dataInitializer.seedDefaultExpensePresets();
        // fix181 (14.4c): the demo dataset comes back only when ge.solutions.seed-demo-data is on (called once, not twice)
        try { dataInitializer.seedScenarioDataOnce(); } catch (Exception e) { System.err.println(">>> [WIPE] demo reseed: " + e.getMessage()); }

        Map<String, Object> files = fileStorageService.deleteAllFiles();

        // fix198: FRESH START empties the audit trail LAST, so the one line written below is its first line
        long auditCleared = -1;
        if (freshStart) {
            long had = count("audit_logs");
            try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
                st.execute("TRUNCATE TABLE audit_logs");
                auditCleared = had;
            } catch (Exception e) {
                System.err.println(">>> [WIPE] audit trail not cleared: " + e.getMessage());
            }
        }

        auditService.logAction("DATA_WIPED", "Data wipe FINISHED. Deleted: " + before + ". Files deleted: "
                + files.get("filesDeleted") + ", files not deleted: " + files.get("filesFailed") + "."
                + (!freshStart ? "" : auditCleared >= 0
                    ? " FRESH START: the audit trail was cleared (" + auditCleared + " older lines); this is its first line. Demo data is switched off."
                    : " FRESH START was asked but the audit trail could NOT be cleared."));
        notificationService.emitNow("SYSTEM_WIPE", "All business data was wiped by " + AuditService.currentOperator()
                + " (" + before.get("projects") + " projects, " + before.get("clients") + " clients, " + before.get("payments") + " payments).",
                "SYSTEM", UUID.nameUUIDFromBytes("system-wipe".getBytes(java.nio.charset.StandardCharsets.UTF_8)));

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("wiped", true);
        response.put("tablesWiped", wiped);
        response.put("deleted", before);
        response.put("filesDeleted", files.get("filesDeleted"));
        response.put("filesFailed", files.get("filesFailed"));
        if (files.get("error") != null) response.put("filesError", files.get("error"));
        response.put("kept", KEPT_ON_PURPOSE);
        response.put("freshStart", freshStart);
        response.put("auditCleared", auditCleared >= 0);
        response.put("auditLinesCleared", Math.max(auditCleared, 0));
        response.put("message", freshStart && auditCleared >= 0
                ? "Fresh start done. All business data and the audit trail were deleted. Real staff accounts were kept."
                : "All business data was deleted. Staff accounts and the audit trail were kept.");
        return ResponseEntity.ok(response);
    }

    private Map<String, Long> counts() {
        Map<String, Long> m = new LinkedHashMap<>();
        m.put("projects", count("land_projects"));
        m.put("clients", count("clients"));
        m.put("payments", count("payment_records"));
        m.put("expenses", count("expenses"));
        m.put("documents", count("project_documents"));
        return m;
    }

    private long count(String table) {
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            if (!tableExists(conn, table)) return 0;
            try (ResultSet rs = st.executeQuery("SELECT COUNT(*) FROM " + table)) { return rs.next() ? rs.getLong(1) : 0; }
        } catch (Exception e) { return -1; }
    }

    private boolean rootExists() {
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement();
             ResultSet rs = st.executeQuery("SELECT COUNT(*) FROM users WHERE is_root = true")) {
            return rs.next() && rs.getLong(1) > 0;
        } catch (Exception e) { return false; }
    }

    /** True when the table exists (any letter case; H2 stores names in capitals). */
    static boolean tableExists(Connection conn, String table) throws java.sql.SQLException {
        var md = conn.getMetaData();
        for (String name : new String[]{ table, table.toUpperCase(Locale.ROOT) }) {
            try (ResultSet rs = md.getTables(null, null, name, new String[]{ "TABLE" })) { if (rs.next()) return true; }
        }
        return false;
    }
}
