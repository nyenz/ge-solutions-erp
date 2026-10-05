// PATH: erp-frontend/src/pages/Reports/reportData.js
/**
* GOLDEN SEED -- THE REPORT STUDIO DATA LAYER.
*
* The fields, filters, grouping and measures live in reportFields.js (no network imports, tested with Node). This file
* adds one loader per dataset and re-exports everything, so ReportStudio.jsx keeps one import.
*
* fix181: every loader walks the server pages until the end or a cap. When the cap is hit the list carries a `note`
* ("showing the newest N of M") that the Studio shows above the report, so a report never undercounts silently.
*/
import api from '../../api/axios';
import landService from '../../services/landService';
import recoveryService from '../../services/recoveryService';
import expenseService from '../../services/expenseService';
import { DATASET_META } from './reportFields';
import { toCSV as csvOf, downloadCSV as csvDownload } from '../../utils/csv';

export * from './reportFields';

const MAX_ROWS = 20000;
const withNote = (rows, total, what) => {
  if (Number.isFinite(total) && total > rows.length) {
    rows.note = `Showing the newest ${rows.length.toLocaleString()} of ${total.toLocaleString()} ${what}.`;
  }
  return rows;
};

/** Walks a Spring page endpoint (content / totalElements) or the payments list (rows / total). */
const walk = async (fetchPage, what) => {
  const out = [];
  const SIZE = 200;
  let total = null;
  for (let page = 0; out.length < MAX_ROWS; page += 1) {
    const data = await fetchPage(page, SIZE);
    const rows = (data && (data.content || data.rows)) || [];
    if (total === null) total = Number(data?.totalElements ?? data?.total);
    out.push(...rows);
    if (rows.length < SIZE) break;
  }
  return withNote(out, total, what);
};

const loaders = {
  PROJECTS: async () => {
    const out = [];
    for (let page = 0; page < 100; page += 1) {
      const data = await landService.getGlobalLedger(page, 200);
      const rows = data?.content || [];
      out.push(...rows);
      if (rows.length < 200) break;
    }
    // fix181 (9.5): Pending field entries (no price yet) are not projects for a report
    const live = out.filter(p => !p.pending);
    // the Recovery state of each project comes from the same client ledger the Recovery page uses
    try {
      const clients = (await recoveryService.getClientLedger()) || [];
      const state = {};
      clients.forEach(c => (c.plots || []).forEach(pl => { if (pl.projectId && pl.recoveryState) state[pl.projectId] = pl.recoveryState; }));
      live.forEach(p => { if (state[p.id]) p.recoveryState = state[p.id]; });
    } catch { /* the report still works without the Recovery state */ }
    return live;
  },
  CLIENTS: async () => (await recoveryService.getClientLedger()) || [],
  // fix181 (16.10e): the same list query as the Payments page, page by page; deleted projects are left out
  PAYMENTS: async () => walk((page, size) => api.get('/recovery/payments/list', { params: { page, size, sort: 'date', dir: 'desc' } }).then(r => r.data), 'payment lines'),
  EXPENSES: async () => {
    const data = await expenseService.search({}, 0, 5000);
    return data?.content || data || [];
  },
  // fix181 (10.7): the whole audit trail up to the cap, with a note when there is more
  COMPANY: async () => walk((page, size) => api.get('/admin/audit/search', { params: { page, size } }).then(r => r.data), 'audit lines'),
};

export const DATASETS = Object.fromEntries(Object.entries(DATASET_META).map(([k, meta]) => [k, { ...meta, load: loaders[k] }]));

export const datasetsFor = (canSeeMoney) =>
  Object.values(DATASETS).filter(d => canSeeMoney || !d.restricted);

/* ── CSV out (fix181, 13.8: the shared, formula-safe writer) ─────── */
export const toCSV = csvOf;
export const downloadCSV = csvDownload;

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
