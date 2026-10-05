// PATH: erp-frontend/src/components/common/notificationCatalog.js
/**
 * GOLDEN SEED -- NOTIFICATION CATALOG
 *
 * WHY THIS FILE EXISTS
 *
 * Notifications were emitted from nine different places in the backend, each
 * inventing its own type string, and the bell rendered all of them as the same
 * grey row with the same coloured dot. So "a payment came in" and "this client
 * has gone silent for a year" looked identical, nothing told you WHEN, and
 * clicking anything that was not a PROJECT dumped you on the recovery page
 * whether or not that was where the thing lived.
 *
 * One registry now owns all three of those decisions per type:
 *
 *   label     what a human calls it, not the enum name
 *   group     MONEY / PIPELINE / RECOVERY / STAFF / SYSTEM -- for filtering
 *   icon      react-icons component, so the row is scannable without reading
 *   severity  the fallback when the server did not set one
 *
 * Routing is separate (routeFor) because it depends on entityType, not on the
 * notification type: a CLIENT signal goes to that client's dossier no matter
 * what raised it.
 *
 * UNKNOWN TYPES ARE NOT AN ERROR. A backend can always emit something this
 * build has not heard of, so `describe` falls back to a sensible row rather
 * than rendering blank. Anything added server-side shows up immediately and
 * only gets prettier when it is listed here.
 */
import {
    FiDollarSign, FiFilePlus, FiClock, FiArchive, FiAlertTriangle, FiPhoneCall,
    FiUnlock, FiLock, FiMapPin, FiTrendingDown, FiUserPlus, FiUserX, FiUserCheck,
    FiShield, FiKey, FiTrash2, FiRotateCcw, FiCheckCircle, FiLayers, FiUploadCloud,
    FiFlag, FiBell, FiCreditCard,
} from 'react-icons/fi';

export const GROUPS = {
    MONEY:    'MONEY',
    PIPELINE: 'PIPELINE',
    RECOVERY: 'RECOVERY',
    STAFF:    'STAFF',
    SYSTEM:   'SYSTEM',
};

export const SEVERITY_COLOR = {
    POSITIVE: 'var(--ok)',
    WARN:     'var(--warn)',
    CRITICAL: 'var(--bad)',
    INFO:     'var(--info)',
};

/* Tinted icon chips, not the same flat grey square for every row -- the
   colour is the fastest way to tell "money came in" from "something is
   overdue" without reading the label first. */
export const SEVERITY_BG = {
    POSITIVE: 'rgba(16, 185, 129, 0.16)',
    WARN:     'rgba(245, 158, 11, 0.16)',
    CRITICAL: 'rgba(239, 68, 68, 0.16)',
    INFO:     'rgba(6, 182, 212, 0.16)',
};

/* Severity alone collapses most of the catalog onto two colours -- the
   large majority of types below are either INFO or WARN, so a payment,
   a new intake and a document upload all rendered in the same cyan chip.
   GROUP gives five real colour families (money / pipeline / recovery /
   staff / system) that line up with how the bell is already filtered,
   so the tint tells you the same story the filter chips do. */
export const GROUP_COLOR = {
    MONEY:    '#22c55e',
    PIPELINE: '#38bdf8',
    RECOVERY: '#f97316',
    STAFF:    '#a78bfa',
    SYSTEM:   '#f43f5e',
};

export const GROUP_BG = {
    MONEY:    'rgba(34, 197, 94, 0.16)',
    PIPELINE: 'rgba(56, 189, 248, 0.16)',
    RECOVERY: 'rgba(249, 115, 22, 0.16)',
    STAFF:    'rgba(167, 139, 250, 0.16)',
    SYSTEM:   'rgba(244, 63, 94, 0.16)',
};

