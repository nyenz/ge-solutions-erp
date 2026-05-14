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
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class RecoveryController {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;
    private final PaymentRecordRepository paymentRecordRepository;
    private final LandService landService;

  

    // ─── BELL COUNT ───────────────────────────────────────────────────────────
    // Counts unique phone numbers eligible for a call today

    @GetMapping("/count")
    public ResponseEntity<Map<String, Long>> getStaleCount() {
        List<LandProject> allProjects = projectRepository.findAll();
        long count = buildPhoneGroups(allProjects).values().stream()
                .filter(dto -> !dto.isLocked())
                .count();
        return ResponseEntity.ok(Map.of("staleCount", count));
    }

    // ─── ACTION QUEUE — only eligible to call today ───────────────────────────

    @GetMapping("/queue")
    public ResponseEntity<List<RecoveryTaskDTO>> getRecoveryQueue() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> queue = buildPhoneGroups(allProjects).values().stream()
                .filter(dto -> !dto.isLocked())
                .filter(dto -> dto.getTotalDemand().compareTo(BigDecimal.ZERO) > 0)
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(queue);
    }

    // ─── FULL SCHEDULE — all outstanding regardless of call eligibility ────────

    @GetMapping("/schedule")
    public ResponseEntity<List<RecoveryTaskDTO>> getFullSchedule() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> all = buildPhoneGroups(allProjects).values().stream()
                .filter(dto -> dto.getTotalDemand().compareTo(BigDecimal.ZERO) > 0)
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(all);
    }

    // ─── RECORD PAYMENT (Admin/Root only) ─────────────────────────────────────

    @PostMapping("/projects/{projectId}/payment")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> recordPayment(
            @PathVariable UUID projectId,
            @RequestParam BigDecimal amount,
            @RequestParam(required = false) String notes) {
        landService.recordPayment(projectId, amount, notes);
        return ResponseEntity.ok().build();
    }

    // ─── BACKLOG MANAGEMENT (Admin/Root only) ─────────────────────────────────

    @PostMapping("/projects/{projectId}/backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> moveToBacklog(@PathVariable UUID projectId) {
        landService.moveToBacklog(projectId);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{projectId}/exit-backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> exitBacklog(@PathVariable UUID projectId) {
        landService.exitBacklog(projectId);
        return ResponseEntity.ok().build();
    }

    // ─── GET PAYMENT HISTORY FOR A PLOT ───────────────────────────────────────

    @GetMapping("/projects/{projectId}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID projectId) {
        return ResponseEntity.ok(paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId));
    }

    // ─── CORE BUILDER — Groups all plots by phone number ──────────────────────

    private Map<String, RecoveryTaskDTO> buildPhoneGroups(List<LandProject> allProjects) {
        // Map: phoneNumber → list of plots belonging to that phone
        Map<String, List<LandProject>> byPhone = new LinkedHashMap<>();

        for (LandProject project : allProjects) {
            // Skip fully paid plots
            BigDecimal balance = project.isBacklog()
                    ? project.backlogTotalOwed()
                    : project.activeTotalOwed();
            if (balance.compareTo(BigDecimal.ZERO) <= 0) continue;

            for (Client owner : project.getProprietors()) {
                String phone = owner.getPhoneNumber();
                byPhone.computeIfAbsent(phone, k -> new ArrayList<>()).add(project);
            }
        }

        // Now build one RecoveryTaskDTO per phone number
        Map<String, RecoveryTaskDTO> result = new LinkedHashMap<>();

        for (Map.Entry<String, List<LandProject>> entry : byPhone.entrySet()) {
            String phone = entry.getKey();
            List<LandProject> plots = entry.getValue();

            // Get the client record for this phone (use first plot's matching proprietor)
            Client client = plots.get(0).getProprietors().stream()
                    .filter(c -> c.getPhoneNumber().equals(phone))
                    .findFirst().orElse(null);
            if (client == null) continue;

            // Determine call status from client record
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

            // Build plot summaries
            List<RecoveryTaskDTO.PlotSummary> plotSummaries = new ArrayList<>();
            BigDecimal totalDemand = BigDecimal.ZERO;
            BigDecimal totalOriginalDebt = BigDecimal.ZERO;
            BigDecimal totalStorageFees = BigDecimal.ZERO;
            boolean hasBacklog = false;

            for (LandProject plot : plots) {
                List<FollowUpLog> logs = followUpRepository
                        .findByProjectIdOrderByTimestampDesc(plot.getId());
                String lastNote = logs.isEmpty() ? "NO PRIOR CONTACT" : logs.get(0).getNotes();

                // Payment health badge
                String badge = computePaymentBadge(plot);
                String lastPaymentStr = plot.getLastPaymentDate() != null
                        ? plot.getLastPaymentDate().toLocalDate().toString() : "NEVER";

                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder =
                        RecoveryTaskDTO.PlotSummary.builder()
                        .projectId(plot.getId())
                        .plotNumber(plot.getLandTitle().getPlotNumber())
                        .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())
                        .isBacklog(plot.isBacklog())
                        .lastInteractionNote(lastNote)
                        .paymentHealthBadge(badge)
                        .lastPaymentDate(lastPaymentStr);

                if (plot.isBacklog()) {
                    hasBacklog = true;
                    BigDecimal owed = plot.backlogTotalOwed();
                    BigDecimal fees = plot.getStorageFeesAccumulated() != null
                            ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;
                    BigDecimal origDebt = plot.getTotalCost() != null ? plot.getTotalCost() : BigDecimal.ZERO;

                    long months = plot.getBacklogStartDate() != null
                            ? ChronoUnit.MONTHS.between(plot.getBacklogStartDate(), LocalDateTime.now())
                            : 0;

                    summaryBuilder
                        .originalDebt(origDebt)
                        .storageFeesAccumulated(fees)
                        .totalBacklogOwed(owed)
                        .storageMonthsCount(months)
                        .amountPaid(plot.getAmountPaid())
                        .currentBalance(owed);

                    totalDemand = totalDemand.add(owed);
                    totalOriginalDebt = totalOriginalDebt.add(origDebt);
                    totalStorageFees = totalStorageFees.add(fees);
                } else {
                    BigDecimal balance = plot.activeTotalOwed();
                    summaryBuilder
                        .totalCost(plot.getTotalCost())
                        .amountPaid(plot.getAmountPaid())
                        .currentBalance(balance);
                    totalDemand = totalDemand.add(balance);
                }

                plotSummaries.add(summaryBuilder.build());
            }

            RecoveryTaskDTO dto = RecoveryTaskDTO.builder()
                    .phoneNumber(phone)
                    .ownerName(client.getFullName())
                    .primaryClientId(client.getId())
                    .lastContactDate(lastContact != null
                            ? lastContact.toLocalDate().toString() : "NEVER")
                    .nextCallDue(nextCallDue)
                    .missionStatus(missionStatus)
                    .isLocked(isLocked)
                    .monthlyCallCount(callCount)
                    .plots(plotSummaries)
                    .totalDemand(totalDemand)
                    .totalOriginalDebt(totalOriginalDebt)
                    .totalStorageFees(totalStorageFees)
                    .hasBacklogPlots(hasBacklog)
                    .build();

            result.put(phone, dto);
        }

        return result;
    }

    // GREEN = payment within 14 days
    // YELLOW = payment within 30 days
    // RED = no payment or over 30 days
    private String computePaymentBadge(LandProject plot) {
        if (plot.getLastPaymentDate() == null) return "RED";
        long daysSince = ChronoUnit.DAYS.between(plot.getLastPaymentDate(), LocalDateTime.now());
        if (daysSince <= 14) return "GREEN";
        if (daysSince <= 30) return "YELLOW";
        return "RED";
    }
}