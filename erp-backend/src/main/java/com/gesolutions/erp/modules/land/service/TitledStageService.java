// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/TitledStageService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.LandTitle;
import com.gesolutions.erp.modules.land.model.ProjectStatus;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.LandTitleRepository;
import com.gesolutions.erp.modules.land.repository.ProjectStatusRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix197 (David, review Q4): HOW A FRESH SURVEY ENDS.
 * A Fresh Survey starts with no title. Its last stage is "Titled". That stage can only be ticked TOGETHER with the
 * Title Details (plot number, block, area, title date): no details, no tick. From then on the project is a titled
 * project like any other: when everything is paid the title is handed over (the normal HAND OVER TITLE button).
 * The same rule holds for every project type: the "Titled" stage is never ticked on a project without Title Details.
 */
@Service
@RequiredArgsConstructor
public class TitledStageService {

    private final LandProjectRepository projectRepository;
    private final LandTitleRepository titleRepository;
    private final ProjectStatusRepository statusRepository;
    private final AuditService auditService;

    private static String text(String v) { return v == null || v.isBlank() ? null : v.trim(); }

    /** Ticks the Titled stage. When the project has no Title Details yet, the request must carry them and they are saved first. */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public LandProject completeTitled(UUID projectId, UUID statusId, LandEntryRequest r) {
        LandProject p = projectRepository.findByIdForUpdate(projectId)
                .orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        if (p.isDeleted()) throw new BusinessException("STATUS_LOCKED: This project is deleted. Restore it first.");
        if (p.isPending()) throw new BusinessException("STILL_PENDING: This project is still Pending. Start it first.");
        ProjectStatus stage = statusRepository.findById(statusId)
                .orElseThrow(() -> new BusinessException("PROJECT_STATUS_NOT_FOUND"));
        if (!projectId.equals(stage.getProjectId())) throw new BusinessException("STATUS_MISMATCH: That stage does not belong to this project.");
        if (!LandService.isTitledStatus(stage.getStatusName())) {
            throw new BusinessException("NOT_THE_TITLED_STAGE: Title Details are entered on the \"Titled\" stage only.");
        }
        LandTitle title = p.getLandTitle();
        if (title != null && title.isReleased()) {
            throw new BusinessException("STATUS_LOCKED: The title has been handed over, so its stages are locked.");
        }
        if (title == null) {
            String plot = text(r == null ? null : r.getPlotNumber());
            String block = text(r == null ? null : r.getBlock());
            if (plot == null) throw new BusinessException("PLOT_NUMBER_REQUIRED: Type the Plot Number of the new title.");
            if (block == null) throw new BusinessException("BLOCK_REQUIRED: Type the Block of the new title.");
            if (r.getAreaHectares() == null || r.getAreaHectares().signum() <= 0) {
                throw new BusinessException("AREA_REQUIRED: Type the Area in hectares (more than 0).");
            }
            if (r.getTitleIssueDate() == null) throw new BusinessException("TITLE_DATE_REQUIRED: Pick the Title Date.");
            if (r.getTitleIssueDate().isAfter(LocalDate.now())) throw new BusinessException("TITLE_DATE_INVALID: The Title Date cannot be in the future.");
            if (titleRepository.existsByPlotNumber(plot)) {
                throw new BusinessException("PLOT_TAKEN: Plot number \"" + plot + "\" is already on another project.");
            }
            title = LandTitle.builder()
                    .tenure(text(r.getTenure()) != null ? text(r.getTenure()) : "FREEHOLD")
                    .plotNumber(plot)
                    .block(block)
                    .areaHectares(r.getAreaHectares())
                    .volume(text(r.getVolume()))
                    .folio(text(r.getFolio()))
                    .projectStartDate(p.getProjectStartDate() != null ? p.getProjectStartDate() : LocalDate.now())
                    .titleIssueDate(r.getTitleIssueDate())
                    .build();
            p.setLandTitle(title);
            p.setTitleDetailsEnabled(true);
            auditService.logActionAfterCommit("TITLE_FIELDS_CHANGED", "Operator [" + AuditService.currentOperator()
                    + "] entered the title details of project #" + p.getProjectIndex() + " on the Titled stage. Old: (none) -> New: plot " + plot
                    + ", block " + block + ", " + title.getTenure() + ", " + r.getAreaHectares().toPlainString() + " ha, title date " + r.getTitleIssueDate());
        }
        LandProject saved = projectRepository.save(p);
        if (!stage.isCompleted()) {
            stage.setCompleted(true);
            stage.setCompletedAt(LocalDateTime.now());
            stage.setCompletedBy(AuditService.currentOperator());
            statusRepository.save(stage);
            auditService.logActionAfterCommit("PROJECT_STATUS_CHANGED", "Operator [" + AuditService.currentOperator() + "] marked status \""
                    + stage.getStatusName() + "\" as COMPLETE on project: " + projectId);
        }
        return saved;
    }
}
