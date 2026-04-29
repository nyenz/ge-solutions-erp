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

    // PILLAR A: SHARED TACTICAL HUD
    private long totalPlots;
    private long plotsGrowth;
    private long staleCallCount;
    private long readyForReleaseCount;
    private long boxCount;

    // PILLAR B: TECHNICAL BOTTLENECKS
    private Map<Integer, Long> stageDistribution;
    private long legacyBacklogCount;
    private long newSurveyCount;

    // PILLAR C: SYSTEMS PULSE
    private long activeManagersOnline;
    private long dailyAuditCount;

    // PILLAR D: FINANCIAL INTELLIGENCE (ROOT/ADMIN ONLY)
    private BigDecimal totalArchiveValue;
    private BigDecimal totalCollected;
    private BigDecimal outstandingArrears;
    private double collectionVelocity;
    private List<BigDecimal> revenueInflowTrend;

    // PILLAR E: RECENT ACTIVITY STREAM (ROOT ONLY)
    private List<AuditLog> recentActivity;
}