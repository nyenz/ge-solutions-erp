package com.gesolutions.erp.modules.client;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.service.ClientViewService;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.land.service.LandService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (5.3, 5.7, 5.9, 6.9): the client pages read the shared rules. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:clientviewdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class ClientViewTest {

    @Autowired private ClientViewService view;
    @Autowired private ClientRepository clients;
    @Autowired private LandProjectRepository projects;
    @Autowired private PaymentRecordRepository payments;
    @Autowired private LandService landService;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private void as(String role) {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("test." + role.toLowerCase(), null,
                List.of(new SimpleGrantedAuthority(role))));
    }

    private Client client() {
        String t = UUID.randomUUID().toString().substring(0, 8);
        return clients.save(Client.builder().fullName("View Client " + t).phoneNumber("0790" + t.substring(0, 6)).nationalId("NIN" + t).build());
    }

    private LandProject project(Client c, long cost, long paid, boolean pending) {
        LandProject p = LandProject.builder().projectIndex("V" + UUID.randomUUID().toString().substring(0, 6).toUpperCase())
                .totalCost(BigDecimal.valueOf(cost)).amountPaid(BigDecimal.valueOf(paid)).pending(pending).build();
        p.addClient(c);
        return projects.save(p);
    }

    @Test
    public void undatedDepositAndReversedPaymentLeaveNoLastPayment() {
        as("ROLE_DIRECTOR");
        Client c = client();
        LandProject p = project(c, 1_000_000, 300_000, false);
        payments.save(PaymentRecord.builder().projectId(p.getId()).amountPaid(BigDecimal.valueOf(300_000))
                .paymentType("INITIAL_DEPOSIT").recordedBy("x").notes("Initial deposit at intake").build());   // no paid_on
        PaymentRecord r = landService.recordPayment(p.getId(), BigDecimal.valueOf(100_000), "x", null, "TITLE");
        landService.reversePayment(p.getId(), r.getId(), "Wrong project entered");
        Map<String, Object> d = view.dossier(c.getId());
        assertNull(d.get("lastPaymentAt"));
        Map<String, Object> row = view.ledger().stream().filter(m -> c.getId().equals(m.get("id"))).findFirst().orElseThrow();
        assertNull(row.get("lastPaymentAt"));
    }

    @Test
    public void oneProjectNeverCancelsAnothersDebt() {
        as("ROLE_DIRECTOR");
        Client c = client();
        project(c, 500_000, 800_000, false);     // over-credited (price lowered later)
        project(c, 1_000_000, 0, false);         // owes 1,000,000
        Map<String, Object> d = view.dossier(c.getId());
        assertEquals(0, ((BigDecimal) d.get("owed")).compareTo(BigDecimal.valueOf(1_000_000)));
    }

    @Test
    public void managersGetNoMoneyAndPendingIsLeftOut() {
        Client c = client();
        project(c, 1_000_000, 0, false);
        project(c, 0, 0, true);
        as("ROLE_MANAGER");
        Map<String, Object> d = view.dossier(c.getId());
        assertNull(d.get("owed"));
        assertNull(d.get("totals"));
        assertEquals(1, ((List<?>) d.get("plots")).size(), "the Pending project is not listed");
        for (Object o : (List<?>) d.get("plots")) assertFalse(((Map<?, ?>) o).containsKey("paid"));
        Map<String, Object> row = view.ledger().stream().filter(m -> c.getId().equals(m.get("id"))).findFirst().orElseThrow();
        assertFalse(row.containsKey("owed"));
        assertEquals(1, row.get("plotCount"));
    }

    @Test
    public void aClientWithOnlyPendingProjectsIsMarkedPendingOnly() {
        as("ROLE_DIRECTOR");
        Client c = client();
        project(c, 0, 0, true);
        Map<String, Object> row = view.ledger().stream().filter(m -> c.getId().equals(m.get("id"))).findFirst().orElseThrow();
        assertEquals(Boolean.TRUE, row.get("pendingOnly"));
        assertEquals(0, row.get("plotCount"));
    }
}
