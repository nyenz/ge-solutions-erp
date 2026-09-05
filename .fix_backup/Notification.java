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
}
