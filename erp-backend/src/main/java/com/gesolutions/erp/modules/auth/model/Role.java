// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java
package com.gesolutions.erp.modules.auth.model;

/**
 * GOLDEN SEED ERP - INDUSTRIAL ROLE DICTIONARY
 *
 * 4-tier hierarchy per Section 17.7 of LLM_CONTEXT_GUIDE.md. ROLE_DIRECTOR
 * and ROLE_SECRETARY are fully wired: every controller's @PreAuthorize
 * checks and the frontend's route/nav gates already reference them
 * (landed via the separate bug-fix roadmap's Stage 1 and Stage 2, not the
 * original Phase 3B/3C patches -- see LLM_CONTEXT_GUIDE.md Section 17.10
 * for the corrected Phase Tracker entry).
 *
 * The 'Root Founder' (Programmer tier) is still not a role here; it remains
 * the 'isRoot' boolean on the User entity, layered on top of ROLE_ADMIN.
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
     * TIER 2: DIRECTOR
     * Full company-wide financial visibility per Section 17.7, distinct
     * from ROLE_ADMIN in the target design (Director sees everything;
     * Manager sees project-level only). Enforced across every controller's
     * @PreAuthorize checks and the frontend's route gates.
     */
    ROLE_DIRECTOR,

    /**
     * TIER 4: SECRETARY
     * Data-entry only, stage changes but not cost changes, no company
     * financials, no template edits, per Section 17.7. Enforced per-method
     * on the relevant controllers (LandController, StageTemplateController,
     * RecoveryController) rather than at the class level, since Secretary
     * needs some but not all of what Manager can do on the same endpoints.
     */
    ROLE_SECRETARY
}
