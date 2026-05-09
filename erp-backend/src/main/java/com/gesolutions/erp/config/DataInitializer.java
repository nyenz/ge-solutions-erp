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
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @PersistenceContext
    private EntityManager entityManager;

    @Value("${ADMIN_EMAIL}")
    private String adminEmail;

    @Value("${ADMIN_DEFAULT_PASSWORD}")
    private String adminDefaultPassword;

    @Override
    @Transactional
    public void run(String... args) {
        System.out.println(">>> NYENZ SYSTEM: Verifying Master Identity Registry...");

        // Ensure session_version column exists before any queries run.
        // This handles the case where the column was added after the DB was created.
        try {
            entityManager.createNativeQuery(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL"
            ).executeUpdate();
            System.out.println(">>> [DB_SCHEMA] session_version column verified.");
        } catch (Exception e) {
            System.out.println(">>> [DB_SCHEMA] session_version already exists or skipped: " + e.getMessage());
        }

        // Fix missing columns in land_projects that Hibernate DDL auto=update missed
        String[] landProjectMigrations = {
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
        };
        for (String sql : landProjectMigrations) {
            try {
                entityManager.createNativeQuery(sql).executeUpdate();
                System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, 60));
            } catch (Exception e) {
                System.out.println(">>> [DB_SCHEMA] Skipped: " + e.getMessage());
            }
        }

        if (userRepository.findByUsername("admin_root").isEmpty()) {
            User root = User.builder()
                    .id(UUID.randomUUID())
                    .username("admin_root")
                    .email(adminEmail)
                    .password(passwordEncoder.encode(adminDefaultPassword))
                    .role(Role.ROLE_ADMIN)
                    .isRoot(true)
                    .isActive(true)
                    .mustChangePassword(true)
                    .build();
            userRepository.save(root);
            System.out.println(">>> [REGISTRY] Master Founder Account Seeded.");
        }

        System.out.println(">>> NYENZ SYSTEM: Identity Protocol Active. Registry Locked.");
    }
}