// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/StatusTemplate.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.util.UUID;

/**
 * GE SOLUTIONS - STATUS TEMPLATE (fix180: was StageTemplate / stage_templates)
 *
 * The master, reusable checklist of processing statuses with a default cost per status. fix180: every project type
 * (ProjectType) has its OWN ordered list; projectType holds the enum name. Rows with no project type are the old
 * global checklist and are switched off at boot.
 *
 * Only Admin, Manager and Director can add, rename or remove statuses (Secretary is data entry only) -- the
 * template edit endpoints are gated in StatusTemplateController / StatusTemplateService.
 *
 * Intentionally separate from ProjectStatus, which stores the actual per-project instance (with its own editable
 * cost, since the same status can cost different amounts on different projects).
 */
@Entity
@Table(name = "status_templates")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StatusTemplate {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "status_name", nullable = false, length = 200)
    private String statusName;

    // fix180: which project type this status belongs to (ProjectType enum name)
    @Column(name = "project_type", length = 40)
    private String projectType;

    @Builder.Default
    @Column(name = "default_cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal defaultCost = BigDecimal.ZERO;

    @Builder.Default
    @Column(name = "display_order", nullable = false)
    private Integer displayOrder = 0;

    /**
     * Soft-delete flag. Deactivated statuses stay in the DB (so historical ProjectStatus rows that reference them
     * by name remain meaningful) but no longer appear in the checklist offered at intake.
     */
    @Builder.Default
    @Column(name = "is_active", nullable = false)
    private boolean isActive = true;
}
