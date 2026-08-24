package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.LandTitle;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
    "MAIL_PASSWORD=testpassword"
})
public class ReceivableSchedulerTest {

    private ReceivableSchedulerService receivableSchedulerService;

    @Autowired
    private LandProjectRepository landProjectRepository;

    @Autowired

    private UUID savedProjectId;

    @AfterEach
    public void tearDown() {
        if (savedProjectId != null) {
            landProjectRepository.findById(savedProjectId).ifPresent(p -> {
                landProjectRepository.delete(p);
            });
        }
    }

    @Test
    public void testDailyStorageFeeLifecycle() throws Exception {

        // ── STEP 1: Create a plot in receivable, started 35 days ago ──────────────
        LandTitle title = LandTitle.builder()
                .tenure("FREEHOLD")
                .plotNumber("SCHED-TEST-" + UUID.randomUUID().toString().substring(0, 6))
                .district("Kampala")
                .county("Central")
                .build();

        LandProject project = LandProject.builder()
                .landTitle(title)
                .totalCost(new BigDecimal("4000000"))
                .amountPaid(new BigDecimal("1000000"))
                .isReceivable(true)
                .receivableStartDate(LocalDateTime.now().minusDays(35))
                .storageFeesAccumulated(BigDecimal.ZERO)
                .receivableMonthsBilled(0)
                .storagePaused(false)
                .status("RECEIVABLE")
                .build();

        LandProject saved = landProjectRepository.save(project);
        savedProjectId = saved.getId();

        // ── STEP 2: Run scheduler — expect 1 month of default fees (50,000) ───
        receivableSchedulerService.applyMonthlyStorageFees();

        LandProject afterStep2 = landProjectRepository.findById(savedProjectId).orElseThrow();
        assertEquals(0, new BigDecimal("50000").compareTo(afterStep2.getStorageFeesAccumulated()),
                "Step 2: Expected 50,000 UGX storage fees after 1 month");
        assertEquals(1, afterStep2.getReceivableMonthsBilled(),
                "Step 2: Expected receivableMonthsBilled = 1");

        // ── STEP 3: Time-travel to 65 days ago, set custom rate of 75,000 ─────
        afterStep2.setReceivableStartDate(LocalDateTime.now().minusDays(65));
        afterStep2.setReceivableMonthsBilled(1);
        afterStep2.setStorageFeeOverride(new BigDecimal("75000"));
        landProjectRepository.save(afterStep2);

        // ── STEP 4: Run scheduler — expect 2nd month billed at 75,000 ─────────
        receivableSchedulerService.applyMonthlyStorageFees();

        LandProject afterStep4 = landProjectRepository.findById(savedProjectId).orElseThrow();
        assertEquals(0, new BigDecimal("125000").compareTo(afterStep4.getStorageFeesAccumulated()),
                "Step 4: Expected total accumulated fees of 125,000 UGX (50k + 75k)");
        assertEquals(2, afterStep4.getReceivableMonthsBilled(),
                "Step 4: Expected receivableMonthsBilled = 2");

        // ── STEP 5: Set a negotiation deadline in the future ──────────────────
        afterStep4.setNegotiationDeadline(LocalDateTime.now().plusDays(2));
        afterStep4.setReceivableStartDate(LocalDateTime.now().minusDays(95));
        landProjectRepository.save(afterStep4);

        // ── STEP 6: Run scheduler — expect fees unchanged due to active deadline
        receivableSchedulerService.applyMonthlyStorageFees();

        LandProject afterStep6 = landProjectRepository.findById(savedProjectId).orElseThrow();
        assertEquals(0, new BigDecimal("125000").compareTo(afterStep6.getStorageFeesAccumulated()),
                "Step 6: Expected fees to remain 125,000 UGX — scheduler should skip due to negotiation deadline");
        assertEquals(2, afterStep6.getReceivableMonthsBilled(),
                "Step 6: Expected receivableMonthsBilled to remain 2 — scheduler should skip");
    }
}
