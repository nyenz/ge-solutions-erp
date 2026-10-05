package com.gesolutions.erp.common.audit;

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

/** fix181 (13.14): who an audit line is written under, and that an after-commit line follows the transaction. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:auditservicedb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class AuditServiceTest {

    @Autowired private AuditService audit;
    @Autowired private AuditLogRepository repo;
    @Autowired private PlatformTransactionManager tx;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private List<AuditLog> withDetails(String marker) {
        return repo.findAll().stream().filter(a -> marker.equals(a.getDetails())).toList();
    }

    @Test
    public void noSignedInPersonIsSystem() {
        String m = UUID.randomUUID().toString();
        audit.logAction("REPORT_EXPORT", m);
        assertEquals("SYSTEM", withDetails(m).get(0).getPerformedBy());
    }

    @Test
    public void signedInPersonIsUsed() {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("mary", null, List.of()));
        String m = UUID.randomUUID().toString();
        audit.logAction("REPORT_EXPORT", m);
        assertEquals("mary", withDetails(m).get(0).getPerformedBy());
    }

    @Test
    public void logActionAsWritesTheGivenNameAndCutsLongOnes() {
        String m = UUID.randomUUID().toString();
        audit.logActionAs("x".repeat(300), "LOGIN_FAILED", m);
        assertEquals(100, withDetails(m).get(0).getPerformedBy().length());
        String m2 = UUID.randomUUID().toString();
        audit.logActionAs("  ", "LOGIN_FAILED", m2);
        assertEquals("(unknown)", withDetails(m2).get(0).getPerformedBy());
    }

    @Test
    public void afterCommitLineFollowsTheTransaction() {
        TransactionTemplate t = new TransactionTemplate(tx);
        String rolled = UUID.randomUUID().toString();
        t.executeWithoutResult(s -> { audit.logActionAfterCommit("RECORD_UPDATED", rolled); s.setRollbackOnly(); });
        assertTrue(withDetails(rolled).isEmpty(), "a rolled-back change leaves no line");
        String kept = UUID.randomUUID().toString();
        t.executeWithoutResult(s -> audit.logActionAfterCommit("RECORD_UPDATED", kept));
        assertEquals(1, withDetails(kept).size(), "a committed change leaves exactly one line");
    }
}
