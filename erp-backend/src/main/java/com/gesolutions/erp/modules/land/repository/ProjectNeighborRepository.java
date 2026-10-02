// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectNeighborRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.ProjectNeighbor;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ProjectNeighborRepository extends JpaRepository<ProjectNeighbor, UUID> {

    List<ProjectNeighbor> findByProjectIdOrderByDisplayOrderAsc(UUID projectId);
}
