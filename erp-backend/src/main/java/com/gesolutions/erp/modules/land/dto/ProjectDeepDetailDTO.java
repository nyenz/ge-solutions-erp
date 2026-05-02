// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectDeepDetailDTO.java
package com.gesolutions.erp.modules.land.dto;

import com.gesolutions.erp.modules.land.model.*;
import lombok.*;
import java.math.BigDecimal;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProjectDeepDetailDTO {
    private LandProject project;
    private List<FollowUpLog> notes;
    private List<ProjectDocument> documents;
    private List<PaymentRecord> payments;
    private BigDecimal remainingBalance;
    private double collectionPercentage;
}