// PATH: erp-frontend/src/pages/Reports/reportData.js
/**
 * GOLDEN SEED -- THE REPORT STUDIO DATA LAYER
 *
 * The canned CSV pillars answer twelve fixed questions. This answers any
 * question, because the shape of the question is the user's to decide: pick a
 * dataset, filter it down as far as you like, choose which columns you want,
 * group it, measure it, compare one slice against another.
 *
 * It runs entirely in the browser on data the app already serves. There is no
 * new backend endpoint and no new query language to get wrong: four list
 * endpoints are pulled once, cached, and everything after that is local. That
 * also means a filter or a grouping is instant and costs nothing, which is the
 * only way an explore-it-yourself tool is usable at all.
 *
 * ROLE RULES ARE ENFORCED IN TWO PLACES, deliberately. The server already
 * refuses the financial endpoints to non-directors -- that is the real
 * boundary. What happens here is the second half: a dataset marked
 * `restricted` and a field marked `money` are never offered to a user without
 * financial access, so a manager is not shown a column that would just come
 * back empty or 403.
 *
 * ADDING A FIELD: add one entry to the dataset's `fields` array. Filters,
 * columns, grouping, measures, comparison and CSV all read from that array, so
 * nothing else needs touching.
 */
import api from '../../api/axios';
import landService from '../../services/landService';
import recoveryService from '../../services/recoveryService';
import expenseService from '../../services/expenseService';
import auditService from '../../services/auditService';

