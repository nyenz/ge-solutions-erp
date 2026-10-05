package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (4.2, 11.5, 16.0a, 16.12b): what a reversal leaves behind, and a retried payment. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:reversaldb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
@Transactional
@WithMockUser(username = "test.director", roles = "DIRECTOR")
public class ReversalTest {

    @Autowired private LandService landService;
    @Autowired private LandProjectRepository projects;
    @Autowired private PaymentRecordRepository payments;
    @Autowired private ClientRepository clients;
    @Autowired private RecoveryNoteRepository notes;

    private LandProject project(boolean receivable) {
        String tag = UUID.randomUUID().toString().substring(0, 8);
        Client c = clients.save(Client.builder().fullName("Client " + tag).phoneNumber("0700" + tag.substring(0, 6))
                .nationalId("NIN" + tag).build());
        LandProject p = LandProject.builder().projectIndex("R" + tag.substring(0, 6).toUpperCase())
                .totalCost(new BigDecimal("1000000")).amountPaid(BigDecimal.ZERO).build();
        p.addClient(c);
        p.setReceivable(receivable);
        return projects.save(p);
    }

    @Test
    public void reversingTheOnlyPaymentClearsTheLastPaymentDateAndLeavesANote() {
        LandProject p = project(false);
        PaymentRecord paid = landService.recordPayment(p.getId(), new BigDecimal("500000"), "cash", null, "TITLE");
        assertNotNull(projects.findById(p.getId()).orElseThrow().getLastPaymentDate());

        landService.reversePayment(p.getId(), paid.getId(), "Entered on the wrong project");
        LandProject after = projects.findById(p.getId()).orElseThrow();
        assertNull(after.getLastPaymentDate(), "the client is no longer LOCKED by a payment that was taken back");
        assertEquals(0, after.getAmountPaid().signum());

        Client c = after.billingParties().iterator().next();
        List<RecoveryNote> ns = notes.findByClientOrderByCreatedAtDesc(c);
        assertTrue(ns.stream().anyMatch(n -> "payment reversed".equals(n.getTag()) && !n.isCountsAsAttempt()));

        // 16.0a: the reversal line has its own date, so the month nets to zero
        BigDecimal net = payments.findByProjectIdOrderByTimestampDesc(p.getId()).stream()
                .peek(r -> assertNotNull(r.getPaidOn(), "every line here has a paid-on date"))
                .map(PaymentRecord::getAmountPaid).reduce(BigDecimal.ZERO, BigDecimal::add);
        assertEquals(0, net.signum());
    }

    @Test
    public void reversingAKeptFeesPaymentPutsTheFeesBack() {
        LandProject p = project(false);
        p.setStorageFeesAccumulated(new BigDecimal("200000"));   // kept after a SET ASIDE
        projects.save(p);
        PaymentRecord fees = landService.recordPayment(p.getId(), new BigDecimal("200000"), "fees", null, "STORAGE");
        LandProject mid = projects.findById(p.getId()).orElseThrow();
        assertEquals(new BigDecimal("1200000"), mid.getTotalCost().stripTrailingZeros().setScale(0));

        landService.reversePayment(p.getId(), fees.getId(), "Cheque bounced at the bank");
        LandProject after = projects.findById(p.getId()).orElseThrow();
        assertEquals(0, after.getTotalCost().compareTo(new BigDecimal("1000000")), "the cost goes back");
        assertEquals(0, after.getStorageFeesAccumulated().compareTo(new BigDecimal("200000")), "the kept fees come back");
    }

    @Test
    public void theSamePaymentWindowCannotSaveTwice() {
        LandProject p = project(false);
        landService.recordPayment(p.getId(), new BigDecimal("100000"), "cash", null, "TITLE", "req-1");
        Exception e = assertThrows(Exception.class,
                () -> landService.recordPayment(p.getId(), new BigDecimal("100000"), "cash", null, "TITLE", "req-1"));
        assertTrue(e.getMessage().contains("already recorded"));
    }
}
