// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java
package com.gesolutions.erp.modules.auth.model;

/**
 * NYENZ ERP - INDUSTRIAL ROLE DICTIONARY
 *
 * PHASE 3A: Enum expanded to prepare for the 4-tier hierarchy (Section 17.7
 * of LLM_CONTEXT_GUIDE.md). This is additive only -- ROLE_DIRECTOR and
 * ROLE_SECRETARY exist now but no @PreAuthorize check anywhere references
 * them yet. Every existing access-control check still only knows about
 * ROLE_ADMIN and ROLE_MANAGER, so current behavior is unchanged.
 *
 * The 'Root Founder' (Programmer tier) is still not a role here; it remains
 * the 'isRoot' boolean on the User entity, layered on top of ROLE_ADMIN.
 *
 * Wiring these new values into actual permission checks (backend
 * @PreAuthorize + frontend role gates) is Phase 3B -- a separate, dedicated
 * patch, since it touches every controller and several frontend files.
 */
public enum Role {

    /**
     * TIER 2: SYSTEM ADMIN
     * Current full-financials tier. Will map toward "Director" behavior
     * once Phase 3B wires real permission checks.
     */
    ROLE_ADMIN,

    /**
     * TIER 3: STANDARD OPERATOR (Manager)
     * Current operational-only tier. Unchanged.
     */
    ROLE_MANAGER,

    /**
     * TIER 2 (NEW, Phase 3A groundwork): DIRECTOR
     * Full company-wide financial visibility per Section 17.7, distinct
     * from ROLE_ADMIN in the target design (Director sees everything;
     * Manager sees project-level only). Not yet enforced anywhere.
     */
    ROLE_DIRECTOR,

    /**
     * TIER 4 (NEW, Phase 3A groundwork): SECRETARY
     * Data-entry only, stage changes but not cost changes, no company
     * financials, no template edits, per Section 17.7. Not yet enforced
     * anywhere -- currently behaves identically to whatever @PreAuthorize
     * checks already exist (i.e. blocked from anything ROLE_ADMIN/
     * ROLE_MANAGER-gated, same as any unrecognized role would be).
     */
    ROLE_SECRETARY
}
