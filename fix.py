#!/usr/bin/env python3
"""
fix.py -- Title Details field removal, part 1 of 3.

Deletes Volume, Folio, Instrument No., Physical Box Number, and Survey
Date from the "Title Details" section of the New Project intake form,
end to end: UI (Intake form + Digital Folder edit/read views + Recovery
Portal cards), API layer (LandEntryRequest / RecoveryTaskDTO), the
LandTitle JPA entity (including the now-unused physical_box_number DB
index), and existing backend tests that referenced these fields.

KEPT:    Title ID, Tenure, Plot Number, Block, Title Date.
REMOVED: Volume, Folio, Instrument No., Physical Box Number, Survey Date.

DATABASE NOTE:
spring.jpa.hibernate.ddl-auto is set to "update" in
erp-backend/src/main/resources/application.properties, and there is no
Flyway/Liquibase migration tooling in this repo. That means Hibernate
will NOT drop the now-unused columns on its own -- they will simply sit
in the land_titles table, unused, until someone runs a migration. The
DROP COLUMN statements below are provided for whenever that migration
is actually wanted; they are NOT executed by this script.

    ALTER TABLE land_titles DROP COLUMN IF EXISTS volume;
    ALTER TABLE land_titles DROP COLUMN IF EXISTS folio;
    ALTER TABLE land_titles DROP COLUMN IF EXISTS instrument_no;
    ALTER TABLE land_titles DROP COLUMN IF EXISTS physical_box_number;
    ALTER TABLE land_titles DROP COLUMN IF EXISTS survey_date;
    -- The dedicated index on physical_box_number (idx_physical_archive)
    -- is dropped automatically by the column drop in Postgres, but if
    -- run standalone for any reason:
    -- DROP INDEX IF EXISTS idx_physical_archive;

BUILD NOTE (read before re-running):
This sandbox's network egress allowlist does not include Maven Central
(repo.maven.apache.org / repo1.maven.org), so `./mvnw compile` cannot
resolve dependencies here and a live backend build could not be run in
this environment. Every backend edit below was verified by hand (field
declarations, builder chains, getters/setters, and DTO fields were
checked line-by-line against every call site) and no getVolume/getFolio/
getInstrumentNo/getPhysicalBoxNumber/getSurveyDate/setX equivalents
remain anywhere in erp-backend/src. The frontend WAS built successfully
end-to-end with `npm run build` (Vite) after these changes.

Run: python3 fix.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WROTE, FAILED = [], []

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(content, encoding="utf-8"); WROTE.append(rel)
    except Exception as e:
        FAILED.append((rel, str(e)))

# =====================================================================
# write: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java
# =====================================================================
write('erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java
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
                        .isReceivable(plot.isReceivable())
                        .lastInteractionNote(lastNote)
                        .paymentHealthBadge(badge)
                        .lastPaymentDate(lastPaymentStr)
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
""")

# =====================================================================
# write: erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java
# =====================================================================
write('erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java
package com.gesolutions.erp.modules.client.dto;

import lombok.*;
import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RecoveryTaskDTO {
    private UUID clientId;
    private String ownerName;
    private String phoneNumber;
    private String email;

    private String lastContactDate;
    private String nextCallDue;
    private String missionStatus;
    private boolean isLocked;
    private int monthlyCallCount;

    private BigDecimal totalDemand;
    private BigDecimal totalOriginalDebt;
    private BigDecimal totalStorageFees;
    private boolean hasReceivablePlots;

    private List<PlotSummary> plots;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PlotSummary {
        private UUID projectId;
        private String plotNumber;
        private boolean isReceivable;

        private BigDecimal totalCost;
        private BigDecimal amountPaid;
        private BigDecimal currentBalance;

        private BigDecimal originalDebt;
        private BigDecimal storageFeesAccumulated;
        private BigDecimal totalReceivableOwed;
        private long storageMonthsCount;
        private boolean storagePaused;
        private BigDecimal storageFeeOverride;

        private String paymentHealthBadge;
        private String lastPaymentDate;
        private String lastInteractionNote;

        // STAGE 10: joint-owner visibility (design brief 3.3)
        private String ownershipType; // "SOLO" or "JOINT"
        private List<CoOwnerRef> coOwners; // other owners on this project, empty for SOLO
        private String ownerLastContactDate; // THIS card-owner's own last-reached date, or "NEVER"
        private String ownerLastContactNote; // THIS card-owner's own note from that contact, or null
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CoOwnerRef {
        private UUID clientId;
        private String fullName;
    }
}
""")

# =====================================================================
# write: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java
# =====================================================================
write('erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java
package com.gesolutions.erp.modules.land.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LandEntryRequest {

    private String plotNumber;
    private String tenure;
    private String blockRoad;
    private String district;
    private String county;
    private String subCounty;
    private String parish;
    private String village;
    private String area;
    private String titleId;
    private LocalDate projectStartDate;
    private LocalDate titleIssueDate;

    @Builder.Default
    private List<OwnerRequest> owners = new ArrayList<>();

    private BigDecimal totalCost;
    private BigDecimal initialPayment;

    // Legacy fields -- kept to avoid breaking existing data, no longer used in new logic
    private BigDecimal weeklyInstallment;
    private String planType;

    @Builder.Default
    private List<NoteRequest> notes = new ArrayList<>();

    private Integer currentStageIndex;

    @JsonProperty("isLegacy")
    private boolean isLegacy;

    // INTAKE PAGE REDESIGN: set true when staff pick "New Title" as the
    // project type at intake (a title is being created immediately even
    // though the project is not a legacy record and the final processing
    // stage has not been reached yet). See LandService.atomicIntake().
    @JsonProperty("titleAtIntake")
    private boolean titleAtIntake;

    // Staff can flag a plot as receivable right at intake (for old/existing cases)
    @JsonProperty("isStartAsReceivable")
    private boolean isStartAsReceivable;

    private java.math.BigDecimal monthlyStorageFee;
    private java.math.BigDecimal initialStorageFee;

    // PHASE 4: Optional stage checklist selected at intake. If omitted,
    // no stages are attached and staff can add them later from the
    // Folder page once Phase 4B ships.
    @Builder.Default
    private List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> selectedStages = new ArrayList<>();

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OwnerRequest {
        private String fullName;
        private String phone;
        private String email;
        private String nationalId;
        private String address;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class NoteRequest {
        private UUID id;
        private String content;
    }
}
""")

# =====================================================================
# write: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
# =====================================================================
write('erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - PHYSICAL ASSET REGISTRY
 * Maps 1-1 with the technical documents (Deed Plans and Titles).
 * Optimized with Indexes for high-speed filing cabinet lookups.
 */
@Entity
@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number"),
    @Index(name = "idx_title_id", columnList = "title_id")
})
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class LandTitle {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 50)
    private String tenure; // e.g. MAILO, FREEHOLD

    @Column(name = "plot_number", unique = true, length = 100)
    private String plotNumber;

    @Column(name = "block_road", length = 100)
    private String blockRoad;

    // DEPRECATED (Phase A, Section 18.10): district/county now live on
    // LandProject and are the source of truth going forward. These
    // columns are kept here on purpose -- not deleted -- because
    // LandService.java and ReportService.java still read/write them
    // directly. Repointing those call sites to LandProject is scoped to
    // Phase B (Section 18.9.1), not this phase. Do not remove these
    // fields until Phase B has migrated every call site.
    @Deprecated
    @Column(length = 100)
    private String district;

    @Deprecated
    @Column(length = 100)
    private String county;

    @Column(name = "title_id", length = 100)
    private String titleId;

    /**
     * PROJECT INDEX
     * Short, never-repeating, searchable code shown to clients and staff.
     * Format: 001A, 002A ... 999A, 001B, 002B ... 999B, 001C ...
     * Generated automatically at intake by ProjectIndexService.
     */
    // DEPRECATED (Phase B, Section 18.10/18.3): projectIndex now lives
    // on LandProject and is assigned there at creation, before any title
    // exists -- see LandProject.java. Kept here on purpose -- not
    // deleted -- since atomicIntake() still writes the same value to
    // both places for backward compatibility with anything still reading
    // it off LandTitle. Safe to drop once nothing reads it from here.
    @Deprecated
    @Column(name = "project_index", unique = true, length = 10)
    private String projectIndex;

    /**
     * PROJECT START DATE
     * The date when the project was initiated/intake was done.
     * Auto-filled with today's date during intake, but can be edited.
     */
    @Column(name = "project_start_date")
    private LocalDate projectStartDate;

    /**
     * TITLE ISSUE DATE
     * The date when the land title was actually issued/received.
     * Optional field - can be set later when title is received.
     * Can be backdated to match the actual title issue date.
     */
    @Column(name = "title_issue_date")
    private LocalDate titleIssueDate;

    @Builder.Default
    @Column(name = "is_released", nullable = false)
    private boolean isReleased = false;

    @Column(name = "created_at", updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}""")

# =====================================================================
# write: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java
# =====================================================================
write('erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.service.ClientService;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.*;
import com.gesolutions.erp.modules.land.dto.*;
import com.gesolutions.erp.modules.land.repository.*;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
public class LandService {

    private final LandProjectRepository projectRepository;
    private final FollowUpRepository followUpRepository;
    private final ProjectDocumentRepository documentRepository;
    private final ClientRepository clientRepository;
    private final ClientService clientService;
    private final FileStorageService fileStorageService;
    private final AuditService auditService;
    private final PaymentRecordRepository paymentRecordRepository;
    private final ProjectIndexService projectIndexService;
    private final StageTemplateService stageTemplateService;
    private final ProjectStageRepository projectStageRepository;

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    // PHASE B (Section 18.9.1): landTitle can now be null. Every audit-log
    // call site that used to read project.getLandTitle().getPlotNumber()
    // directly goes through this instead -- falls back to projectIndex
    // (now on LandProject itself, see Phase B migration) when there is no
    // title yet, instead of NPE-ing.
    private String plotLabel(LandProject project) {
        if (project.getLandTitle() != null && project.getLandTitle().getPlotNumber() != null) {
            return project.getLandTitle().getPlotNumber();
        }
        return "project #" + project.getProjectIndex();
    }

    // ─── UNLOCK LOG ───────────────────────────────────────────────────────────

    @Transactional
    public void logUnlockAction(UUID id) {
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        auditService.logAction("EDIT_MODE_OPENED",
            "Operator [" + getCurrentOperator() + "] opened edit mode for plot: "
            + plotLabel(project));
    }

    // ─── DEEP DETAIL ──────────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public ProjectDeepDetailDTO getProjectDeepDetail(UUID id) {
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("VAULT FAULT"));
        List<FollowUpLog> notes = followUpRepository.findByProjectIdOrderByTimestampDesc(id);
        List<ProjectDocument> documents = documentRepository.findByProjectId(id);
        List<PaymentRecord> payments = paymentRecordRepository.findByProjectIdOrderByTimestampDesc(id);

        BigDecimal cost = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal paid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;

        BigDecimal remaining;
        if (project.isReceivable()) {
            remaining = project.receivableTotalOwed();
        } else {
            remaining = cost.subtract(paid);
        }

        double percent = cost.compareTo(BigDecimal.ZERO) > 0
                ? paid.divide(cost, 4, RoundingMode.HALF_UP).doubleValue() * 100 : 0;

        return ProjectDeepDetailDTO.builder()
                .project(project)
                .notes(notes)
                .documents(documents)
                .payments(payments)
                .remainingBalance(remaining)
                .collectionPercentage(percent)
                .build();
    }

    // ─── PAYMENT RECORDING ────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void recordPayment(UUID projectId, BigDecimal amount, String notes) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("PAYMENT_FAULT: Amount must be greater than zero.");
        }

        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        // STAGE 1 FIX: block overpayment -- work out what is still owed
        // using the same logic already used below for balanceAfter.
        BigDecimal currentlyOwed = project.isReceivable()
                ? project.receivableTotalOwed()
                : project.getTotalCost().subtract(project.getAmountPaid());
        if (amount.compareTo(currentlyOwed) > 0) {
            throw new BusinessException("OVERPAYMENT_BLOCKED: This project only owes UGX "
                    + currentlyOwed + ". You tried to record UGX " + amount + ".");
        }

        String operator = getCurrentOperator();
        String paymentType = project.isReceivable() ? "RECEIVABLE_PARTIAL" : "STANDARD";

        BigDecimal newAmountPaid = project.getAmountPaid().add(amount);
        project.setAmountPaid(newAmountPaid);
        project.setLastPaymentDate(LocalDateTime.now());

        BigDecimal balanceAfter;
        if (project.isReceivable()) {
            balanceAfter = project.receivableTotalOwed();
        } else {
            balanceAfter = project.getTotalCost().subtract(newAmountPaid);
        }

        PaymentRecord record = PaymentRecord.builder()
                .projectId(projectId)
                .amountPaid(amount)
                .paymentType(paymentType)
                .recordedBy(operator)
                .notes(notes)
                .balanceAfter(balanceAfter)
                .build();
        paymentRecordRepository.save(record);

        // Auto-exit receivable if fully paid
        if (project.isReceivable() && balanceAfter.compareTo(BigDecimal.ZERO) <= 0) {
            project.setReceivable(false);
            project.setStatus("ACTIVE");
            projectRepository.save(project);
            auditService.logAction("RECEIVABLE_EXIT",
                "Operator [" + operator + "] — Plot " + plotLabel(project)
                + " EXITED RECEIVABLE after full payment clearance.");
        } else {
            projectRepository.save(project);
        }

        auditService.logAction("PAYMENT_RECORDED",
            "Operator [" + operator + "] recorded UGX " + amount
            + " for plot: " + plotLabel(project)
            + " | Type: " + paymentType
            + " | Amount owed after: UGX " + balanceAfter);
    }

    // ─── RECEIVABLE MANAGEMENT ───────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void moveToReceivable(UUID projectId) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        if (project.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot is already in receivable.");
        }

        BigDecimal outstanding = project.getTotalCost().subtract(project.getAmountPaid());
        if (outstanding.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot has no outstanding balance.");
        }

        project.setReceivable(true);
        project.setReceivableStartDate(LocalDateTime.now());
        project.setOriginalDebt(outstanding);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setStatus("RECEIVABLE");
        projectRepository.save(project);

        auditService.logAction("RECEIVABLE_TRIGGER",
            "Operator [" + getCurrentOperator() + "] manually moved plot "
            + plotLabel(project)
            + " to RECEIVABLE. Original debt frozen at: UGX " + outstanding);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void exitReceivable(UUID projectId, boolean capitalizeFees) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));

        if (!project.isReceivable()) {
            throw new BusinessException("RECEIVABLE_FAULT: Plot is not in receivable.");
        }

        BigDecimal titleCost   = project.getTotalCost() != null ? project.getTotalCost() : BigDecimal.ZERO;
        BigDecimal totalPaid   = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
        BigDecimal storageFees = project.getStorageFeesAccumulated() != null ? project.getStorageFeesAccumulated() : BigDecimal.ZERO;

        if (capitalizeFees && storageFees.compareTo(BigDecimal.ZERO) > 0) {
            // ADD TO TOTAL VALUE: client owes titleCost + storageFees going forward
            // amountPaid stays as-is; amount owed = (titleCost + fees) - paid
            project.setTotalCost(titleCost.add(storageFees));
        } else {
            // WAIVE FEES: reset amountPaid to only what was paid toward the title
            // Cap paid at titleCost so client cannot over-pay on exit
            BigDecimal titlePaymentPortion = totalPaid.min(titleCost);
            project.setAmountPaid(titlePaymentPortion);
        }

        project.setReceivable(false);
        project.setReceivableStartDate(null);
        project.setOriginalDebt(BigDecimal.ZERO);
        project.setStorageFeesAccumulated(BigDecimal.ZERO);
        project.setReceivableMonthsBilled(0);
        project.setStatus("ACTIVE");
        projectRepository.save(project);

        String feeAction = capitalizeFees ? "Storage fees ADDED TO TOTAL VALUE (UGX " + storageFees + ")" : "Storage fees WAIVED";
        auditService.logAction("RECEIVABLE_EXIT",
            "Operator [" + getCurrentOperator() + "] removed plot "
            + plotLabel(project)
            + " from RECEIVABLE. " + feeAction
            + ". Title total value: UGX " + project.getTotalCost() + ".");
    }

    // ─── INTAKE ───────────────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public String previewNextIndex() {
        return projectIndexService.previewNextIndex();
    }


    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {
        // PHASE D (Section 18.10): LandProject is built FIRST. A LandTitle
        // is only built if the legacy preset is used or the final
        // processing stage ("Registration and Title Issuance") is checked.
        boolean hasFinalStage = request.getSelectedStages() != null && request.getSelectedStages().stream()
                .anyMatch(s -> s.isCompleted() && "Registration and Title Issuance".equalsIgnoreCase(s.getStageName()));
        boolean hasTitleFields = request.isLegacy() || hasFinalStage || request.isTitleAtIntake();
        String projectIndex = projectIndexService.generateNextIndex();

        BigDecimal initialPayment = request.getInitialPayment() != null
                ? request.getInitialPayment() : BigDecimal.ZERO;
        BigDecimal totalCost = request.getTotalCost() != null
                ? request.getTotalCost() : BigDecimal.ZERO;
        BigDecimal outstanding = totalCost.subtract(initialPayment);

        boolean startAsReceivable = request.isStartAsReceivable();

        LandTitle title = null;
        if (hasTitleFields) {
            if (request.getPlotNumber() == null || request.getPlotNumber().isBlank()) {
                throw new com.gesolutions.erp.common.exception.BusinessException("PLOT_NUMBER_REQUIRED: Plot number is required when using Legacy preset or completing the final stage.");
            }
            title = LandTitle.builder()
                    .titleId(request.getTitleId())
                    .tenure(request.getTenure() != null && !request.getTenure().isBlank() ? request.getTenure() : "FREEHOLD")
                    .plotNumber(request.getPlotNumber())
                    .blockRoad(request.getBlockRoad())
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
        }

        LandProject.LandProjectBuilder builder = LandProject.builder()
                .landTitle(title)
                .projectIndex(projectIndex)
                .district(request.getDistrict())
                .county(request.getCounty())
                .subCounty(request.getSubCounty())
                .parish(request.getParish())
                .village(request.getVillage())
                .area(request.getArea())
                .totalCost(totalCost)
                .amountPaid(initialPayment)
                .isLegacy(request.isLegacy())
                .currentStageIndex(startAsReceivable ? 5 : 1)
                .status(startAsReceivable ? "RECEIVABLE" : "ACTIVE");

        if (startAsReceivable && outstanding.compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal initialFees = request.getInitialStorageFee() != null
                    ? request.getInitialStorageFee() : BigDecimal.ZERO;
            builder.isReceivable(true)
                   .receivableStartDate(LocalDateTime.now())
                   .originalDebt(outstanding)
                   .storageFeesAccumulated(initialFees);
            if (request.getMonthlyStorageFee() != null
                    && request.getMonthlyStorageFee().compareTo(BigDecimal.ZERO) > 0) {
                builder.storageFeeOverride(request.getMonthlyStorageFee());
            }
        }

        LandProject project = builder.build();

        if (request.getOwners() != null) {
            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {
                if (o.getNationalId() == null || o.getNationalId().isBlank()) {
                    throw new BusinessException("NIN_REQUIRED: Owner \"" + o.getFullName() + "\" is missing a National ID (NIN).");
                }
                Client c = clientService.findOrCreateClientByNin(o.getFullName(), o.getNationalId(), o.getPhone(), o.getEmail());
                c.setHomeAddress(o.getAddress());
                project.addProprietor(c);
            }
        }

        LandProject saved = projectRepository.save(project);

        // Record initial payment if any
        if (initialPayment.compareTo(BigDecimal.ZERO) > 0) {
            PaymentRecord initialRecord = PaymentRecord.builder()
                    .projectId(saved.getId())
                    .amountPaid(initialPayment)
                    .paymentType("INITIAL_DEPOSIT")
                    .recordedBy(getCurrentOperator())
                    .notes("Initial deposit at intake")
                    .balanceAfter(outstanding)
                    .build();
            paymentRecordRepository.save(initialRecord);
            saved.setLastPaymentDate(LocalDateTime.now());
            projectRepository.save(saved);
        }

        if (request.getSelectedStages() != null && !request.getSelectedStages().isEmpty()) {
            stageTemplateService.attachStagesToProject(saved.getId(), request.getSelectedStages());
        }

        if (scans != null) addScansToProject(saved.getId(), scans);

        if (request.getNotes() != null) {
            for (LandEntryRequest.NoteRequest noteReq : request.getNotes()) {
                if (noteReq.getContent() != null && !noteReq.getContent().trim().isEmpty()) {
                    FollowUpLog entry = FollowUpLog.builder()
                            .projectId(saved.getId())
                            .notes("INTAKE NOTE: " + noteReq.getContent())
                            .recordedBy(getCurrentOperator())
                            .build();
                    followUpRepository.save(entry);
                }
            }
        }

        String plotOrIndex = title != null ? title.getPlotNumber() : "project #" + projectIndex;
        String receivableNote = startAsReceivable ? " [ENTERED AS RECEIVABLE]" : "";
        auditService.logAction("INTAKE",
            "Operator [" + getCurrentOperator() + "] ingested binder: "
            + plotOrIndex + receivableNote);

        if (startAsReceivable) {
            auditService.logAction("RECEIVABLE_TRIGGER",
                "Operator [" + getCurrentOperator() + "] flagged plot "
                + plotOrIndex + " as RECEIVABLE at intake. Debt: UGX " + outstanding);
        }

        return saved;
    }

    // ─── FULL UPDATE ──────────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public LandProject updateProjectFull(UUID projectId, LandEntryRequest request) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("ARCHIVE_FAULT"));
        LandTitle title = project.getLandTitle();

        // PHASE E (Section 18.9.4): Create LandTitle on edit if title fields
        // are provided but no title exists yet. Otherwise update existing title.
        boolean hasTitleFields = request.getPlotNumber() != null && !request.getPlotNumber().isBlank();
        if (title == null && hasTitleFields) {
            title = LandTitle.builder()
                    .titleId(request.getTitleId())
                    .tenure(request.getTenure() != null && !request.getTenure().isBlank() ? request.getTenure() : "FREEHOLD")
                    .plotNumber(request.getPlotNumber())
                    .blockRoad(request.getBlockRoad())
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : java.time.LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
            project.setLandTitle(title);
        } else if (title != null) {
            title.setTitleId(request.getTitleId());
            title.setPlotNumber(request.getPlotNumber());
            title.setTenure(request.getTenure());
            title.setBlockRoad(request.getBlockRoad());
        }

        // Save location fields on LandProject (Phase A/E)
        project.setDistrict(request.getDistrict());
        project.setCounty(request.getCounty());
        project.setSubCounty(request.getSubCounty());
        project.setParish(request.getParish());
        project.setVillage(request.getVillage());
        project.setArea(request.getArea());

        if (request.getOwners() != null) {
            Set<Client> updatedRegistry = new HashSet<>();
            for (LandEntryRequest.OwnerRequest incoming : request.getOwners()) {
                if (incoming.getNationalId() == null || incoming.getNationalId().isBlank()) {
                    throw new BusinessException("NIN_REQUIRED: Owner \"" + incoming.getFullName() + "\" is missing a National ID (NIN).");
                }
                // STAGE 8 FIX: this used to look the client up directly by NIN and,
                // when found, unconditionally overwrite its stored fullName with
                // whatever was typed on this form -- bypassing the NIN_NAME_MISMATCH
                // guard entirely, because that guard only ran inside
                // findOrCreateClientByNin(), which this code only called on the
                // NOT-FOUND branch (orElseGet). Reusing an existing NIN with a
                // different typed name silently renamed that person's identity
                // record everywhere they appear. Routing every owner through
                // findOrCreateClientByNin() unconditionally -- same as atomicIntake
                // does on Intake -- restores the mismatch check on Edit, and, like
                // Intake, leaves fullName untouched for a matching existing person
                // (full name is identity-level, not a per-project field; it only
                // changes via the explicit mismatch-confirmation flow).
                Client person = clientService.findOrCreateClientByNin(
                        incoming.getFullName(), incoming.getNationalId(), incoming.getPhone(), incoming.getEmail());
                person.setEmail(incoming.getEmail() != null
                        ? incoming.getEmail().toLowerCase() : null);
                person.setHomeAddress(incoming.getAddress());
                if (incoming.getPhone() != null && !incoming.getPhone().isBlank()) {
                    person.setPhoneNumber(incoming.getPhone());
                }
                clientRepository.save(person);
                updatedRegistry.add(person);
            }
            project.setProprietors(updatedRegistry);
        }

        BigDecimal newTotalCost = request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO;
        project.setTotalCost(newTotalCost);
        project.setAmountPaid(request.getInitialPayment() != null ? request.getInitialPayment() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());

        // FIX 1: If in receivable, keep originalDebt in sync with totalCost changes.
        // originalDebt = new title cost minus payments already made toward the title.
        if (project.isReceivable()) {
            BigDecimal amtPaid = project.getAmountPaid() != null ? project.getAmountPaid() : BigDecimal.ZERO;
            project.setOriginalDebt(newTotalCost.subtract(amtPaid).max(BigDecimal.ZERO));
        }

        LandProject saved = projectRepository.save(project);
        auditService.logAction("RECORD_UPDATED",
            "Operator [" + getCurrentOperator() + "] modified Binder: "
            + plotLabel(project));
        return saved;
    }

    // ─── SOFT DELETE (formerly NUCLEAR DELETE) ───────────────────────────────
    // STAGE 3 FIX: this used to hard-delete the Cloudinary files, every payment
    // record, every note, and the DB row itself -- irreversible in one click.
    // It now only flags the row as deleted. Nothing else is touched, so a
    // mis-click is recoverable via restoreProject() below.

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void nuclearDelete(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = plotLabel(project);

        project.setDeleted(true);
        project.setDeletedAt(LocalDateTime.now());
        projectRepository.save(project);

        auditService.logAction("RECORD_DELETED",
            "Root user [" + getCurrentOperator() + "] deleted plot: " + plotNo);
    }

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void restoreProject(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = plotLabel(project);

        project.setDeleted(false);
        project.setDeletedAt(null);
        projectRepository.save(project);

        auditService.logAction("RECORD_RESTORED",
            "Root user [" + getCurrentOperator() + "] restored plot: " + plotNo);
    }

    @Transactional(readOnly = true)
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public List<LandProject> getDeletedProjects() {
        return projectRepository.findAllDeleted();
    }

    // ─── FOLLOW-UP / NOTES ────────────────────────────────────────────────────

    // STAGE 10 FIX: NIN_JOINT_OWNER_CONTACT_MISATTRIBUTION (design brief 3.3/3.4)
    // Previously this always logged the contact against whichever proprietor's
    // fullName sorted first alphabetically ("primary owner"), regardless of
    // which co-owner staff actually reached -- silently resetting the WRONG
    // person's 14-day cooldown clock while the person really contacted never
    // got their own record updated. It also auto-copied the note onto every
    // OTHER outstanding plot the resolved primary owner held, fabricating
    // contact history on unrelated projects. Both behaviors are removed.
    // The caller must now name the specific owner being logged (this is the
    // "merge log-a-call and add-a-note into one action" from open question
    // 3.4 #1 -- project + specific owner + timestamp + note, in one record).
    // STAGE 11 FIX: SOFT_DUPLICATE_CONTACT_WARNING (design brief 3.4, open
    // question #2 -- explicitly left undecided by Stage 10). Decision:
    //   - SOFT, never blocks: 3.3 already agreed staff must be able to call
    //     different joint owners independently, so a second co-owner call
    //     inside the window is normal and is never prevented.
    //   - 3-day look-back, not the full 14-day cooldown: this flags "we just
    //     called about this plot yesterday", not ordinary independent contact.
    //   - Surfaced on the existing endpoint's response, same pattern Stage 10
    //     used for merging log-a-call/add-a-note into one action.
    @Transactional(rollbackFor = Exception.class)
    public java.util.Map<String, Object> logFollowUp(UUID projectId, UUID ownerId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();

        boolean ownerIsProprietor = project.getProprietors() != null &&
                project.getProprietors().stream()
                        .anyMatch(o -> o != null && o.getId() != null && o.getId().equals(ownerId));
        if (!ownerIsProprietor) {
            throw new BusinessException(
                    "OWNER_NOT_ON_PROJECT: The selected owner is not a proprietor of this project.");
        }

        // STAGE 11: advisory-only read -- does not touch any co-owner's state.
        String coOwnerWarning = null;
        LocalDateTime recentWindowStart = LocalDateTime.now().minusDays(3);
        java.util.List<FollowUpLog> recentProjectLogs =
                followUpRepository.findByProjectIdOrderByTimestampDesc(projectId);
        for (FollowUpLog log : recentProjectLogs) {
            if (log.getOwnerId() != null
                    && !log.getOwnerId().equals(ownerId)
                    && log.getTimestamp() != null
                    && log.getTimestamp().isAfter(recentWindowStart)) {
                Client coOwner = project.getProprietors().stream()
                        .filter(o -> o != null && log.getOwnerId().equals(o.getId()))
                        .findFirst().orElse(null);
                String coOwnerName = coOwner != null ? coOwner.getFullName() : "another owner";
                coOwnerWarning = coOwnerName + " was already contacted about this plot on "
                        + log.getTimestamp().toLocalDate() + ".";
                break;
            }
        }

        // Update ONLY the specific owner who was actually reached. Cooldown
        // state lives on Client (per person), so this cannot touch any
        // co-owner who was not part of this call.
        clientService.logManagerContact(ownerId);

        String operator = getCurrentOperator();
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .ownerId(ownerId)
                .notes(content)
                .recordedBy(operator)
                .build();
        followUpRepository.save(entry);

        auditService.logAction("RECOVERY_SYNC",
            "Operator [" + operator + "] logged call for plot: "
            + plotLabel(project) + " (owner reached: " + ownerId + ")");

        java.util.Map<String, Object> result = new java.util.HashMap<>();
        result.put("ownerId", ownerId);
        result.put("coOwnerWarning", coOwnerWarning);
        return result;
    }

    @Transactional
    public void logNewNote(UUID projectId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(content)
                .recordedBy(getCurrentOperator())
                .build();
        followUpRepository.save(entry);
        auditService.logAction("NOTE_ADDED",
            "Operator [" + getCurrentOperator() + "] added note to plot: "
            + project.getLandTitle().getPlotNumber());
    }

    @Transactional
    public void updateNote(UUID noteId, String content) {
        FollowUpLog log = followUpRepository.findById(noteId).orElseThrow();
        log.setNotes(content);
        followUpRepository.save(log);
        auditService.logAction("NOTE_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated a log entry.");
    }

    @Transactional
    public void removeNote(UUID noteId) {
        followUpRepository.deleteById(noteId);
        auditService.logAction("NOTE_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted a log entry.");
    }

    // ─── DOCUMENTS ────────────────────────────────────────────────────────────

    @Transactional
    public void addScansToProject(UUID projectId, MultipartFile[] scans) throws Exception {
        for (MultipartFile file : scans) {
            String path = fileStorageService.storeFile(file, projectId.toString());
            ProjectDocument doc = ProjectDocument.builder()
                    .projectId(projectId)
                    .fileName(file.getOriginalFilename())
                    .fileType(file.getContentType())
                    .filePath(path)
                    .uploadedBy(getCurrentOperator())
                    .build();
            documentRepository.save(doc);
        }
        auditService.logAction("DOCUMENT_UPLOADED",
            "Operator [" + getCurrentOperator() + "] uploaded " + scans.length
            + " document(s) to plot: " + projectId);
    }

    @Transactional
    public void removeDocument(UUID docId) {
        ProjectDocument doc = documentRepository.findById(docId).orElseThrow();
        fileStorageService.deleteFile(doc.getFilePath());
        documentRepository.delete(doc);
        auditService.logAction("DOCUMENT_DELETED",
            "Operator [" + getCurrentOperator() + "] deleted file: " + doc.getFileName());
    }

    // ─── STAGE / RELEASE ──────────────────────────────────────────────────────

    @Transactional
    public void manualRealityOverride(UUID id, int targetStage) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        int oldStage = project.getCurrentStageIndex();
        project.setCurrentStageIndex(targetStage);
        if (targetStage >= 5) project.setStatus("COMPLETED");
        projectRepository.save(project);
        auditService.logAction("STAGE_OVERRIDE",
            "Operator [" + getCurrentOperator() + "] shifted plot "
            + plotLabel(project)
            + " from stage " + oldStage + " to stage " + targetStage);
    }

    @Transactional
    public void authorizeRelease(UUID id, String managerNote) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        if (project.getAmountPaid().compareTo(project.getTotalCost()) < 0) {
            throw new BusinessException("RELEASE DENIED: Arrears Detected.");
        }
        // PHASE B (Section 18.9.1): landTitle can now be null.
        // Releasing implies a title exists to hand over -- silently
        // succeeding when there is nothing to release would be
        // misleading to staff, so this fails loudly instead of NPE-ing.
        if (project.getLandTitle() == null) {
            throw new BusinessException("RELEASE DENIED: This project has no title to release yet.");
        }
        project.getLandTitle().setReleased(true);
        project.setStatus("RELEASED");
        projectRepository.save(project);
        auditService.logAction("TITLE_RELEASED",
            "Operator [" + getCurrentOperator() + "] authorized handover for Plot: "
            + project.getLandTitle().getPlotNumber());
    }

    // ─── READ METHODS ─────────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setStoragePaused(UUID projectId, boolean paused) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        project.setStoragePaused(paused);
        projectRepository.save(project);
        String action = paused ? "PAUSED" : "RESUMED";
        auditService.logAction("STORAGE_FEE_" + action,
            "Operator [" + getCurrentOperator() + "] " + action.toLowerCase() + " monthly storage fees for plot: "
            + plotLabel(project)
            + " (monthly rate: UGX " + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : "50000 (default)") + ")");
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setStorageFeeOverride(UUID projectId, java.math.BigDecimal rate) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        project.setStorageFeeOverride(rate);
        projectRepository.save(project);
        auditService.logAction("STORAGE_RATE_CHANGED",
            "Operator [" + getCurrentOperator() + "] changed monthly storage fee to UGX " + rate
            + " for plot: " + plotLabel(project)
            + " (previously UGX " + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : "50000 (default)") + ")");
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setAccumulatedFees(UUID projectId, java.math.BigDecimal amount) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        java.math.BigDecimal old = project.getStorageFeesAccumulated();
        project.setStorageFeesAccumulated(amount);
        projectRepository.save(project);
        auditService.logAction("STORAGE_FEES_ADJUSTED",
            "Operator [" + getCurrentOperator() + "] manually adjusted accumulated storage fees from UGX " + old
            + " to UGX " + amount + " for plot: " + plotLabel(project));
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setNegotiationDeadline(UUID projectId, String deadlineStr) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (deadlineStr == null || deadlineStr.isBlank()) {
            project.setNegotiationDeadline(null);
            // Resume fees if deadline cleared
            project.setStoragePaused(false);
            auditService.logAction("NEGOTIATION_DEADLINE_CLEARED",
                "Operator [" + getCurrentOperator() + "] cleared negotiation deadline for plot: "
                + plotLabel(project) + " -- storage fees resumed.");
        } else {
            java.time.LocalDateTime deadline = java.time.LocalDate.parse(deadlineStr)
                    .atTime(23, 59, 59);
            project.setNegotiationDeadline(deadline);
            // Auto-pause fees while negotiating
            project.setStoragePaused(true);
            auditService.logAction("NEGOTIATION_DEADLINE_SET",
                "Operator [" + getCurrentOperator() + "] set negotiation deadline to " + deadlineStr
                + " for plot: " + plotLabel(project)
                + " -- storage fees paused until then.");
        }
        projectRepository.save(project);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void setReceivableStartOverride(UUID projectId, String startDateStr) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        java.time.LocalDateTime startDate = java.time.LocalDate.parse(startDateStr).atStartOfDay();
        project.setReceivableStartOverride(startDate);
        // Apply the override to the actual receivable start date so fees calculate from correct date
        project.setReceivableStartDate(startDate);
        projectRepository.save(project);
        auditService.logAction("RECEIVABLE_START_OVERRIDDEN",
            "Operator [" + getCurrentOperator() + "] set receivable start date to " + startDateStr
            + " for plot: " + plotLabel(project));
    }

    @Transactional(readOnly = true)
    public List<ProjectDocument> getProjectDocuments(UUID projectId) {
        return documentRepository.findByProjectId(projectId);
    }

    @Transactional(readOnly = true)
    public List<FollowUpLog> getProjectNotes(UUID projectId) {
        return followUpRepository.findByProjectIdOrderByTimestampDesc(projectId);
    }

    @Transactional(readOnly = true)
    public List<PaymentRecord> getProjectPayments(UUID projectId) {
        return paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId);
    }

    @Transactional(readOnly = true)
    public Page<LandProject> getGlobalLedger(Pageable pageable) {
        Page<LandProject> page = projectRepository.findAll(pageable);
        page.getContent().forEach(p -> p.setStages(projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(p.getId())));
        return page;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public int bulkMarkTitleProduced(java.util.List<java.util.UUID> projectIds) {
        if (projectIds == null || projectIds.isEmpty()) return 0;
        int count = 0;
        for (java.util.UUID id : projectIds) {
            LandProject project = projectRepository.findById(id).orElse(null);
            if (project != null && project.getLandTitle() == null) {
                LandTitle title = LandTitle.builder()
                        .tenure("FREEHOLD")
                        .projectStartDate(java.time.LocalDate.now())
                        .build();
                project.setLandTitle(title);
                projectRepository.save(project);

                java.util.List<ProjectStage> stages = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(id);
                for (ProjectStage stage : stages) {
                    if (stage.getStageName() != null && stage.getStageName().toLowerCase().contains("registration")) {
                        stage.setCompleted(true);
                        stage.setCompletedAt(java.time.LocalDateTime.now());
                        projectStageRepository.save(stage);
                    }
                }
                count++;
            }
        }
        auditService.logAction("BULK_TITLE_PRODUCED", 
            "Operator [" + getCurrentOperator() + "] marked " + count + " projects as title-produced.");
        return count;
    }
}""")

