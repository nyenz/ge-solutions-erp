// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/DashboardSummaryDTO.java
package com.gesolutions.erp.modules.land.dto;

import lombok.*;
import java.math.BigDecimal;
import java.util.Map;
import java.util.List;

/**
 * NYENZ ERP - DASHBOARD SUMMARY BINDER (V3)
 * 
 * Consolidates all 8 pillars of intelligence into one high-speed signal.
 * Updated to include specific counters for Legacy vs Standard backlogs.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DashboardSummaryDTO {

    // --- PILLAR A: SHARED TACTICAL HUD ---
    private long totalPlots;
    private long plotsGrowth; // 7-Day Trend
    private long staleCallCount; 
    private long readyForReleaseCount;
    private long boxCount; // Physical Inventory

    // --- PILLAR B: TECHNICAL BOTTLENECKS ---
    private Map<Integer, Long> stageDistribution; // Stage 1-5 counts
    
    // Missing Fields Restored:
    private long legacyBacklogCount;
    private long newSurveyCount;

    // --- PILLAR C: SYSTEMS PULSE ---
    private long activeManagersOnline; 
    private long dailyAuditCount; 

    // --- PILLAR D: FINANCIAL INTELLIGENCE (ROOT/ADMIN ONLY) ---
    private BigDecimal totalArchiveValue; 
    private BigDecimal totalCollected;
    private BigDecimal outstandingArrears;
    private double collectionVelocity; 

    private List<BigDecimal> revenueInflowTrend;
}