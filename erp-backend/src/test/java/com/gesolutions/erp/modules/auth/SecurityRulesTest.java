package com.gesolutions.erp.modules.auth;

import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.config.ApplicationConfig;
import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;

import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * fix181 (15.7c, 13.14): the sign-in, key and staff rules, end to end through the real filters.
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:securityrulesdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
    "MAIL_PASSWORD=testpassword",
    "spring.datasource.hikari.connection-init-sql=SELECT 1",
    "ge.solutions.seed-demo-data=false"
})
@AutoConfigureMockMvc
public class SecurityRulesTest {

    @Autowired private MockMvc mvc;
    @Autowired private JwtService jwt;
    @Autowired private UserRepository users;
    @Autowired private PasswordEncoder encoder;
    @Autowired private AuditLogRepository audit;

    private static final String KEY = "Golden2026";

    private User user(String name, Role role) {
        return users.save(User.builder().id(UUID.randomUUID()).username(name).email(name + "@t.co").password(encoder.encode(KEY))
                .role(role).isRoot(false).isActive(true).build());
    }

    private String uniq(String p) { return p + UUID.randomUUID().toString().substring(0, 6).toLowerCase(); }

    private String bearer(User u) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", users.findById(u.getId()).orElseThrow().getSessionVersion());
        return "Bearer " + jwt.generateToken(claims, new ApplicationConfig.CustomUserPrincipal(users.findById(u.getId()).orElseThrow()));
    }

    private ResultActions login(String name, String key, String ip, String oldToken) throws Exception {
        var req = post("/api/v1/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"" + name + "\",\"password\":\"" + key + "\"}").with(r -> { r.setRemoteAddr(ip); return r; });
        if (oldToken != null) req.header("Authorization", oldToken);
        return mvc.perform(req);
    }

    private ResultActions changeKey(String token, String oldKey, String newKey) throws Exception {
        return mvc.perform(put("/api/v1/profile/change-password").header("Authorization", token).contentType(MediaType.APPLICATION_JSON)
                .content("{\"oldPassword\":\"" + oldKey + "\",\"newPassword\":\"" + newKey + "\"}"));
    }

    @Test
    public void usernameWithCapitalsOrSpacesStillSignsIn() throws Exception {
        String n = uniq("mary");
        user(n, Role.ROLE_SECRETARY);
        login("  " + n.toUpperCase() + " ", KEY, "10.0.0.1", null).andExpect(status().isOk());
    }

    @Test
    public void loginLinesUseTheRealAndTheTypedName() throws Exception {
        String n = uniq("john");
        User other = user(uniq("old"), Role.ROLE_MANAGER);
        user(n, Role.ROLE_MANAGER);
        login(n, KEY, "10.0.0.2", bearer(other)).andExpect(status().isOk());   // an old person's token rides along
        assertTrue(audit.findAll().stream().anyMatch(a -> "LOGIN_SUCCESS".equals(a.getAction()) && n.equals(a.getPerformedBy())));
        login(n, "wrong-key", "10.0.0.2", null).andExpect(status().is4xxClientError());
        assertTrue(audit.findAll().stream().anyMatch(a -> "LOGIN_FAILED".equals(a.getAction()) && n.equals(a.getPerformedBy())));
    }

    @Test
    public void expiredTemporaryKeyIsRefused() throws Exception {
        String n = uniq("temp");
        User u = user(n, Role.ROLE_EMPLOYEE);
        u.setMustChangePassword(true);
        u.setTempKeyExpiresAt(LocalDateTime.now().minusDays(1));
        users.save(u);
        String body = login(n, KEY, "10.0.0.3", null).andExpect(status().is4xxClientError()).andReturn().getResponse().getContentAsString();
        assertTrue(body.contains("KEY_EXPIRED"), body);
    }

    @Test
    public void suspendedPersonCannotSwitchThemselvesBackOn() throws Exception {
        User u = user(uniq("susp"), Role.ROLE_SECRETARY);
        String token = bearer(u);
        u = users.findById(u.getId()).orElseThrow();
        u.setActive(false);
        users.save(u);
        changeKey(token, KEY, "NewGolden2027").andExpect(r -> assertTrue(r.getResponse().getStatus() >= 400));
        assertFalse(users.findById(u.getId()).orElseThrow().isActive(), "still suspended");
    }

    @Test
    public void profileAndStaffListSendNoSecrets() throws Exception {
        User d = user(uniq("dir"), Role.ROLE_DIRECTOR);
        String me = mvc.perform(get("/api/v1/profile/me").header("Authorization", bearer(d))).andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        String staff = mvc.perform(get("/api/v1/staff/all").header("Authorization", bearer(d))).andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        for (String body : List.of(me, staff)) {
            assertFalse(body.contains("\"password\""), body);
            assertFalse(body.contains("resetToken"), body);
            assertFalse(body.contains("sessionVersion"), body);
        }
    }

    @Test
    public void signOutKillsTheOldToken() throws Exception {
        User u = user(uniq("out"), Role.ROLE_MANAGER);
        String token = bearer(u);
        mvc.perform(get("/api/v1/profile/me").header("Authorization", token)).andExpect(status().isOk());
        mvc.perform(post("/api/v1/auth/logout").header("Authorization", token)).andExpect(r -> assertTrue(r.getResponse().getStatus() < 300));
        mvc.perform(get("/api/v1/profile/me").header("Authorization", token)).andExpect(status().isUnauthorized());
    }

    @Test
    public void directorCannotResetTheAdminsKey() throws Exception {
        User d = user(uniq("boss"), Role.ROLE_DIRECTOR);
        User root = users.findByUsername("admin_root").orElseThrow();
        mvc.perform(post("/api/v1/staff/reset-password").header("Authorization", bearer(d)).contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"" + root.getUsername() + "\"}"))
                .andExpect(r -> assertTrue(r.getResponse().getStatus() >= 400, "refused, got " + r.getResponse().getStatus()));
    }

    @Test
    public void newKeyRules() throws Exception {
        String n = uniq("keyrules");
        User u = user(n, Role.ROLE_MANAGER);
        String token = bearer(u);
        String tooLong = "Aa1" + "\u00e9".repeat(36);    // 75 bytes in UTF-8
        assertTrue(changeKey(token, KEY, tooLong).andReturn().getResponse().getContentAsString().contains("too long"));
        assertTrue(changeKey(token, KEY, "X1" + n + "Z").andReturn().getResponse().getContentAsString().contains("username"));
        assertTrue(changeKey(token, KEY, "NY-ABCDE-12345").andReturn().getResponse().getContentAsString().contains("temporary"));
        for (int i = 0; i < 5; i++) changeKey(token, "wrong-" + i, "Fine2027Key");
        String body = changeKey(token, KEY, "Fine2027Key").andReturn().getResponse().getContentAsString();
        assertTrue(body.contains("TOO_MANY_ATTEMPTS"), "five wrong current keys = wait: " + body);
    }

    @Test
    public void usernameWithSlashOrSpaceIsRefused() throws Exception {
        User d = user(uniq("prov"), Role.ROLE_DIRECTOR);
        for (String bad : List.of("ma/ry", "ma ry")) {
            String body = mvc.perform(post("/api/v1/staff/create").header("Authorization", bearer(d)).contentType(MediaType.APPLICATION_JSON)
                            .content("{\"username\":\"" + bad + "\",\"email\":\"x@y.co\",\"role\":\"ROLE_SECRETARY\"}"))
                    .andExpect(r -> assertTrue(r.getResponse().getStatus() >= 400)).andReturn().getResponse().getContentAsString();
            assertTrue(body.contains("USERNAME_INVALID"), body);
        }
    }
}