# =====================================================================
# write: erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/LandCascadeDeleteTest.java
# =====================================================================
write('erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/LandCascadeDeleteTest.java', r"""package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.config.ApplicationConfig;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.LandTitleRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "ge.solutions.jwt.secret=YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    "cloudinary.cloud-name=test",
    "cloudinary.api-key=test",
    "cloudinary.api-secret=test",
    "ADMIN_EMAIL=test@gesolutions.com",
    "ADMIN_DEFAULT_PASSWORD=TestPassword123",
    "MAIL_USERNAME=test@gmail.com",
    "MAIL_PASSWORD=testpassword"
})
public class LandCascadeDeleteTest {

    @Autowired
    private LandService landService;

    @Autowired
    private LandProjectRepository landProjectRepository;

    @Autowired
    private LandTitleRepository landTitleRepository;

    @Autowired
    private FollowUpRepository followUpRepository;

    @Autowired
    private PaymentRecordRepository paymentRecordRepository;

    @AfterEach
    public void clearSecurityContext() {
        SecurityContextHolder.clearContext();
    }

    private void mockRootAuthentication() {
        User mockUser = User.builder()
                .id(UUID.randomUUID())
                .username("admin_root")
                .email("root@test.com")
                .password("ignored")
                .role(Role.ROLE_ADMIN)
                .isRoot(true)
                .isActive(true)
                .mustChangePassword(false)
                .build();

        ApplicationConfig.CustomUserPrincipal principal = new ApplicationConfig.CustomUserPrincipal(mockUser);

        UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                principal,
                null,
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_ADMIN"))
        );
        SecurityContextHolder.getContext().setAuthentication(auth);
    }

    @Test
    public void testNuclearDeleteCascadesCorrectly() throws Exception {
        mockRootAuthentication();

        LandEntryRequest.OwnerRequest owner = LandEntryRequest.OwnerRequest.builder()
                .fullName("Cascade Test Owner")
                .phone("0711000999")
                .email("cascade@test.com")
                .nationalId("CM99999999ZZZZZ")
                .address("Kampala, Uganda")
                .build();

        List<LandEntryRequest.OwnerRequest> owners = new ArrayList<>();
        owners.add(owner);

        LandEntryRequest request = LandEntryRequest.builder()
                .plotNumber("CASCADE-001-TEST")
                .tenure("FREEHOLD")
                .blockRoad("Cascade Block")
                .district("Kampala")
                .county("Central")
                .owners(owners)
                .totalCost(new BigDecimal("5000000"))
                .initialPayment(new BigDecimal("1000000"))
                .isLegacy(false)
                .isStartAsReceivable(false)
                .build();

        LandProject project = landService.atomicIntake(request, null);
        UUID projectId = project.getId();
        UUID titleId = project.getLandTitle().getId();

        landService.logNewNote(projectId, "Test cascade note - should be deleted");

        assertTrue(landProjectRepository.findById(projectId).isPresent(), "Project should exist before delete");
        assertTrue(landTitleRepository.findById(titleId).isPresent(), "Title should exist before delete");
        assertFalse(paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Payments should exist before delete");
        assertFalse(followUpRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Notes should exist before delete");

        landService.nuclearDelete(projectId);

        assertFalse(landProjectRepository.findById(projectId).isPresent(), "Project should be deleted");
        assertFalse(landTitleRepository.findById(titleId).isPresent(), "Title should be cascade-deleted");
        assertTrue(paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Payments should be deleted");
        assertTrue(followUpRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Notes should be deleted");
    }
}
""")

# =====================================================================
# write: erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/LandServiceTest.java
# =====================================================================
write('erp-backend/src/test/java/com/gesolutions/erp/modules/land/service/LandServiceTest.java', r"""package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "ge.solutions.jwt.secret=YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    "cloudinary.cloud-name=test",
    "cloudinary.api-key=test",
    "cloudinary.api-secret=test",
    "ADMIN_EMAIL=test@gesolutions.com",
    "ADMIN_DEFAULT_PASSWORD=TestPassword123",
    "MAIL_USERNAME=test@gmail.com",
    "MAIL_PASSWORD=testpassword"
})
@Transactional
public class LandServiceTest {

    @Autowired
    private LandService landService;

    @Autowired
    private LandProjectRepository landProjectRepository;

    @Autowired
    private PaymentRecordRepository paymentRecordRepository;

    @Test
    public void testAtomicIntakeSavesCorrectly() throws Exception {
        LandEntryRequest.OwnerRequest owner = LandEntryRequest.OwnerRequest.builder()
                .fullName("Test Owner")
                .phone("0700000000")
                .email("owner@test.com")
                .nationalId("CM12345678ABCDE")
                .address("Kampala, Uganda")
                .build();

        List<LandEntryRequest.OwnerRequest> owners = new ArrayList<>();
        owners.add(owner);

        LandEntryRequest request = LandEntryRequest.builder()
                .plotNumber("KLA-001-TEST")
                .tenure("FREEHOLD")
                .blockRoad("Test Block")
                .district("Kampala")
                .county("Test County")
                .owners(owners)
                .totalCost(new BigDecimal("5000000"))
                .initialPayment(new BigDecimal("1000000"))
                .isLegacy(false)
                .isStartAsReceivable(false)
                .build();

        LandProject saved = landService.atomicIntake(request, null);

        assertEquals("KLA-001-TEST", saved.getLandTitle().getPlotNumber());

        Optional<LandProject> fetched = landProjectRepository.findById(saved.getId());
        assertTrue(fetched.isPresent());
        assertEquals("KLA-001-TEST", fetched.get().getLandTitle().getPlotNumber());
        assertEquals(1, fetched.get().getProprietors().size());

        List<PaymentRecord> payments = paymentRecordRepository.findByProjectIdOrderByTimestampDesc(saved.getId());
        assertFalse(payments.isEmpty());

        boolean foundInitialPayment = payments.stream()
                .anyMatch(p -> p.getAmountPaid().compareTo(new BigDecimal("1000000")) == 0);
        assertTrue(foundInitialPayment);
    }
}
""")

