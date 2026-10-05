package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.SpyBean;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.doThrow;

/** fix181 (17.16): one bad project does not stop the night's storage fees for the others, and is reported. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:jobsdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class NightJobsTest {

    @Autowired private ReceivableSchedulerService jobs;
    @SpyBean private LandProjectRepository projects;
    @Autowired private AuditLogRepository audit;
    @Autowired private NotificationRepository notifications;

    private LandProject receivable() {
        LandProject p = LandProject.builder().projectIndex("J" + UUID.randomUUID().toString().substring(0, 6).toUpperCase())
                .totalCost(new BigDecimal("1000000")).amountPaid(BigDecimal.ZERO).build();
        p.setReceivable(true);
        p.setReceivableStartDate(LocalDateTime.now().minusDays(65));
        p.setStorageFeesAccumulated(BigDecimal.ZERO);
        p.setReceivableMonthsBilled(0);
        return projects.save(p);
    }

    @Test
    public void oneFailingProjectDoesNotStopTheOthers() {
        LandProject good = receivable();
        LandProject bad = receivable();
        doThrow(new IllegalStateException("broken row")).when(projects).findById(bad.getId());

        jobs.applyMonthlyStorageFees();

        assertTrue(projects.findAllIncludingPending().stream().filter(p -> p.getId().equals(good.getId()))
                .findFirst().orElseThrow().getStorageFeesAccumulated().signum() > 0, "the good project was billed");
        assertTrue(audit.findAll().stream().anyMatch(a -> "STORAGE_JOB_FAILED".equals(a.getAction())));
        assertTrue(notifications.findAll().stream().noneMatch(n -> bad.getId().equals(n.getEntityId())), "no alert for the failed project");
        assertTrue(notifications.findAll().stream().anyMatch(n -> "JOB_FAILED".equals(n.getType())));
        assertTrue(notifications.findAll().stream().noneMatch(n -> good.getId().equals(n.getEntityId())),
                "one summary alert per day, not one per project");
    }
}
