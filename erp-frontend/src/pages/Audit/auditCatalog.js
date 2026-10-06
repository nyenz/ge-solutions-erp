// PATH: erp-frontend/src/pages/Audit/auditCatalog.js
/**
 * GOLDEN SEED -- AUDIT ACTION CATALOG
 *
 * THE BUG THIS FILE FIXES
 *
 * The audit page shipped a six-entry filter dropdown and an eleven-entry
 * friendly-name map, both written by hand, and three of those entries named
 * actions the backend does not emit:
 *
 *   'RECOVERY_MISSION_COMPLETE'  the server writes RECOVERY_NOTE
 *   'MASTER_REWRITE'             the server writes RECORD_UPDATED
 *   'NUCLEAR_PURGE'              the server writes RECORD_DELETED
 *
 * So picking "CALL LOG" from the filter sent a query for a string that has
 * never existed in the table and came back empty every time, and the three
 * most important rows in the log rendered under their raw enum names.
 *
 * Meanwhile the backend emits FIFTY-FOUR distinct actions. Forty-eight of them
 * were unfilterable: there was no way to ask "show me every document deletion"
 * or "every storage-rate change", which is most of what an audit trail is for.
 *
 * This catalog is generated from the real logAction() call sites. Grouping is
 * what makes fifty-four usable in one dropdown -- the filter renders it as
 * optgroups rather than one flat list.
 *
 * severity drives the colour stripe on the row:
 *   high    destructive or privileged -- deletions, overrides, rank changes
 *   med     changes money or a record
 *   intel   contact history, worth reading but not alarming
 *   low     everything else
 */

