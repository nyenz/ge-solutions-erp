package com.gesolutions.erp.modules.notification.controller;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import com.gesolutions.erp.modules.notification.repository.NotificationReadRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import com.gesolutions.erp.modules.notification.service.NotificationTypes;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * THE BELL.
 * fix181 (Sections 17 and 21): one summary call per tick; the list is cut in the database and paged by time; the
 * badge, the dots and the list count the same alerts (exact role, nothing older than notify_since); each row carries
 * its own link, worked out here for the person's rank (no link to a page they cannot open), and its day group and
 * age from the SERVER clock; READ is validated, safe against double clicks, and never marks alerts the person did not
 * have on screen (upTo). The Employee has no bell: empty answers with 200.
 */
@RestController
@RequestMapping("/api/v1/notifications")
@RequiredArgsConstructor
public class NotificationController {
    private final NotificationRepository notifRepo;
    private final NotificationReadRepository readRepo;
    private final UserRepository userRepo;
    private final com.gesolutions.erp.modules.client.service.RecoveryStateService recoveryState;
    private final com.gesolutions.erp.modules.land.service.WorkCountsService workCountsService;

    private static final int MAX_ROWS = 200;

    private User me(Authentication auth) { return userRepo.findByUsername(auth.getName()).orElse(null); }

    private static boolean noBell(User u) {
        return u == null || u.getRole() == null || u.getRole() == Role.ROLE_EMPLOYEE || u.isMustChangePassword();
    }
    private static LocalDateTime since(User u) {
        return u.getNotifySince() != null ? u.getNotifySince() : LocalDateTime.of(2000, 1, 1, 0, 0);
    }
    // fix181 (17.14): the person who caused the alert reads "by you" instead of their own name
    private static String textFor(Notification n, User u) {
        String m = n.getMessage() == null ? "" : n.getMessage();
        if (n.getActor() != null && n.getActor().equalsIgnoreCase(u.getUsername())) m = m.replace("by " + n.getActor(), "by you");
        return m;
    }
    private Set<UUID> readIds(User u) {
        return readRepo.findByUserId(u.getId()).stream().map(NotificationRead::getNotificationId).collect(Collectors.toSet());
    }

    /** fix181 (17.19a): only the ranks that make recovery calls see the "due now" row (Secretary, Manager, Director). */
    private static boolean seesDueNow(User u) {
        return u.getRole() == Role.ROLE_SECRETARY || u.getRole() == Role.ROLE_MANAGER || u.getRole() == Role.ROLE_DIRECTOR;
    }

    /** fix181 (21.6): the groups this rank can ever receive. */
    private static List<String> groupsFor(Role role) {
        LinkedHashSet<String> g = new LinkedHashSet<>();
        for (NotificationTypes.Type t : NotificationTypes.all().values()) if (t.audience().contains(role.name())) g.add(t.group().name());
        return new ArrayList<>(g);
    }

