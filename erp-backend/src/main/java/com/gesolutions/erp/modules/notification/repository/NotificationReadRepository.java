package com.gesolutions.erp.modules.notification.repository;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
public interface NotificationReadRepository extends JpaRepository<NotificationRead, UUID> {
    boolean existsByNotificationIdAndUserId(UUID notificationId, UUID userId);
    List<NotificationRead> findByUserId(UUID userId);
}