export const ACTION_GROUPS = [
    {
        group: 'RECORDS',
        actions: [
            { code: 'INTAKE',            label: 'New project',            severity: 'med'  },
            { code: 'RECORD_UPDATED',    label: 'Record edited',          severity: 'med'  },
            { code: 'RECORD_DELETED',    label: 'Record deleted',         severity: 'high' },
            { code: 'RECORD_RESTORED',   label: 'Record restored',        severity: 'high' },
            { code: 'EDIT_MODE_OPENED',  label: 'Edit mode opened',       severity: 'low'  },
            { code: 'PROBLEM_FLAG',      label: 'Problem flag toggled',   severity: 'med'  },
            { code: 'CLIENT_ARCHIVE',    label: 'Client archived',        severity: 'high' },
            // fix181 (10.2, 10.10)
            { code: 'PENDING_CREATED',   label: 'Pending project entered (Employee)', severity: 'med' },
            { code: 'PENDING_UPDATED',   label: 'Pending project edited',  severity: 'low'  },
            { code: 'PROJECT_GRADUATED', label: 'Pending project started (prices set)', severity: 'med' },
            { code: 'PROJECT_NUMBERS_CHANGED', label: 'Invoice / contract number set or corrected', severity: 'med' },
            { code: 'PROJECT_PENDING_REJECTED', label: 'Pending project rejected', severity: 'high' },
            { code: 'OWNERS_CHANGED',    label: 'Owners changed',         severity: 'med'  },
            { code: 'CLIENT_UPDATED',    label: 'Client details edited',  severity: 'med'  },
            { code: 'CLIENT_NIN_CORRECTED', label: 'Client NIN corrected', severity: 'high' },
        ],
    },
    {
        group: 'MONEY',
        actions: [
            { code: 'PAYMENT_RECORDED',          label: 'Payment recorded',        severity: 'med'  },
            { code: 'EXPENSE_LOGGED',            label: 'Expense logged',          severity: 'med'  },
            { code: 'EXPENSE_EDITED',            label: 'Expense corrected',       severity: 'med'  },
            { code: 'EXPENSE_DELETED',           label: 'Expense deleted',         severity: 'high' },
            { code: 'EXPENSE_PRESET_CREATED',    label: 'Expense preset added',    severity: 'low'  },
            { code: 'FEES_WAIVED',               label: 'Fees waived',             severity: 'high' },
            { code: 'FEES_CAPITALIZED',          label: 'Fees capitalised',        severity: 'med'  },
            { code: 'STORAGE_FEE_APPLIED',       label: 'Storage fee applied',     severity: 'low'  },
            // fix181 (10.2): written by the server but missing from this list before
            { code: 'PAYMENT_REVERSED',          label: 'Payment reversed',        severity: 'high' },
            { code: 'COST_CHANGED',              label: 'Total cost changed',      severity: 'high' },
            { code: 'FEES_REDUCED',              label: 'Storage fees reduced',    severity: 'high' },
            { code: 'STORAGE_FEE_RESUMED',       label: 'Storage fees resumed',    severity: 'med'  },
            { code: 'BOOKS_MISMATCH',            label: 'Books check found a difference', severity: 'high' },
            // written only by the old demo seeder or old rows (the real code is RECEIVABLE_SETTINGS); kept so old lines read well
            { code: 'STORAGE_FEES_ADJUSTED',     label: 'Storage fees adjusted (old)', severity: 'high' },
            { code: 'STORAGE_RATE_CHANGED',      label: 'Storage rate changed (old)',  severity: 'high' },
        ],
    },
    {
        group: 'RECEIVABLES',
        actions: [
            { code: 'RECEIVABLE_ENTER',              label: 'Entered receivables',       severity: 'med'  },
            { code: 'RECEIVABLE_EXIT',               label: 'Left receivables',          severity: 'med'  },
            { code: 'AUTO_RECEIVABLE',               label: 'Auto-flagged receivable',   severity: 'med'  },
            { code: 'RECEIVABLE_TRIGGER',            label: 'Receivable trigger fired',  severity: 'low'  },
            { code: 'RECEIVABLE_SET_ASIDE',          label: 'Receivable set aside',      severity: 'high' },
            { code: 'RECEIVABLE_SETTINGS',           label: 'Receivable settings',       severity: 'high' },
            // written only by the old demo seeder or old rows (the real code is RECEIVABLE_SETTINGS)
            { code: 'RECEIVABLE_START_OVERRIDDEN',   label: 'Receivable start override (old)', severity: 'high' },
            { code: 'STORAGE_JOB_FAILED',            label: 'Nightly storage-fee job failed', severity: 'high' },
            { code: 'AUTO_RECEIVABLE_FAILED',        label: 'Nightly receivables job failed', severity: 'high' },
        ],
    },
    {
        group: 'PIPELINE',
        actions: [
            { code: 'STATUS_OVERRIDE',                 label: 'Stage override',         severity: 'high' },
            { code: 'PROJECT_STATUS_CHANGED',          label: 'Stage ticked / unticked', severity: 'med' },
            { code: 'PROJECT_STATUS_COST_UPDATED',     label: 'Stage cost updated',     severity: 'med'  },
            { code: 'PROJECT_STATUS_REMOVED',          label: 'Stage removed',          severity: 'high' },
            { code: 'PROJECT_STATUSES_ATTACHED',       label: 'Stages attached',       severity: 'low'  },
            { code: 'PROJECT_STATUSES_REORDERED',      label: 'Stages reordered',      severity: 'low'  },
            { code: 'PROJECT_STATUSES_RESTORED',       label: 'Stages restored',       severity: 'med'  },
            { code: 'STATUS_TEMPLATE_ADDED',           label: 'Template stage added',   severity: 'med'  },
            { code: 'STATUS_TEMPLATE_UPDATED',         label: 'Template stage updated', severity: 'med'  },
            { code: 'STATUS_TEMPLATE_REMOVED',         label: 'Template stage removed', severity: 'high' },
            { code: 'STATUS_TEMPLATE_RESTORED',        label: 'Template stages restored', severity: 'med' },
            { code: 'SUBDIVISIONS_CHANGED',            label: 'Subdivisions changed',    severity: 'med'  },
            { code: 'CLIENTS_CHANGED',                 label: 'Clients changed',         severity: 'med'  },
            // written before fix180 (Stage was renamed Status); kept so old audit lines still read well
            { code: 'STAGE_OVERRIDE',                  label: 'Stage override (old)',   severity: 'high' },
            { code: 'PROJECT_STAGE_STATUS_CHANGED',    label: 'Stage changed (old)',    severity: 'med'  },
            { code: 'PROJECT_STAGE_COST_UPDATED',      label: 'Stage cost updated (old)', severity: 'med' },
            { code: 'PROJECT_STAGE_REMOVED',           label: 'Stage removed (old)',    severity: 'high' },
            { code: 'PROJECT_STAGES_ATTACHED',         label: 'Stages attached (old)', severity: 'low'  },
            { code: 'PROJECT_STAGES_REORDERED',        label: 'Stages reordered (old)', severity: 'low' },
            { code: 'PROJECT_STAGES_RESTORED',         label: 'Stages restored (old)', severity: 'med'  },
            { code: 'STAGE_TEMPLATE_ADDED',            label: 'Template stage added (old)', severity: 'med' },
            { code: 'STAGE_TEMPLATE_UPDATED',          label: 'Template stage updated (old)', severity: 'med' },
            { code: 'STAGE_TEMPLATE_REMOVED',          label: 'Template stage removed (old)', severity: 'high' },
            { code: 'TITLE_RELEASED',                  label: 'Title released',         severity: 'med'  },
            { code: 'TITLE_RELEASE_UNDONE',            label: 'Title release undone',   severity: 'high' },
            { code: 'TITLE_REVERTED',                  label: 'Title reverted',         severity: 'high' },
            { code: 'TITLE_FIELDS_CHANGED',            label: 'Title details changed',  severity: 'med'  },
            { code: 'BULK_TITLE_PRODUCED',             label: 'Bulk titles produced',   severity: 'med'  },
            // written only by the old demo seeder or old rows (the real code is RECEIVABLE_SETTINGS)
            { code: 'NEGOTIATION_DEADLINE_SET',        label: 'Deadline set (old)',     severity: 'low'  },
            { code: 'NEGOTIATION_DEADLINE_CLEARED',    label: 'Deadline cleared (old)', severity: 'low'  },
        ],
    },
    {
        group: 'CONTACT & NOTES',
        actions: [
            { code: 'RECOVERY_NOTE',          label: 'Call logged',        severity: 'intel' },
            { code: 'RECOVERY_NOTE_DELETED',  label: 'Call log deleted',   severity: 'high'  },
            { code: 'RECOVERY_SYNC',          label: 'Recovery sync',      severity: 'intel' },
            { code: 'NOTE_ADDED',             label: 'Note added',         severity: 'intel' },
            { code: 'NOTE_UPDATED',           label: 'Note edited',        severity: 'intel' },
            { code: 'NOTE_DELETED',           label: 'Note deleted',       severity: 'high'  },
        ],
    },
    {
        group: 'DOCUMENTS',
        actions: [
            { code: 'DOCUMENT_UPLOADED', label: 'Document uploaded', severity: 'low'  },
            { code: 'DOCUMENT_DELETED',  label: 'Document deleted',  severity: 'high' },
            { code: 'DOCUMENT_CATEGORY_ADDED', label: 'Document category added', severity: 'low' },
            { code: 'REPORT_EXPORT',     label: 'Report exported',   severity: 'low'  },
            { code: 'AUDIT_EXPORT',      label: 'Audit trail exported', severity: 'med' },
        ],
    },
    {
        group: 'ACCESS & STAFF',
        actions: [
            { code: 'LOGIN_SUCCESS',            label: 'Sign in',              severity: 'low'  },
            { code: 'LOGIN_FAILED',             label: 'Wrong sign-in',        severity: 'med'  },
            { code: 'LOGIN_BLOCKED',            label: 'Sign-in paused (too many tries)', severity: 'high' },
            { code: 'ACCESS_DENIED',            label: 'Access refused',       severity: 'med'  },
            { code: 'RECOVERY_REQUESTED',       label: 'Key recovery requested', severity: 'high' },
            { code: 'RECOVERY_USED',            label: 'Admin key recovery used', severity: 'high' },
            { code: 'ROOT_RECOVERY_TRIGGERED',  label: 'Root recovery triggered (old)', severity: 'high' },
            { code: 'DATA_WIPED',               label: 'All business data wiped', severity: 'high' },
            { code: 'WIPE_REFUSED',             label: 'Wipe refused',         severity: 'high' },
            { code: 'TIMEZONE_CHANGED',         label: 'Server time zone changed', severity: 'med' },
            { code: 'NOTIFICATIONS_CLEANED',    label: 'Old alerts cleaned up', severity: 'low' },
            { code: 'AUDIT_REPAIRED',           label: 'Old audit lines repaired', severity: 'high' },
            { code: 'OPERATOR_PROVISIONED',     label: 'Operator provisioned', severity: 'high' },
            { code: 'OPERATOR_STATUS_CHANGE',   label: 'Operator suspended / activated', severity: 'high' },
            { code: 'RANK_ADJUSTMENT',          label: 'Rank changed',         severity: 'high' },
            { code: 'CREDENTIAL_RESET',         label: 'Key reset',            severity: 'high' },
            { code: 'SECURITY_KEY_UPDATE',      label: 'Key changed',          severity: 'med'  },
        ],
    },
];