/* Ordered loosely by how often the office sees them. */
export const CATALOG = {
    /* ── money ──────────────────────────────────────────────────── */
    PAYMENT_RECORDED:      { label: 'Payment recorded',      group: GROUPS.MONEY,    icon: FiDollarSign,  severity: 'POSITIVE' },
    PAYMENT_ON_RECEIVABLE: { label: 'Payment on receivable', group: GROUPS.MONEY,    icon: FiCreditCard,  severity: 'POSITIVE' },
    STORAGE_FEE_APPLIED:   { label: 'Storage fee applied',   group: GROUPS.MONEY,    icon: FiArchive,     severity: 'INFO' },
    EXPENSE_LOGGED:        { label: 'Expense logged',        group: GROUPS.MONEY,    icon: FiTrendingDown, severity: 'INFO' },
    EXPENSE_EDITED:        { label: 'Expense corrected',     group: GROUPS.MONEY,    icon: FiTrendingDown, severity: 'WARN' },
    EXPENSE_DELETED:       { label: 'Expense deleted',       group: GROUPS.MONEY,    icon: FiTrash2,      severity: 'WARN' },
    // fix181 (17.2): new types; the server list is NotificationTypes.java (a test checks both lists match)
    PAYMENT_REVERSED:      { label: 'Payment reversed',      group: GROUPS.MONEY,    icon: FiRotateCcw,   severity: 'WARN' },
    COST_CHANGED:          { label: 'Total cost changed',    group: GROUPS.MONEY,    icon: FiDollarSign,  severity: 'WARN' },
    FEES_REDUCED:          { label: 'Storage fees reduced',  group: GROUPS.MONEY,    icon: FiArchive,     severity: 'WARN' },
    RECEIVABLE_EXIT:       { label: 'Left receivables',      group: GROUPS.MONEY,    icon: FiCheckCircle, severity: 'POSITIVE' },
    BOOKS_MISMATCH:        { label: 'Books check differs',   group: GROUPS.MONEY,    icon: FiAlertTriangle, severity: 'CRITICAL' },

    /* ── pipeline ───────────────────────────────────────────────── */
    NEW_INTAKE:            { label: 'New project',           group: GROUPS.PIPELINE, icon: FiFilePlus,    severity: 'INFO' },
    STATUS_ADVANCED:       { label: 'Status advanced',       group: GROUPS.PIPELINE, icon: FiLayers,      severity: 'POSITIVE' },
    STAGE_ADVANCED:        { label: 'Status advanced',       group: GROUPS.PIPELINE, icon: FiLayers,      severity: 'POSITIVE' },   // before fix180
    TITLE_COMPLETED:       { label: 'Title completed',       group: GROUPS.PIPELINE, icon: FiCheckCircle, severity: 'POSITIVE' },
    NEGOTIATION_DEADLINE:  { label: 'Deadline approaching',  group: GROUPS.PIPELINE, icon: FiClock,       severity: 'WARN' },
    AUTO_RECEIVABLE_365:   { label: 'Auto-flagged receivable', group: GROUPS.PIPELINE, icon: FiAlertTriangle, severity: 'WARN' },
    PROBLEM_FLAGGED:       { label: 'Flagged as a problem',  group: GROUPS.PIPELINE, icon: FiFlag,        severity: 'CRITICAL' },
    DOC_UPLOADED:          { label: 'Document attached',     group: GROUPS.PIPELINE, icon: FiUploadCloud, severity: 'INFO' },
    PROJECT_DELETED:       { label: 'Plot deleted',          group: GROUPS.PIPELINE, icon: FiTrash2,      severity: 'CRITICAL' },
    PROJECT_RESTORED:      { label: 'Plot restored',         group: GROUPS.PIPELINE, icon: FiRotateCcw,   severity: 'POSITIVE' },
    PENDING_CREATED:       { label: 'New pending project',   group: GROUPS.PIPELINE, icon: FiFilePlus,    severity: 'INFO' },
    PENDING_STALE:         { label: 'Pending project waiting', group: GROUPS.PIPELINE, icon: FiClock,     severity: 'WARN' },
    TITLE_RELEASE_UNDONE:  { label: 'Hand-over undone',      group: GROUPS.PIPELINE, icon: FiRotateCcw,   severity: 'WARN' },
    PROBLEM_CLEARED:       { label: 'Problem cleared',       group: GROUPS.PIPELINE, icon: FiCheckCircle, severity: 'POSITIVE' },
    PROJECT_GRADUATED:     { label: 'Project started',       group: GROUPS.PIPELINE, icon: FiCheckCircle, severity: 'INFO' },
    STORAGE_FEE_RESUMED:   { label: 'Storage fees running again', group: GROUPS.MONEY, icon: FiArchive,   severity: 'WARN' },

    /* ── recovery ───────────────────────────────────────────────── */
    LOCKED:                { label: 'Client resting',        group: GROUPS.RECOVERY, icon: FiLock,        severity: 'INFO' },
    UNLOCK:                { label: 'Callable again',        group: GROUPS.RECOVERY, icon: FiUnlock,      severity: 'INFO' },
    UNLOCK_M:              { label: 'Callable again',        group: GROUPS.RECOVERY, icon: FiUnlock,      severity: 'INFO' },   // old rows only (fix181)
    NIN_CONFLICT:          { label: 'NIN conflict',          group: GROUPS.RECOVERY, icon: FiAlertTriangle, severity: 'WARN' },
    SITE_VISIT_AUTO:       { label: 'Site visit needed',     group: GROUPS.RECOVERY, icon: FiMapPin,      severity: 'WARN' },
    RECOVERY_DUE:          { label: 'Recovery mission due',  group: GROUPS.RECOVERY, icon: FiPhoneCall,   severity: 'WARN' },

    /* ── staff ──────────────────────────────────────────────────── */
    STAFF_PROVISIONED:     { label: 'Operator provisioned',  group: GROUPS.STAFF,    icon: FiUserPlus,    severity: 'INFO' },
    STAFF_SUSPENDED:       { label: 'Operator suspended',    group: GROUPS.STAFF,    icon: FiUserX,       severity: 'WARN' },
    STAFF_ACTIVATED:       { label: 'Operator activated',    group: GROUPS.STAFF,    icon: FiUserCheck,   severity: 'POSITIVE' },
    STAFF_ROLE_CHANGED:    { label: 'Rank changed',          group: GROUPS.STAFF,    icon: FiShield,      severity: 'WARN' },
    KEY_RESET:             { label: 'Security key reset',    group: GROUPS.STAFF,    icon: FiKey,         severity: 'WARN' },

    /* ── system ─────────────────────────────────────────────────── */
    SYSTEM_WIPE:           { label: 'System wiped',          group: GROUPS.SYSTEM,   icon: FiAlertTriangle, severity: 'CRITICAL' },
    LOGIN_BLOCKED:         { label: 'Sign-in paused',        group: GROUPS.SYSTEM,   icon: FiLock,        severity: 'WARN' },
    JOB_FAILED:            { label: 'Night job problem',     group: GROUPS.SYSTEM,   icon: FiAlertTriangle, severity: 'CRITICAL' },
};

