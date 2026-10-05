// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/WorkCountsService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectStatus;
import com.gesolutions.erp.modules.land.model.ProjectType;
import com.gesolutions.erp.modules.land.model.StatusTemplate;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.ProjectStatusRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * fix181 (8.4, 17.6, 20.3, 12.7): the live WORK COUNTS for Secretary and above -- plain numbers, no money.
 *  - pending: how many Pending projects, and the age in days of the oldest;
 *  - byType: per project type, how many projects stand at each CURRENT status (the status at currentStatusIndex;
 *    a custom name or an index past the list is counted as OTHER), plus PENDING and RECEIVABLES lines;
 *  - problems, receivables, releaseReady (LandProject.releaseBlocker() == null).
 * Deleted projects are never counted. Two reads: the projects, and every status of those projects at once.
 */
@Service
@RequiredArgsConstructor
public class WorkCountsService {

    private final LandProjectRepository projectRepository;
    private final ProjectStatusRepository statusRepository;
    private final StatusTemplateService statusTemplateService;

    @Transactional(readOnly = true)
    public Map<String, Object> counts() {
        List<LandProject> all = projectRepository.findAllIncludingPending();
        List<UUID> ids = new ArrayList<>();
        for (LandProject p : all) ids.add(p.getId());
        Map<UUID, List<ProjectStatus>> statuses = new HashMap<>();
        for (int i = 0; i < ids.size(); i += 500) {
            for (ProjectStatus s : statusRepository.findByProjectIdIn(ids.subList(i, Math.min(ids.size(), i + 500)))) {
                statuses.computeIfAbsent(s.getProjectId(), k -> new ArrayList<>()).add(s);
            }
        }
        Map<String, Set<String>> templateNames = new HashMap<>();
        for (ProjectType t : ProjectType.values()) {
            Set<String> names = new HashSet<>();
            for (StatusTemplate st : statusTemplateService.getActiveTemplate(t.name())) names.add(st.getStatusName());
            templateNames.put(t.name(), names);
        }

        long pending = 0, problems = 0, receivables = 0, releaseReady = 0;
        LocalDateTime oldest = null;
        Map<String, Map<String, Long>> byType = new LinkedHashMap<>();
        for (ProjectType t : ProjectType.values()) byType.put(t.name(), new LinkedHashMap<>());
        for (LandProject p : all) {
            String type = ProjectType.of(p).name();
            Map<String, Long> row = byType.computeIfAbsent(type, k -> new LinkedHashMap<>());
            if (p.isPending()) {
                pending++;
                if (p.getCreatedAt() != null && (oldest == null || p.getCreatedAt().isBefore(oldest))) oldest = p.getCreatedAt();
                row.merge("PENDING", 1L, Long::sum);
                continue;
            }
            if (p.isProblem()) problems++;
            if (p.releaseBlocker() == null) releaseReady++;
            if (p.isReceivable()) {
                receivables++;
                row.merge("RECEIVABLES", 1L, Long::sum);
                continue;
            }
            if (p.getLandTitle() != null && p.getLandTitle().isReleased()) { row.merge("HANDED OVER", 1L, Long::sum); continue; }
            List<ProjectStatus> list = new ArrayList<>(statuses.getOrDefault(p.getId(), List.of()));
            list.sort(Comparator.comparing(s -> s.getDisplayOrder() == null ? 0 : s.getDisplayOrder()));
            int idx = p.getCurrentStatusIndex() == null ? 1 : p.getCurrentStatusIndex();
            String name = idx >= 1 && idx <= list.size() ? list.get(idx - 1).getStatusName() : null;
            if (name == null || !templateNames.getOrDefault(type, Set.of()).contains(name)) name = "OTHER";
            row.merge(name, 1L, Long::sum);
        }
        byType.values().removeIf(Map::isEmpty);

        Map<String, Object> pend = new LinkedHashMap<>();
        pend.put("count", pending);
        pend.put("oldestDays", oldest == null ? null : ChronoUnit.DAYS.between(oldest, LocalDateTime.now()));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("pending", pend);
        out.put("byType", byType);
        out.put("problems", problems);
        out.put("receivables", receivables);
        out.put("releaseReady", releaseReady);
        return out;
    }
}