    /**
     * fix181 (17.10, 17.20): where a click on the alert goes, for THIS person. null = no link (the page is not theirs).
     */
    static String linkFor(Notification n, Role role) {
        boolean owner = role == Role.ROLE_ADMIN || role == Role.ROLE_DIRECTOR;
        String type = n.getType() == null ? "" : n.getType();
        UUID id = n.getEntityId();
        switch (type) {
            case "STORAGE_FEE_APPLIED" -> { if ("SYSTEM".equals(n.getEntityType())) return "/land/projects?tab=RECEIVABLES"; }
            case "PENDING_STALE" -> { return "/land/projects?tab=PENDING"; }
            case "BOOKS_MISMATCH" -> { return owner ? "/payments?books=1" : null; }
            case "JOB_FAILED", "LOGIN_BLOCKED", "SYSTEM_WIPE" -> { return owner ? "/audit" : null; }
            case "AUTO_RECEIVABLE_365" -> { if ("SYSTEM".equals(n.getEntityType())) return "/land/projects?tab=RECEIVABLES"; }
            default -> { }
        }
        if (id == null) return null;
        String et = n.getEntityType() == null ? "" : n.getEntityType();
        switch (et) {
            case "PROJECT" -> {
                if ("PENDING_CREATED".equals(type)) return "/pending/" + id;
                String hash = switch (type) {
                    case "PAYMENT_ON_RECEIVABLE", "PAYMENT_REVERSED", "RECEIVABLE_EXIT", "STORAGE_FEE_APPLIED", "FEES_REDUCED",
                         "COST_CHANGED", "STORAGE_FEE_RESUMED" -> "#payment";
                    case "DOC_UPLOADED" -> "#documents";
                    case "PROBLEM_FLAGGED", "PROBLEM_CLEARED" -> "#notes";
                    default -> "#overview";
                };
                return "/folder/" + id + hash;
            }
            case "CLIENT" -> {
                if (List.of("LOCKED", "UNLOCK", "UNLOCK_M", "SITE_VISIT_AUTO").contains(type)) return "/recovery?client=" + id;
                return "/client/" + id;
            }
            case "STAFF" -> { return owner ? "/settings?tab=staff" : null; }
            case "EXPENSE" -> { return role == Role.ROLE_SECRETARY ? null : "/financials"; }
            default -> { return null; }
        }
    }

    /** fix181 (21.8): the day group from the SERVER clock. */
    private static String dayBucket(LocalDateTime t, LocalDateTime now) {
        if (t == null) return "EARLIER";
        long d = ChronoUnit.DAYS.between(t.toLocalDate(), now.toLocalDate());
        return d <= 0 ? "TODAY" : d == 1 ? "YESTERDAY" : "EARLIER";
    }

