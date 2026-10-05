package com.gesolutions.erp.modules.notification.repository;
import com.gesolutions.erp.modules.notification.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
public interface NotificationRepository extends JpaRepository<Notification, UUID> {
    // fix181 (17.0a, 17.5): exact role only (no "ALL"); nothing older than the person's notify_since (set on a rank change,
    // so a promoted person does not get the whole history of the new rank as unread)
    @Query("SELECT n FROM Notification n WHERE n.targetRole = :role AND n.createdAt >= :since ORDER BY n.createdAt DESC")
    List<Notification> findForRole(@Param("role") String role, @Param("since") LocalDateTime since);
    // fix181 (14.8): the list is cut IN the database (newest first) and unread is a COUNT, not everything in memory
    @Query("SELECT n FROM Notification n WHERE n.targetRole = :role AND n.createdAt >= :since ORDER BY n.createdAt DESC")
    List<Notification> findForRolePage(@Param("role") String role, @Param("since") LocalDateTime since, org.springframework.data.domain.Pageable page);
    @Query("SELECT COUNT(n) FROM Notification n WHERE n.targetRole = :role AND n.createdAt >= :since "
         + "AND NOT EXISTS (SELECT r FROM NotificationRead r WHERE r.notificationId = n.id AND r.userId = :userId)")
    long countUnread(@Param("role") String role, @Param("since") LocalDateTime since, @Param("userId") UUID userId);
    @org.springframework.data.jpa.repository.Modifying
    @Query("DELETE FROM Notification n WHERE n.createdAt < :before")
    int deleteOlderThan(@Param("before") LocalDateTime before);
    // fix181 (17.1): repeat checks always include the audience role
    boolean existsByTypeAndEntityIdAndTargetRole(String type, UUID entityId, String targetRole);
    boolean existsByTypeAndEntityIdAndTargetRoleAndCreatedAtAfter(String type, UUID entityId, String targetRole, LocalDateTime after);
    boolean existsByTypeAndDedupeKeyAndTargetRole(String type, String dedupeKey, String targetRole);
    // fix181 (17.7): the newest row of a type for one thing and role since a time (for grouping)
    java.util.Optional<Notification> findFirstByTypeAndEntityIdAndTargetRoleAndCreatedAtAfterOrderByCreatedAtDesc(String type, UUID entityId, String targetRole, LocalDateTime after);
}
