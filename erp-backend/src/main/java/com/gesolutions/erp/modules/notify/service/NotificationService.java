// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/notify/service/NotificationService.java
package com.gesolutions.erp.modules.notify.service;

import com.gesolutions.erp.modules.notify.model.Notification;
import com.gesolutions.erp.modules.notify.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Objects;
import java.util.UUID;

/**
 * GE SOLUTIONS - SYSTEM ALERT HUB
 * Physically links alerts to specific Project/Folder IDs for immediate access.
 * Optimized for strict Null Type Safety.
 */
@Service
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationRepository repository;

    /**
     * BROADCAST TO MANAGERS:
     * Anchors a system message to a specific physical asset folder.
     */
    @Transactional
    public void alertManagers(@NonNull String msg, @NonNull UUID projectId) {
        // Explicit validation to clear IDE warnings
        String verifiedMsg = Objects.requireNonNull(msg);
        UUID verifiedProjectId = Objects.requireNonNull(projectId);

        Notification alert = Notification.builder()
                .message(verifiedMsg)
                .targetRole("ROLE_MANAGER")
                .projectId(verifiedProjectId) // Link established
                .isRead(false)
                .build();
        
        repository.save(Objects.requireNonNull(alert));
    }

    /**
     * SECURE READOUT:
     * Fetches unread alerts for the management console.
     */
    @Transactional(readOnly = true)
    public List<Notification> getUnreadNotifications() {
        return repository.findByTargetRoleAndIsReadFalse("ROLE_MANAGER");
    }

    /**
     * CLEAR STATUS:
     * Marks an alert as processed in the registry.
     */
    @Transactional
    public void markAsRead(@NonNull UUID id) {
        UUID verifiedId = Objects.requireNonNull(id);
        
        Notification notification = repository.findById(verifiedId)
                .orElseThrow(() -> new RuntimeException("INDUSTRIAL FAULT: Alert ID not found."));
        
        notification.setRead(true);
        repository.save(notification);
    }
}