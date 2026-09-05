package com.gesolutions.erp.modules.notification.repository;
import com.gesolutions.erp.modules.notification.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
public interface NotificationRepository extends JpaRepository<Notification, UUID> {
    @Query("SELECT n FROM Notification n WHERE n.targetRole = 'ALL' OR n.targetRole = :role ORDER BY n.createdAt DESC")
    List<Notification> findForRole(@Param("role") String role);
    boolean existsByTypeAndEntityId(String type, UUID entityId);
    boolean existsByTypeAndEntityIdAndCreatedAtAfter(String type, UUID entityId, LocalDateTime after);
}
