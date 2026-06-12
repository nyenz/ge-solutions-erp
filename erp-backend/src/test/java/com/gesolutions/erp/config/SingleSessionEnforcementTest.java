package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
    "SPRING_DATASOURCE_URL=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "SPRING_DATASOURCE_USERNAME=sa",
    "SPRING_DATASOURCE_PASSWORD=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "JWT_SECRET=YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    "CLOUDINARY_CLOUD_NAME=test",
    "CLOUDINARY_API_KEY=test",
    "CLOUDINARY_API_SECRET=test",
    "ADMIN_EMAIL=test@gesolutions.com",
    "ADMIN_DEFAULT_PASSWORD=TestPassword123",
    "MAIL_USERNAME=test@gmail.com",
    "MAIL_PASSWORD=testpassword"
})
@AutoConfigureMockMvc
public class SingleSessionEnforcementTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private static final String TEST_USERNAME = "session_test_user_" + UUID.randomUUID().toString().substring(0, 8);

    private User savedUser;

    @BeforeEach
    public void setUp() {
        userRepository.findByUsername(TEST_USERNAME).ifPresent(userRepository::delete);

        User user = User.builder()
                .id(UUID.randomUUID())
                .username(TEST_USERNAME)
                .email(TEST_USERNAME + "@test.com")
                .password(passwordEncoder.encode("TestPassword1"))
                .role(Role.ROLE_MANAGER)
                .isRoot(false)
                .isActive(true)
                .mustChangePassword(false)
                .sessionVersion(1)
                .build();

        savedUser = userRepository.save(user);
    }

    @AfterEach
    public void tearDown() {
        userRepository.findByUsername(TEST_USERNAME).ifPresent(userRepository::delete);
    }

    @Test
    public void testOldSessionRejectedWith401() throws Exception {
        // Build a UserDetails-compatible principal for token generation
        org.springframework.security.core.userdetails.UserDetails userDetails =
            org.springframework.security.core.userdetails.User.builder()
                .username(savedUser.getUsername())
                .password(savedUser.getPassword())
                .roles("MANAGER")
                .build();

        // Generate a JWT with sessionVersion = 1
        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", 1);
        String tokenWithV1 = jwtService.generateToken(claims, userDetails);

        // Step 1: Request with version-1 token should succeed (DB also has version 1)
        mockMvc.perform(get("/api/v1/profile/me")
                .header("Authorization", "Bearer " + tokenWithV1))
                .andExpect(status().isOk());

        // Step 2: Simulate a concurrent login from another device by incrementing sessionVersion in DB
        savedUser.setSessionVersion(2);
        userRepository.save(savedUser);

        // Step 3: The original token (still claiming version 1) must now be rejected with 401
        mockMvc.perform(get("/api/v1/profile/me")
                .header("Authorization", "Bearer " + tokenWithV1))
                .andExpect(status().isForbidden());
    }
}
