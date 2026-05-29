// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java
package com.gesolutions.erp.modules.client.dto;

import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RecoveryTaskDTO {
    private UUID clientId;
    private String ownerName;
    private String phoneNumber;
    private String email;

    private String lastContactDate;
    private String nextCallDue;
    private String missionStatus;
    private boolean isLocked;
    private int monthlyCallCount;

    private BigDecimal totalDemand;
    private BigDecimal totalOriginalDebt;
    private BigDecimal totalStorageFees;
    private boolean hasBacklogPlots;

    private List<PlotSummary> plots;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PlotSummary {
        private UUID projectId;
        private String plotNumber;
        private String physicalBoxNumber;
        private boolean isBacklog;

        private BigDecimal totalCost;
        private BigDecimal amountPaid;
        private BigDecimal currentBalance;

        private BigDecimal originalDebt;
        private BigDecimal storageFeesAccumulated;
        private BigDecimal totalBacklogOwed;
        private long storageMonthsCount;
        private boolean storagePaused;
        private BigDecimal storageFeeOverride;

        private String paymentHealthBadge;
        private String lastPaymentDate;
        private String lastInteractionNote;
        private LocalDate surveyDate;
    }
}
