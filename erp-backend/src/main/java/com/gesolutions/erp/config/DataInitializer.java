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
 * NYENZ ERP - MASTER BOOTSTRAPPER (V7 - PRODUCTION LOCKDOWN)
 * 
 * Physically ensures 3-tier identities exist without overwriting 
 * user-changed passwords on server restarts.
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
        System.out.println(">>> NYENZ SYSTEM: Synchronizing Identity Protocols...");

        // --- TIER 1: THE ROOT FOUNDER ---
        if (userRepository.findByUsername("admin_root").isEmpty()) {
            User newRoot = User.builder()
                    .id(UUID.randomUUID())
                    .username("admin_root")
                    .email("nyenzdav@gmail.com")
                    .password(passwordEncoder.encode("Manager@123"))
                    .role(Role.ROLE_ADMIN)
                    .isRoot(true)
                    .isActive(true)
                    .mustChangePassword(true) // Initial force
                    .build();
            userRepository.save(newRoot);
            System.out.println(">>> [INIT] Created MASTER ROOT account.");
        }

        // --- TIER 2: THE SYSTEM ADMIN ---
        if (userRepository.findByUsername("admin_01").isEmpty()) {
            User newAdmin = User.builder()
                    .id(UUID.randomUUID())
                    .username("admin_01")
                    .email("admin@golden-seed.com")
                    .password(passwordEncoder.encode("Manager@123"))
                    .role(Role.ROLE_ADMIN)
                    .isRoot(false)
                    .isActive(true)
                    .mustChangePassword(true)
                    .build();
            userRepository.save(newAdmin);
            System.out.println(">>> [INIT] Created SYSTEM ADMIN account.");
        }

        // --- TIER 3: THE STANDARD OPERATOR ---
        if (userRepository.findByUsername("operator_01").isEmpty()) {
            User newOp = User.builder()
                    .id(UUID.randomUUID())
                    .username("operator_01")
                    .email("staff@golden-seed.com")
                    .password(passwordEncoder.encode("Manager@123"))
                    .role(Role.ROLE_MANAGER)
                    .isRoot(false)
                    .isActive(true)
                    .mustChangePassword(true)
                    .build();
            userRepository.save(newOp);
            System.out.println(">>> [INIT] Created STANDARD OPERATOR account.");
        }

        System.out.println(">>> NYENZ SYSTEM: Identity Handshake Verified. Registry Locked.");
    }
}