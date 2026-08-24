// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java
package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.dto.RecoveryTaskDTO;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
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
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class RecoveryController {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;

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
            BigDecimal balance = plot.isReceivable() ? plot.receivableTotalOwed() : plot.activeTotalOwed();
            if (balance.compareTo(BigDecimal.ZERO) <= 0) continue;

            Set<Client> proprietors = plot.getProprietors();
            if (proprietors == null || proprietors.isEmpty()) continue;

            // STAGE 9 FIX: NIN_JOINT_OWNER_VISIBILITY
            // Previously only the alphabetically-first co-owner ("primary") got
            // this project attached to their Recovery card, so every other joint
            // owner's exposure on this project was invisible to Recovery entirely.
            // Attach the project to EVERY proprietor instead -- each co-owner gets
            // their own card entry for it, on top of whatever solo/other-joint
            // projects they carry. Per-person state (lastContactedAt /
            // monthlyContactCount cooldown clock) is unaffected by this change: it
            // already lives on Client, so it's naturally shared/consistent across
            // every project that person co-owns.
            for (Client proprietor : proprietors) {
                if (proprietor == null) continue;
                clientPlotsMap.computeIfAbsent(proprietor.getId(), k -> new ArrayList<>()).add(plot);
                clientRegistry.put(proprietor.getId(), proprietor);
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
            boolean hasReceivable = false;

            List<RecoveryTaskDTO.PlotSummary> plotSummaries = new ArrayList<>();

            for (LandProject plot : plots) {
                List<FollowUpLog> logs = followUpRepository.findByProjectIdOrderByTimestampDesc(plot.getId());
                String lastNote = logs.isEmpty() ? "NO PRIOR CONTACT" : logs.get(0).getNotes();

                BigDecimal plotBalance = plot.isReceivable() ? plot.receivableTotalOwed() : plot.activeTotalOwed();
                totalDemand = totalDemand.add(plotBalance);

                String badge = computePaymentBadge(plot);
                String lastPaymentStr = plot.getLastPaymentDate() != null
                        ? plot.getLastPaymentDate().toLocalDate().toString() : "NEVER";

                // STAGE 10: SOLO vs JOINT label + navigable co-owners + this
                // owner's OWN contact history on this project (design brief 3.3).
                // The balance is still computed exactly once above, from the
                // project (plotBalance / totalDemand) -- it is only ever
                // referenced here, never duplicated or re-totaled per owner, so
                // this cannot cause a joint debt to be double-counted in
                // company-wide reporting just because it appears on more than
                // one person's card.
                Set<Client> plotOwners = plot.getProprietors();
                String ownershipType = (plotOwners != null && plotOwners.size() > 1) ? "JOINT" : "SOLO";
                List<RecoveryTaskDTO.CoOwnerRef> coOwners = new ArrayList<>();
                if (plotOwners != null) {
                    for (Client co : plotOwners) {
                        if (co == null || co.getId() == null || co.getId().equals(client.getId())) continue;
                        coOwners.add(RecoveryTaskDTO.CoOwnerRef.builder()
                                .clientId(co.getId())
                                .fullName(co.getFullName())
                                .build());
                    }
                }

                List<FollowUpLog> ownerLogs = followUpRepository
                        .findByProjectIdAndOwnerIdOrderByTimestampDesc(plot.getId(), client.getId());
                String ownerLastContactDate = ownerLogs.isEmpty()
                        ? "NEVER" : ownerLogs.get(0).getTimestamp().toLocalDate().toString();
                String ownerLastContactNote = ownerLogs.isEmpty() ? null : ownerLogs.get(0).getNotes();

                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()
                        .projectId(plot.getId())
                        .plotNumber(plot.getLandTitle() != null ? plot.getLandTitle().getPlotNumber() : plot.getProjectIndex())
                        .physicalBoxNumber(plot.getLandTitle() != null ? plot.getLandTitle().getPhysicalBoxNumber() : null)
                        .isReceivable(plot.isReceivable())
                        .lastInteractionNote(lastNote)
                        .paymentHealthBadge(badge)
                        .lastPaymentDate(lastPaymentStr)
                        .surveyDate(plot.getLandTitle() != null ? plot.getLandTitle().getSurveyDate() : null)
                        .ownershipType(ownershipType)
                        .coOwners(coOwners)
                        .ownerLastContactDate(ownerLastContactDate)
                        .ownerLastContactNote(ownerLastContactNote);

                if (plot.isReceivable()) {
                    hasReceivable = true;
                    BigDecimal fees = plot.getStorageFeesAccumulated() != null ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;
                    BigDecimal origDebt = plot.getTotalCost() != null ? plot.getTotalCost() : BigDecimal.ZERO;
                    long months = plot.getReceivableStartDate() != null
                            ? ChronoUnit.MONTHS.between(plot.getReceivableStartDate(), LocalDateTime.now()) : 0;

                    summaryBuilder
                            .totalCost(origDebt)
                            .originalDebt(origDebt)
                            .storageFeesAccumulated(fees)
                            .totalReceivableOwed(plotBalance)
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
                    .hasReceivablePlots(hasReceivable)
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
