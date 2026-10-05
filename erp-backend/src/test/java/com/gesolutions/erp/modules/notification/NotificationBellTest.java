package com.gesolutions.erp.modules.notification;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.notification.controller.NotificationController;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (17.4, 17.18, 21.x): the bell counts, notify_since, READ by group up to a time, validated ids. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:belldb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class NotificationBellTest {

    @Autowired private NotificationController bell;
    @Autowired private NotificationRepository repo;
    @Autowired private UserRepository users;

    private User user(Role role, LocalDateTime since) {
        String n = "bell_" + UUID.randomUUID().toString().substring(0, 8);
        return users.save(User.builder().id(UUID.randomUUID()).username(n).email(n + "@t.co").password("x").role(role)
                .isRoot(false).isActive(true).notifySince(since).build());
    }

    private UsernamePasswordAuthenticationToken auth(User u) { return new UsernamePasswordAuthenticationToken(u.getUsername(), null, List.of()); }

    private Notification alert(String role, String category, LocalDateTime at) {
        return repo.save(Notification.builder().type("STATUS_ADVANCED").severity("INFO").message("x").entityType("PROJECT")
                .entityId(UUID.randomUUID()).targetRole(role).category(category).createdAt(at).build());
    }

    @Test
    public void unreadCountsEveryAlertNotJustTheFirst200() {
        LocalDateTime start = LocalDateTime.now().minusSeconds(5);
        User m = user(Role.ROLE_SECRETARY, start);
        List<Notification> batch = new ArrayList<>();
        for (int i = 0; i < 230; i++) batch.add(Notification.builder().type("LOCKED").severity("INFO").message("x").entityType("CLIENT")
                .entityId(UUID.randomUUID()).targetRole("ROLE_SECRETARY").category("RECOVERY").createdAt(LocalDateTime.now()).build());
        repo.saveAll(batch);
        Map<String, Object> s = bell.summary(auth(m));
        assertTrue(((Number) s.get("unread")).longValue() >= 230);
        assertEquals(200, bell.list(auth(m), null, 200).size(), "the list is cut at 200, the count is not");
    }

    @Test
    public void newAndPromotedPeopleDoNotInheritOldAlerts() {
        alert("ROLE_MANAGER", "PIPELINE", LocalDateTime.now().minusDays(3));
        User fresh = user(Role.ROLE_MANAGER, LocalDateTime.now().minusMinutes(1));
        assertEquals(0L, ((Number) bell.summary(auth(fresh)).get("unread")).longValue());
    }

    @Test
    public void readAllMarksOneGroupUpToTheTimeShown() {
        User d = user(Role.ROLE_DIRECTOR, LocalDateTime.now().minusDays(1));
        LocalDateTime t0 = LocalDateTime.now().minusMinutes(10);
        alert("ROLE_DIRECTOR", "MONEY", t0);
        alert("ROLE_DIRECTOR", "STAFF", t0);
        Notification later = alert("ROLE_DIRECTOR", "MONEY", LocalDateTime.now().plusSeconds(5));   // arrives after the list was shown
        bell.readAll(auth(d), "MONEY", t0.plusMinutes(1).toString());
        Map<String, Object> s = bell.summary(auth(d));
        @SuppressWarnings("unchecked") Map<String, Long> g = (Map<String, Long>) s.get("unreadByGroup");
        assertEquals(1L, g.get("STAFF"), "another group is untouched");
        assertEquals(1L, g.get("MONEY"), "the alert that came later stays unread");
        assertNotNull(later.getId());
    }

    @Test
    public void readRefusesAnUnknownOrForeignAlertAndToleratesDoubleClicks() {
        User sec = user(Role.ROLE_SECRETARY, LocalDateTime.now().minusDays(1));
        assertThrows(ResponseStatusException.class, () -> bell.read(UUID.randomUUID(), auth(sec)));
        Notification forManager = alert("ROLE_MANAGER", "PIPELINE", LocalDateTime.now());
        assertThrows(ResponseStatusException.class, () -> bell.read(forManager.getId(), auth(sec)));
        Notification mine = alert("ROLE_SECRETARY", "RECOVERY", LocalDateTime.now());
        bell.read(mine.getId(), auth(sec));
        bell.read(mine.getId(), auth(sec));
    }

    @Test
    public void linksFollowTheRank() {
        Notification staffAlert = Notification.builder().type("STAFF_SUSPENDED").entityType("STAFF").entityId(UUID.randomUUID()).build();
        Notification books = Notification.builder().type("BOOKS_MISMATCH").entityType("SYSTEM").entityId(UUID.randomUUID()).build();
        assertEquals("/settings?tab=staff", invokeLink(staffAlert, Role.ROLE_DIRECTOR));
        assertNull(invokeLink(books, Role.ROLE_MANAGER), "a Manager cannot open the Payments page");
    }

    private static String invokeLink(Notification n, Role r) {
        try {
            var m = NotificationController.class.getDeclaredMethod("linkFor", Notification.class, Role.class);
            m.setAccessible(true);
            return (String) m.invoke(null, n, r);
        } catch (Exception e) { throw new RuntimeException(e); }
    }
}
