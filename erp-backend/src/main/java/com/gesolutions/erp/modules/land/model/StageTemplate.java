// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/StageTemplate.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.util.UUID;

/**
 * GE SOLUTIONS - STAGE TEMPLATE (PHASE 4)
 *
 * The master, reusable checklist of processing stages (Field Work, Deed Plan,
 * LC Inspection, District Land Board Approval, Tax Assessment and Stamp Duty,
 * Registration and Title Issuance) with a default cost per stage.
 *
 * Per Section 17.5: everyone EXCEPT Secretary can edit this master template
 * (add/remove/rename stages, change default costs). Secretary can only pick
 * from it at intake -- template edit endpoints are gated accordingly in
 * StageTemplateController / StageTemplateService.
 *
 * Intentionally separate from ProjectStage, which stores the actual
 * per-project instance (with its own editable cost, since the same stage
 * can cost different amounts on different projects).
 */
@Entity
@Table(name = "stage_templates")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StageTemplate {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "stage_name", nullable = false, length = 200)
    private String stageName;

    @Builder.Default
    @Column(name = "default_cost", nullable = false, precision = 15, scale = 2)
    private BigDecimal defaultCost = BigDecimal.ZERO;

    @Builder.Default
    @Column(name = "display_order", nullable = false)
    private Integer displayOrder = 0;

    /**
     * Soft-delete flag. Deactivated stages stay in the DB (so historical
     * ProjectStage rows that reference them by name remain meaningful) but
     * no longer appear in the checklist offered at intake.
     */
    @Builder.Default
    @Column(name = "is_active", nullable = false)
    private boolean isActive = true;
}
