package com.gesolutions.erp.modules.land;

import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.land.service.FileStorageService;
import com.gesolutions.erp.modules.land.service.LandService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/** fix181 (13.4, 13.14): a payment whose receipt cannot be stored is not saved and leaves no PAYMENT_RECORDED line. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:receiptdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
@WithMockUser(username = "receipt.manager", roles = "MANAGER")
public class PaymentReceiptRollbackTest {

    @Autowired private LandService landService;
    @Autowired private LandProjectRepository projects;
    @Autowired private PaymentRecordRepository payments;
    @Autowired private AuditLogRepository audit;
    @MockBean private FileStorageService storage;

    @Test
    public void failedReceiptLeavesNoPaymentAndNoAuditLine() throws Exception {
        when(storage.storeFile(any(), any())).thenThrow(new RuntimeException("storage is down"));
        LandProject p = projects.save(LandProject.builder().projectIndex("RCPT1").totalCost(BigDecimal.valueOf(1_000_000))
                .amountPaid(BigDecimal.ZERO).build());
        byte[] png = new byte[] { (byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10, 0, 0, 0, 13 };
        MockMultipartFile receipt = new MockMultipartFile("receipt", "r.png", "image/png", png);

        assertThrows(Exception.class, () -> landService.recordPaymentWithReceipt(p.getId(), BigDecimal.valueOf(250_000), "x", receipt, null, "TITLE"));

        assertEquals(0, projects.findById(p.getId()).orElseThrow().getAmountPaid().compareTo(BigDecimal.ZERO), "the payment was rolled back");
        assertTrue(payments.findAll().stream().noneMatch(r -> p.getId().equals(r.getProjectId())), "no payment line");
        assertTrue(audit.findAll().stream().noneMatch(a -> "PAYMENT_RECORDED".equals(a.getAction())
                && a.getDetails() != null && a.getDetails().contains("RCPT1")), "no PAYMENT_RECORDED line");
    }
}
