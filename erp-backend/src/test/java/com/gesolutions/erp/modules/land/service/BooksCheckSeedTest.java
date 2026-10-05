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
