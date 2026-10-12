package com.gesolutions.erp.modules.land;

import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.service.LandService;
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
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * fix201 (David, test step G5): the Manager reverses a payment through the SAME web address the Folder page calls
 * (POST /api/v1/land/projects/{id}/payments/{paymentId}/reverse), signed in with a real token, exactly like the app.
 * A Secretary is still refused (403). If this passes and the live app still refuses the Manager, the live server is
 * running older code (Render has not deployed it).
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:managerrightsdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class ManagerMoneyRightsWebTest {

    @Autowired private MockMvc mvc;
    @Autowired private JwtService jwt;
    @Autowired private UserRepository users;
    @Autowired private LandProjectRepository projects;
    @Autowired private ClientRepository clients;
    @Autowired private LandService land;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private User staff(Role role) {
        String name = "web_" + role.name().toLowerCase() + "_" + UUID.randomUUID().toString().substring(0, 6);
        return users.save(User.builder().username(name).email(name + "@t.co").password("x").role(role)
                .isRoot(false).isActive(true).mustChangePassword(false).sessionVersion(0).build());
    }

    private String token(User u) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("sv", u.getSessionVersion());
        return "Bearer " + jwt.generateToken(claims, new com.gesolutions.erp.config.ApplicationConfig.CustomUserPrincipal(u));
    }

    private PaymentRecord paidProject() {
        String tag = UUID.randomUUID().toString().substring(0, 8);
        Client c = clients.save(Client.builder().fullName("WEB CLIENT " + tag).phoneNumber("0700" + tag.substring(0, 6)).nationalId("NIN" + tag).build());
        LandProject p = LandProject.builder().projectIndex("W" + tag.substring(0, 6).toUpperCase())
                .totalCost(new BigDecimal("1000000")).amountPaid(BigDecimal.ZERO).build();
        p.addClient(c);
        p = projects.save(p);
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("seed", null,
                List.of(new SimpleGrantedAuthority("ROLE_DIRECTOR"))));
        PaymentRecord pay = land.recordPayment(p.getId(), new BigDecimal("150050"), "test", null, "TITLE");
        SecurityContextHolder.clearContext();
        return pay;
    }

    @Test
    public void aManagerReversesThroughTheWebAddressAndASecretaryIsRefused() throws Exception {
        PaymentRecord pay = paidProject();
        String url = "/api/v1/land/projects/" + pay.getProjectId() + "/payments/" + pay.getId() + "/reverse";

        mvc.perform(post(url).param("reason", "Entered by mistake (wrong amount)").header("Authorization", token(staff(Role.ROLE_SECRETARY))))
                .andExpect(status().isForbidden());
        mvc.perform(post(url).param("reason", "Entered by mistake (wrong amount)").header("Authorization", token(staff(Role.ROLE_MANAGER))))
                .andExpect(status().isOk());
        assertEquals(0, projects.findById(pay.getProjectId()).orElseThrow().getAmountPaid().signum(), "the payment was taken back");
    }

    /** fix206 (David): the Manager reads the payment lines (last 90 days) but never the totals; a Secretary reads neither. */
    @Test
    public void aManagerSeesPaymentLinesButNotTheTotals() throws Exception {
        String manager = token(staff(Role.ROLE_MANAGER));
        mvc.perform(get("/api/v1/recovery/payments/list").param("from", "2000-01-01").header("Authorization", manager)).andExpect(status().isOk());
        mvc.perform(get("/api/v1/recovery/payments/totals").header("Authorization", manager)).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/recovery/payments/books-check").header("Authorization", manager)).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/recovery/payments/list").header("Authorization", token(staff(Role.ROLE_SECRETARY)))).andExpect(status().isForbidden());
    }
}