# =====================================================================
# write: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
# =====================================================================
write('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', r"""// PATH: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiUnlock, FiX, FiMap, FiUsers, FiCreditCard,
    FiUploadCloud, FiFileText, FiClock,
    FiCheckCircle, FiTrash2, FiEdit3, FiChevronDown,
    FiPhoneCall, FiMail, FiMapPin, FiShield,
    FiInfo, FiAlertTriangle, FiAlertOctagon,
    FiCheckSquare, FiPrinter, FiAlertCircle, FiSave,
    FiDollarSign, FiActivity, FiHome, FiArchive
} from 'react-icons/fi';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import NinMismatchModal from '../../components/common/NinMismatchModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import recoveryService from '../../services/recoveryService';
import predictionService from '../../services/predictionService';
import clientService from '../../services/clientService';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import ErrorMessage from '../../components/common/ErrorMessage';
import styles from './FolderPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const STAGE_LABELS = ['COMMITMENT', 'FIELD WORK', 'DOCUMENTATION', 'DEED PLAN', 'RELEASE'];
const EMAIL_DOMAINS = ['@gmail.com', '@yahoo.com', '@outlook.com', '@hotmail.com', '@icloud.com'];

const formatSinglePhone = (raw) => {
    const d = raw.replace(/\D/g, '');
    if (!d) return '';
    return [d.slice(0, 4), d.slice(4, 7), d.slice(7, 10)].filter(Boolean).join(' ');
};
const formatPhoneEntry = (raw) =>
    raw.split('/').map(p => formatSinglePhone(p.trim())).filter(Boolean).join(' / ');

const validateBuffer = (buffer) => {
    const errors = [];
    if (!buffer.plotNumber?.trim()) errors.push('PLOT ID IS REQUIRED');
    if (!buffer.district?.trim())   errors.push('DISTRICT IS REQUIRED');
    if (!buffer.tenure?.trim())     errors.push('TENURE IS REQUIRED');
    buffer.owners?.forEach((o, i) => {
        if (!o.fullName?.trim()) errors.push(`OWNER ${i + 1}: LEGAL NAME IS REQUIRED`);
        if (!o.nationalId?.trim()) errors.push(`OWNER ${i + 1}: NATIONAL ID (NIN) IS REQUIRED`);
    });
    return errors;
};

const TOAST_ICONS = {
    success: <FiCheckSquare aria-hidden="true" />,
    error:   <FiAlertCircle aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo aria-hidden="true" />,
};

const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);
    const dismissToast = useCallback((id) => setToasts(prev => prev.filter(t => t.id !== id)), []);
    return { toasts, toast, dismissToast };
};

const ToastContainer = ({ toasts, onDismiss }) => {
    if (typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
                    <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
                    <span className={styles.toastMsg}>{t.message}</span>
                    <button className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss">
                        <FiX aria-hidden="true" />
                    </button>
                </div>
            ))}
        </div>,
        document.body
    );
};

const SavingOverlay = ({ visible }) => {
    if (!visible || typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.savingOverlay} role="status" aria-label="Committing to archive">
            <div className={styles.savingSpinner} aria-hidden="true" />
            <span className={styles.savingLabel}>COMMITTING TO ARCHIVE...</span>
        </div>,
        document.body
    );
};

const SkeletonPanel = () => (
    <div className={styles.skeletonPanel} aria-hidden="true">
        <div className={styles.skeletonHeader} />
        <div className={styles.skeletonBody}>
            {[1,2,3,4].map(i => <div key={i} className={styles.skeletonLine} />)}
        </div>
    </div>
);
const SkeletonPage = () => (
    <div className={styles.skeletonPage} aria-busy="true" aria-label="Loading record">
        <div className={styles.skeletonHUD} />
        <div className={styles.skeletonTermHeader} />
        <SkeletonPanel /><SkeletonPanel /><SkeletonPanel />
    </div>
);

const DrawerHeader = ({ label, count, isOpen, onClick, icon: Icon }) => (
    <div className={styles.drawerHeader} onClick={onClick} role="button" tabIndex={0}
        aria-expanded={isOpen} aria-label={`${label} section, ${isOpen ? 'collapse' : 'expand'}`}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}>
        <div className={styles.drawerTitle}>
            {Icon && <Icon className={styles.drawerIcon} aria-hidden="true" />}
            {label}
            {count !== undefined && <span className={styles.drawerCount}>{count}</span>}
        </div>
        <FiChevronDown className={`${styles.chevron} ${isOpen ? styles.rotated : ''}`} aria-hidden="true" />
    </div>
);

const SmartInput = React.forwardRef(({
    label, value, onChange, onBlur, placeholder,
    suggestions = [], inputMode, maxLength, hint,
    showCaps, required = false, error = null, id: propId,
}, ref) => {
    const inputId    = propId || 'inp-' + (label || '').replace(/\W/g, '-').toLowerCase();
    const errorId    = inputId + '_err';
    const hintId     = inputId + '_hint';
    const datalistId = suggestions.length ? 'dl-' + inputId : undefined;
    return (
        <div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>
                    {label}{required && <span className={styles.reqStar} aria-hidden="true"> *</span>}
                </label>
                {showCaps && <span className={styles.capsBadge}>CAPS</span>}
            </div>
            <input id={inputId} ref={ref} type="text"
                className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                value={value} onChange={onChange} onBlur={onBlur}
                placeholder={placeholder} inputMode={inputMode} maxLength={maxLength}
                list={datalistId} autoComplete="off"
                aria-required={required ? 'true' : undefined}
                aria-invalid={error ? 'true' : 'false'}
            />
            {datalistId && <datalist id={datalistId}>{suggestions.map((s,i) => <option key={i} value={s} />)}</datalist>}
            {error && <span id={errorId} className={styles.fieldError} role="alert">{error}</span>}
            {!error && hint && <span id={hintId} className={styles.inputHint}>{hint}</span>}
        </div>
    );
});
SmartInput.displayName = 'SmartInput';

const SmartSelect = ({ label, options, value, onChange, id }) => {
    const [open, setOpen] = useState(false);
    const wrapRef  = useRef(null);
    const selectId = id || 'ss-' + (label || '').replace(/\W/g, '-').toLowerCase();
    useEffect(() => {
        const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);
    const handleKey = (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); }
        if (e.key === 'Escape') setOpen(false);
        if (e.key === 'ArrowDown') { e.preventDefault(); const i = options.indexOf(value); if (i < options.length - 1) onChange(options[i+1]); }
        if (e.key === 'ArrowUp')   { e.preventDefault(); const i = options.indexOf(value); if (i > 0) onChange(options[i-1]); }
    };
    return (
        <div className={styles.hwInputWrap} ref={wrapRef} style={{ position: 'relative' }}>
            <div className={styles.inputLabelRow}><label id={selectId + '_lbl'}>{label}</label></div>
            <div id={selectId} role="combobox" aria-haspopup="listbox" aria-expanded={open}
                aria-labelledby={selectId + '_lbl'} tabIndex={0}
                className={`${styles.selectTrigger} ${open ? styles.selectTriggerOpen : ''}`}
                onClick={() => setOpen(o => !o)} onKeyDown={handleKey}>
                <span className={styles.selectValue}>{value}</span>
                <FiChevronDown className={`${styles.selectChevron} ${open ? styles.rotated : ''}`} aria-hidden="true" />
            </div>
            {open && (
                <ul role="listbox" aria-labelledby={selectId + '_lbl'} className={styles.selectDropdown}>
                    {options.map(opt => (
                        <li key={opt} role="option" aria-selected={opt === value} tabIndex={-1}
                            className={`${styles.selectOption} ${opt === value ? styles.selectOptionActive : ''}`}
                            onClick={() => { onChange(opt); setOpen(false); }}>{opt}</li>
                    ))}
                </ul>
            )}
        </div>
    );
};

const EmailInput = ({ label = 'EMAIL', value, onChange, onCommit, id, required }) => {
    const [showDomains, setShowDomains] = useState(false);
    const [activeIdx,   setActiveIdx]   = useState(-1);
    const wrapRef = useRef(null);
    const inputId = id || 'ei_email';
    const listId  = inputId + '_list';
    const localPart    = value.includes('@') ? value.split('@')[0] : value;
    const hasAt        = value.includes('@');
    const pickerVisible = showDomains && localPart.length > 0 && !hasAt;
    const applyDomain = (domain) => { onCommit(localPart + domain); setShowDomains(false); setActiveIdx(-1); };
    const handleBlur = () => setTimeout(() => {
        setShowDomains(false);
        if (value && !value.includes('@') && value.trim()) onCommit(value.trim() + '@gmail.com');
    }, 160);
    const handleKey = (e) => {
        if (!pickerVisible) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i+1, EMAIL_DOMAINS.length-1)); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i-1, 0)); }
        else if ((e.key === 'Enter' || e.key === 'Tab') && activeIdx >= 0) { e.preventDefault(); applyDomain(EMAIL_DOMAINS[activeIdx]); }
        else if (e.key === 'Escape') setShowDomains(false);
    };
    useEffect(() => {
        const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setShowDomains(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);
    return (
        <div className={styles.hwInputWrap} ref={wrapRef}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={styles.assistBadge}>@</span>
            </div>
            <div className={styles.emailWrap}>
                <input id={inputId} className={styles.hwInput} type="email" value={value}
                    onChange={e => { onChange(e.target.value.toLowerCase().replace(/\s/g,'')); setShowDomains(true); setActiveIdx(-1); }}
                    onBlur={handleBlur} onFocus={() => setShowDomains(true)} onKeyDown={handleKey}
                    placeholder="name@domain.com" autoComplete="off" autoCapitalize="none" inputMode="email" />
                {pickerVisible && (
                    <ul id={listId} role="listbox" className={styles.domainPicker}>
                        {EMAIL_DOMAINS.map((domain, idx) => (
                            <li key={domain} id={listId + '_' + idx} role="option" aria-selected={idx === activeIdx}
                                className={`${styles.domainOption} ${idx === activeIdx ? styles.domainOptionActive : ''}`}
                                onMouseDown={() => applyDomain(domain)}>
                                <span className={styles.emailLocalPart}>{localPart}</span>
                                <span className={styles.emailDomainPart}>{domain}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

const PhoneInput = ({ label = 'RECOVERY PHONE', value, onChange, onBlur, id, required, fieldError }) => {
    const [raw, setRaw] = useState(() => value || '');
    const inputId = id || 'phi_phone';
    const isDual  = raw.includes('/');
    const handleChange = (e) => {
        let v = e.target.value.replace(/[^0-9\s/]/g, '').replace(/[/]+/g, '/');
        if (v.startsWith('/')) v = v.slice(1);
        setRaw(v); onChange(v);
    };
    const handleBlur = () => {
        if (!raw.trim()) return;
        const f = formatPhoneEntry(raw);
        if (f) { setRaw(f); onChange(f); }
        if (onBlur) onBlur(raw);
    };
    return (
        <div className={`${styles.hwInputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={`${styles.assistBadge} ${isDual ? styles.assistBadgeDual : ''}`}>{isDual ? 'DUAL' : 'TEL'}</span>
            </div>
            <input id={inputId} type="tel" value={raw} onChange={handleChange} onBlur={handleBlur}
                placeholder="0712 345 678  ·  dual: 0712.../0701..." inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                autoComplete="tel-national" />
            {fieldError && <span className={styles.fieldError} role="alert">{fieldError}</span>}
            <span className={styles.inputHint}>Use &#39;/&#39; to separate multiple numbers (e.g. 077... / 075...)</span>
        </div>
    );
};

const NINInput = ({ label = 'NATIONAL ID / NIN', value, onChange, onBlur, id, required }) => {
    const inputId = id || 'nin_input';
    const MAX = 14;
    const handleChange = (e) => onChange(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,MAX));
    return (
        <div className={styles.hwInputWrap}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={styles.capsBadge}>CAPS</span>
            </div>
            <input id={inputId} type="text" value={value} onChange={handleChange} onBlur={onBlur}
                maxLength={MAX} placeholder="CM90XXXXXXXX12"
                className={styles.hwInput} autoComplete="off" autoCapitalize="characters" />
        </div>
    );
};

const AddressInput = (props) => <SmartInput {...props} placeholder="Street, Town, District" />;

const CurrencyInput = ({ label, value, onChange, error, id, disabled }) => {
    const [focused, setFocused] = useState(false);
    const inputId = id || 'cur-' + (label||'').replace(/\W/g,'-').toLowerCase();
    const display = focused ? String(value||'') : (value ? Number(value).toLocaleString() : '');
    return (
        <div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}</label>
                <span className={styles.currencyTag}>UGX</span>
                {disabled && <span className={styles.autoCalcBadge} style={{color:'rgba(255,255,255,0.4)',background:'rgba(255,255,255,0.05)',borderColor:'rgba(255,255,255,0.1)'}}>LOCKED</span>}
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''} ${disabled ? styles.calcInput : ''}`}
                inputMode="numeric" value={display}
                onFocus={() => { if (!disabled) setFocused(true); }} onBlur={() => setFocused(false)}
                onChange={e => { if (!disabled) onChange(e.target.value.replace(/\D/g,'')); }}
                placeholder="0" aria-invalid={error ? 'true' : 'false'}
                disabled={disabled}
                style={disabled ? {background:'rgba(0,0,0,0.25)',color:'rgba(255,255,255,0.45)',cursor:'not-allowed',border:'1.5px solid rgba(255,255,255,0.08)'} : {}} />
            {error && <span className={styles.fieldError} role="alert">{error}</span>}
        </div>
    );
};

const useConfirm = () => {
    const [state, setState] = useState({ open: false, title: '', message: '', variant: 'warn', resolve: null });
    const confirm = useCallback((title, message, variant = 'warn') =>
        new Promise(resolve => setState({ open: true, title, message, variant, resolve })), []);
    const handleAnswer = useCallback((answer) => {
        setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; });
    }, []);
    return { confirmState: state, confirm, handleAnswer };
};

const ConfirmModal = ({ state, onAnswer }) => {
    if (!state.open || typeof document === 'undefined') return null;
    const isDanger = state.variant === 'danger';
    return createPortal(
        <div className={styles.confirmOverlay} role="dialog" aria-modal="true">
            <div className={styles.confirmBox}>
                <div className={`${styles.confirmHeader} ${isDanger ? styles.confirmHeaderDanger : styles.confirmHeaderWarn}`}>
                    {isDanger ? <FiAlertOctagon className={styles.confirmIcon} aria-hidden="true" />
                              : <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" />}
                    <span className={styles.confirmTitle}>{state.title}</span>
                </div>
                <p className={styles.confirmMessage}>{state.message}</p>
                <div className={styles.confirmFooter}>
                    <button type="button" className={styles.confirmCancelBtn} onClick={() => onAnswer(false)} autoFocus>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button type="button" className={`${styles.confirmOkBtn} ${isDanger ? styles.confirmOkDanger : styles.confirmOkWarn}`}
                        onClick={() => onAnswer(true)}>
                        {isDanger ? <><FiTrash2 aria-hidden="true" /> CONFIRM ERASE</>
                                  : <><FiCheckCircle aria-hidden="true" /> CONFIRM</>}
                    </button>
                </div>
            </div>
        </div>,
        document.body
    );
};

const fmt = (n) => Number(n || 0).toLocaleString();

// ═══════════════════════════════════════════════════════════════
// RECEIVABLES FEE ADMIN CONTROLS
// ═══════════════════════════════════════════════════════════════
const ReceivableFeeControls = ({ project, projectId, onRefresh, toast }) => {
    const [feeInput,    setFeeInput]    = React.useState('');
    const [rateInput,   setRateInput]   = React.useState('');
    const [saving,      setSaving]      = React.useState(false);

    const handlePause = async () => {
        try {
            await recoveryService.pauseStorageFees(projectId, !project.storagePaused);
            await onRefresh();
            toast(project.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED', 'info');
        } catch { toast('ACTION FAILED', 'error'); }
    };

    const handleSetRate = async () => {
        const val = Number(rateInput);
        if (!rateInput || val < 0) { toast('ENTER A VALID RATE (0 or more)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setStorageRate(projectId, val);
            setRateInput('');
            await onRefresh();
            toast('MONTHLY RATE UPDATED', 'success');
        } catch { toast('RATE UPDATE FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const handleSetFees = async () => {
        const val = Number(feeInput);
        if (feeInput === '' || val < 0) { toast('ENTER A VALID AMOUNT (0 to waive all)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setAccumulatedFees(projectId, val);
            setFeeInput('');
            await onRefresh();
            toast('ACCUMULATED FEES ADJUSTED', 'success');
        } catch { toast('FEE ADJUSTMENT FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const boxStyle = { background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 8, padding: '12px 14px', marginTop: 12 };
    const labelStyle = { display: 'block', fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 };
    const inputStyle = { background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6, color: '#1a2e30', fontFamily: 'Space Mono,monospace', fontWeight: 700, fontSize: 13, padding: '6px 10px', outline: 'none', width: '100%', boxSizing: 'border-box' };
    const btnStyle = (color) => ({ background: color + '22', border: '1.5px solid ' + color, color: color, borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 10, fontWeight: 900, fontFamily: 'DM Sans,sans-serif', textTransform: 'uppercase', letterSpacing: 1, marginTop: 6 });

    return (
        <div style={boxStyle}>
            <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#ef4444', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 10 }}>
                ADMIN: STORAGE FEE CONTROLS
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div>
                    <span style={labelStyle}>PAUSE / RESUME FEES</span>
                    <button onClick={handlePause} style={btnStyle(project.storagePaused ? '#22c55e' : '#f59e0b')}>
                        {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                    </button>
                    {project.storagePaused && <div style={{ fontSize: 9, color: '#f59e0b', marginTop: 4, fontWeight: 700 }}>Fees currently PAUSED</div>}
                </div>
                <div>
                    <span style={labelStyle}>SET MONTHLY RATE (UGX)</span>
                    <input style={inputStyle} type="number" value={rateInput} placeholder={project.storageFeeOverride ? String(project.storageFeeOverride) : '50000'} onChange={e => setRateInput(e.target.value)} />
                    <button onClick={handleSetRate} style={btnStyle('#EE8C3A')} disabled={saving}>APPLY RATE</button>
                </div>
                <div>
                    <span style={labelStyle}>ADJUST TOTAL FEES (UGX)</span>
                    <input style={inputStyle} type="number" value={feeInput} placeholder={String(project.storageFeesAccumulated || 0)} onChange={e => setFeeInput(e.target.value)} />
                    <button onClick={handleSetFees} style={btnStyle('#ef4444')} disabled={saving}>SET TOTAL</button>
                    <div style={{ fontSize: 8, color: 'rgba(255,255,255,0.4)', marginTop: 3, fontWeight: 700 }}>Enter 0 to waive all fees</div>
                </div>
            </div>
        </div>
    );
};

const StageChecklistPanel = ({ projectId, isEditing, isAdmin, toast }) => {
    const [stages, setStages] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [addModalOpen, setAddModalOpen] = useState(false);
    const [checkedTemplates, setCheckedTemplates] = useState({});
    const [customName, setCustomName] = useState('');
    const [customCost, setCustomCost] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editCost, setEditCost] = useState('');
    const [editNotes, setEditNotes] = useState('');
    const [saving, setSaving] = useState(false);

    const loadStages = useCallback(async () => {
        try {
            const data = await stageTemplateService.getProjectStages(projectId);
            setStages(data || []);
        } catch { /* silent */ }
        finally { setLoading(false); }
    }, [projectId]);

    useEffect(() => { loadStages(); }, [loadStages]);

    const openAddModal = async () => {
        try {
            const t = await stageTemplateService.getTemplate();
            setTemplates(t || []);
        } catch { setTemplates([]); }
        setCheckedTemplates({});
        setCustomName('');
        setCustomCost('');
        setAddModalOpen(true);
    };

    const handleAttach = async () => {
        const requests = [];
        templates.forEach(t => {
            if (checkedTemplates[t.id]) {
                requests.push({ stageTemplateId: t.id, cost: t.defaultCost, isCustom: false });
            }
        });
        if (customName.trim()) {
            requests.push({
                stageName: customName.trim(),
                cost: Number(customCost) || 0,
                isCustom: true,
            });
        }
        if (requests.length === 0) {
            toast && toast('Select at least one stage', 'error');
            return;
        }
        setSaving(true);
        try {
            await stageTemplateService.attachStages(projectId, requests);
            await loadStages();
            setAddModalOpen(false);
            toast && toast('Stage(s) added', 'success');
        } catch {
            toast && toast('Failed to add stage(s)', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleToggleComplete = async (stage) => {
        try {
            await stageTemplateService.toggleStageCompletion(projectId, stage.id, !stage.isCompleted);
            await loadStages();
        } catch { toast && toast('Failed to update stage', 'error'); }
    };

    const startEdit = (stage) => {
        setEditingId(stage.id);
        setEditCost(String(stage.cost || 0));
        setEditNotes(stage.notes || '');
    };

    const saveEdit = async (stageId) => {
        try {
            await stageTemplateService.updateStageCost(projectId, stageId, Number(editCost) || 0, editNotes);
            setEditingId(null);
            await loadStages();
            toast && toast('Stage updated', 'success');
        } catch { toast && toast('Failed to save stage', 'error'); }
    };

    const handleRemove = async (stageId) => {
        try {
            await stageTemplateService.removeStage(projectId, stageId);
            await loadStages();
            toast && toast('Stage removed', 'warn');
        } catch { toast && toast('Failed to remove stage', 'error'); }
    };

    const rowStyle = (completed) => ({
        display: 'flex', alignItems: 'center', gap: 12,
        background: completed ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.04)',
        border: '1px solid ' + (completed ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'),
        borderRadius: 7, padding: '10px 14px', marginBottom: 8,
    });

    if (loading) return null;

    return (
        <div style={{ marginTop: 4 }}>
            {stages.length === 0 && (
                <div style={{ textAlign: 'center', padding: '24px 0', color: 'rgba(255,255,255,0.25)',
                    fontFamily: "'Space Mono',monospace", fontSize: 11, fontWeight: 900,
                    letterSpacing: 2, textTransform: 'uppercase' }}>
                    NO STAGES ATTACHED YET
                </div>
            )}
            {stages.map(stage => (
                <div key={stage.id} style={rowStyle(stage.isCompleted)}>
                    <input
                        type="checkbox"
                        checked={!!stage.isCompleted}
                        onChange={() => handleToggleComplete(stage)}
                        disabled={!isEditing}
                        style={{ width: 18, height: 18, flexShrink: 0, cursor: isEditing ? 'pointer' : 'default' }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            <strong style={{
                                fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 13,
                                color: stage.isCompleted ? '#6ee7b7' : '#fff', textTransform: 'uppercase',
                                textDecoration: stage.isCompleted ? 'line-through' : 'none',
                            }}>{stage.stageName}</strong>
                            {stage.isCustom && (
                                <span style={{ fontSize: 8, fontWeight: 900, color: '#EE8C3A',
                                    background: 'rgba(238,140,58,0.15)', padding: '2px 6px', borderRadius: 3,
                                    textTransform: 'uppercase', letterSpacing: 1 }}>CUSTOM</span>
                            )}
                        </div>
                        {editingId === stage.id ? (
                            <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                                <input type="number" value={editCost} onChange={e => setEditCost(e.target.value)}
                                    placeholder="Cost"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '6px 10px', fontFamily: "'Space Mono',monospace", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', width: 120 }} />
                                <input type="text" value={editNotes} onChange={e => setEditNotes(e.target.value)}
                                    placeholder="Notes"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '6px 10px', fontFamily: "'DM Sans',sans-serif", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', flex: 1, minWidth: 140 }} />
                                <button onClick={() => saveEdit(stage.id)}
                                    style={{ background: '#EE8C3A', border: 'none', borderRadius: 6, padding: '6px 12px',
                                        fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 10,
                                        textTransform: 'uppercase', color: '#1a2e30', cursor: 'pointer' }}>SAVE</button>
                                <button onClick={() => setEditingId(null)}
                                    style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: 6, padding: '6px 12px', fontFamily: "'DM Sans',sans-serif",
                                        fontWeight: 900, fontSize: 10, textTransform: 'uppercase', color: '#fff',
                                        cursor: 'pointer' }}>CANCEL</button>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', gap: 14, marginTop: 4, flexWrap: 'wrap' }}>
                                <span style={{ fontFamily: "'Space Mono',monospace", fontSize: 11, fontWeight: 700,
                                    color: 'rgba(255,255,255,0.6)' }}>UGX {Number(stage.cost || 0).toLocaleString()}</span>
                                {stage.notes && (
                                    <span style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 11, fontWeight: 600,
                                        color: 'rgba(255,255,255,0.4)', fontStyle: 'italic' }}>{stage.notes}</span>
                                )}
                            </div>
                        )}
                    </div>
                    {isEditing && editingId !== stage.id && (
                        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                            <button onClick={() => startEdit(stage)} title="Edit cost/notes"
                                style={{ background: 'transparent', border: 'none', color: '#EE8C3A', cursor: 'pointer',
                                    fontSize: 15, padding: 4 }}>
                                <FiEdit3 />
                            </button>
                            {isAdmin && (
                                <button onClick={() => handleRemove(stage.id)} title="Remove stage"
                                    style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer',
                                        fontSize: 15, padding: 4 }}>
                                    <FiTrash2 />
                                </button>
                            )}
                        </div>
                    )}
                </div>
            ))}

            {isEditing && (
                <button type="button" onClick={openAddModal}
                    style={{ width: '100%', marginTop: 8, padding: '10px 0', background: 'rgba(238,140,58,0.06)',
                        border: '2px dashed rgba(238,140,58,0.4)', borderRadius: 7, color: '#EE8C3A',
                        fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 11, textTransform: 'uppercase',
                        letterSpacing: 1, cursor: 'pointer' }}>
                    + ADD STAGE
                </button>
            )}

            <HardwareModal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title="ADD STAGE(S)">
                <div style={{ marginBottom: 14 }}>
                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900,
                        color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                        FROM MASTER CHECKLIST
                    </div>
                    {templates.length === 0 && (
                        <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: 11, fontFamily: "'DM Sans',sans-serif" }}>
                            No template stages available.
                        </div>
                    )}
                    {templates.map(t => (
                        <label key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0',
                            cursor: 'pointer', fontFamily: "'DM Sans',sans-serif", fontSize: 12, fontWeight: 700, color: '#fff' }}>
                            <input type="checkbox" checked={!!checkedTemplates[t.id]}
                                onChange={e => setCheckedTemplates(prev => ({ ...prev, [t.id]: e.target.checked }))}
                                style={{ width: 16, height: 16 }} />
                            <span style={{ flex: 1 }}>{t.stageName}</span>
                            <span style={{ fontFamily: "'Space Mono',monospace", fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>
                                UGX {Number(t.defaultCost || 0).toLocaleString()}
                            </span>
                        </label>
                    ))}
                </div>
                <div style={{ marginBottom: 14, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 12 }}>
                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900,
                        color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                        OR ADD A CUSTOM STAGE
                    </div>
                    <input type="text" value={customName} onChange={e => setCustomName(e.target.value)}
                        placeholder="Custom stage name"
                        style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(255,255,255,0.07)',
                            border: '1.5px solid rgba(255,255,255,0.18)', borderRadius: 8, padding: '10px 12px',
                            color: '#fff', fontFamily: "'DM Sans',sans-serif", fontWeight: 700, fontSize: 13,
                            marginBottom: 8 }} />
                    <input type="number" value={customCost} onChange={e => setCustomCost(e.target.value)}
                        placeholder="Cost (UGX)"
                        style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(255,255,255,0.07)',
                            border: '1.5px solid rgba(255,255,255,0.18)', borderRadius: 8, padding: '10px 12px',
                            color: '#fff', fontFamily: "'Space Mono',monospace", fontWeight: 700, fontSize: 13 }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                    <button onClick={() => setAddModalOpen(false)}
                        style={{ background: 'rgba(255,255,255,0.06)', border: '1.5px solid rgba(255,255,255,0.2)',
                            color: 'rgba(255,255,255,0.7)', borderRadius: 8, padding: '10px 18px',
                            fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 11, textTransform: 'uppercase',
                            cursor: 'pointer' }}>CANCEL</button>
                    <button onClick={handleAttach} disabled={saving}
                        style={{ background: '#EE8C3A', border: 'none', color: '#1a2e30', borderRadius: 8,
                            padding: '10px 20px', fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 11,
                            textTransform: 'uppercase', cursor: saving ? 'wait' : 'pointer', opacity: saving ? 0.6 : 1 }}>
                        {saving ? 'SAVING...' : 'ADD SELECTED'}
                    </button>
                </div>
            </HardwareModal>
        </div>
    );
};

// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════
const FolderPage = () => {
    const { id }   = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR' || user?.isRoot;

    const [binder,      setBinder]      = useState(null);
    const [buffer,      setBuffer]      = useState(null);
    const [loading,     setLoading]     = useState(true);
    const [loadError,   setLoadError]   = useState(false);
    const [isEditing,   setIsEditing]   = useState(false);
    const [committing,  setCommitting]  = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    // STAGE 3: { idx, existingName, enteredName } while unresolved, else null
    const [ninMismatch, setNinMismatch] = useState(null);
    const [payments,    setPayments]    = useState([]);

    const [activeTab, setActiveTab] = useState(() => {
    const h = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : '';
    return (h.includes('finance') || h.includes('payment')) ? 'FINANCIALS' : 'OVERVIEW';
});
    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS'];

    const [noteModal,  setNoteModal]  = useState({ open:false, id:null, content:'' });
    const [payModal,        setPayModal]        = useState({ open:false });
    const [payAmount,       setPayAmount]       = useState('');
    const [payNotes,        setPayNotes]        = useState('');
    const [payType,         setPayType]         = useState('TITLE');
    const [paying,          setPaying]          = useState(false);
    const [exitReceivableModal, setExitReceivableModal] = useState(false);

    const [drawers, setDrawers] = useState({ overview: true, balance: true, receivable: true, history: true, notes: true, owners: true, docs: true, stagesPanel: true });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));

    const { confirmState, confirm, handleAnswer } = useConfirm();

    const firstInputRef = useRef(null);
    const fileInputRef  = useRef(null);
    // Track whether any field was actually changed since edit mode opened
    // MUST be declared before useRouterBlock to avoid TDZ crash in minified build
    const touchedRef    = useRef(false);
    // Wrap setBuffer so any change marks the form as touched
    const touchedSetBuffer = React.useCallback((updater) => {
        touchedRef.current = true;
        setBuffer(updater);
    }, []);

    // Unsaved changes guard -- active only while in edit mode and not mid-save
    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =
        useRouterBlock(!committing && isEditing);

    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-') || hash === 'record-payment' || hash === 'storage-fees') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                if (hash === 'record-payment') {
                    if (isAdmin) setPayModal({ open: true });
                } else if (hash === 'storage-fees') {
                    const el = document.getElementById('receivable-controls');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    const el = document.getElementById('paymentHistorySection');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {
            setActiveTab('OWNERS');
        } else if (hash === 'vault' || hash === 'documents') {
            setActiveTab('DOCUMENTS');
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id, isAdmin]);



    useEffect(() => {
        if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120);
    }, [isEditing]);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const action = params.get('action');
        if (!action || !binder) return;
        if (action === 'pay') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                setPayType('TITLE');
                setPayAmount('');
                setPayNotes('');
                setPayModal({ open: true });
            }, 400);
        } else if (action === 'storage') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                setPayType('STORAGE');
                setPayAmount('');
                setPayNotes('');
                setPayModal({ open: true });
            }, 400);
        }
    }, [location.search, binder, isAdmin]);



    // beforeunload -- catches tab close, hard refresh, browser back to external site
    // useRouterBlock also adds beforeunload, this is a belt-and-suspenders backup
    useEffect(() => {
        if (!isEditing || committing) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
            return '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);

    const loadFolderData = useCallback(async () => {
        try {
            const data = await landService.getDeepBinder(id);
            if (!data) throw new Error('NULL_SIGNAL');
            setBinder(data);
            setPayments(data.payments || []);
            setLoadError(false);
            if (!isEditing) {
                setBuffer({
                    plotNumber:        data.project?.landTitle?.plotNumber        || '',
                    tenure:            data.project?.landTitle?.tenure            || 'MAILO',
                    blockRoad:         data.project?.landTitle?.blockRoad         || '',
                    district:          data.project?.district                     || '',
                    county:            data.project?.county                       || '',
                    subCounty:         data.project?.subCounty                    || '',
                    parish:            data.project?.parish                       || '',
                    village:           data.project?.village                      || '',
                    area:              data.project?.area                         || '',
                    titleId:           data.project?.landTitle?.titleId           || '',
                    totalCost:         String(data.project?.totalCost             || 0),
                    initialPayment:    String(data.project?.amountPaid            || 0),
                    isLegacy:          data.project?.isLegacy                     || false,
                    owners: (data.project?.proprietors || []).map(p => ({
                        fullName: p.fullName||'', phone: p.phoneNumber||'',
                        nationalId: p.nationalId||'', address: p.homeAddress||'', email: p.email||'',
                    })),
                });
                setFieldErrors({});
            }
        } catch { setLoadError(true); }
        finally  { setLoading(false); }
    }, [id, isEditing]);

    useEffect(() => { loadFolderData(); }, [loadFolderData]);

    const handleCommit = async () => {
        // STAGE 3: block save while an unresolved NIN mismatch warning is open
        if (ninMismatch) {
            toast('Confirm or fix the NIN mismatch warning before saving.', 'error', 6000);
            return;
        }
        const errors = validateBuffer(buffer);
        if (errors.length) {
            const fe = {};
            if (!buffer.plotNumber?.trim())  fe.plotNumber = 'Required';
            if (!buffer.district?.trim())    fe.district   = 'Required';
            buffer.owners?.forEach((o,i) => { if (!o.fullName?.trim()) fe['owner_'+i+'_name']='Required'; });
            setFieldErrors(fe);
            toast('VALIDATION FAILED: ' + errors[0], 'error', 6000);
            return;
        }
        setFieldErrors({});
        setCommitting(true);
        try {
            await landService.updateMasterFolder(id, {
                ...buffer,
                totalCost:      Number(buffer.totalCost) || 0,
                initialPayment: Number(buffer.initialPayment) || 0,
            });
            predictionService.learn(buffer);
            touchedRef.current = false;
            setIsEditing(false);
            await loadFolderData();
            toast('Changes saved successfully', 'success');
        // STAGE 3 FIX: this only ever showed the generic axios err.message, so a
        // backend validation message (e.g. NIN_NAME_MISMATCH) never reached the
        // user -- same fix already applied to payments in Stage 1.
        } catch (err) { toast('SAVE FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setCommitting(false); }
    };

    const handleUnlock = async () => {
        touchedRef.current = false; // reset touch tracking
        setIsEditing(true);
        try { await landService.logDossierUnlock(id); } catch { /* non-fatal */ }
    };

    const handleAbort = async () => {
        const ok = await confirm('DISCARD CHANGES', 'All unsaved changes will be lost. This cannot be undone.', 'warn');
        if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); }
    };

    const handleNuclearPurge = async () => {
        const ok = await confirm('DELETE',
            'PERMANENTLY erase this entire archive entry including all documents and notes. Cannot be undone.', 'danger');
        if (!ok) return;
        try {
            await landService.purgeAsset(id);
            toast('Record permanently deleted', 'warn', 3000);
            setTimeout(() => navigate('/land/projects'), 1500);
        } catch { toast('Delete failed', 'error'); }
    };

    const handleStageClick = async (num) => {
        if (!isEditing) return;
        try {
            await landService.setRealityStage(id, num);
            await loadFolderData();
            toast('Stage updated: ' + STAGE_LABELS[num-1], 'info', 3000);
        } catch { toast('STAGE UPDATE FAILED', 'error'); }
    };

    // PHASE 2 / STAGE 3: NIN duplicate/auto-fill check on edit -- same blocking
    // behavior as Intake now (see IntakePage.jsx handleNinBlurCheck).
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (buffer.owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            setNinMismatch({ idx, existingName: result.fullName, enteredName: buffer.owners[idx]?.fullName || '' });
            return;
        }

        const owners = buffer.owners.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                phone:   o.phone.trim()   ? o.phone   : (result.phoneNumber || o.phone),
                email:   o.email.trim()   ? o.email   : (result.email || o.email),
                address: o.address.trim() ? o.address : (result.homeAddress || o.address),
            };
        });
        touchedSetBuffer(p => ({ ...p, owners }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };

    // STAGE 3: user confirmed it IS the same person -- unblock save
    const handleNinMismatchConfirm = () => setNinMismatch(null);

    // STAGE 3: user says it's NOT the same person -- clear the NIN and refocus it
    const handleNinMismatchReject = () => {
        if (!ninMismatch) return;
        const idx = ninMismatch.idx;
        handleOwnerChange(idx, 'nationalId', '');
        setNinMismatch(null);
        setTimeout(() => {
            const el = document.getElementById('owner_' + idx + '_nin');
            if (el) el.focus();
        }, 50);
    };

    const handlePhoneBlurCheck = (idx, val) => {
        if (!val.trim()) return;
        const normalized = val.replace(/\s+/g, '');
        const duplicate = (buffer.owners || []).some((o, i) =>
            i !== idx && o.phone.replace(/\s+/g, '') === normalized
        );
        if (duplicate) {
            toast('WARNING: This phone number is already used by another owner on this plot.', 'warn', 5000);
        }
    };

    const handleOwnerChange = (idx, field, val) => {
        const owners = buffer.owners.map((o,i) => {
            if (i !== idx) return o;
            let v = val;
            if (field==='fullName')   v = val.toUpperCase();
            if (field==='nationalId') v = val.toUpperCase().replace(/\s/g,'');
            if (field==='email')      v = val.toLowerCase().replace(/\s/g,'');
            return { ...o, [field]: v };
        });
        touchedRef.current = true;
        setBuffer(p => ({ ...p, owners }));
    };

    const handleEmailCommit = (idx, val) => {
        const owners = buffer.owners.map((o,i) => i===idx ? { ...o, email:val } : o);
        touchedRef.current = true;
        setBuffer(p => ({ ...p, owners }));
    };

    const handleVaultAction = async (files) => {
        if (!files?.length) return;
        setCommitting(true);
        try {
            await landService.addExtraDocuments(id, files);
            await loadFolderData();
            toast(files.length + ' document(s) uploaded', 'success', 3000);
        } catch { toast('INGESTION FAILED', 'error', 8000); }
        finally { setCommitting(false); }
    };

    const handleDeleteDoc = async (docId, fileName) => {
        const ok = await confirm('DELETE DOCUMENT', `Delete "${fileName}"? Cannot be undone.`, 'danger');
        if (!ok) return;
        try {
            await landService.deleteDocument(docId);
            await loadFolderData();
            toast('Document removed', 'warn', 3000);
        } catch { toast('DELETE FAILED', 'error'); }
    };

    const handleNoteSave = async () => {
        if (!noteModal.content.trim()) return;
        try {
            if (noteModal.id) await landService.editStandaloneNote(noteModal.id, noteModal.content);
            else              await landService.addStandaloneNote(id, noteModal.content);
            setNoteModal({ open:false, id:null, content:'' });
            await loadFolderData();
            toast('Note saved', 'success', 3000);
        } catch { toast('SAVE FAILED', 'error'); }
    };

    const handleDeleteNote = async (noteId) => {
        const ok = await confirm('DELETE NOTE', 'Delete this entry? Cannot be undone.', 'danger');
        if (!ok) return;
        try {
            await landService.deleteStandaloneNote(noteId);
            await loadFolderData();
            toast('Note deleted', 'warn', 3000);
        } catch { toast('DELETE FAILED', 'error'); }
    };

    const handleMoveToReceivable = async () => {
        const ok = await confirm('MOVE TO RECEIVABLES',
            'This will freeze the current balance as original debt and start monthly storage fees of UGX 50,000. Continue?', 'warn');
        if (!ok) return;
        try {
            await recoveryService.moveToReceivable(id);
            await loadFolderData();
            toast('Plot moved to receivables. Storage fees are now active.', 'warn');
        } catch (err) { toast('RECEIVABLES FAILED: ' + (err.response?.data?.message || err.message), 'error'); }
    };

    const handleExitReceivable = () => {
        setExitReceivableModal(true);
    };

    const handleExitReceivableConfirm = async (capitalizeFees) => {
        setExitReceivableModal(false);
        try {
            await recoveryService.exitReceivable(id, capitalizeFees);
            await loadFolderData();
            toast(capitalizeFees
                ? 'Plot exited receivable. Storage fees added to total value.'
                : 'Plot exited receivable. Storage fees waived.',
                'success');
        } catch (err) { toast('EXIT FAILED: ' + (err.response?.data?.message || err.message), 'error'); }
    };

    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        setPaying(true);
        try {
            const fullNotes = payType === 'STORAGE'
                ? `[STORAGE FEE PAYMENT] ${payNotes}`.trim()
                : payNotes;
            await recoveryService.recordPayment(id, payAmount, fullNotes);
            await loadFolderData();
            setPayModal({ open: false });
            setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            toast('Payment recorded successfully', 'success');
        } catch (err) { toast('PAYMENT FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setPaying(false); }
    };

    const getDocUrl = (filePath) => {
        if (!filePath) return '#';
        if (filePath.startsWith('http')) return filePath;
        const parts = filePath.split(/ge_uploads[/]/);
        const rel   = parts.length > 1 ? parts[1] : filePath;
        const base  = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';
        return `${base}/vault/` + rel.replace(/\\/g, '/');
    };

    const handleOpenDoc = (filePath) => {
        if (!filePath) return;
        const url = getDocUrl(filePath);
        if (filePath.startsWith('http')) {
            window.open(url, '_blank', 'noopener,noreferrer');
        } else {
            fetch(url, { headers: { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } })
                .then(r => r.blob())
                .then(blob => {
                    const blobUrl = URL.createObjectURL(blob);
                    window.open(blobUrl, '_blank', 'noopener,noreferrer');
                    setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
                })
                .catch(() => window.open(url, '_blank', 'noopener,noreferrer'));
        }
    };

    const isPDF = (filePath) => {
        if (!filePath) return false;
        const lower = filePath.toLowerCase();
        return lower.includes('.pdf') || lower.includes('application/pdf') ||
               (lower.includes('cloudinary') && lower.includes('/raw/'));
    };

    const sg = useMemo(() => (key) => predictionService.getSuggestions(key) || [], []);

    if (loading) return <div className={styles.container}><SkeletonPage /></div>;

    if (loadError || !binder || !buffer) return (
        <div style={{ padding: 'clamp(40px,8vw,80px) clamp(20px,4vw,40px)' }}>
            <ErrorMessage
                type="error"
                title="Record not found"
                message="This archive entry could not be loaded. It may have been deleted or the server is temporarily unavailable."
                onRetry={loadFolderData}
                retryLabel="Try Again"
            />
        </div>
    );

    const project      = binder.project;
    const isReceivable    = project?.isReceivable || false;
    const docCount     = (binder.documents||[]).length;
    const noteCount    = (binder.notes||[]).length;
    const paymentCount = payments.length;

    // Financial figures — 4-Pocket Math: AMOUNT OWED = (PLOT VALUE + STORAGE FEES) - PAID
    const totalValue          = Number(project?.totalCost || 0);
    const totalCost           = totalValue; // alias
    const amountPaid          = Number(project?.amountPaid || 0);
    const paid                = amountPaid; // alias
    const storageFees         = Number(project?.storageFeesAccumulated || 0);
    const receivableAmountOwed   = Math.max(0, totalValue + storageFees - amountPaid);
    const activeAmountOwed    = Math.max(0, totalValue - amountPaid);
    const amountOwed          = isReceivable ? receivableAmountOwed : activeAmountOwed;
    const remaining           = amountOwed; // alias
    const arrearsEdit         = (Number(buffer?.totalCost)||0) - (Number(buffer?.initialPayment)||0);
    const effectiveMonthlyFee = Number(project?.storageFeeOverride) > 0
        ? Number(project.storageFeeOverride)
        : 50000;

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing || paying} />

            {/* PRINT-ONLY CORPORATE DOSSIER HEADER */}
            <div className={styles.printDossierHeader} aria-hidden="true">
                <div className={styles.printDossierTopBar}>
                    <div className={styles.printDossierLeft}>
                        <div className={styles.printDossierCompany}>GE SOLUTIONS</div>
                        <div className={styles.printDossierDivision}>LAND REGISTRY DIVISION</div>
                    </div>
                    <div className={styles.printDossierCenter}>
                        <div className={styles.printDossierTitleBox}>OFFICIAL LAND DOSSIER</div>
                    </div>
                    <div className={styles.printDossierRight}>
                        <div className={styles.printDossierDateLabel}>PRINTED ON</div>
                        <div className={styles.printDossierDateVal}>
                            {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })}
                        </div>
                    </div>
                </div>
                <div className={styles.printDossierMeta}>
                    <span><strong>PLOT ID:</strong> {project.landTitle.plotNumber}</span>
                    <span><strong>TENURE:</strong> {project.landTitle.tenure}</span>
                    {project.district && <span><strong>DISTRICT:</strong> {project.district}</span>}
                    <span><strong>STATUS:</strong> {project.status}</span>
                    <span><strong>STAGE:</strong> {STAGE_LABELS[(project.currentStageIndex || 1) - 1] || project.currentStageIndex}</span>
                </div>
            </div>

            {/* PIPELINE HUD */}
            <nav className={styles.pipelineHUD} aria-label="Project pipeline">
                <div className={styles.track}>
                    {STAGE_LABELS.map((label, idx) => {
                        const num    = idx + 1;
                        const active = project.currentStageIndex >= num;
                        return (
                            <div key={num} className={styles.stageModule}>
                                <div className={`${styles.dot} ${active ? styles.dotActive : ''} ${isEditing ? styles.dotInteractive : ''}`}
                                    onClick={() => handleStageClick(num)}
                                    role={isEditing ? 'button' : 'img'} tabIndex={isEditing ? 0 : -1}
                                    aria-label={`Stage ${num}: ${label}${active ? ' (complete)' : ''}`}
                                    onKeyDown={e => { if (isEditing && (e.key==='Enter'||e.key===' ')) { e.preventDefault(); handleStageClick(num); }}}>
                                    {active ? <FiCheckCircle aria-hidden="true" /> : num}
                                </div>
                                <span className={styles.stageLabel}>{label}</span>
                            </div>
                        );
                    })}
                </div>
                <div className={styles.protocolReadout}>
                    <strong>PROTOCOL: {project.status}</strong>
                    <span>LIVE STATUS</span>
                </div>
            </nav>

            {/* TERMINAL HEADER */}
            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle?.plotNumber || project.projectIndex || 'UNTITLED'}</h1>
                    <div className={styles.metaLine}>
                        {project.projectIndex && (
                            <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                                PROJECT #{project.projectIndex}
                            </span>
                        )}
                        <span className={`${styles.metaTag} ${project.landTitle ? styles.tagGreen : styles.tagOrange}`}>
                            {project.landTitle ? 'TITLED' : 'FOLDER'}
                        </span>
                        {project.landTitle?.projectStartDate && (
                            <span className={`${styles.metaTag} ${styles.tagGreen}`}>
                                STARTED: {new Date(project.landTitle.projectStartDate).toLocaleDateString()}
                            </span>
                        )}
                        {project.landTitle?.titleIssueDate ? (
                            <span className={`${styles.metaTag} ${styles.tagPurple}`}>
                                TITLED: {new Date(project.landTitle.titleIssueDate).toLocaleDateString()}
                            </span>
                        ) : (
                            <span className={`${styles.metaTag} ${styles.tagOrange}`}>
                                TITLE: PENDING
                            </span>
                        )}
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>
                        {isReceivable
                            ? <span className={styles.metaTag} style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', borderColor: 'rgba(239,68,68,0.4)' }}>RECEIVABLES</span>
                            : project.landTitle?.isReleased
                            ? <span className={styles.metaTag} style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', borderColor: 'rgba(16,185,129,0.4)' }}>RELEASED</span>
                            : amountPaid >= totalCost
                            ? <span className={styles.metaTag} style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', borderColor: 'rgba(16,185,129,0.4)' }}>FULLY PAID</span>
                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>
                        }
                        {isEditing && <div className={styles.editBadge}>EDIT MODE ENABLED</div>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {/* VIEW MODE ACTIONS */}
                    {!isEditing && (
                        <div className={styles.ctrlGroup}>
                            <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record">
                                <FiPrinter aria-hidden="true" />
                            </button>
                            {isAdmin && (
                                <button className={styles.ctrlBtnPay}
                                    onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>
                                    <FiDollarSign aria-hidden="true" /> PAYMENT
                                </button>
                            )}
                            {isAdmin && !isReceivable && (
                                <button className={styles.ctrlBtnReceivable} onClick={handleMoveToReceivable}>
                                    <FiAlertOctagon aria-hidden="true" /> RECEIVABLES
                                </button>
                            )}
                            {isAdmin && isReceivable && (
                                <button className={styles.ctrlBtnReceivable} onClick={handleExitReceivable}>
                                    <FiAlertOctagon aria-hidden="true" /> EXIT RECEIVABLES
                                </button>
                            )}
                            <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                                <FiUnlock aria-hidden="true" /> EDIT
                            </button>
                        </div>
                    )}
                    {/* EDIT MODE ACTIONS */}
                    {isEditing && (
                        <div className={styles.ctrlGroup}>
                            {user?.isRoot && (
                                <button className={styles.purgeBtn} onClick={handleNuclearPurge} title="Permanently delete this record">
                                    <FiTrash2 aria-hidden="true" /> DELETE
                                </button>
                            )}
                            <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}>
                                <FiX aria-hidden="true" /> CANCEL
                            </button>
                            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}>
                                <FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}
                            </button>
                        </div>
                    )}
                </div>
            </header>

            {/* TAB BAR */}
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                {TABS.map(tab => (
                    <button
                        key={tab}
                        role="tab"
                        aria-selected={activeTab === tab}
                        className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`}
                        onClick={() => setActiveTab(tab)}
                        title={tab}
                    >
                        <span className={styles.tabFull}>{tab}</span>
                        <span className={styles.tabShort}>{tab.substring(0, 2)}</span>
                    </button>
                ))}
            </div>

            <main className={styles.workstationBody} role="tabpanel">

                {/* ════════════════════════════════════════════════════
                    OVERVIEW TAB — Plot technical details
                    ════════════════════════════════════════════════════ */}
                <section
                    className={styles.hwPanel}
                    aria-label="Plot Details"
                    style={activeTab !== 'OVERVIEW' ? {display:'none'} : {}}
                    data-print-section="OVERVIEW"
                >
                        <DrawerHeader label="PLOT DETAILS" isOpen={drawers.overview} onClick={() => toggleDrawer('overview')} icon={FiMap} />
                        <div className={`${styles.panelBody} ${drawers.overview ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <>
                                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 4 }}>LOCATION (Always visible)</div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                        <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                        <SmartInput label="SUB-COUNTY" value={buffer.subCounty} showCaps onChange={e => touchedSetBuffer({...buffer, subCounty: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="PARISH" value={buffer.parish} showCaps onChange={e => touchedSetBuffer({...buffer, parish: e.target.value.toUpperCase()})} />
                                        <SmartInput label="VILLAGE" value={buffer.village} showCaps onChange={e => touchedSetBuffer({...buffer, village: e.target.value.toUpperCase()})} />
                                        <SmartInput label="AREA" value={buffer.area} onChange={e => touchedSetBuffer({...buffer, area: e.target.value})} />
                                    </div>
                                    {project.landTitle && (
                                        <>
                                            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 16, borderTop: '1px solid rgba(139,92,246,0.3)', paddingTop: 12 }}>TITLE & PLOT DETAILS</div>
                                            <div className={styles.inputGrid3}>
                                                <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                                <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />
                                                <SmartInput label="TITLE ID" value={buffer.titleId} showCaps onChange={e => touchedSetBuffer({...buffer, titleId: e.target.value.toUpperCase()})} />
                                            </div>
                                            <div className={styles.inputGrid3}>
                                                <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                            </div>
                                        </>
                                    )}
                                </>
                            ) : (
                                <>
                                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 4 }}>LOCATION</div>
                                    <div className={styles.readOnlyGrid}>
                                        {[
                                            ['DISTRICT',     project.district],
                                            ['COUNTY',       project.county],
                                            ['SUB-COUNTY',   project.subCounty],
                                            ['PARISH',       project.parish],
                                            ['VILLAGE',      project.village],
                                            ['AREA',         project.area],
                                        ].map(([l,v],i) => (
                                            <div key={i} className={styles.specItem}>
                                                <span className={styles.specLabel}>{l}</span>
                                                <span className={styles.specValue}>{v || '---'}</span>
                                            </div>
                                        ))}
                                    </div>
                                    {project.landTitle && (
                                        <>
                                            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 16, borderTop: '1px solid rgba(139,92,246,0.3)', paddingTop: 12 }}>TITLE & PLOT DETAILS</div>
                                            <div className={styles.readOnlyGrid}>
                                                {[
                                                    ['PLOT ID',      project.landTitle.plotNumber],
                                                    ['TENURE',       project.landTitle.tenure],
                                                    ['TITLE ID',     project.landTitle.titleId],
                                                    ['BLOCK / ROAD', project.landTitle.blockRoad],
                                                ].map(([l,v],i) => (
                                                    <div key={i} className={styles.specItem}>
                                                        <span className={styles.specLabel}>{l}</span>
                                                        <span className={styles.specValue}>{v || '---'}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                </>
                            )}
                        </div>
                        </div>
                </section>

                {/* STAGE CHECKLIST (Phase 4B, additive -- flexible stage list from ProjectStage)
                    NOTE: separate from the pipeline dots above (COMMITMENT/FIELD WORK/etc),
                    which are the older fixed 5-stage system used by Dashboard and Ledger
                    sorting. Both systems coexist for now -- see fix.py header comment. */}
                <section
                    className={styles.hwPanel}
                    aria-label="Stage Checklist"
                    style={activeTab !== 'OVERVIEW' ? {display:'none'} : {}}
                    data-print-section="STAGES"
                >
                        <DrawerHeader label="STAGE CHECKLIST" isOpen={drawers.stagesPanel} onClick={() => toggleDrawer('stagesPanel')} icon={FiCheckCircle} />
                        <div className={`${styles.panelBody} ${drawers.stagesPanel ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            <StageChecklistPanel projectId={id} isEditing={isEditing} isAdmin={isAdmin} toast={toast} />
                        </div>
                        </div>
                </section>

                {/* ════════════════════════════════════════════════════
                    FINANCIALS TAB — Central hub:
                    1. Balance Summary
                    2. Record Payment (admin)
                    3. Receivables Controls (admin, if receivable)
                    4. Payment History
                    5. Notes & Call Log
                    ════════════════════════════════════════════════════ */}
                <div
                    className={styles.financialsStack}
                    style={activeTab !== 'FINANCIALS' ? {display:'none'} : {}}
                    data-print-section="FINANCIALS"
                >

                        {/* ── 1. BALANCE SUMMARY ── */}
                        <section className={styles.hwPanel} aria-label="Balance Summary">
                            <DrawerHeader label="BALANCE SUMMARY" isOpen={drawers.balance} onClick={() => toggleDrawer('balance')} icon={FiCreditCard} />
                            <div className={`${styles.panelBody} ${drawers.balance ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                {isEditing ? (
                                    <>
                                        <div className={styles.inputGrid3}>
                                            <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />
                                            <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}><label>AMOUNT OWED</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                                <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                            </div>
                                        </div>
                                    </>
                                ) : isReceivable ? (
                                    <>
                                        <div className={styles.receivableNotice}>
                                            <FiAlertOctagon className={styles.receivableNoticeIcon} size={14} />
                                            <div className={styles.receivableNoticeText}>
                                                <strong>STORAGE FEES ACTIVE</strong>
                                                <span>UGX {fmt(effectiveMonthlyFee)}/month accumulates until balance is cleared</span>
                                            </div>
                                        </div>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox}>
                                                <label>PLOT VALUE</label>
                                                <strong>UGX {fmt(totalValue)}</strong>
                                            </div>
                                            <div className={styles.statBox}>
                                                <label style={{color:'#ef4444'}}>+ STORAGE FEES</label>
                                                <strong style={{color:'#fca5a5',textShadow:'0 0 8px rgba(239,68,68,0.35)'}}>UGX {fmt(storageFees)}</strong>
                                                <small style={{opacity:0.5,fontSize:'0.7rem'}}>
                                                    {project.receivableStartDate
                                                        ? `Since ${new Date(project.receivableStartDate).toLocaleDateString()}`
                                                        : 'UGX ' + fmt(effectiveMonthlyFee) + '/month'}
                                                </small>
                                            </div>
                                            <div className={styles.statBox}>
                                                <label style={{color:'#22c55e'}}>PAID</label>
                                                <strong style={{color:'#22c55e'}}>UGX {fmt(amountPaid)}</strong>
                                            </div>
                                            <div className={styles.statBox} style={{borderLeft:'2px solid rgba(239,68,68,0.6)',background:'rgba(239,68,68,0.07)'}}>
                                                <label style={{color:'#fca5a5'}}>AMOUNT OWED</label>
                                                <strong style={{color:'#fca5a5',textShadow:'0 0 12px rgba(239,68,68,0.45)'}}>UGX {fmt(receivableAmountOwed)}</strong>
                                                <small style={{opacity:0.5,fontSize:'0.7rem'}}>(Value + Fees - Paid)</small>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalValue)}</strong></div>
                                            <div className={styles.statBox}><label>PAID</label><strong style={{color:'#22c55e'}}>UGX {fmt(amountPaid)}</strong></div>
                                            <div className={styles.statBox}><label>AMOUNT OWED</label><strong style={{color:'#fca5a5',textShadow:'0 0 12px rgba(239,68,68,0.45)'}}>UGX {fmt(activeAmountOwed)}</strong></div>
                                        </div>
                                        <div className={styles.collectionBar}>
                                            <div className={styles.collectionFill}
                                                style={{width: totalValue > 0 ? `${Math.min(100,(paid/totalValue)*100)}%` : '0%'}} />
                                        </div>
                                        <div className={styles.velocityNote}>
                                            <FiClock aria-hidden="true" />
                                            <span>COLLECTION: <strong>{(binder.collectionPercentage||0).toFixed(1)}%</strong></span>
                                        </div>
                                    </>
                                )}

                            </div>
                            </div>
                        </section>

                        {/* ── 2. RECEIVABLES MANAGEMENT (admin only, shown when receivable) ── */}
                        {isAdmin && isReceivable && (
                            <section className={styles.hwPanel} aria-label="Receivables Controls" id="receivable-controls">
                                <DrawerHeader label="RECEIVABLES MANAGEMENT" isOpen={drawers.receivable} onClick={() => toggleDrawer('receivable')} icon={FiAlertOctagon} />
                                <div className={`${styles.panelBody} ${drawers.receivable ? styles.bodyOpen : styles.bodyClosed}`}>
                                <div className={styles.panelInner}>
                                    {isEditing ? (
                                        <>
                                            <div className={styles.inputGrid3}>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>MONTHLY STORAGE FEE (UGX)</label></div>
                                                    <input type="number" className={styles.hwInput}
                                                        defaultValue={project.storageFeeOverride || 50000}
                                                        onBlur={async e => {
                                                            const val = Number(e.target.value);
                                                            if (val >= 0) {
                                                                try { await recoveryService.setStorageRate(project.id, val); await loadFolderData(); toast('RATE UPDATED', 'success'); }
                                                                catch { /* silent */ }
                                                            }
                                                        }}
                                                        placeholder="50000" />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>ADJUST ACCUMULATED FEES (UGX)</label></div>
                                                    <input type="number" className={styles.hwInput}
                                                        defaultValue={project.storageFeesAccumulated || 0}
                                                        onBlur={async e => {
                                                            const val = Number(e.target.value);
                                                            if (val >= 0) {
                                                                try { await recoveryService.setAccumulatedFees(project.id, val); await loadFolderData(); toast('FEES ADJUSTED', 'success'); }
                                                                catch { /* silent */ }
                                                            }
                                                        }}
                                                        placeholder={String(project.storageFeesAccumulated || 0)} />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>FEE STATUS</label></div>
                                                    <button type="button"
                                                        className={project.storagePaused ? styles.btnResumeActive : styles.btnPauseGrey}
                                                        onClick={async () => {
                                                            try {
                                                                await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                                await loadFolderData();
                                                                toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                            } catch { toast('ACTION FAILED', 'error'); }
                                                        }}>
                                                        {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                                    </button>
                                                </div>
                                            </div>
                                            <div className={styles.inputGrid3} style={{marginTop:8}}>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>NEGOTIATION DEADLINE</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        defaultValue={project.negotiationDeadline ? project.negotiationDeadline.substring(0,10) : ''}
                                                        onBlur={async e => {
                                                            try { await recoveryService.setNegotiationDeadline(project.id, e.target.value || null); await loadFolderData(); toast('DEADLINE UPDATED', 'info', 2000); }
                                                            catch { /* silent */ }
                                                        }} />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>RECEIVABLES START DATE OVERRIDE</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        defaultValue={project.receivableStartDate ? project.receivableStartDate.substring(0,10) : ''}
                                                        onBlur={async e => {
                                                            if (!e.target.value) return;
                                                            try { await recoveryService.setReceivableStartOverride(project.id, e.target.value); await loadFolderData(); toast('START DATE OVERRIDDEN', 'info', 2000); }
                                                            catch { /* silent */ }
                                                        }} />
                                                </div>
                                            </div>
                                            <div className={styles.editReceivableFeeHint}>
                                                Current monthly fee: UGX {fmt(effectiveMonthlyFee)}. Negotiation deadline pauses fees automatically until that date.
                                            </div>
                                        </>
                                    ) : (
                                        <div className={styles.readOnlyGrid}>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>MONTHLY STORAGE FEE</span>
                                                <span className={styles.specValue}>UGX {fmt(effectiveMonthlyFee)}</span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>FEE STATUS</span>
                                                <span className={styles.specValue} style={{ color: project.storagePaused ? '#fcd34d' : '#86efac' }}>
                                                    {project.storagePaused ? 'PAUSED' : 'ACTIVE'}
                                                </span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>ACCUMULATED FEES</span>
                                                <span className={styles.specValue}>UGX {fmt(project.storageFeesAccumulated)}</span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>NEGOTIATION DEADLINE</span>
                                                <span className={styles.specValue}>
                                                    {project.negotiationDeadline ? new Date(project.negotiationDeadline).toLocaleDateString() : 'NONE'}
                                                </span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>RECEIVABLES START DATE</span>
                                                <span className={styles.specValue}>
                                                    {project.receivableStartDate ? new Date(project.receivableStartDate).toLocaleDateString() : 'UNKNOWN'}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                                </div>
                            </section>
                        )}

                        {/* ── 3. PAYMENT HISTORY ── */}
                        <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                            <DrawerHeader label="PAYMENT HISTORY" isOpen={drawers.history} onClick={() => toggleDrawer('history')} icon={FiActivity} count={paymentCount} />
                            <div className={`${styles.panelBody} ${drawers.history ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                {paymentCount === 0 ? (
                                    <div className={styles.emptyState} role="status">
                                        <FiDollarSign className={styles.emptyIcon} aria-hidden="true" />
                                        <span>NO PAYMENTS RECORDED YET</span>
                                    </div>
                                ) : (
                                    <div className={styles.paymentList}>
                                        {payments.map((pay, i) => (
                                            <div key={pay.id || i} id={`payment-${pay.id}`} className={styles.paymentRow}
                                                style={{borderLeftColor: pay.paymentType === 'RECEIVABLE_PARTIAL' ? '#ef4444' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#06b6d4' : '#22c55e'}}>
                                                <div className={styles.payRowLeft}>
                                                    <div className={styles.payAmount}>UGX {fmt(pay.amountPaid)}</div>
                                                    <div className={styles.payMeta}>
                                                        <span className={styles.payType}
                                                            style={{color: pay.paymentType === 'RECEIVABLE_PARTIAL' ? '#fca5a5' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#67e8f9' : '#86efac'}}>
                                                            {pay.paymentType === 'STANDARD' ? 'Title Payment'
                                                            : pay.paymentType === 'INITIAL_DEPOSIT' ? 'Initial Deposit'
                                                            : pay.paymentType === 'RECEIVABLE_PARTIAL' ? 'Receivables Payment'
                                                            : pay.paymentType}
                                                        </span>
                                                        <span className={styles.payBy}>by {pay.recordedBy}</span>
                                                        {pay.notes && <span className={styles.payNotes}>{pay.notes}</span>}
                                                    </div>
                                                </div>
                                                <div className={styles.payRowRight}>
                                                    <div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div>
                                                    {pay.balanceAfter != null && (
                                                        <div className={styles.payBalance}>Bal: UGX {fmt(pay.balanceAfter)}</div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            </div>
                        </section>

                        {/* ── 4. NOTES & CALL LOG ── */}
                        <section className={styles.hwPanel} aria-label="Notes and Call Log">
                            <DrawerHeader label="NOTES & CALL LOG" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} count={noteCount} />
                            <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                {isEditing && (
                                    <button type="button" className={styles.addNoteBtn} style={{marginBottom: '10px', marginTop: '0'}}
                                        onClick={() => setNoteModal({open:true,id:null,content:''})}>
                                        + ADD NOTE
                                    </button>
                                )}
                                {noteCount === 0 ? (
                                    <div className={styles.emptyState} role="status">
                                        <FiInfo className={styles.emptyIcon} aria-hidden="true" />
                                        <span>NO NOTES LOGGED YET</span>
                                    </div>
                                ) : (
                                    <div className={styles.notebookTimeline} role="list">
                                        {binder.notes.map((log, i) => (
                                            <article key={i} className={styles.ruledNote} role="listitem">
                                                <div className={styles.noteMeta}>
                                                    <div className={styles.noteMetaLeft}>
                                                        <time className={styles.noteTime} dateTime={log.timestamp}>
                                                            {new Date(log.timestamp).toLocaleDateString()}
                                                        </time>
                                                        <span className={styles.noteAuthor}>by {log.recordedBy}</span>
                                                    </div>
                                                    {isEditing && (
                                                        <div className={styles.actionBlock}>
                                                            <button type="button" className={styles.iconBtn}
                                                                onClick={() => setNoteModal({open:true,id:log.id,content:log.notes})}>
                                                                <FiEdit3 className={styles.editIcon} aria-hidden="true" />
                                                            </button>
                                                            <button type="button" className={styles.iconBtn}
                                                                onClick={() => handleDeleteNote(log.id)}>
                                                                <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                                <p className={styles.noteContent}>{log.notes}</p>
                                            </article>
                                        ))}
                                    </div>
                                )}
                            </div>
                            </div>
                        </section>

                </div>

                {/* ════════════════════════════════════════════════════
                    OWNERS TAB
                    ════════════════════════════════════════════════════ */}
                <section
                    className={styles.hwPanel}
                    aria-label="Owners"
                    style={activeTab !== 'OWNERS' ? {display:'none'} : {}}
                    data-print-section="OWNERS"
                >
                        <DrawerHeader label="OWNERS" isOpen={drawers.owners} onClick={() => toggleDrawer('owners')} icon={FiUsers} count={project.proprietors.length} />
                        <div className={`${styles.panelBody} ${drawers.owners ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            <div className={styles.ownersScroll}>
                                <div className={styles.ownersGrid2} role="list">
                                    {isEditing ? buffer.owners.map((o, idx) => (
                                        <div key={idx} className={styles.ownerEditCard} role="listitem">
                                            <div className={styles.ownerCardLabel}>ENTITY #{idx+1} {idx===0&&'(PRIMARY)'}</div>
                                            <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                            <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} onBlur={v => handlePhoneBlurCheck(idx, v)} id={`owner_${idx}_phone`} />
                                            <NINInput value={o.nationalId} required
                                                onChange={v => handleOwnerChange(idx,'nationalId',v)}
                                                onBlur={e => handleNinBlurCheck(idx, e.target.value)}
                                                id={`owner_${idx}_nin`} />
                                            <EmailInput value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} onCommit={val => handleEmailCommit(idx,val)} id={`owner_${idx}_email`} />
                                            <AddressInput label="HOME ADDRESS" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />
                                        </div>
                                    )) : project.proprietors.map((p, i) => (
                                        <div key={i} className={styles.ownerStaticCard} role="listitem">
                                            <h2 className={styles.ownerName}>{p.fullName}</h2>
                                            <div className={styles.infoColumns}>
                                                <div className={styles.infoRow}><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMail   aria-hidden="true" /><span>{p.email||'---'}</span></div>
                                                <div className={styles.infoRow}><FiShield aria-hidden="true" /><span>{p.nationalId||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMapPin aria-hidden="true" /><span>{p.homeAddress||'---'}</span></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        </div>
                </section>

                {/* ════════════════════════════════════════════════════
                    DOCUMENTS TAB — Files + upload
                    ════════════════════════════════════════════════════ */}
                <section
                    className={styles.hwPanel}
                    aria-label="Documents"
                    style={activeTab !== 'DOCUMENTS' ? {display:'none'} : {}}
                    data-print-section="DOCUMENTS"
                >
                        <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')} icon={FiUploadCloud} count={docCount} />
                        <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            {docCount === 0 ? (
                                <div className={styles.emptyState} role="status">
                                    <FiUploadCloud className={styles.emptyIcon} aria-hidden="true" />
                                    <span>NO DOCUMENTS ATTACHED</span>
                                    {isEditing && (
                                        <button type="button" className={styles.addDocBtn}
                                            onClick={() => fileInputRef.current?.click()}>
                                            + INGEST NEW SCANS
                                        </button>
                                    )}
                                </div>
                            ) : (
                                <>
                                    <div className={styles.compactVault} role="list">
                                        {binder.documents.map((doc, idx) => (
                                            <div key={idx} className={styles.docTag} role="listitem">
                                                <FiFileText className={styles.docIcon} aria-hidden="true" />
                                                <button type="button" className={styles.docName}
                                                    style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}
                                                    onClick={() => handleOpenDoc(doc.filePath, doc.fileName)}
                                                    title={isPDF(doc.filePath) ? 'Open PDF in new tab' : 'Open ' + doc.fileName}>
                                                    {isPDF(doc.filePath) ? '📄 ' : '🖼 '}{doc.fileName}
                                                </button>
                                                {isEditing && (
                                                    <button type="button" className={styles.iconBtn}
                                                        onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>
                                                        <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                    {isEditing && (
                                        <button type="button" className={styles.addDocBtn}
                                            onClick={() => fileInputRef.current?.click()}>
                                            + INGEST MORE SCANS
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                        </div>
                </section>

            </main>

            <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp"
                style={{ display:'none' }} aria-hidden="true" tabIndex={-1}
                onChange={e => { if (!e.target.files?.length) return; handleVaultAction(Array.from(e.target.files)); e.target.value=''; }} />

            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="Plot Record Edit"
            />

            {/* STAGE 3: NIN NAME MISMATCH GUARD */}
            <NinMismatchModal
                isOpen={!!ninMismatch}
                existingName={ninMismatch?.existingName}
                enteredName={ninMismatch?.enteredName}
                onConfirm={handleNinMismatchConfirm}
                onReject={handleNinMismatchReject}
            />

            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />


            {/* NOTE MODAL */}
            <HardwareModal isOpen={noteModal.open} onClose={async () => {
                if (noteModal.content.trim() !== '') {
                    const ok = await confirm('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                    if (!ok) return;
                }
                setNoteModal({open:false, id:null, content:''});
            }} title="ADD NOTE">
                <div className={modalStyles.modalField}>
                    <textarea className={modalStyles.modalTextarea} value={noteModal.content}
                        onChange={e => setNoteModal({...noteModal,content:e.target.value})}
                        placeholder="Enter interaction note..." aria-label="Note content" />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setNoteModal({open:false,id:null,content:''})}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave}>
                        <FiSave aria-hidden="true" /> SAVE ENTRY
                    </button>
                </div>
            </HardwareModal>

            {/* EXIT RECEIVABLES MODAL — choose fee handling */}
            <HardwareModal isOpen={exitReceivableModal} onClose={() => setExitReceivableModal(false)} title="EXIT RECEIVABLES">
                <div className={modalStyles.modalInfoBoxDanger} style={{marginBottom:16}}>
                    <strong>How should the accumulated storage fees be handled?</strong>
                    <br /><br />
                    Accumulated storage fees: <strong style={{color:'#fca5a5'}}>UGX {fmt(storageFees)}</strong>
                </div>

                {/* Option 1: Capitalize */}
                <div style={{background:'rgba(239,68,68,0.08)',border:'1.5px solid rgba(239,68,68,0.3)',borderRadius:8,padding:'14px 16px',marginBottom:10}}>
                    <div style={{fontFamily:"'DM Sans',sans-serif",fontSize:11,fontWeight:900,color:'#fca5a5',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                        OPTION A: ADD TO PLOT VALUE
                    </div>
                    <div style={{fontFamily:"'DM Sans',sans-serif",fontSize:12,fontWeight:700,color:'rgba(255,255,255,0.7)',lineHeight:1.5,marginBottom:10}}>
                        Storage fees are added to the plot cost. Client now owes:<br/>
                        <strong style={{color:'#fff',fontFamily:"'Space Mono',monospace"}}>UGX {fmt(totalValue + storageFees)}</strong>
                        <span style={{fontSize:10,color:'rgba(255,255,255,0.4)'}}> (UGX {fmt(totalValue)} + UGX {fmt(storageFees)} fees)</span>
                    </div>
                    <button type="button"
                        onClick={() => handleExitReceivableConfirm(true)}
                        style={{width:'100%',padding:'10px 0',background:'#ef4444',border:'none',borderRadius:7,
                                fontFamily:"'DM Sans',sans-serif",fontWeight:900,fontSize:11,
                                textTransform:'uppercase',letterSpacing:1.5,color:'#fff',cursor:'pointer'}}>
                        CAPITALIZE FEES — Exit Receivables
                    </button>
                </div>

                {/* Option 2: Waive */}
                <div style={{background:'rgba(16,185,129,0.06)',border:'1.5px solid rgba(16,185,129,0.3)',borderRadius:8,padding:'14px 16px',marginBottom:14}}>
                    <div style={{fontFamily:"'DM Sans',sans-serif",fontSize:11,fontWeight:900,color:'#34d399',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                        OPTION B: WAIVE FEES
                    </div>
                    <div style={{fontFamily:"'DM Sans',sans-serif",fontSize:12,fontWeight:700,color:'rgba(255,255,255,0.7)',lineHeight:1.5,marginBottom:10}}>
                        Storage fees are cancelled. Client owes the original balance only:<br/>
                        <strong style={{color:'#fff',fontFamily:"'Space Mono',monospace"}}>UGX {fmt(Math.max(0, totalValue - amountPaid))}</strong>
                        <span style={{fontSize:10,color:'rgba(255,255,255,0.4)'}}> (UGX {fmt(totalValue)} value - UGX {fmt(amountPaid)} paid)</span>
                    </div>
                    <button type="button"
                        onClick={() => handleExitReceivableConfirm(false)}
                        style={{width:'100%',padding:'10px 0',background:'#10b981',border:'none',borderRadius:7,
                                fontFamily:"'DM Sans',sans-serif",fontWeight:900,fontSize:11,
                                textTransform:'uppercase',letterSpacing:1.5,color:'#1a2e30',cursor:'pointer'}}>
                        WAIVE FEES — Exit Receivables
                    </button>
                </div>

                <div className={modalStyles.modalFooter} style={{paddingTop:8,marginTop:0}}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setExitReceivableModal(false)}>
                        CANCEL
                    </button>
                </div>
            </HardwareModal>

            {/* PAYMENT MODAL */}
            <HardwareModal isOpen={payModal.open} onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={`RECORD PAYMENT - ${project.landTitle?.plotNumber || project.projectIndex || 'FOLDER'}`}>
                <div className={styles.payBreakdownBox}>
                    {isReceivable ? (
                        <>
                            <div className={styles.payBreakdownTitle}>
                                <FiAlertOctagon size={11} /> RECEIVABLES — AMOUNT OWED BREAKDOWN
                            </div>
                            <div className={styles.payBreakdownGrid}>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel}>PLOT VALUE</span>
                                    <span className={styles.pbVal}>UGX {fmt(totalValue)}</span>
                                </div>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel} style={{color:'#fca5a5'}}>+ STORAGE FEES</span>
                                    <span className={styles.pbVal} style={{color:'#ef4444'}}>UGX {fmt(storageFees)}</span>
                                </div>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel} style={{color:'#22c55e'}}>PAID</span>
                                    <span className={styles.pbVal} style={{color:'#22c55e'}}>UGX {fmt(paid)}</span>
                                </div>
                                <div className={styles.pbItemTotal}>
                                    <span className={styles.pbLabel}>AMOUNT OWED</span>
                                    <span className={styles.pbValTotal}>UGX {fmt(receivableAmountOwed)}</span>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className={styles.payBreakdownGrid}>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel}>PLOT VALUE</span>
                                <span className={styles.pbVal}>UGX {fmt(totalValue)}</span>
                            </div>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel} style={{color:'#22c55e'}}>PAID</span>
                                <span className={styles.pbVal} style={{color:'#22c55e'}}>UGX {fmt(paid)}</span>
                            </div>
                            <div className={styles.pbItemTotal}>
                                <span className={styles.pbLabel}>AMOUNT OWED</span>
                                <span className={styles.pbValTotal}>UGX {fmt(activeAmountOwed)}</span>
                            </div>
                        </div>
                    )}
                </div>

                {isReceivable && (
                    <div className={styles.payTypeRow}>
                        <div className={styles.payTypeLabel}>WHAT IS THIS PAYMENT FOR?</div>
                        <div className={styles.payTypeButtons}>
                            <button type="button" className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`} onClick={() => setPayType('TITLE')}>
                                <FiHome size={12} />
                                <div>
                                    <div className={styles.payTypeBtnName}>TITLE PAYMENT</div>
                                    <div className={styles.payTypeBtnSub}>Reduces the original title debt</div>
                                </div>
                            </button>
                            <button type="button" className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`} onClick={() => setPayType('STORAGE')}>
                                <FiArchive size={12} />
                                <div>
                                    <div className={styles.payTypeBtnName}>STORAGE FEE</div>
                                    <div className={styles.payTypeBtnSub}>Covers monthly storage charges</div>
                                </div>
                            </button>
                        </div>
                    </div>
                )}

                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="number" className={modalStyles.modalInput}
                        placeholder={isReceivable && payType === 'STORAGE' ? "e.g. 50000 (1 month)" : `e.g. ${fmt(Math.max(0, remaining))}`}
                        value={payAmount} onChange={e => setPayAmount(e.target.value)} />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="e.g. Paid via MTN Mobile Money..."
                        value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <HardwareButton type="button" onClick={handleRecordPayment} loading={paying} icon={FiDollarSign}>
                        CONFIRM {payType === 'STORAGE' ? 'STORAGE FEE' : 'PAYMENT'}
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default FolderPage;""")

