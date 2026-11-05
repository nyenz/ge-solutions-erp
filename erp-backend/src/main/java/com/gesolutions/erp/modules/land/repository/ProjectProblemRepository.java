// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectProblemRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.ProjectProblem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

/** fix289: the problems beside the projects. */
public interface ProjectProblemRepository extends JpaRepository<ProjectProblem, UUID> {

    List<ProjectProblem> findByProjectIdOrderByCreatedAtDesc(UUID projectId);

    List<ProjectProblem> findByStatusOrderByCreatedAtDesc(String status);

    List<ProjectProblem> findAllByOrderByCreatedAtDesc();

    List<ProjectProblem> findByClientIdOrderByCreatedAtDesc(UUID clientId);

    boolean existsByProjectIdAndKindAndStatus(UUID projectId, String kind, String status);

    // the words typed under OTHER before, most used first (the list that remembers)
    @Query("SELECT p.label FROM ProjectProblem p WHERE p.kind = 'OTHER' GROUP BY p.label ORDER BY COUNT(p) DESC, p.label")
    List<String> rememberedOtherLabels();

    @Query("SELECT p.projectId, COUNT(p) FROM ProjectProblem p WHERE p.status = 'OPEN' GROUP BY p.projectId")
    List<Object[]> openCountPerProject();
}
