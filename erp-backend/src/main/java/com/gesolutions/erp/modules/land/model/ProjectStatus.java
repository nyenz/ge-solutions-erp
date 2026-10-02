// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectStatus.java
package com.gesolutions.erp.modules.land.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PER-PROJECT STATUS INSTANCE (fix180: was ProjectStage / project_stages)
 *
 * A single status attached to a specific project. Created either by copying a StatusTemplate entry (at intake or
 * later), or as a one-off custom status added directly on a project via the "+" button.
 *
 * Stores its own copy of statusName and cost rather than a foreign key to StatusTemplate, so that editing or
 * deactivating the master template later never changes numbers already committed on a live project.
 *
 * Statuses can move backward (e.g. Approved -> Refused, then resubmitted) -- modeled simply as isCompleted
 * toggling back to false. fix180: documents can be attached to a status (ProjectDocument.statusId).
 */
@Entity
@Table(name = "project_statuses", indexes = {
    @Index(name = "idx_project_status_project", columnList = "project_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProjectStatus {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "status_name", nullable = false, length = 200)
    private String statusName;

    @Builder.Default
    @Column(name = "cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal cost = BigDecimal.ZERO;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    /** True if this status was added ad-hoc on this project via the "+" button, not picked from the master list. */
    @Builder.Default
    @JsonProperty("isCustom")
    @Column(name = "is_custom", nullable = false)
    private boolean isCustom = false;

    // fix167: sent to the page as "isCompleted" (Lombok alone named it "completed")
    @Builder.Default
    @JsonProperty("isCompleted")
    @Column(name = "is_completed", nullable = false)
    private boolean isCompleted = false;

    // fix167: who ticked the status (shown when hovering a ticked status on the folder page)
    @Column(name = "completed_by", length = 100)
    private String completedBy;

    @Builder.Default
    @Column(name = "display_order", nullable = false)
    private Integer displayOrder = 0;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
