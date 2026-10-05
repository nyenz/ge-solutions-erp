// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StatusTemplateController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.ProjectStatus;
import com.gesolutions.erp.modules.land.model.StatusTemplate;
import com.gesolutions.erp.modules.land.dto.ProjectStatusRequest;
import com.gesolutions.erp.modules.land.service.StatusTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * fix180: was StageTemplateController (/stage-templates, /land/projects/{id}/stages). Adding statuses -- to a
 * project type's master list or to one project -- is Admin / Manager / Director only (class level). Secretary can
 * read the lists (New Project needs them) and tick statuses.
 */
@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class StatusTemplateController {

    private final StatusTemplateService statusTemplateService;

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR', 'ROLE_EMPLOYEE')")
    @GetMapping("/status-templates")
    public ResponseEntity<?> getTemplate(@RequestParam(required = false) String projectType) {
        List<StatusTemplate> list = statusTemplateService.getActiveTemplate(projectType);
        // fix181 (8.8): the Employee gets the status names only, never the default costs
        var a = org.springframework.security.core.context.SecurityContextHolder.getContext().getAuthentication();
        boolean employee = a != null && a.getAuthorities().stream().anyMatch(g -> "ROLE_EMPLOYEE".equals(g.getAuthority()));
        if (!employee) return ResponseEntity.ok(list);
        List<Map<String, Object>> out = new java.util.ArrayList<>();
        for (StatusTemplate t : list) {
            Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("id", t.getId()); m.put("statusName", t.getStatusName()); m.put("projectType", t.getProjectType());
            m.put("displayOrder", t.getDisplayOrder()); m.put("isActive", t.isActive());
            out.add(m);
        }
        return ResponseEntity.ok(out);
    }

    @PostMapping("/status-templates")
    public ResponseEntity<StatusTemplate> addTemplateStatus(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("statusName");
        String type = (String) body.get("projectType");
        BigDecimal cost = body.get("defaultCost") != null
                ? new BigDecimal(body.get("defaultCost").toString()) : BigDecimal.ZERO;
        Integer order = body.get("displayOrder") != null
                ? Integer.valueOf(body.get("displayOrder").toString()) : null;
        return ResponseEntity.ok(statusTemplateService.addTemplateStatus(type, name, cost, order));
    }

    @PutMapping("/status-templates/{id}")
    public ResponseEntity<StatusTemplate> updateTemplateStatus(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        String name = (String) body.get("statusName");
        BigDecimal cost = body.get("defaultCost") != null
                ? new BigDecimal(body.get("defaultCost").toString()) : null;
        Integer order = body.get("displayOrder") != null
                ? Integer.valueOf(body.get("displayOrder").toString()) : null;
        return ResponseEntity.ok(statusTemplateService.updateTemplateStatus(id, name, cost, order));
    }

    @DeleteMapping("/status-templates/{id}")
    public ResponseEntity<Void> deactivateTemplateStatus(@PathVariable UUID id) {
        statusTemplateService.deactivateTemplateStatus(id);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/status-templates/reorder")
    public ResponseEntity<List<StatusTemplate>> reorderTemplateStatuses(@RequestBody Map<String, List<String>> body) {
        List<UUID> orderedIds = (body.getOrDefault("orderedIds", List.of())).stream()
                .map(UUID::fromString).toList();
        return ResponseEntity.ok(statusTemplateService.reorderTemplateStatuses(orderedIds));
    }

    @DeleteMapping("/status-templates/bulk")
    public ResponseEntity<Void> bulkDeleteTemplateStatuses(@RequestBody Map<String, List<String>> body) {
        List<UUID> ids = (body.getOrDefault("ids", List.of())).stream()
                .map(UUID::fromString).toList();
        statusTemplateService.bulkDeleteTemplateStatuses(ids);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/status-templates/restore-defaults")
    public ResponseEntity<List<StatusTemplate>> restoreDefaultStatuses(@RequestParam String projectType) {
        return ResponseEntity.ok(statusTemplateService.restoreDefaultStatuses(projectType));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/land/projects/{projectId}/statuses")
    public ResponseEntity<List<ProjectStatus>> getProjectStatuses(@PathVariable UUID projectId) {
        return ResponseEntity.ok(statusTemplateService.getProjectStatuses(projectId));
    }

    @PostMapping("/land/projects/{projectId}/statuses")
    public ResponseEntity<List<ProjectStatus>> attachStatuses(
            @PathVariable UUID projectId, @RequestBody List<ProjectStatusRequest> requests) {
        statusTemplateService.requireProjectStatusesEditable(projectId); // fix167
        return ResponseEntity.ok(statusTemplateService.attachStatusesToProject(projectId, requests));
    }

    @PutMapping("/land/projects/{projectId}/statuses/reorder")
    public ResponseEntity<List<ProjectStatus>> reorderProjectStatuses(
            @PathVariable UUID projectId, @RequestBody List<String> orderedIds) {
        statusTemplateService.requireProjectStatusesEditable(projectId); // fix167
        List<UUID> ids = orderedIds.stream().map(UUID::fromString).toList();
        return ResponseEntity.ok(statusTemplateService.reorderProjectStatuses(projectId, ids));
    }

    // fix167: RESTORE DEFAULTS for one project, in one server step (director only)
    @PostMapping("/land/projects/{projectId}/statuses/restore-defaults")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<List<ProjectStatus>> restoreProjectDefaults(@PathVariable UUID projectId) {
        return ResponseEntity.ok(statusTemplateService.restoreProjectDefaults(projectId));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PatchMapping("/land/projects/{projectId}/statuses/{statusId}/complete")
    public ResponseEntity<ProjectStatus> toggleStatusCompletion(
            @PathVariable UUID projectId, @PathVariable UUID statusId,
            @RequestParam boolean completed) {
        statusTemplateService.requireStatusEditable(projectId, statusId);
        return ResponseEntity.ok(statusTemplateService.toggleStatusCompletion(statusId, completed));
    }

    @PatchMapping("/land/projects/{projectId}/statuses/{statusId}/cost")
    public ResponseEntity<ProjectStatus> updateStatusCost(
            @PathVariable UUID projectId, @PathVariable UUID statusId,
            @RequestBody Map<String, Object> body) {
        BigDecimal cost = body.get("cost") != null ? new BigDecimal(body.get("cost").toString()) : null;
        String notes = (String) body.get("notes");
        statusTemplateService.requireStatusEditable(projectId, statusId);
        return ResponseEntity.ok(statusTemplateService.updateStatusCostAndNotes(statusId, cost, notes));
    }

    // fix167: removing a status is director-only on the server too
    @DeleteMapping("/land/projects/{projectId}/statuses/{statusId}")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> removeStatus(@PathVariable UUID projectId, @PathVariable UUID statusId) {
        statusTemplateService.requireStatusEditable(projectId, statusId);
        statusTemplateService.removeProjectStatus(statusId);
        return ResponseEntity.noContent().build();
    }
}