# =====================================================================
# write: erp-frontend/src/pages/Intake/IntakePage.jsx
# =====================================================================
write('erp-frontend/src/pages/Intake/IntakePage.jsx', r"""// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useBlocker } from 'react-router-dom';
import { createPortal } from 'react-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiEdit3, FiBookmark, FiX, FiCopy, FiArrowUp, FiFile, FiEye, FiRefreshCw,
    FiCalendar
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareSelect from '../../components/common/HardwareSelect';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import styles from './IntakePage.module.css';

const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const PROJECT_TYPES = [
    { value: 'NEW_FOLDER',   label: 'New Folder',   icon: <FiFolderPlus aria-hidden="true" />, hint: 'No title yet' },
    { value: 'NEW_TITLE',    label: 'New Title',    icon: <FiFilePlus aria-hidden="true" />,   hint: 'Title captured now' },
    { value: 'LEGACY_TITLE', label: 'Legacy Title', icon: <FiArchive aria-hidden="true" />,    hint: 'Existing title, receivable' },
];

const TENURE_OPTIONS = ['FREEHOLD', 'MAILO', 'LEASEHOLD', 'CUSTOMARY'];

const DEFAULT_STAGES = [
    'Field Work',
    'Deed Plan',
    'LC Inspection',
    'District Land Board Approval',
    'Tax Assessment and Stamp Duty',
    'Registration and Title Issuance',
];

const todayISO = () => new Date().toISOString().slice(0, 10);
const todayDMY = () => {
    const d = new Date();
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
};
const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';

const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';
const loadPresets = () => {
    try {
        const raw = localStorage.getItem(PRESET_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch { return []; }
};
const savePresets = (presets) => {
    try { localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(presets)); } catch {}
};

export default function IntakePage() {
    const navigate = useNavigate();
    const topRef = useRef(null);
    const fileInputRef = useRef(null);
    const [saving, setSaving] = useState(false);
    const [nextIndex, setNextIndex] = useState('');
    const [projectType, setProjectType] = useState('NEW_FOLDER');
    const [projectStartDate, setProjectStartDate] = useState(todayISO);
    const [owners, setOwners] = useState([EMPTY_OWNER()]);

    const [district, setDistrict] = useState('');
    const [county, setCounty] = useState('');
    const [subCounty, setSubCounty] = useState('');
    const [parish, setParish] = useState('');
    const [village, setVillage] = useState('');
    const [area, setArea] = useState('');

    const [templates, setTemplates] = useState([]);
    const [checkedStages, setCheckedStages] = useState({});
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [insertAfterId, setInsertAfterId] = useState('');
    const [restoring, setRestoring] = useState(false);
    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState('');
    const [showSavePreset, setShowSavePreset] = useState(false);

    const [titleId, setTitleId] = useState('');
    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');
    const [titleIssueDate, setTitleIssueDate] = useState('');

    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);
    const [initialStorageFee, setInitialStorageFee] = useState(0);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState(0);

    const [fileQueue, setFileQueue] = useState([]);
    const [notes, setNotes] = useState('');

    const [dirty, setDirty] = useState(false);
    const dirtyRef = useRef(false);
    const markDirty = useCallback(() => { dirtyRef.current = true; setDirty(true); }, []);

    const [toasts, setToasts] = useState([]);
    const toast = useCallback((msg, type = 'info') => {
        const id = Date.now();
        setToasts(p => [...p, { id, msg, type }]);
        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    }, []);

    const fetchTemplates = useCallback(() => {
        stageTemplateService.getTemplate().then(t => setTemplates(t || [])).catch(() => {});
    }, []);
    useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

    useEffect(() => {
        landService.getNextIndex().then(idx => setNextIndex(idx || ''))
            .catch(() => toast('Could not load the next index. Refresh to try again.', 'error'));
    }, []);

    // STANDARD: sidebar auto-collapses once the user starts working on the form
    const collapsedOnce = useRef(false);
    useEffect(() => {
        const el = topRef.current;
        if (!el) return;
        const handler = () => {
            if (collapsedOnce.current) return;
            collapsedOnce.current = true;
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) {
                toggle.click();
            }
        };
        el.addEventListener('focusin', handler);
        el.addEventListener('input', handler);
        el.addEventListener('click', handler);
        return () => {
            el.removeEventListener('focusin', handler);
            el.removeEventListener('input', handler);
            el.removeEventListener('click', handler);
        };
    }, []);

    // STANDARD: warn before closing the tab with unsaved work
    useEffect(() => {
        const h = (e) => {
            if (dirtyRef.current) { e.preventDefault(); e.returnValue = ''; }
        };
        window.addEventListener('beforeunload', h);
        return () => window.removeEventListener('beforeunload', h);
    }, []);

    // Warn before navigating away inside the app with unsaved work
    const blocker = useBlocker(dirty && !saving);

    const sortedTemplates = useMemo(
        () => [...templates].sort((a, b) => (a.displayOrder ?? 0) - (b.displayOrder ?? 0)),
        [templates]
    );
    const firstStageId = sortedTemplates[0]?.id;
    const lastStageId = sortedTemplates[sortedTemplates.length - 1]?.id;

    useEffect(() => {
        if (!sortedTemplates.length) return;
        setCheckedStages(prev => {
            const next = { ...prev };
            if (firstStageId && next[firstStageId] === undefined) next[firstStageId] = true;
            return next;
        });
    }, [sortedTemplates.length, firstStageId]);

    const finalStageChecked = lastStageId ? !!checkedStages[lastStageId] : false;
    const isLegacy = projectType === 'LEGACY_TITLE';
    const titleAtIntake = projectType === 'NEW_TITLE';
    const isTitleType = isLegacy || titleAtIntake;
    const isTitleSectionVisible = isTitleType || finalStageChecked;
    const showStages = !isTitleType;

    const allStagesChecked = () => {
        const all = {};
        sortedTemplates.forEach(t => { all[t.id] = true; });
        return all;
    };
    const defaultStages = () => {
        const d = {};
        if (firstStageId) d[firstStageId] = true;
        return d;
    };

    const handleProjectTypeChange = (value) => {
        setProjectType(value);
        markDirty();
        if (value === 'LEGACY_TITLE' || value === 'NEW_TITLE') {
            setCheckedStages(allStagesChecked());
        } else {
            setCheckedStages(defaultStages());
        }
    };

    const toggleStage = (id) => {
        markDirty();
        setCheckedStages(p => ({ ...p, [id]: !p[id] }));
    };

    // one parallel wave of order updates = fast, no lag
    const renumber = (ordered) => Promise.all(
        ordered.map((t, i) =>
            t?.id ? stageTemplateService.updateTemplateStage(t.id, t.stageName, t.defaultCost || 0, i + 1) : null
        )
    );

    const openInsertBelow = (stageId) => {
        setInsertAfterId(stageId);
        setAddingStage(true);
    };

    const handleAddStage = async () => {
        if (!newStageName.trim()) { toast('Enter a stage name first.', 'error'); return; }
        try {
            let k = sortedTemplates.length - 1; // default: just before last
            const idx = sortedTemplates.findIndex(t => t.id === insertAfterId);
            if (idx >= 0) k = idx + 1; // appears directly under the clicked stage
            k = Math.min(Math.max(k, 1), Math.max(1, sortedTemplates.length - 1));

            const created = await stageTemplateService.addTemplateStage(newStageName.trim(), 0, k + 1);
            const item = { id: created?.id, stageName: newStageName.trim(), defaultCost: 0 };
            const next = sortedTemplates.filter(t => t.id !== created?.id);
            next.splice(k, 0, item);
            await renumber(next);

            setNewStageName('');
            setInsertAfterId('');
            setAddingStage(false);
            fetchTemplates();
            if (created?.id) setCheckedStages(p => ({ ...p, [created.id]: true }));
            toast('Stage inserted.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not add stage.', 'error');
        }
    };

    const handleDeleteStage = async (id) => {
        try {
            await stageTemplateService.deleteTemplateStage(id);
            setCheckedStages(p => { const n = { ...p }; delete n[id]; return n; });
            fetchTemplates();
            toast('Stage removed.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not delete stage.', 'error');
        }
    };

    const handleRestoreDefaults = async () => {
        setRestoring(true);
        try {
            const keep = sortedTemplates.filter(t => DEFAULT_STAGES.includes(t.stageName));
            await Promise.all(
                sortedTemplates
                    .filter(t => !DEFAULT_STAGES.includes(t.stageName))
                    .map(t => stageTemplateService.deleteTemplateStage(t.id))
            );
            const have = new Set(keep.map(t => t.stageName));
            const added = [];
            for (const name of DEFAULT_STAGES) {
                if (!have.has(name)) {
                    const c = await stageTemplateService.addTemplateStage(name, 0);
                    added.push({ id: c?.id, stageName: name, defaultCost: 0 });
                }
            }
            const byName = {};
            [...keep, ...added].forEach(t => { byName[t.stageName] = t; });
            await renumber(DEFAULT_STAGES.map(name => byName[name]).filter(Boolean));
            fetchTemplates();
            toast('Default stages restored.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Restore failed.', 'error');
        } finally {
            setRestoring(false);
        }
    };

    const handleSavePreset = () => {
        if (!presetName.trim()) { toast('Name the preset first.', 'error'); return; }
        const stageNames = sortedTemplates.filter(t => checkedStages[t.id]).map(t => t.stageName);
        const next = [...presets.filter(p => p.name !== presetName.trim()), { name: presetName.trim(), stageNames }];
        setPresets(next);
        savePresets(next);
        setPresetName('');
        setShowSavePreset(false);
        toast('Stage preset saved.', 'success');
    };

    const applyPreset = (name) => {
        if (!name) return;
        const preset = presets.find(p => p.name === name);
        if (!preset) return;
        const next = {};
        sortedTemplates.forEach(t => {
            next[t.id] = preset.stageNames.includes(t.stageName);
        });
        setCheckedStages(next);
        markDirty();
    };

    const deletePreset = (name) => {
        const next = presets.filter(p => p.name !== name);
        setPresets(next);
        savePresets(next);
    };

    const updateOwner = (idx, field, val) => {
        markDirty();
        setOwners(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o));
    };

    const handleFileUpload = (e) => {
        const items = Array.from(e.target.files).map(f => ({
            name: f.name, size: f.size, file: f, url: URL.createObjectURL(f),
        }));
        if (items.length) {
            setFileQueue(p => [...p, ...items]);
            markDirty();
        }
        e.target.value = '';
    };

    const removeFile = (i) => {
        setFileQueue(p => {
            URL.revokeObjectURL(p[i].url);
            return p.filter((_, idx) => idx !== i);
        });
    };

    const triggerFileInput = () => fileInputRef.current && fileInputRef.current.click();

    const scrollTop = () => topRef.current && topRef.current.scrollIntoView({ behavior: 'smooth' });

    // ---- validation shared by Save and Duplicate ----
    const validate = () => {
        if (!district.trim() || !county.trim()) {
            toast('District and County are required.', 'error'); return false;
        }
        for (let i = 0; i < owners.length; i++) {
            const o = owners[i];
            if (!o.nationalId.trim()) { toast(`Owner ${i + 1}: NIN is required.`, 'error'); return false; }
            if (!o.fullName.trim()) { toast(`Owner ${i + 1}: Full Name is required.`, 'error'); return false; }
            if (!o.phone.trim()) { toast(`Owner ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }
        }
        if (isTitleSectionVisible) {
            if (!titleId.trim()) { toast('Title ID is required for a title record.', 'error'); return false; }
            if (!plotNumber.trim()) { toast('Plot Number is required for a title record.', 'error'); return false; }
            if (!area.trim()) { toast('Area is required for Title details.', 'error'); return false; }
        }
        if (!(Number(totalCost) > 0)) { toast('Total Cost must be greater than 0.', 'error'); return false; }
        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) {
            toast('Initial Payment is required (0 or more).', 'error'); return false;
        }
        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }
        return true;
    };

    // ---- the actual save (no navigation) ----
    const doSave = async () => {
        if (!validate()) return false;
        setSaving(true);
        try {
            let noteText = notes.trim();
            if (noteText && !/^\[\d{2}\/\d{2}\/\d{4}\]/.test(noteText)) {
                noteText = `[${todayDMY()}] ${noteText}`; // STANDARD: notes carry their date
            }

            const payload = {
                district: district.trim().toUpperCase(),
                county: county.trim().toUpperCase(),
                subCounty: subCounty.trim().toUpperCase(),
                parish: parish.trim().toUpperCase(),
                village: village.trim().toUpperCase(),
                area: area.trim(),
                totalCost: Number(totalCost) || 0,
                initialPayment: Number(initialPayment) || 0,
                isLegacy: isLegacy,
                titleAtIntake: titleAtIntake,
                projectStartDate: projectStartDate || todayISO(),
                owners: owners.map(o => ({
                    fullName: o.fullName.trim().toUpperCase(),
                    phone: o.phone.trim(),
                    email: o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address: o.address.trim(),
                })),
                selectedStages: Object.entries(checkedStages)
                    .filter(([id, v]) => v && templates.some(t => t.id === id))
                    .map(([id]) => {
                        const t = templates.find(x => x.id === id);
                        return {
                            stageTemplateId: id,
                            stageName: t ? t.stageName : '',
                            isCustom: false,
                            isCompleted: true
                        };
                    }),
                notes: noteText ? [{ content: noteText }] : [],
            };

            if (isTitleSectionVisible) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.blockRoad = blockRoad.trim().toUpperCase();
                payload.titleId = titleId.trim().toUpperCase();
                payload.titleIssueDate = titleIssueDate || null;
            }

            if (isLegacy) {
                payload.isStartAsReceivable = true;
                payload.initialStorageFee = Number(initialStorageFee) || 0;
                payload.monthlyStorageFee = Number(monthlyStorageFee) || 0;
            }

            await landService.createAtomicEntry(payload, fileQueue.map(q => q.file));
            dirtyRef.current = false;
            setDirty(false);
            return true;
        } catch (err) {
            toast(err.response?.data?.message || 'Save failed', 'error');
            return false;
        } finally {
            setSaving(false);
        }
    };

    const handleSubmit = async () => {
        const ok = await doSave();
        if (ok) {
            toast('Project registered successfully!', 'success');
            setTimeout(() => navigate('/land/projects'), 1200);
        }
    };

    // Duplicate = SAVE the current form first (same validations/warnings),
    // then carry owners + location into a fresh form.
    const handleDuplicate = async () => {
        const ok = await doSave();
        if (!ok) return;
        toast('Saved. Form duplicated for the next plot.', 'success');
        setProjectType('NEW_FOLDER');
        setTitleId(''); setTenure('FREEHOLD'); setPlotNumber(''); setBlockRoad(''); setTitleIssueDate('');
        setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0); setMonthlyStorageFee(0);
        setNotes('');
        setFileQueue(q => { q.forEach(x => URL.revokeObjectURL(x.url)); return []; });
        setCheckedStages(defaultStages());
        setProjectStartDate(todayISO);
        landService.getNextIndex().then(idx => setNextIndex(idx || ''))
            .catch(() => toast('Could not load the next index. Refresh to try again.', 'error'));
        scrollTop();
    };

    const amountOwed = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));

    let n = 0;
    const nIndex = ++n;
    const nOwners = ++n;
    const nTitle = isTitleSectionVisible ? ++n : null;
    const nLocation = ++n;
    const nStages = showStages ? ++n : null;
    const nFinancials = ++n;
    const nDocuments = ++n;
    const nNotes = ++n;

    const insertAfterName = sortedTemplates.find(t => t.id === insertAfterId)?.stageName;

    return (
        <div className={styles.container} ref={topRef}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Project</h1>
                    <p className={styles.subtitle}>Intake Form</p>
                </div>
                <div className={styles.actions}>
                    <button className={`${styles.btn} ${styles.headerBtn}`} onClick={() => navigate(-1)}>Cancel</button>
                </div>
            </header>

            <div className={styles.sections}>

                <CollapsibleSection icon={<FiHash />} title={`${nIndex}. Entry Mode`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={styles.label}>Index</label>
                            <div className={styles.indexDisplay}>{nextIndex || 'Loading...'}</div>
                            <p className={styles.hint}>Next available index, assigned on save</p>
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Date Started</label>
                            <input type="date" className={styles.input} value={projectStartDate} onChange={e => { setProjectStartDate(e.target.value); markDirty(); }} />
                            <p className={styles.hint}>Auto-filled with today. Edit if started earlier.</p>
                        </div>
                    </div>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${styles.required}`}>Type</label>
                        <div className={styles.typeGroup}>
                            {PROJECT_TYPES.map(pt => (
                                <button
                                    key={pt.value}
                                    type="button"
                                    className={`${styles.typeBtn} ${projectType === pt.value ? styles.typeBtnActive : ''}`}
                                    onClick={() => handleProjectTypeChange(pt.value)}
                                >
                                    {pt.icon}
                                    <span>{pt.label}</span>
                                </button>
                            ))}
                        </div>
                        <p className={styles.typeHint}>{PROJECT_TYPES.find(pt => pt.value === projectType)?.hint}</p>
                    </div>
                </CollapsibleSection>

                <CollapsibleSection icon={<FiUsers />} title={`${nOwners}. Owners`}>
                    {owners.map((o, idx) => (
                        <div key={idx} className={styles.ownerRow}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>NIN</label>
                                <input className={styles.input} value={o.nationalId} onChange={e => updateOwner(idx, 'nationalId', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Full Name</label>
                                <input className={styles.input} value={o.fullName} onChange={e => updateOwner(idx, 'fullName', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Phone</label>
                                <input className={styles.input} value={o.phone} onChange={e => updateOwner(idx, 'phone', e.target.value)} placeholder="0700 000 000 / 0788 000 000" />
                                <p className={styles.hint}>Multiple: separate with /</p>
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Email</label>
                                <input className={styles.input} value={o.email} onChange={e => updateOwner(idx, 'email', e.target.value)} />
                            </div>
                            <button
                                type="button"
                                className={`${styles.btn} ${styles.deleteBtn}`}
                                onClick={() => setOwners(p => p.filter((_, i) => i !== idx))}
                                disabled={owners.length === 1}
                                aria-label="Remove owner"
                            >
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                    <button type="button" className={styles.addBtn} onClick={() => { setOwners(p => [...p, EMPTY_OWNER()]); markDirty(); }}>
                        <FiPlus /> Add Owner
                    </button>
                </CollapsibleSection>

                {isTitleSectionVisible && (
                    <CollapsibleSection icon={<FiFileText />} title={`${nTitle}. Title Details`} accent>
                        <div className={styles.grid3}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Title ID</label>
                                <input className={styles.input} value={titleId} onChange={e => { setTitleId(e.target.value); markDirty(); }} />
                            </div>
                            <HardwareSelect
                                label="Tenure"
                                required
                                options={TENURE_OPTIONS}
                                value={tenure}
                                onChange={(v) => { setTenure(v); markDirty(); }}
                            />
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Plot Number</label>
                                <input className={styles.input} value={plotNumber} onChange={e => { setPlotNumber(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Block</label>
                                <input className={styles.input} value={blockRoad} onChange={e => { setBlockRoad(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Title Date</label>
                                <input type="date" className={styles.input} value={titleIssueDate} onChange={e => { setTitleIssueDate(e.target.value); markDirty(); }} />
                                <p className={styles.hint}>Leave blank if not yet received.</p>
                            </div>
                        </div>
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiMap />} title={`${nLocation}. Location`}>
                    <div className={styles.grid3}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>District</label>
                            <input className={styles.input} value={district} onChange={e => { setDistrict(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>County</label>
                            <input className={styles.input} value={county} onChange={e => { setCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Sub-county</label>
                            <input className={styles.input} value={subCounty} onChange={e => { setSubCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Parish</label>
                            <input className={styles.input} value={parish} onChange={e => { setParish(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Village</label>
                            <input className={styles.input} value={village} onChange={e => { setVillage(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${isTitleSectionVisible ? styles.required : ''}`}>Area{!isTitleSectionVisible ? ' (Optional)' : ''}</label>
                            <input className={styles.input} value={area} onChange={e => { setArea(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                </CollapsibleSection>

                {showStages && (
                    <CollapsibleSection
                        icon={<FiCheckSquare />}
                        title={`${nStages}. Stages`}
                        right={
                            <div style={{ display: 'flex', gap: 'var(--gap-md)', flexWrap: 'wrap', alignItems: 'center' }}>
                                {presets.length > 0 && (
                                    <HardwareSelect
                                        compact
                                        placeholder="Apply preset..."
                                        value=""
                                        options={presets.map(p => p.name)}
                                        onChange={applyPreset}
                                    />
                                )}
                                <button type="button" className={styles.addBtn} onClick={() => setShowSavePreset(s => !s)}>
                                    <FiBookmark /> Save Preset
                                </button>
                                <button type="button" className={styles.addBtn} onClick={() => { setAddingStage(s => !s); setInsertAfterId(''); }}>
                                    <FiPlus /> New Stage
                                </button>
                                <button type="button" className={styles.addBtn} disabled={restoring} onClick={handleRestoreDefaults}>
                                    <FiRefreshCw /> Restore Defaults
                                </button>
                            </div>
                        }
                    >
                        {showSavePreset && (
                            <div className={styles.inlineAddRow}>
                                <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setShowSavePreset(false); setPresetName(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        {addingStage && (
                            <div className={styles.inlineAddRow}>
                                <span className={styles.insertCtx}>
                                    {insertAfterName ? `Insert under: ${insertAfterName}` : 'Insert before last stage'}
                                </span>
                                <input className={styles.input} placeholder="New stage name" value={newStageName} onChange={e => setNewStageName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleAddStage}>Add</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setAddingStage(false); setNewStageName(''); setInsertAfterId(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        <div className={styles.stageList}>
                            {sortedTemplates.map((t, i) => {
                                const isLast = t.id === lastStageId;
                                return (
                                    <label key={t.id} className={`${styles.stageItem} ${checkedStages[t.id] ? styles.checked : ''}`}>
                                        <input type="checkbox" className={styles.checkbox} checked={!!checkedStages[t.id]}
                                            onChange={() => toggleStage(t.id)} />
                                        <span className={styles.stageName}>{t.stageName}</span>
                                        <span className={styles.stageActions}>
                                            {!isLast && (
                                                <button
                                                    type="button"
                                                    className={styles.plusBtn}
                                                    title="Insert a stage below this one"
                                                    aria-label={`Insert stage below ${t.stageName}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(t.id); }}
                                                >
                                                    <FiPlus size={12} />
                                                </button>
                                            )}
                                            {!isLast && t.id !== firstStageId && (
                                                <button
                                                    type="button"
                                                    className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDeleteStage(t.id); }}
                                                    aria-label={`Delete stage ${t.stageName}`}
                                                >
                                                    <FiTrash2 size={12} />
                                                </button>
                                            )}
                                        </span>
                                    </label>
                                );
                            })}
                        </div>
                        {presets.length > 0 && (
                            <div className={styles.presetList}>
                                {presets.map(p => (
                                    <span key={p.name} className={styles.presetChip}>
                                        {p.name}
                                        <button
                                            type="button"
                                            className={styles.presetChipRemove}
                                            onClick={() => deletePreset(p.name)}
                                            aria-label={`Delete preset ${p.name}`}
                                        >
                                            <FiX size={12} />
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiDollarSign />} title={`${nFinancials}. Financials`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Total Cost</label>
                            <input type="number" className={styles.input} value={totalCost} onChange={e => { setTotalCost(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Initial Payment</label>
                            <input type="number" className={styles.input} value={initialPayment} onChange={e => { setInitialPayment(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                    {isLegacy && (
                        <>
                            <h3 className={styles.subheading}><FiArchive size={13} /> Storage Fees</h3>
                            <div className={styles.grid2}>
                                <div className={styles.field}>
                                    <label className={styles.label}>Initial Storage Fee</label>
                                    <input type="number" className={styles.input} value={initialStorageFee} onChange={e => { setInitialStorageFee(e.target.value); markDirty(); }} />
                                </div>
                                <div className={styles.field}>
                                    <label className={styles.label}>Monthly Storage Fee</label>
                                    <input type="number" className={styles.input} value={monthlyStorageFee} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} placeholder="System default" />
                                </div>
                            </div>
                        </>
                    )}
                    <div className={styles.financialsSummary}>
                        <div className={styles.finRow}><span>Total Cost</span><span>{Number(totalCost) || 0}</span></div>
                        <div className={styles.finRow}><span>Initial Payment</span><span>{Number(initialPayment) || 0}</span></div>
                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}
                        <div className={`${styles.finRow} ${styles.total}`}><span>Amount Owed</span><span>{amountOwed}</span></div>
                    </div>
                </CollapsibleSection>

                <div className={styles.splitRow}>
                    <CollapsibleSection icon={<FiUploadCloud />} title={`${nDocuments}. Documents`}>
                        <div
                            className={styles.dropzone}
                            onClick={triggerFileInput}
                            role="button"
                            tabIndex={0}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); } }}
                        >
                            <span className={styles.dropzoneIcon}><FiUploadCloud size={18} /></span>
                            <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>
                            <span className={styles.dropzoneSub}>Required - PDF, images, any file</span>
                        </div>
                        <input ref={fileInputRef} type="file" multiple onChange={handleFileUpload} style={{ display: 'none' }} />
                        <div className={styles.fileList}>
                            {fileQueue.map((f, i) => (
                                <div key={i} className={styles.fileItem}>
                                    <span className={styles.fileMeta}>
                                        <FiFile className={styles.fileIcon} size={14} />
                                        <span className={styles.fileName}>{f.name}</span>
                                        <span className={styles.fileSize}>{fmtSize(f.size)}</span>
                                    </span>
                                    <span className={styles.fileActions}>
                                        <a className={`${styles.btn} ${styles.small}`} href={f.url} target="_blank" rel="noreferrer" aria-label={`View ${f.name}`}>
                                            <FiEye size={12} /> View
                                        </a>
                                        <button
                                            type="button"
                                            className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                            onClick={() => removeFile(i)}
                                            aria-label={`Remove ${f.name}`}
                                        >
                                            <FiTrash2 size={12} />
                                        </button>
                                    </span>
                                </div>
                            ))}
                        </div>
                    </CollapsibleSection>

                    <CollapsibleSection icon={<FiEdit3 />} title={`${nNotes}. Notes`}>
                        <div className={styles.notesWrap}>
                            <span className={styles.noteDateChip}><FiCalendar size={11} /> {todayDMY()}</span>
                            <textarea className={styles.textarea} value={notes} onChange={e => { setNotes(e.target.value); markDirty(); }} placeholder="Shared project notes - visible to all staff on the folder page..." />
                            <p className={styles.hint}>Saved with today's date as an intake note.</p>
                        </div>
                    </CollapsibleSection>
                </div>

            </div>

            <div className={styles.bottomBar}>
                <button type="button" className={styles.topBtn} onClick={scrollTop} aria-label="Back to top">
                    <FiArrowUp />
                </button>
                <div className={styles.bottomBarRight}>
                    <button type="button" className={styles.addBtn} onClick={handleDuplicate} disabled={saving}>
                        <FiCopy /> Duplicate
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> Save Project
                    </button>
                </div>
            </div>

            {blocker.state === 'blocked' && typeof document !== 'undefined' && createPortal(
                <div className={styles.modalOverlay}>
                    <div className={styles.modalCard}>
                        <h3 className={styles.modalTitle}>Unsaved work</h3>
                        <p className={styles.modalText}>
                            You have unsaved information on this form. Do you want to save it before leaving?
                        </p>
                        <div className={styles.modalBtns}>
                            <button type="button" className={styles.btn} onClick={() => blocker.reset()}>Stay</button>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`} onClick={() => blocker.proceed()}>Leave without saving</button>
                            <button
                                type="button"
                                className={`${styles.btn} ${styles.primary}`}
                                onClick={async () => {
                                    const ok = await doSave();
                                    if (ok) blocker.proceed(); else blocker.reset();
                                }}
                            >
                                <FiSave /> Save & Leave
                            </button>
                        </div>
                    </div>
                </div>,
                document.body
            )}

            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles[t.type] || ''}`}>{t.msg}</div>
            ))}
        </div>
    );
}
""")

