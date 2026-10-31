package com.gesolutions.erp.modules.archive;

import com.gesolutions.erp.modules.archive.model.ArchivedItem;
import com.gesolutions.erp.modules.archive.repository.ArchivedItemRepository;
import com.gesolutions.erp.modules.archive.service.ArchiveService;
import com.gesolutions.erp.modules.finance.model.Expense;
import com.gesolutions.erp.modules.finance.repository.ExpenseRepository;
import com.gesolutions.erp.modules.finance.service.ExpenseService;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.service.NoteService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** fix284 (B1, David): a deleted expense or note is kept 90 days, can be put back, and is removed for good after that. */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:archiveditemdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
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
public class ArchivedItemTest {

    @Autowired private ExpenseService expenseService;
    @Autowired private ExpenseRepository expenses;
    @Autowired private NoteService noteService;
    @Autowired private FollowUpRepository notes;
    @Autowired private ArchiveService archiveService;
    @Autowired private ArchivedItemRepository archive;

    private ArchivedItem only(String kind) {
        List<ArchivedItem> l = archive.findAll().stream().filter(a -> kind.equals(a.getKind())).toList();
        assertEquals(1, l.size());
        return l.get(0);
    }

    @Test
    void deletedExpenseIsKeptAndComesBack() {
        Expense e = new Expense();
        e.setCategory("FUEL");
        e.setAmount(new BigDecimal("85000"));
        e.setRecordedBy("test.manager");
        e.setNote("Trip to Iganga");
        UUID id = expenses.save(e).getId();

        expenseService.deleteExpense(id, "typed twice");
        assertTrue(expenses.findById(id).isEmpty(), "the live row is gone");
        ArchivedItem a = only(ArchivedItem.EXPENSE);
        assertEquals("typed twice", a.getReason());
        assertTrue(a.getExpiresAt().isAfter(LocalDateTime.now().plusDays(89)));

        Map<String, Object> back = archiveService.restore(a.getId());
        Expense again = expenses.findById((UUID) back.get("id")).orElseThrow();
        assertEquals(0, new BigDecimal("85000").compareTo(again.getAmount()));
        assertEquals("FUEL", again.getCategory());
        assertEquals("test.manager", again.getRecordedBy());
        assertEquals("Trip to Iganga", again.getNote());
        assertTrue(archive.findAll().isEmpty(), "restored items leave the archive");
    }

    @Test
    void deletedNoteIsKeptAndComesBack() {
        FollowUpLog n = FollowUpLog.builder().notes("Client will pay on Friday").recordedBy("test.director")
                .timestamp(LocalDateTime.now().minusDays(2)).topic("MONEY").build();
        UUID id = notes.save(n).getId();

        noteService.delete(id, null);
        assertTrue(notes.findById(id).isEmpty());
        ArchivedItem a = only(ArchivedItem.NOTE);

        Map<String, Object> back = archiveService.restore(a.getId());
        FollowUpLog again = notes.findById((UUID) back.get("id")).orElseThrow();
        assertEquals("Client will pay on Friday", again.getNotes());
        assertEquals("MONEY", again.getTopic());
        assertEquals("test.director", again.getRecordedBy());
    }

    @Test
    void itemsOlderThan90DaysAreRemovedForGood() {
        Expense e = new Expense();
        e.setCategory("AIRTIME");
        e.setAmount(new BigDecimal("5000"));
        e.setRecordedBy("test.manager");
        expenseService.deleteExpense(expenses.save(e).getId(), null);
        ArchivedItem a = only(ArchivedItem.EXPENSE);
        a.setExpiresAt(LocalDateTime.now().minusMinutes(1));
        archive.save(a);

        assertEquals(1, archiveService.purgeExpired());
        assertTrue(archive.findAll().isEmpty());
    }
}
