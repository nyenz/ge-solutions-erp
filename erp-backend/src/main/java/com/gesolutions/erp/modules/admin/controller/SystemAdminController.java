// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java
package com.gesolutions.erp.modules.admin.controller;

import com.gesolutions.erp.config.DataInitializer;
import com.gesolutions.erp.modules.land.service.FileStorageService;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * GOLDEN SEED ERP - SYSTEM RESET CONTROLLER
 *
 * Physically wipes every business record in the database and restores the
 * app to a fresh, empty state. SECURITY PROTOCOL: Root Founder only -- this
 * is the single most destructive endpoint in the system.
 *
 * After the wipe, the root admin account, the project index counter, and
 * the default stage-template checklist are automatically reseeded so the
 * app is immediately usable again (nobody gets permanently locked out).
 *
 * Also purges every file this app has ever uploaded to Cloudinary (all
 * project documents, all resource types), so nothing is left behind in
 * storage either.
 */
@RestController
@RequestMapping("/api/v1/admin/system")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ROLE_ADMIN') and authentication.principal.isRoot")
public class SystemAdminController {

    private static final String CONFIRM_PHRASE = "WIPE-EVERYTHING";

    // Every table that holds real business/user data. TRUNCATE ... CASCADE
    // resolves foreign-key order automatically, so list order doesn't matter.
    private static final String[] TABLES_TO_WIPE = {
        "audit_logs",
        "notifications",
        "payment_records",
        "payment_schedules",
        "follow_up_logs",
        "project_documents",
        "project_stages",
        "land_titles",
        "land_projects",
        "clients",
        "company_expenses",
        "expenses",
        "expense_presets",
        "stage_templates",
        "users"
    };

    private final DataSource dataSource;
    private final DataInitializer dataInitializer;
    private final StageTemplateService stageTemplateService;
    private final FileStorageService fileStorageService;

    /**
     * THE BIG RED BUTTON.
     * Wipes every table above, then immediately reseeds the root admin
     * account, the project index counter, and the default stage template
     * so the system is left clean, working, and empty.
     *
     * Requires ?confirm=WIPE-EVERYTHING exactly, so this can never fire by
     * accident (typo, stray request, browser prefetch, etc).
     */
    @PostMapping("/wipe-all-data")
    public ResponseEntity<Map<String, Object>> wipeAllData(@RequestParam(required = false) String confirm) {
        if (!CONFIRM_PHRASE.equals(confirm)) {
            return ResponseEntity.badRequest().body(Map.of(
                "wiped", false,
                "message", "Confirmation phrase missing or incorrect. Send confirm=" + CONFIRM_PHRASE + " to proceed."
            ));
        }

        System.out.println(">>> [WIPE] ================================================");
        System.out.println(">>> [WIPE] FULL SYSTEM DATA WIPE TRIGGERED BY ROOT FOUNDER.");
        System.out.println(">>> [WIPE] ================================================");

        String tableList = String.join(", ", TABLES_TO_WIPE);
        Connection conn = null;
        Statement stmt = null;
        try {
            conn = dataSource.getConnection();
            stmt = conn.createStatement();
            stmt.execute("TRUNCATE TABLE " + tableList + " RESTART IDENTITY CASCADE");
            System.out.println(">>> [WIPE] OK: All business tables truncated -- " + tableList);
        } catch (Exception e) {
            System.err.println(">>> [WIPE] FATAL: Truncate failed: " + e.getMessage());
            return ResponseEntity.internalServerError().body(Map.of(
                "wiped", false,
                "message", "Wipe failed: " + e.getMessage()
            ));
        } finally {
            if (stmt != null) try { stmt.close(); } catch (Exception ignored) {}
            if (conn != null) try { conn.close(); } catch (Exception ignored) {}
        }

        // Reset the project index counter back to 000/A
        Connection conn2 = null;
        Statement stmt2 = null;
        try {
            conn2 = dataSource.getConnection();
            stmt2 = conn2.createStatement();
            stmt2.execute("UPDATE project_index_counter SET current_number = 0, current_letter = 'A' WHERE id = 1");
            System.out.println(">>> [WIPE] OK: project_index_counter reset to 000/A");
        } catch (Exception e) {
            System.err.println(">>> [WIPE] WARNING: Could not reset project_index_counter: " + e.getMessage());
        } finally {
            if (stmt2 != null) try { stmt2.close(); } catch (Exception ignored) {}
            if (conn2 != null) try { conn2.close(); } catch (Exception ignored) {}
        }

        // Reseed the root admin account so nobody gets locked out
        try {
            dataInitializer.seedRootUser();
            System.out.println(">>> [WIPE] OK: admin_root reseeded");
        } catch (Exception e) {
            System.err.println(">>> [WIPE] WARNING: admin_root reseed failed: " + e.getMessage());
        }

        // Reseed the default stage template checklist
        stageTemplateService.seedDefaultStagesIfEmpty();
        System.out.println(">>> [WIPE] OK: default stage template reseeded");

        // Reseed the default expense presets (Office, Fieldwork, Land Office)
        dataInitializer.seedDefaultExpensePresets();
        System.out.println(">>> [WIPE] OK: default expense presets reseeded");

        // Purge every uploaded file from Cloudinary storage too
        fileStorageService.deleteAllFiles();
        System.out.println(">>> [WIPE] OK: Cloudinary storage purge attempted");

        System.out.println(">>> [WIPE] SYSTEM RESET COMPLETE. Fresh start.");

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("wiped", true);
        response.put("tablesWiped", TABLES_TO_WIPE);
        response.put("message", "All business data AND all uploaded files on Cloudinary have been deleted. Root admin login, project index, and default stage template were reseeded to defaults. You will need to log in again with the ADMIN_EMAIL / ADMIN_DEFAULT_PASSWORD credentials.");
        return ResponseEntity.ok(response);
    }
}
