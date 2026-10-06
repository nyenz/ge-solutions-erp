// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditActions.java
package com.gesolutions.erp.common.audit;

import java.util.Set;

/**
 * fix181 (13.13): ONE list of every audit code the server writes, so the writers, the readers (Dashboard, Reports, the
 * Audit page catalog) and the tests cannot drift apart again. AuditActionsTest fails when a logAction call in the
 * server code uses a code that is not here; scripts/check-audit-codes.mjs (front end build) warns when the Audit page
 * catalog misses one. New code: add the constant here AND an entry in erp-frontend/src/pages/Audit/auditCatalog.js.
 * AUDIT_REPAIRED is reserved for the owner-approved repair of old LOGIN_SUCCESS rows (13.0d); nothing writes it yet.
 */
public final class AuditActions {

    private AuditActions() {}

    public static final String ACCESS_DENIED = "ACCESS_DENIED";
    public static final String AUDIT_EXPORT = "AUDIT_EXPORT";
    public static final String AUDIT_REPAIRED = "AUDIT_REPAIRED";
    public static final String AUTO_RECEIVABLE = "AUTO_RECEIVABLE";
    public static final String AUTO_RECEIVABLE_FAILED = "AUTO_RECEIVABLE_FAILED";
    public static final String BOOKS_MISMATCH = "BOOKS_MISMATCH";
    public static final String BULK_TITLE_PRODUCED = "BULK_TITLE_PRODUCED";
    public static final String CLIENTS_CHANGED = "CLIENTS_CHANGED";
    public static final String CLIENT_ARCHIVE = "CLIENT_ARCHIVE";
    public static final String CLIENT_NIN_CORRECTED = "CLIENT_NIN_CORRECTED";
    public static final String CLIENT_UPDATED = "CLIENT_UPDATED";
    public static final String COST_CHANGED = "COST_CHANGED";
    public static final String CREDENTIAL_RESET = "CREDENTIAL_RESET";
    public static final String DATA_WIPED = "DATA_WIPED";
    public static final String DOCUMENT_CATEGORY_ADDED = "DOCUMENT_CATEGORY_ADDED";
    public static final String DOCUMENT_DELETED = "DOCUMENT_DELETED";
    public static final String DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED";
    public static final String EDIT_MODE_OPENED = "EDIT_MODE_OPENED";
    public static final String EXPENSE_DELETED = "EXPENSE_DELETED";
    public static final String EXPENSE_EDITED = "EXPENSE_EDITED";
    public static final String EXPENSE_LOGGED = "EXPENSE_LOGGED";
    public static final String EXPENSE_PRESET_CREATED = "EXPENSE_PRESET_CREATED";
    public static final String FEES_CAPITALIZED = "FEES_CAPITALIZED";
    public static final String FEES_REDUCED = "FEES_REDUCED";
    public static final String FEES_WAIVED = "FEES_WAIVED";
    public static final String INTAKE = "INTAKE";
    public static final String LOGIN_BLOCKED = "LOGIN_BLOCKED";
    public static final String LOGIN_FAILED = "LOGIN_FAILED";
    public static final String LOGIN_SUCCESS = "LOGIN_SUCCESS";
    public static final String NOTE_ADDED = "NOTE_ADDED";
    public static final String NOTE_DELETED = "NOTE_DELETED";
    public static final String NOTE_UPDATED = "NOTE_UPDATED";
    public static final String NOTIFICATIONS_CLEANED = "NOTIFICATIONS_CLEANED";
    public static final String OPERATOR_PROVISIONED = "OPERATOR_PROVISIONED";
    public static final String OPERATOR_STATUS_CHANGE = "OPERATOR_STATUS_CHANGE";
    public static final String OWNERS_CHANGED = "OWNERS_CHANGED";
    public static final String PAYMENT_RECORDED = "PAYMENT_RECORDED";
    public static final String PAYMENT_REVERSED = "PAYMENT_REVERSED";
    public static final String PENDING_CREATED = "PENDING_CREATED";
    public static final String PENDING_UPDATED = "PENDING_UPDATED";
    public static final String PROBLEM_FLAG = "PROBLEM_FLAG";
    public static final String PROJECT_GRADUATED = "PROJECT_GRADUATED";
    public static final String PROJECT_NUMBERS_CHANGED = "PROJECT_NUMBERS_CHANGED";
    public static final String PROJECT_PENDING_REJECTED = "PROJECT_PENDING_REJECTED";
    public static final String PROJECT_STATUSES_ATTACHED = "PROJECT_STATUSES_ATTACHED";
    public static final String PROJECT_STATUSES_REORDERED = "PROJECT_STATUSES_REORDERED";
    public static final String PROJECT_STATUSES_RESTORED = "PROJECT_STATUSES_RESTORED";
    public static final String PROJECT_STATUS_CHANGED = "PROJECT_STATUS_CHANGED";
    public static final String PROJECT_STATUS_COST_UPDATED = "PROJECT_STATUS_COST_UPDATED";
    public static final String PROJECT_STATUS_REMOVED = "PROJECT_STATUS_REMOVED";
    public static final String RANK_ADJUSTMENT = "RANK_ADJUSTMENT";
    public static final String RECEIVABLE_ENTER = "RECEIVABLE_ENTER";
    public static final String RECEIVABLE_EXIT = "RECEIVABLE_EXIT";
    public static final String RECEIVABLE_SETTINGS = "RECEIVABLE_SETTINGS";
    public static final String RECEIVABLE_SET_ASIDE = "RECEIVABLE_SET_ASIDE";
    public static final String RECEIVABLE_TRIGGER = "RECEIVABLE_TRIGGER";
    public static final String RECORD_DELETED = "RECORD_DELETED";
    public static final String RECORD_RESTORED = "RECORD_RESTORED";
    public static final String RECORD_UPDATED = "RECORD_UPDATED";
    public static final String RECOVERY_NOTE = "RECOVERY_NOTE";
    public static final String RECOVERY_NOTE_DELETED = "RECOVERY_NOTE_DELETED";
    public static final String RECOVERY_REQUESTED = "RECOVERY_REQUESTED";
    public static final String RECOVERY_SYNC = "RECOVERY_SYNC";
    public static final String RECOVERY_USED = "RECOVERY_USED";
    public static final String REPORT_EXPORT = "REPORT_EXPORT";
    public static final String SECURITY_KEY_UPDATE = "SECURITY_KEY_UPDATE";
    public static final String STATUS_OVERRIDE = "STATUS_OVERRIDE";
    public static final String STATUS_TEMPLATE_ADDED = "STATUS_TEMPLATE_ADDED";
    public static final String STATUS_TEMPLATE_REMOVED = "STATUS_TEMPLATE_REMOVED";
    public static final String STATUS_TEMPLATE_RESTORED = "STATUS_TEMPLATE_RESTORED";
    public static final String STATUS_TEMPLATE_UPDATED = "STATUS_TEMPLATE_UPDATED";
    public static final String STORAGE_FEE_APPLIED = "STORAGE_FEE_APPLIED";
    public static final String STORAGE_FEE_RESUMED = "STORAGE_FEE_RESUMED";
    public static final String STORAGE_JOB_FAILED = "STORAGE_JOB_FAILED";
    public static final String SUBDIVISIONS_CHANGED = "SUBDIVISIONS_CHANGED";
    public static final String TIMEZONE_CHANGED = "TIMEZONE_CHANGED";
    public static final String TITLE_FIELDS_CHANGED = "TITLE_FIELDS_CHANGED";
    public static final String TITLE_RELEASED = "TITLE_RELEASED";
    public static final String TITLE_RELEASE_UNDONE = "TITLE_RELEASE_UNDONE";
    public static final String TITLE_REVERTED = "TITLE_REVERTED";
    public static final String WIPE_REFUSED = "WIPE_REFUSED";

