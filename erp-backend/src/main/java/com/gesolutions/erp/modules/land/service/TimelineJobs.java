// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/TimelineJobs.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.TimelineEntry;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.TimelineEntryRepository;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * fix215 (David): the two background jobs of the Notes timeline.
 *  1. FOLLOW-UP REMINDER (07:00 Kampala, and once at start-up for today): a note whose follow-up day is today rings the
 *     bell of the Secretary, Manager and Director once (FOLLOW_UP_DUE). The alert never carries the note's words.
 *  2. ONE-TIME BACK-FILL: the reasons and events written before fix215 are copied from the audit trail into the
 *     timeline once (app_flags TIMELINE_BACKFILL_V1). Only lines that name their project (#index or its id) are copied.
 */
@Component
@RequiredArgsConstructor
public class TimelineJobs {

    private static final Logger log = LoggerFactory.getLogger(TimelineJobs.class);
    static final String BACKFILL_FLAG = "TIMELINE_BACKFILL_V1";

    private final FollowUpRepository noteRepository;
    private final LandProjectRepository projectRepository;
    private final TimelineEntryRepository entryRepository;
    private final NotificationService notificationService;
    private final JdbcTemplate jdbc;

    @EventListener(ApplicationReadyEvent.class)
    public void onStart() {
        try { backfillOnce(); } catch (RuntimeException e) { log.warn("[TIMELINE] back-fill skipped: {}", e.getMessage()); }
        try { remindToday(); } catch (RuntimeException e) { log.warn("[TIMELINE] reminder skipped: {}", e.getMessage()); }
    }

    @Scheduled(cron = "0 0 7 * * *", zone = "Africa/Kampala")
    public void remindToday() {
        LocalDate today = LocalDate.now();
        for (FollowUpLog n : noteRepository.findByFollowUpOn(today)) {
            LandProject p = projectRepository.findById(n.getProjectId()).orElse(null);
            if (p == null || p.isDeleted()) continue;
            notificationService.emitToAudience("FOLLOW_UP_DUE",
                    "Follow-up today on project #" + p.getProjectIndex() + " (note by " + n.getRecordedBy() + "). Open its Notes to read it.",
                    "PROJECT", p.getId(), today);
        }
    }

    // ── back-fill from the audit trail ──────────────────────────────────────

    /** code -> { title, kind, money } */
    private static final Map<String, String[]> CATALOG = new LinkedHashMap<>();
    static {
        CATALOG.put("RECEIVABLE_ENTER", new String[] { "Moved to receivables", "REASON", "1" });
        CATALOG.put("FEES_WAIVED", new String[] { "Storage fees waived", "REASON", "1" });
        CATALOG.put("FEES_CAPITALIZED", new String[] { "Storage fees added to the cost", "REASON", "1" });
        CATALOG.put("RECEIVABLE_SET_ASIDE", new String[] { "Set aside: storage fees stopped", "REASON", "1" });
        CATALOG.put("FEES_REDUCED", new String[] { "Storage fees reduced", "REASON", "1" });
        CATALOG.put("RECEIVABLE_SETTINGS", new String[] { "Storage fee rate or pause changed", "REASON", "1" });
        CATALOG.put("TITLE_REVERTED", new String[] { "Title details removed", "REASON", "0" });
        CATALOG.put("PROJECT_GRADUATED", new String[] { "Project started: prices set", "EVENT", "1" });
        CATALOG.put("PROJECT_NUMBERS_CHANGED", new String[] { "Invoice or contract number changed", "EVENT", "0" });
        CATALOG.put("SUBDIVISIONS_CHANGED", new String[] { "Number of plots changed", "EVENT", "0" });
        CATALOG.put("PROJECT_STATUS_CHANGED", new String[] { "Stage ticked", "EVENT", "0" });
        CATALOG.put("TITLE_FIELDS_CHANGED", new String[] { "Title details entered", "EVENT", "0" });
    }

    private static final Pattern INDEX = Pattern.compile("#([A-Za-z0-9]+)");
    private static final Pattern UUID_RE = Pattern.compile("([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})");
    private static final Pattern STAGE = Pattern.compile("marked status \"(.+?)\" as (COMPLETE|NOT COMPLETE)");

    void backfillOnce() {
        jdbc.execute("CREATE TABLE IF NOT EXISTS app_flags (name VARCHAR(60) PRIMARY KEY, set_at TIMESTAMP)");
        Integer done = jdbc.queryForObject("SELECT COUNT(*) FROM app_flags WHERE name = ?", Integer.class, BACKFILL_FLAG);
        if (done != null && done > 0) return;
        Map<String, UUID> byIndex = new HashMap<>();
        Set<UUID> ids = new HashSet<>();
        for (LandProject p : projectRepository.findAllIncludingPendingAndDeleted()) {
            if (p.getProjectIndex() != null) byIndex.put(String.valueOf(p.getProjectIndex()).toUpperCase(Locale.ROOT), p.getId());
            ids.add(p.getId());
        }
        String in = String.join(",", Collections.nCopies(CATALOG.size(), "?"));
        List<Map<String, Object>> lines = jdbc.queryForList(
                "SELECT id, action, details, performed_by, timestamp FROM audit_logs WHERE action IN (" + in + ")", CATALOG.keySet().toArray());
        int copied = 0;
        for (Map<String, Object> a : lines) {
            try {
                UUID auditId = a.get("id") instanceof UUID u ? u : UUID.fromString(String.valueOf(a.get("id")));
                if (entryRepository.existsBySourceAuditId(auditId)) continue;
                TimelineEntry e = fromAudit(String.valueOf(a.get("action")), String.valueOf(a.get("details")), byIndex, ids);
                if (e == null) continue;
                e.setSourceAuditId(auditId);
                e.setRecordedBy(a.get("performed_by") == null ? "SYSTEM" : String.valueOf(a.get("performed_by")));
                Object ts = a.get("timestamp");
                e.setCreatedAt(ts instanceof java.sql.Timestamp t ? t.toLocalDateTime() : ts instanceof LocalDateTime l ? l : LocalDateTime.now());
                entryRepository.save(e);
                copied++;
            } catch (RuntimeException ex) {
                log.warn("[TIMELINE] audit line not copied: {}", ex.getMessage());
            }
        }
        jdbc.update("INSERT INTO app_flags (name, set_at) VALUES (?, CURRENT_TIMESTAMP)", BACKFILL_FLAG);
        log.info("[TIMELINE] back-fill done: {} line(s) copied from the audit trail", copied);
    }

    /** One audit line -> one timeline line (null when it does not name a project we know). */
    static TimelineEntry fromAudit(String action, String details, Map<String, UUID> byIndex, Set<UUID> ids) {
        String[] c = CATALOG.get(action);
        if (c == null || details == null) return null;
        UUID project = null;
        Matcher u = UUID_RE.matcher(details);
        while (project == null && u.find()) { UUID x = UUID.fromString(u.group(1)); if (ids.contains(x)) project = x; }
        Matcher m = INDEX.matcher(details);
        while (project == null && m.find()) project = byIndex.get(m.group(1).toUpperCase(Locale.ROOT));
        if (project == null && "TITLE_REVERTED".equals(action)) {
            Matcher t = Pattern.compile("off project ([A-Za-z0-9]+)").matcher(details);
            if (t.find()) project = byIndex.get(t.group(1).toUpperCase(Locale.ROOT));
        }
        if (project == null) return null;
        String title = c[0];
        String reason = null;
        String detail = details;
        int r = detail.indexOf("Reason: ");
        if (r >= 0) { reason = detail.substring(r + 8).trim(); detail = detail.substring(0, r).trim(); }
        if ("PROJECT_STATUS_CHANGED".equals(action)) {
            Matcher s = STAGE.matcher(details);
            if (!s.find()) return null;
            title = ("COMPLETE".equals(s.group(2)) ? "Stage ticked: " : "Stage un-ticked: ") + s.group(1);
            detail = null;
        }
        if (detail != null) {
            detail = detail.replaceFirst("^Operator \\[[^\\]]*\\]\\s*", "").replaceFirst("^SYSTEM:\\s*", "").trim();
            if (detail.endsWith(".")) detail = detail.substring(0, detail.length() - 1);
            if (!detail.isEmpty()) detail = Character.toUpperCase(detail.charAt(0)) + detail.substring(1);
            if (detail.isEmpty()) detail = null;
        }
        return TimelineEntry.builder().projectId(project).kind(c[1]).action(action).title(title)
                .reason(reason == null || reason.isBlank() ? null : reason).detail(detail).money("1".equals(c[2])).build();
    }
}
