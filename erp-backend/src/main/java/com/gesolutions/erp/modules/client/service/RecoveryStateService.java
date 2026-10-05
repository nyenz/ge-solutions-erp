// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/service/RecoveryStateService.java
package com.gesolutions.erp.modules.client.service;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * fix181 (4.3): THE Recovery rules, in one place. The Recovery page, the client pages, the Folder, the Dashboard,
 * the nightly unlock job and the reports all ask this service, so a client is in the same state everywhere.
 *
 * States: NEW, CONTACTED, MISSED, SITE, LOCKED.
 *  - LOCKED: paid in the last 30 days, or 2 good calls in the last 30 days (rest until 30 days after the 2nd).
 *  - SITE: SITE_VISIT_MISS_THRESHOLD missed calls (counted on DIFFERENT days, 4.1) in the last 30 days and no good call.
 *  - otherwise the NEWEST note decides (CONTACTED / MISSED); no notes = NEW.
 * REQUIREMENT: every note list given to this service is sorted NEWEST FIRST (noteRepo.findByClientOrderByCreatedAtDesc,
 * or load()). state() reads the newest note as element 0.
 *
 * Which projects count (4.4): never a Pending project, and not a project that graduated less than one month ago
 * (per project: an older overdue project of the same client is still chased).
 */
@Service
@RequiredArgsConstructor
public class RecoveryStateService {

    /** fix181 (4.1): missed calls (on different days, within 30 days, no good call) before a site visit. */
    public static final int SITE_VISIT_MISS_THRESHOLD = 4;
    public static final int REST_DAYS = 30;
    public static final int GRADUATION_DELAY_MONTHS = 1;

    /** Order of urgency for a project with several billing parties (4.3). */
    public static final List<String> URGENCY = List.of("SITE", "MISSED", "NEW", "CONTACTED", "LOCKED");

    private final RecoveryNoteRepository noteRepo;
    private final LandProjectRepository projectRepo;

    /** Notes (newest first) and live projects per client, read once. */
    public record Snapshot(Map<UUID, List<RecoveryNote>> notes, Map<UUID, List<LandProject>> projects) {
        public List<RecoveryNote> notesOf(UUID clientId) { return notes.getOrDefault(clientId, List.of()); }
        public List<LandProject> projectsOf(UUID clientId) { return projects.getOrDefault(clientId, List.of()); }
    }

    public Snapshot load() {
        return new Snapshot(notesByClient(), projectsByClient());
    }

    /** Every note per client, NEWEST FIRST. */
    public Map<UUID, List<RecoveryNote>> notesByClient() {
        Map<UUID, List<RecoveryNote>> nm = new HashMap<>();
        for (RecoveryNote n : noteRepo.findAllWithClient()) nm.computeIfAbsent(n.getClient().getId(), k -> new ArrayList<>()).add(n);
        for (List<RecoveryNote> l : nm.values()) l.sort((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()));
        return nm;
    }

    /** Live projects per billing party. findAll() already leaves out deleted and Pending projects. */
    public Map<UUID, List<LandProject>> projectsByClient() {
        Map<UUID, List<LandProject>> pm = new HashMap<>();
        for (LandProject p : projectRepo.findAll()) {
            if (p.isPending() || p.billingParties() == null) continue;
            for (Client o : p.billingParties()) if (o != null && o.getId() != null) pm.computeIfAbsent(o.getId(), k -> new ArrayList<>()).add(p);
        }
        return pm;
    }

    // ── which projects count ─────────────────────────────────────────────────

    public static boolean inGraduationDelay(LandProject p, LocalDateTime now) {
        return p.getGraduatedAt() != null && p.getGraduatedAt().plusMonths(GRADUATION_DELAY_MONTHS).isAfter(now);
    }

    /** A project Recovery may chase today. */
    public static boolean counts(LandProject p, LocalDateTime now) {
        return p != null && !p.isPending() && !p.isDeleted() && !inGraduationDelay(p, now);
    }

    public static BigDecimal owed(LandProject p) {
        return p.isReceivable() ? p.receivableTotalOwed() : p.activeTotalOwed();
    }

    /** On the Recovery list: owes money on at least one project that counts (fix173; kept fees are not chased). */
    public boolean qualifies(List<LandProject> ps, LocalDateTime now) {
        for (LandProject p : ps) if (counts(p, now) && owed(p).signum() > 0) return true;
        return false;
    }

    public LocalDateTime lastPayment(List<LandProject> ps, LocalDateTime now) {
        LocalDateTime newest = null;
        for (LandProject p : ps) {
            if (!counts(p, now) || p.getLastPaymentDate() == null) continue;
            if (newest == null || p.getLastPaymentDate().isAfter(newest)) newest = p.getLastPaymentDate();
        }
        return newest;
    }

    public String payBadge(List<LandProject> ps, LocalDateTime now) {
        LocalDateTime newest = lastPayment(ps, now);
        if (newest == null) return "RED";
        long d = ChronoUnit.DAYS.between(newest, now);
        return d <= 14 ? "GREEN" : d <= 30 ? "YELLOW" : "RED";
    }

