package com.gesolutions.erp.modules.admin;

import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * fix181 (14.4, 15.5a): the wipe works on a fresh database (old tables that do not exist are skipped), leaves zero
 * projects with the demo data switched off, keeps the staff accounts and writes DATA_WIPED to the audit trail.
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:wipedb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class WipeRunTest {

    @Autowired private MockMvc mvc;
    @Autowired private JwtService jwt;
    @Autowired private UserRepository users;
    @Autowired private LandProjectRepository projects;
    @Autowired private ClientRepository clients;
    @Autowired private AuditLogRepository audit;

    @Test
    public void wipeEmptiesBusinessDataAndKeepsStaffAndAudit() throws Exception {
        projects.save(LandProject.builder().projectIndex("W001").totalCost(BigDecimal.TEN).amountPaid(BigDecimal.ZERO).build());
        User root = users.findByUsername("admin_root").orElseThrow();
        root.setMustChangePassword(false);   // a fresh root must change its key first (403 PASSWORD_CHANGE_REQUIRED)
        root = users.save(root);
        long staffBefore = users.count();

        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", root.getSessionVersion());
        String token = jwt.generateToken(claims, new com.gesolutions.erp.config.ApplicationConfig.CustomUserPrincipal(root));

        mvc.perform(post("/api/v1/admin/system/wipe-all-data").param("confirm", "WRONG").header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest());
        // fix181 (14.4f): the right phrase with a wrong (or no) key is refused and deletes nothing
        mvc.perform(post("/api/v1/admin/system/wipe-all-data").param("confirm", "WIPE-EVERYTHING").header("Authorization", "Bearer " + token)
                        .contentType("application/json").content("{\"password\":\"wrong-key\"}"))
                .andExpect(status().isBadRequest());
        mvc.perform(post("/api/v1/admin/system/wipe-all-data").param("confirm", "WIPE-EVERYTHING").header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest());
        assertEquals(1, projects.findAllIncludingPending().stream().filter(p -> "W001".equals(p.getProjectIndex())).count());
        mvc.perform(post("/api/v1/admin/system/wipe-all-data").param("confirm", "WIPE-EVERYTHING").header("Authorization", "Bearer " + token)
                        .contentType("application/json").content("{\"password\":\"TestPassword123\"}"))
                .andExpect(status().isOk())
                // fix181 (15.5b): the answer says how many files were and were not deleted
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.filesDeleted").exists())
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.filesFailed").exists());

        assertEquals(0, projects.findAllIncludingPending().size());
        assertEquals(0, clients.count());
        assertEquals(staffBefore, users.count(), "staff accounts are kept");
        assertTrue(audit.findAll().stream().anyMatch(a -> "DATA_WIPED".equals(a.getAction())));
        assertTrue(audit.findAll().stream().anyMatch(a -> "WIPE_REFUSED".equals(a.getAction())));
    }

    /** fix198: a FRESH START also empties the audit trail (one line is left), removes demo staff and keeps real staff. */
    @Test
    public void freshStartAlsoClearsTheAuditTrailAndDemoStaff() throws Exception {
        projects.save(LandProject.builder().projectIndex("W002").totalCost(BigDecimal.TEN).amountPaid(BigDecimal.ZERO).build());
        User root = users.findByUsername("admin_root").orElseThrow();
        root.setMustChangePassword(false);
        root = users.save(root);
        users.save(User.builder().username("demo.clerk").email("demo.clerk@demo.gesolutions.local").password("x")
                .role(com.gesolutions.erp.modules.auth.model.Role.ROLE_EMPLOYEE).isRoot(false).isActive(true).mustChangePassword(false).build());
        users.save(User.builder().username("real.clerk").email("real.clerk@gesolutions.com").password("x")
                .role(com.gesolutions.erp.modules.auth.model.Role.ROLE_EMPLOYEE).isRoot(false).isActive(true).mustChangePassword(false).build());

        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", root.getSessionVersion());
        String token = jwt.generateToken(claims, new com.gesolutions.erp.config.ApplicationConfig.CustomUserPrincipal(root));

        // a refused try first, so the trail has older lines to clear
        mvc.perform(post("/api/v1/admin/system/wipe-all-data").param("confirm", "WRONG").header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest());
        assertTrue(audit.count() >= 1);

        mvc.perform(post("/api/v1/admin/system/wipe-all-data").param("confirm", "WIPE-EVERYTHING").header("Authorization", "Bearer " + token)
                        .contentType("application/json").content("{\"password\":\"TestPassword123\",\"freshStart\":true}"))
                .andExpect(status().isOk())
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.auditCleared").value(true));

        assertEquals(0, projects.findAllIncludingPending().size());
        assertEquals(1, audit.count(), "the trail holds only the line about the fresh start");
        assertEquals("DATA_WIPED", audit.findAll().get(0).getAction());
        assertTrue(audit.findAll().get(0).getDetails().contains("FRESH START"));
        assertTrue(users.findByUsername("demo.clerk").isEmpty(), "demo staff accounts are removed");
        assertTrue(users.findByUsername("real.clerk").isPresent(), "real staff accounts are kept");
        assertTrue(users.findByUsername("admin_root").isPresent(), "the Admin is kept");
    }
}
