package com.gesolutions.erp.modules.notification.repository;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
public interface NotificationReadRepository extends JpaRepository<NotificationRead, UUID> {
    boolean existsByNotificationIdAndUserId(UUID notificationId, UUID userId);
    List<NotificationRead> findByUserId(UUID userId);
    // fix181 (14.8): read markers whose alert is gone (the 90-day cleanup)
    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.data.jpa.repository.Query("DELETE FROM NotificationRead r WHERE NOT EXISTS (SELECT n FROM Notification n WHERE n.id = r.notificationId)")
    int deleteOrphans();
}
