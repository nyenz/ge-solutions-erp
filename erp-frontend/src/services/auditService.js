// PATH: erp-frontend/src/services/auditService.js
import api from '../api/axios';
import { errorText } from '../utils/errorText';

/**
 * GOLDEN SEED ERP - AUDIT TRAIL SERVICE
 * fix181 (10.5): a failure keeps its HTTP status and a plain sentence, so the page can tell "nothing found" from
 * "could not load" (expired sign-in, no access, server down).
 * fix181 (10.13): `actions` is a LIST of codes, sent as actions=A&actions=B (no [] brackets, which Spring would not read).
 */
const fail = (error) => {
    const e = new Error(errorText(error));
    e.status = error?.response?.status || null;
    throw e;
};

const auditService = {
    /** filters: { operator, actions: [codes], keyword, start, end (exclusive), excludeSystem } */
    searchForensics: (filters = {}, page = 0, size = 50) =>
        api.get('/admin/audit/search', {
            params: {
                operator: filters.operator || undefined,
                actions: filters.actions && filters.actions.length ? filters.actions : undefined,
                keyword: filters.keyword || undefined,
                start: filters.start || undefined,
                end: filters.end || undefined,
                excludeSystem: filters.excludeSystem || undefined,
                page,
                size,
            },
            paramsSerializer: { indexes: null },
        }).then(r => r.data).catch(fail),

    /** Every name in the audit trail (SYSTEM included); works for the Director too (10.3). */
    getOperators: () => api.get('/admin/audit/operators').then(r => r.data || []).catch(fail),

    /** One AUDIT_EXPORT line: who exported, which filters, how many rows (10.6c). Best effort. */
    logExport: (filters, rows) => api.post('/admin/audit/export-log', { filters, rows }).catch(() => {}),

    getRawStream: (page = 0, size = 200) =>
        api.get('/admin/audit/stream', { params: { page, size } }).then(r => r.data).catch(fail),
};

export default auditService;
