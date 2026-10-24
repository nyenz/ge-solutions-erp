// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/TimelineService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentMethods;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.TimelineEntry;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.land.repository.TimelineEntryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;

/**
 * fix215 (David): THE Notes timeline -- one list, newest first, of everything that happened on a project (or on all
 * the projects of a client). It joins five sources, so nothing is written twice:
 *   NOTE   typed notes (follow_up_logs)                         -- may be pinned, carry a follow-up day, a topic, a file
 *   EVENT  the app's own lines (project_timeline kind EVENT, and the [PROBLEM] / [HANDED OVER] record notes)
 *   REASON every reason window (project_timeline kind REASON)  -- add fees to cost, pause, reduce, delete ...
 *   MONEY  every payment and reversal (payment_records), with its method and reference
 *   CALL   the Recovery calls of the project's clients (recovery_notes; the "payment received" line is left out: MONEY has it)
 * MONEY lines and app lines marked money are shown to the Manager and above only. Nothing here is ever edited, except
 * a typed note by its writer or a Manager+ (NoteService).
 */
@Service
@RequiredArgsConstructor
public class TimelineService {

    private final TimelineEntryRepository entryRepository;
    private final FollowUpRepository noteRepository;
    private final PaymentRecordRepository paymentRepository;
    private final RecoveryNoteRepository callRepository;
    private final LandProjectRepository projectRepository;
    private final ClientRepository clientRepository;

    // ── writing ─────────────────────────────────────────────────────────────

    /** A reason typed in a reason window. money = only the Manager and above see it. */
    public void reason(UUID projectId, String action, String title, String reason, String detail, boolean money) {
        write(projectId, "REASON", action, title, reason, detail, money);
    }

    /** Something the app did or saw happen. */
    public void event(UUID projectId, String action, String title, String detail, boolean money) {
        write(projectId, "EVENT", action, title, null, detail, money);
    }

    private void write(UUID projectId, String kind, String action, String title, String reason, String detail, boolean money) {
        if (projectId == null || title == null) return;
        try {
            entryRepository.save(TimelineEntry.builder().projectId(projectId).kind(kind).action(action)
                    .title(cut(title, 160)).reason(blankToNull(reason)).detail(blankToNull(detail)).money(money)
                    .recordedBy(operator()).createdAt(LocalDateTime.now()).build());
        } catch (RuntimeException e) {
            // the timeline is a mirror of the work: it must never stop the work itself (the audit trail still has the line)
            org.slf4j.LoggerFactory.getLogger(TimelineService.class).warn("[TIMELINE] line not written: {}", e.getMessage());
        }
    }

    // ── reading ─────────────────────────────────────────────────────────────

    /** The timeline of one project. */
    @Transactional(readOnly = true)
    public Map<String, Object> forProject(UUID projectId) {
        LandProject p = projectRepository.findById(projectId)
                .orElseThrow(() -> new com.gesolutions.erp.common.exception.BusinessException("PLOT_NOT_FOUND: This project no longer exists."));
        Set<Client> callPeople = new LinkedHashSet<>(p.billingParties());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entries", collect(List.of(p), callPeople));
        out.put("canSeeMoney", canSeeMoney());
        out.put("me", operator());
        out.put("canManage", canManage());
        return out;
    }

