// PATH: erp-frontend/src/pages/Reports/reportFields.js
/**
* GOLDEN SEED -- REPORT STUDIO FIELDS (fix181: split out of reportData.js so it has no network imports and can be
* tested with plain Node, see tests/reportFields.test.mjs).
*
* One source of truth for datasets, fields, filtering, grouping and measures. reportData.js adds the loaders.
*
* ROLE RULES: a dataset marked `restricted` and a field marked `money` are never offered to a user without financial
* access (the server refuses those endpoints too). A field marked `hidden` is for grouping/filtering only and is never
* offered as a column.
*/
import { projectTypeOf } from '../../constants/projectTypes.js';

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
  if (!v) return 'No date';
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return 'No date';
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
const clientsOf = (p) => ((p.clients && p.clients.length) ? p.clients : (p.proprietors || []));
const uniq = (list) => [...new Set(list.filter(Boolean))].join(', ');
// the Recovery states (RecoveryStateService.URGENCY), most urgent first
const RECOVERY_LABEL = { SITE: '1 Site visit', MISSED: '2 Missed calls', NEW: '3 Not called yet', CONTACTED: '4 Contacted', LOCKED: '5 Called recently (locked)' };
const recoveryLabel = (v) => (v ? (RECOVERY_LABEL[v] || String(v).replace(/_/g, ' ').toLowerCase().replace(/^./, c => c.toUpperCase())) : 'Not in recovery');

