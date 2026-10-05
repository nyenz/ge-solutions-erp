package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.client.service.RecoveryStateService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (20.10): the home page per rank, on the demo data. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:seedbooksdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
    "ge.solutions.seed-demo-data=true"
})
public class HomeDashboardTest {

    @Autowired private HomeDashboardService home;
    @Autowired private RecoveryStateService recovery;

    @Test
    public void managersAndSecretariesGetNoMoneyAndNoActivity() {
        for (Role r : List.of(Role.ROLE_MANAGER, Role.ROLE_SECRETARY)) {
            Map<String, Object> m = home.build(r);
            assertNull(m.get("money"), r + " must not get money");
            assertNull(m.get("periods"));
            assertNull(m.get("recentActivity"));
            assertEquals(HomeDashboardService.dashboardBlocks(r), m.get("blocks"));
        }
        Map<String, Object> d = home.build(Role.ROLE_DIRECTOR);
        assertNotNull(d.get("money"));
        assertNotNull(d.get("recentActivity"));
        assertNull(d.get("systemHealth"), "system health is the Admin's");
        assertNotNull(home.build(Role.ROLE_ADMIN).get("systemHealth"));
    }

    @Test
    @SuppressWarnings("unchecked")
    public void moneyStaysInsideItsLimitsAndTheTrendHasSixMonths() {
        Map<String, Object> money = (Map<String, Object>) home.build(Role.ROLE_DIRECTOR).get("money");
        double pct = ((Number) money.get("collectionPercent")).doubleValue();
        assertTrue(pct >= 0 && pct <= 100);
        assertTrue(((java.math.BigDecimal) money.get("titleArrears")).signum() >= 0);
        assertEquals(6, ((List<?>) money.get("trend")).size(), "every month is there, even with no payment");
    }

    @Test
    public void clientsDueForACallMatchesRecovery() {
        long due = ((Number) home.build(Role.ROLE_MANAGER).get("dueCalls")).longValue();
        assertEquals(recovery.dueNow(recovery.load(), LocalDateTime.now()), due);
    }
}