    /** "new project - recovery starts <date>" when one of these projects is still in its first month after graduating. */
    public String delayNote(List<LandProject> ps, LocalDateTime now) {
        LocalDate starts = null;
        for (LandProject p : ps) {
            if (!inGraduationDelay(p, now)) continue;
            LocalDate d = p.getGraduatedAt().plusMonths(GRADUATION_DELAY_MONTHS).toLocalDate();
            if (starts == null || d.isBefore(starts)) starts = d;
        }
        return starts == null ? null : "new project - recovery starts " + starts;
    }

    // ── calls ────────────────────────────────────────────────────────────────

    private static boolean within30(RecoveryNote x, LocalDateTime now) {
        return x.getCreatedAt() != null && x.getCreatedAt().isAfter(now.minusDays(REST_DAYS));
    }

    public int succ30(List<RecoveryNote> ns, LocalDateTime now) {
        int n = 0;
        for (RecoveryNote x : ns) if ("POSITIVE".equals(x.getTone()) && x.isCountsAsAttempt() && within30(x, now)) n++;
        return n;
    }

    /** Missed calls in 30 days, counted per DAY (4.1): four quick clicks on one day are one missed day. */
    public long miss30(List<RecoveryNote> ns, LocalDateTime now) {
        Set<LocalDate> days = new HashSet<>();
        for (RecoveryNote x : ns) if ("NEGATIVE".equals(x.getTone()) && x.isCountsAsAttempt() && within30(x, now)) days.add(x.getCreatedAt().toLocalDate());
        return days.size();
    }

    public LocalDate lockedUntil(List<LandProject> ps, List<RecoveryNote> ns, LocalDateTime now) {
        LocalDate unlock = null;
        LocalDateTime pay = lastPayment(ps, now);
        if (pay != null && pay.plusDays(REST_DAYS).isAfter(now)) unlock = pay.plusDays(REST_DAYS).toLocalDate();
        int count = 0; LocalDateTime second = null;
        for (RecoveryNote x : ns) {
            if ("POSITIVE".equals(x.getTone()) && x.isCountsAsAttempt() && within30(x, now)) { count++; if (count == 2) second = x.getCreatedAt(); }
        }
        if (second != null) { LocalDate u2 = second.plusDays(REST_DAYS).toLocalDate(); if (unlock == null || u2.isAfter(unlock)) unlock = u2; }
        return unlock;
    }

    public boolean siteVisit(List<RecoveryNote> ns, LocalDateTime now) {
        return miss30(ns, now) >= SITE_VISIT_MISS_THRESHOLD && succ30(ns, now) == 0;
    }

    public String state(List<LandProject> ps, List<RecoveryNote> ns, LocalDateTime now) {
        if (lockedUntil(ps, ns, now) != null) return "LOCKED";
        if (siteVisit(ns, now)) return "SITE";
        if (ns.isEmpty()) return "NEW";
        if ("POSITIVE".equals(ns.get(0).getTone())) return "CONTACTED";
        if ("NEGATIVE".equals(ns.get(0).getTone())) return "MISSED";
        return "NEW";
    }

    public long dayMiss(List<RecoveryNote> ns, LocalDateTime now) {
        LocalDateTime oldest = null;
        for (RecoveryNote n : ns) if ("NEGATIVE".equals(n.getTone()) && n.isCountsAsAttempt() && within30(n, now)) oldest = n.getCreatedAt();
        if (oldest == null) return 0;
        return Math.min(30, ChronoUnit.DAYS.between(oldest, now));
    }

    // ── bulk ─────────────────────────────────────────────────────────────────

    /** State of a client, or null when the client is not on the Recovery list (owes nothing that counts). */
    public String clientState(Snapshot s, UUID clientId, LocalDateTime now) {
        List<LandProject> ps = s.projectsOf(clientId);
        if (!qualifies(ps, now)) return null;
        return state(ps, s.notesOf(clientId), now);
    }

    /** Every listed client's state in one pass. */
    public Map<UUID, String> clientStates(Snapshot s, LocalDateTime now) {
        Map<UUID, String> out = new HashMap<>();
        for (UUID id : s.projects().keySet()) {
            String st = clientState(s, id, now);
            if (st != null) out.put(id, st);
        }
        return out;
    }

    /** A project's Recovery state = the most urgent state among its billing parties (null = not chased). */
    public String projectState(Snapshot s, LandProject p, LocalDateTime now) {
        if (p == null || !counts(p, now) || owed(p).signum() <= 0 || p.billingParties() == null) return null;
        String best = null;
        for (Client c : p.billingParties()) {
            if (c == null || c.getId() == null) continue;
            String st = state(s.projectsOf(c.getId()), s.notesOf(c.getId()), now);
            if (best == null || URGENCY.indexOf(st) < URGENCY.indexOf(best)) best = st;
        }
        return best;
    }

    /** Clients a caller should phone now (NEW, CONTACTED or MISSED): the Recovery "due now" and the Dashboard tile. */
    public long dueNow(Snapshot s, LocalDateTime now) {
        return clientStates(s, now).values().stream()
                .filter(st -> st.equals("NEW") || st.equals("CONTACTED") || st.equals("MISSED")).count();
    }
}
