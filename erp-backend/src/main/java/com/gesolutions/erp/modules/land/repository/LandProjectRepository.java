// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/LandProjectRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.LandProject;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

/**
 * GE SOLUTIONS - LAND PROJECT REPOSITORY
 * 
 * Standardized with Spring Null-Safety annotations to satisfy strict IDE analysis.
 * Uses @EntityGraph to solve the N+1 problem and ensures high-speed data retrieval.
 */
@Repository
public interface LandProjectRepository extends JpaRepository<LandProject, UUID> {

    /**
     * FETCH ALL PLOTS
     * FIXED: Attribute mapping changed to "proprietors" to resolve 500 error.
     * @NonNull used to match the parent PagingAndSortingRepository contract.
     */
    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Page<LandProject> findAll(@NonNull Pageable pageable);

    /**
     * FETCH SPECIFIC FOLDER
     * FIXED: Attribute mapping changed to "proprietors".
     * @NonNull used to match the parent CrudRepository contract.
     */
    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Optional<LandProject> findById(@NonNull UUID id);
}