/* ── PROJECTS ────────────────────────────────────────────────────── */
export const projectFields = [
  f('index', 'Project Index', 'text', p => p.projectIndex || ''),
  f('plot', 'Plot Number', 'text', p => p.landTitle?.plotNumber || ''),
  f('tenure', 'Tenure', 'text', p => p.landTitle?.tenure || ''),
  f('block', 'Block', 'text', p => p.landTitle?.block || ''),
  f('areaHa', 'Area (ha)', 'number', p => (p.landTitle?.areaHectares == null ? null : num(p.landTitle.areaHectares))),
  f('volume', 'Volume', 'text', p => p.landTitle?.volume || ''),
  f('folio', 'Folio', 'text', p => p.landTitle?.folio || ''),
  f('district', 'District', 'text', p => p.district || ''),
  f('county', 'County', 'text', p => p.county || ''),
  f('subCounty', 'Sub-County', 'text', p => p.subCounty || ''),
  f('parish', 'Parish', 'text', p => p.parish || ''),
  f('village', 'Village', 'text', p => p.village || ''),
  f('area', 'Area', 'text', p => p.area || ''),
  f('projectType', 'Project Type', 'text', p => projectTypeOf(p).label),
  // the CLIENT pays and is who Recovery calls; old projects with no clients fall back to the owners
  f('client', 'Primary Client', 'text', p => clientsOf(p)[0]?.fullName || ''),
  f('clientPhone', 'Client Phone', 'text', p => clientsOf(p)[0]?.phoneNumber || ''),
  f('clientNin', 'Client NIN', 'text', p => clientsOf(p)[0]?.nationalId || ''),
  f('clientAddress', 'Client Address', 'text', p => clientsOf(p)[0]?.homeAddress || ''),
  f('allClients', 'All Clients', 'text', p => clientsOf(p).map(o => o.fullName).join(', ')),
  f('owner', 'Primary Owner', 'text', p => p.proprietors?.[0]?.fullName || ''),
  f('ownerPhone', 'Owner Phone', 'text', p => p.proprietors?.[0]?.phoneNumber || ''),
  f('ownerNin', 'Owner NIN', 'text', p => p.proprietors?.[0]?.nationalId || ''),
  f('ownerAddress', 'Owner Address', 'text', p => p.proprietors?.[0]?.homeAddress || ''),
  f('allOwners', 'All Owners', 'text', p => (p.proprietors || []).map(o => o.fullName).join(', ')),
  f('ownerCount', 'Owner Count', 'number', p => (p.proprietors || []).length),
  f('ownership', 'Ownership', 'text', p => ((p.proprietors || []).length > 1 ? 'JOINT' : 'SOLO')),
  f('status', 'Status', 'text', p => p.status || ''),
  f('statusIndex', 'Status Index', 'number', p => num(p.currentStatusIndex)),
  // fix181 (9.5): the Recovery state and the shared CRITICAL rule (the same ones the Recovery and client pages show)
  f('recoveryState', 'Recovery State', 'text', p => recoveryLabel(p.recoveryState)),
  f('critical', 'Critical', 'bool', p => !!p.critical),
  f('planType', 'Plan Type', 'text', p => p.planType || ''),
  f('titled', 'Has Title', 'bool', p => !!p.landTitle),
  f('released', 'Title Released', 'bool', p => !!p.landTitle?.isReleased),
  f('legacy', 'Legacy', 'bool', p => !!p.isLegacy),
  f('receivable', 'In Receivables', 'bool', p => !!p.isReceivable),
  f('problem', 'Flagged Problem', 'bool', p => !!p.problem),
  f('startDate', 'Project Start', 'date', p => p.projectStartDate || null),
  f('lastPayment', 'Last Payment', 'date', p => p.lastPaymentDate || null),
  f('daysSincePayment', 'Days Since Payment', 'number', p => (p.daysSincePayment ?? daysSince(p.lastPaymentDate))),
  f('receivableStart', 'Receivables Start', 'date', p => p.receivableStartDate || null),
  f('totalCost', 'Total Cost', 'money', p => num(p.totalCost), { money: true }),
  f('amountPaid', 'Amount Paid', 'money', p => num(p.amountPaid), { money: true }),
  // owed = billed - paid toward billed: a project in receivables also owes its storage fees (same rule as the server)
  f('balance', 'Balance Owed', 'money', p => Math.max(0, num(p.totalCost) + (p.isReceivable ? num(p.storageFeesAccumulated) : 0) - num(p.amountPaid)), { money: true }),
  f('storage', 'Storage Fees', 'money', p => num(p.storageFeesAccumulated), { money: true }),
  f('storagePaid', 'Storage Fees Paid', 'money', p => num(p.storageFeesPaid), { money: true }),
  f('storageUnpaid', 'Storage Fees Unpaid', 'money', p => Math.max(0, num(p.storageFeesAccumulated) - num(p.storageFeesPaid)), { money: true }),
  f('originalDebt', 'Original Debt', 'money', p => num(p.originalDebt), { money: true }),
  f('installment', 'Weekly Installment', 'money', p => num(p.weeklyInstallment), { money: true }),
  f('pctPaid', 'Percent Paid', 'percent', p => (num(p.totalCost) > 0 ? Math.round(((num(p.amountPaid) - num(p.storageFeesPaid)) / num(p.totalCost)) * 100) : 0), { money: true }),
];

