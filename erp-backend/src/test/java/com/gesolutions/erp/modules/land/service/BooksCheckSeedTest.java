package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** fix181 (16.12c, 11.2): the demo data adds up, and no project outside receivables holds storage-fee money. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:seedbooksdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
    "ge.solutions.seed-demo-data=true"
})
public class BooksCheckSeedTest {

    @Autowired private BooksCheckService booksCheck;
    @Autowired private LandProjectRepository projects;
    @Autowired private WorkCountsService workCounts;

    /** fix181 (17.6): the work counts equal what the Ledger filters show for the same data. */
    @Test
    @SuppressWarnings("unchecked")
    public void workCountsMatchTheLedgerRules() {
        Map<String, Object> c = workCounts.counts();
        long pending = projects.findAllIncludingPending().stream().filter(LandProject::isPending).count();
        assertEquals(pending, ((Map<String, Object>) c.get("pending")).get("count"));
        assertTrue(pending >= 4, "the demo data has 4 Pending projects");
        long ready = projects.findAll().stream().filter(p -> p.releaseBlocker() == null).count();
        assertEquals(ready, c.get("releaseReady"));
        long problems = projects.findAll().stream().filter(LandProject::isProblem).count();
        assertEquals(problems, c.get("problems"));
        long totalByType = ((Map<String, Map<String, Long>>) c.get("byType")).values().stream()
                .flatMap(m -> m.values().stream()).mapToLong(Long::longValue).sum();
        assertEquals(projects.findAllIncludingPending().size(), totalByType, "every live project is counted once");
    }

    @Test
    public void seededBooksAddUp() {
        List<Map<String, Object>> diff = booksCheck.differences();
        assertTrue(diff.isEmpty(), "seeded projects whose payments do not add up (report, do not edit): " + diff);
    }

    @Test
    public void storagePaidIsZeroOutsideReceivables() {
        for (LandProject p : projects.findAllIncludingPending()) {
            if (p.isReceivable()) continue;
            assertEquals(0, p.storagePaidSafe().signum(), "project #" + p.getProjectIndex() + " is not in receivables but has storage fees paid");
        }
    }
}
