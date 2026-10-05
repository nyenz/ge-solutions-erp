package com.gesolutions.erp.modules.notification.controller;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import com.gesolutions.erp.modules.notification.repository.NotificationReadRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;
@RestController
@RequestMapping("/api/v1/notifications")
@RequiredArgsConstructor
public class NotificationController {
    private final NotificationRepository notifRepo;
    private final NotificationReadRepository readRepo;
    private final UserRepository userRepo;
    private User me(Authentication auth) { return userRepo.findByUsername(auth.getName()).orElse(null); }

    // fix181 (17.0b): the Employee has no bell (answer empty, not 403); nobody sees alerts older than notify_since
    private static boolean noBell(User u) { return u == null || u.getRole() == null || u.getRole() == com.gesolutions.erp.modules.auth.model.Role.ROLE_EMPLOYEE; }
    private static LocalDateTime since(User u) {
        return u.getNotifySince() != null ? u.getNotifySince() : LocalDateTime.of(2000, 1, 1, 0, 0);
    }
    private List<Notification> mine(User u) {
        return notifRepo.findForRolePage(u.getRole().name(), since(u), org.springframework.data.domain.PageRequest.of(0, MAX_ROWS));
    }
    // fix181 (17.14): the person who caused the alert reads "by you" instead of their own name
    private static String textFor(Notification n, User u) {
        String m = n.getMessage() == null ? "" : n.getMessage();
        if (n.getActor() != null && n.getActor().equalsIgnoreCase(u.getUsername())) m = m.replace("by " + n.getActor(), "by you");
        return m;
    }
    /**
     * fix71 -- THE N+1 THAT GREW WITH THE TABLE.
     *
     * This used to call existsByNotificationIdAndUserId() once PER ROW, so
     * opening the bell fired one query plus one per notification the role had
     * ever been sent -- and nothing ever deletes a notification, so that count
     * only goes up. After a few months in production it is thousands of round
     * trips to render a dropdown.
     *
     * The read markers for one user are now a single query into a Set, and the
     * list is capped: the bell shows the recent past, not the whole archive.
     */
    private static final int MAX_ROWS = 200;

    @GetMapping
    public List<Map<String, Object>> list(Authentication auth) {
        User u = me(auth);
        if (noBell(u)) return List.of();

        Set<UUID> readIds = readRepo.findByUserId(u.getId()).stream()
                .map(NotificationRead::getNotificationId)
                .collect(Collectors.toSet());

        List<Map<String, Object>> out = new ArrayList<>();
        for (Notification n : mine(u)) {
            if (out.size() >= MAX_ROWS) break;
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", n.getId()); m.put("type", n.getType()); m.put("severity", n.getSeverity());
            m.put("message", textFor(n, u)); m.put("category", n.getCategory()); m.put("entityType", n.getEntityType());
            m.put("entityId", n.getEntityId()); m.put("createdAt", n.getCreatedAt());
            m.put("read", readIds.contains(n.getId()));
            out.add(m);
        }
        return out;
    }
    @GetMapping("/unread-count")
    public Map<String, Long> unread(Authentication auth) {
        User u = me(auth);
        if (noBell(u)) return Map.of("unread", 0L);
        // Same N+1 as list() -- and this one runs on a timer for every signed-in
        // user, so it was the more expensive of the two.
        // fix181 (14.8): one COUNT query (the badge and the list now agree on the same alerts)
        return Map.of("unread", notifRepo.countUnread(u.getRole().name(), since(u), u.getId()));
    }
    @PostMapping("/{id}/read")
    public Map<String, Object> read(@PathVariable UUID id, Authentication auth) {
        User u = me(auth);
        if (u != null && !readRepo.existsByNotificationIdAndUserId(id, u.getId())) {
            readRepo.save(NotificationRead.builder().notificationId(id).userId(u.getId()).readAt(LocalDateTime.now()).build());
        }
        return Map.of("ok", true);
    }
    @PostMapping("/read-all")
    public Map<String, Object> readAll(Authentication auth) {
        User u = me(auth);
        if (noBell(u)) return Map.of("ok", false);
        Set<UUID> readIds = readRepo.findByUserId(u.getId()).stream()
                .map(NotificationRead::getNotificationId)
                .collect(Collectors.toSet());
        List<NotificationRead> toSave = new ArrayList<>();
        for (Notification n : notifRepo.findForRole(u.getRole().name(), since(u))) {
            if (!readIds.contains(n.getId())) {
                toSave.add(NotificationRead.builder()
                    .notificationId(n.getId()).userId(u.getId()).readAt(LocalDateTime.now()).build());
            }
        }
        // One batched write instead of one INSERT per unread row.
        if (!toSave.isEmpty()) readRepo.saveAll(toSave);
        return Map.of("ok", true);
    }
}
