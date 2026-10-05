package com.gesolutions.erp.common.audit;

import com.gesolutions.erp.config.ApplicationConfig;
import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * fix181 (10.3, 10.11, 10.13, 13.0e): the audit search filters one way per combination, the end date is exclusive,
 * % and _ are plain letters, only Admin and Director may read the trail, and the Director gets the operator list.
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:auditsearchdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class AuditSearchTest {

    @Autowired private AuditSearchService search;
    @Autowired private AuditLogRepository repo;
    @Autowired private MockMvc mvc;
    @Autowired private JwtService jwt;
    @Autowired private UserRepository users;

    private static final LocalDateTime DAY = LocalDateTime.of(2030, 1, 15, 0, 0);
    private static boolean seeded = false;

    private void log(String who, String action, String details, LocalDateTime at) {
        repo.save(AuditLog.builder().performedBy(who).action(action).details(details).timestamp(at).build());
    }

    @BeforeEach
    public void seed() {
        if (seeded) return;
        seeded = true;
        log("zz_mary", "RECORD_DELETED", "deleted plot 12", DAY.plusHours(9));
        log("zz_mary", "RECORD_RESTORED", "restored plot 12", DAY.plusHours(10));
        log("zz_john", "PAYMENT_REVERSED", "reversed 100%_off promo", DAY.plusHours(11));
        log("SYSTEM", "STORAGE_FEE_APPLIED", "fee on plot 12", DAY.plusHours(12));
        log("zz_john", "LOGIN_SUCCESS", "signed in", DAY.plusHours(23).plusMinutes(59).plusSeconds(59));
        log("zz_john", "LOGIN_SUCCESS", "signed in next day", DAY.plusDays(1));
    }

    private long count(String op, List<String> actions, LocalDateTime start, LocalDateTime end, String kw, boolean noSystem) {
        return search.search(new AuditSearchService.Filter(op, actions, start, end, kw, noSystem), 0, 200).getTotalElements();
    }

    private final LocalDateTime from = DAY, to = DAY.plusDays(1);   // the whole of 15 January, end exclusive

    @Test public void datesOnlyKeepTheLastSecondAndDropTheNextDay() { assertEquals(5, count(null, null, from, to, null, false)); }
    @Test public void operatorOnly() { assertEquals(2, count("zz_mary", null, null, null, null, false)); }
    @Test public void actionsOnly() { assertEquals(3, count(null, List.of("RECORD_DELETED", "RECORD_RESTORED", "PAYMENT_REVERSED"), null, null, null, false)); }
    @Test public void keywordOnlyTreatsPercentAsALetter() {
        assertEquals(1, count(null, null, null, null, "100%_off", false));
        assertEquals(0, count(null, null, from, to, "1%2", false));
    }
    @Test public void allTogether() { assertEquals(1, count("zz_mary", List.of("RECORD_RESTORED", "LOGIN_SUCCESS"), from, to, "PLOT", false)); }
    @Test public void noneReturnsEverything() { assertTrue(count(null, null, null, null, null, false) >= 6); }
    @Test public void systemCanBeLeftOut() {
        assertEquals(4, count(null, null, from, to, null, true));
    }
    @Test public void newestFirst() {
        var rows = search.search(new AuditSearchService.Filter(null, null, from, to, null, false), 0, 2).getContent();
        assertEquals("LOGIN_SUCCESS", rows.get(0).getAction());
        assertEquals(5, search.search(new AuditSearchService.Filter(null, null, from, to, null, false), 0, 2).getTotalElements());
    }

    private String token(Role role) {
        String n = "aud_" + UUID.randomUUID().toString().substring(0, 8);
        User u = users.save(User.builder().id(UUID.randomUUID()).username(n).email(n + "@t.co").password("x").role(role)
                .isRoot(false).isActive(true).build());
        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", u.getSessionVersion());
        return "Bearer " + jwt.generateToken(claims, new ApplicationConfig.CustomUserPrincipal(u));
    }

    @Test
    public void onlyAdminAndDirectorReadTheTrailAndTheDirectorGetsTheOperatorList() throws Exception {
        for (Role r : List.of(Role.ROLE_MANAGER, Role.ROLE_SECRETARY, Role.ROLE_EMPLOYEE)) {
            mvc.perform(get("/api/v1/admin/audit/search").header("Authorization", token(r))).andExpect(status().isForbidden());
            mvc.perform(get("/api/v1/admin/audit/operators").header("Authorization", token(r))).andExpect(status().isForbidden());
        }
        String body = mvc.perform(get("/api/v1/admin/audit/operators").header("Authorization", token(Role.ROLE_DIRECTOR)))
                .andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
        assertTrue(body.contains("zz_mary") && body.contains("SYSTEM"), body);
        mvc.perform(get("/api/v1/admin/audit/search").param("actions", "RECORD_DELETED", "RECORD_RESTORED")
                        .param("operator", "zz_mary").header("Authorization", token(Role.ROLE_DIRECTOR)))
                .andExpect(status().isOk()).andExpect(jsonPath("$.totalElements").value(2));
    }
}
