package com.gesolutions.erp.config;
import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.service.StatusTemplateService;
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
    private final StatusTemplateService statusTemplateService;
    private final ExpensePresetRepository expensePresetRepository;
    private final ScenarioSeeder scenarioSeeder;
        @Value("${ADMIN_EMAIL}") private String adminEmail;
    @Value("${ADMIN_DEFAULT_PASSWORD}") private String adminDefaultPassword;
    @Override
    public void run(String... args) {
        try {
            System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
            runSchemaMigrations();
            seedRootUser();
            statusTemplateService.seedDefaultStatusesIfEmpty();
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
    // ---------- SCENARIO DATASET v3 (see ScenarioSeeder and ScenarioData) ----------
    // Removes every older seed (v1, v2) and loads the v3 dataset once. The method name
    // stays the same because SystemAdminController calls it after a full wipe.
    public void seedScenarioDataOnce() {
        scenarioSeeder.seedOnce();
    }

    // ---------- schema migrations (unchanged) ----------
    // fix144: the database keeps the role list it was created with (users_role_check), so a role
    // added to the Role enum later (Director, Secretary) is rejected on insert. Rebuilt from the
    // enum on every start so the two can never drift apart again.
    private static String roleCheckSql() {
        StringBuilder sb = new StringBuilder("ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN (");
        boolean first = true;
        for (com.gesolutions.erp.modules.auth.model.Role r : com.gesolutions.erp.modules.auth.model.Role.values()) {
            if (!first) sb.append(", ");
            sb.append('\'').append(r.name()).append('\'');
            first = false;
        }
        return sb.append("))").toString();
    }

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
            "ALTER TABLE notifications DROP COLUMN IF EXISTS is_read",
            // fix180: Title ID is gone; Volume / Folio / Area (ha) are new columns (Hibernate adds them). Old projects get a type,
            // and their owners become their clients (Recovery now follows clients) -- only where a project has no clients yet.
            "DROP INDEX IF EXISTS idx_title_id",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS title_id",
            "UPDATE land_projects SET project_type = CASE WHEN is_legacy THEN 'LEGACY_TITLES' ELSE 'FRESH_SURVEY' END WHERE project_type IS NULL",
            "UPDATE land_projects SET title_details_enabled = FALSE WHERE title_details_enabled IS NULL",
            "INSERT INTO project_clients (project_id, client_id) SELECT pp.project_id, pp.client_id FROM project_proprietors pp WHERE NOT EXISTS (SELECT 1 FROM project_clients pc WHERE pc.project_id = pp.project_id)",
            "ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check",
            roleCheckSql()
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
