package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** fix273: with GE_SOLUTIONS_STORAGE=local a saved document opens only for a signed-in person. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:vaultdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "ge.solutions.jwt.secret=YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    "ge.solutions.storage=local",
    "ge.solutions.upload-dir=target/test-uploads-vault",
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
public class VaultWebTest {

    @Autowired private MockMvc mvc;
    @Autowired private JwtService jwt;
    @Autowired private UserRepository users;
    @Autowired private FileStorageService storage;

    @Test
    public void aSavedDocumentOpensOnlyWithAKey() throws Exception {
        assertTrue(storage instanceof LocalStorageServiceImpl, "local storage is the one in use");
        String addr = storage.storeFile(new MockMultipartFile("f", "Title deed.pdf", "application/pdf", "PDFDATA".getBytes()), "proj-1");
        String[] parts = addr.substring("/ge_uploads/".length()).split("/");
        String url = "/api/v1/vault/" + parts[0] + "/" + parts[1];

        mvc.perform(get(url)).andExpect(status().is4xxClientError());

        User root = users.findByUsername("admin_root").orElseThrow();
        root.setMustChangePassword(false);
        root = users.save(root);
        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", root.getSessionVersion());
        String token = jwt.generateToken(claims, new com.gesolutions.erp.config.ApplicationConfig.CustomUserPrincipal(root));

        String body = mvc.perform(get(url).header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        assertEquals("PDFDATA", body);
        mvc.perform(get("/api/v1/vault/proj-1/not-there.pdf").header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());

        storage.deleteFile(addr);
        mvc.perform(get(url).header("Authorization", "Bearer " + token)).andExpect(status().isNotFound());
    }
}
