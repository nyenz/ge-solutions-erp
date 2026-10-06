// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/LandProjectRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.LandProject;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.lang.NonNull;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface LandProjectRepository extends JpaRepository<LandProject, UUID> {

    // STAGE 3: covers every plain projectRepository.findAll() call across the
    // codebase in one place -- soft-deleted plots (and, since fix181, Pending
    // projects) simply stop showing up anywhere that lists "all" projects.
    @Override
    @NonNull
    // fix170: owners + title come in the SAME query. Both are EAGER, and a plain JPQL query loads EAGER links one
    // project at a time (hundreds of tiny queries per request) -- Recovery, Dashboard, Reports and Client Ledger all pay that.
    // fix180: the clients (who Recovery calls) come in the same query too
    // fix181 (8.9): Pending projects are left out HERE, once, so no money figure, Recovery list or nightly job sees them.
    @Query("SELECT DISTINCT p FROM LandProject p LEFT JOIN FETCH p.proprietors LEFT JOIN FETCH p.clients LEFT JOIN FETCH p.landTitle WHERE p.deleted = false AND p.pending = false")
    List<LandProject> findAll();

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "clients", "landTitle"})
    @Query("SELECT p FROM LandProject p WHERE p.deleted = false AND p.pending = false")
    Page<LandProject> findAll(@NonNull Pageable pageable);

    /**
     * fix181 (8.9): the same lists WITH Pending projects. Use ONLY for the ledger endpoint (the Pending tab shows them
     * there), the Pending count and the Employee's MY ENTRIES. Never for money, Recovery or a job.
     */
    @Query("SELECT DISTINCT p FROM LandProject p LEFT JOIN FETCH p.proprietors LEFT JOIN FETCH p.clients LEFT JOIN FETCH p.landTitle WHERE p.deleted = false")
    List<LandProject> findAllIncludingPending();

    @EntityGraph(attributePaths = {"proprietors", "clients", "landTitle"})
    @Query("SELECT p FROM LandProject p WHERE p.deleted = false")
    Page<LandProject> findAllIncludingPending(Pageable pageable);

    @Query("SELECT COUNT(p) FROM LandProject p WHERE p.deleted = false AND p.pending = true")
    long countPending();

    /** fix181 (16.12a): the project row, locked for writing until this transaction ends (payments and reversals). */
    @org.springframework.data.jpa.repository.Lock(jakarta.persistence.LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT p FROM LandProject p WHERE p.id = :id")
    Optional<LandProject> findByIdForUpdate(@org.springframework.data.repository.query.Param("id") UUID id);

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "clients", "landTitle"})
    Optional<LandProject> findById(@NonNull UUID id);

    // STAGE 3: restore screen -- deliberately the ONLY query that returns
    // deleted=true rows.
    @Query("SELECT p FROM LandProject p WHERE p.deleted = true ORDER BY p.deletedAt DESC")
    List<LandProject> findAllDeleted();

    // All active (non-receivable) plots with outstanding balance
    // that have had no payment for over 365 days — candidates for auto-receivable
    // Fixed: require BOTH registration date AND last payment date to be older than cutoff
    // This prevents newly registered plots with no initial payment from being instantly flagged
    // fix197 (David, Q4; review S09): EVERY project type goes to Receivables after 365 days without payment. The query
    // used to read the title's date only, so a project with no Title Details (Fresh Survey, Special Projects) was never
    // found. Now: a project WITH Title Details is judged by the title's date, as before; a project WITHOUT them is judged
    // by its own entry date. (A Fresh Survey that gets its title later is judged by the new title's date from then on.)
    @Query("SELECT p FROM LandProject p LEFT JOIN p.landTitle t WHERE p.isReceivable = false " +
           "AND p.deleted = false AND p.pending = false " +
           "AND p.amountPaid < p.totalCost " +
           "AND (t.createdAt < :cutoff OR (t IS NULL AND p.createdAt < :cutoff)) " +
           "AND (p.graduatedAt IS NULL OR p.graduatedAt < :cutoff) " +   // fix181 (4.4): the clock starts at the LATER of the two
           "AND (p.lastPaymentDate IS NULL OR p.lastPaymentDate < :cutoff)")
    List<LandProject> findAutoReceivableCandidates(LocalDateTime cutoff);

    // fix167: other live (not deleted) projects that share at least one owner -- the Related Projects list
    @Query("SELECT DISTINCT p FROM LandProject p JOIN p.proprietors c WHERE c.id IN :ownerIds AND p.id <> :projectId AND p.deleted = false AND p.pending = false")   // fix181 (3.7)
    List<LandProject> findRelatedByOwners(@org.springframework.data.repository.query.Param("ownerIds") java.util.Collection<UUID> ownerIds,
                                          @org.springframework.data.repository.query.Param("projectId") UUID projectId);

    /**
     * fix181 (4.3): one client's live projects where they are a billing party (a client of the project, or an owner of
     * an old project that has no clients). Replaces reading every project to find one client's.
     */
    @Query("SELECT DISTINCT p FROM LandProject p LEFT JOIN p.clients c LEFT JOIN p.proprietors o "
         + "WHERE p.deleted = false AND p.pending = false AND (c.id = :clientId OR (o.id = :clientId AND p.clients IS EMPTY))")
    List<LandProject> findByBillingClient(@org.springframework.data.repository.query.Param("clientId") UUID clientId);

    // fix196: who already uses this invoice / contract number (deleted projects do not count; capitals do not matter)
    @Query("SELECT p FROM LandProject p WHERE p.deleted = false AND LOWER(p.invoiceNumber) = LOWER(:n)")
    List<LandProject> findLiveByInvoiceNumber(@org.springframework.data.repository.query.Param("n") String n);

    @Query("SELECT p FROM LandProject p WHERE p.deleted = false AND LOWER(p.contractNumber) = LOWER(:n)")
    List<LandProject> findLiveByContractNumber(@org.springframework.data.repository.query.Param("n") String n);

    /** fix181 (8.10b, 11.1b): every live project (Pending included) where this person is a client or an owner. */
    @Query("SELECT DISTINCT p FROM LandProject p LEFT JOIN p.clients c LEFT JOIN p.proprietors o "
         + "WHERE p.deleted = false AND (c.id = :clientId OR o.id = :clientId)")
    List<LandProject> findAllOfPersonIncludingPending(@org.springframework.data.repository.query.Param("clientId") UUID clientId);

    /** fix181 (8.7d, 12.3): the projects an Employee entered (deleted = rejected ones too), newest first. */
    @Query("SELECT p FROM LandProject p WHERE p.createdById = :userId ORDER BY p.createdAt DESC")
    List<LandProject> findByCreatedById(@org.springframework.data.repository.query.Param("userId") UUID userId);

    // fix180: the Transfer of Title projects made from one subdivision project's plots (deleted ones left out)
    @Query("SELECT p FROM LandProject p WHERE p.parentProjectId = :parentId AND p.deleted = false")
    List<LandProject> findTransfersOf(@org.springframework.data.repository.query.Param("parentId") UUID parentId);

    // All plots currently in receivable
    @Query("SELECT p FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false AND p.pending = false")
    List<LandProject> findAllReceivablePlots();

    // Count receivable plots
    @Query("SELECT COUNT(p) FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false AND p.pending = false")
    long countReceivablePlots();

    // Sum all storage fees across all receivable plots
    @Query("SELECT COALESCE(SUM(p.storageFeesAccumulated), 0) FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false AND p.pending = false")
    java.math.BigDecimal sumAllStorageFees();
}