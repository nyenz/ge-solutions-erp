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

    // STAGE 3: covers every plain projectRepository.findAll() call across the
    // codebase (RecoveryController, DashboardController, ReportService) in one
    // place -- soft-deleted plots simply stop showing up anywhere that lists
    // "all" projects, with no other file needing to change.
    @Override
    @NonNull
    @Query("SELECT p FROM LandProject p WHERE p.deleted = false")
    List<LandProject> findAll();

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    @Query("SELECT p FROM LandProject p WHERE p.deleted = false")
    Page<LandProject> findAll(@NonNull Pageable pageable);

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Optional<LandProject> findById(@NonNull UUID id);

    // STAGE 3: restore screen -- deliberately the ONLY query that returns
    // deleted=true rows.
    @Query("SELECT p FROM LandProject p WHERE p.deleted = true ORDER BY p.deletedAt DESC")
    List<LandProject> findAllDeleted();

    // All active (non-receivable) plots with outstanding balance
    // that have had no payment for over 365 days — candidates for auto-receivable
    // Fixed: require BOTH registration date AND last payment date to be older than cutoff
    // This prevents newly registered plots with no initial payment from being instantly flagged
    @Query("SELECT p FROM LandProject p WHERE p.isReceivable = false " +
           "AND p.deleted = false " +
           "AND p.amountPaid < p.totalCost " +
           "AND p.landTitle.createdAt < :cutoff " +
           "AND (p.lastPaymentDate IS NULL OR p.lastPaymentDate < :cutoff)")
    List<LandProject> findAutoReceivableCandidates(LocalDateTime cutoff);

    // All plots currently in receivable
    @Query("SELECT p FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false")
    List<LandProject> findAllReceivablePlots();

    // Count receivable plots
    @Query("SELECT COUNT(p) FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false")
    long countReceivablePlots();

    // Sum all storage fees across all receivable plots
    @Query("SELECT COALESCE(SUM(p.storageFeesAccumulated), 0) FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false")
    java.math.BigDecimal sumAllStorageFees();
}