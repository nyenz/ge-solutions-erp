package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.dto.PendingProjectDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectStatus;
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

/** fix196: the invoice number and the contract number, and the rules of the Invoice / Contract stage. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:projectnumbersdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class ProjectNumbersTest {

    private static final String IC = "Invoice / Contract Number";

    @Autowired private ProjectNumbersService numbers;
    @Autowired private PendingProjectService pending;
    @Autowired private StatusTemplateService stages;
    @Autowired private LandProjectRepository projects;
    @Autowired private ProjectStatusRepository statuses;
    @Autowired private UserRepository users;
    @Autowired private LandService land;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private static String tag() { return UUID.randomUUID().toString().substring(0, 8).toUpperCase(); }

    private User as(Role role) {
        String name = role.name().toLowerCase() + "_" + tag();
        User u = users.save(User.builder().id(UUID.randomUUID()).username(name).email(name + "@t.co").password("x")
                .role(role).isRoot(false).isActive(true).mustChangePassword(false).sessionVersion(0).build());
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(u.getUsername(), null,
                List.of(new SimpleGrantedAuthority(role.name()))));
        return u;
    }

    private LandEntryRequest entry() {
        LandEntryRequest r = new LandEntryRequest();
        r.setProjectType("FRESH_SURVEY");
        r.setDistrict("WAKISO");
        r.setClients(new ArrayList<>(List.of(LandEntryRequest.OwnerRequest.builder()
                .fullName("Numbers Client").phone("0772405913").nationalId("CM" + tag() + tag().substring(0, 2)).build())));
        return r;
    }

    private LandEntryRequest start(String invoice, String contract) {
        LandEntryRequest r = new LandEntryRequest();
        r.setTotalCost(new BigDecimal("1000000"));
        r.setInitialPayment(BigDecimal.ZERO);
        r.setInvoiceNumber(invoice);
        r.setContractNumber(contract);
        return r;
    }

    /** A started project from before fix196: no numbers yet. */
    private LandProject oldProject() {
        return projects.save(LandProject.builder().projectIndex("N" + tag().substring(0, 6))
                .totalCost(new BigDecimal("1000000")).amountPaid(BigDecimal.ZERO).pending(false).build());
    }

    private ProjectStatus stage(UUID projectId, String name, int order) {
        return statuses.save(ProjectStatus.builder().projectId(projectId).statusName(name).displayOrder(order).build());
    }

    @Test
    public void aProjectStaysPendingUntilBothNumbersAndAPriceAreGiven() throws Exception {
        as(Role.ROLE_EMPLOYEE);
        PendingProjectDTO dto = pending.createPending(entry(), null, null);
        ProjectStatus ic = stage(dto.getId(), IC, 1);
        as(Role.ROLE_SECRETARY);
        String inv = "INV/2026/" + tag(), con = "GS-CON " + tag();

        BusinessException e = assertThrows(BusinessException.class, () -> pending.graduatePending(dto.getId(), start(null, null)));
        assertTrue(e.getMessage().startsWith("NUMBERS_REQUIRED"), e.getMessage());
        assertThrows(BusinessException.class, () -> pending.graduatePending(dto.getId(), start(inv, "  ")));
        assertThrows(BusinessException.class, () -> pending.graduatePending(dto.getId(), start("", con)));
        LandEntryRequest noPrice = start(inv, con);
        noPrice.setTotalCost(BigDecimal.ZERO);
        assertThrows(BusinessException.class, () -> pending.graduatePending(dto.getId(), noPrice));
        assertTrue(projects.findById(dto.getId()).orElseThrow().isPending(), "still Pending after every refused try");
        assertNull(projects.findById(dto.getId()).orElseThrow().getInvoiceNumber());

        pending.graduatePending(dto.getId(), start("  " + inv + " ", con));
        LandProject p = projects.findById(dto.getId()).orElseThrow();
        assertFalse(p.isPending());
        assertEquals(inv, p.getInvoiceNumber(), "saved trimmed, in the format that was typed");
        assertEquals(con, p.getContractNumber());
        assertTrue(statuses.findById(ic.getId()).orElseThrow().isCompleted(), "the Invoice / Contract stage is ticked by itself");
    }

    /** fix199 (David, test notes 9 + 12): the parts are saved one at a time; the project starts when all three are in. */
    @Test
    public void partsAreSavedOneAtATimeAndTheProjectStartsWhenAllThreeAreIn() throws Exception {
        as(Role.ROLE_EMPLOYEE);
        PendingProjectDTO dto = pending.createPending(entry(), null, null);
        ProjectStatus ic = stage(dto.getId(), IC, 1);
        as(Role.ROLE_SECRETARY);
        String inv = "P-INV-" + tag(), con = "P-CON-" + tag();

        LandEntryRequest priceOnly = new LandEntryRequest();
        priceOnly.setTotalCost(new BigDecimal("2500000"));
        assertEquals(false, pending.saveParts(dto.getId(), priceOnly).get("started"));
        LandProject p = projects.findById(dto.getId()).orElseThrow();
        assertTrue(p.isPending(), "a price alone keeps it Pending");
        assertEquals(0, new BigDecimal("2500000").compareTo(p.getTotalCost()));

        LandEntryRequest withMoney = new LandEntryRequest();
        withMoney.setInvoiceNumber(inv);
        withMoney.setInitialPayment(new BigDecimal("100000"));
        BusinessException e = assertThrows(BusinessException.class, () -> pending.saveParts(dto.getId(), withMoney));
        assertTrue(e.getMessage().startsWith("MONEY_NEEDS_START"), e.getMessage());

        LandEntryRequest invoiceOnly = new LandEntryRequest();
        invoiceOnly.setInvoiceNumber(inv);
        assertEquals(false, pending.saveParts(dto.getId(), invoiceOnly).get("started"));
        assertEquals(inv, projects.findById(dto.getId()).orElseThrow().getInvoiceNumber());
        assertTrue(projects.findById(dto.getId()).orElseThrow().isPending());

        LandEntryRequest contractOnly = new LandEntryRequest();
        contractOnly.setContractNumber(con);
        assertEquals(true, pending.saveParts(dto.getId(), contractOnly).get("started"), "the third part starts it");
        p = projects.findById(dto.getId()).orElseThrow();
        assertFalse(p.isPending());
        assertEquals(inv, p.getInvoiceNumber());
        assertEquals(con, p.getContractNumber());
        assertEquals(0, new BigDecimal("2500000").compareTo(p.getTotalCost()));
        assertTrue(statuses.findById(ic.getId()).orElseThrow().isCompleted());
    }

    /** fix199 (David, test note 12): an office New Project with a missing part is saved as Pending, not refused. */
    @Test
    public void anOfficeEntryWithAMissingPartIsSavedAsPending() throws Exception {
        as(Role.ROLE_SECRETARY);
        LandEntryRequest r = entry();
        r.setInvoiceNumber("O-INV-" + tag());
        r.setTotalCost(new BigDecimal("900000"));
        LandProject saved = land.atomicIntake(r, null);
        assertTrue(saved.isPending(), "no contract number yet, so it waits as Pending");
        assertNotNull(saved.getInvoiceNumber());
        assertNull(saved.getContractNumber());

        LandEntryRequest paid = entry();
        paid.setTotalCost(new BigDecimal("900000"));
        paid.setInitialPayment(new BigDecimal("100000"));
        BusinessException e = assertThrows(BusinessException.class, () -> land.atomicIntake(paid, null));
        assertTrue(e.getMessage().startsWith("MONEY_NEEDS_START"), e.getMessage());
    }

    @Test
    public void eachNumberIsOnOneProjectOnly() throws Exception {
        as(Role.ROLE_EMPLOYEE);
        PendingProjectDTO a = pending.createPending(entry(), null, null);
        PendingProjectDTO b = pending.createPending(entry(), null, null);
        as(Role.ROLE_SECRETARY);
        String inv = "inv-" + tag(), con = "con-" + tag();
        pending.graduatePending(a.getId(), start(inv, con));

        BusinessException e = assertThrows(BusinessException.class, () -> pending.graduatePending(b.getId(), start(inv.toUpperCase(), "con-" + tag())));
        assertTrue(e.getMessage().startsWith("INVOICE_NUMBER_TAKEN"), e.getMessage());
        e = assertThrows(BusinessException.class, () -> pending.graduatePending(b.getId(), start("inv-" + tag(), con.toUpperCase())));
        assertTrue(e.getMessage().startsWith("CONTRACT_NUMBER_TAKEN"), e.getMessage());
        assertTrue(projects.findById(b.getId()).orElseThrow().isPending());

        // a deleted project does not hold its numbers
        LandProject first = projects.findById(a.getId()).orElseThrow();
        first.setDeleted(true);
        projects.save(first);
        pending.graduatePending(b.getId(), start(inv, con));
        assertEquals(inv, projects.findById(b.getId()).orElseThrow().getInvoiceNumber());
    }

    @Test
    public void everyRankExceptEmployeeCanCorrectTheNumbers() {
        LandProject old = oldProject();
        ProjectStatus ic = stage(old.getId(), IC, 0);
        String inv = "A-" + tag(), con = "B-" + tag();

        as(Role.ROLE_EMPLOYEE);
        assertThrows(AccessDeniedException.class, () -> numbers.correct(old.getId(), inv, con));

        as(Role.ROLE_SECRETARY);
        assertThrows(BusinessException.class, () -> numbers.correct(old.getId(), inv, null), "both are needed");
        numbers.correct(old.getId(), inv, con);
        LandProject p = projects.findById(old.getId()).orElseThrow();
        assertEquals(inv, p.getInvoiceNumber());
        assertEquals(con, p.getContractNumber());
        assertTrue(statuses.findById(ic.getId()).orElseThrow().isCompleted());

        // saving a project's own numbers again is not a clash; a Manager changes one of them
        as(Role.ROLE_MANAGER);
        numbers.correct(old.getId(), inv, con);
        numbers.correct(old.getId(), inv + "-X", con);
        assertEquals(inv + "-X", projects.findById(old.getId()).orElseThrow().getInvoiceNumber());
    }

    @Test
    public void theStageCannotBeTickedWithoutNumbersNorRemovedNorOvertaken() {
        LandProject old = oldProject();
        ProjectStatus field = stage(old.getId(), "Field Measurement", 0);
        ProjectStatus ic = stage(old.getId(), IC, 1);
        ProjectStatus later = stage(old.getId(), "Area Land Committee", 2);

        as(Role.ROLE_MANAGER);
        BusinessException e = assertThrows(BusinessException.class, () -> stages.toggleStatusCompletion(ic.getId(), true));
        assertTrue(e.getMessage().startsWith("NUMBERS_REQUIRED"), e.getMessage());
        assertTrue(stages.toggleStatusCompletion(later.getId(), true).isCompleted(), "other stages tick as before");

        e = assertThrows(BusinessException.class, () -> stages.reorderProjectStatuses(old.getId(), List.of(later.getId(), field.getId(), ic.getId())));
        assertTrue(e.getMessage().startsWith("STAGE_ORDER_BLOCKED"), e.getMessage());
        assertEquals(IC, statuses.findByProjectIdOrderByDisplayOrderAsc(old.getId()).get(1).getStatusName(), "the order did not change");
        // the stage that was already above may stay; moving a stage BELOW is fine
        ProjectStatus last = stage(old.getId(), "Titled", 3);
        stages.reorderProjectStatuses(old.getId(), List.of(field.getId(), ic.getId(), last.getId(), later.getId()));
        assertEquals("Titled", statuses.findByProjectIdOrderByDisplayOrderAsc(old.getId()).get(2).getStatusName());

        as(Role.ROLE_DIRECTOR);
        e = assertThrows(BusinessException.class, () -> stages.removeProjectStatus(ic.getId()));
        assertTrue(e.getMessage().startsWith("STAGE_LOCKED"), e.getMessage());
        stages.removeProjectStatus(last.getId());
        assertTrue(statuses.findById(ic.getId()).isPresent());
        assertTrue(statuses.findById(last.getId()).isEmpty());
    }

    @Test
    public void theHelpersReadNamesAndNumbersTheSameWayAsThePage() {
        assertTrue(ProjectNumbersService.isInvoiceContractStage("Invoice / Contract Number"));
        assertTrue(ProjectNumbersService.isInvoiceContractStage("CONTRACT AND INVOICE"));
        assertFalse(ProjectNumbersService.isInvoiceContractStage("Progressive Invoice"));
        assertFalse(ProjectNumbersService.isInvoiceContractStage(null));
        assertEquals("INV 12 / 2026", ProjectNumbersService.clean("  INV   12 / 2026 "));
        assertNull(ProjectNumbersService.clean("   "));
    }
}
