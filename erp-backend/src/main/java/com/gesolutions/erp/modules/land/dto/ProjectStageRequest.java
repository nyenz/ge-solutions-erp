// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectStageRequest.java
package com.gesolutions.erp.modules.land.dto;

import lombok.*;
import java.math.BigDecimal;

/**
 * GE SOLUTIONS - PROJECT STAGE SELECTION (PHASE 4)
 *
 * One entry in the checklist a staff member submits when attaching stages
 * to a project. If stageTemplateId is set, cost defaults to that
 * template's defaultCost unless overridden here. If isCustom is true,
 * stageTemplateId is ignored and stageName/cost are used directly to
 * create a one-off stage.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProjectStageRequest {

    private String stageTemplateId;
    private String stageName;
    private BigDecimal cost;
    private String notes;
    private boolean isCustom;
    private boolean isCompleted;
}
