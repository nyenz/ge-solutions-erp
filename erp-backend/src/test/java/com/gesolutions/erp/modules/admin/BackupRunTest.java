package com.gesolutions.erp.modules.admin;

import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;

import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * fix268: the root backup copies every table (without key hashes), and saving it leaves an audit line and the time
 * for the monthly reminder.
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:backupdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class BackupRunTest {

    @Autowired private MockMvc mvc;
    @Autowired private JwtService jwt;
    @Autowired private UserRepository users;
    @Autowired private LandProjectRepository projects;
    @Autowired private AuditLogRepository audit;

    @Test
    public void backupCopiesTablesWithoutSecretsAndRemembersTheTime() throws Exception {
        projects.save(LandProject.builder().projectIndex("B001").totalCost(BigDecimal.TEN).amountPaid(BigDecimal.ZERO).build());
        User root = users.findByUsername("admin_root").orElseThrow();
        root.setMustChangePassword(false);
        root = users.save(root);
        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", root.getSessionVersion());
        String token = jwt.generateToken(claims, new com.gesolutions.erp.config.ApplicationConfig.CustomUserPrincipal(root));

        mvc.perform(get("/api/v1/admin/backup/status").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
        String json = mvc.perform(get("/api/v1/admin/backup/data").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tables.land_projects[0].project_index").value("B001"))
                .andExpect(jsonPath("$.tables.users[0].username").exists())
                .andReturn().getResponse().getContentAsString();
        assertFalse(json.contains("\"password\""), "key hashes never leave the server");

        mvc.perform(post("/api/v1/admin/backup/done").header("Authorization", "Bearer " + token)
                        .contentType("application/json").content("{\"mode\":\"zip\",\"files\":3,\"clients\":1}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.lastBackupAt").exists());
        assertTrue(audit.findAll().stream().anyMatch(a -> "BACKUP_SAVED".equals(a.getAction())));
    }
}
