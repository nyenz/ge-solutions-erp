// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditLogRepository.java
package com.gesolutions.erp.common.audit;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - FORENSIC ARCHIVE ACCESS
 * 
 * Physically manages the retrieval of system footprints.
 * Standardized for multi-axis filtering and specific interaction tracing.
 */
@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, UUID> {

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
           "(cast(:end as timestamp) IS NULL OR a.timestamp <= :end)")
    Page<AuditLog> findWithFilters(
            @Param("operator") String operator,
            @Param("action") String action,
            @Param("start") LocalDateTime startDate,
            @Param("end") LocalDateTime endDate,
            Pageable pageable
    );

    /**
     * KEYWORD INVESTIGATION
     * Full-text search across the 'details' block for Plots/IDs/Notes.
     */
    Page<AuditLog> findByDetailsContainingIgnoreCase(String keyword, Pageable pageable);
}