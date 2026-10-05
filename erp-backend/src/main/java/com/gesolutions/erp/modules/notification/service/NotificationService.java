// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/notification/service/NotificationService.java
package com.gesolutions.erp.modules.notification.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import com.gesolutions.erp.modules.notification.repository.NotificationReadRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix181 (17.1, 17.2, 17.9, 17.14): every bell alert goes through here.
 *  - WHO gets it comes from NotificationTypes (one row per audience role); callers no longer pass a role.
 *  - It is written AFTER the main save is final (a payment that rolls back leaves no alert), in its own small
 *    transaction. emitNow() is only for alerts that must exist even when the request fails (LOGIN_BLOCKED, SYSTEM_WIPE).
 *  - It never throws: a failed alert must never undo, or look like it undid, the real action (17.21).
 *  - The person who caused it still gets the row (others of the same rank must see it) but already marked read.
 */
@Service
public class NotificationService {

    private final NotificationRepository repo;
    private final NotificationReadRepository readRepo;
    private final UserRepository userRepo;
    private final TransactionTemplate newTx;

    public NotificationService(NotificationRepository repo, NotificationReadRepository readRepo, UserRepository userRepo,
                               PlatformTransactionManager txManager) {
        this.repo = repo;
        this.readRepo = readRepo;
        this.userRepo = userRepo;
        this.newTx = new TransactionTemplate(txManager);
        this.newTx.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);
    }

    /** Alert for this type's audience, written once the current save is final. */
    public void emitToAudience(String type, String message, String entityType, UUID entityId) {
        emitToAudience(type, message, entityType, entityId, null);
    }

    /** eventDate: the date that makes a ONCE_PER_EVENT_DATE alert new (ignored by the other repeat rules). */
    public void emitToAudience(String type, String message, String entityType, UUID entityId, LocalDate eventDate) {
        String actor = currentActor();
        Runnable write = () -> write(type, message, entityType, entityId, eventDate, actor, LocalDateTime.now());
        try {
            if (TransactionSynchronizationManager.isSynchronizationActive()) {
                TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                    @Override public void afterCommit() { write.run(); }
                });
            } else {
                write.run();
            }
        } catch (Exception e) {
            System.err.println(">>> [NOTIFY] could not queue " + type + ": " + e.getMessage());
        }
    }

    /** Written at once, even if the request then fails. Only for LOGIN_BLOCKED and SYSTEM_WIPE. */
    public void emitNow(String type, String message, String entityType, UUID entityId) {
        write(type, message, entityType, entityId, null, currentActor(), LocalDateTime.now());
    }

    private void write(String type, String message, String entityType, UUID entityId, LocalDate eventDate,
                       String actor, LocalDateTime when) {
        try {
            NotificationTypes.Type t = NotificationTypes.of(type);
            if (t == null) {
                System.err.println(">>> [NOTIFY] unknown type " + type + " (add it to NotificationTypes)");
                return;
            }
            newTx.executeWithoutResult(status -> {
                User actorUser = actor == null ? null : userRepo.findByUsername(actor).orElse(null);
                String key = t.repeat() == NotificationTypes.Repeat.ONCE_PER_EVENT_DATE && entityId != null
                        ? entityId + "|" + (eventDate != null ? eventDate : when.toLocalDate()) : null;
                for (String role : t.audience()) {
                    if (t.repeat() == NotificationTypes.Repeat.GROUP_30_MIN && entityId != null) {
                        var recent = repo.findFirstByTypeAndEntityIdAndTargetRoleAndCreatedAtAfterOrderByCreatedAtDesc(type, entityId, role, when.minusMinutes(30));
                        if (recent.isPresent()) {
                            Notification r = recent.get();
                            r.setMessage(grouped(r.getMessage(), message));
                            repo.save(r);
                            continue;
                        }
                    }
                    if (isRepeat(t, entityId, key, role, when)) continue;
                    Notification n = repo.save(Notification.builder().type(type).severity(t.severity())
                            .message(message == null ? "" : message).entityType(entityType).entityId(entityId)
                            .targetRole(role).category(t.group().name()).actor(actor).dedupeKey(key)
                            .createdAt(when).build());
                    if (actorUser != null && actorUser.getRole() != null && role.equals(actorUser.getRole().name())) {
                        readRepo.save(NotificationRead.builder().notificationId(n.getId()).userId(actorUser.getId()).readAt(when).build());
                    }
                }
            });
        } catch (Exception e) {
            System.err.println(">>> [NOTIFY] could not write " + type + ": " + e.getMessage());
        }
    }

    private boolean isRepeat(NotificationTypes.Type t, UUID entityId, String key, String role, LocalDateTime when) {
        if (entityId == null) return false;
        return switch (t.repeat()) {
            case EVERY_TIME -> false;
            case ONCE_PER_ENTITY -> repo.existsByTypeAndEntityIdAndTargetRole(t.code(), entityId, role);
            case ONCE_PER_DAY -> repo.existsByTypeAndEntityIdAndTargetRoleAndCreatedAtAfter(t.code(), entityId, role, when.toLocalDate().atStartOfDay());
            case ONCE_PER_EVENT_DATE -> repo.existsByTypeAndDedupeKeyAndTargetRole(t.code(), key, role);
            case GROUP_30_MIN -> false;
        };
    }

    /** "3 document(s) attached to X by Y." + "2 document(s) ..." -> "5 document(s) attached to X by Y." */
    static String grouped(String old, String add) {
        try {
            int a = Integer.parseInt(old.trim().split("\\s+")[0]);
            int b = Integer.parseInt(add.trim().split("\\s+")[0]);
            return (a + b) + old.trim().substring(old.trim().indexOf(' '));
        } catch (Exception e) {
            return add;
        }
    }

    /** The signed-in username, or null for the nightly jobs and other system work. */
    private static String currentActor() {
        String op = AuditService.currentOperator();
        return op == null || "SYSTEM".equals(op) ? null : op;
    }
}
