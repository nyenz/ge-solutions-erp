// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/notify/model/Notification.java
package com.gesolutions.erp.modules.notify.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - SYSTEM ALERT MODEL
 * Stores industrial events and anchors them to specific digital folders.
 */
@Entity
@Table(name = "notifications")
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private String message;

    @Builder.Default
    @Column(name = "is_read", nullable = false)
    private boolean isRead = false;

    @Column(name = "target_role", length = 50)
    private String targetRole; // e.g. ROLE_MANAGER

    /**
     * FOLDER ANCHOR: Allows UI to navigate directly 
     * to the related land project folder.
     */
    @Column(name = "project_id")
    private UUID projectId;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}