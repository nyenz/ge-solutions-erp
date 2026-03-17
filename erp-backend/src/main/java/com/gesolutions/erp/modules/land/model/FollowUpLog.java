// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/FollowUpLog.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - ARCHIVE INTELLIGENCE LOG
 * Stores all qualitative notes, excuses, and recovery call results.
 * Supports 'Multiple Notes' from the Master Intake form.
 */
@Entity
@Table(name = "follow_up_logs")
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class FollowUpLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    /**
     * THE INTELLIGENCE: Detailed record of the interaction or status.
     */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String notes;

    /**
     * AUDIT ANCHOR: Captured from the security context (Admin/Manager).
     */
    @Column(name = "recorded_by", nullable = false, length = 100)
    private String recordedBy;

    @Builder.Default
    @Column(name = "timestamp", nullable = false, updatable = false)
    private LocalDateTime timestamp = LocalDateTime.now();
}