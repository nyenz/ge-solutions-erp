package com.gesolutions.erp.modules.land.pending;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.config.ApplicationConfig;
import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.dto.PendingProjectDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.land.service.PendingProjectService;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** fix181 (Section 8, 12.1 to 12.3): the Employee / Pending workflow, end to end. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:pendingflowdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
@AutoConfigureMockMvc
public class PendingWorkflowTest {

    @Autowired private PendingProjectService pending;
    @Autowired private UserRepository users;
    @Autowired private LandProjectRepository projects;
    @Autowired private PaymentRecordRepository payments;
    @Autowired private NotificationRepository notifications;
    @Autowired private AuditLogRepository audit;
    @Autowired private MockMvc mvc;
    @Autowired private JwtService jwt;
    @Autowired private ObjectMapper json;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private User user(String prefix, Role role) {
        String name = prefix + UUID.randomUUID().toString().substring(0, 6);
        return users.save(User.builder().id(UUID.randomUUID()).username(name).email(name + "@t.co").password("x")
                .role(role).isRoot(false).isActive(true).mustChangePassword(false).sessionVersion(0).build());
    }

    private void as(User u) {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(u.getUsername(), null,
                List.of(new SimpleGrantedAuthority(u.getRole().name()))));
    }

    private LandEntryRequest entry(String nin) {
        LandEntryRequest r = new LandEntryRequest();
        r.setProjectType("FRESH_SURVEY");
        r.setDistrict("WAKISO");
        r.setClients(new ArrayList<>(List.of(LandEntryRequest.OwnerRequest.builder()
                .fullName("Field Client " + nin).phone("0772000111").nationalId(nin).build())));
        return r;
    }

    @Test
    public void employeeEntersWithoutMoneyAndASecretaryStartsIt() throws Exception {
        User emp = user("emp_", Role.ROLE_EMPLOYEE);
        User sec = user("sec_", Role.ROLE_SECRETARY);
        as(emp);

        LandEntryRequest withMoney = entry("CM" + UUID.randomUUID().toString().substring(0, 10).toUpperCase());
        withMoney.setTotalCost(new BigDecimal("1000000"));
        assertThrows(BusinessException.class, () -> pending.createPending(withMoney, null, null), "an Employee cannot send a price");

        PendingProjectDTO dto = pending.createPending(entry("CM" + UUID.randomUUID().toString().substring(0, 10).toUpperCase()), null, null);
        LandProject p = projects.findById(dto.getId()).orElseThrow();
        assertTrue(p.isPending());
        assertEquals(0, p.getTotalCost().signum());
        assertEquals(emp.getId(), p.getCreatedById());
        assertTrue(payments.findByProjectIdOrderByTimestampDesc(p.getId()).isEmpty());
        assertTrue(notifications.findAll().stream().anyMatch(n -> "PENDING_CREATED".equals(n.getType()) && p.getId().equals(n.getEntityId())));
        assertTrue(notifications.findAll().stream().noneMatch(n -> "NEW_INTAKE".equals(n.getType()) && p.getId().equals(n.getEntityId())));
        assertEquals(1, pending.mine().stream().filter(m -> m.getId().equals(p.getId())).count());

        // the office starts it: no price = refused; a price + deposit = started
        as(sec);
        LandEntryRequest noPrice = new LandEntryRequest();
        assertThrows(BusinessException.class, () -> pending.graduatePending(p.getId(), noPrice));
        LandEntryRequest price = new LandEntryRequest();
        price.setTotalCost(new BigDecimal("2000000"));
        price.setInitialPayment(new BigDecimal("500000"));
        pending.graduatePending(p.getId(), price);
        LandProject started = projects.findById(p.getId()).orElseThrow();
        assertFalse(started.isPending());
        assertNotNull(started.getGraduatedAt());
        assertEquals(0, started.getTotalCost().compareTo(new BigDecimal("2000000")));
        assertEquals(0, started.getAmountPaid().compareTo(new BigDecimal("500000")));
        assertEquals(1, payments.findByProjectIdOrderByTimestampDesc(p.getId()).size());
        assertTrue(audit.findAll().stream().noneMatch(a -> "COST_CHANGED".equals(a.getAction()) && a.getDetails().contains(String.valueOf(started.getProjectIndex()))));

        // the Employee can no longer change it
        as(emp);
        assertThrows(BusinessException.class, () -> pending.updateOwn(p.getId(), entry("X")));
    }

    @Test
    public void anEmployeeCannotTouchSomeoneElsesEntryAndARejectNeedsAReason() throws Exception {
        User a = user("empa_", Role.ROLE_EMPLOYEE);
        User b = user("empb_", Role.ROLE_EMPLOYEE);
        User sec = user("sec_", Role.ROLE_SECRETARY);
        as(a);
        PendingProjectDTO dto = pending.createPending(entry("CM" + UUID.randomUUID().toString().substring(0, 10).toUpperCase()), null, null);
        as(b);
        assertThrows(BusinessException.class, () -> pending.viewOwn(dto.getId()));
        assertThrows(BusinessException.class, () -> pending.addNote(dto.getId(), "hello"));
        as(sec);
        assertThrows(BusinessException.class, () -> pending.rejectPending(dto.getId(), "no"));
        pending.rejectPending(dto.getId(), "Entered twice by mistake");
        as(a);
        PendingProjectDTO mine = pending.mine().stream().filter(m -> m.getId().equals(dto.getId())).findFirst().orElseThrow();
        assertTrue(mine.isRejected());
        assertEquals("Entered twice by mistake", mine.getRejectedReason());
    }

    @Test
    public void theEmployeeAnswerHasNoMoneyWords() throws Exception {
        User emp = user("empj_", Role.ROLE_EMPLOYEE);
        as(emp);
        PendingProjectDTO dto = pending.createPending(entry("CM" + UUID.randomUUID().toString().substring(0, 10).toUpperCase()), null, null);
        String text = json.writeValueAsString(pending.viewOwn(dto.getId())).toLowerCase();
        for (String w : List.of("totalcost", "amountpaid", "storagefees", "balance", "payment")) {
            assertFalse(text.contains(w), "the Employee answer contains '" + w + "'");
        }
    }

    @Test
    public void theEmployeeIsLockedOutOfTheOfficeAreas() throws Exception {
        User emp = user("empx_", Role.ROLE_EMPLOYEE);
        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", emp.getSessionVersion());
        String token = "Bearer " + jwt.generateToken(claims, new ApplicationConfig.CustomUserPrincipal(emp));
        UUID any = UUID.randomUUID();
        for (String url : List.of("/api/v1/land/ledger", "/api/v1/recovery/queue", "/api/v1/dashboard/home",
                "/api/v1/admin/audit/search", "/api/v1/recovery/payments/list", "/api/v1/land/projects/" + any + "/deep",
                "/api/v1/land/portal/" + any + "/receivable", "/api/v1/land/portal/" + any + "/portfolio", "/api/v1/finance/expenses/recent",
                "/api/v1/recovery/clients/ledger", "/api/v1/land/storage-fee-default")) {
            int code = mvc.perform(get(url).header("Authorization", token)).andReturn().getResponse().getStatus();
            assertEquals(403, code, url + " must be closed to the Employee");
        }
        mvc.perform(get("/api/v1/notifications").header("Authorization", token)).andExpect(status().isOk());
        mvc.perform(get("/api/v1/land/pending/mine").header("Authorization", token)).andExpect(status().isOk());
    }
}
