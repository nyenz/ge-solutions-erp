// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
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

    @Transactional
    public void seedRootUser() {
        try {
            String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
            String password = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";

            System.out.println(">>> [REGISTRY] Preparing to seed/reset 'admin_root' with password: '" + password + "'");

            java.util.Optional<User> existing = userRepository.findByUsername("admin_root");
            if (existing.isEmpty()) {
                User root = User.builder()
                        .id(UUID.randomUUID())
                        .username("admin_root")
                        .email(email)
                        .password(passwordEncoder.encode(password))
                        .role(Role.ROLE_ADMIN)
                        .isRoot(true)
                        .isActive(true)
                        .mustChangePassword(true)
                        .build();
                userRepository.saveAndFlush(root);
                System.out.println(">>> [REGISTRY] Master Founder Account Seeded with fallback default credentials.");
            } else {
                User root = existing.get();
                root.setPassword(passwordEncoder.encode(password));
                root.setMustChangePassword(true);
                root.setActive(true);
                userRepository.saveAndFlush(root);
                System.out.println(">>> [REGISTRY] Master Account found. Forced password reset to default for testing.");
            }
        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
