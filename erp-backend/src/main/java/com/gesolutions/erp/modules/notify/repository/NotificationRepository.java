// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/notify/repository/NotificationRepository.java
package com.gesolutions.erp.modules.notify.repository;

import com.gesolutions.erp.modules.notify.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.UUID;

@Repository
public interface NotificationRepository extends JpaRepository<Notification, UUID> {
    
    /**
     * Returns unread alerts for a specific security role.
     */
    List<Notification> findByTargetRoleAndIsReadFalse(String role);
}