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

    // fix180: the project type (ProjectType name). Missing = worked out from isLegacy (old pages).
    private String projectType;
    // fix180: Topographic Survey only -- the optional Title Details panel is switched on
    @JsonProperty("titleDetailsEnabled")
    private boolean titleDetailsEnabled;
    // fix180: Subdivision only -- how many plots the subdivision creates
    private Integer subdivisionCount;
    // fix180: a Transfer of Title started from a subdivision plot (the subdivision project and the plot number)
    private UUID parentProjectId;
    private Integer parentSubdivisionNo;

    // TITLE DETAILS (fix180: Plot Number, Block, Area in hectares, Volume, Folio; Title ID removed)
    private String plotNumber;
    private String tenure;
    private String block;
    private BigDecimal areaHectares;
    private String volume;
    private String folio;
    private String district;
    private String county;
    private String subCounty;
    private String parish;
    private String village;
    private String area;
    private LocalDate projectStartDate;
    private LocalDate titleIssueDate;

    // fix180: CLIENTS first, then OWNERS. Owners left empty = a copy of the clients.
    @Builder.Default
    private List<OwnerRequest> clients = new ArrayList<>();

    @Builder.Default
    private List<OwnerRequest> owners = new ArrayList<>();

    // fix180: NEIGHBORS panel (every project type)
    @Builder.Default
    private List<NeighborRequest> neighbors = new ArrayList<>();

    private BigDecimal totalCost;
    private BigDecimal initialPayment;

    // fix162 money safety: why the total cost changed, and the cost this form was loaded with (edit-conflict guard)
    private String costChangeReason;
    private BigDecimal expectedTotalCost;

    // Legacy fields -- kept to avoid breaking existing data, no longer used in new logic
    private BigDecimal weeklyInstallment;
    private String planType;

    @Builder.Default
    private List<NoteRequest> notes = new ArrayList<>();

    private Integer currentStatusIndex;

    // Legacy Titles entry (fix180: set by the server from the project type; old pages still send it)
    @JsonProperty("isLegacy")
    private boolean isLegacy;

    // Staff can flag a plot as receivable right at intake (for old/existing cases)
    @JsonProperty("isStartAsReceivable")
    private boolean isStartAsReceivable;

    private java.math.BigDecimal monthlyStorageFee;
    private java.math.BigDecimal initialStorageFee;
    // fix171: how much of the initial storage fee the client has ALREADY paid (counts toward the fees, not the title work)
    private java.math.BigDecimal initialStorageFeePaid;
    // fix172: optional date the client last paid (for the money entered as already paid at intake). Empty = today.
    private LocalDate lastPaidDate;
    // fix172: Legacy Title only. The date the project went into receivables; the months since then are billed at intake.
    private LocalDate receivablesSince;
    // fix172: WHICH client paid the intake money (fix180: the NIN typed in the Clients section). Needed when there is more than one client.
    private String initialPaymentPayerNin;
    private String initialStorageFeePaidPayerNin;

    // The status checklist picked at intake (fix180: the project type's list). If omitted, no statuses are attached
    // and staff can add them later from the Folder page.
    @Builder.Default
    private List<com.gesolutions.erp.modules.land.dto.ProjectStatusRequest> selectedStatuses = new ArrayList<>();

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
    public static class NeighborRequest {
        private String fullName;
        private String phone;
        private String side;
        private String plotNumber;
        private String notes;
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
