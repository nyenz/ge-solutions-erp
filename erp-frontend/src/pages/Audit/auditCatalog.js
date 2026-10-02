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
            { code: 'STORAGE_FEES_ADJUSTED',     label: 'Storage fees adjusted',   severity: 'high' },
            { code: 'STORAGE_RATE_CHANGED',      label: 'Storage rate changed',    severity: 'high' },
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
            { code: 'RECEIVABLE_START_OVERRIDDEN',   label: 'Receivable start override', severity: 'high' },
            { code: 'ROOT_RECOVERY_TRIGGERED',       label: 'Root recovery triggered',   severity: 'high' },
        ],
    },
    {
        group: 'PIPELINE',
        actions: [
            { code: 'STATUS_OVERRIDE',                 label: 'Status override',         severity: 'high' },
            { code: 'PROJECT_STATUS_CHANGED',          label: 'Status ticked / unticked', severity: 'med' },
            { code: 'PROJECT_STATUS_COST_UPDATED',     label: 'Status cost updated',     severity: 'med'  },
            { code: 'PROJECT_STATUS_REMOVED',          label: 'Status removed',          severity: 'high' },
            { code: 'PROJECT_STATUSES_ATTACHED',       label: 'Statuses attached',       severity: 'low'  },
            { code: 'PROJECT_STATUSES_REORDERED',      label: 'Statuses reordered',      severity: 'low'  },
            { code: 'PROJECT_STATUSES_RESTORED',       label: 'Statuses restored',       severity: 'med'  },
            { code: 'STATUS_TEMPLATE_ADDED',           label: 'Template status added',   severity: 'med'  },
            { code: 'STATUS_TEMPLATE_UPDATED',         label: 'Template status updated', severity: 'med'  },
            { code: 'STATUS_TEMPLATE_REMOVED',         label: 'Template status removed', severity: 'high' },
            { code: 'STATUS_TEMPLATE_RESTORED',        label: 'Template statuses restored', severity: 'med' },
            { code: 'SUBDIVISIONS_CHANGED',            label: 'Subdivisions changed',    severity: 'med'  },
            { code: 'CLIENTS_CHANGED',                 label: 'Clients changed',         severity: 'med'  },
            // written before fix180 (Stage was renamed Status); kept so old audit lines still read well
            { code: 'STAGE_OVERRIDE',                  label: 'Status override (old)',   severity: 'high' },
            { code: 'PROJECT_STAGE_STATUS_CHANGED',    label: 'Status changed (old)',    severity: 'med'  },
            { code: 'PROJECT_STAGE_COST_UPDATED',      label: 'Status cost updated (old)', severity: 'med' },
            { code: 'PROJECT_STAGE_REMOVED',           label: 'Status removed (old)',    severity: 'high' },
            { code: 'PROJECT_STAGES_ATTACHED',         label: 'Statuses attached (old)', severity: 'low'  },
            { code: 'PROJECT_STAGES_REORDERED',        label: 'Statuses reordered (old)', severity: 'low' },
            { code: 'PROJECT_STAGES_RESTORED',         label: 'Statuses restored (old)', severity: 'med'  },
            { code: 'STAGE_TEMPLATE_ADDED',            label: 'Template status added (old)', severity: 'med' },
            { code: 'STAGE_TEMPLATE_UPDATED',          label: 'Template status updated (old)', severity: 'med' },
            { code: 'STAGE_TEMPLATE_REMOVED',          label: 'Template status removed (old)', severity: 'high' },
            { code: 'TITLE_RELEASED',                  label: 'Title released',         severity: 'med'  },
            { code: 'BULK_TITLE_PRODUCED',             label: 'Bulk titles produced',   severity: 'med'  },
            { code: 'NEGOTIATION_DEADLINE_SET',        label: 'Deadline set',           severity: 'low'  },
            { code: 'NEGOTIATION_DEADLINE_CLEARED',    label: 'Deadline cleared',       severity: 'low'  },
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
        ],
    },
    {
        group: 'ACCESS & STAFF',
        actions: [
            { code: 'LOGIN_SUCCESS',            label: 'Sign in',              severity: 'low'  },
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
