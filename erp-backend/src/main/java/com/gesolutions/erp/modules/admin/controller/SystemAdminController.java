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
import org.springframework.web.bind.annotation.RequestParam;
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

    @PostMapping("/wipe-all-data")
    public ResponseEntity<Map<String, Object>> wipeAllData(@RequestParam(required = false) String confirm) {
        if (!CONFIRM_PHRASE.equals(confirm)) {
            auditService.logAction("WIPE_REFUSED", "Data wipe refused: the confirmation phrase was missing or wrong.");
            return ResponseEntity.badRequest().body(Map.of(
                "wiped", false,
                "message", "The confirmation phrase is missing or wrong. Type " + CONFIRM_PHRASE + " exactly."
            ));
        }

        Map<String, Long> before = counts();
        auditService.logAction("DATA_WIPED", "Data wipe STARTED. Existing records: " + before
                + ". Staff accounts and the audit trail are kept.");

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

        auditService.logAction("DATA_WIPED", "Data wipe FINISHED. Deleted: " + before + ". Files deleted: "
                + files.get("filesDeleted") + ", files not deleted: " + files.get("filesFailed") + ".");
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
        response.put("message", "All business data was deleted. Staff accounts and the audit trail were kept.");
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
