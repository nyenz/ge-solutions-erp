// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import java.util.UUID;

/**
 * NYENZ ERP - MASTER BOOTSTRAPPER (V8 - LEAN PRODUCTION)
 * 
 * Physically ensures only the ROOT FOUNDER account exists.
 * Extra staff accounts have been purged to keep the registry clean.
 */
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    @SuppressWarnings("null")
    public void run(String... args) {
        System.out.println(">>> NYENZ SYSTEM: Verifying Master Identity Registry...");

        // ROOT USER: The only account that will exist by default.
        if (userRepository.findByUsername("admin_root").isEmpty()) {
            User root = User.builder()
                    .id(UUID.randomUUID())
                    .username("admin_root")
                    .email("nyenzdav@gmail.com") // Master Recovery Email
                    .password(passwordEncoder.encode("Manager@123"))
                    .role(Role.ROLE_ADMIN)
                    .isRoot(true)
                    .isActive(true)
                    .mustChangePassword(true) // Forces you to secure the account on first login
                    .build();
            userRepository.save(root);
            System.out.println(">>> [REGISTRY] Master Founder Account Seeded.");
        }

        System.out.println(">>> NYENZ SYSTEM: Identity Protocol Active. Registry Locked.");
    }
}