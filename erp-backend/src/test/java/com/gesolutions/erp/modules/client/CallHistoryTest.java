package com.gesolutions.erp.modules.client;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.client.controller.RecoveryNoteController;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/**
 * fix220 (David, test O7): a client's call history must come back with the calls a PERSON logged. The note's author is
 * lazy and open-in-view is off, so this test deliberately runs WITHOUT a test transaction (like a real web request).
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:callhistorydb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.jpa.open-in-view=false",
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
public class CallHistoryTest {

    @Autowired private RecoveryNoteController controller;
    @Autowired private ClientRepository clients;
    @Autowired private RecoveryNoteRepository notes;
    @Autowired private UserRepository users;

    @AfterEach
    void out() { SecurityContextHolder.clearContext(); }

    @Test
    public void theHistoryShowsCallsLoggedByAPerson() {
        String tag = UUID.randomUUID().toString().substring(0, 8);
        User sec = users.save(User.builder().username("sec." + tag).email("sec." + tag + "@gesolutions.com").password("x")
                .role(Role.ROLE_SECRETARY).isRoot(false).isActive(true).mustChangePassword(false).build());
        Client c = clients.save(Client.builder().fullName("Client " + tag).phoneNumber("0711" + tag.substring(0, 6)).nationalId("NIN" + tag).build());
        notes.save(RecoveryNote.builder().client(c).author(sec).tag("not picking up").tone("NEGATIVE").countsAsAttempt(true).text("Rang twice").build());
        notes.save(RecoveryNote.builder().client(c).author(null).tag("payment received").tone("INFO").countsAsAttempt(false).text("Paid").build());

        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("boss", "x",
                List.of(new SimpleGrantedAuthority("ROLE_MANAGER"))));
        List<Map<String, Object>> history = controller.notes(c.getId());
        assertEquals(2, history.size(), history.toString());
        assertTrue(history.stream().anyMatch(m -> ("sec." + tag).equals(m.get("author"))), "the person who logged the call is named");
    }

    @Test
    public void aManagerDeletesACallNoteButNeverAPaymentLine() {
        String tag = UUID.randomUUID().toString().substring(0, 8);
        User sec = users.save(User.builder().username("sec2." + tag).email("sec2." + tag + "@gesolutions.com").password("x")
                .role(Role.ROLE_SECRETARY).isRoot(false).isActive(true).mustChangePassword(false).build());
        Client c = clients.save(Client.builder().fullName("Client " + tag).phoneNumber("0712" + tag.substring(0, 6)).nationalId("NJN" + tag).build());
        RecoveryNote call = notes.save(RecoveryNote.builder().client(c).author(sec).tag("not picking up").tone("NEGATIVE").countsAsAttempt(true).text("No answer").build());
        RecoveryNote paid = notes.save(RecoveryNote.builder().client(c).author(null).tag("payment received").tone("INFO").countsAsAttempt(false).text("Paid").build());
        var auth = new UsernamePasswordAuthenticationToken("boss", "x", List.of(new SimpleGrantedAuthority("ROLE_MANAGER")));
        SecurityContextHolder.getContext().setAuthentication(auth);

        assertThrows(com.gesolutions.erp.common.exception.BusinessException.class, () -> controller.deleteNote(paid.getId(), auth));
        controller.deleteNote(call.getId(), auth);
        List<Map<String, Object>> left = controller.notes(c.getId());
        assertEquals(1, left.size(), left.toString());
        assertEquals("payment received", left.get(0).get("tag"));
        assertThrows(com.gesolutions.erp.common.exception.BusinessException.class, () -> controller.deleteNote(call.getId(), auth),
                "deleting twice says the note is gone");
    }
}
