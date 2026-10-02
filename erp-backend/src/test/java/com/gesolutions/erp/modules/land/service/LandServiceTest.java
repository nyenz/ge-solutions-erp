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
    "MAIL_PASSWORD=testpassword",
    // the Postgres-only "SET lock_timeout" from application.properties cannot run on H2
    "spring.datasource.hikari.connection-init-sql=SELECT 1"
})
@Transactional
public class LandServiceTest {

    @Autowired
    private LandService landService;

    @Autowired
    private LandProjectRepository landProjectRepository;

    @Autowired
    private PaymentRecordRepository paymentRecordRepository;

    @Autowired
    private javax.sql.DataSource dataSource;

    // the boot migration that creates the project index counter row is Postgres SQL; on H2 the row is added here
    // (own connection, committed, so the index service -- which uses its own connection -- sees it)
    @org.junit.jupiter.api.BeforeEach
    void indexCounterRow() throws Exception {
        try (java.sql.Connection c = dataSource.getConnection(); java.sql.Statement st = c.createStatement()) {
            st.execute("INSERT INTO project_index_counter (id, current_number, current_letter) SELECT 1, 0, 'A' "
                    + "WHERE NOT EXISTS (SELECT 1 FROM project_index_counter WHERE id = 1)");
        }
    }

    @Test
    public void testAtomicIntakeSavesCorrectly() throws Exception {
        LandEntryRequest.OwnerRequest owner = LandEntryRequest.OwnerRequest.builder()
                .fullName("Test Owner")
                .phone("0772123456")
                .email("owner@test.com")
                .nationalId("CM12345678ABCDE")
                .address("Kampala, Uganda")
                .build();

        List<LandEntryRequest.OwnerRequest> owners = new ArrayList<>();
        owners.add(owner);

        LandEntryRequest request = LandEntryRequest.builder()
                .projectType("TRANSFER_OF_TITLE")
                .plotNumber("KLA-001-TEST")
                .tenure("FREEHOLD")
                .block("Test Block")
                .areaHectares(new BigDecimal("0.8"))
                .volume("LRV 100")
                .folio("7")
                .titleIssueDate(java.time.LocalDate.now())
                .district("Kampala")
                .county("Test County")
                .clients(owners)
                .totalCost(new BigDecimal("5000000"))
                .initialPayment(new BigDecimal("1000000"))
                .isStartAsReceivable(false)
                .build();

        LandProject saved = landService.atomicIntake(request, null);

        assertEquals("KLA-001-TEST", saved.getLandTitle().getPlotNumber());
        assertEquals("TRANSFER_OF_TITLE", saved.getProjectType());

        Optional<LandProject> fetched = landProjectRepository.findById(saved.getId());
        assertTrue(fetched.isPresent());
        assertEquals("KLA-001-TEST", fetched.get().getLandTitle().getPlotNumber());
        assertEquals("7", fetched.get().getLandTitle().getFolio());
        // owners left empty = a copy of the clients
        assertEquals(1, fetched.get().getProprietors().size());
        assertEquals(1, fetched.get().getClients().size());

        List<PaymentRecord> payments = paymentRecordRepository.findByProjectIdOrderByTimestampDesc(saved.getId());
        assertFalse(payments.isEmpty());

        boolean foundInitialPayment = payments.stream()
                .anyMatch(p -> p.getAmountPaid().compareTo(new BigDecimal("1000000")) == 0);
        assertTrue(foundInitialPayment);
    }

    private LandEntryRequest.OwnerRequest person(String nin, String name) {
        return LandEntryRequest.OwnerRequest.builder().fullName(name).phone("0772123456").nationalId(nin).build();
    }

    @Test
    public void freshSurveyNeverKeepsTitleAndAreaIsRequired() throws Exception {
        LandEntryRequest fresh = LandEntryRequest.builder()
                .projectType("FRESH_SURVEY").plotNumber("IGNORED").district("Kampala")
                .clients(List.of(person("CM12345678FRSH1", "Fresh Client")))
                .totalCost(new BigDecimal("1000000")).initialPayment(BigDecimal.ZERO).build();
        assertEquals(null, landService.atomicIntake(fresh, null).getLandTitle());

        LandEntryRequest noArea = LandEntryRequest.builder()
                .projectType("RESURVEY").plotNumber("P1").block("B1").titleIssueDate(java.time.LocalDate.now())
                .district("Kampala").clients(List.of(person("CM12345678RESV1", "Resurvey Client")))
                .totalCost(new BigDecimal("1000000")).initialPayment(BigDecimal.ZERO).build();
        org.junit.jupiter.api.Assertions.assertThrows(com.gesolutions.erp.common.exception.BusinessException.class,
                () -> landService.atomicIntake(noArea, null));
    }

    @Test
    public void subdivisionPlotTransfersOnceIntoALinkedTransferProject() throws Exception {
        LandEntryRequest sub = LandEntryRequest.builder()
                .projectType("SUBDIVISION").subdivisionCount(3)
                .plotNumber("MOTHER-1").block("BLK 9").areaHectares(new BigDecimal("2.5")).titleIssueDate(java.time.LocalDate.now())
                .district("Wakiso")
                .clients(List.of(person("CM12345678SUBC1", "Sub Client")))
                .owners(List.of(person("CM12345678SUBO1", "Sub Owner")))
                .totalCost(new BigDecimal("3000000")).initialPayment(BigDecimal.ZERO).build();
        LandProject parent = landService.atomicIntake(sub, null);
        assertEquals(3, landService.getProjectDeepDetail(parent.getId()).getSubdivisions().size());

        LandEntryRequest transfer = LandEntryRequest.builder()
                .projectType("TRANSFER_OF_TITLE").parentProjectId(parent.getId()).parentSubdivisionNo(2)
                .plotNumber("CHILD-2").block("BLK 9").areaHectares(new BigDecimal("0.5")).titleIssueDate(java.time.LocalDate.now())
                .district("Wakiso")
                .clients(List.of(person("CM12345678SUBC1", "Sub Client")))
                .owners(List.of(person("CM12345678SUBO1", "Sub Owner")))
                .totalCost(new BigDecimal("500000")).initialPayment(BigDecimal.ZERO).build();
        LandProject child = landService.atomicIntake(transfer, null);
        assertEquals(parent.getId(), child.getParentProjectId());
        assertEquals(child.getId(), landService.getProjectDeepDetail(parent.getId()).getSubdivisions().get(1).getTransferProjectId());

        transfer.setPlotNumber("CHILD-2B");
        org.junit.jupiter.api.Assertions.assertThrows(com.gesolutions.erp.common.exception.BusinessException.class,
                () -> landService.atomicIntake(transfer, null));
    }
}
