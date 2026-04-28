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
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Value("${ADMIN_EMAIL}")
    private String adminEmail;

    @Value("${ADMIN_DEFAULT_PASSWORD}")
    private String adminDefaultPassword;

    @Override
    @Transactional
    public void run(String... args) {
        System.out.println(">>> NYENZ SYSTEM: Verifying Master Identity Registry...");

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