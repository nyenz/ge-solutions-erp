// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java
package com.gesolutions.erp.modules.client.dto;

import lombok.*;
import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RecoveryTaskDTO {

    // The phone number this card represents — one card per unique phone
    private String phoneNumber;
    private String ownerName;
    private UUID primaryClientId;

    // --- CALL STATUS (applies to this phone number as a whole) ---
    private String lastContactDate;
    private String nextCallDue;
    private String missionStatus;   // NEW ASSIGNMENT | ACTION REQUIRED | COOLING DOWN | MONTHLY LIMIT
    private boolean isLocked;
    private int monthlyCallCount;   // How many times called this month (max 2)

    // --- ALL PLOTS BELONGING TO THIS PHONE NUMBER ---
    private List<PlotSummary> plots;

    // --- AGGREGATED TOTALS ACROSS ALL PLOTS ---
    private BigDecimal totalDemand;         // Sum of all outstanding balances
    private BigDecimal totalOriginalDebt;   // Sum of original debts (backlog plots only)
    private BigDecimal totalStorageFees;    // Sum of storage fees (backlog plots only)
    private boolean hasBacklogPlots;        // True if ANY plot is in backlog

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PlotSummary {
        private UUID projectId;
        private String plotNumber;
        private String physicalBoxNumber;
        private boolean isBacklog;

        // For ACTIVE plots
        private BigDecimal totalCost;
        private BigDecimal amountPaid;
        private BigDecimal currentBalance;  // totalCost - amountPaid

        // For BACKLOG plots
        private BigDecimal originalDebt;
        private BigDecimal storageFeesAccumulated;
        private BigDecimal totalBacklogOwed; // originalDebt + fees - payments
        private long storageMonthsCount;     // How many months of fees applied

        // Payment health badge: GREEN | YELLOW | RED
        // GREEN = payment within 14 days
        // YELLOW = payment within 30 days
        // RED = no payment or over 30 days
        private String paymentHealthBadge;
        private String lastPaymentDate;

        private String lastInteractionNote;
    }
}