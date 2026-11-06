package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.dto.PendingProjectDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectProblem;
import com.gesolutions.erp.modules.land.repository.ProjectProblemRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.ProjectStatusRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix289 (David): the Problems subsystem -- ticks, Other problems, same number, solutions, site visits, old flags. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:problemsdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class ProblemsTest {

    @Autowired private LandProjectRepository projects;
    @Autowired private ProjectProblemRepository problemRepo;
    @Autowired private UserRepository users;
    @Autowired private LandService land;
    @Autowired private ProblemService problems;
    @Autowired private com.gesolutions.erp.modules.client.repository.ClientRepository clientRepo;
    @Autowired private com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNotes;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private static String tag() { return UUID.randomUUID().toString().substring(0, 8).toUpperCase(); }

    private void as(Role role) {
        String name = role.name().toLowerCase() + "_" + tag();
        User u = users.save(User.builder().id(UUID.randomUUID()).username(name).email(name + "@t.co").password("x")
                .role(role).isRoot(false).isActive(true).mustChangePassword(false).sessionVersion(0).build());
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(u.getUsername(), null,
                List.of(new SimpleGrantedAuthority(role.name()))));
    }

    private LandEntryRequest entry(String nin) {
        LandEntryRequest r = new LandEntryRequest();
        r.setProjectType("FRESH_SURVEY");
        r.setDistrict("KAMULI"); r.setSubCounty("NAMWENDWA");
        r.setClients(new ArrayList<>(List.of(LandEntryRequest.OwnerRequest.builder().fullName("Problem Client " + nin).phone("0772405913").nationalId(nin).build())));
        r.setInvoiceNumber("P-INV-" + tag()); r.setContractNumber("P-CON-" + tag());
        r.setTotalCost(new BigDecimal("900000")); r.setInitialPayment(BigDecimal.ZERO);
        return r;
    }

    private static LandEntryRequest.ProblemRequest pr(String kind, String label, String nin) {
        return LandEntryRequest.ProblemRequest.builder().kind(kind).label(label).personNin(nin).build();
    }

    @Test
    public void ticksAndOtherProblemsArriveWithTheEntryAndRemember() throws Exception {
        as(Role.ROLE_SECRETARY);
        String nin = "PROBLEMCLIENT" + tag();
        LandEntryRequest r = entry(nin);
        r.getClients().get(0).setPhone(null);   // Phone missing
        r.setProblems(List.of(pr("NO_NIN", null, nin), pr("MISSING_PHONE", null, nin), pr("OTHER", "Wrong village on invoice " + tag().substring(0, 2), null)));
        LandProject p = land.atomicIntake(r, null);
        List<ProjectProblem> list = problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId());
        assertEquals(3, list.size(), "three problems came with the entry");
        ProjectProblem phone = list.stream().filter(x -> x.getKind().equals("MISSING_PHONE")).findFirst().orElseThrow();
        assertNotNull(phone.getClientId(), "a phone problem is tied to the person");
        assertEquals("SITE_VISIT", phone.getSolution(), "a missing phone needs a site visit by default");
        assertTrue(problems.remembered().stream().anyMatch(s -> s.startsWith("Wrong village on invoice")), "the Other words are remembered");
        assertTrue(problems.siteVisits().stream().anyMatch(v -> p.getId().equals(v.get("projectId"))), "it is on the Site Visits list");
    }

    @Test
    public void saveWithProblemWhenTheNumberIsAlreadyUsed() throws Exception {
        as(Role.ROLE_SECRETARY);
        LandEntryRequest a = entry("SAMEA" + tag());
        LandProject first = land.atomicIntake(a, null);
        LandEntryRequest b = entry("SAMEB" + tag());
        b.setContractNumber(a.getContractNumber());
        assertThrows(BusinessException.class, () -> land.atomicIntake(b, null), "without the choice it is refused as before");
        b.setAllowSameNumber(true);
        LandProject second = land.atomicIntake(b, null);
        assertEquals(a.getContractNumber(), second.getContractNumber(), "saved with the same contract number");
        assertTrue(problemRepo.findByProjectIdOrderByCreatedAtDesc(second.getId()).stream()
                .anyMatch(x -> x.getKind().equals("SAME_NUMBER") && first.getId().equals(x.getLinkedProjectId())), "the new one points at the old one");
        assertTrue(problemRepo.findByProjectIdOrderByCreatedAtDesc(first.getId()).stream()
                .anyMatch(x -> x.getKind().equals("SAME_NUMBER") && second.getId().equals(x.getLinkedProjectId())), "and the old one at the new one");
    }

    @Test
    public void aTitleDetailsProblemLetsAreaAndDateStayEmpty() throws Exception {
        as(Role.ROLE_SECRETARY);
        LandEntryRequest r = entry("TITLEP" + tag());
        r.setProjectType("LEGACY_TITLES");
        r.setPlotNumber("P" + tag()); r.setBlock("B" + tag().substring(0, 3));
        assertThrows(BusinessException.class, () -> land.atomicIntake(r, null), "without the problem the area is required");
        r.setProblems(List.of(pr("TITLE_DETAILS", null, null)));
        LandProject p = land.atomicIntake(r, null);
        assertNotNull(p.getLandTitle());
        assertNull(p.getLandTitle().getAreaHectares());
        assertTrue(problems.hasOpen(p.getId(), "TITLE_DETAILS"));
    }

    @Test
    public void solvingWritesTheNoteAndChangingTheSolutionWorks() throws Exception {
        as(Role.ROLE_SECRETARY);
        String nin = "SOLVE" + tag();
        LandEntryRequest r = entry(nin);
        r.setProblems(List.of(pr("NO_NIN", null, nin)));
        LandProject p = land.atomicIntake(r, null);
        ProjectProblem pp = problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId()).get(0);
        problems.update(pp.getId(), "SITE_VISIT", "ask at the village");
        assertEquals("SITE_VISIT", problemRepo.findById(pp.getId()).orElseThrow().getSolution());
        assertThrows(BusinessException.class, () -> problems.solve(pp.getId(), " "), "solving needs words");
        problems.solve(pp.getId(), "Client brought the ID");
        assertEquals("SOLVED", problemRepo.findById(pp.getId()).orElseThrow().getStatus());
        assertThrows(BusinessException.class, () -> problems.solve(pp.getId(), "again"), "solving twice is refused");
        assertTrue(problems.list("OPEN", p.getId(), null).isEmpty(), "no open problem is left");
    }

    @Test
    public void theOldProblemFlagShowsAsAFlaggedProblem() throws Exception {
        as(Role.ROLE_SECRETARY);
        LandProject p = land.atomicIntake(entry("FLAG" + tag()), null);
        p.setProblem(true); p.setProblemNote("Boundary dispute with neighbour"); projects.save(p);
        problems.bringOldFlags();
        assertTrue(problems.hasOpen(p.getId(), "FLAGGED"));
        problems.bringOldFlags();
        assertEquals(1, problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId()).stream().filter(x -> x.getKind().equals("FLAGGED")).count(), "brought once");
        ProjectProblem f = problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId()).stream().filter(x -> x.getKind().equals("FLAGGED")).findFirst().orElseThrow();
        problems.solve(f.getId(), "Agreed with the neighbour");
        assertFalse(projects.findById(p.getId()).orElseThrow().isProblem(), "solving it clears the old flag");
    }

    // ── fix291: solving with the real value ──

    @Test
    public void solvingNoNinAndMissingPhonePutsTheRealValuesOnTheClient() throws Exception {
        as(Role.ROLE_SECRETARY);
        String made = "MADENIN" + tag();
        LandEntryRequest r = entry(made);
        r.getClients().get(0).setPhone(null);
        r.setProblems(List.of(pr("NO_NIN", null, made), pr("MISSING_PHONE", null, made)));
        LandProject p = land.atomicIntake(r, null);
        List<ProjectProblem> list = problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId());
        ProjectProblem nin = list.stream().filter(x -> x.getKind().equals("NO_NIN")).findFirst().orElseThrow();
        ProjectProblem phone = list.stream().filter(x -> x.getKind().equals("MISSING_PHONE")).findFirst().orElseThrow();
        String real = "CM" + tag() + "AB";
        problems.solve(nin.getId(), null, java.util.Map.of("nin", real.toLowerCase()));
        assertTrue(clientRepo.findByNationalId(real).isPresent(), "the real NIN is on the client (in capitals)");
        assertTrue(clientRepo.findByNationalId(made).isEmpty(), "the made-up NIN is gone");
        assertTrue(problemRepo.findById(nin.getId()).orElseThrow().getSolvedNote().contains(real), "the note says what was put in");
        problems.solve(phone.getId(), "Got it from the LC1", java.util.Map.of("phone", "0772 405 999"));
        assertEquals("0772405999", clientRepo.findByNationalId(real).orElseThrow().getPhoneNumber().replaceAll("\\D", "").replaceFirst("^256", "0"));
        assertEquals("SOLVED", problemRepo.findById(phone.getId()).orElseThrow().getStatus());
    }

    @Test
    public void aNinOfAnotherClientIsRefusedAndNothingChanges() throws Exception {
        as(Role.ROLE_SECRETARY);
        String other = "OTHERNIN" + tag();
        land.atomicIntake(entry(other), null);
        String made = "MADEB" + tag();
        LandEntryRequest r = entry(made);
        r.setProblems(List.of(pr("NO_NIN", null, made)));
        LandProject p = land.atomicIntake(r, null);
        ProjectProblem nin = problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId()).get(0);
        assertThrows(BusinessException.class, () -> problems.solve(nin.getId(), null, java.util.Map.of("nin", other)));
        assertTrue(clientRepo.findByNationalId(made).isPresent(), "the client keeps its NIN");
        assertEquals("OPEN", problemRepo.findById(nin.getId()).orElseThrow().getStatus(), "the problem stays open");
    }

    @Test
    public void fixingTheSameNumberSolvesItOnBothProjects() throws Exception {
        as(Role.ROLE_SECRETARY);
        LandEntryRequest a = entry("SAMEX" + tag());
        LandProject first = land.atomicIntake(a, null);
        LandEntryRequest b = entry("SAMEY" + tag());
        b.setContractNumber(a.getContractNumber());
        b.setAllowSameNumber(true);
        LandProject second = land.atomicIntake(b, null);
        ProjectProblem mine = problemRepo.findByProjectIdOrderByCreatedAtDesc(second.getId()).stream().filter(x -> x.getKind().equals("SAME_NUMBER")).findFirst().orElseThrow();
        String fresh = "P-CON-NEW-" + tag();
        problems.solve(mine.getId(), null, java.util.Map.of("contract", fresh));
        assertEquals(fresh, projects.findById(second.getId()).orElseThrow().getContractNumber());
        assertFalse(problems.hasOpen(second.getId(), "SAME_NUMBER"), "solved here");
        assertFalse(problems.hasOpen(first.getId(), "SAME_NUMBER"), "and on the other project");
    }

    @Test
    public void visitDoneSolvesVisitProblemsAndWritesTheRecoveryNote() throws Exception {
        as(Role.ROLE_SECRETARY);
        String nin = "VISIT" + tag();
        LandEntryRequest r = entry(nin);
        r.setProblems(List.of(pr("LOCATION", null, null)));
        LandProject p = land.atomicIntake(r, null);
        assertTrue(problems.siteVisits().stream().anyMatch(v -> p.getId().equals(v.get("projectId"))));
        assertEquals(1, problems.siteVisitDone(p.getId(), "Plot is in Bugaya village, boundary marked"));
        assertFalse(problems.hasOpen(p.getId(), "LOCATION"));
        assertFalse(problems.siteVisits().stream().anyMatch(v -> p.getId().equals(v.get("projectId"))), "off the Site Visits list");
        var c = clientRepo.findByNationalId(nin).orElseThrow();
        assertTrue(recoveryNotes.findByClientOrderByCreatedAtDesc(c).stream()
                .anyMatch(n -> com.gesolutions.erp.modules.client.service.RecoveryStateService.VISIT_DONE_TAG.equals(n.getTag()) && !n.isCountsAsAttempt()),
                "a site visit line on Recovery that is not a call");
    }

    @Test
    public void missedCallsBeforeAVisitNoLongerAskForAnotherVisit() {
        var rs = new com.gesolutions.erp.modules.client.service.RecoveryStateService(null, null);
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        List<com.gesolutions.erp.modules.client.model.RecoveryNote> ns = new ArrayList<>();
        for (int d = 1; d <= 6; d++) ns.add(com.gesolutions.erp.modules.client.model.RecoveryNote.builder().tag("not picking up").tone("NEGATIVE")
                .countsAsAttempt(true).createdAt(now.minusDays(d + 2)).build());
        assertTrue(rs.siteVisit(ns, now), "six missed days: visit needed (as before)");
        ns.add(0, com.gesolutions.erp.modules.client.model.RecoveryNote.builder().tag(com.gesolutions.erp.modules.client.service.RecoveryStateService.VISIT_DONE_TAG)
                .tone("INFO").countsAsAttempt(false).createdAt(now.minusDays(1)).build());
        assertFalse(rs.siteVisit(ns, now), "after the visit the old misses do not count");
    }
}
