// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditService.java
package com.gesolutions.erp.common.audit;

import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import java.time.LocalDateTime;

/**
 * GE SOLUTIONS - AUTONOMOUS FORENSIC LOGGER
 *
 * fix181: three ways to write a line.
 *  - logAction: written AT ONCE in its own transaction. Only for events that must exist even when the request fails
 *    (failed / blocked logins, refused access, the data wipe).
 *  - logActionAfterCommit: written only AFTER the caller's transaction commits. Use it for every data change, so a save
 *    that is rolled back never leaves a line describing something that did not happen (e.g. a payment whose receipt
 *    could not be filed). A failure to write is printed to the server log and never reported to the user, because the
 *    real action is already saved.
 *  - logActionAs: like logAction, but with the operator name given (login events: nobody is signed in yet, and the
 *    browser may still send an OLD person's token, so the security context cannot be trusted).
 * Operator names are cut to 100 characters, actions to 60, and control characters are removed, so a typed name can
 * never break the insert.
 */
@Service
public class AuditService {

    private final AuditLogRepository auditLogRepository;
    private final TransactionTemplate newTx;

    public AuditService(AuditLogRepository auditLogRepository, PlatformTransactionManager txManager) {
        this.auditLogRepository = auditLogRepository;
        this.newTx = new TransactionTemplate(txManager);
        this.newTx.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);
    }

    /** The signed-in operator, or SYSTEM (nightly jobs, start-up). The anonymous placeholder never counts as a person. */
    public static String currentOperator() {
        Authentication a = SecurityContextHolder.getContext().getAuthentication();
        if (a == null || a instanceof AnonymousAuthenticationToken || a.getName() == null) return "SYSTEM";
        return a.getName();
    }

    static String clean(String v, int max) {
        if (v == null) return null;
        String t = v.replaceAll("[\\p{Cntrl}]", " ").trim();
        return t.length() > max ? t.substring(0, max) : t;
    }

    /** Written at once, even if the caller's transaction later fails. */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logAction(String action, String details) {
        save(currentOperator(), action, details);
    }

    /** Written at once under the given operator name (login events). */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logActionAs(String operatorName, String action, String details) {
        String who = clean(operatorName, 100);
        save(who == null || who.isEmpty() ? "(unknown)" : who, action, details);
    }

    /** Written after the caller's transaction commits (or at once when there is none). Never throws. */
    public void logActionAfterCommit(String action, String details) {
        final String who = currentOperator();
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    writeSafely(who, action, details);
                }
            });
        } else {
            writeSafely(who, action, details);
        }
    }

    private void writeSafely(String who, String action, String details) {
        try {
            newTx.executeWithoutResult(st -> save(who, action, details));
        } catch (Exception e) {
            System.err.println(">>> [AUDIT] could not write " + action + " for " + who + ": " + e.getMessage());
        }
    }

    private void save(String who, String action, String details) {
        auditLogRepository.save(AuditLog.builder()
                .action(clean(action, 60))
                .details(details)
                .performedBy(clean(who, 100))
                .timestamp(LocalDateTime.now())
                .build());
    }
}