    /** The timeline of a client: every project they pay for, plus their own calls. */
    @Transactional(readOnly = true)
    public Map<String, Object> forClient(UUID clientId) {
        Client c = clientRepository.findById(clientId)
                .orElseThrow(() -> new com.gesolutions.erp.common.exception.BusinessException("CLIENT_NOT_FOUND: This client no longer exists."));
        List<LandProject> projects = projectRepository.findByBillingClient(clientId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entries", collect(projects, List.of(c)));
        List<Map<String, Object>> list = new ArrayList<>();
        for (LandProject p : projects) list.add(Map.of("id", p.getId(), "index", String.valueOf(p.getProjectIndex())));
        out.put("projects", list);
        out.put("canSeeMoney", canSeeMoney());
        out.put("me", operator());
        out.put("canManage", canManage());
        return out;
    }

    private List<Map<String, Object>> collect(List<LandProject> projects, Collection<Client> callPeople) {
        boolean money = canSeeMoney();
        boolean manage = canManage();
        String me = operator();
        Map<UUID, String> indexOf = new HashMap<>();
        for (LandProject p : projects) indexOf.put(p.getId(), String.valueOf(p.getProjectIndex()));
        List<Map<String, Object>> rows = new ArrayList<>();
        if (indexOf.isEmpty() && callPeople.isEmpty()) return rows;

        // typed notes and the record notes ([PROBLEM], [HANDED OVER] ...)
        if (!indexOf.isEmpty()) {
            for (FollowUpLog n : noteRepository.findByProjectIdInOrderByTimestampDesc(indexOf.keySet())) {
                if (n.getOwnerId() != null) continue;   // old per-owner contact lines belong to Recovery, not here
                String text = n.getNotes() == null ? "" : n.getNotes().trim();
                boolean record = LandService.isEvidenceNote(text);
                Map<String, Object> m = row("NOTE", record ? "EVENT" : "NOTE", n.getId(), n.getProjectId(), indexOf, n.getRecordedBy(), n.getTimestamp());
                if (record) {
                    int end = text.indexOf(']');
                    String tag = text.substring(1, Math.max(1, end)).trim();
                    m.put("title", switch (tag) {
                        case "PROBLEM" -> "Flagged as a problem";
                        case "PROBLEM CLEARED" -> "Problem cleared";
                        case "HANDED OVER" -> "Title handed over";
                        case "HAND-OVER UNDONE" -> "Hand-over undone";
                        default -> tag;
                    });
                    m.put("text", end > 0 ? text.substring(end + 1).trim() : text);
                    m.put("tone", "PROBLEM".equals(tag) || "HAND-OVER UNDONE".equals(tag) ? "bad" : "good");
                    m.put("locked", true);
                } else {
                    typedNote(m, n, text, manage, me);
                }
                rows.add(m);
            }
            // the app's own lines
            for (TimelineEntry e : entryRepository.findByProjectIdInOrderByCreatedAtDesc(indexOf.keySet())) {
                if (e.isMoney() && !money) continue;
                Map<String, Object> m = row("ENTRY", e.getKind(), e.getId(), e.getProjectId(), indexOf, e.getRecordedBy(), e.getCreatedAt());
                m.put("title", e.getTitle());
                m.put("text", e.getReason());
                m.put("detail", e.getDetail());
                m.put("money", e.isMoney());
                m.put("action", e.getAction());
                m.put("locked", true);
                rows.add(m);
            }
            // money
            if (money) {
                for (UUID pid : indexOf.keySet()) {
                    for (PaymentRecord r : paymentRepository.findByProjectIdOrderByTimestampDesc(pid)) rows.add(moneyRow(r, indexOf));
                }
            }
        }
        // fix225 (David): notes about the clients themselves (not about one project), marked CLIENT
        Map<UUID, Client> byId = new LinkedHashMap<>();
        for (Client c : callPeople) if (c != null && c.getId() != null) byId.put(c.getId(), c);
        if (!byId.isEmpty()) {
            for (FollowUpLog n : noteRepository.findByClientIdInOrderByTimestampDesc(byId.keySet())) {
                if (n.getProjectId() != null) continue;
                String text = n.getNotes() == null ? "" : n.getNotes().trim();
                Map<String, Object> m = row("NOTE", "NOTE", n.getId(), null, indexOf, n.getRecordedBy(), n.getTimestamp());
                typedNote(m, n, text, manage, me);
                Client c = byId.get(n.getClientId());
                m.put("clientNote", true);
                m.put("clientId", n.getClientId());
                m.put("clientName", c == null ? null : c.getFullName());
                rows.add(m);
            }
        }
        // calls
        for (Client c : callPeople) {
            for (RecoveryNote n : callRepository.findByClientOrderByCreatedAtDesc(c)) {
                if ("payment received".equalsIgnoreCase(n.getTag())) continue;
                Map<String, Object> m = row("CALL", "CALL", n.getId(), null, indexOf,
                        n.getAuthor() != null ? n.getAuthor().getUsername() : "SYSTEM", n.getCreatedAt());
                m.put("title", capital(n.getTag() == null ? "call" : n.getTag()));
                m.put("text", n.getText());
                m.put("detail", c.getFullName() + (n.getPromiseDate() != null ? " · promised for " + n.getPromiseDate() : ""));
                m.put("tone", "POSITIVE".equals(n.getTone()) ? "good" : "NEGATIVE".equals(n.getTone()) ? "bad" : "info");
                m.put("clientName", c.getFullName());
                m.put("locked", true);
                rows.add(m);
            }
        }
        rows.sort((a, b) -> {
            LocalDateTime x = (LocalDateTime) a.get("at"), y = (LocalDateTime) b.get("at");
            if (x == null || y == null) return x == null ? (y == null ? 0 : 1) : -1;
            return y.compareTo(x);
        });
        return rows;
    }

    private static void typedNote(Map<String, Object> m, FollowUpLog n, String text, boolean manage, String me) {
        m.put("title", n.getTopic() != null && !n.getTopic().isBlank() ? n.getTopic() : "Note");
        m.put("text", text);
        m.put("topic", n.getTopic());
        // fix241: a note pinned "only for me" shows pinned only to the person who pinned it
        boolean pinnedForAll = !"ME".equals(n.getPinFor());
        m.put("pinned", Boolean.TRUE.equals(n.getPinned()) && (pinnedForAll || (me != null && me.equalsIgnoreCase(n.getPinnedBy()))));
        m.put("pinFor", pinnedForAll ? "ALL" : "ME");
        m.put("remindFor", "ME".equals(n.getRemindFor()) ? "ME" : "ALL");
        m.put("followUpOn", n.getFollowUpOn());
        m.put("documentId", n.getDocumentId());
        m.put("edited", n.getEditedAt() != null);
        m.put("editable", manage || (me != null && me.equals(n.getRecordedBy())));
    }

    private Map<String, Object> moneyRow(PaymentRecord r, Map<UUID, String> indexOf) {
        LocalDateTime at = r.getPaidOn() != null ? r.getPaidOn() : r.getTimestamp();
        Map<String, Object> m = row("PAYMENT", "MONEY", r.getId(), r.getProjectId(), indexOf, r.getRecordedBy(), at);
        boolean reversal = "REVERSAL".equals(r.getPaymentType());
        boolean storage = "STORAGE".equals(r.getAllocation());
        String title = reversal ? "Payment reversed"
                : "INITIAL_DEPOSIT".equals(r.getPaymentType()) ? (storage ? "Storage fees paid before entry" : "Opening deposit")
                : storage ? "Storage fee payment" : "Payment received";
        m.put("title", title);
        String notes = r.getNotes() == null ? "" : r.getNotes().trim();
        if (reversal) notes = notes.replaceFirst("^\\[REVERSAL OF [^\\]]*\\]\\s*", "");
        if (notes.startsWith("Initial deposit at intake") || notes.startsWith("Storage fees already paid before entry") || "Payment received".equals(notes)) notes = "";
        m.put("text", notes.isEmpty() ? null : notes);
        List<String> bits = new ArrayList<>();
        bits.add(ugx(r.getAmountPaid()));
        bits.add(PaymentMethods.label(r.getPaymentMethod()) + (r.getPaymentReference() != null ? " (" + r.getPaymentReference() + ")" : ""));
        if (r.getPayerName() != null) bits.add("paid by " + r.getPayerName());
        if (r.getBalanceAfter() != null) bits.add("owed after " + ugx(r.getBalanceAfter()));
        m.put("detail", String.join(" · ", bits));
        m.put("amount", r.getAmountPaid());
        m.put("money", true);
        m.put("tone", reversal ? "bad" : "good");
        m.put("locked", true);
        return m;
    }

    private static Map<String, Object> row(String source, String kind, UUID id, UUID projectId, Map<UUID, String> indexOf, String by, LocalDateTime at) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", id);
        m.put("source", source);
        m.put("kind", kind);
        m.put("projectId", projectId);
        m.put("projectIndex", projectId == null ? null : indexOf.get(projectId));
        m.put("by", by);
        m.put("at", at);
        return m;
    }

