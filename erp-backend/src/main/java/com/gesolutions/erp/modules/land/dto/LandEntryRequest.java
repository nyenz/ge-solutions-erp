// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java
package com.gesolutions.erp.modules.land.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LandEntryRequest {

    private String plotNumber;
    private String tenure;
    private String blockRoad;
    private String district;
    private String county;
    private String volume;
    private String folio;
    private String instrumentNo;
    private String physicalBoxNumber;
    private LocalDate surveyDate;
    private LocalDate projectStartDate;
    private LocalDate titleIssueDate;

    @Builder.Default
    private List<OwnerRequest> owners = new ArrayList<>();

    private BigDecimal totalCost;
    private BigDecimal initialPayment;

    // Legacy fields -- kept to avoid breaking existing data, no longer used in new logic
    private BigDecimal weeklyInstallment;
    private String planType;

    @Builder.Default
    private List<NoteRequest> notes = new ArrayList<>();

    private Integer currentStageIndex;

    @JsonProperty("isLegacy")
    private boolean isLegacy;

    // Staff can flag a plot as backlog right at intake (for old/existing cases)
    @JsonProperty("isStartAsBacklog")
    private boolean isStartAsBacklog;

    private java.math.BigDecimal monthlyStorageFee;
    private java.math.BigDecimal initialStorageFee;

    // PHASE 4: Optional stage checklist selected at intake. If omitted,
    // no stages are attached and staff can add them later from the
    // Folder page once Phase 4B ships.
    @Builder.Default
    private List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> selectedStages = new ArrayList<>();

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
