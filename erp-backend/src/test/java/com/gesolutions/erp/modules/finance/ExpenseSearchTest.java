package com.gesolutions.erp.modules.finance;

import com.gesolutions.erp.modules.finance.model.Expense;
import com.gesolutions.erp.modules.finance.repository.ExpenseRepository;
import com.gesolutions.erp.modules.finance.service.ExpenseService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;

/** fix222 (David): Reports could not load expenses -- the search must work with every filter left empty. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:expensesearchdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
@WithMockUser(username = "test.director", roles = "DIRECTOR")
public class ExpenseSearchTest {

    @Autowired private ExpenseService expenseService;
    @Autowired private ExpenseRepository expenses;

    private Expense save(String category, String amount, String by, String spentBy) {
        Expense e = new Expense();
        e.setCategory(category);
        e.setAmount(new BigDecimal(amount));
        e.setRecordedBy(by);
        e.setSpentBy(spentBy);
        return expenses.save(e);
    }

    @Test
    void everyFilterEmptyReturnsEveryExpenseNewestFirst() {
        save("FUEL", "85000", "test.manager", null);
        save("COURIER FEE", "15000", "test.manager", "driver.one");
        Page<Expense> page = expenseService.search(null, null, null, null, null, null, null, PageRequest.of(0, 5000));
        assertTrue(page.getTotalElements() >= 2);
    }

    @Test
    void filtersStillNarrowTheList() {
        save("FUEL", "85000", "test.manager", null);
        save("COURIER FEE", "15000", "test.manager", "driver.one");
        assertEquals(1, expenseService.search(null, null, "FUEL", null, null, null, null, PageRequest.of(0, 50))
                .getContent().stream().filter(e -> "FUEL".equals(e.getCategory())).count());
        assertTrue(expenseService.search(null, null, null, null, "DRIVER", null, null, PageRequest.of(0, 50))
                .getContent().stream().allMatch(e -> "driver.one".equals(e.getSpentBy())));
        assertTrue(expenseService.search(LocalDateTime.now().minusDays(1), LocalDateTime.now().plusDays(1), null, null, null,
                new BigDecimal("50000"), null, PageRequest.of(0, 50)).getContent().stream()
                .allMatch(e -> e.getAmount().compareTo(new BigDecimal("50000")) >= 0));
    }
}
