// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/DirectorDashboardDTO.java
package com.gesolutions.erp.modules.land.dto;

import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * GE SOLUTIONS - DIRECTOR'S DASHBOARD (PHASE 7)
 *
 * Company-wide snapshot for a single time window (DAY/WEEK/MONTH/YEAR),
 * plus the always-current pipeline and company financials snapshots
 * (those two are not time-windowed -- they reflect the live state).
 *
 * See Section 17.9 of the LLM context guide for the business rules.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DirectorDashboardDTO {

    private String period;       // DAY, WEEK, MONTH, YEAR
    private String periodLabel;  // human-readable, e.g. "LAST 7 DAYS"

    private BigDecimal revenueCollected;
    private long transactionCount;

    private List<StaffActivityDTO> staffActivity;

    private Map<Integer, Long> pipelineStageCounts;

    private BigDecimal companyExpensesTotal;
    private Map<String, BigDecimal> companyExpensesByCategory;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class StaffActivityDTO {
        private String username;
        private int actionCount;
        private LocalDateTime lastActiveAt;
    }
}
