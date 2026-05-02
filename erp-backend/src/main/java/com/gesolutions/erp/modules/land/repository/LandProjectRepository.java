// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/LandProjectRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.LandProject;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface LandProjectRepository extends JpaRepository<LandProject, UUID> {

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Page<LandProject> findAll(@NonNull Pageable pageable);

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Optional<LandProject> findById(@NonNull UUID id);

    // All active (non-backlog) plots with outstanding balance
    // that have had no payment for over 365 days — candidates for auto-backlog
    @Query("SELECT p FROM LandProject p WHERE p.isBacklog = false " +
           "AND p.amountPaid < p.totalCost " +
           "AND (p.lastPaymentDate IS NULL OR p.lastPaymentDate < :cutoff)")
    List<LandProject> findAutoBacklogCandidates(LocalDateTime cutoff);

    // All plots currently in backlog
    @Query("SELECT p FROM LandProject p WHERE p.isBacklog = true")
    List<LandProject> findAllBacklogPlots();

    // Count backlog plots
    @Query("SELECT COUNT(p) FROM LandProject p WHERE p.isBacklog = true")
    long countBacklogPlots();

    // Sum all storage fees across all backlog plots
    @Query("SELECT COALESCE(SUM(p.storageFeesAccumulated), 0) FROM LandProject p WHERE p.isBacklog = true")
    java.math.BigDecimal sumAllStorageFees();
}