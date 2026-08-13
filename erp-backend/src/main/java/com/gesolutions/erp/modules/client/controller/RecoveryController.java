// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java
package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.dto.RecoveryTaskDTO;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.service.LandService;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class RecoveryController {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;
    private final PaymentRecordRepository paymentRecordRepository;
    private final LandService landService;

    @GetMapping("/count")
    public ResponseEntity<Map<String, Long>> getStaleCount() {
        List<LandProject> allProjects = projectRepository.findAll();
        long count = buildOwnerTasks(allProjects).stream()
                .filter(dto -> !dto.isLocked())
                .count();
        return ResponseEntity.ok(Map.of("staleCount", count));
    }

    @GetMapping("/queue")
    public ResponseEntity<List<RecoveryTaskDTO>> getRecoveryQueue() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> queue = buildOwnerTasks(allProjects).stream()
                .filter(dto -> !dto.isLocked())
                .filter(dto -> dto.getTotalDemand().compareTo(BigDecimal.ZERO) > 0)
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(queue);
    }

    @GetMapping("/schedule")
    public ResponseEntity<List<RecoveryTaskDTO>> getFullSchedule() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> all = buildOwnerTasks(allProjects).stream()
                .filter(dto -> dto.getTotalDemand().compareTo(BigDecimal.ZERO) > 0)
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(all);
    }

    private List<RecoveryTaskDTO> buildOwnerTasks(List<LandProject> allProjects) {
        Map<UUID, List<LandProject>> clientPlotsMap = new LinkedHashMap<>();
        Map<UUID, Client> clientRegistry = new HashMap<>();

        for (LandProject plot : allProjects) {
            BigDecimal balance = plot.isBacklog() ? plot.backlogTotalOwed() : plot.activeTotalOwed();
            if (balance.compareTo(BigDecimal.ZERO) <= 0) continue;

            Set<Client> proprietors = plot.getProprietors();
            if (proprietors == null || proprietors.isEmpty()) continue;

            Client primary = proprietors.stream()
                    .sorted(Comparator.comparing(Client::getFullName))
                    .findFirst().orElse(null);

            if (primary != null) {
                clientPlotsMap.computeIfAbsent(primary.getId(), k -> new ArrayList<>()).add(plot);
                clientRegistry.put(primary.getId(), primary);
            }
        }

        List<RecoveryTaskDTO> result = new ArrayList<>();

        for (Map.Entry<UUID, List<LandProject>> entry : clientPlotsMap.entrySet()) {
            UUID clientId = entry.getKey();
            List<LandProject> plots = entry.getValue();
            Client client = clientRegistry.get(clientId);

            if (client.shouldResetMonthlyCounter()) {
                client.setMonthlyContactCount(0);
            }

            LocalDateTime lastContact = client.getLastContactedAt();
            int callCount = client.getMonthlyContactCount();

            String missionStatus;
            String nextCallDue;
            boolean isLocked;

            if (lastContact == null) {
                missionStatus = "NEW ASSIGNMENT";
                nextCallDue = LocalDate.now().toString();
                isLocked = false;
            } else if (callCount >= 2) {
                missionStatus = "MONTHLY LIMIT";
                nextCallDue = LocalDate.now().plusMonths(1)
                        .with(TemporalAdjusters.firstDayOfMonth()).toString();
                isLocked = true;
            } else {
                LocalDate eligibleDate = lastContact.toLocalDate().plusDays(14);
                if (!LocalDate.now().isBefore(eligibleDate)) {
                    missionStatus = "ACTION REQUIRED";
                    nextCallDue = LocalDate.now().toString();
                    isLocked = false;
                } else {
                    missionStatus = "COOLING DOWN";
                    nextCallDue = eligibleDate.toString();
                    isLocked = true;
                }
            }

            BigDecimal totalDemand = BigDecimal.ZERO;
            BigDecimal totalOriginalDebt = BigDecimal.ZERO;
            BigDecimal totalStorageFees = BigDecimal.ZERO;
            boolean hasBacklog = false;

            List<RecoveryTaskDTO.PlotSummary> plotSummaries = new ArrayList<>();

            for (LandProject plot : plots) {
                List<FollowUpLog> logs = followUpRepository.findByProjectIdOrderByTimestampDesc(plot.getId());
                String lastNote = logs.isEmpty() ? "NO PRIOR CONTACT" : logs.get(0).getNotes();

                BigDecimal plotBalance = plot.isBacklog() ? plot.backlogTotalOwed() : plot.activeTotalOwed();
                totalDemand = totalDemand.add(plotBalance);

                String badge = computePaymentBadge(plot);
                String lastPaymentStr = plot.getLastPaymentDate() != null
                        ? plot.getLastPaymentDate().toLocalDate().toString() : "NEVER";

                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()
                        .projectId(plot.getId())
                        .plotNumber(plot.getLandTitle().getPlotNumber())
                        .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())
                        .isBacklog(plot.isBacklog())
                        .lastInteractionNote(lastNote)
                        .paymentHealthBadge(badge)
                        .lastPaymentDate(lastPaymentStr)
                        .surveyDate(plot.getLandTitle().getSurveyDate());

                if (plot.isBacklog()) {
                    hasBacklog = true;
                    BigDecimal fees = plot.getStorageFeesAccumulated() != null ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;
                    BigDecimal origDebt = plot.getTotalCost() != null ? plot.getTotalCost() : BigDecimal.ZERO;
                    long months = plot.getBacklogStartDate() != null
                            ? ChronoUnit.MONTHS.between(plot.getBacklogStartDate(), LocalDateTime.now()) : 0;

                    summaryBuilder
                            .totalCost(origDebt)
                            .originalDebt(origDebt)
                            .storageFeesAccumulated(fees)
                            .totalBacklogOwed(plotBalance)
                            .storageMonthsCount(months)
                            .storagePaused(plot.isStoragePaused())
                            .storageFeeOverride(plot.getStorageFeeOverride())
                            .amountPaid(plot.getAmountPaid())
                            .currentBalance(plotBalance);

                    totalOriginalDebt = totalOriginalDebt.add(origDebt);
                    totalStorageFees = totalStorageFees.add(fees);
                } else {
                    BigDecimal cost = plot.getTotalCost() != null ? plot.getTotalCost() : BigDecimal.ZERO;
                    BigDecimal paid = plot.getAmountPaid() != null ? plot.getAmountPaid() : BigDecimal.ZERO;
                    summaryBuilder
                            .totalCost(cost)
                            .originalDebt(cost)
                            .amountPaid(paid)
                            .currentBalance(cost.subtract(paid).max(java.math.BigDecimal.ZERO));
                }

                plotSummaries.add(summaryBuilder.build());
            }

            RecoveryTaskDTO dto = RecoveryTaskDTO.builder()
                    .clientId(client.getId())
                    .ownerName(client.getFullName())
                    .phoneNumber(client.getPhoneNumber())
                    .email(client.getEmail())
                    .lastContactDate(lastContact != null ? lastContact.toLocalDate().toString() : "NEVER")
                    .nextCallDue(nextCallDue)
                    .missionStatus(missionStatus)
                    .isLocked(isLocked)
                    .monthlyCallCount(callCount)
                    .totalDemand(totalDemand)
                    .totalOriginalDebt(totalOriginalDebt)
                    .totalStorageFees(totalStorageFees)
                    .hasBacklogPlots(hasBacklog)
                    .plots(plotSummaries)
                    .build();

            result.add(dto);
        }

        return result;
    }

    private String computePaymentBadge(LandProject plot) {
        if (plot.getLastPaymentDate() == null) return "RED";
        long daysSince = ChronoUnit.DAYS.between(plot.getLastPaymentDate(), LocalDateTime.now());
        if (daysSince <= 14) return "GREEN";
        if (daysSince <= 30) return "YELLOW";
        return "RED";
    }
}
