package com.gesolutions.erp.modules.land;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.LandTitle;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.service.LandService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * fix181 (14.7a, 14.7c): the Archive list is a small summary with the reason and who deleted; a restore that would
 * clash with a live project on the same plot is refused unless forced; a Pending project comes back Pending.
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:archivedb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
@WithMockUser(username = "admin_root", roles = "ADMIN")
public class ArchiveRestoreTest {

    @Autowired private LandService landService;
    @Autowired private LandProjectRepository projects;

    private LandProject project(String index, String plot, boolean pending) {
        LandTitle t = new LandTitle();
        t.setPlotNumber(plot);
        t.setBlock("7");
        t.setTenure("MAILO");
        LandProject p = LandProject.builder().projectIndex(index).district("Wakiso").landTitle(t)
                .totalCost(BigDecimal.TEN).amountPaid(BigDecimal.ZERO).build();
        p.setPending(pending);
        return projects.save(p);
    }

    @Test
    public void restoreChecksForClashAndKeepsPending() {
        LandProject old = project("R001", "55", true);
        landService.nuclearDelete(old.getId(), "Entered twice by mistake");
        LandProject live = project("R002", " 55 ", false);

        List<Map<String, Object>> rows = landService.getDeletedProjects();
        Map<String, Object> row = rows.stream().filter(r -> old.getId().equals(r.get("id"))).findFirst().orElseThrow();
        assertEquals("Entered twice by mistake", row.get("reason"));
        assertEquals("admin_root", row.get("deletedBy"));
        assertEquals("55", row.get("plotLabel"));
        assertFalse(row.containsKey("totalCost"), "no prices in the Archive list");

        BusinessException e = assertThrows(BusinessException.class, () -> landService.restoreProject(old.getId(), false));
        assertTrue(e.getMessage().startsWith("RESTORE_CLASH"), e.getMessage());
        assertTrue(e.getMessage().contains("#R002"), e.getMessage());
        assertTrue(projects.findById(old.getId()).orElseThrow().isDeleted(), "nothing restored without force");

        landService.restoreProject(old.getId(), true);
        LandProject back = projects.findById(old.getId()).orElseThrow();
        assertFalse(back.isDeleted());
        assertTrue(back.isPending(), "a Pending project stays Pending after restore");
        assertNotNull(live.getId());
    }
}
