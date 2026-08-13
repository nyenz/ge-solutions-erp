// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;

    @Value("${ADMIN_EMAIL}")
    private String adminEmail;

    @Value("${ADMIN_DEFAULT_PASSWORD}")
    private String adminDefaultPassword;

    @Override
    public void run(String... args) {
        System.out.println(">>> NYENZ SYSTEM: Verifying Master Identity Registry...");

        // Run schema migrations via raw JDBC -- never touches JPA/Hibernate session
        runSchemaMigrations();

        // Seed root user if missing
        seedRootUser();

        // PHASE 4: Seed the default stage template checklist if empty
        stageTemplateService.seedDefaultStagesIfEmpty();

        System.out.println(">>> NYENZ SYSTEM: Identity Protocol Active. Registry Locked.");
    }

    private void runSchemaMigrations() {
        String[] migrations = {
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS negotiation_deadline TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS survey_date DATE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",

            // PHASE 1 - PROJECT INDEX SYSTEM
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index)",

            // PHASE 1.5 - DATE TRACKING SYSTEM
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",

            // PHASE 2 - NIN-BASED IDENTITY
            // Unique constraint on national_id. Postgres allows multiple NULLs under
            // a UNIQUE constraint, so old clients with no NIN yet are not affected.
            "ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id)",
            // Phone numbers are no longer required to be unique -- joint owners or
            // family members can share one phone. NIN is now the real identity check.
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",
        };

        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {

            for (String sql : migrations) {
                try {
                    stmt.execute(sql);
                    System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length())));
                } catch (Exception e) {
                    // Column already exists or similar -- safe to ignore
                    System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage());
                }
            }

        } catch (Exception e) {
            // If we can't get a connection, log and continue -- don't kill startup
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());
        }
    }

    // NOTE: Deliberately NOT @Transactional -- we use raw JDBC so this is
    // completely immune to Spring AOP proxy bypass, Hibernate L1 cache,
    // EntityManager flush timing, and @Builder.Default field conflicts.
    public void seedRootUser() {
        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";
        String encodedPassword = passwordEncoder.encode(rawPassword);

        System.out.println(">>> [REGISTRY] seedRootUser() via raw JDBC. Raw password=" + rawPassword.substring(0,3) + "***");

        try (java.sql.Connection conn = dataSource.getConnection()) {
            // Check if admin_root exists
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) exists = rs.getInt(1) > 0;
                }
            }

            if (!exists) {
                // INSERT brand-new admin_root row
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) "
                           + "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }
            } else {
                // UPDATE existing row -- raw JDBC, auto-commits, no cache issues
                String sql = "UPDATE users SET password = ?, is_active = true, must_change_password = true "
                           + "WHERE username = 'admin_root'";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setString(1, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] UPDATE admin_root rows affected: " + rows);
                }
            }

            // Verify by re-reading the stored hash
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT password, is_active FROM users WHERE username = 'admin_root'")) {
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) {
                        String storedHash = rs.getString("password");
                        boolean active = rs.getBoolean("is_active");
                        boolean matches = passwordEncoder.matches(rawPassword, storedHash);
                        System.out.println(">>> [REGISTRY] Post-write verification:");
                        System.out.println(">>>   is_active in DB = " + active);
                        System.out.println(">>>   hash starts with = " + storedHash.substring(0, Math.min(20, storedHash.length())));
                        System.out.println(">>>   BCrypt.matches(rawPassword, storedHash) = " + matches);
                        if (!matches) {
                            System.err.println(">>> [REGISTRY] FATAL: BCrypt verify FAILED after write! Check encoder config.");
                        } else {
                            System.out.println(">>> [REGISTRY] SUCCESS: Password verified. Login WILL work.");
                        }
                    } else {
                        System.err.println(">>> [REGISTRY] FATAL: admin_root row not found after write!");
                    }
                }
            }

        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