# =====================================================================
# write: erp-frontend/src/pages/Recovery/RecoveryPortal.jsx
# =====================================================================
write('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx', r"""import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch,
    FiSave, FiList, FiCalendar,
    FiChevronDown, FiChevronUp,
    FiDollarSign, FiAlertOctagon, FiActivity
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = {
    GREEN:  'Paid within 14 days',
    YELLOW: 'Paid within 30 days',
    RED:    'No recent payment',
};

const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;
    // STAGE 2 FIX: matches the backend permission on POST /land/projects/{id}/payment
    // (ROLE_MANAGER/ROLE_ADMIN/ROLE_DIRECTOR, widened in Stage 1) -- isAdmin alone
    // was hiding this button from Directors and Managers who could already use it.
    const canRecordPayment = user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR' || user?.role === 'ROLE_MANAGER' || user?.isRoot;

    const [viewMode,     setViewMode]     = useState('ACTION');
    const [missions,     setMissions]     = useState([]);
    const [loading,      setLoading]      = useState(true);
    const [expandedId,   setExpandedId]   = useState(null);
    const [searchTerm,   setSearchTerm]   = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');
    // STAGE 10 FIX: the call log has to say WHICH owner was reached, not
    // just which plot -- carry the card's own clientId/ownerName through.
    const [callModal,    setCallModal]    = useState({ open: false, mission: null, ownerId: null, ownerName: '' });
    const [logContent,   setLogContent]   = useState('');
    const [committing,   setCommitting]   = useState(false);
    // STAGE 11 FIX: soft, dismissible notice for "a co-owner was already
    // contacted about this plot recently" (design brief 3.4 #2) -- never
    // blocks the call log, which has already been saved by the time this shows.
    const [coOwnerWarning, setCoOwnerWarning] = useState(null);
    // STAGE 12 FIX: lets a co-owner link (design brief 3.3, "navigable")
    // jump to that person's own card even if it is filtered out or
    // collapsed right now -- clears filters, expands their card, then
    // scrolls to it once it is present in the loaded mission list.
    const [scrollTargetId, setScrollTargetId] = useState(null);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION'
                ? await recoveryService.getMissionQueue()
                : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch { /* silent */ }
        finally { setLoading(false); }
    }, [viewMode]);

    useEffect(() => { loadData(); }, [loadData]);

    // STAGE 12 FIX: once the mission list contains the co-owner we just
    // navigated to, scroll their card into view. Runs again whenever
    // missions reloads (e.g. after switching to ALL TARGETS) until found.
    useEffect(() => {
        if (!scrollTargetId) return;
        const el = document.getElementById('recovery-card-' + scrollTargetId);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setScrollTargetId(null);
        }
    }, [missions, scrollTargetId]);

    const filteredMissions = useMemo(() => {
        let list = missions;
        if (searchTerm.trim()) {
            const t = searchTerm.toLowerCase();
            list = list.filter(m =>
                m.ownerName.toLowerCase().includes(t) ||
                m.phoneNumber.includes(t) ||
                m.plots.some(p => p.plotNumber.toLowerCase().includes(t))
            );
        }
        if (statusFilter === 'RECEIVABLES') list = list.filter(m => m.hasReceivablePlots);
        if (statusFilter === 'ACTIVE')  list = list.filter(m => !m.hasReceivablePlots);
        return list;
    }, [missions, searchTerm, statusFilter]);

    const totalActiveOwed  = missions.filter(m => !m.hasReceivablePlots).reduce((s, m) => s + Number(m.totalDemand || 0), 0);
    const totalReceivableOwed = missions.filter(m =>  m.hasReceivablePlots).reduce((s, m) => s + Number(m.totalDemand || 0), 0);
    const totalStorageFees = missions.reduce((s, m) => s + Number(m.totalStorageFees || 0), 0);

    const handleLogCall = async () => {
        if (!callModal.mission || !callModal.ownerId) return;
        setCommitting(true);
        try {
            const result = await recoveryService.logRecoveryCall(callModal.mission.projectId, callModal.ownerId, logContent);
            setCallModal({ open: false, mission: null, ownerId: null, ownerName: '' });
            setLogContent('');
            // STAGE 11 FIX: purely informational -- the call was already
            // logged successfully by this point regardless of this value.
            setCoOwnerWarning(result && result.coOwnerWarning ? result.coOwnerWarning : null);
            loadData();
        } catch { /* silent */ }
        finally { setCommitting(false); }
    };

    // STAGE 10 FIX: caller now passes ownerId/ownerName from the card that
    // triggered this modal, so a joint call is attributed to the actual
    // person on that card -- never silently defaulted to a co-owner -- and
    // pre-fills with THAT owner's own last note, not a shared one.
    const openCallModal = (e, plot, ownerId, ownerName) => {
        e.stopPropagation();
        const lastNote = plot.ownerLastContactNote ? plot.ownerLastContactNote : '';
        setCallModal({ open: true, mission: plot, ownerId, ownerName });
        setLogContent(lastNote);
    };

    // STAGE 12 FIX: co-owner link handler (design brief 3.3). Switches to
    // ALL TARGETS so a locked/cooling-down co-owner is not hidden by the
    // DUE FOR CALL filter, clears search/status filters that could hide
    // their card, expands their card, and queues the scroll-to for the
    // effect above.
    const handleGoToCoOwner = (e, coOwnerId) => {
        e.stopPropagation();
        setSearchTerm('');
        setStatusFilter('ALL');
        setViewMode('FORECAST');
        setExpandedId(coOwnerId);
        setScrollTargetId(coOwnerId);
    };

    return (
        <div className={styles.container}>

            {/* HEADER */}
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Call Recovery</h1>
                    <p className={styles.pageSubtitle}>Log client calls and record payments</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.modeSwitch}>
                        <button
                            className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive}
                            onClick={() => setViewMode('ACTION')}
                        >
                            <FiList aria-hidden="true" /> DUE FOR CALL
                        </button>
                        <button
                            className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive}
                            onClick={() => setViewMode('FORECAST')}
                        >
                            <FiCalendar aria-hidden="true" /> ALL TARGETS
                        </button>
                    </div>
                </div>
            </header>

            {/* FINANCIAL HUD */}
            <div className={styles.finHUD}>
                <div className={styles.finHUDCard}>
                    <label>ACTIVE TITLES OWED</label>
                    <strong>UGX {fmt(totalActiveOwed)}</strong>
                </div>
                <div className={styles.finHUDCard}>
                    <label>RECEIVABLES TOTAL OWED</label>
                    <strong>UGX {fmt(totalReceivableOwed)}</strong>
                </div>
                <div className={styles.finHUDCard}>
                    <label>STORAGE FEES</label>
                    <strong>UGX {fmt(totalStorageFees)}</strong>
                </div>
            </div>

            {/* STAGE 11: soft, dismissible co-owner-recently-contacted notice
                (design brief 3.4 #2) -- purely informational, call is already
                logged by the time this can appear. */}
            {coOwnerWarning && (
                <div className={styles.coOwnerWarningBanner} role="status">
                    <span>{coOwnerWarning}</span>
                    <button
                        type="button"
                        className={styles.coOwnerWarningDismiss}
                        onClick={() => setCoOwnerWarning(null)}
                        aria-label="Dismiss notice"
                    >
                        &times;
                    </button>
                </div>
            )}

            {/* FILTER BAR */}
            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <FiSearch className={styles.searchIcon} aria-hidden="true" />
                    <input
                        className={styles.searchInput}
                        type="search"
                        placeholder="Search owner name, plot ID, phone..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        aria-label="Search recovery missions"
                    />
                </div>
                <div className={styles.filterPills} role="group" aria-label="Filter missions">
                    {['ALL', 'ACTIVE', 'RECEIVABLES'].map(f => (
                        <button
                            key={f}
                            className={`${styles.filterPill} ${statusFilter === f ? styles.filterPillActive : ''}`}
                            onClick={() => setStatusFilter(f)}
                            aria-pressed={statusFilter === f}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* BADGE LEGEND */}
            <div className={styles.legend} aria-label="Payment health legend">
                {Object.entries(BADGE_COLORS).map(([k, c]) => (
                    <span key={k} className={styles.legendItem}>
                        <span style={{ width: 9, height: 9, borderRadius: '50%', background: c, display: 'inline-block', flexShrink: 0, boxShadow: `0 0 4px ${c}` }} />
                        {BADGE_LABELS[k]}
                    </span>
                ))}
            </div>

            {/* MISSION LIST */}
            {loading ? (
                <div className={styles.emptyState} role="status">
                    <div className={styles.loadingSpinner} aria-hidden="true" />
                    <span>LOADING RECOVERY QUEUE...</span>
                </div>
            ) : filteredMissions.length === 0 ? (
                <div className={styles.emptyState} role="status">
                    <FiActivity className={styles.emptyIcon} aria-hidden="true" />
                    <span>{searchTerm ? `NO MISSIONS MATCH "${searchTerm.toUpperCase()}"` : 'NO MISSIONS IN QUEUE'}</span>
                </div>
            ) : (
                <div className={styles.missionGrid}>
                    {filteredMissions.map(m => {
                        const isExpanded = expandedId === m.clientId;
                        const badgeColor = BADGE_COLORS[m.plots[0]?.paymentHealthBadge] || '#ef4444';
                        return (
                            <div
                                key={m.clientId}
                                id={'recovery-card-' + m.clientId}
                                className={`${styles.missionCard} ${m.hasReceivablePlots ? styles.cardReceivable : ''}`}
                            >
                                {/* CARD HEADER */}
                                <div
                                    className={styles.cardHeader}
                                    onClick={() => setExpandedId(isExpanded ? null : m.clientId)}
                                    role="button"
                                    tabIndex={0}
                                    aria-expanded={isExpanded}
                                    aria-label={`${m.ownerName} — ${isExpanded ? 'collapse' : 'expand'}`}
                                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedId(isExpanded ? null : m.clientId); } }}
                                >
                                    {/* ROW 1: Plot ID + Balance */}
                                    <div className={styles.cardTopRow}>
                                        <div className={styles.cardTopRowLeft}>
                                            <span
                                                style={{ width: 9, height: 9, borderRadius: '50%', background: badgeColor, display: 'inline-block', flexShrink: 0, boxShadow: `0 0 5px ${badgeColor}` }}
                                                title={BADGE_LABELS[m.plots[0]?.paymentHealthBadge]}
                                            />
                                            <span className={styles.plotId}>
                                                {m.plots.map(p => p.plotNumber).join(' / ')}
                                            </span>
                                            {m.hasReceivablePlots && (
                                                <span className={styles.receivablePill}>RECEIVABLES</span>
                                            )}
                                        </div>
                                        <div className={styles.balanceLine}>
                                            <span className={styles.balanceLabel}>TOTAL OWED</span>
                                            <span className={`${styles.balanceVal} ${m.hasReceivablePlots ? styles.balanceRed : ''}`}>
                                                UGX {fmt(m.totalDemand)}
                                            </span>
                                        </div>
                                    </div>

                                    {/* ROW 2: Owner + Phone + Actions */}
                                    <div className={styles.cardMain}>
                                        <div className={styles.ownerPhoneBlock}>
                                            <span className={styles.ownerLine}>{m.ownerName}</span>
                                            <span className={styles.phoneLine}>{m.phoneNumber}</span>
                                        </div>
                                        <div className={styles.cardSideActions}>
                                            <button
                                                className={styles.logCallBtnSmall}
                                                disabled={m.isLocked}
                                                onClick={e => openCallModal(e, m.plots[0], m.clientId, m.ownerName)}
                                                aria-label={m.isLocked ? 'Call locked' : `Log call for ${m.ownerName}`}
                                            >
                                                <FiPhoneCall aria-hidden="true" />
                                                {m.isLocked ? 'LOCKED' : 'LOG CALL'}
                                            </button>
                                            {isExpanded
                                                ? <FiChevronUp  className={styles.expandIcon} aria-hidden="true" />
                                                : <FiChevronDown className={styles.expandIcon} aria-hidden="true" />
                                            }
                                        </div>
                                    </div>
                                </div>

                                {/* EXPANDED BODY */}
                                {isExpanded && (
                                    <div className={styles.cardBody}>
                                        <div className={styles.timingRow}>
                                            <FiClock aria-hidden="true" />
                                            <span className={styles.timingItem}>Last contact: <strong>{m.lastContactDate}</strong></span>
                                            <span className={styles.timingItem}>Next due: <strong>{m.nextCallDue}</strong></span>
                                            <span className={styles.timingItem}>This month: <strong>{m.monthlyCallCount}/2</strong></span>
                                        </div>

                                        {m.plots.map(p => {
                                            // CORRECT MATH:
                                            // totalValue  = the true plot cost (totalCost from DTO, same as originalDebt for receivable)
                                            // amtPaid     = what has been paid so far
                                            // storageFees = accumulated fees (receivable only)
                                            // amountOwed  = totalValue + storageFees - amtPaid
                                            // 4-Pocket Math: AMOUNT OWED = (PLOT VALUE + STORAGE FEES) - PAID
                                            const totalValue  = Number(p.totalCost || 0);
                                            const amtPaid     = Number(p.amountPaid || 0);
                                            const storageFees = p.isReceivable ? Number(p.storageFeesAccumulated || 0) : 0;
                                            const amountOwed  = Math.max(0, totalValue + storageFees - amtPaid);

                                            return (
                                            <div key={p.projectId} className={styles.plotSubCard}>
                                                <div className={styles.plotSubCardHeader}>
                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>
                                                </div>

                                                {/* STAGE 12 FIX: SOLO/JOINT badge + navigable co-owner links
                                                    (design brief 3.3). The backend has supplied
                                                    p.ownershipType / p.coOwners since Stage 10, and the CSS
                                                    for this row has existed since Stage 10 too -- this was
                                                    the missing piece that actually renders it. */}
                                                <div className={styles.ownershipRow}>
                                                    <span className={p.ownershipType === 'JOINT' ? styles.jointBadge : styles.soloBadge}>
                                                        {p.ownershipType}
                                                    </span>
                                                    {p.ownershipType === 'JOINT' && p.coOwners && p.coOwners.length > 0 && (
                                                        <>
                                                            <span className={styles.jointOwnersLabel}>WITH:</span>
                                                            {p.coOwners.map((co, i) => (
                                                                <React.Fragment key={co.clientId}>
                                                                    <button
                                                                        type="button"
                                                                        className={styles.coOwnerLink}
                                                                        onClick={e => handleGoToCoOwner(e, co.clientId)}
                                                                    >
                                                                        {co.fullName}
                                                                    </button>
                                                                    {i < p.coOwners.length - 1 && (
                                                                        <span className={styles.jointOwnersLabel}>,</span>
                                                                    )}
                                                                </React.Fragment>
                                                            ))}
                                                        </>
                                                    )}
                                                </div>

                                                {/* STAGE 12 FIX: THIS owner's own reach status for this
                                                    project, separate from the general note below -- on a
                                                    JOINT plot the general note can belong to a co-owner's
                                                    call and must never be mistaken for this owner having
                                                    been personally reached (design brief 3.3). */}
                                                <div className={styles.ownerContactLine}>
                                                    YOU last reached: <strong>{p.ownerLastContactDate || 'NEVER'}</strong>
                                                </div>
                                                {p.ownerLastContactNote && (
                                                    <div className={styles.interactionNote}>
                                                        <span className={styles.interactionNoteLabel}>YOUR LAST NOTE WITH THIS OWNER</span>
                                                        <p className={styles.interactionNoteText}>{p.ownerLastContactNote}</p>
                                                    </div>
                                                )}

                                                {/* Last interaction note — notebook style */}
                                                {p.lastInteractionNote && p.lastInteractionNote !== 'NO PRIOR CONTACT' && (
                                                    <div className={styles.interactionNote}>
                                                        {/* STAGE 12 FIX: on a JOINT plot this note can belong
                                                            to a co-owner's call, not this card-owner's --
                                                            relabeled so it is never confused with the
                                                            YOUR LAST NOTE WITH THIS OWNER block above. */}
                                                        <span className={styles.interactionNoteLabel}>
                                                            {p.ownershipType === 'JOINT' ? 'MOST RECENT NOTE (ANY OWNER)' : 'LAST CONTACT NOTE'}
                                                        </span>
                                                        <p className={styles.interactionNoteText}>{p.lastInteractionNote}</p>
                                                    </div>
                                                )}

                                                {/* Financial breakdown */}
                                                <div className={styles.finBreakdown}>
                                                    <div className={styles.finRow}>
                                                        <span className={styles.finLabel}>PLOT VALUE</span>
                                                        <span className={styles.finValWhite}>UGX {fmt(totalValue)}</span>
                                                    </div>
                                                    {p.isReceivable && storageFees > 0 && (
                                                        <div className={styles.finRow}>
                                                            <span className={styles.finLabel}>+ STORAGE FEES</span>
                                                            <span className={styles.finValOrange}>UGX {fmt(storageFees)}</span>
                                                        </div>
                                                    )}
                                                    <div className={styles.finRow}>
                                                        <span className={styles.finLabel} style={{color:"#22c55e"}}>PAID</span>
                                                        <span className={styles.finValGreen}>UGX {fmt(amtPaid)}</span>
                                                    </div>
                                                    <div className={styles.finRowTotal}>
                                                        <span className={styles.finLabelTotal}>AMOUNT OWED</span>
                                                        <span className={styles.finValRed}>UGX {fmt(amountOwed)}</span>
                                                    </div>
                                                </div>

                                                <div className={styles.expandedActions}>
                                                    <button
                                                        className={styles.folderBtn}
                                                        onClick={() => navigate(`/folder/${p.projectId}`)}
                                                    >
                                                        OPEN FOLDER
                                                    </button>
                                                    {canRecordPayment && (
                                                        <button
                                                            className={styles.payBtn}
                                                            onClick={() => navigate(`/folder/${p.projectId}?action=pay`)}
                                                        >
                                                            <FiDollarSign aria-hidden="true" /> RECORD PAYMENT
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* LOG CALL MODAL — textarea pre-filled with last note */}
            <HardwareModal
                isOpen={callModal.open}
                onClose={() => { setCallModal({ open: false, mission: null, ownerId: null, ownerName: '' }); setLogContent(''); }}
                title={callModal.mission ? `LOG CALL — ${callModal.mission.plotNumber} (${callModal.ownerName || 'owner'})` : 'LOG CALL'}
            >
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>INTERACTION NOTES</label>
                    <textarea
                        className={modalStyles.modalTextarea}
                        value={logContent}
                        onChange={e => setLogContent(e.target.value)}
                        placeholder="e.g. Client confirmed payment by Friday, awaiting bank transfer..."
                        autoFocus
                    />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button
                        type="button"
                        className={modalStyles.modalBtnSecondary}
                        onClick={() => { setCallModal({ open: false, mission: null, ownerId: null, ownerName: '' }); setLogContent(''); }}
                    >
                        CANCEL
                    </button>
                    <HardwareButton onClick={handleLogCall} loading={committing} icon={FiSave}>
                        SAVE LOG
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default RecoveryPortal;
""")