    // ── small helpers ───────────────────────────────────────────────────────

    /** "UGX 1,250,000" (a minus sign for reversals) */
    public static String ugx(BigDecimal v) {
        if (v == null) return "UGX 0";
        return (v.signum() < 0 ? "-UGX " : "UGX ") + String.format(Locale.ROOT, "%,d", v.abs().setScale(0, java.math.RoundingMode.HALF_UP).longValue());
    }

    private static String capital(String s) {
        String t = s.trim();
        return t.isEmpty() ? t : Character.toUpperCase(t.charAt(0)) + t.substring(1);
    }

    private static String cut(String s, int max) { return s.length() > max ? s.substring(0, max) : s; }

    private static String blankToNull(String s) { return s == null || s.isBlank() ? null : s.trim(); }

    static String operator() {
        try {
            String who = AuditService.currentOperator();
            return who == null || who.isBlank() ? "SYSTEM" : who;
        } catch (RuntimeException e) {
            return "SYSTEM";
        }
    }

    private static boolean hasAny(String... roles) {
        Authentication a = SecurityContextHolder.getContext().getAuthentication();
        if (a == null) return false;
        Set<String> want = Set.of(roles);
        return a.getAuthorities().stream().anyMatch(g -> want.contains(g.getAuthority()));
    }

    /** Payments and money reasons: the Manager and above (the Secretary sees the work, not the money). */
    public static boolean canSeeMoney() { return hasAny("ROLE_MANAGER", "ROLE_DIRECTOR", "ROLE_ADMIN"); }

    /** May edit or delete anybody's typed note. */
    public static boolean canManage() { return hasAny("ROLE_MANAGER", "ROLE_DIRECTOR", "ROLE_ADMIN"); }
}
