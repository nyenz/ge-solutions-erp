// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java
package com.gesolutions.erp.modules.client.dto;

import lombok.*;
import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

/**
 * NYENZ ERP - RECOVERY MISSION OBJECT (V3 - ASSET CENTRIC)
 * 
 * Physically structured to represent a Plot and ALL its contactable owners.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RecoveryTaskDTO {

    private UUID projectId;
    private String plotNumber;
    private String physicalBoxNumber;

    // --- AGGREGATED IDENTITY ---
    private List<OwnerDetail> allOwners;
    private boolean isMultiAssetProprietor; // True if any owner has other plots

    // --- FINANCIAL DEMAND ---
    private BigDecimal weeklyRequirement;
    private BigDecimal totalArrears;

    // --- INTELLIGENCE ---
    private String lastInteractionNote;
    private String lastContactDate;
    private String nextCallDue; 
    private String missionStatus;
    private boolean isLocked;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OwnerDetail {
        private UUID id;
        private String name;
        private String phone; // Supports "/" characters
    }
}