const FALLBACK = { label: 'System signal', group: GROUPS.SYSTEM, icon: FiBell, severity: 'INFO' };

/**
 * Describe a notification for rendering. Never throws and never returns a
 * blank row -- an unrecognised type is titled from its own enum name so a new
 * backend signal is still readable before it is added above.
 */
export const describe = (n) => {
    const entry = CATALOG[n?.type];
    if (entry) {
        return { ...entry, severity: n.severity || entry.severity };
    }
    const pretty = String(n?.type || 'SIGNAL')
        .replace(/_/g, ' ')
        .toLowerCase()
        .replace(/^./, c => c.toUpperCase());
    // fix181 (17.19b): an unknown type keeps the group the server sends (not always a red SYSTEM signal)
    const group = n?.category && Object.values(GROUPS).includes(n.category) ? n.category : FALLBACK.group;
    return { ...FALLBACK, group, label: pretty, severity: n?.severity || FALLBACK.severity };
};

/**
 * Where a notification should take you.
 *
 * Driven by entityType, not by type: whatever raised it, a CLIENT signal
 * belongs on that client's dossier and a PROJECT signal on that folder. The
 * old code only understood PROJECT and sent everything else to /recovery,
 * which is why a "callable again" signal about a named client dropped you on
 * a list you then had to search.
 */
export const routeFor = (n) => {
    if (!n) return '/dashboard';
    if (n.entityId) {
        if (n.entityType === 'PROJECT') return '/folder/' + n.entityId;
        if (n.entityType === 'CLIENT')  return '/client/' + n.entityId;
        if (n.entityType === 'EXPENSE') return '/financials';
        if (n.entityType === 'STAFF')   return '/settings';
    }
    const group = describe(n).group;
    if (group === GROUPS.MONEY)    return '/payments';
    if (group === GROUPS.RECOVERY) return '/recovery';
    if (group === GROUPS.STAFF)    return '/settings';
    return '/dashboard';
};

/**
 * "2 min ago" beats a timestamp in a dropdown you are scanning, but only up
 * to about a day -- past that the actual date is the more useful fact.
 */
export const relativeTime = (iso) => {
    if (!iso) return '';
    const then = new Date(iso).getTime();
    if (!Number.isFinite(then)) return '';
    const secs = Math.floor((Date.now() - then) / 1000);
    if (secs < 45)    return 'just now';
    if (secs < 3600)  return Math.floor(secs / 60) + ' min ago';
    if (secs < 86400) return Math.floor(secs / 3600) + ' hr ago';
    if (secs < 172800) return 'yesterday';
    return new Date(iso).toLocaleDateString();
};

// fix181 (21.9): the old FILTERS list was removed; the bell builds its own group chips from GROUPS.

export default CATALOG;
