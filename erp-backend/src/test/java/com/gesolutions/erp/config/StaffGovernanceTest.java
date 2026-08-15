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

import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "ge.solutions.jwt.secret=YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    "cloudinary.cloud-name=test",
    "cloudinary.api-key=test",
    "cloudinary.api-secret=test",
    "ADMIN_EMAIL=test@gesolutions.com",
    "ADMIN_DEFAULT_PASSWORD=TestPassword123",
    "MAIL_USERNAME=test@gmail.com",
    "MAIL_PASSWORD=testpassword"
})
@AutoConfigureMockMvc
public class StaffGovernanceTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private static final String MANAGER_USERNAME = "gov_test_manager_" + UUID.randomUUID().toString().substring(0, 8);
    private static final String ADMIN_USERNAME = "gov_test_admin_" + UUID.randomUUID().toString().substring(0, 8);

    private User savedManager;
    private User savedAdmin;

    @BeforeEach
    public void setUp() {
        userRepository.findByUsername(MANAGER_USERNAME).ifPresent(userRepository::delete);
        userRepository.findByUsername(ADMIN_USERNAME).ifPresent(userRepository::delete);

        User manager = User.builder()
                .id(UUID.randomUUID())
                .username(MANAGER_USERNAME)
                .email(MANAGER_USERNAME + "@test.com")
                .password(passwordEncoder.encode("TestPassword1"))
                .role(Role.ROLE_MANAGER)
                .isRoot(false)
                .isActive(true)
                .mustChangePassword(false)
                .sessionVersion(1)
                .build();
        savedManager = userRepository.save(manager);

        User admin = User.builder()
                .id(UUID.randomUUID())
                .username(ADMIN_USERNAME)
                .email(ADMIN_USERNAME + "@test.com")
                .password(passwordEncoder.encode("TestPassword1"))
                .role(Role.ROLE_ADMIN)
                .isRoot(false)
                .isActive(true)
                .mustChangePassword(false)
                .sessionVersion(1)
                .build();
        savedAdmin = userRepository.save(admin);
    }

    @AfterEach
    public void tearDown() {
        userRepository.findByUsername(MANAGER_USERNAME).ifPresent(userRepository::delete);
        userRepository.findByUsername(ADMIN_USERNAME).ifPresent(userRepository::delete);
    }

    private String buildToken(User user, String roleName) {
        org.springframework.security.core.userdetails.UserDetails userDetails =
            org.springframework.security.core.userdetails.User.builder()
                .username(user.getUsername())
                .password(user.getPassword())
                .roles(roleName)
                .build();

        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", user.getSessionVersion());
        return jwtService.generateToken(claims, userDetails);
    }

    @Test
    public void testManagerIsBlockedFromAdminEndpoints() throws Exception {
        String managerToken = buildToken(savedManager, "MANAGER");

        mockMvc.perform(get("/api/v1/reports/debt-ledger")
                .header("Authorization", "Bearer " + managerToken))
                .andExpect(status().isForbidden());

        mockMvc.perform(get("/api/v1/admin/audit/stream")
                .header("Authorization", "Bearer " + managerToken))
                .andExpect(status().isForbidden());
    }

    @Test
    public void testAdminIsAllowedOnAdminEndpoints() throws Exception {
        String adminToken = buildToken(savedAdmin, "ADMIN");

        int debtLedgerStatus = mockMvc.perform(get("/api/v1/reports/debt-ledger")
                .header("Authorization", "Bearer " + adminToken))
                .andReturn().getResponse().getStatus();
        assertNotEquals(403, debtLedgerStatus, "Admin should not be forbidden from debt-ledger report");

        int auditStreamStatus = mockMvc.perform(get("/api/v1/admin/audit/stream")
                .header("Authorization", "Bearer " + adminToken))
                .andReturn().getResponse().getStatus();
        assertNotEquals(403, auditStreamStatus, "Admin should not be forbidden from audit stream");
    }
}
