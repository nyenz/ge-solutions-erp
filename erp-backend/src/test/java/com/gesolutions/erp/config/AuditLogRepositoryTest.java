package com.gesolutions.erp.config;

import com.gesolutions.erp.common.audit.AuditLogRepository;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;

import static org.junit.jupiter.api.Assertions.assertFalse;

/** fix181: the audit trail is append-only in code. Nobody may add a delete or update method to its repository. */
class AuditLogRepositoryTest {

    @Test
    void repositoryHasNoDeleteOrRemoveMethod() {
        for (Method m : AuditLogRepository.class.getMethods()) {
            String n = m.getName().toLowerCase();
            assertFalse(n.startsWith("delete") || n.startsWith("remove") || n.startsWith("update"),
                    "AuditLogRepository must stay append-only, found: " + m.getName());
        }
    }
}
