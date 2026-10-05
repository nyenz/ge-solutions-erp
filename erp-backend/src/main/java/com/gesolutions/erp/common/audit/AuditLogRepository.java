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

    // fix181 (12.5c, 20.6): counts by SQL (the Dashboard used to load the whole table into memory)
    long countByTimestampAfter(java.time.LocalDateTime after);
    long countByActionInAndTimestampAfter(java.util.Collection<String> actions, java.time.LocalDateTime after);
    @Query("SELECT a FROM AuditLog a WHERE a.action NOT IN :hidden ORDER BY a.timestamp DESC")
    List<AuditLog> findRecentExcept(@org.springframework.data.repository.query.Param("hidden") java.util.Collection<String> hidden, Pageable page);

    // fix181 (10.13, 10.7): searching is done by AuditSearchService (a read-only criteria query with a list of codes);
    // the old one-code search and the keyword-only /investigate query were removed.
}
