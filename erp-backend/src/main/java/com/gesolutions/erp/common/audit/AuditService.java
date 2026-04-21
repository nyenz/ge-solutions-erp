// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditService.java
package com.gesolutions.erp.common.audit;

import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import java.time.LocalDateTime;

/**
 * GE SOLUTIONS - AUTONOMOUS FORENSIC LOGGER
 * 
 * Physically ensures all footprints are permanent. 
 * Uses REQUIRES_NEW to prevent log rollback during system errors.
 */
@Service
@RequiredArgsConstructor
public class AuditService {

    private final AuditLogRepository auditLogRepository;

    /**
     * PERMANENT LOG COMMIT
     * 
     * Propagation.REQUIRES_NEW: Starts a separate transaction for the log.
     * Even if the main technical action fails, the log remains in the DB.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logAction(String action, String details) {
        // Retrieve current operator from security context
        String currentUser = "SYSTEM";
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            currentUser = SecurityContextHolder.getContext().getAuthentication().getName();
        }

        AuditLog logEntry = AuditLog.builder()
                .action(action)
                .details(details)
                .performedBy(currentUser)
                .timestamp(LocalDateTime.now())
                .build();

        // Physically commit to PostgreSQL disk
        auditLogRepository.save(logEntry);
    }
}