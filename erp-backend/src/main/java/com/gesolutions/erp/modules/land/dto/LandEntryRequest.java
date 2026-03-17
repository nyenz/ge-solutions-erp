// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java
package com.gesolutions.erp.modules.land.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * GE SOLUTIONS - MASTER INTAKE & OVERRIDE DTO
 * 
 * Synchronized with PostgreSQL Schema.
 * Includes weeklyInstallment to resolve the LandService compilation error.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LandEntryRequest {

    /* --- CLUSTER 1: TECHNICAL SPECIFICATIONS --- */
    private String plotNumber;
    private String tenure;
    private String blockRoad;
    private String district;
    private String county;
    private String volume;
    private String folio;
    private String instrumentNo;
    private String physicalBoxNumber;

    /* --- CLUSTER 2: PROPRIETOR IDENTITIES --- */
    @Builder.Default
    private List<OwnerRequest> owners = new ArrayList<>();

    /* --- CLUSTER 3: FINANCIAL HARDWARE --- */
    private BigDecimal totalCost;
    private BigDecimal initialPayment;
    private BigDecimal weeklyInstallment; // FIXED: Added missing field
    private String planType;

    /* --- CLUSTER 4: CASE INTELLIGENCE (NOTES) --- */
    @Builder.Default
    private List<NoteRequest> notes = new ArrayList<>();

    /* --- CLUSTER 5: PROTOCOL STAGE & LEGACY --- */
    private Integer currentStageIndex;
    
    @JsonProperty("isLegacy")
    private boolean isLegacy;

    /* --- NESTED INDUSTRIAL SCHEMAS --- */

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OwnerRequest {
        private String fullName;
        private String phone;
        private String email;
        private String nationalId;
        private String address;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class NoteRequest {
        private UUID id;
        private String content;
    }
}