// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditLogRepository.java
package com.gesolutions.erp.common.audit;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.Repository;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * GE SOLUTIONS - FORENSIC ARCHIVE ACCESS
 * 
 * Physically manages the retrieval of system footprints.
 * Standardized for multi-axis filtering and specific interaction tracing.
 */
// fix181: APPEND-ONLY. The audit trail is evidence, so this repository can only add and read lines: there is no delete,
// update or deleteAll here on purpose (AuditLogRepositoryTest fails if one is added). The real protection is the
// database password; this stops accidents in code.
public interface AuditLogRepository extends Repository<AuditLog, UUID> {

    AuditLog save(AuditLog log);

    <S extends AuditLog> List<S> saveAll(Iterable<S> logs);

    List<AuditLog> findAll();

    Page<AuditLog> findAll(Pageable pageable);

    long count();

    /**
     * MULTI-AXIS FORENSIC SEARCH (Hardened Version)
     * 
     * FIXED: Explicit cast to text and timestamp to resolve the 
     * 'could not determine data type' PostgreSQL error.
     * Includes support for RECOVERY_MISSION_COMPLETE (Call Logs).
     */
    @Query("SELECT a FROM AuditLog a WHERE " +
           "(cast(:operator as text) IS NULL OR a.performedBy = cast(:operator as text)) AND " +
           "(cast(:action as text) IS NULL OR a.action = cast(:action as text)) AND " +
           "(cast(:start as timestamp) IS NULL OR a.timestamp >= :start) AND " +
           "(cast(:end as timestamp) IS NULL OR a.timestamp <= :end) AND " +
           "(cast(:keyword as text) IS NULL OR " +
           "   LOWER(a.details) LIKE LOWER(CONCAT('%', cast(:keyword as text), '%')) OR " +
           "   LOWER(a.performedBy) LIKE LOWER(CONCAT('%', cast(:keyword as text), '%')))")
    Page<AuditLog> findWithFilters(
            @Param("operator") String operator,
            @Param("action") String action,
            @Param("start") LocalDateTime startDate,
            @Param("end") LocalDateTime endDate,
            @Param("keyword") String keyword,
            Pageable pageable
    );

    /**
     * KEYWORD INVESTIGATION
     * Full-text search across the 'details' block for Plots/IDs/Notes.
     */
    Page<AuditLog> findByDetailsContainingIgnoreCase(String keyword, Pageable pageable);
}