/* Flat lookup built once from the groups above -- there is exactly one source
   of truth for a code's label and severity, and it is the list. */
const INDEX = {};
ACTION_GROUPS.forEach(g => g.actions.forEach(a => { INDEX[a.code] = a; }));

export const ALL_ACTION = '__ALL__';

/**
 * An unlisted code still renders readably: the raw enum is title-cased rather
 * than shown as PROJECT_STAGE_COST_UPDATED. A new backend action is therefore
 * never invisible, it is just not yet pretty.
 */
export const friendlyAction = (code) => {
    const hit = INDEX[code];
    if (hit) return hit.label;
    return String(code || 'Unknown')
        .replace(/_/g, ' ')
        .toLowerCase()
        .replace(/^./, c => c.toUpperCase());
};

export const severityOf = (code) => (INDEX[code]?.severity) || 'low';

/** fix181 (10.1, 10.8): the codes of one group (the Audit filter and Report Studio send these lists to the server). */
export const codesOfGroup = (group) => (ACTION_GROUPS.find(g => g.group === group)?.actions || []).map(a => a.code);

/* fix181 (10.8, 13.0f): the explicit code lists of the COMPANY reports (one source of truth). */
export const REPORT_CODES = {
    DELETIONS_RESTORES: ['RECORD_DELETED', 'RECORD_RESTORED', 'DOCUMENT_DELETED', 'NOTE_DELETED', 'EXPENSE_DELETED',
        'RECOVERY_NOTE_DELETED', 'PAYMENT_REVERSED', 'PROJECT_PENDING_REJECTED'],
    STORAGE_OVERRIDES: ['RECEIVABLE_SETTINGS', 'FEES_REDUCED', 'FEES_WAIVED', 'FEES_CAPITALIZED', 'STORAGE_FEE_RESUMED',
        'RECEIVABLE_SET_ASIDE', 'STORAGE_FEES_ADJUSTED', 'STORAGE_RATE_CHANGED', 'RECEIVABLE_START_OVERRIDDEN'],
    STATUS_MOVES: ['STATUS_OVERRIDE', 'PROJECT_STATUS_CHANGED', 'PROJECT_STATUS_COST_UPDATED', 'PROJECT_STATUS_REMOVED',
        'STAGE_OVERRIDE', 'PROJECT_STAGE_STATUS_CHANGED', 'PROJECT_STAGE_COST_UPDATED', 'PROJECT_STAGE_REMOVED'],
    LOGINS: ['LOGIN_SUCCESS'],
};


/* fix160: colour by GROUP. Six basic colours, one per family of actions:
   blue   = RECORDS + DOCUMENTS   green  = MONEY          orange = RECEIVABLES
   purple = PIPELINE              yellow = CONTACT & NOTES  red    = ACCESS & STAFF
   An unlisted code is neutral grey. */
const GROUP_COLOR = {
    'RECORDS':         '#2563eb',
    'DOCUMENTS':       '#2563eb',
    'MONEY':           '#16a34a',
    'RECEIVABLES':     '#f97316',
    'PIPELINE':        '#9333ea',
    'CONTACT & NOTES': '#eab308',
    'ACCESS & STAFF':  '#dc2626',
};
const GROUP_OF = {};
ACTION_GROUPS.forEach(g => g.actions.forEach(a => { GROUP_OF[a.code] = g.group; }));
export const actionColor = (code) => GROUP_COLOR[GROUP_OF[String(code || '')]] || '#6b7280';

export default ACTION_GROUPS;
