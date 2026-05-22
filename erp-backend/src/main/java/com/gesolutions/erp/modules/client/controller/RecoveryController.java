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

    // ── BELL COUNT ───────────────────────────────────────────────────────
    // Counts plots eligible for a call today (outstanding balance + call not locked)
    @GetMapping("/count")
    public ResponseEntity<Map<String, Long>> getStaleCount() {
        List<LandProject> allProjects = projectRepository.findAll();
        long count = buildPlotTasks(allProjects).stream()
                .filter(dto -> !dto.isLocked())
                .count();
        return ResponseEntity.ok(Map.of("staleCount", count));
    }

    // ── ACTION QUEUE — only plots eligible to call today ──────────────────
    @GetMapping("/queue")
    public ResponseEntity<List<RecoveryTaskDTO>> getRecoveryQueue() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> queue = buildPlotTasks(allProjects).stream()
                .filter(dto -> !dto.isLocked())
                .filter(dto -> dto.getCurrentBalance() != null
                        ? dto.getCurrentBalance().compareTo(BigDecimal.ZERO) > 0
                        : (dto.getTotalBacklogOwed() != null && dto.getTotalBacklogOwed().compareTo(BigDecimal.ZERO) > 0))
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(queue);
    }

    // ── FULL SCHEDULE — all outstanding regardless of call eligibility ─────
    @GetMapping("/schedule")
    public ResponseEntity<List<RecoveryTaskDTO>> getFullSchedule() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> all = buildPlotTasks(allProjects).stream()
                .filter(dto -> {
                    BigDecimal bal = dto.isBacklog()
                            ? dto.getTotalBacklogOwed()
                            : dto.getCurrentBalance();
                    return bal != null && bal.compareTo(BigDecimal.ZERO) > 0;
                })
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList());
        return ResponseEntity.ok(all);
    }

    // ── RECORD PAYMENT (Admin/Root only) ──────────────────────────────────
    @PostMapping("/projects/{projectId}/payment")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> recordPayment(
            @PathVariable UUID projectId,
            @RequestParam BigDecimal amount,
            @RequestParam(required = false) String notes) {
        landService.recordPayment(projectId, amount, notes);
        return ResponseEntity.ok().build();
    }

    // ── BACKLOG MANAGEMENT ────────────────────────────────────────────────
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

    @GetMapping("/projects/{projectId}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID projectId) {
        return ResponseEntity.ok(paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId));
    }

    // ── CORE BUILDER — one DTO per Plot ───────────────────────────────────
    private List<RecoveryTaskDTO> buildPlotTasks(List<LandProject> allProjects) {
        List<RecoveryTaskDTO> result = new ArrayList<>();

        for (LandProject plot : allProjects) {
            // Skip plots with no outstanding balance
            BigDecimal balance = plot.isBacklog()
                    ? plot.backlogTotalOwed()
                    : plot.activeTotalOwed();
            if (balance.compareTo(BigDecimal.ZERO) <= 0) continue;

            // Use the first proprietor as the "primary" for call-status tracking
            Set<Client> proprietors = plot.getProprietors();
            if (proprietors == null || proprietors.isEmpty()) continue;

            // Sort owners to get a stable primary (earliest by fullName)
            List<Client> ownerList = proprietors.stream()
                    .sorted(Comparator.comparing(Client::getFullName))
                    .collect(Collectors.toList());

            Client primary = ownerList.get(0);

            // Reset monthly counter if needed
            if (primary.shouldResetMonthlyCounter()) {
                primary.setMonthlyContactCount(0);
            }

            LocalDateTime lastContact = primary.getLastContactedAt();
            int callCount = primary.getMonthlyContactCount();

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

            // Last note
            List<FollowUpLog> logs = followUpRepository
                    .findByProjectIdOrderByTimestampDesc(plot.getId());
            String lastNote = logs.isEmpty() ? "NO PRIOR CONTACT" : logs.get(0).getNotes();

            // Payment badge
            String badge = computePaymentBadge(plot);
            String lastPaymentStr = plot.getLastPaymentDate() != null
                    ? plot.getLastPaymentDate().toLocalDate().toString() : "NEVER";

            // Build owner list
            List<RecoveryTaskDTO.OwnerInfo> ownerInfos = ownerList.stream()
                    .map(c -> RecoveryTaskDTO.OwnerInfo.builder()
                            .clientId(c.getId())
                            .fullName(c.getFullName())
                            .phoneNumber(c.getPhoneNumber())
                            .email(c.getEmail())
                            .build())
                    .collect(Collectors.toList());

            // Financial fields
            BigDecimal totalCost  = plot.getTotalCost() != null ? plot.getTotalCost() : BigDecimal.ZERO;
            BigDecimal amountPaid = plot.getAmountPaid() != null ? plot.getAmountPaid() : BigDecimal.ZERO;
            BigDecimal fees       = plot.getStorageFeesAccumulated() != null ? plot.getStorageFeesAccumulated() : BigDecimal.ZERO;
            long months = plot.getBacklogStartDate() != null
                    ? ChronoUnit.MONTHS.between(plot.getBacklogStartDate(), LocalDateTime.now()) : 0;

            RecoveryTaskDTO dto = RecoveryTaskDTO.builder()
                    .projectId(plot.getId())
                    .plotNumber(plot.getLandTitle().getPlotNumber())
                    .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())
                    .isBacklog(plot.isBacklog())
                    .owners(ownerInfos)
                    .lastContactDate(lastContact != null ? lastContact.toLocalDate().toString() : "NEVER")
                    .nextCallDue(nextCallDue)
                    .missionStatus(missionStatus)
                    .isLocked(isLocked)
                    .monthlyCallCount(callCount)
                    .totalCost(totalCost)
                    .amountPaid(amountPaid)
                    .currentBalance(plot.isBacklog() ? null : balance)
                    .originalDebt(plot.isBacklog() ? totalCost : null)
                    .storageFeesAccumulated(plot.isBacklog() ? fees : null)
                    .totalBacklogOwed(plot.isBacklog() ? balance : null)
                    .storageMonthsCount(months)
                    .paymentHealthBadge(badge)
                    .lastPaymentDate(lastPaymentStr)
                    .lastInteractionNote(lastNote)
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
