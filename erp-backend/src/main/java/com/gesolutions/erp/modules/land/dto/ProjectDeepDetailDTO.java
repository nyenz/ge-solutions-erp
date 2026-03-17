// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectDeepDetailDTO.java
package com.gesolutions.erp.modules.land.dto;

import com.gesolutions.erp.modules.land.model.*;
import lombok.*;
import java.math.BigDecimal;
import java.util.List;

/**
 * GE SOLUTIONS - DEEP DETAIL BINDER
 * 
 * Consolidates all 5 Industrial Clusters into one object for the Command Console.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProjectDeepDetailDTO {
    // Cluster 1, 2, 3: The Project & Identity Core
    private LandProject project;

    // Cluster 4: The Intelligence Stream (Full History of Notes)
    private List<FollowUpLog> notes;

    // Cluster 4: The Digital Vault (List of all Scans/PDFs)
    private List<ProjectDocument> documents;

    // Cluster 5: Financial Diagnostics (Calculated Arrears)
    private BigDecimal remainingBalance;
    private double collectionPercentage;
}