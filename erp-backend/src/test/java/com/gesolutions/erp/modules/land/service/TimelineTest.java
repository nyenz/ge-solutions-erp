package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.TimelineEntry;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/** fix215 (David): the Notes timeline -- notes, reasons, money and calls in one list; money only for Manager and above. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:timelinedb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class TimelineTest {

    @Autowired private TimelineService timeline;
    @Autowired private NoteService notes;
    @Autowired private LandService landService;
    @Autowired private LandProjectRepository projects;
    @Autowired private ClientRepository clients;
    @Autowired private FollowUpRepository noteRepository;

    private static void as(String name, String role) {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(name, "x",
                List.of(new SimpleGrantedAuthority(role))));
    }

    @AfterEach
    void out() { SecurityContextHolder.clearContext(); }

    private LandProject project() {
        String tag = UUID.randomUUID().toString().substring(0, 8);
        Client c = clients.save(Client.builder().fullName("Client " + tag).phoneNumber("0711" + tag.substring(0, 6)).nationalId("NIN" + tag).build());
        LandProject p = LandProject.builder().projectIndex("T" + tag.substring(0, 5).toUpperCase())
                .totalCost(new BigDecimal("2000000")).amountPaid(BigDecimal.ZERO)
                .createdAt(LocalDateTime.now().minusDays(100)).build();
        p.addClient(c);
        return projects.save(p);
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> entries(Map<String, Object> t) { return (List<Map<String, Object>>) t.get("entries"); }

    private static boolean has(List<Map<String, Object>> rows, String kind) { return rows.stream().anyMatch(r -> kind.equals(r.get("kind"))); }

    @Test
    public void oneListWithNotesReasonsAndMoneyAndTheSecretarySeesNoMoney() throws Exception {
        as("test.director", "ROLE_DIRECTOR");
        LandProject p = project();
        landService.recordPayment(p.getId(), new BigDecimal("300000"), "x", null, "TITLE", null, null, "MOBILE_MONEY", "MP99");
        timeline.reason(p.getId(), "FEES_CAPITALIZED", "Storage fees added to the cost", "Client agreed", "UGX 150,000 added", true);
        timeline.event(p.getId(), "PROJECT_STATUS_CHANGED", "Stage ticked: Deed Plan", null, false);
        as("test.secretary", "ROLE_SECRETARY");
        notes.add(p.getId(), "Client will bring the ID copy on Monday.", "Waiting for client", LocalDate.now().plusDays(3), false, null);

        as("test.director", "ROLE_DIRECTOR");
        List<Map<String, Object>> all = entries(timeline.forProject(p.getId()));
        assertTrue(has(all, "MONEY") && has(all, "REASON") && has(all, "EVENT") && has(all, "NOTE"), all.toString());
        Map<String, Object> pay = all.stream().filter(r -> "MONEY".equals(r.get("kind"))).findFirst().orElseThrow();
        assertTrue(String.valueOf(pay.get("detail")).contains("Mobile Money (MP99)"), String.valueOf(pay.get("detail")));
        assertTrue(String.valueOf(pay.get("detail")).contains("UGX 300,000"));

        as("test.secretary", "ROLE_SECRETARY");
        List<Map<String, Object>> sec = entries(timeline.forProject(p.getId()));
        assertFalse(has(sec, "MONEY"), "the Secretary sees no payments");
        assertFalse(has(sec, "REASON"), "the money reason is hidden from the Secretary");
        assertTrue(has(sec, "EVENT") && has(sec, "NOTE"));
    }

    @Test
    public void onlyTheWriterOrAManagerChangesANoteAndRecordLinesNever() throws Exception {
        as("sec.one", "ROLE_SECRETARY");
        LandProject p = project();
        FollowUpLog n = notes.add(p.getId(), "First note", null, null, false, null);
        as("sec.two", "ROLE_SECRETARY");
        BusinessException e = assertThrows(BusinessException.class, () -> notes.edit(n.getId(), "Changed", null, null));
        assertTrue(e.getMessage().startsWith("NOTE_NOT_YOURS"), e.getMessage());
        notes.pin(n.getId(), true);   // anyone may pin
        assertTrue(noteRepository.findById(n.getId()).orElseThrow().getPinned());
        as("boss", "ROLE_MANAGER");
        notes.edit(n.getId(), "Changed by the manager", "Promise to pay", null);
        assertEquals("Promise to pay", noteRepository.findById(n.getId()).orElseThrow().getTopic());
        FollowUpLog record = noteRepository.save(FollowUpLog.builder().projectId(p.getId()).notes("[PROBLEM] Boundary dispute").recordedBy("boss").build());
        assertThrows(BusinessException.class, () -> notes.delete(record.getId()));
    }

    @Test
    public void aFollowUpDayCannotBeInThePast() {
        as("sec.one", "ROLE_SECRETARY");
        LandProject p = project();
        BusinessException e = assertThrows(BusinessException.class,
                () -> notes.add(p.getId(), "Call back", null, LocalDate.now().minusDays(1), false, null));
        assertTrue(e.getMessage().startsWith("FOLLOW_UP_IN_PAST"), e.getMessage());
    }

    @Test
    public void anOldAuditLineBecomesAFriendlyTimelineLine() {
        UUID id = UUID.randomUUID();
        TimelineEntry e = TimelineJobs.fromAudit("FEES_CAPITALIZED",
                "Operator [test.director] capitalized UGX 150000 of storage fees into total cost on #004A (total cost UGX 2000000 -> UGX 2150000). Reason: Client agreed to pay the fees with the title balance",
                Map.of("004A", id), Set.of(id));
        assertNotNull(e);
        assertEquals(id, e.getProjectId());
        assertEquals("Storage fees added to the cost", e.getTitle());
        assertEquals("Client agreed to pay the fees with the title balance", e.getReason());
        assertTrue(e.isMoney());
        assertFalse(e.getDetail().startsWith("Operator"), e.getDetail());

        TimelineEntry stage = TimelineJobs.fromAudit("PROJECT_STATUS_CHANGED",
                "Operator [x] marked status \"Deed Plan\" as COMPLETE on project: " + id, Map.of(), Set.of(id));
        assertEquals("Stage ticked: Deed Plan", stage.getTitle());
        assertNull(TimelineJobs.fromAudit("FEES_REDUCED", "reduced storage fees on #999Z", Map.of("004A", id), Set.of(id)), "an unknown project is skipped");
    }

    /** fix225 (David): a note about the client alone shows on the client page AND on each of the client's projects. */
    @Test
    public void aClientNoteShowsOnTheClientAndOnTheirProjects() {
        as("test.secretary", "ROLE_SECRETARY");
        LandProject p = project();
        Client c = p.billingParties().iterator().next();
        notes.addForClient(c.getId(), "Prefers calls after 5 pm.", "Call with client", null, true);

        List<Map<String, Object>> onClient = entries(timeline.forClient(c.getId()));
        Map<String, Object> row = onClient.stream().filter(r -> Boolean.TRUE.equals(r.get("clientNote"))).findFirst().orElseThrow();
        assertEquals("Prefers calls after 5 pm.", row.get("text"));
        assertEquals(Boolean.TRUE, row.get("pinned"));
        assertNull(row.get("projectId"));

        List<Map<String, Object>> onProject = entries(timeline.forProject(p.getId()));
        assertTrue(onProject.stream().anyMatch(r -> Boolean.TRUE.equals(r.get("clientNote"))), "the project shows its client's note");

        // it can be changed and deleted like any note (no project to check)
        UUID id = (UUID) row.get("id");
        notes.edit(id, "Prefers calls after 6 pm.", null, null);
        notes.delete(id, "Wrong details");
        assertTrue(entries(timeline.forClient(c.getId())).stream().noneMatch(r -> Boolean.TRUE.equals(r.get("clientNote"))));
    }
}
