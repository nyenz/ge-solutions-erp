package com.gesolutions.erp.modules.notification.service;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;
@Service
@RequiredArgsConstructor
public class NotificationService {
    private final NotificationRepository repo;
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void emit(String type, String severity, String message, String entityType, UUID entityId, String targetRole) {
        if (type == null || entityId == null) return;
        if (repo.existsByTypeAndEntityId(type, entityId)) return;
        repo.save(Notification.builder().type(type).severity(severity).message(message)
            .entityType(entityType).entityId(entityId).targetRole(targetRole)
            .createdAt(LocalDateTime.now()).build());
    }
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void emitRaw(String type, String severity, String message, String entityType, UUID entityId, String targetRole) {
        repo.save(Notification.builder().type(type).severity(severity).message(message)
            .entityType(entityType).entityId(entityId).targetRole(targetRole)
            .createdAt(LocalDateTime.now()).build());
    }
    @Transactional(readOnly = true)
    public boolean existsToday(String type, UUID entityId) {
        return repo.existsByTypeAndEntityIdAndCreatedAtAfter(type, entityId, LocalDate.now().atStartOfDay());
    }
}
