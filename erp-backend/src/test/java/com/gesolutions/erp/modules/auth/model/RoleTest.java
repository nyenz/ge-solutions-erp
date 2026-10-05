package com.gesolutions.erp.modules.auth.model;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** fix181: the 5 ranks (LLM_CONTEXT_GUIDE.md Section 5). Admin 5 > Director 4 > Manager 3 > Secretary 2 > Employee 1. */
public class RoleTest {

    @Test
    public void ranksAreInOrder() {
        assertTrue(Role.ROLE_ADMIN.outranks(Role.ROLE_DIRECTOR));
        assertTrue(Role.ROLE_DIRECTOR.outranks(Role.ROLE_MANAGER));
        assertTrue(Role.ROLE_MANAGER.outranks(Role.ROLE_SECRETARY));
        assertTrue(Role.ROLE_SECRETARY.outranks(Role.ROLE_EMPLOYEE));
        assertFalse(Role.ROLE_DIRECTOR.outranks(Role.ROLE_DIRECTOR), "same rank never outranks itself");
    }

    @Test
    public void onlyAdminAndDirectorAreOwnerLevel() {
        assertTrue(Role.ROLE_ADMIN.isOwnerLevel());
        assertTrue(Role.ROLE_DIRECTOR.isOwnerLevel());
        assertFalse(Role.ROLE_MANAGER.isOwnerLevel());
        assertFalse(Role.ROLE_SECRETARY.isOwnerLevel());
        assertFalse(Role.ROLE_EMPLOYEE.isOwnerLevel());
    }
}