/* ── CLIENTS ─────────────────────────────────────────────────────── */
// fix181 (5.6): a joint project sits under EVERY client who pays it, so a sum over client rows counts it once per
// client; company-wide owed is on the PROJECTS dataset. Two people with the same name are kept apart by "Client".
const clientLabel = (c) => (c.name || '?') + (c.nin ? ' (' + c.nin + ')' : (c.id ? ' (#' + String(c.id).slice(0, 6) + ')' : ''));
export const clientFields = [
  f('clientId', 'Client Id', 'text', c => (c.id ? String(c.id) : ''), { hidden: true }),
  f('client', 'Client', 'text', c => clientLabel(c)),
  f('name', 'Client Name', 'text', c => c.name || ''),
  f('nin', 'NIN', 'text', c => c.nin || ''),
  f('phone', 'Phone', 'text', c => c.phone || ''),
  f('email', 'Email', 'text', c => c.email || ''),
  f('plotCount', 'Projects', 'number', c => num(c.plotCount)),
  f('districts', 'Districts', 'text', c => uniq((c.plots || []).map(p => p.district))),
  // fix181 (9.9): the Client Ledger rows carry the sub-county, not the county
  f('subCounties', 'Sub-Counties', 'text', c => uniq((c.plots || []).map(p => p.subCounty))),
  // fix181 (9.3): the project types the client has
  f('projectTypes', 'Project Types', 'text', c => uniq((c.plots || []).map(p => p.projectTypeLabel || p.projectType))),
  f('receivables', 'Has Receivables', 'bool', c => (c.plots || []).some(p => p.receivable)),
  // fix181 (9.5, 9.6): the same Recovery state, CRITICAL count and missed calls the Recovery page works from
  f('recoveryState', 'Recovery State', 'text', c => recoveryLabel(c.recoveryState)),
  f('criticalCount', 'Critical Projects', 'number', c => num(c.criticalCount)),
  f('missedCalls', 'Missed Call Days (30 days)', 'number', c => num(c.missedCallDays30)),
  f('lastContact', 'Last Contact', 'date', c => c.lastContact || null),
  f('daysSinceContact', 'Days Since Contact', 'number', c => (c.daysSinceContact ?? daysSince(c.lastContact))),
  f('lastPaymentAt', 'Last Payment', 'date', c => c.lastPaymentAt || null),
  f('daysSincePayment', 'Days Since Payment', 'number', c => (c.daysSincePayment ?? daysSince(c.lastPaymentAt))),
  f('lastTag', 'Last Call Tag', 'text', c => c.lastTag || ''),
  f('lastTone', 'Last Call Tone', 'text', c => c.lastTone || ''),
  f('owed', 'Total Owed', 'money', c => num(c.owed), { money: true }),
  f('paid', 'Total Paid', 'money', c => num(c.paid), { money: true }),
  f('storage', 'Storage Fees', 'money', c => num(c.storage), { money: true }),
  f('storagePaid', 'Storage Fees Paid', 'money', c => num(c.storagePaid), { money: true }),
  // fix181 (5.5, 9.10): billed comes from the server (billed = owed + paid for every project)
  f('billed', 'Total Billed', 'money', c => (c.billed != null ? num(c.billed) : num(c.owed) + num(c.paid)), { money: true }),
  f('pctPaid', 'Percent Paid', 'percent', c => {
    const total = c.billed != null ? num(c.billed) : num(c.owed) + num(c.paid);
    return total > 0 ? Math.round((num(c.paid) / total) * 100) : 0;
  }, { money: true }),
];

/* ── PAYMENTS ────────────────────────────────────────────────────── */
// fix181 (16.10): one row per payment line from /recovery/payments/list. Month, year and days are from the DATE PAID
// (a reversal has its own date; an undated opening deposit shows "No date"). Sums are NET of reversals.
const KIND_LABELS = { OPENING_DEPOSIT: 'Opening deposit', IN_RECEIVABLES: 'Payment in receivables', PAYMENT: 'Payment', REVERSAL: 'Reversal' };
export const paymentFields = [
  f('date', 'Date Paid', 'date', p => p.paidOn || null),
  f('month', 'Month', 'text', p => monthKey(p.paidOn)),
  f('year', 'Year', 'text', p => (p.paidOn ? String(new Date(p.paidOn).getFullYear()) : 'No date')),
  f('entered', 'Date Entered', 'date', p => p.enteredAt || null),
  f('project', 'Project', 'text', p => p.projectIndex || ''),
  f('projectType', 'Project Type', 'text', p => p.projectTypeLabel || ''),
  f('plot', 'Plot', 'text', p => p.plotNumber || ''),
  f('clientId', 'Client Id', 'text', p => (p.payerClientId ? String(p.payerClientId) : ''), { hidden: true }),
  f('client', 'Client', 'text', p => p.clientName || ''),   // the person who paid (current name), from the server
  f('kind', 'Kind', 'text', p => KIND_LABELS[p.kind] || p.kind || ''),
  f('allocation', 'Allocation', 'text', p => p.allocation || 'TITLE'),
  f('reversed', 'Reversed', 'bool', p => !!p.reversed),
  f('reverses', 'Reverses Payment', 'text', p => (p.reversalOf ? String(p.reversalOf) : '')),
  f('hasReceipt', 'Has Receipt', 'bool', p => !!p.hasReceipt),
  f('deleted', 'Deleted Project', 'bool', p => !!p.deleted, { hidden: true }),
  f('recordedBy', 'Recorded By', 'text', p => p.recordedBy || ''),
  f('notes', 'Notes', 'text', p => p.notes || ''),
  f('amount', 'Amount Paid', 'money', p => num(p.amountPaid), { money: true }),
  f('balanceAfter', 'Balance After', 'money', p => num(p.balanceAfter), { money: true }),
  f('daysAgo', 'Days Ago', 'number', p => daysSince(p.paidOn)),
];

