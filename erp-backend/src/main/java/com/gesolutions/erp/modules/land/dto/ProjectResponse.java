// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectResponse.java
package com.gesolutions.erp.modules.land.dto;

import com.gesolutions.erp.modules.land.model.TenureType;
import lombok.*;
import java.math.BigDecimal;
import java.util.UUID;

/**
 * GE SOLUTIONS - PROJECT READOUT DTO
 * Optimized for the 'Digital Folder' view on the frontend.
 * Provides a clean summary of an asset and its owners.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProjectResponse {

    private UUID projectId;
    private String plotNumber;
    private String titleStatus;
    private String subCounty;
    private String parish;
    private String village;
    private String titleId;
    
    // ENUM TYPE: Resolved the "cannot be resolved" error
    private TenureType tenure;

    /* --- FINANCIAL SUMMARY --- */
    private BigDecimal totalCost;
    private BigDecimal amountPaid;
    
    @Builder.Default
    private double paymentPercentage = 0.0;
    
    @Builder.Default
    private String status = "ACTIVE";

    /* --- IDENTITY SUMMARY --- */
    private String primaryProprietorName;
    private int jointOwnerCount;

    /* --- SYSTEM METADATA --- */
    @Builder.Default
    private boolean isReleased = false;
    
    @Builder.Default
    private boolean isLegacy = false;
}