package com.gesolutions.erp.modules.client;

import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.service.RecoveryStateService;
import com.gesolutions.erp.modules.land.model.LandProject;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (4.1, 4.3, 4.4): the shared Recovery rules. */
public class RecoveryStateServiceTest {

    private final RecoveryStateService rs = new RecoveryStateService(null, null);
    private final LocalDateTime now = LocalDateTime.of(2026, 6, 15, 12, 0);

    private RecoveryNote call(boolean good, int daysAgo) {
        return RecoveryNote.builder().tone(good ? "POSITIVE" : "NEGATIVE").countsAsAttempt(true)
                .tag(good ? "answered call" : "not picking up").createdAt(now.minusDays(daysAgo).minusHours(1)).build();
    }

    /** newest first, as the service requires */
    private List<RecoveryNote> notes(RecoveryNote... ns) {
        List<RecoveryNote> l = new ArrayList<>(List.of(ns));
        l.sort((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()));
        return l;
    }

    private LandProject owing() {
        LandProject p = new LandProject();
        p.setTotalCost(new BigDecimal("1000000"));
        p.setAmountPaid(BigDecimal.ZERO);
        p.setReceivable(false);
        return p;
    }

    @Test
    public void fourMissedDaysMakeASiteVisitButNotFourClicksOnOneDay() {
        assertEquals(4, RecoveryStateService.SITE_VISIT_MISS_THRESHOLD);
        List<RecoveryNote> sameDay = notes(call(false, 2), call(false, 2), call(false, 2), call(false, 2));
        assertEquals(1, rs.miss30(sameDay, now));
        assertEquals("MISSED", rs.state(List.of(owing()), sameDay, now));

        List<RecoveryNote> three = notes(call(false, 20), call(false, 10), call(false, 2));
        assertEquals("MISSED", rs.state(List.of(owing()), three, now));

        List<RecoveryNote> four = notes(call(false, 25), call(false, 20), call(false, 10), call(false, 2));
        assertEquals("SITE", rs.state(List.of(owing()), four, now));

        List<RecoveryNote> fourAndAGoodOne = notes(call(false, 25), call(false, 20), call(true, 15), call(false, 10), call(false, 2));
        assertNotEquals("SITE", rs.state(List.of(owing()), fourAndAGoodOne, now), "one good call stops the site visit");
    }

    @Test
    public void theNewestNoteDecides() {
        assertEquals("CONTACTED", rs.state(List.of(owing()), notes(call(false, 9), call(true, 3)), now));
        assertEquals("MISSED", rs.state(List.of(owing()), notes(call(true, 9), call(false, 3)), now));
        assertEquals("NEW", rs.state(List.of(owing()), List.of(), now));
    }

    @Test
    public void twoGoodCallsOrARecentPaymentLock() {
        assertEquals("LOCKED", rs.state(List.of(owing()), notes(call(true, 9), call(true, 3)), now));
        LandProject paid = owing();
        paid.setLastPaymentDate(now.minusDays(5));
        assertEquals("LOCKED", rs.state(List.of(paid), List.of(), now));
    }

    @Test
    public void pendingAndNewlyGraduatedProjectsAreNotChased() {
        LandProject pending = owing();
        pending.setPending(true);
        assertFalse(rs.qualifies(List.of(pending), now));

        LandProject fresh = owing();
        fresh.setGraduatedAt(now.minusDays(10));
        assertFalse(rs.qualifies(List.of(fresh), now));
        assertNotNull(rs.delayNote(List.of(fresh), now));

        LandProject old = owing();
        assertTrue(rs.qualifies(List.of(fresh, old), now), "an older overdue project of the same client is still chased");

        fresh.setLastPaymentDate(now.minusDays(2));
        assertNull(rs.lastPayment(List.of(fresh, old), now), "a payment on the project in its first month does not lock the client");
    }
}
