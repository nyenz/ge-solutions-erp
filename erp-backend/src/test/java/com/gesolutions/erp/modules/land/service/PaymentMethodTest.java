package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
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
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix214 (David): every payment says HOW it was paid -- Office, Mobile Money, Bank or Other. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:methoddb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class PaymentMethodTest {

    @Autowired private LandService landService;
    @Autowired private LandProjectRepository projects;
    @Autowired private PaymentRecordRepository payments;
    @Autowired private ClientRepository clients;
    @Autowired private PaymentQueryService paymentQuery;

    private LandProject project() {
        String tag = UUID.randomUUID().toString().substring(0, 8);
        Client c = clients.save(Client.builder().fullName("Client " + tag).phoneNumber("0711" + tag.substring(0, 6)).nationalId("NIN" + tag).build());
        LandProject p = LandProject.builder().projectIndex("W" + tag.substring(0, 6).toUpperCase())
                .totalCost(new BigDecimal("5000000")).amountPaid(BigDecimal.ZERO)
                .createdAt(LocalDateTime.now().minusDays(200)).build();
        p.addClient(c);
        return projects.save(p);
    }

    @Test
    public void aPaymentWithoutAMethodIsRefusedAndSavesNothing() {
        LandProject p = project();
        BusinessException e = assertThrows(BusinessException.class, () -> landService.recordPayment(p.getId(), new BigDecimal("100000"),
                "x", null, "TITLE", null, null, null, null));
        assertTrue(e.getMessage().startsWith("PAYMENT_METHOD_REQUIRED"), e.getMessage());
        assertThrows(BusinessException.class, () -> landService.recordPayment(p.getId(), new BigDecimal("100000"),
                "x", null, "TITLE", null, null, "CHEQUE", null));
        assertTrue(payments.findByProjectIdOrderByTimestampDesc(p.getId()).isEmpty());
        assertEquals(0, projects.findById(p.getId()).orElseThrow().getAmountPaid().signum());
    }

    @Test
    public void otherNeedsAFewWordsSayingHow() {
        LandProject p = project();
        BusinessException e = assertThrows(BusinessException.class, () -> landService.recordPayment(p.getId(), new BigDecimal("100000"),
                "x", null, "TITLE", null, null, "OTHER", ""));
        assertTrue(e.getMessage().startsWith("PAYMENT_METHOD_DETAIL_REQUIRED"), e.getMessage());
        PaymentRecord ok = landService.recordPayment(p.getId(), new BigDecimal("100000"), "x", null, "TITLE", null, null, "OTHER", "Cheque no. 1042");
        assertEquals("OTHER", ok.getPaymentMethod());
        assertEquals("Cheque no. 1042", ok.getPaymentReference());
    }

    @Test
    public void theMethodAndReferenceAreSavedAndAReversalCopiesThem() {
        LandProject p = project();
        PaymentRecord paid = landService.recordPayment(p.getId(), new BigDecimal("300000"), "x", null, "TITLE", null, null, "mobile money", " MP2410 77 ");
        assertEquals("MOBILE_MONEY", paid.getPaymentMethod(), "the words are turned into the code");
        assertEquals("MP2410 77", paid.getPaymentReference());
        landService.reversePayment(p.getId(), paid.getId(), "Entered on the wrong project");
        PaymentRecord rev = payments.findByProjectIdOrderByTimestampDesc(p.getId()).stream()
                .filter(r -> "REVERSAL".equals(r.getPaymentType())).findFirst().orElseThrow();
        assertEquals("MOBILE_MONEY", rev.getPaymentMethod());
    }

    @Test
    @SuppressWarnings("unchecked")
    public void thePaymentsListFiltersAndTotalsByMethod() {
        LandProject p = project();
        landService.recordPayment(p.getId(), new BigDecimal("100000"), "x", null, "TITLE", null, null, "OFFICE", null);
        landService.recordPayment(p.getId(), new BigDecimal("250000"), "x", null, "TITLE", null, null, "BANK", "DFCU 88");
        String q = String.valueOf(p.getProjectIndex());
        var bank = new PaymentQueryService.Filter(null, null, "ALL", null, q, false, false, "date", "desc", "BANK");
        List<Map<String, Object>> rows = paymentQuery.rows(bank);
        assertEquals(1, rows.size());
        assertEquals("Bank", rows.get(0).get("paymentMethodLabel"));
        Map<String, Object> totals = paymentQuery.totals(new PaymentQueryService.Filter(null, null, "ALL", null, q, false, false, "date", "desc"));
        List<Map<String, Object>> by = (List<Map<String, Object>>) totals.get("byMethod");
        BigDecimal office = BigDecimal.ZERO, bankSum = BigDecimal.ZERO;
        for (Map<String, Object> m : by) {
            if ("OFFICE".equals(m.get("method"))) office = (BigDecimal) m.get("net");
            if ("BANK".equals(m.get("method"))) bankSum = (BigDecimal) m.get("net");
        }
        assertEquals(0, office.compareTo(new BigDecimal("100000")));
        assertEquals(0, bankSum.compareTo(new BigDecimal("250000")));
    }

    @Test
    public void intakeMoneyNeedsAMethodButAnEntryWithNoMoneyDoesNot() {
        LandEntryRequest r = new LandEntryRequest();
        r.setTotalCost(new BigDecimal("1000000"));
        r.setInitialPayment(new BigDecimal("200000"));
        BusinessException e = assertThrows(BusinessException.class, () -> landService.checkIntakeMoney(r));
        assertTrue(e.getMessage().startsWith("PAYMENT_METHOD_REQUIRED"), e.getMessage());
        r.setPaymentMethod("BANK");
        assertEquals("BANK", landService.checkIntakeMoney(r).method());

        LandEntryRequest none = new LandEntryRequest();
        none.setTotalCost(new BigDecimal("1000000"));
        none.setPaymentMethod("BANK");
        assertNull(landService.checkIntakeMoney(none).method(), "no money = no method kept");
    }
}
