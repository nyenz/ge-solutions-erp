// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectStageRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.ProjectStage;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ProjectStageRepository extends JpaRepository<ProjectStage, UUID> {

    List<ProjectStage> findByProjectIdOrderByDisplayOrderAsc(UUID projectId);

    List<ProjectStage> findByProjectIdIn(List<UUID> projectIds);

    void deleteByProjectId(UUID projectId);
}
