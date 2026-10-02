// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectStatusRequest.java
package com.gesolutions.erp.modules.land.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import java.math.BigDecimal;

/**
 * GE SOLUTIONS - PROJECT STATUS SELECTION (fix180: was ProjectStageRequest)
 *
 * One entry in the checklist a staff member submits when attaching statuses to a project. If statusTemplateId is
 * set, cost defaults to that template's defaultCost unless overridden here. If isCustom is true, statusTemplateId
 * is ignored and statusName/cost are used directly to create a one-off status.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProjectStatusRequest {

    private String statusTemplateId;
    private String statusName;
    private BigDecimal cost;
    private String notes;
    // fix167: both spellings of the flags are accepted
    @JsonProperty("isCustom")
    @JsonAlias({"custom"})
    private boolean isCustom;
    @JsonProperty("isCompleted")
    @JsonAlias({"completed"})
    private boolean isCompleted;
}
