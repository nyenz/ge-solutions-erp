package com.gesolutions.erp.modules.notification.model;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;
@Entity
@Table(name = "notification_reads", uniqueConstraints = @UniqueConstraint(columnNames = {"notification_id", "user_id"}))
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class NotificationRead {
    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    @Column(name = "notification_id", nullable = false) private UUID notificationId;
    @Column(name = "user_id", nullable = false) private UUID userId;
    @Column(name = "read_at") private LocalDateTime readAt;
}
