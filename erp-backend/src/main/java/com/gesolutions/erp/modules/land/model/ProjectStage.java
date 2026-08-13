// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectStage.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PER-PROJECT STAGE INSTANCE (PHASE 4)
 *
 * A single stage attached to a specific project. Created either by copying
 * a StageTemplate entry (at intake or later), or as a one-off custom stage
 * added directly on a project via the "+" button per Section 17.5.
 *
 * Stores its own copy of stageName and cost rather than a foreign key to
 * StageTemplate, so that editing or deactivating the master template later
 * never changes numbers already committed on a live project.
 *
 * Stages can move backward (e.g. Approved -> Refused, then resubmitted) --
 * modeled here simply as isCompleted toggling back to false, matching
 * Section 17.5's requirement that "Refused is not final -- can be
 * resubmitted."
 */
@Entity
@Table(name = "project_stages", indexes = {
    @Index(name = "idx_project_stage_project", columnList = "project_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProjectStage {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "stage_name", nullable = false, length = 200)
    private String stageName;

    @Builder.Default
    @Column(name = "cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal cost = BigDecimal.ZERO;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    /**
     * True if this stage was added ad-hoc on this project via the "+"
     * button, rather than picked from the master StageTemplate checklist.
     */
    @Builder.Default
    @Column(name = "is_custom", nullable = false)
    private boolean isCustom = false;

    @Builder.Default
    @Column(name = "is_completed", nullable = false)
    private boolean isCompleted = false;

    @Builder.Default
    @Column(name = "display_order", nullable = false)
    private Integer displayOrder = 0;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
