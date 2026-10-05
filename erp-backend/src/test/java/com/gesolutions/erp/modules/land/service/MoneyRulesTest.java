package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
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
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (16.1, 16.2, 16.9, 16.12c): payment dates, period totals and the books check. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:moneydb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class MoneyRulesTest {

    @Autowired private LandService landService;
    @Autowired private LandProjectRepository projects;
    @Autowired private PaymentRecordRepository payments;
    @Autowired private ClientRepository clients;
    @Autowired private BooksCheckService booksCheck;
    @Autowired private PaymentQueryService paymentQuery;

    /** fix181 (16.13): the Payments list -- purpose, reversed pairs net to 0, deleted projects never in totals. */
    @Test
    @SuppressWarnings("unchecked")
    public void paymentListShowsPurposeAndNetsReversals() {
        LandProject p = project();
        PaymentRecord a = landService.recordPayment(p.getId(), new BigDecimal("300000"), "x", null, "TITLE");
        landService.reversePayment(p.getId(), a.getId(), "Wrong amount typed");
        landService.recordPayment(p.getId(), new BigDecimal("200000"), "y", null, "TITLE");
        var f = new PaymentQueryService.Filter(null, null, "ALL", null, String.valueOf(p.getProjectIndex()), false, false, "date", "desc");
        var rows = paymentQuery.rows(f);
        assertEquals(3, rows.size());
        assertTrue(rows.stream().anyMatch(r -> Boolean.TRUE.equals(r.get("reversed"))));
        assertTrue(rows.stream().anyMatch(r -> "REVERSAL".equals(r.get("kind")) && r.get("reversalOf") != null));
        var t = paymentQuery.totals(f);
        assertEquals(0, ((BigDecimal) t.get("net")).compareTo(new BigDecimal("200000")));
        assertEquals(0, ((BigDecimal) t.get("reversed")).compareTo(new BigDecimal("300000")));
        p.setDeleted(true);
        projects.save(p);
        assertEquals(0, ((Number) paymentQuery.totals(f).get("rowCount")).intValue(), "a deleted project's lines are in no total");
        var withDeleted = new PaymentQueryService.Filter(null, null, "ALL", null, String.valueOf(p.getProjectIndex()), true, false, "date", "desc");
        assertEquals(3, paymentQuery.rows(withDeleted).size(), "the switch shows them (tagged DELETED)");
    }

    private LandProject project() {
        String tag = UUID.randomUUID().toString().substring(0, 8);
        Client c = clients.save(Client.builder().fullName("Client " + tag).phoneNumber("0711" + tag.substring(0, 6)).nationalId("NIN" + tag).build());
        LandProject p = LandProject.builder().projectIndex("M" + tag.substring(0, 6).toUpperCase())
                .totalCost(new BigDecimal("5000000")).amountPaid(BigDecimal.ZERO)
                .createdAt(LocalDateTime.now().minusDays(200)).build();
        p.addClient(c);
        return projects.save(p);
    }

    @Test
    public void aBackdatedPaymentNeverMovesTheLastPaymentDateBack() {
        LandProject p = project();
        landService.recordPayment(p.getId(), new BigDecimal("100000"), "today", null, "TITLE", null, null);
        LocalDateTime last = projects.findById(p.getId()).orElseThrow().getLastPaymentDate();
        landService.recordPayment(p.getId(), new BigDecimal("100000"), "last week", null, "TITLE", null, LocalDate.now().minusDays(7));
        assertEquals(last, projects.findById(p.getId()).orElseThrow().getLastPaymentDate());
    }

    @Test
    public void aFutureOrTooOldDateIsRefused() {
        LandProject p = project();
        assertThrows(BusinessException.class, () -> landService.recordPayment(p.getId(), new BigDecimal("1000"), "x", null, "TITLE", null, LocalDate.now().plusDays(1)));
        assertThrows(BusinessException.class, () -> landService.recordPayment(p.getId(), new BigDecimal("1000"), "x", null, "TITLE", null, LocalDate.now().minusDays(61)));
    }

    @Test
    public void periodTotalsUsePaidOnAndLeaveOutUndatedAndDeleted() {
        LocalDateTime since = LocalDateTime.now().minusDays(30);
        BigDecimal before = payments.sumAllPaymentsSince(since);

        LandProject p = project();
        PaymentRecord dated = landService.recordPayment(p.getId(), new BigDecimal("500000"), "dated", null, "TITLE");
        PaymentRecord reversed = landService.recordPayment(p.getId(), new BigDecimal("200000"), "oops", null, "TITLE");
        landService.reversePayment(p.getId(), reversed.getId(), "Typed the wrong amount");
        // an undated intake deposit (paid_on NULL)
        payments.save(PaymentRecord.builder().projectId(p.getId()).amountPaid(new BigDecimal("3000000"))
                .paymentType("INITIAL_DEPOSIT").recordedBy("x").notes("Initial deposit at intake").build());

        assertEquals(0, payments.sumAllPaymentsSince(since).subtract(before).compareTo(new BigDecimal("500000")),
                "500,000 dated + 200,000 - 200,000 reversed; the undated 3,000,000 is not in the month");
        List<Object[]> undated = payments.undatedDeposits();
        assertTrue(((Number) undated.get(0)[0]).longValue() >= 1);

        // a deleted project's payments are in no total
        LandProject gone = project();
        landService.recordPayment(gone.getId(), new BigDecimal("700000"), "x", null, "TITLE");
        BigDecimal withIt = payments.sumAllPaymentsSince(since);
        gone.setDeleted(true);
        projects.save(gone);
        assertEquals(0, withIt.subtract(payments.sumAllPaymentsSince(since)).compareTo(new BigDecimal("700000")));
        assertNotNull(dated.getPaidOn());
    }

    @Test
    public void theBooksCheckFindsAProjectWhoseLinesDoNotAddUp() {
        LandProject p = project();
        landService.recordPayment(p.getId(), new BigDecimal("100000"), "x", null, "TITLE");
        assertTrue(booksCheck.differences().stream().noneMatch(m -> p.getId().equals(m.get("projectId"))));
        LandProject broken = projects.findById(p.getId()).orElseThrow();
        broken.setAmountPaid(new BigDecimal("150000"));   // a total that no payment line explains
        projects.save(broken);
        assertTrue(booksCheck.differences().stream().anyMatch(m -> p.getId().equals(m.get("projectId"))));
        assertEquals(0, projects.findById(p.getId()).orElseThrow().getAmountPaid().compareTo(new BigDecimal("150000")), "the check never edits");
    }
}
