// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java
package com.gesolutions.erp.modules.auth.model;

/**
 * GOLDEN SEED ERP - RANKS (fix181: five ranks, top to bottom; LLM_CONTEXT_GUIDE.md Section 5)
 *
 *  5 ROLE_ADMIN     the system designer. Exactly ONE account (the admin_root user, isRoot = true). Nobody can create,
 *                   promote to, suspend or re-rank an Admin.
 *  4 ROLE_DIRECTOR  the business owner. Full money view; manages Manager, Secretary and Employee accounts; Archive.
 *  3 ROLE_MANAGER   runs the work: statuses, payments, edits.
 *  2 ROLE_SECRETARY office data entry and recovery calls; sets prices on Pending projects.
 *  1 ROLE_EMPLOYEE  field data entry only: creates Pending projects, never sees money.
 *
 * Every rank comparison in the server goes through rank() / outranks() here; the page has the same list in
 * erp-frontend/src/utils/roles.js. Keep the two in step. The database role check is rebuilt from values() on every
 * start (DataInitializer.roleCheckSql), so adding a rank here needs no SQL.
 */
public enum Role {

    ROLE_ADMIN(5, "Admin"),
    ROLE_MANAGER(3, "Manager"),
    ROLE_DIRECTOR(4, "Director"),
    ROLE_SECRETARY(2, "Secretary"),
    ROLE_EMPLOYEE(1, "Employee");

    private final int rank;
    private final String label;

    Role(int rank, String label) {
        this.rank = rank;
        this.label = label;
    }

    public int rank() { return rank; }

    public String label() { return label; }

    /** True when this rank is strictly above the other one. */
    public boolean outranks(Role other) {
        return other == null || this.rank > other.rank;
    }

    /** Director and Admin: the owner level (money, staff below them, archive). */
    public boolean isOwnerLevel() { return rank >= ROLE_DIRECTOR.rank; }
}
