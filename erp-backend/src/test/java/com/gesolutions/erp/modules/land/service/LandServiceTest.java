package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

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
@Transactional
public class LandServiceTest {

    @Autowired
    private LandService landService;

    @Autowired
    private LandProjectRepository landProjectRepository;

    @Autowired
    private PaymentRecordRepository paymentRecordRepository;

    @Test
    public void testAtomicIntakeSavesCorrectly() throws Exception {
        LandEntryRequest.OwnerRequest owner = LandEntryRequest.OwnerRequest.builder()
                .fullName("Test Owner")
                .phone("0700000000")
                .email("owner@test.com")
                .nationalId("CM12345678ABCDE")
                .address("Kampala, Uganda")
                .build();

        List<LandEntryRequest.OwnerRequest> owners = new ArrayList<>();
        owners.add(owner);

        LandEntryRequest request = LandEntryRequest.builder()
                .plotNumber("KLA-001-TEST")
                .tenure("FREEHOLD")
                .blockRoad("Test Block")
                .district("Kampala")
                .county("Test County")
                .volume("V1")
                .folio("F1")
                .instrumentNo("INS-001")
                .physicalBoxNumber("BOX-01")
                .owners(owners)
                .totalCost(new BigDecimal("5000000"))
                .initialPayment(new BigDecimal("1000000"))
                .isLegacy(false)
                .isStartAsReceivable(false)
                .build();

        LandProject saved = landService.atomicIntake(request, null);

        assertEquals("KLA-001-TEST", saved.getLandTitle().getPlotNumber());

        Optional<LandProject> fetched = landProjectRepository.findById(saved.getId());
        assertTrue(fetched.isPresent());
        assertEquals("KLA-001-TEST", fetched.get().getLandTitle().getPlotNumber());
        assertEquals(1, fetched.get().getProprietors().size());

        List<PaymentRecord> payments = paymentRecordRepository.findByProjectIdOrderByTimestampDesc(saved.getId());
        assertFalse(payments.isEmpty());

        boolean foundInitialPayment = payments.stream()
                .anyMatch(p -> p.getAmountPaid().compareTo(new BigDecimal("1000000")) == 0);
        assertTrue(foundInitialPayment);
    }
}
