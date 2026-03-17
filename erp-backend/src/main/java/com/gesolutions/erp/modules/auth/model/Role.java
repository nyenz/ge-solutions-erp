// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/Role.java
package com.gesolutions.erp.modules.auth.model;

/**
 * NYENZ ERP - INDUSTRIAL ROLE DICTIONARY
 * 
 * Defines the operational boundaries of the system.
 * NOTE: The 'Root Founder' is not a role here; it is handled by the 'isRoot' boolean
 * on the User entity to grant absolute supremacy over staff governance.
 */
public enum Role {
    
    /**
     * TIER 2: SYSTEM ADMIN
     * Has full access to Financial Dashboards and Intelligence Reports (The 8 Pillars).
     * Physically blocked from Staff Governance (Cannot create/suspend users).
     */
    ROLE_ADMIN,

    /**
     * TIER 3: STANDARD OPERATOR (Manager)
     * Restricted to Operational Tasks: Master Intake, Ledger, and Recovery Hub.
     * Physically blocked from company-wide Financials and Intelligence Reports.
     */
    ROLE_MANAGER
}