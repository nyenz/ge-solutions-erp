package com.gesolutions.erp.modules.notification.model;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;
@Entity
@Table(name = "notifications")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Notification {
    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    @Column(nullable = false, length = 60) private String type;
    @Column(nullable = false, length = 20) private String severity;
    @Column(columnDefinition = "TEXT", nullable = false) private String message;
    @Column(length = 20) private String entityType;
    private UUID entityId;
    @Column(nullable = false, length = 30) private String targetRole;
    @Column(name = "created_at", nullable = false) private LocalDateTime createdAt;
    // fix181 (17.2): the group of the type (MONEY, PIPELINE, RECOVERY, STAFF, SYSTEM), so counts can be made per group
    @Column(length = 20) private String category;
    // fix181 (17.14): the username who caused it (null for the nightly jobs); that person's own copy is written as read
    @Column(length = 100) private String actor;
    // fix181 (17.1): the repeat key for ONCE_PER_EVENT_DATE types (entity id + date)
    @Column(name = "dedupe_key", length = 120) private String dedupeKey;
}
