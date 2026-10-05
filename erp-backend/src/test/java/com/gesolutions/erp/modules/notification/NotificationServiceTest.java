package com.gesolutions.erp.modules.notification;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.repository.NotificationReadRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (17.1, 17.9, 17.13, 17.14, 17.22): repeat rules, after-commit writing and the "by you" read marker. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:notifdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class NotificationServiceTest {

    @Autowired private NotificationService service;
    @Autowired private NotificationRepository repo;
    @Autowired private NotificationReadRepository readRepo;
    @Autowired private UserRepository users;
    @Autowired private PlatformTransactionManager tx;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private List<Notification> rows(String type, UUID entity) {
        return repo.findAll().stream().filter(n -> n.getType().equals(type) && entity.equals(n.getEntityId())).toList();
    }

    private User director(String name) {
        return users.save(User.builder().id(UUID.randomUUID()).username(name).email(name + "@t.co").password("x")
                .role(Role.ROLE_DIRECTOR).isRoot(false).isActive(true).build());
    }

    @Test
    public void twoPaymentsOnOneReceivableGiveTwoAlerts() {
        UUID p = UUID.randomUUID();
        service.emitToAudience("PAYMENT_ON_RECEIVABLE", "Payment one", "PROJECT", p);
        service.emitToAudience("PAYMENT_ON_RECEIVABLE", "Payment two", "PROJECT", p);
        assertEquals(2, rows("PAYMENT_ON_RECEIVABLE", p).size());
    }

    @Test
    public void oncePerEntityGivesOneRowPerAudienceRole() {
        UUID p = UUID.randomUUID();
        service.emitToAudience("PENDING_CREATED", "New pending", "PROJECT", p);
        service.emitToAudience("PENDING_CREATED", "New pending again", "PROJECT", p);
        List<Notification> r = rows("PENDING_CREATED", p);
        assertEquals(2, r.size(), "one for the Secretary and one for the Manager, not repeated");
        assertTrue(r.stream().anyMatch(n -> n.getTargetRole().equals("ROLE_SECRETARY")));
        assertTrue(r.stream().anyMatch(n -> n.getTargetRole().equals("ROLE_MANAGER")));
        assertTrue(r.stream().allMatch(n -> "PIPELINE".equals(n.getCategory())));
    }

    @Test
    public void staffAlertsReachDirectorAndAdmin() {
        UUID s = UUID.randomUUID();
        service.emitToAudience("STAFF_SUSPENDED", "Operator x suspended.", "STAFF", s);
        List<String> roles = rows("STAFF_SUSPENDED", s).stream().map(Notification::getTargetRole).toList();
        assertTrue(roles.contains("ROLE_DIRECTOR"));
        assertTrue(roles.contains("ROLE_ADMIN"));
    }

    @Test
    public void anAlertInsideARolledBackSaveIsNeverWritten() {
        UUID p = UUID.randomUUID();
        TransactionTemplate t = new TransactionTemplate(tx);
        t.executeWithoutResult(status -> {
            service.emitToAudience("PAYMENT_ON_RECEIVABLE", "Payment that fails", "PROJECT", p);
            status.setRollbackOnly();
        });
        assertEquals(0, rows("PAYMENT_ON_RECEIVABLE", p).size());
    }

    @Test
    public void theActorsOwnCopyIsAlreadyRead() {
        User d1 = director("dir_one_" + UUID.randomUUID().toString().substring(0, 6));
        User d2 = director("dir_two_" + UUID.randomUUID().toString().substring(0, 6));
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(d1.getUsername(), null, List.of()));
        UUID e = UUID.randomUUID();
        service.emitToAudience("EXPENSE_LOGGED", "Expense logged by " + d1.getUsername() + ".", "EXPENSE", e);
        Notification n = rows("EXPENSE_LOGGED", e).get(0);
        assertEquals(d1.getUsername(), n.getActor());
        assertTrue(readRepo.existsByNotificationIdAndUserId(n.getId(), d1.getId()), "the Director who logged it has 0 unread");
        assertFalse(readRepo.existsByNotificationIdAndUserId(n.getId(), d2.getId()), "a second Director still has it unread");
    }
}
