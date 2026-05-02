// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.common.audit.AuditLog;
import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.modules.land.dto.DashboardSummaryDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class DashboardController {

    private final LandProjectRepository projectRepository;
    private final ClientRepository clientRepository;
    private final UserRepository userRepository;
    private final AuditLogRepository auditLogRepository;
    private final PaymentRecordRepository paymentRecordRepository;

    @GetMapping("/summary")
    public ResponseEntity<DashboardSummaryDTO> getSummary() {

        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        User currentUser = userRepository.findByUsername(username).orElseThrow();
        boolean showFinancials = currentUser.isRoot() || currentUser.getRole() == Role.ROLE_ADMIN;

        List<LandProject> allPlots = projectRepository.findAll();
        LocalDateTime sevenDaysAgo = LocalDateTime.now().minusDays(7);
        LocalDateTime todayStart = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0);

        long totalPlots = allPlots.size();
        long plotsGrowth = allPlots.stream()
                .filter(p -> p.getLandTitle().getCreatedAt().isAfter(sevenDaysAgo))
                .count();

        // Stale count = unique phone numbers eligible to call today
        long staleCalls = clientRepository.countUniqueEligiblePhones();

        long readyForRelease = allPlots.stream()
                .filter(p -> p.getAmountPaid().compareTo(p.getTotalCost()) >= 0)
                .filter(p -> !p.getLandTitle().isReleased())
                .count();

        long uniqueBoxes = allPlots.stream()
                .map(p -> p.getLandTitle().getPhysicalBoxNumber())
                .distinct().count();

        long backlogCount = projectRepository.countBacklogPlots();
        long legacyCount = allPlots.stream().filter(LandProject::isLegacy).count();
        long newSurveyCount = totalPlots - legacyCount;

        Map<Integer, Long> bottlenecks = allPlots.stream()
                .collect(Collectors.groupingBy(LandProject::getCurrentStageIndex, Collectors.counting()));

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
                .backlogCount(backlogCount)
                .stageDistribution(bottlenecks)
                .legacyBacklogCount(legacyCount)
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
}