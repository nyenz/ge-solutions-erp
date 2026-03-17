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
import java.time.temporal.TemporalAdjusters;
import java.util.*;
import java.util.stream.Collectors;

/**
 * NYENZ ERP - RECOVERY HUB (V9.1 - SENSOR PATCH)
 * 
 * Physically manages recovery logic and the Header Notification Sensor.
 */
@RestController
@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class RecoveryController {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;

    /**
     * SENSOR: TASK COUNT
     * Physically counts unique PLOTS that are eligible for a call today.
     */
    @GetMapping("/count")
    public ResponseEntity<Map<String, Long>> getStaleCount() {
        List<LandProject> allProjects = projectRepository.findAll();
        long stalePlotCount = 0;

        for (LandProject project : allProjects) {
            BigDecimal arrears = project.getTotalCost().subtract(project.getAmountPaid());
            if (arrears.compareTo(BigDecimal.ZERO) <= 0) continue;

            // Logic: Is there ANY contact attempt record or is the last one > 14 days ago?
            LocalDateTime lastContact = project.getProprietors().stream()
                    .map(Client::getLastContactedAt)
                    .filter(Objects::nonNull)
                    .max(LocalDateTime::compareTo)
                    .orElse(null);

            int maxContactCount = project.getProprietors().stream()
                    .mapToInt(Client::getMonthlyContactCount)
                    .max()
                    .orElse(0);

            boolean isStale = (lastContact == null || lastContact.isBefore(LocalDateTime.now().minusDays(14)));
            boolean underLimit = (maxContactCount < 2);

            if (isStale && underLimit) {
                stalePlotCount++;
            }
        }
        
        return ResponseEntity.ok(Map.of("staleCount", stalePlotCount));
    }

    @GetMapping("/queue")
    public ResponseEntity<List<RecoveryTaskDTO>> getRecoveryQueue() {
        List<LandProject> allProjects = projectRepository.findAll();
        List<RecoveryTaskDTO> queue = new ArrayList<>();

        for (LandProject project : allProjects) {
            BigDecimal arrears = project.getTotalCost().subtract(project.getAmountPaid());
            if (arrears.compareTo(BigDecimal.ZERO) <= 0) continue;

            LocalDateTime lastContact = project.getProprietors().stream()
                    .map(Client::getLastContactedAt).filter(Objects::nonNull).max(LocalDateTime::compareTo).orElse(null);
            int maxCount = project.getProprietors().stream().mapToInt(Client::getMonthlyContactCount).max().orElse(0);

            if ((lastContact == null || lastContact.isBefore(LocalDateTime.now().minusDays(14))) && (maxCount < 2)) {
                queue.add(buildAssetDto(project, arrears, lastContact, maxCount));
            }
        }
        return ResponseEntity.ok(queue);
    }

    @GetMapping("/schedule")
    public ResponseEntity<List<RecoveryTaskDTO>> getFullForecast() {
        List<LandProject> allProjects = projectRepository.findAll();
        return ResponseEntity.ok(allProjects.stream()
                .filter(p -> p.getTotalCost().subtract(p.getAmountPaid()).compareTo(BigDecimal.ZERO) > 0)
                .map(p -> {
                    BigDecimal arrears = p.getTotalCost().subtract(p.getAmountPaid());
                    LocalDateTime last = p.getProprietors().stream().map(Client::getLastContactedAt).filter(Objects::nonNull).max(LocalDateTime::compareTo).orElse(null);
                    int count = p.getProprietors().stream().mapToInt(Client::getMonthlyContactCount).max().orElse(0);
                    return buildAssetDto(p, arrears, last, count);
                })
                .sorted(Comparator.comparing(RecoveryTaskDTO::getNextCallDue))
                .collect(Collectors.toList()));
    }

    private RecoveryTaskDTO buildAssetDto(LandProject project, BigDecimal arrears, LocalDateTime lastCall, int count) {
        LocalDate nextCall;
        String status;
        boolean isLocked;

        if (lastCall == null) {
            nextCall = LocalDate.now();
            status = "NEW ASSIGNMENT";
            isLocked = false;
        } else if (count >= 2) {
            nextCall = LocalDate.now().plusMonths(1).with(TemporalAdjusters.firstDayOfMonth());
            status = "MONTHLY LIMIT";
            isLocked = true;
        } else {
            nextCall = lastCall.toLocalDate().plusDays(14);
            if (LocalDate.now().isAfter(nextCall) || LocalDate.now().isEqual(nextCall)) {
                status = "ACTION REQUIRED";
                isLocked = false;
            } else {
                status = "COOLING DOWN";
                isLocked = true;
            }
        }

        List<FollowUpLog> logs = followUpRepository.findByProjectIdOrderByTimestampDesc(project.getId());
        String note = logs.isEmpty() ? "SYSTEM: NEW INTAKE" : logs.get(0).getNotes();
        List<RecoveryTaskDTO.OwnerDetail> ownerList = project.getProprietors().stream().map(c -> new RecoveryTaskDTO.OwnerDetail(c.getId(), c.getFullName(), c.getPhoneNumber())).collect(Collectors.toList());

        return RecoveryTaskDTO.builder().projectId(project.getId()).plotNumber(project.getLandTitle().getPlotNumber()).physicalBoxNumber(project.getLandTitle().getPhysicalBoxNumber()).allOwners(ownerList).weeklyRequirement(project.getWeeklyInstallment()).totalArrears(arrears).lastInteractionNote(note).lastContactDate(lastCall != null ? lastCall.toLocalDate().toString() : "NEVER").nextCallDue(nextCall.toString()).missionStatus(status).isLocked(isLocked).build();
    }
}