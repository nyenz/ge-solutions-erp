// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectStatusRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.ProjectStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ProjectStatusRepository extends JpaRepository<ProjectStatus, UUID> {

    List<ProjectStatus> findByProjectIdOrderByDisplayOrderAsc(UUID projectId);

    List<ProjectStatus> findByProjectIdIn(List<UUID> projectIds);

    void deleteByProjectId(UUID projectId);
}
