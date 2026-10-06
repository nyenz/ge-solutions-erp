package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
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
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix197 (David, Q4): a Fresh Survey ends through the "Titled" stage; every type goes to Receivables after 365 days. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:titledstagedb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class TitledStageTest {

    @Autowired private TitledStageService titled;
    @Autowired private StatusTemplateService stages;
    @Autowired private ReceivableSchedulerService jobs;
    @Autowired private LandProjectRepository projects;
    @Autowired private ProjectStatusRepository statuses;

    @AfterEach
    void clear() { SecurityContextHolder.clearContext(); }

    private static String tag() { return UUID.randomUUID().toString().substring(0, 8).toUpperCase(); }

    private void as(String role) {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("test." + role.toLowerCase(), null,
                List.of(new SimpleGrantedAuthority(role))));
    }

    private LandProject freshSurvey() {
        return projects.save(LandProject.builder().projectIndex("T" + tag().substring(0, 6)).projectType("FRESH_SURVEY")
                .totalCost(new BigDecimal("1000000")).amountPaid(BigDecimal.ZERO).pending(false).build());
    }

    private ProjectStatus stage(UUID projectId, String name, int order) {
        return statuses.save(ProjectStatus.builder().projectId(projectId).statusName(name).displayOrder(order).build());
    }

    private LandEntryRequest details(String plot) {
        return LandEntryRequest.builder().plotNumber(plot).block("BLOCK 12").areaHectares(new BigDecimal("0.25"))
                .tenure("MAILO").volume("LRV 9").folio("14").titleIssueDate(LocalDate.now().minusDays(3)).build();
    }

    @Test
    public void titledCannotBeTickedWithoutTitleDetails() {
        LandProject p = freshSurvey();
        ProjectStatus last = stage(p.getId(), "Titled", 5);
        as("ROLE_MANAGER");
        BusinessException e = assertThrows(BusinessException.class, () -> stages.toggleStatusCompletion(last.getId(), true));
        assertTrue(e.getMessage().startsWith("TITLE_DETAILS_REQUIRED"), e.getMessage());

        // every needed box is checked, and nothing is saved by a refused try
        assertThrows(BusinessException.class, () -> titled.completeTitled(p.getId(), last.getId(), null));
        LandEntryRequest noBlock = details("PLOT-" + tag()); noBlock.setBlock(" ");
        assertThrows(BusinessException.class, () -> titled.completeTitled(p.getId(), last.getId(), noBlock));
        LandEntryRequest noArea = details("PLOT-" + tag()); noArea.setAreaHectares(BigDecimal.ZERO);
        assertThrows(BusinessException.class, () -> titled.completeTitled(p.getId(), last.getId(), noArea));
        LandEntryRequest noDate = details("PLOT-" + tag()); noDate.setTitleIssueDate(null);
        assertThrows(BusinessException.class, () -> titled.completeTitled(p.getId(), last.getId(), noDate));
        LandEntryRequest future = details("PLOT-" + tag()); future.setTitleIssueDate(LocalDate.now().plusDays(2));
        assertThrows(BusinessException.class, () -> titled.completeTitled(p.getId(), last.getId(), future));
        assertFalse(statuses.findById(last.getId()).orElseThrow().isCompleted());
        assertNull(projects.findById(p.getId()).orElseThrow().getLandTitle());
    }

    @Test
    public void aFreshSurveyGetsItsTitleOnTheTitledStageAndCanThenBeHandedOver() {
        LandProject p = freshSurvey();
        ProjectStatus first = stage(p.getId(), "Field Measurement", 0);
        ProjectStatus last = stage(p.getId(), "Titled", 5);
        String plot = "PLOT-" + tag();

        as("ROLE_EMPLOYEE");
        assertThrows(AccessDeniedException.class, () -> titled.completeTitled(p.getId(), last.getId(), details(plot)));
        as("ROLE_SECRETARY");
        assertThrows(BusinessException.class, () -> titled.completeTitled(p.getId(), first.getId(), details(plot)), "only on the Titled stage");

        titled.completeTitled(p.getId(), last.getId(), details(plot));
        LandProject saved = projects.findById(p.getId()).orElseThrow();
        assertNotNull(saved.getLandTitle());
        assertEquals(plot, saved.getLandTitle().getPlotNumber());
        assertEquals("MAILO", saved.getLandTitle().getTenure());
        assertTrue(saved.isTitleDetailsEnabled());
        assertTrue(statuses.findById(last.getId()).orElseThrow().isCompleted());
        // not paid yet: the hand-over is still blocked by the money, no longer by a missing title
        assertNotNull(saved.releaseBlocker());

        // the stage can be unticked and ticked again the normal way now that the details exist
        as("ROLE_MANAGER");
        assertFalse(stages.toggleStatusCompletion(last.getId(), false).isCompleted());
        assertTrue(stages.toggleStatusCompletion(last.getId(), true).isCompleted());

        // the same plot number cannot go onto a second project
        LandProject other = freshSurvey();
        ProjectStatus otherLast = stage(other.getId(), "Titled", 5);
        BusinessException e = assertThrows(BusinessException.class, () -> titled.completeTitled(other.getId(), otherLast.getId(), details(plot)));
        assertTrue(e.getMessage().startsWith("PLOT_TAKEN"), e.getMessage());
    }

    @Test
    public void aProjectWithoutATitleGoesToReceivablesAfter365UnpaidDays() {
        LandProject old = projects.save(LandProject.builder().projectIndex("T" + tag().substring(0, 6)).projectType("FRESH_SURVEY")
                .totalCost(new BigDecimal("1000000")).amountPaid(new BigDecimal("200000")).pending(false)
                .createdAt(LocalDateTime.now().minusDays(400)).build());
        LandProject young = projects.save(LandProject.builder().projectIndex("T" + tag().substring(0, 6)).projectType("FRESH_SURVEY")
                .totalCost(new BigDecimal("1000000")).amountPaid(BigDecimal.ZERO).pending(false)
                .createdAt(LocalDateTime.now().minusDays(100)).build());
        LandProject paid = projects.save(LandProject.builder().projectIndex("T" + tag().substring(0, 6)).projectType("SPECIAL_PROJECTS")
                .totalCost(new BigDecimal("1000000")).amountPaid(new BigDecimal("1000000")).pending(false)
                .createdAt(LocalDateTime.now().minusDays(400)).build());

        jobs.autoFlagStaleAsReceivable();

        assertTrue(projects.findById(old.getId()).orElseThrow().isReceivable(), "old, unpaid, no title: now found");
        assertFalse(projects.findById(young.getId()).orElseThrow().isReceivable(), "not a year old yet");
        assertFalse(projects.findById(paid.getId()).orElseThrow().isReceivable(), "nothing owed");
    }
}