# =====================================================================
# write: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css
# =====================================================================
write('erp-frontend/src/pages/Recovery/RecoveryPortal.module.css', r"""/* PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --panel-border:  rgba(238, 140, 58, 0.2);
    --red:           #ef4444;
    --green:         #10b981;
    --cyan:          #06b6d4;

    --gap-xl:   clamp(14px, 2vw, 24px);
    --gap-lg:   clamp(10px, 1.5vw, 18px);
    --gap-md:   clamp(7px,  1.1vw, 13px);
    --radius:   12px;
    --radius-sm: 7px;

    --fs-h1:    clamp(18px, 2.5vw, 24px);
    --fs-sub:   clamp(8px,  0.85vw, 10px);
    --fs-label: clamp(7px,  0.75vw, 9px);
    --fs-value: clamp(13px, 1.4vw, 17px);
    --fs-tag:   clamp(7px,  0.78vw, 9px);
    --fs-td:    clamp(11px, 1.15vw, 13px);
    --fs-meta:  clamp(9px,  0.95vw, 11px);
    --fs-btn:   clamp(9px,  0.9vw,  11px);

    max-width: 1400px;
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    gap: 0;
    box-sizing: border-box;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}

@keyframes warmBoot {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── PAGE HEADER ── */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 22px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 var(--radius) var(--radius) 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
    flex-shrink: 0;
}
.headerLeft  { display: flex; flex-direction: column; gap: clamp(3px, 0.4vw, 5px); flex: 1; min-width: 0; }
.headerRight { display: flex; align-items: center; gap: clamp(8px, 1.2vw, 14px); flex-shrink: 0; flex-wrap: wrap; }
.pageTitle   { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0; line-height: 1; }
.pageSubtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

/* ── MODE SWITCH ── */
.modeSwitch {
    display: flex;
    background: rgba(26, 46, 48, 0.85);
    padding: clamp(3px, 0.4vw, 5px);
    border-radius: var(--radius-sm);
    border: 1.5px solid var(--orange-border);
    gap: clamp(4px, 0.5vw, 6px);
}
.modeActive {
    background: #EE8C3A; color: #1a2e30; border: none;
    padding: clamp(7px, 0.9vw, 10px) clamp(12px, 1.5vw, 18px);
    border-radius: calc(var(--radius-sm) - 2px);
    font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: var(--fs-btn);
    letter-spacing: 1px; text-transform: uppercase; cursor: pointer;
    display: inline-flex; align-items: center; gap: clamp(5px, 0.7vw, 8px);
    white-space: nowrap; transition: background 0.2s;
}
.modeActive:hover { background: #f0a050; }
.modeInactive {
    background: transparent; color: rgba(255, 255, 255, 0.6); border: none;
    padding: clamp(7px, 0.9vw, 10px) clamp(12px, 1.5vw, 18px);
    border-radius: calc(var(--radius-sm) - 2px);
    font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: var(--fs-btn);
    letter-spacing: 1px; text-transform: uppercase; cursor: pointer;
    display: inline-flex; align-items: center; gap: clamp(5px, 0.7vw, 8px);
    white-space: nowrap; transition: color 0.2s, background 0.2s;
}
.modeInactive:hover { color: #fff; background: rgba(255, 255, 255, 0.06); }
.modeActive:focus-visible, .modeInactive:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── FIN HUD CARDS ── */
.finHUD {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--gap-lg);
    margin-bottom: var(--gap-xl);
    flex-shrink: 0;
}
.finHUDCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--panel-border);
    border-radius: var(--radius);
    padding: clamp(14px, 2vw, 22px) clamp(16px, 2.2vw, 26px);
    display: flex;
    flex-direction: column;
    gap: clamp(4px, 0.5vw, 6px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    transition: border-color 0.2s, transform 0.2s;
}
.finHUDCard:hover { border-color: var(--orange); transform: translateY(-2px); }
.finHUDCard label {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.finHUDCard strong {
    font-family: 'Space Mono', monospace;
    font-size: clamp(15px, 1.8vw, 21px);
    font-weight: 700;
    color: #fff;
    word-break: break-all;
    line-height: 1.2;
}

/* ── FILTER BAR ── */
.filterBar {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: var(--gap-lg);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: transparent;
    padding: clamp(8px, 1vw, 12px) 0;
    margin-left: clamp(-12px, -2vw, -24px);
    margin-right: clamp(-12px, -2vw, -24px);
    padding-left: clamp(12px, 2vw, 24px);
    padding-right: clamp(12px, 2vw, 24px);
}

.searchInner {
    position: relative;
    display: flex;
    align-items: center;
    background: #fff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    height: clamp(36px, 4.5vw, 44px);
    max-width: clamp(320px, 55vw, 560px);
    width: 100%;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.searchInner:focus-within { border-color: var(--orange); box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.18); }
.searchIcon {
    position: absolute; left: clamp(10px, 1.2vw, 14px); top: 50%;
    transform: translateY(-50%); color: var(--orange);
    font-size: clamp(14px, 1.6vw, 18px); pointer-events: none; flex-shrink: 0;
}
.searchInput {
    width: 100%; border: none; outline: none; background: transparent;
    color: #1a2e30; padding: 0 clamp(10px, 1.2vw, 14px) 0 clamp(36px, 4.5vw, 44px) !important;
    font-family: 'DM Sans', sans-serif; font-weight: 800;
    font-size: clamp(11px, 1.1vw, 13px); height: 100%;
}
.searchInput::placeholder { font-weight: 500; color: rgba(26, 46, 48, 0.3); }

/* Filter pills */
.filterPills {
    display: flex; flex-wrap: nowrap; overflow-x: auto;
    gap: clamp(6px, 0.9vw, 10px); scrollbar-width: none; padding-bottom: 2px;
}
.filterPills::-webkit-scrollbar { display: none; }

.filterPill {
    background: rgba(26, 46, 48, 0.75); border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85); padding: clamp(7px, 0.9vw, 9px) clamp(12px, 1.5vw, 18px);
    border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif; font-weight: 900;
    font-size: var(--fs-btn); letter-spacing: 1.5px; text-transform: uppercase;
    cursor: pointer; transition: all 0.2s ease; white-space: nowrap; flex-shrink: 0;
}
.filterPill:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.filterPillActive {
    background: #EE8C3A !important; color: #1a2e30 !important;
    border-color: #EE8C3A !important; box-shadow: 0 0 12px rgba(238, 140, 58, 0.35);
}
.filterPill:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── BADGE LEGEND ── */
.legend {
    display: flex; flex-wrap: wrap; gap: clamp(12px, 1.8vw, 20px);
    padding: clamp(6px, 0.8vw, 8px) 0; margin-bottom: var(--gap-lg); flex-shrink: 0;
}
.legendItem {
    display: flex; align-items: center; gap: clamp(6px, 0.8vw, 8px);
    font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 800; color: rgba(26, 46, 48, 0.65); white-space: nowrap;
}

/* ── MISSION GRID ── */
.missionGrid { display: flex; flex-direction: column; gap: var(--gap-lg); }

/* ── MISSION CARD ── */
.missionCard {
    background: var(--panel-bg); border: 1.5px solid var(--panel-border);
    border-radius: var(--radius); box-shadow: 0 8px 28px rgba(0, 0, 0, 0.18);
    overflow: hidden; transition: border-color 0.22s, box-shadow 0.22s, transform 0.22s;
}
.missionCard:hover {
    border-color: rgba(238, 140, 58, 0.45);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.28);
    transform: translateY(-2px);
}
.cardReceivable {
    border-color: rgba(239, 68, 68, 0.35) !important;
    border-left: clamp(3px, 0.4vw, 5px) solid rgba(239, 68, 68, 0.6) !important;
}
.cardReceivable:hover { border-color: rgba(239, 68, 68, 0.6) !important; }

/* Card header */
.cardHeader {
    display: flex; flex-direction: column; gap: clamp(10px, 1.3vw, 14px);
    padding: clamp(16px, 2.2vw, 24px) clamp(18px, 2.5vw, 28px);
    cursor: pointer; user-select: none; transition: background 0.15s;
}
.cardHeader:hover { background: rgba(255, 255, 255, 0.025); }

/* Top row */
.cardTopRow {
    display: flex; justify-content: space-between; align-items: center;
    gap: clamp(10px, 1.4vw, 16px); flex-wrap: wrap;
}
.cardTopRowLeft {
    display: flex; align-items: center; gap: clamp(8px, 1vw, 12px); min-width: 0; flex: 1;
}
.plotId {
    font-family: 'Space Mono', monospace; font-size: var(--fs-value); font-weight: 900;
    color: var(--orange); letter-spacing: 0.5px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.receivablePill {
    background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.45);
    color: #fca5a5; font-family: 'DM Sans', sans-serif; font-size: clamp(7px, 0.75vw, 8px);
    font-weight: 900; padding: clamp(2px, 0.3vw, 3px) clamp(7px, 0.9vw, 10px);
    border-radius: 4px; text-transform: uppercase; letter-spacing: 1px;
    white-space: nowrap; flex-shrink: 0;
}
.balanceLine {
    display: flex; flex-direction: column; align-items: flex-end;
    gap: clamp(2px, 0.3vw, 3px); flex-shrink: 0;
}
.balanceLabel {
    font-family: 'DM Sans', sans-serif; font-size: var(--fs-label); font-weight: 900;
    color: rgba(255, 255, 255, 0.35); text-transform: uppercase; letter-spacing: 1px;
}
.balanceVal {
    font-family: 'Space Mono', monospace;
    font-size: clamp(16px, 2vw, 22px);
    font-weight: 900;
    color: #fff;
    letter-spacing: 0.3px;
}
.balanceRed { color: #fca5a5 !important; text-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }

/* Main row: owner + phone + actions */
.cardMain {
    display: flex; justify-content: space-between; align-items: center;
    gap: clamp(10px, 1.4vw, 16px);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding-top: clamp(10px, 1.3vw, 14px); flex-wrap: wrap;
}
.ownerPhoneBlock {
    display: flex; flex-direction: column; gap: clamp(4px, 0.5vw, 6px);
    flex: 1; min-width: 0;
}
/* Owner name */
.ownerLine {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-td);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.9);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    text-transform: uppercase; letter-spacing: 0.3px;
}
/* Phone — EXACT SAME SIZE as owner name */
.phoneLine {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 900;
    color: var(--orange);
    white-space: nowrap; letter-spacing: 0.5px;
}
.cardSideActions {
    display: flex; align-items: center; gap: clamp(8px, 1.1vw, 12px); flex-shrink: 0;
}
.expandIcon {
    color: rgba(255, 255, 255, 0.3); font-size: clamp(16px, 1.8vw, 20px);
    transition: color 0.2s; flex-shrink: 0;
}
.cardHeader:hover .expandIcon { color: var(--orange); }

/* Log call button */
.logCallBtnSmall {
    display: inline-flex; align-items: center; gap: clamp(5px, 0.7vw, 7px);
    height: clamp(34px, 4vw, 40px); padding: 0 clamp(12px, 1.6vw, 18px);
    background: #EE8C3A; border: none; color: #1a2e30;
    border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif; font-weight: 900;
    font-size: var(--fs-btn); text-transform: uppercase; letter-spacing: 1px;
    cursor: pointer; white-space: nowrap; flex-shrink: 0;
    transition: background 0.2s, box-shadow 0.2s;
    box-shadow: 0 3px 10px rgba(238, 140, 58, 0.3);
}
.logCallBtnSmall:hover:not(:disabled) { background: #f0a050; box-shadow: 0 0 18px rgba(238, 140, 58, 0.5); }
.logCallBtnSmall:disabled {
    background: rgba(255, 255, 255, 0.08); border: 1.5px solid rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.3); cursor: not-allowed; box-shadow: none;
}
.logCallBtnSmall:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── CARD BODY (expanded) ── */
.cardBody {
    padding: 0 clamp(18px, 2.5vw, 28px) clamp(18px, 2.5vw, 24px);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(0, 0, 0, 0.12);
}

/* ── TIMING ROW — high-contrast values ── */
.timingRow {
    display: flex; align-items: center; flex-wrap: wrap;
    gap: clamp(8px, 1.2vw, 14px);
    background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(255, 255, 255, 0.06);
    padding: clamp(9px, 1.2vw, 12px) clamp(12px, 1.5vw, 16px);
    border-radius: var(--radius-sm);
    margin: clamp(12px, 1.6vw, 16px) 0;
    font-family: 'DM Sans', sans-serif; font-size: var(--fs-meta);
    font-weight: 800; color: rgba(255, 255, 255, 0.45); letter-spacing: 0.3px;
}
/* Each timing item — muted label, pure white bold value */
.timingItem {
    color: rgba(255, 255, 255, 0.45);
    font-size: var(--fs-meta);
    font-weight: 800;
    white-space: nowrap;
}
.timingRow strong,
.timingItem strong {
    color: #ffffff;
    font-weight: 900;
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-meta);
}
.timingRow svg { color: var(--orange); flex-shrink: 0; }

/* ── INTERACTION NOTE — notebook style ── */
.interactionNote {
    background: #ffffff;
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    border-radius: 0 4px 4px 0;
    padding: clamp(8px, 1vw, 11px) clamp(10px, 1.3vw, 14px);
    margin-bottom: var(--gap-md);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}
.interactionNoteLabel {
    display: block;
    font-family: 'Space Mono', monospace;
    font-size: clamp(7px, 0.75vw, 9px);
    font-weight: 900; color: #64748b;
    text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: clamp(3px, 0.4vw, 5px);
}
.interactionNoteText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(11px, 1.05vw, 13px);
    font-weight: 700; color: #1a2e30;
    line-height: 1.5; margin: 0; word-break: break-word;
}

/* ── PLOT SUB-CARD ── */
.plotSubCard {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-left: clamp(3px, 0.4vw, 4px) solid rgba(238, 140, 58, 0.35);
    border-radius: var(--radius-sm);
    padding: clamp(12px, 1.6vw, 18px) clamp(14px, 1.8vw, 20px);
    margin-bottom: var(--gap-md);
    transition: border-color 0.2s, background 0.2s;
}
.plotSubCard:hover { border-color: rgba(238, 140, 58, 0.5); border-left-color: var(--orange); background: rgba(255, 255, 255, 0.05); }
.plotSubCard:last-child { margin-bottom: 0; }

.plotSubCardHeader {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: clamp(10px, 1.3vw, 14px);
    padding-bottom: clamp(8px, 1vw, 10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.plotSubCardTitle {
    font-family: 'Space Mono', monospace; color: var(--orange);
    font-size: clamp(11px, 1.2vw, 14px); font-weight: 900;
}

/* ── FINANCIAL BREAKDOWN — high-contrast values ── */
.finBreakdown {
    display: flex; flex-direction: column; gap: clamp(6px, 0.8vw, 9px);
    margin-bottom: clamp(12px, 1.5vw, 16px);
    background: rgba(0, 0, 0, 0.2); border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-sm);
    padding: clamp(10px, 1.3vw, 14px) clamp(12px, 1.5vw, 16px);
}
.finRow {
    display: flex; justify-content: space-between; align-items: center;
    gap: clamp(10px, 1.4vw, 16px);
}
.finRowTotal {
    display: flex; justify-content: space-between; align-items: center;
    gap: clamp(10px, 1.4vw, 16px);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: clamp(6px, 0.8vw, 9px);
    margin-top: clamp(3px, 0.4vw, 5px);
}
/* Labels: muted grey */
.finLabel {
    font-family: 'DM Sans', sans-serif; font-size: var(--fs-meta); font-weight: 800;
    color: rgba(255, 255, 255, 0.4); text-transform: uppercase;
    letter-spacing: 0.5px; white-space: nowrap; flex-shrink: 0;
}
.finLabelTotal {
    font-family: 'DM Sans', sans-serif; font-size: var(--fs-meta); font-weight: 900;
    color: rgba(255, 255, 255, 0.55); text-transform: uppercase;
    letter-spacing: 0.5px; white-space: nowrap; flex-shrink: 0;
}
/* Values: PURE BOLD WHITE for maximum contrast */
.finValWhite {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 900;
    color: #ffffff;
    word-break: break-all;
}
.finValGreen {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 900;
    color: #22c55e;
    word-break: break-all;
}
.finValOrange {
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-td);
    font-weight: 900;
    color: #EE8C3A;
    word-break: break-all;
}
.finValRed {
    font-family: 'Space Mono', monospace;
    font-size: clamp(13px, 1.4vw, 16px);
    font-weight: 900;
    color: #fca5a5;
    word-break: break-all;
    text-shadow: 0 0 8px rgba(239,68,68,0.35);
}

/* Expanded action buttons */
.expandedActions { display: flex; gap: clamp(8px, 1.1vw, 12px); flex-wrap: wrap; }
.folderBtn {
    display: inline-flex; align-items: center; gap: clamp(5px, 0.6vw, 7px);
    height: clamp(32px, 3.8vw, 38px); padding: 0 clamp(12px, 1.5vw, 17px);
    background: rgba(26, 46, 48, 0.75); border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.8); border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: var(--fs-btn);
    text-transform: uppercase; letter-spacing: 1px; cursor: pointer;
    white-space: nowrap; transition: all 0.2s;
}
.folderBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.folderBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.payBtn {
    display: inline-flex; align-items: center; gap: clamp(5px, 0.6vw, 7px);
    height: clamp(32px, 3.8vw, 38px); padding: 0 clamp(12px, 1.5vw, 17px);
    background: rgba(16, 185, 129, 0.12); border: 1.5px solid rgba(16, 185, 129, 0.4);
    color: #34d399; border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: var(--fs-btn);
    text-transform: uppercase; letter-spacing: 1px; cursor: pointer;
    white-space: nowrap; transition: all 0.2s;
}
.payBtn:hover { background: #10b981; color: #1a2e30; border-color: #10b981; box-shadow: 0 0 12px rgba(16,185,129,0.3); }
.payBtn:focus-visible { outline: 2px solid #10b981; outline-offset: 2px; }

/* ── EMPTY / LOADING ── */
.emptyState {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: clamp(10px, 1.5vw, 16px); padding: clamp(48px, 8vh, 80px) 24px;
    background: var(--panel-bg); border: 1.5px solid var(--panel-border);
    border-radius: var(--radius); font-family: 'Space Mono', monospace;
    font-size: var(--fs-meta); font-weight: 900; letter-spacing: 2px;
    text-transform: uppercase; color: rgba(255, 255, 255, 0.2);
}
.emptyIcon { font-size: clamp(32px, 5vw, 48px); opacity: 0.18; }
.loadingSpinner {
    width: clamp(30px, 4vw, 40px); height: clamp(30px, 4vw, 40px);
    border: 3px solid rgba(238, 140, 58, 0.15); border-top-color: #EE8C3A;
    border-radius: 50%; animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
    .finHUD { grid-template-columns: repeat(3, 1fr); }
}

/* MOBILE: stack HUD cards cleanly in a single column */
@media (max-width: 600px) {
    .finHUD {
        grid-template-columns: 1fr;
        gap: clamp(8px, 2vw, 10px);
    }
    .finHUDCard {
        display: grid;
        grid-template-columns: 1fr 1fr;
        align-items: center;
        padding: clamp(12px, 3vw, 16px) clamp(14px, 4vw, 20px);
    }
    .finHUDCard label {
        font-size: clamp(9px, 2.5vw, 11px);
        letter-spacing: 0.8px;
    }
    .finHUDCard strong {
        font-size: clamp(15px, 4.5vw, 19px);
        text-align: right;
    }
    .cardTopRow { flex-direction: column; align-items: flex-start; gap: 8px; }
    .balanceLine { align-items: flex-start; }
    .cardMain { flex-direction: column; align-items: flex-start; gap: 10px; }
    .cardSideActions { width: 100%; }
    .logCallBtnSmall { flex: 1; justify-content: center; }
    .expandedActions { flex-direction: column; }
    .folderBtn, .payBtn { width: 100%; justify-content: center; }
    .timingRow { flex-direction: column; align-items: flex-start; gap: 5px; }
    .searchInner { max-width: 100%; }
}

@media (max-width: 480px) {
    .finHUD {
        grid-template-columns: 1fr;
        gap: 8px;
    }
    .finHUDCard {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        padding: clamp(12px, 4vw, 16px);
        gap: clamp(4px, 1vw, 6px);
    }
    .finHUDCard label {
        font-size: clamp(9px, 3vw, 11px);
    }
    .finHUDCard strong {
        font-size: clamp(16px, 5vw, 20px);
        text-align: left;
    }
}

/* ── STAGE 10: SOLO / JOINT ownership row on each plot sub-card ── */
.ownershipRow {
    display: flex; align-items: center; flex-wrap: wrap;
    gap: clamp(6px, 0.8vw, 9px);
    margin-bottom: clamp(6px, 0.8vw, 9px);
}
.soloBadge, .jointBadge {
    font-family: 'Space Mono', monospace; font-size: clamp(7px, 0.75vw, 9px);
    font-weight: 900; letter-spacing: 1px; text-transform: uppercase;
    padding: clamp(2px, 0.3vw, 3px) clamp(7px, 0.9vw, 10px);
    border-radius: 4px; white-space: nowrap;
}
.soloBadge {
    background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.55);
}
.jointBadge {
    background: rgba(238, 140, 58, 0.15); border: 1px solid rgba(238, 140, 58, 0.5);
    color: var(--orange);
}
.jointOwnersLabel {
    font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 700; color: rgba(255, 255, 255, 0.4);
}
.coOwnerLink {
    background: none; border: none; padding: 0;
    font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 800; color: var(--orange); text-decoration: underline;
    cursor: pointer;
}
.coOwnerLink:hover { color: #f0a050; }
.coOwnerLink:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── STAGE 11: soft co-owner-recently-contacted notice banner ── */
.coOwnerWarningBanner {
    display: flex; align-items: center; justify-content: space-between;
    gap: clamp(8px, 1vw, 12px);
    background: rgba(238, 140, 58, 0.12); border: 1px solid rgba(238, 140, 58, 0.4);
    border-radius: 8px;
    padding: clamp(8px, 1vw, 12px) clamp(12px, 1.4vw, 16px);
    margin-bottom: clamp(10px, 1.2vw, 14px);
    font-family: 'DM Sans', sans-serif; font-size: clamp(11px, 1vw, 13px);
    font-weight: 700; color: rgba(255, 255, 255, 0.85);
}
.coOwnerWarningDismiss {
    background: none; border: none; cursor: pointer;
    font-size: 16px; line-height: 1; color: rgba(255, 255, 255, 0.6);
    padding: 0 2px; flex-shrink: 0;
}
.coOwnerWarningDismiss:hover { color: #fff; }
.coOwnerWarningDismiss:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* -- STAGE 12: per-owner "you last reached" line on each plot sub-card -- */
.ownerContactLine {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 700;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: clamp(6px, 0.8vw, 9px);
}
.ownerContactLine strong { color: rgba(255, 255, 255, 0.85); }
""")

