package com.gesolutions.erp.modules.auth;

import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.auth.service.MailService;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** fix279: the owner (root) can get back in with a code sent to the real owner email. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:recoverydb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "ge.solutions.jwt.secret=YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    "ge.solutions.storage=local",
    "ge.solutions.upload-dir=target/test-uploads-recovery",
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
public class OwnerRecoveryWebTest {

    @Autowired private MockMvc mvc;
    @Autowired private UserRepository users;
    @Autowired private PasswordEncoder encoder;
    @MockBean private MailService mail;

    private void setRootEmail(String email) {
        User root = users.findByUsername("admin_root").orElseThrow();
        root.setEmail(email);
        root.setResetToken(null);
        users.save(root);
    }

    private void ask() throws Exception {
        mvc.perform(post("/api/v1/auth/recover-owner").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isOk());
    }

    private int confirm(String code, String key) throws Exception {
        return mvc.perform(post("/api/v1/auth/recover-owner/confirm").contentType(MediaType.APPLICATION_JSON)
                .content("{\"code\":\"" + code + "\",\"newPassword\":\"" + key + "\"}"))
                .andReturn().getResponse().getStatus();
    }

    @Test
    public void aCodeWorksOnceAndOnlyForTheRealOwnerEmail() throws Exception {
        // 1. the old placeholder email gets NO mail, but the answer looks the same
        setRootEmail("test@gesolutions.com");
        ask();
        verify(mail, never()).sendOwnerCode(any(), any(), anyInt());

        // 2. a real email gets a code
        setRootEmail("owner@example.org");
        when(mail.sendOwnerCode(eq("owner@example.org"), anyString(), anyInt())).thenReturn(true);
        ask();
        ArgumentCaptor<String> code = ArgumentCaptor.forClass(String.class);
        verify(mail).sendOwnerCode(eq("owner@example.org"), code.capture(), anyInt());
        assertTrue(code.getValue().matches("\\d{6}"));

        // 3. a wrong code is refused
        String wrong = code.getValue().equals("000000") ? "111111" : "000000";
        assertEquals(400, confirm(wrong, "Brand-New-Key-9"));

        // 4. the right code with a weak key is refused and the code is still alive
        assertEquals(400, confirm(code.getValue(), "short"));

        // 5. the right code with a good key works
        assertEquals(200, confirm(code.getValue(), "Brand-New-Key-9"));
        User root = users.findByUsername("admin_root").orElseThrow();
        assertTrue(encoder.matches("Brand-New-Key-9", root.getPassword()));
        assertNull(root.getResetToken());
        assertFalse(root.isMustChangePassword());

        // 6. the same code cannot be used twice
        assertEquals(400, confirm(code.getValue(), "Another-New-Key-7"));
    }

    @Test
    public void tooManyWrongTriesKillTheCode() throws Exception {
        setRootEmail("owner2@example.org");
        when(mail.sendOwnerCode(eq("owner2@example.org"), anyString(), anyInt())).thenReturn(true);
        ask();
        ArgumentCaptor<String> code = ArgumentCaptor.forClass(String.class);
        verify(mail).sendOwnerCode(eq("owner2@example.org"), code.capture(), anyInt());
        String wrong = code.getValue().equals("000000") ? "111111" : "000000";
        for (int i = 0; i < 5; i++) assertEquals(400, confirm(wrong, "Brand-New-Key-9"));
        // the code is dead now, even the right one is refused
        assertEquals(400, confirm(code.getValue(), "Brand-New-Key-9"));
    }
}
