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

    // ── PRIMARY ENTITY: the Plot ──────────────────────────────────────────
    private UUID   projectId;
    private String plotNumber;
    private String physicalBoxNumber;
    private boolean isBacklog;

    // ── ALL OWNERS of this plot ────────────────────────────────────────────
    private List<OwnerInfo> owners;

    // ── CALL STATUS (driven by the primary owner's client record) ──────────
    private String  lastContactDate;
    private String  nextCallDue;
    private String  missionStatus;   // NEW ASSIGNMENT | ACTION REQUIRED | COOLING DOWN | MONTHLY LIMIT
    private boolean isLocked;
    private int     monthlyCallCount;

    // ── FINANCIAL SUMMARY ──────────────────────────────────────────────────
    private BigDecimal totalCost;
    private BigDecimal amountPaid;
    private BigDecimal currentBalance;   // for active plots

    // backlog-only extras
    private BigDecimal originalDebt;
    private BigDecimal storageFeesAccumulated;
    private BigDecimal totalBacklogOwed;
    private long       storageMonthsCount;

    // payment health
    private String paymentHealthBadge;  // GREEN | YELLOW | RED
    private String lastPaymentDate;

    private String lastInteractionNote;

    // ── INNER: owner identity ─────────────────────────────────────────────
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OwnerInfo {
        private UUID   clientId;
        private String fullName;
        private String phoneNumber;
        private String email;
    }
}