    /** Codes only old rows (before the Stage -> Status rename and the receivables rework) or the old demo data carry. */
    public static final Set<String> OLD = Set.of(
            "STAGE_OVERRIDE",
            "PROJECT_STAGE_STATUS_CHANGED",
            "PROJECT_STAGE_COST_UPDATED",
            "PROJECT_STAGE_REMOVED",
            "PROJECT_STAGES_ATTACHED",
            "PROJECT_STAGES_REORDERED",
            "PROJECT_STAGES_RESTORED",
            "STAGE_TEMPLATE_ADDED",
            "STAGE_TEMPLATE_UPDATED",
            "STAGE_TEMPLATE_REMOVED",
            "STORAGE_RATE_CHANGED",
            "STORAGE_FEES_ADJUSTED",
            "RECEIVABLE_START_OVERRIDDEN",
            "NEGOTIATION_DEADLINE_SET",
            "NEGOTIATION_DEADLINE_CLEARED",
            "ROOT_RECOVERY_TRIGGERED");

    /** Every code current server code may write. */
    public static final Set<String> ALL = Set.of(
            ACCESS_DENIED,
            AUDIT_EXPORT,
            AUDIT_REPAIRED,
            AUTO_RECEIVABLE,
            AUTO_RECEIVABLE_FAILED,
            BOOKS_MISMATCH,
            BULK_TITLE_PRODUCED,
            CLIENTS_CHANGED,
            CLIENT_ARCHIVE,
            CLIENT_NIN_CORRECTED,
            CLIENT_UPDATED,
            COST_CHANGED,
            CREDENTIAL_RESET,
            DATA_WIPED,
            DOCUMENT_CATEGORY_ADDED,
            DOCUMENT_DELETED,
            DOCUMENT_UPLOADED,
            EDIT_MODE_OPENED,
            EXPENSE_DELETED,
            EXPENSE_EDITED,
            EXPENSE_LOGGED,
            EXPENSE_PRESET_CREATED,
            FEES_CAPITALIZED,
            FEES_REDUCED,
            FEES_WAIVED,
            INTAKE,
            LOGIN_BLOCKED,
            LOGIN_FAILED,
            LOGIN_SUCCESS,
            NOTE_ADDED,
            NOTE_DELETED,
            NOTE_UPDATED,
            NOTIFICATIONS_CLEANED,
            OPERATOR_PROVISIONED,
            OPERATOR_STATUS_CHANGE,
            OWNERS_CHANGED,
            PAYMENT_RECORDED,
            PAYMENT_REVERSED,
            PENDING_CREATED,
            PENDING_UPDATED,
            PROBLEM_FLAG,
            PROJECT_GRADUATED,
            PROJECT_NUMBERS_CHANGED,
            PROJECT_PENDING_REJECTED,
            PROJECT_STATUSES_ATTACHED,
            PROJECT_STATUSES_REORDERED,
            PROJECT_STATUSES_RESTORED,
            PROJECT_STATUS_CHANGED,
            PROJECT_STATUS_COST_UPDATED,
            PROJECT_STATUS_REMOVED,
            RANK_ADJUSTMENT,
            RECEIVABLE_ENTER,
            RECEIVABLE_EXIT,
            RECEIVABLE_SETTINGS,
            RECEIVABLE_SET_ASIDE,
            RECEIVABLE_TRIGGER,
            RECORD_DELETED,
            RECORD_RESTORED,
            RECORD_UPDATED,
            RECOVERY_NOTE,
            RECOVERY_NOTE_DELETED,
            RECOVERY_REQUESTED,
            RECOVERY_SYNC,
            RECOVERY_USED,
            REPORT_EXPORT,
            SECURITY_KEY_UPDATE,
            STATUS_OVERRIDE,
            STATUS_TEMPLATE_ADDED,
            STATUS_TEMPLATE_REMOVED,
            STATUS_TEMPLATE_RESTORED,
            STATUS_TEMPLATE_UPDATED,
            STORAGE_FEE_APPLIED,
            STORAGE_FEE_RESUMED,
            STORAGE_JOB_FAILED,
            SUBDIVISIONS_CHANGED,
            TIMEZONE_CHANGED,
            TITLE_FIELDS_CHANGED,
            TITLE_RELEASED,
            TITLE_RELEASE_UNDONE,
            TITLE_REVERTED,
            WIPE_REFUSED);

    /** Sign-in noise: not staff work (Dashboard activity, 13.7d). */
    public static final java.util.List<String> NOT_STAFF_WORK = java.util.List.of(LOGIN_FAILED, LOGIN_BLOCKED, ACCESS_DENIED, LOGIN_SUCCESS);
}
