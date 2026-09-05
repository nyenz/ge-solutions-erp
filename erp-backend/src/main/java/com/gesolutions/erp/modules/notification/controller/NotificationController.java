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
@RestController
@RequestMapping("/api/v1/notifications")
@RequiredArgsConstructor
public class NotificationController {
    private final NotificationRepository notifRepo;
    private final NotificationReadRepository readRepo;
    private final UserRepository userRepo;
    private User me(Authentication auth) { return userRepo.findByUsername(auth.getName()).orElse(null); }
    @GetMapping
    public List<Map<String, Object>> list(Authentication auth) {
        User u = me(auth);
        if (u == null) return List.of();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Notification n : notifRepo.findForRole(u.getRole().name())) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", n.getId()); m.put("type", n.getType()); m.put("severity", n.getSeverity());
            m.put("message", n.getMessage()); m.put("entityType", n.getEntityType());
            m.put("entityId", n.getEntityId()); m.put("createdAt", n.getCreatedAt());
            m.put("read", readRepo.existsByNotificationIdAndUserId(n.getId(), u.getId()));
            out.add(m);
        }
        return out;
    }
    @GetMapping("/unread-count")
    public Map<String, Long> unread(Authentication auth) {
        User u = me(auth);
        if (u == null) return Map.of("unread", 0L);
        long c = notifRepo.findForRole(u.getRole().name()).stream()
            .filter(n -> !readRepo.existsByNotificationIdAndUserId(n.getId(), u.getId())).count();
        return Map.of("unread", c);
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
        if (u == null) return Map.of("ok", false);
        for (Notification n : notifRepo.findForRole(u.getRole().name())) {
            if (!readRepo.existsByNotificationIdAndUserId(n.getId(), u.getId())) {
                readRepo.save(NotificationRead.builder().notificationId(n.getId()).userId(u.getId()).readAt(LocalDateTime.now()).build());
            }
        }
        return Map.of("ok", true);
    }
}
