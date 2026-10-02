// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StatusTemplateService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectStatus;
import com.gesolutions.erp.modules.land.model.ProjectType;
import com.gesolutions.erp.modules.land.model.StatusTemplate;
import com.gesolutions.erp.modules.land.dto.ProjectStatusRequest;
import com.gesolutions.erp.modules.land.repository.ProjectStatusRepository;
import com.gesolutions.erp.modules.land.repository.StatusTemplateRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * fix180: was StageTemplateService. Every project type has its own ordered status list (ProjectType). Adding a
 * status -- to a type's master list or to one project -- is for Admin, Manager and Director only, never Secretary.
 */
@Service
@RequiredArgsConstructor
public class StatusTemplateService {

    private final StatusTemplateRepository templateRepository;
    private final ProjectStatusRepository projectStatusRepository;
    private final AuditService auditService;
    private final com.gesolutions.erp.modules.land.repository.LandProjectRepository projectRepository;

    private String getCurrentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }

    // fix180: only these roles may create a status (Secretary is data entry only)
    public static boolean canAddStatuses() {
        Authentication a = SecurityContextHolder.getContext().getAuthentication();
        if (a == null) return true;   // boot / seed
        return a.getAuthorities().stream().anyMatch(g -> {
            String r = g.getAuthority();
            return "ROLE_ADMIN".equals(r) || "ROLE_MANAGER".equals(r) || "ROLE_DIRECTOR".equals(r);
        });
    }

    private static ProjectType requireType(String projectType) {
        ProjectType t = ProjectType.from(projectType);
        if (t == null) throw new BusinessException("PROJECT_TYPE_REQUIRED: Pick a valid project type.");
        return t;
    }

    // fix166: the status endpoints check the status belongs to the project in the web address, and the project is open.
    // fix180: a saved title no longer locks the list (every type has statuses now); only delete and hand-over do.
    public void requireStatusEditable(UUID projectId, UUID statusId) {
        ProjectStatus status = projectStatusRepository.findById(statusId)
                .orElseThrow(() -> new BusinessException("PROJECT_STATUS_NOT_FOUND"));
        if (status.getProjectId() == null || !status.getProjectId().equals(projectId)) {
            throw new BusinessException("STATUS_MISMATCH: That status does not belong to this project.");
        }
        requireProjectStatusesEditable(projectId);
    }

    public void requireProjectStatusesEditable(UUID projectId) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        if (project.isDeleted()) {
            throw new BusinessException("STATUS_LOCKED: This project is deleted. Restore it first.");
        }
        if (project.getLandTitle() != null && project.getLandTitle().isReleased()) {
            throw new BusinessException("STATUS_LOCKED: The title has been handed over, so its statuses are locked. A director must UNDO the hand-over first.");
        }
    }

    // fix167: RESTORE DEFAULTS in ONE step on the server: the project's statuses are replaced by its type's master list
    // (first status ticked). All or nothing, director only, audited with the old list.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<ProjectStatus> restoreProjectDefaults(UUID projectId) {
        requireProjectStatusesEditable(projectId);
        LandProject project = projectRepository.findById(projectId).orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        List<StatusTemplate> tpls = getActiveTemplate(ProjectType.of(project).name());
        if (tpls.isEmpty()) {
            throw new BusinessException("TEMPLATE_EMPTY: The master status list for this project type is empty, so nothing was changed.");
        }
        List<ProjectStatus> old = projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
        StringBuilder was = new StringBuilder();
        for (ProjectStatus st : old) {
            if (was.length() > 0) was.append(", ");
            was.append(st.getStatusName()).append(st.isCompleted() ? " (done)" : "");
        }
        projectStatusRepository.deleteAll(old);
        projectStatusRepository.flush();
        int order = 0;
        for (StatusTemplate t : tpls) {
            boolean first = order == 0;
            projectStatusRepository.save(ProjectStatus.builder()
                    .projectId(projectId).statusName(t.getStatusName())
                    .cost(t.getDefaultCost() != null ? t.getDefaultCost() : BigDecimal.ZERO)
                    .isCustom(false).isCompleted(first).completedAt(first ? LocalDateTime.now() : null)
                    .completedBy(first ? getCurrentOperator() : null)
                    .displayOrder(order++).build());
        }
        auditService.logAction("PROJECT_STATUSES_RESTORED",
            "Operator [" + getCurrentOperator() + "] restored the default statuses on project: " + projectId + ". Old list: " + was);
        return projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
    }

    /**
     * Boot-time (and after a wipe): the old global checklist (no project type) is switched off, and every project
     * type that has no active statuses gets its default list. Lists staff already changed are left alone.
     */
    @Transactional
    public void seedDefaultStatusesIfEmpty() {
        for (StatusTemplate t : templateRepository.findByProjectTypeIsNullAndIsActiveTrue()) {
            t.setActive(false);
            templateRepository.save(t);
        }
        for (ProjectType type : ProjectType.values()) {
            if (!templateRepository.findByProjectTypeAndIsActiveTrueOrderByDisplayOrderAsc(type.name()).isEmpty()) continue;
            int order = 1;
            for (String name : type.getDefaultStatuses()) {
                templateRepository.save(StatusTemplate.builder()
                        .statusName(name).projectType(type.name()).defaultCost(BigDecimal.ZERO)
                        .displayOrder(order++).isActive(true).build());
            }
            System.out.println(">>> [STATUS_TEMPLATE] Seeded " + type.getDefaultStatuses().size() + " default statuses for " + type.getLabel() + ".");
        }
    }

    /** The active master list of one project type (blank = every type's list). */
    @Transactional(readOnly = true)
    public List<StatusTemplate> getActiveTemplate(String projectType) {
        if (projectType == null || projectType.isBlank()) {
            return templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc().stream()
                    .filter(t -> t.getProjectType() != null).toList();
        }
        return templateRepository.findByProjectTypeAndIsActiveTrueOrderByDisplayOrderAsc(requireType(projectType).name());
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public StatusTemplate addTemplateStatus(String projectType, String statusName, BigDecimal defaultCost, Integer displayOrder) {
        ProjectType type = requireType(projectType);
        if (statusName == null || statusName.isBlank()) {
            throw new BusinessException("STATUS_NAME_REQUIRED: A status name is required.");
        }
        int next = templateRepository.findByProjectTypeAndIsActiveTrueOrderByDisplayOrderAsc(type.name()).size() + 1;
        StatusTemplate status = StatusTemplate.builder()
                .statusName(statusName.trim())
                .projectType(type.name())
                .defaultCost(defaultCost != null ? defaultCost : BigDecimal.ZERO)
                .displayOrder(displayOrder != null ? displayOrder : next)
                .isActive(true)
                .build();
        StatusTemplate saved = templateRepository.save(status);
        auditService.logAction("STATUS_TEMPLATE_ADDED",
            "Operator [" + getCurrentOperator() + "] added master status \"" + status.getStatusName() + "\" to " + type.getLabel());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public StatusTemplate updateTemplateStatus(UUID id, String statusName, BigDecimal defaultCost, Integer displayOrder) {
        StatusTemplate status = templateRepository.findById(id)
                .orElseThrow(() -> new BusinessException("STATUS_TEMPLATE_NOT_FOUND"));
        if (statusName != null && !statusName.isBlank()) status.setStatusName(statusName.trim());
        if (defaultCost != null) status.setDefaultCost(defaultCost);
        if (displayOrder != null) status.setDisplayOrder(displayOrder);
        StatusTemplate saved = templateRepository.save(status);
        auditService.logAction("STATUS_TEMPLATE_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated master status: " + status.getStatusName());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void deactivateTemplateStatus(UUID id) {
        StatusTemplate status = templateRepository.findById(id)
                .orElseThrow(() -> new BusinessException("STATUS_TEMPLATE_NOT_FOUND"));
        status.setActive(false);
        templateRepository.save(status);
        auditService.logAction("STATUS_TEMPLATE_REMOVED",
            "Operator [" + getCurrentOperator() + "] removed master status from the list: " + status.getStatusName());
    }

    @Transactional(readOnly = true)
    public List<ProjectStatus> getProjectStatuses(UUID projectId) {
        return projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
    }

    @Transactional
    public List<ProjectStatus> attachStatusesToProject(UUID projectId, List<ProjectStatusRequest> requests) {
        if (requests == null || requests.isEmpty()) return List.of();
        // fix180: a custom status is a NEW status -- Secretary cannot create one (the master list is picked as it is)
        if (!canAddStatuses() && requests.stream().anyMatch(ProjectStatusRequest::isCustom)) {
            throw new BusinessException("STATUS_ADD_DENIED: Only an Admin, Manager or Director can add a status.");
        }
        int startOrder = projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(projectId).size();
        java.util.List<ProjectStatus> created = new java.util.ArrayList<>();
        int i = 0;
        for (ProjectStatusRequest req : requests) {
            String name; BigDecimal cost;
            if (req.isCustom()) {
                if (req.getStatusName() == null || req.getStatusName().isBlank()) {
                    throw new BusinessException("STATUS_NAME_REQUIRED: Custom status needs a name.");
                }
                name = req.getStatusName().trim();
                cost = req.getCost() != null ? req.getCost() : BigDecimal.ZERO;
            } else {
                if (req.getStatusTemplateId() == null) throw new BusinessException("STATUS_TEMPLATE_ID_REQUIRED");
                StatusTemplate template = templateRepository.findById(UUID.fromString(req.getStatusTemplateId()))
                        .orElseThrow(() -> new BusinessException("STATUS_TEMPLATE_NOT_FOUND"));
                name = template.getStatusName();
                cost = req.getCost() != null ? req.getCost() : template.getDefaultCost();
            }
            // fix167: a status ticked on New Project arrives ticked, with when and by whom
            created.add(projectStatusRepository.save(ProjectStatus.builder()
                    .projectId(projectId).statusName(name).cost(cost).notes(req.getNotes())
                    .isCustom(req.isCustom()).isCompleted(req.isCompleted())
                    .completedAt(req.isCompleted() ? LocalDateTime.now() : null)
                    .completedBy(req.isCompleted() ? getCurrentOperator() : null)
                    .displayOrder(startOrder + (i++))
                    .build()));
        }
        auditService.logAction("PROJECT_STATUSES_ATTACHED",
            "Operator [" + getCurrentOperator() + "] attached " + created.size()
            + " status(es) to project: " + projectId);
        return created;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<ProjectStatus> reorderProjectStatuses(UUID projectId, List<UUID> orderedIds) {
        List<ProjectStatus> statuses = projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
        if (orderedIds == null || orderedIds.isEmpty()) return statuses;
        java.util.Map<UUID, ProjectStatus> byId = new java.util.LinkedHashMap<>();
        for (ProjectStatus st : statuses) byId.put(st.getId(), st);
        List<ProjectStatus> toSave = new java.util.ArrayList<>();
        int order = 0;
        for (UUID id : orderedIds) {
            ProjectStatus st = byId.remove(id);
            if (st != null) { st.setDisplayOrder(order++); toSave.add(st); }
        }
        for (ProjectStatus st : byId.values()) { st.setDisplayOrder(order++); toSave.add(st); }
        projectStatusRepository.saveAll(toSave);
        auditService.logAction("PROJECT_STATUSES_REORDERED",
            "Operator [" + getCurrentOperator() + "] reordered statuses on project: " + projectId);
        return projectStatusRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStatus toggleStatusCompletion(UUID statusId, boolean completed) {
        ProjectStatus status = projectStatusRepository.findById(statusId)
                .orElseThrow(() -> new BusinessException("PROJECT_STATUS_NOT_FOUND"));
        status.setCompleted(completed);
        status.setCompletedAt(completed ? LocalDateTime.now() : null);
        status.setCompletedBy(completed ? getCurrentOperator() : null);
        ProjectStatus saved = projectStatusRepository.save(status);
        auditService.logAction("PROJECT_STATUS_CHANGED",
            "Operator [" + getCurrentOperator() + "] marked status \"" + status.getStatusName()
            + "\" as " + (completed ? "COMPLETE" : "NOT COMPLETE") + " on project: " + status.getProjectId());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ProjectStatus updateStatusCostAndNotes(UUID statusId, BigDecimal cost, String notes) {
        ProjectStatus status = projectStatusRepository.findById(statusId)
                .orElseThrow(() -> new BusinessException("PROJECT_STATUS_NOT_FOUND"));
        if (cost != null) status.setCost(cost);
        if (notes != null) status.setNotes(notes);
        ProjectStatus saved = projectStatusRepository.save(status);
        auditService.logAction("PROJECT_STATUS_COST_UPDATED",
            "Operator [" + getCurrentOperator() + "] updated cost/notes on status \"" + status.getStatusName()
            + "\" for project: " + status.getProjectId());
        return saved;
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void removeProjectStatus(UUID statusId) {
        ProjectStatus status = projectStatusRepository.findById(statusId)
                .orElseThrow(() -> new BusinessException("PROJECT_STATUS_NOT_FOUND"));
        projectStatusRepository.delete(status);
        auditService.logAction("PROJECT_STATUS_REMOVED",
            "Operator [" + getCurrentOperator() + "] removed status \"" + status.getStatusName()
            + "\" from project: " + status.getProjectId());
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StatusTemplate> reorderTemplateStatuses(List<UUID> orderedIds) {
        if (orderedIds == null || orderedIds.isEmpty()) return List.of();
        List<StatusTemplate> found = templateRepository.findAllById(orderedIds);
        java.util.Map<UUID, StatusTemplate> byId = found.stream()
                .collect(java.util.stream.Collectors.toMap(StatusTemplate::getId, s -> s));
        List<StatusTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (UUID id : orderedIds) {
            StatusTemplate status = byId.get(id);
            if (status == null) continue;
            status.setDisplayOrder(order++);
            toSave.add(status);
        }
        return templateRepository.saveAll(toSave);
    }

    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void bulkDeleteTemplateStatuses(List<UUID> ids) {
        if (ids == null || ids.isEmpty()) return;
        List<StatusTemplate> toDelete = templateRepository.findAllById(ids);
        if (!toDelete.isEmpty()) templateRepository.deleteAllInBatch(toDelete);
    }

    /** One project type's master list goes back to the fixed default list (custom statuses on that type are switched off). */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StatusTemplate> restoreDefaultStatuses(String projectType) {
        ProjectType type = requireType(projectType);
        List<StatusTemplate> current = templateRepository.findByProjectTypeAndIsActiveTrueOrderByDisplayOrderAsc(type.name());
        java.util.Map<String, StatusTemplate> keepByName = new java.util.HashMap<>();
        for (StatusTemplate t : current) {
            if (type.getDefaultStatuses().contains(t.getStatusName()) && !keepByName.containsKey(t.getStatusName())) {
                keepByName.put(t.getStatusName(), t);
            } else {
                t.setActive(false);
                templateRepository.save(t);
            }
        }
        List<StatusTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (String name : type.getDefaultStatuses()) {
            StatusTemplate status = keepByName.get(name);
            if (status == null) {
                status = StatusTemplate.builder().statusName(name).projectType(type.name()).defaultCost(BigDecimal.ZERO)
                        .displayOrder(order).isActive(true).build();
            } else {
                status.setDisplayOrder(order);
            }
            order++;
            toSave.add(status);
        }
        auditService.logAction("STATUS_TEMPLATE_RESTORED",
            "Operator [" + getCurrentOperator() + "] restored the default status list of " + type.getLabel());
        return templateRepository.saveAll(toSave);
    }
}
