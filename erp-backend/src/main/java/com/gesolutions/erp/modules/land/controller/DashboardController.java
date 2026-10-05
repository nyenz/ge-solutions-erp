// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.common.audit.AuditLog;
import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.modules.land.dto.DashboardSummaryDTO;
import com.gesolutions.erp.modules.land.dto.DirectorDashboardDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.finance.repository.ExpenseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class DashboardController {

    private final LandProjectRepository projectRepository;
    private final UserRepository userRepository;
    private final AuditLogRepository auditLogRepository;
    private final PaymentRecordRepository paymentRecordRepository;
    private final com.gesolutions.erp.modules.client.service.RecoveryStateService recoveryState;
    private final com.gesolutions.erp.modules.land.service.HomeDashboardService homeDashboardService;
    private final ExpenseRepository expenseRepository;
    private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;

    @GetMapping("/summary")
    public ResponseEntity<DashboardSummaryDTO> getSummary() {

        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User currentUser = userRepository.findByUsername(username).orElseThrow();
        boolean showFinancials = currentUser.isRoot()
                || currentUser.getRole() == Role.ROLE_ADMIN
                || currentUser.getRole() == Role.ROLE_DIRECTOR;

        List<LandProject> allPlots = projectRepository.findAll();
        LocalDateTime sevenDaysAgo = LocalDateTime.now().minusDays(7);
        LocalDateTime todayStart = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0);

        long totalPlots = allPlots.size();
        long plotsGrowth = allPlots.stream()
                .filter(p -> {
                    if (p.getLandTitle() != null && p.getLandTitle().getCreatedAt() != null) return p.getLandTitle().getCreatedAt().isAfter(sevenDaysAgo);
                    return p.getProjectStartDate() != null && p.getProjectStartDate().isAfter(sevenDaysAgo.toLocalDate());
                })
                .count();

        // STAGE 11 FIX: DASHBOARD_STALE_COUNT_PRIMARY_OWNER_BUG.
        // This used to pick only the alphabetically-first proprietor per plot
        // ("primary") and test THEIR cooldown/count -- the exact bug Stage 9/10
        // already removed from Recovery itself, just never ported here, so this
        // KPI could silently disagree with GET /api/v1/recovery/count. Decision
        // (3.4): both must report the same definition of "stale" -- unique
        // Client IDs, deduped across every plot they co-own, each independently
        // eligible under their own cooldown/monthly-count state -- matching
        // RecoveryNoteController locked()/qualifies() rule exactly (live /recovery/stats).
        // fix181 (4.3): the SAME rule as the Recovery page "due now" (it used a calendar-month count + 14-day gap here,
        // so the two numbers could disagree)
        long staleCalls = recoveryState.dueNow(recoveryState.load(), LocalDateTime.now());

        // fix181 (2.3, 11.3): the same hand-over rule as authorizeRelease (no zero-price, no storage money as title money,
        // no kept fees, no PROBLEM flag, title record needed)
        long readyForRelease = allPlots.stream()
                .filter(p -> p.releaseBlocker() == null)
                .count();

        long uniqueBoxes = allPlots.stream()
                .map(p -> p.getLandTitle() != null ? p.getLandTitle().getPlotNumber() : null).filter(pb -> pb != null)
                .distinct().count();

        long receivableCount = projectRepository.countReceivablePlots();
        long legacyCount = allPlots.stream().filter(LandProject::isLegacy).count();
        long newSurveyCount = totalPlots - legacyCount;

        Map<Integer, Long> bottlenecks = allPlots.stream()
                .collect(Collectors.groupingBy(LandProject::getCurrentStatusIndex, Collectors.counting()));

        long onlineCount = userRepository.countByIsActiveTrue();
        long dailyActions = auditLogRepository.findAll().stream()
                .filter(a -> a.getTimestamp().isAfter(todayStart)).count();

        List<AuditLog> recentActivity = auditLogRepository.findAll(
                PageRequest.of(0, 5, Sort.by("timestamp").descending())).getContent();

        DashboardSummaryDTO.DashboardSummaryDTOBuilder builder = DashboardSummaryDTO.builder()
                .totalPlots(totalPlots)
                .plotsGrowth(plotsGrowth)
                .staleCallCount(staleCalls)
                .readyForReleaseCount(readyForRelease)
                .boxCount(uniqueBoxes)
                .receivableCount(receivableCount)
                .statusDistribution(bottlenecks)
                .legacyReceivableCount(legacyCount)
                .newSurveyCount(newSurveyCount)
                .activeManagersOnline(onlineCount)
                .dailyAuditCount(dailyActions)
                .recentActivity(recentActivity);

        if (showFinancials) {
            BigDecimal totalValue = allPlots.stream()
                    .map(LandProject::getTotalCost)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

            BigDecimal totalCollected = allPlots.stream()
                    .map(LandProject::getAmountPaid)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

            BigDecimal arrears = totalValue.subtract(totalCollected);
            BigDecimal totalStorageFees = projectRepository.sumAllStorageFees();

            double velocity = 0;
            if (totalValue.compareTo(BigDecimal.ZERO) > 0) {
                velocity = totalCollected.divide(totalValue, 4, RoundingMode.HALF_UP)
                        .doubleValue() * 100;
            }

            // Real revenue trend — last 6 months from payment_records
            LocalDateTime sixMonthsAgo = LocalDateTime.now().minusMonths(6);
            List<Object[]> monthlyData = paymentRecordRepository.monthlyRevenueSince(sixMonthsAgo);
            List<BigDecimal> inflowTrend = monthlyData.stream()
                    .map(row -> row[1] != null ? new BigDecimal(row[1].toString()) : BigDecimal.ZERO)
                    .collect(Collectors.toList());

            if (inflowTrend.isEmpty()) inflowTrend.add(BigDecimal.ZERO);

            builder.totalArchiveValue(totalValue)
                   .totalCollected(totalCollected)
                   .outstandingArrears(arrears)
                   .totalStorageFeesAccumulated(totalStorageFees)
                   .collectionVelocity(velocity)
                   .revenueInflowTrend(inflowTrend);
        }

        return ResponseEntity.ok(builder.build());
    }

    /**
     * PHASE 7: DIRECTOR'S DASHBOARD
     *
     * Company-wide snapshot for a single time window. Frontend calls this
     * twice by default (period=WEEK and period=MONTH) to satisfy the
     * "default view is week + month" rule in Section 17.9, and can call
     * again with period=DAY or period=YEAR when the Director drills down.
     *
     * pipelineStatusCounts and the company financials snapshot are NOT
     * time-windowed -- they always reflect the current live state,
     * regardless of which period was requested.
     */
    /**
     * fix181 (20.1): THE home page answer -- only the blocks of the caller's rank (HomeDashboardService.dashboardBlocks).
     * Money is never sent to Manager or Secretary. /summary stays for one release, then goes (Step 5).
     */
    @GetMapping("/home")
    public Map<String, Object> home() {
        String name = SecurityContextHolder.getContext().getAuthentication().getName();
        User u = userRepository.findByUsername(name).orElseThrow();
        return homeDashboardService.home(u.isRoot() ? Role.ROLE_ADMIN : u.getRole());
    }

    @GetMapping("/director")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<DirectorDashboardDTO> getDirectorDashboard(
            @RequestParam(defaultValue = "WEEK") String period) {

        String normalizedPeriod = period == null ? "WEEK" : period.toUpperCase();
        LocalDateTime since;
        String periodLabel;

        switch (normalizedPeriod) {
            case "DAY":
                since = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0).withNano(0);
                periodLabel = "TODAY";
                break;
            case "MONTH":
                since = LocalDateTime.now().minusDays(30);
                periodLabel = "LAST 30 DAYS";
                break;
            case "YEAR":
                since = LocalDateTime.now().minusDays(365);
                periodLabel = "LAST 365 DAYS";
                break;
            case "WEEK":
            default:
                since = LocalDateTime.now().minusDays(7);
                periodLabel = "LAST 7 DAYS";
                normalizedPeriod = "WEEK";
                break;
        }

        // Revenue collected in the window (all payment types, title + storage fee + company cost payments excluded)
        BigDecimal revenueCollected = paymentRecordRepository.sumAllPaymentsSince(since);

        List<AuditLog> logsInPeriod = auditLogRepository.findAll().stream()
                .filter(a -> a.getTimestamp() != null && a.getTimestamp().isAfter(since))
                .collect(Collectors.toList());

        long transactionCount = logsInPeriod.stream()
                .filter(a -> "PAYMENT_RECORDED".equals(a.getAction()) || "COMPANY_EXPENSE_PAYMENT".equals(a.getAction()))
                .count();

        // Staff activity: group audit logs in this window by operator
        Map<String, List<AuditLog>> byOperator = logsInPeriod.stream()
                .filter(a -> a.getPerformedBy() != null && !"SYSTEM".equals(a.getPerformedBy()))
                .collect(Collectors.groupingBy(AuditLog::getPerformedBy));

        List<DirectorDashboardDTO.StaffActivityDTO> staffActivity = byOperator.entrySet().stream()
                .map(entry -> {
                    LocalDateTime lastActive = entry.getValue().stream()
                            .map(AuditLog::getTimestamp)
                            .max(Comparator.naturalOrder())
                            .orElse(null);
                    return DirectorDashboardDTO.StaffActivityDTO.builder()
                            .username(entry.getKey())
                            .actionCount(entry.getValue().size())
                            .lastActiveAt(lastActive)
                            .build();
                })
                .sorted(Comparator.comparingInt(DirectorDashboardDTO.StaffActivityDTO::getActionCount).reversed())
                .collect(Collectors.toList());

        // Pipeline status counts -- live snapshot, same 5-step status index used by /summary
        List<LandProject> allPlots = projectRepository.findAll();
        Map<Integer, Long> pipelineStatusCounts = allPlots.stream()
                .collect(Collectors.groupingBy(LandProject::getCurrentStatusIndex, Collectors.counting()));

        // Company financials -- live snapshot, not time-windowed
        BigDecimal companyExpensesTotal = expenseRepository.sumAll();
        Map<String, BigDecimal> companyExpensesByCategory = new LinkedHashMap<>();
        for (Object[] row : expenseRepository.sumByCategoryAll()) {
            companyExpensesByCategory.put((String) row[0], (BigDecimal) row[1]);
        }

        DirectorDashboardDTO dto = DirectorDashboardDTO.builder()
                .period(normalizedPeriod)
                .periodLabel(periodLabel)
                .revenueCollected(revenueCollected)
                .transactionCount(transactionCount)
                .staffActivity(staffActivity)
                .pipelineStatusCounts(pipelineStatusCounts)
                .companyExpensesTotal(companyExpensesTotal)
                .companyExpensesByCategory(companyExpensesByCategory)
                .build();

        return ResponseEntity.ok(dto);
    }
}