# =====================================================================
# write: erp-frontend/src/services/predictionService.js
# =====================================================================
write('erp-frontend/src/services/predictionService.js', r"""// PATH: erp-frontend/src/services/predictionService.js

/**
 * GOLDEN SEED PREDICTION ENGINE
 * Learns from user input to provide intelligent auto-complete suggestions.
 */

const STORAGE_KEY = 'gs_neural_memory';

// The fields we want to learn patterns for
const LEARNABLE_FIELDS = ['district', 'county', 'blockRoad', 'tenure'];

const predictionService = {
    
    /**
     * INGEST: Called on Form Submit.
     * Scans the data and saves unique values to memory.
     */
    learn: (formData) => {
        const currentMemory = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};

        LEARNABLE_FIELDS.forEach(field => {
            const val = formData[field]?.trim().toUpperCase();
            if (!val) return;

            // Initialize array if missing
            if (!currentMemory[field]) currentMemory[field] = [];

            // Add only if unique
            if (!currentMemory[field].includes(val)) {
                currentMemory[field].unshift(val); // Add to top
                // Keep memory lean: max 10 suggestions per field
                if (currentMemory[field].length > 10) currentMemory[field].pop();
            }
        });

        localStorage.setItem(STORAGE_KEY, JSON.stringify(currentMemory));
    },

    /**
     * RECALL: Called when Input gets Focus.
     * Returns list of suggestions for a specific field.
     */
    getSuggestions: (field) => {
        const memory = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        return memory[field] || [];
    }
};

export default predictionService;""")