    private Map<String, Object> row(Notification n, User u, Set<UUID> read, LocalDateTime now) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", n.getId()); m.put("type", n.getType()); m.put("severity", n.getSeverity());
        m.put("category", n.getCategory());
        m.put("message", textFor(n, u)); m.put("entityType", n.getEntityType());
        m.put("entityId", n.getEntityId()); m.put("createdAt", n.getCreatedAt());
        m.put("ageSeconds", n.getCreatedAt() == null ? null : Math.max(0, ChronoUnit.SECONDS.between(n.getCreatedAt(), now)));
        m.put("dayBucket", dayBucket(n.getCreatedAt(), now));
        m.put("link", linkFor(n, u.getRole()));
        m.put("read", read.contains(n.getId()));
        return m;
    }

    /** The list, newest first, cut in the database. `before` = the createdAt of the last row already shown (paging). */
    @GetMapping
    public List<Map<String, Object>> list(Authentication auth,
                                          @RequestParam(required = false) String before,
                                          @RequestParam(defaultValue = "200") int limit) {
        User u = me(auth);
        if (noBell(u)) return List.of();
        LocalDateTime now = LocalDateTime.now();
        int lim = Math.min(Math.max(limit, 1), MAX_ROWS);
        List<Notification> page;
        if (before != null && !before.isBlank()) {
            LocalDateTime b = LocalDateTime.parse(before);
            page = notifRepo.findForRole(u.getRole().name(), since(u)).stream()
                    .filter(n -> n.getCreatedAt().isBefore(b)).limit(lim).toList();
        } else {
            page = notifRepo.findForRolePage(u.getRole().name(), since(u), org.springframework.data.domain.PageRequest.of(0, lim));
        }
        Set<UUID> read = readIds(u);
        List<Map<String, Object>> out = new ArrayList<>();
        for (Notification n : page) out.add(row(n, u, read, now));
        return out;
    }

    /**
     * fix181 (17.6, 17.4, 21.6): ONE call per bell tick: unread (total, per group, critical), the groups this rank can
     * receive, total alerts in the list, "due now" (callers only, cached 60 s) and the server time.
     */
    @GetMapping("/summary")
    public Map<String, Object> summary(Authentication auth) {
        User u = me(auth);
        Map<String, Object> m = new LinkedHashMap<>();
        LocalDateTime now = LocalDateTime.now();
        m.put("serverTime", now);
        if (noBell(u)) {
            m.put("unread", 0L); m.put("unreadByGroup", Map.of()); m.put("unreadCritical", 0L);
            m.put("groups", List.of()); m.put("total", 0L); m.put("dueNow", null);
            return m;
        }
        Set<UUID> read = readIds(u);
        Map<String, Long> byGroup = new LinkedHashMap<>();
        long total = 0, unread = 0, critical = 0;
        for (Notification n : notifRepo.findForRole(u.getRole().name(), since(u))) {
            total++;
            if (read.contains(n.getId())) continue;
            unread++;
            if ("CRITICAL".equals(n.getSeverity())) critical++;
            byGroup.merge(n.getCategory() == null ? "SYSTEM" : n.getCategory(), 1L, Long::sum);
        }
        m.put("unread", unread);
        m.put("unreadByGroup", byGroup);
        m.put("unreadCritical", critical);
        m.put("groups", groupsFor(u.getRole()));
        m.put("total", total);
        m.put("dueNow", seesDueNow(u) ? recoveryState.dueNowCached() : null);
        return m;
    }

    /** fix181 (8.4, 17.6): the live work counts (Secretary and above). */
    @GetMapping("/work-counts")
    @org.springframework.security.access.prepost.PreAuthorize("hasAnyRole('ROLE_SECRETARY','ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    public Map<String, Object> workCounts() {
        return workCountsService.counts();
    }

    @GetMapping("/unread-count")
    public Map<String, Long> unread(Authentication auth) {
        User u = me(auth);
        if (noBell(u)) return Map.of("unread", 0L);
        return Map.of("unread", notifRepo.countUnread(u.getRole().name(), since(u), u.getId()));
    }

    /** fix181 (17.4d, 17.18a): the alert must exist and be addressed to the person's rank; a double click is harmless. */
    @PostMapping("/{id}/read")
    public Map<String, Object> read(@PathVariable UUID id, Authentication auth) {
        User u = me(auth);
        if (noBell(u)) return Map.of("ok", false);
        Notification n = notifRepo.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "No such alert"));
        if (!u.getRole().name().equals(n.getTargetRole())) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "No such alert");
        markRead(List.of(n.getId()), u);
        return Map.of("ok", true);
    }

    /**
     * fix181 (17.4(3), 17.18b, 21.2): ONE call marks a group read, and only alerts created at or before `upTo` (what the
     * person had on screen), so an alert that arrived after the list was loaded stays unread.
     */
    @PostMapping("/read-all")
    public Map<String, Object> readAll(Authentication auth,
                                       @RequestParam(required = false) String group,
                                       @RequestParam(required = false) String upTo) {
        User u = me(auth);
        if (noBell(u)) return Map.of("ok", false);
        LocalDateTime limit = upTo == null || upTo.isBlank() ? LocalDateTime.now() : LocalDateTime.parse(upTo);
        Set<UUID> read = readIds(u);
        List<UUID> toMark = new ArrayList<>();
        for (Notification n : notifRepo.findForRole(u.getRole().name(), since(u))) {
            if (read.contains(n.getId()) || n.getCreatedAt().isAfter(limit)) continue;
            if (group != null && !group.isBlank() && !"ALL".equalsIgnoreCase(group)
                    && !group.equalsIgnoreCase(n.getCategory() == null ? "SYSTEM" : n.getCategory())) continue;
            toMark.add(n.getId());
        }
        int marked = markRead(toMark, u);
        return Map.of("ok", true, "marked", marked);
    }

    private int markRead(List<UUID> ids, User u) {
        int n = 0;
        for (UUID id : ids) {
            try {
                if (readRepo.existsByNotificationIdAndUserId(id, u.getId())) continue;
                readRepo.save(NotificationRead.builder().notificationId(id).userId(u.getId()).readAt(LocalDateTime.now()).build());
                n++;
            } catch (org.springframework.dao.DataIntegrityViolationException dup) {
                // someone (another tab, a double click) marked it a moment ago: that is the wanted result
            }
        }
        return n;
    }
}
