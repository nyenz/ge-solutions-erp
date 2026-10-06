package com.gesolutions.erp.modules.client;

import com.gesolutions.erp.modules.client.controller.ClientController;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectStatus;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.ProjectStatusRepository;
import com.gesolutions.erp.modules.land.service.StatusTemplateService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix193 (review Q3 = B): what the Secretary may do -- tick any stage, correct a client's phone number. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:secretaryrightsdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class SecretaryRightsTest {

    @Autowired private ClientController clientController;
    @Autowired private StatusTemplateService statusService;
    @Autowired private ClientRepository clients;
    @Autowired private LandProjectRepository projects;
    @Autowired private ProjectStatusRepository statuses;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private void as(String role) {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("test." + role.toLowerCase(), null,
                List.of(new SimpleGrantedAuthority(role))));
    }

    private Client client() {
        String t = UUID.randomUUID().toString().substring(0, 8);
        return clients.save(Client.builder().fullName("Rights Client " + t).phoneNumber("0790111222").nationalId("NIN" + t)
                .email("old@t.co").homeAddress("Old address").build());
    }

    private LandProject project(Client c, boolean pending) {
        LandProject p = LandProject.builder().projectIndex("S" + UUID.randomUUID().toString().substring(0, 6).toUpperCase())
                .totalCost(BigDecimal.valueOf(pending ? 0 : 1_000_000)).amountPaid(BigDecimal.ZERO).pending(pending).build();
        p.addClient(c);
        return projects.save(p);
    }

    private Map<String, String> edit() {
        Map<String, String> body = new HashMap<>();
        body.put("fullName", "Changed Name");
        body.put("phoneNumber", "0772345678");
        body.put("email", "new@t.co");
        body.put("homeAddress", "New address");
        return body;
    }

    @Test
    public void secretaryTicksAndUnticksAStage() {
        Client c = client();
        LandProject p = project(c, false);
        ProjectStatus s = statuses.save(ProjectStatus.builder().projectId(p.getId()).statusName("Field Measurement").displayOrder(0).build());
        as("ROLE_SECRETARY");
        assertTrue(statusService.toggleStatusCompletion(s.getId(), true).isCompleted());
        assertEquals("test.role_secretary", statuses.findById(s.getId()).orElseThrow().getCompletedBy());
        assertFalse(statusService.toggleStatusCompletion(s.getId(), false).isCompleted());
    }

    @Test
    public void employeeStillCannotTickAStage() {
        Client c = client();
        LandProject p = project(c, false);
        ProjectStatus s = statuses.save(ProjectStatus.builder().projectId(p.getId()).statusName("Field Measurement").displayOrder(0).build());
        as("ROLE_EMPLOYEE");
        assertThrows(AccessDeniedException.class, () -> statusService.toggleStatusCompletion(s.getId(), true));
        assertFalse(statuses.findById(s.getId()).orElseThrow().isCompleted());
    }

    @Test
    public void secretaryCorrectsOnlyThePhoneOfALiveClient() {
        Client c = client();
        project(c, false);                       // a started project: this is a live client
        String oldPhone = c.getPhoneNumber();
        as("ROLE_SECRETARY");
        clientController.updateClient(c.getId(), edit());
        Client after = clients.findById(c.getId()).orElseThrow();
        assertNotEquals(oldPhone, after.getPhoneNumber(), "the phone number is corrected");
        assertTrue(after.getPhoneNumber().contains("772345678"));
        assertEquals(c.getFullName(), after.getFullName(), "the name stays");
        assertEquals("old@t.co", after.getEmail(), "the email stays");
        assertEquals("Old address", after.getHomeAddress(), "the address stays");
    }

    @Test
    public void secretaryMustSendAPhoneForALiveClient() {
        Client c = client();
        project(c, false);
        as("ROLE_SECRETARY");
        Map<String, String> body = new HashMap<>();
        body.put("fullName", "Changed Name");
        assertThrows(com.gesolutions.erp.common.exception.BusinessException.class, () -> clientController.updateClient(c.getId(), body));
        assertNotEquals("Changed Name", clients.findById(c.getId()).orElseThrow().getFullName());
    }

    @Test
    public void secretaryStillCorrectsEverythingWhileAllProjectsArePending() {
        Client c = client();
        project(c, true);
        as("ROLE_SECRETARY");
        clientController.updateClient(c.getId(), edit());
        Client after = clients.findById(c.getId()).orElseThrow();
        assertEquals("Changed Name", after.getFullName());
        assertEquals("new@t.co", after.getEmail());
        assertEquals("New address", after.getHomeAddress());
    }

    @Test
    public void managerCorrectsEverythingOnALiveClient() {
        Client c = client();
        project(c, false);
        as("ROLE_MANAGER");
        clientController.updateClient(c.getId(), edit());
        Client after = clients.findById(c.getId()).orElseThrow();
        assertEquals("Changed Name", after.getFullName());
        assertEquals("New address", after.getHomeAddress());
    }
}