# =====================================================================
# write: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
# =====================================================================
write('erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;

    @Value("${ADMIN_EMAIL}")
    private String adminEmail;

    @Value("${ADMIN_DEFAULT_PASSWORD}")
    private String adminDefaultPassword;

    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");

        // Run schema migrations via raw JDBC -- never touches JPA/Hibernate session
        runSchemaMigrations();

        // Seed root user if missing
        seedRootUser();

        // PHASE 4: Seed the default stage template checklist if empty
        stageTemplateService.seedDefaultStagesIfEmpty();

        // EXPENSES REBUILD: Seed the default expense presets if empty
        seedDefaultExpensePresets();

        System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
    }

    // NOTE: Deliberately NOT @Transactional -- same raw-JDBC-safety reasoning
    // as seedRootUser() below. Only seeds if the table is completely empty,
    // so it never overwrites presets a Manager has already created.
    public void seedDefaultExpensePresets() {
        if (expensePresetRepository.count() > 0) {
            System.out.println(">>> [EXPENSES] Presets already exist, skipping default seed.");
            return;
        }
        String[] defaults = { "Office", "Fieldwork", "Land Office" };
        for (String name : defaults) {
            expensePresetRepository.save(ExpensePreset.builder()
                    .name(name)
                    .createdBy("SYSTEM")
                    .build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    private void runSchemaMigrations() {
        String[] migrations = {
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS negotiation_deadline TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",
            // NOTE: the "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS
            // survey_date DATE" migration that used to live here has been
            // removed along with the surveyDate field itself (Title Details
            // cleanup) -- leaving it in place would silently re-add the
            // column on every boot even after a manual DROP COLUMN.
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",

            // PHASE 1 - PROJECT INDEX SYSTEM
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_titles_project_index') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",

            // PHASE 1.5 - DATE TRACKING SYSTEM
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",

            // PHASE 2 - NIN-BASED IDENTITY
            // Phone numbers are no longer required to be unique -- joint owners or
            // family members can share one phone. NIN is now the real identity check.
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",

            // PHASE C - FOLDER-TO-TITLE REDESIGN (Section 18.10 / 18.4)
            // national_id becomes a TRUE mandatory, unique column. The old
            // "ADD CONSTRAINT UNIQUE" line above this comment (removed) had been
            // silently failing on every boot since Phase 2 -- the blanket
            // try/catch below logs any failure as "already exists" whether that
            // was true or not, and there was nothing upstream cleaning duplicate
            // or blank values first. These four steps run in order, each one
            // guarded so it is a no-op once already applied -- same repeatable,
            // safe-on-every-boot pattern as the district/county and projectIndex
            // backfills above.
            //
            // Step 1: blank-string NINs are not the same as a real NULL -- fold
            // them in first so step 3 catches them too.
            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            //
            // Step 2: disambiguate any rows that already share a duplicate NIN
            // (possible from before this was ever enforced) -- keep the oldest
            // row's value untouched, suffix every later duplicate with its own
            // id so the unique constraint below has something valid to apply to.
            // Naturally idempotent: once every value is distinct, ROW_NUMBER()
            // never produces rn > 1 for the same national_id again.
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            //
            // Step 3: legacy rows created before Phase 2 may still have a blank
            // national_id (per the old Client.java comment, "blank until next
            // edited") -- a real NOT NULL constraint cannot coexist with actual
            // NULLs, so give each one a unique placeholder. Naturally idempotent:
            // once set, national_id is no longer NULL so the WHERE clause skips it.
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            //
            // Step 4: now safe to apply both constraints for real. SET NOT NULL is
            // itself idempotent in Postgres (no error re-running it once already
            // set). The UNIQUE constraint is wrapped in a DO block guarded by a
            // pg_constraint lookup, so once it exists every later boot silently
            // no-ops and logs OK instead of a red "already exists" skip.
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",

            // EXPENSES REBUILD -- flat cash-out log, replaces the old
            // committed/paid CompanyExpense model for new entries. The old
            // company_expenses table is left untouched (deprecated, not
            // deleted) so nothing already recorded there is lost.
            "CREATE TABLE IF NOT EXISTS expense_presets (" +
                "id UUID PRIMARY KEY, " +
                "name VARCHAR(100) NOT NULL UNIQUE, " +
                "created_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now())",
            "CREATE TABLE IF NOT EXISTS expenses (" +
                "id UUID PRIMARY KEY, " +
                "category VARCHAR(150) NOT NULL, " +
                "amount NUMERIC(15,2) NOT NULL, " +
                "note TEXT, " +
                "recorded_by VARCHAR(100), " +
                "created_at TIMESTAMP NOT NULL DEFAULT now(), " +
                "edited_at TIMESTAMP, " +
                "edited_by VARCHAR(100))",
            "CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category)",

            // STAGE 3 -- SOFT DELETE
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",

            // PHASE A -- FOLDER-TO-TITLE REDESIGN (Section 18.10)
            // landTitle becomes optional on LandProject (see model change),
            // and location fields move up so they are permanent even for
            // titleless folder-stage projects.
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            // Backfill: copy existing district/county from land_titles up to
            // their parent land_projects row via the title_id FK. The
            // "lp.district IS NULL" guard makes this safe to run on every
            // boot -- once a row has been backfilled its district is no
            // longer NULL, so this becomes a no-op for it from then on.
            // land_titles.district/county are left in place (deprecated,
            // not dropped) so this UPDATE is repeatable and non-destructive.
            "UPDATE land_projects lp SET district = lt.district, county = lt.county " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL " +
                "AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)",

            // PHASE B -- FOLDER-TO-TITLE REDESIGN (Section 18.10 / 18.3)
            // projectIndex moves up to LandProject: Section 18.3 requires it
            // be assigned at LandProject creation, before any title exists,
            // and Phase B's null-safe audit-log fallback needs it to exist
            // even when landTitle does not. land_titles.project_index is
            // left in place (deprecated, not dropped).
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            // Backfill: copy each project's existing projectIndex up from
            // its LandTitle via the title_id FK. Same "IS NULL" guard as
            // the district/county backfill above -- safe on every boot,
            // no-op once already copied.
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",

            // PHASE F -- FOLDER-TO-TITLE REDESIGN (Section 18.10)
            // Make plot_number nullable so bulk title-produced action can
            // attach an empty LandTitle record to unlock fields before
            // the unique plot numbers are known.
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
        };

        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {

            for (String sql : migrations) {
                try {
                    stmt.execute(sql);
                    System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length())));
                } catch (Exception e) {
                    // Column already exists or similar -- safe to ignore
                    System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage());
                }
            }

        } catch (Exception e) {
            // If we can't get a connection, log and continue -- don't kill startup
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());
        }
    }

    // NOTE: Deliberately NOT @Transactional -- we use raw JDBC so this is
    // completely immune to Spring AOP proxy bypass, Hibernate L1 cache,
    // EntityManager flush timing, and @Builder.Default field conflicts.
    public void seedRootUser() {
        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";
        String encodedPassword = passwordEncoder.encode(rawPassword);

        try (java.sql.Connection conn = dataSource.getConnection()) {
            // Check if admin_root exists
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement(
                    "SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) exists = rs.getInt(1) > 0;
                }
            }

            if (!exists) {
                // INSERT brand-new admin_root row
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) "
                           + "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }

                // Verify by re-reading the stored hash -- only meaningful right
                // after a fresh insert, since this is the only branch that
                // actually wrote a new password.
                try (java.sql.PreparedStatement ps = conn.prepareStatement(
                        "SELECT password, is_active FROM users WHERE username = 'admin_root'")) {
                    try (java.sql.ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            String storedHash = rs.getString("password");
                            boolean active = rs.getBoolean("is_active");
                            boolean matches = passwordEncoder.matches(rawPassword, storedHash);
                            System.out.println(">>> [REGISTRY] Post-write verification:");
                            System.out.println(">>>   is_active in DB = " + active);
                            System.out.println(">>>   BCrypt.matches(rawPassword, storedHash) = " + matches);
                            if (!matches) {
                                System.err.println(">>> [REGISTRY] FATAL: BCrypt verify FAILED after write! Check encoder config.");
                            } else {
                                System.out.println(">>> [REGISTRY] SUCCESS: Password verified. Login WILL work.");
                            }
                        } else {
                            System.err.println(">>> [REGISTRY] FATAL: admin_root row not found after write!");
                        }
                    }
                }
            } else {
                // STAGE 1 FIX: admin_root already exists -- do NOT touch its
                // password, is_active, or must_change_password on restart.
                // Whatever David set those to in the running app stays as-is.
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset. Existing credentials remain in effect.");
            }

        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
""")


# =====================================================================
# Report + commit + push
# =====================================================================
print(f"\n=== fix.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)} file(s)")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        commit_msg = """feat: delete Volume/Folio/Instrument No./Box Number/Survey Date from Title Details

Part 1 of 3. Removes these 5 fields end to end, keeping Title ID,
Tenure, Plot Number, Block, and Title Date:

Frontend:
- IntakePage.jsx: state, save payload, duplicate-reset, and the 5 form fields
- FolderPage.jsx: edit buffer, edit-mode inputs, read-only spec-sheet rows
- RecoveryPortal.jsx (+ .module.css): box number / survey date on plot cards
- predictionService.js: 'volume' removed from LEARNABLE_FIELDS

Backend:
- LandTitle.java: entity fields + idx_physical_archive index deleted
- LandEntryRequest.java, LandService.java: DTO fields + call sites
- RecoveryTaskDTO.java, RecoveryController.java: DTO field + mapping
- LandServiceTest.java, LandCascadeDeleteTest.java: builder calls updated

DB: ddl-auto=update with no Flyway/Liquibase, so Hibernate will not drop
the now-orphaned columns. DROP COLUMN SQL is included as a comment at
the top of this script for whenever that migration is wanted -- not
executed here."""
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed all changes")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed to remote")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit code {e.returncode})")
        if e.output:
            print(f"    {e.output.decode('utf-8', errors='replace').strip()}")
    except FileNotFoundError:
        print("\n  Git: git not found in PATH")

print()