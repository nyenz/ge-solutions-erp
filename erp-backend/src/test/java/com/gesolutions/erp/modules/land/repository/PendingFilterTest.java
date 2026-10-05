package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.LandProject;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.PageRequest;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/**
 * fix181 (8.9): a Pending project is left out of the plain findAll() (Dashboard, Recovery, nightly jobs, reports,
 * Client Ledger all read it) and out of the receivable queries, but the ledger list and findById still see it.
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:pendingdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
    "spring.datasource.hikari.connection-init-sql=SELECT 1"
})
public class PendingFilterTest {

    @Autowired
    private LandProjectRepository repo;

    private LandProject project(boolean pending, boolean receivable) {
        String idx = "T" + UUID.randomUUID().toString().substring(0, 6).toUpperCase();
        LandProject p = LandProject.builder()
                .projectIndex(idx)
                .totalCost(BigDecimal.valueOf(pending ? 0 : 1_000_000))
                .amountPaid(BigDecimal.ZERO)
                .pending(pending)
                .build();
        p.setReceivable(receivable);
        if (receivable) {
            p.setReceivableStartDate(LocalDateTime.now().minusMonths(2));
            p.setStorageFeesAccumulated(BigDecimal.valueOf(50_000));
        }
        return repo.save(p);
    }

    @Test
    public void pendingProjectsStayOutOfMoneyListsButOpenInTheLedger() {
        LandProject live = project(false, false);
        LandProject pending = project(true, false);
        LandProject pendingReceivable = project(true, true);

        List<UUID> plain = repo.findAll().stream().map(LandProject::getId).toList();
        assertTrue(plain.contains(live.getId()));
        assertFalse(plain.contains(pending.getId()), "Pending must not reach the Dashboard, Recovery, jobs or reports");
        assertFalse(repo.findAll(PageRequest.of(0, 500)).getContent().stream().anyMatch(p -> p.getId().equals(pending.getId())));

        List<UUID> ledger = repo.findAllIncludingPending(PageRequest.of(0, 500)).getContent().stream().map(LandProject::getId).toList();
        assertTrue(ledger.contains(pending.getId()), "the ledger (Pending tab) still lists it");
        assertTrue(repo.findAllIncludingPending().stream().anyMatch(p -> p.getId().equals(pending.getId())));
        assertTrue(repo.countPending() >= 2);

        assertFalse(repo.findAllReceivablePlots().stream().anyMatch(p -> p.getId().equals(pendingReceivable.getId())));
        assertEquals(0, repo.countReceivablePlots());
        assertEquals(0, repo.sumAllStorageFees().signum());
        assertFalse(repo.findAutoReceivableCandidates(LocalDateTime.now().plusYears(5)).stream()
                .anyMatch(p -> p.getId().equals(pending.getId())));

        assertTrue(repo.findById(pending.getId()).isPresent(), "the Folder page still opens a Pending project");
        assertNotNull(repo.findById(live.getId()).orElseThrow().getCreatedAt(), "created_at is set on first save");
    }
}
