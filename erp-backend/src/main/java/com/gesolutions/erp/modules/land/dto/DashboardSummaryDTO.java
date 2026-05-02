// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/DashboardSummaryDTO.java
package com.gesolutions.erp.modules.land.dto;

import com.gesolutions.erp.common.audit.AuditLog;
import lombok.*;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DashboardSummaryDTO {

    private long totalPlots;
    private long plotsGrowth;
    private long staleCallCount;
    private long readyForReleaseCount;
    private long boxCount;
    private long backlogCount;

    private Map<Integer, Long> stageDistribution;
    private long legacyBacklogCount;
    private long newSurveyCount;

    private long activeManagersOnline;
    private long dailyAuditCount;

    // Financial (Admin/Root only)
    private BigDecimal totalArchiveValue;
    private BigDecimal totalCollected;
    private BigDecimal outstandingArrears;
    private BigDecimal totalStorageFeesAccumulated;
    private double collectionVelocity;
    private List<BigDecimal> revenueInflowTrend;  // Now uses real payment_records data

    private List<AuditLog> recentActivity;
}