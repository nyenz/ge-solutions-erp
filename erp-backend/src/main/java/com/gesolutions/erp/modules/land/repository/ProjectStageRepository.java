// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectStageRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.ProjectStage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ProjectStageRepository extends JpaRepository<ProjectStage, UUID> {

    List<ProjectStage> findByProjectIdOrderByDisplayOrderAsc(UUID projectId);

    void deleteByProjectId(UUID projectId);
}