/* ── EXPENSES ────────────────────────────────────────────────────── */
export const expenseFields = [
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

/* ── COMPANY (audit trail) ───────────────────────────────────────── */
export const companyFields = [
  f('timestamp', 'Timestamp', 'date', a => a.timestamp || null),
  f('month', 'Month', 'text', a => monthKey(a.timestamp)),
  // fix181 (10.8): the nightly jobs write as SYSTEM; shown under a name that says so
  f('operator', 'Operator', 'text', a => (a.performedBy === 'SYSTEM' ? 'SYSTEM (automatic)' : (a.performedBy || ''))),
  f('action', 'Action', 'text', a => a.action || ''),
  f('details', 'Details', 'text', a => a.details || ''),
];

/* ── dataset descriptions (reportData.js adds `load`) ─────────────── */
export const DATASET_META = {
  PROJECTS: {
    key: 'PROJECTS', label: 'Projects', restricted: false, dateField: 'Project Start', fields: projectFields,
    blurb: 'Every land project: type, location, clients, owners, status, recovery state and the money against it. Pending field entries are left out.',
    defaultColumns: ['index', 'plot', 'district', 'client', 'status', 'totalCost', 'amountPaid', 'balance'],
  },
  CLIENTS: {
    key: 'CLIENTS', label: 'Clients', restricted: false, dateField: 'Last Contact', fields: clientFields,
    blurb: 'Every registered client with their portfolio totals, recovery state and call history. A joint project counts once for each client.',
    defaultColumns: ['client', 'phone', 'plotCount', 'districts', 'owed', 'paid', 'lastContact'],
  },
  PAYMENTS: {
    key: 'PAYMENTS', label: 'Payments', restricted: true, dateField: 'Date Paid', fields: paymentFields,
    blurb: 'Every payment line (reversals as minus lines, so sums are net), with who paid and who recorded it.',
    defaultColumns: ['date', 'project', 'client', 'kind', 'amount', 'recordedBy'],
  },
  EXPENSES: {
    key: 'EXPENSES', label: 'Expenses', restricted: true, dateField: 'Date', fields: expenseFields,
    blurb: 'Every shilling logged as leaving the office, by category and by staff.',
    defaultColumns: ['date', 'category', 'amount', 'recordedBy', 'spentBy'],
  },
  COMPANY: {
    key: 'COMPANY', label: 'Company', restricted: true, dateField: 'Timestamp', fields: companyFields,
    blurb: 'Every staff action in the audit trail: logins, edits, deletes, overrides, status moves.',
    defaultColumns: ['timestamp', 'operator', 'action', 'details'],
  },
};

export const fieldsFor = (dataset, canSeeMoney) =>
  (dataset?.fields || []).filter(fld => !fld.hidden && (canSeeMoney || !fld.money));
export const fieldByKey = (dataset, key) => (dataset?.fields || []).find(fld => fld.key === key);
export const fieldByLabel = (dataset, label) => (dataset?.fields || []).find(fld => fld.label === label);

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
    // fix181 (9.4): "on or before" uses the same end-of-day cut-off as "between" (one copy of the date maths)
    const endOfV1 = v1 ? new Date(v1 + 'T23:59:59').getTime() : null;
    if (op === 'before') return endOfV1 === null || t <= endOfV1;
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
  // fix181 (10.8): an exact list of values (the COMPANY reports filter by a list of audit codes)
  if (op === 'oneOf') return Array.isArray(v1) ? v1.includes(String(raw ?? '')) : true;
  if (op === 'noneOf') return Array.isArray(v1) ? !v1.includes(String(raw ?? '')) : true;
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