/* ── value helpers ───────────────────────────────────────────────── */
export const num = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
};
export const fmtMoney = (v) => 'UGX ' + num(v).toLocaleString();
export const fmtNum = (v) => num(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
export const fmtDate = (v) => (v ? new Date(v).toLocaleDateString() : '---');

const daysSince = (v) => {
    if (!v) return null;
    const t = new Date(v).getTime();
    if (!Number.isFinite(t)) return null;
    return Math.floor((Date.now() - t) / 86400000);
};
const monthKey = (v) => {
    if (!v) return '---';
    const d = new Date(v);
    if (Number.isNaN(d.getTime())) return '---';
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
};

export const formatValue = (value, type) => {
    if (value === null || value === undefined || value === '') return '---';
    if (type === 'money') return fmtMoney(value);
    if (type === 'number') return fmtNum(value);
    if (type === 'percent') return fmtNum(value) + '%';
    if (type === 'date') return fmtDate(value);
    if (type === 'bool') return value ? 'YES' : 'NO';
    return String(value);
};

const f = (key, label, type, get, extra) => ({ key, label, type, get, ...(extra || {}) });

/* ── PROJECTS ────────────────────────────────────────────────────── */
const projectFields = [
    f('index', 'Project Index', 'text', p => p.projectIndex || ''),
    f('plot', 'Plot Number', 'text', p => p.landTitle?.plotNumber || ''),
    f('titleId', 'Title ID', 'text', p => p.landTitle?.titleId || ''),
    f('tenure', 'Tenure', 'text', p => p.landTitle?.tenure || ''),
    f('blockRoad', 'Block / Road', 'text', p => p.landTitle?.blockRoad || ''),
    f('district', 'District', 'text', p => p.district || ''),
    f('county', 'County', 'text', p => p.county || ''),
    f('subCounty', 'Sub-County', 'text', p => p.subCounty || ''),
    f('parish', 'Parish', 'text', p => p.parish || ''),
    f('village', 'Village', 'text', p => p.village || ''),
    f('area', 'Area', 'text', p => p.area || ''),
    f('entryMode', 'Entry Mode', 'text', p => (p.isLegacy ? 'Legacy Title' : (p.landTitle ? 'New Title' : 'New Folder'))),
  f('startMonth', 'Start Month', 'text', p => monthKey(p.projectStartDate)),
  f('owner', 'Primary Owner', 'text', p => p.proprietors?.[0]?.fullName || ''),
    f('ownerPhone', 'Owner Phone', 'text', p => p.proprietors?.[0]?.phoneNumber || ''),
    f('ownerNin', 'Owner NIN', 'text', p => p.proprietors?.[0]?.nationalId || ''),
    f('ownerAddress', 'Owner Address', 'text', p => p.proprietors?.[0]?.homeAddress || ''),
    f('allOwners', 'All Owners', 'text', p => (p.proprietors || []).map(o => o.fullName).join(', ')),
    f('ownerCount', 'Owner Count', 'number', p => (p.proprietors || []).length),
    f('ownership', 'Ownership', 'text', p => ((p.proprietors || []).length > 1 ? 'JOINT' : 'SOLO')),
    f('status', 'Status', 'text', p => p.status || ''),
    f('stage', 'Stage Index', 'number', p => num(p.currentStageIndex)),
    f('planType', 'Plan Type', 'text', p => p.planType || ''),
    f('titled', 'Has Title', 'bool', p => !!p.landTitle),
    f('released', 'Title Released', 'bool', p => !!p.landTitle?.isReleased),
    f('legacy', 'Legacy', 'bool', p => !!p.isLegacy),
    f('receivable', 'In Receivables', 'bool', p => !!p.isReceivable),
    f('problem', 'Flagged Problem', 'bool', p => !!p.problem),
    f('startDate', 'Project Start', 'date', p => p.projectStartDate || null),
    f('lastPayment', 'Last Payment', 'date', p => p.lastPaymentDate || null),
    f('daysSincePayment', 'Days Since Payment', 'number', p => daysSince(p.lastPaymentDate)),
    f('receivableStart', 'Receivables Start', 'date', p => p.receivableStartDate || null),
    f('totalCost', 'Total Cost', 'money', p => num(p.totalCost), { money: true }),
    f('amountPaid', 'Amount Paid', 'money', p => num(p.amountPaid), { money: true }),
    f('balance', 'Balance Owed', 'money', p => Math.max(0, num(p.totalCost) - num(p.amountPaid)), { money: true }),
    f('storage', 'Storage Fees', 'money', p => num(p.storageFeesAccumulated), { money: true }),
    f('originalDebt', 'Original Debt', 'money', p => num(p.originalDebt), { money: true }),
    f('installment', 'Weekly Installment', 'money', p => num(p.weeklyInstallment), { money: true }),
    f('pctPaid', 'Percent Paid', 'percent', p => (num(p.totalCost) > 0 ? Math.round((num(p.amountPaid) / num(p.totalCost)) * 100) : 0), { money: true }),
];

/* ── CLIENTS ─────────────────────────────────────────────────────── */
const clientFields = [
    f('name', 'Client Name', 'text', c => c.name || ''),
    f('nin', 'NIN', 'text', c => c.nin || ''),
    f('phone', 'Phone', 'text', c => c.phone || ''),
    f('email', 'Email', 'text', c => c.email || ''),
    f('plotCount', 'Projects', 'number', c => num(c.plotCount)),
    f('districts', 'Districts', 'text', c => [...new Set((c.plots || []).map(p => p.district).filter(Boolean))].join(', ')),
    f('receivables', 'Has Receivables', 'bool', c => (c.plots || []).some(p => p.receivable)),
    f('lastContact', 'Last Contact', 'date', c => c.lastContact || null),
    f('daysSinceContact', 'Days Since Contact', 'number', c => daysSince(c.lastContact)),
    f('lastPaymentAt', 'Last Payment', 'date', c => c.lastPaymentAt || null),
    f('daysSincePayment', 'Days Since Payment', 'number', c => daysSince(c.lastPaymentAt)),
    f('lastTag', 'Last Call Tag', 'text', c => c.lastTag || ''),
    f('lastTone', 'Last Call Tone', 'text', c => c.lastTone || ''),
    f('owed', 'Total Owed', 'money', c => num(c.owed), { money: true }),
    f('paid', 'Total Paid', 'money', c => num(c.paid), { money: true }),
    f('storage', 'Storage Fees', 'money', c => num(c.storage), { money: true }),
    f('billed', 'Total Billed', 'money', c => num(c.owed) + num(c.paid), { money: true }),
    f('pctPaid', 'Percent Paid', 'percent', c => {
        const total = num(c.owed) + num(c.paid);
        return total > 0 ? Math.round((num(c.paid) / total) * 100) : 0;
    }, { money: true }),
];

/* ── PAYMENTS ────────────────────────────────────────────────────── */
const PAYMENT_TYPE_LABELS = {
    STANDARD: 'Title Payment',
    INITIAL_DEPOSIT: 'Initial Deposit',
    RECEIVABLE_PARTIAL: 'Receivables Payment',
};
const paymentFields = [
    f('date', 'Date', 'date', p => p.timestamp || null),
    f('month', 'Month', 'text', p => monthKey(p.timestamp)),
    f('year', 'Year', 'text', p => (p.timestamp ? String(new Date(p.timestamp).getFullYear()) : '---')),
    f('plot', 'Plot', 'text', p => p.plotNumber || ''),
    f('owner', 'Owner', 'text', p => p.ownerName || ''),
    f('type', 'Payment Type', 'text', p => PAYMENT_TYPE_LABELS[p.paymentType] || p.paymentType || ''),
    f('recordedBy', 'Recorded By', 'text', p => p.recordedBy || ''),
    f('notes', 'Notes', 'text', p => p.notes || ''),
    f('amount', 'Amount Paid', 'money', p => num(p.amountPaid), { money: true }),
    f('balanceAfter', 'Balance After', 'money', p => num(p.balanceAfter), { money: true }),
    f('daysAgo', 'Days Ago', 'number', p => daysSince(p.timestamp)),
];

/* ── EXPENSES ────────────────────────────────────────────────────── */
const expenseFields = [
    f('date', 'Date', 'date', e => e.createdAt || null),
    f('month', 'Month', 'text', e => monthKey(e.createdAt)),
    f('category', 'Category', 'text', e => e.category || ''),
    f('recordedBy', 'Logged By', 'text', e => e.recordedBy || ''),
    f('spentBy', 'Spent By', 'text', e => e.spentBy || e.recordedBy || ''),
    f('note', 'Note', 'text', e => e.note || ''),
    f('edited', 'Edited', 'bool', e => !!e.editedAt),
    f('amount', 'Amount', 'money', e => num(e.amount), { money: true }),
    f('daysAgo', 'Days Ago', 'number', e => daysSince(e.createdAt)),
];
/* ── COMPANY (audit ledger) ─────────────────────────────────────── */
const companyFields = [
  f('timestamp', 'Timestamp', 'date', a => a.timestamp || null),
  f('month', 'Month', 'text', a => monthKey(a.timestamp)),
  f('operator', 'Operator', 'text', a => a.performedBy || ''),
  f('action', 'Action', 'text', a => a.action || ''),
  f('details', 'Details', 'text', a => a.details || ''),
];

/* ── dataset registry ────────────────────────────────────────────── */
export const DATASETS = {
    PROJECTS: {
        key: 'PROJECTS',
        label: 'Projects',
        blurb: 'Every land project: location, owners, stage, and the money against it.',
        restricted: false,
        fields: projectFields,
        defaultColumns: ['index', 'plot', 'district', 'owner', 'status', 'totalCost', 'amountPaid', 'balance'],
        load: async () => {
            // The ledger endpoint is paged. A report has to see all of it, not
            // page one, so this walks until a short page comes back.
            const out = [];
            const SIZE = 200;
            for (let page = 0; page < 60; page += 1) {
                const data = await landService.getGlobalLedger(page, SIZE);
                const rows = data?.content || [];
                out.push(...rows);
                if (rows.length < SIZE) break;
            }
            return out;
        },
    },
    CLIENTS: {
        key: 'CLIENTS',
        label: 'Clients',
        blurb: 'Every registered client with their portfolio totals and call history.',
        restricted: false,
        fields: clientFields,
        defaultColumns: ['name', 'phone', 'plotCount', 'districts', 'owed', 'paid', 'lastContact'],
        load: async () => (await recoveryService.getClientLedger()) || [],
    },
    PAYMENTS: {
        key: 'PAYMENTS',
        label: 'Payments',
        blurb: 'Every cash payment ever recorded, with who recorded it.',
        restricted: true,
        fields: paymentFields,
        defaultColumns: ['date', 'plot', 'owner', 'type', 'amount', 'recordedBy'],
        load: async () => (await api.get('/recovery/payments/all')).data || [],
    },
    EXPENSES: {
        key: 'EXPENSES',
        label: 'Expenses',
        blurb: 'Every shilling logged as leaving the office, by category and by staff.',
        restricted: true,
        fields: expenseFields,
        defaultColumns: ['date', 'category', 'amount', 'recordedBy', 'spentBy'],
        load: async () => {
            const data = await expenseService.search({}, 0, 5000);
            return data?.content || data || [];
        },
    },
};

companyFields = [
  f('timestamp', 'Timestamp', 'date', a => a.timestamp || null),
  f('month', 'Month', 'text', a => monthKey(a.timestamp)),
  f('operator', 'Operator', 'text', a => a.performedBy || ''),
  f('action', 'Action', 'text', a => a.action || ''),
  f('details', 'Details', 'text', a => a.details || ''),
];
DATASETS.COMPANY = {
  key: 'COMPANY',
  label: 'Company',
  blurb: 'Every staff action in the audit ledger: logins, edits, deletes, overrides, stage moves.',
  restricted: true,
  entityTypes: { OPERATOR: 'Operator' },
  dateField: 'Timestamp',
  fields: companyFields,
    dateField: 'Timestamp',
  defaultColumns: ['timestamp', 'operator', 'action', 'details'],
  load: async () => {
    const out = [];
    for (let page = 0; page < 40; page += 1) {
      const data = await auditService.getRawStream(page, 200);
      const rows = data?.content || [];
      out.push(...rows);
      if (rows.length < 200) break;
    }
    return out;
  },
};
export const datasetsFor = (canSeeMoney) =>
    Object.values(DATASETS).filter(d => canSeeMoney || !d.restricted);

export const fieldsFor = (dataset, canSeeMoney) =>
    (dataset?.fields || []).filter(fld => canSeeMoney || !fld.money);

export const fieldByKey = (dataset, key) => (dataset?.fields || []).find(fld => fld.key === key);

/* ── filtering ───────────────────────────────────────────────────── */
export const OPERATORS = {
    text: [
        { key: 'contains', label: 'contains', value: true },
        { key: 'notContains', label: 'does not contain', value: true },
        { key: 'is', label: 'is exactly', value: true },
        { key: 'isNot', label: 'is not', value: true },
        { key: 'startsWith', label: 'starts with', value: true },
        { key: 'empty', label: 'is empty', value: false },
        { key: 'notEmpty', label: 'is not empty', value: false },
    ],
    number: [
        { key: 'eq', label: '=', value: true },
        { key: 'ne', label: '!=', value: true },
        { key: 'gt', label: '>', value: true },
        { key: 'gte', label: '>=', value: true },
        { key: 'lt', label: '<', value: true },
        { key: 'lte', label: '<=', value: true },
        { key: 'between', label: 'between', value: true, value2: true },
    ],
    date: [
        { key: 'after', label: 'on or after', value: true, input: 'date' },
        { key: 'before', label: 'on or before', value: true, input: 'date' },
        { key: 'between', label: 'between', value: true, value2: true, input: 'date' },
        { key: 'lastDays', label: 'in the last N days', value: true },
        { key: 'empty', label: 'is empty (never)', value: false },
        { key: 'notEmpty', label: 'is not empty', value: false },
    ],
    bool: [
        { key: 'isTrue', label: 'is YES', value: false },
        { key: 'isFalse', label: 'is NO', value: false },
    ],
};
OPERATORS.money = OPERATORS.number;
OPERATORS.percent = OPERATORS.number;

export const operatorsFor = (type) => OPERATORS[type] || OPERATORS.text;

const matchOne = (raw, type, op, v1, v2) => {
    if (type === 'bool') {
        if (op === 'isTrue') return !!raw;
        if (op === 'isFalse') return !raw;
        return true;
    }
    if (type === 'date') {
        const has = raw !== null && raw !== undefined && raw !== '';
        if (op === 'empty') return !has;
        if (op === 'notEmpty') return has;
        if (!has) return false;
        const t = new Date(raw).getTime();
        if (op === 'lastDays') {
            const n = Number(v1);
            if (!Number.isFinite(n)) return true;
            return Date.now() - t <= n * 86400000;
        }
        const a = v1 ? new Date(v1 + 'T00:00:00').getTime() : null;
        const b = v2 ? new Date(v2 + 'T23:59:59').getTime() : null;
        if (op === 'after') return a === null || t >= a;
        if (op === 'before') return a === null || t <= new Date(v1 + 'T23:59:59').getTime();
        if (op === 'between') return (a === null || t >= a) && (b === null || t <= b);
        return true;
    }
    if (type === 'number' || type === 'money' || type === 'percent') {
        const n = num(raw);
        const a = Number(v1);
        const b = Number(v2);
        if (op === 'between') {
            if (Number.isFinite(a) && n < a) return false;
            if (Number.isFinite(b) && n > b) return false;
            return true;
        }
        if (!Number.isFinite(a)) return true;
        if (op === 'eq') return n === a;
        if (op === 'ne') return n !== a;
        if (op === 'gt') return n > a;
        if (op === 'gte') return n >= a;
        if (op === 'lt') return n < a;
        if (op === 'lte') return n <= a;
        return true;
    }
    const s = String(raw === null || raw === undefined ? '' : raw).toLowerCase();
    const q = String(v1 === null || v1 === undefined ? '' : v1).toLowerCase().trim();
    if (op === 'empty') return s.trim() === '';
    if (op === 'notEmpty') return s.trim() !== '';
    if (!q) return true;
    if (op === 'contains') return s.includes(q);
    if (op === 'notContains') return !s.includes(q);
    if (op === 'is') return s === q;
    if (op === 'isNot') return s !== q;
    if (op === 'startsWith') return s.startsWith(q);
    return true;
};

/**
 * Conditions combine with AND by default; set `mode` to 'OR' for any-of.
 * `search` is a free-text sweep across every text field, so you can narrow
 * without having to know which column a name lives in.
 */
export const applyFilters = (rows, dataset, conditions, mode = 'AND', search = '') => {
    const active = (conditions || []).filter(c => c.field && c.op);
    const q = (search || '').trim().toLowerCase();
    const textFields = (dataset.fields || []).filter(fld => fld.type === 'text');

    return rows.filter(row => {
        if (q) {
            const hit = textFields.some(fld => String(fld.get(row) || '').toLowerCase().includes(q));
            if (!hit) return false;
        }
        if (active.length === 0) return true;
        const results = active.map(c => {
            const fld = fieldByKey(dataset, c.field);
            if (!fld) return true;
            return matchOne(fld.get(row), fld.type, c.op, c.value, c.value2);
        });
        return mode === 'OR' ? results.some(Boolean) : results.every(Boolean);
    });
};

/* ── measures ────────────────────────────────────────────────────── */
export const AGGREGATIONS = [
    { key: 'count', label: 'Count of rows', needsField: false, type: 'number' },
    { key: 'sum', label: 'Sum', needsField: true },
    { key: 'avg', label: 'Average', needsField: true },
    { key: 'min', label: 'Minimum', needsField: true },
    { key: 'max', label: 'Maximum', needsField: true },
    { key: 'distinct', label: 'Distinct values', needsField: true, type: 'number' },
];

const aggregate = (rows, agg, fld) => {
    if (agg === 'count' || !fld) return rows.length;
    if (agg === 'distinct') return new Set(rows.map(r => String(fld.get(r) ?? ''))).size;
    const vals = rows.map(r => num(fld.get(r)));
    if (vals.length === 0) return 0;
    if (agg === 'sum') return vals.reduce((a, b) => a + b, 0);
    if (agg === 'avg') return vals.reduce((a, b) => a + b, 0) / vals.length;
    if (agg === 'min') return Math.min(...vals);
    if (agg === 'max') return Math.max(...vals);
    return 0;
};

export const measureType = (measure, dataset) => {
    const def = AGGREGATIONS.find(a => a.key === measure.agg);
    if (def && def.type) return def.type;
    const fld = fieldByKey(dataset, measure.field);
    if (!fld) return 'number';
    return fld.type === 'percent' ? 'number' : fld.type;
};

export const measureLabel = (measure, dataset) => {
    const def = AGGREGATIONS.find(a => a.key === measure.agg);
    if (!def) return 'Value';
    if (!def.needsField) return def.label;
    const fld = fieldByKey(dataset, measure.field);
    return def.label + ' of ' + (fld ? fld.label : '?');
};

/**
 * Group by one or two fields and run every measure over each bucket.
 * Two levels is the ceiling on purpose: a third turns a readable table into
 * a puzzle, and "compare" already covers the cross-tab case.
 */
export const groupRows = (rows, dataset, groupKeys, measures) => {
    const keys = (groupKeys || []).filter(Boolean).slice(0, 2);
    const flds = keys.map(k => fieldByKey(dataset, k)).filter(Boolean);
    const buckets = new Map();

    rows.forEach(row => {
        const path = flds.map(fld => {
            const v = fld.get(row);
            if (v === null || v === undefined || v === '') return '(none)';
            if (fld.type === 'bool') return v ? 'YES' : 'NO';
            if (fld.type === 'date') return fmtDate(v);
            return String(v);
        });
        const id = path.join(' \u2023 ') || 'ALL';
        if (!buckets.has(id)) buckets.set(id, { id, path, rows: [] });
        buckets.get(id).rows.push(row);
    });

    return [...buckets.values()].map(b => ({
        id: b.id,
        path: b.path,
        count: b.rows.length,
        values: (measures || []).map(m => aggregate(b.rows, m.agg, fieldByKey(dataset, m.field))),
        rows: b.rows,
    }));
};

export const summarise = (rows, dataset, measures) =>
    (measures || []).map(m => aggregate(rows, m.agg, fieldByKey(dataset, m.field)));

/* ── CSV out ─────────────────────────────────────────────────────── */
const csvCell = (v) => {
    const s = v === null || v === undefined ? '' : String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};

export const toCSV = (headers, matrix) =>
    [headers.map(csvCell).join(','), ...matrix.map(r => r.map(csvCell).join(','))].join('\n');

export const downloadCSV = (filename, csv) => {
    // Excel reads a bare UTF-8 CSV as Latin-1 and mangles anything non-ASCII.
    // The BOM is what tells it otherwise.
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
};

/* ── saved views ─────────────────────────────────────────────────── */
const VIEW_KEY = 'goldenseed.reportstudio.views.v1';

export const loadViews = () => {
    try {
        return JSON.parse(window.localStorage.getItem(VIEW_KEY) || '[]');
    } catch {
        return [];
    }
};

export const saveViews = (views) => {
    try {
        window.localStorage.setItem(VIEW_KEY, JSON.stringify(views));
        return true;
    } catch {
        return false;
    }
};
