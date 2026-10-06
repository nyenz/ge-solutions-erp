// PATH: erp-frontend/src/services/settingsService.js
import api from '../api/axios';
import { errorText } from '../utils/errorText';

/**
 * GOLDEN SEED ERP - SECURITY & GOVERNANCE SERVICE
 * fix181 (15.2i): every failure is re-thrown as a plain sentence (utils/errorText.js), never upper-cased; the server
 * code (the part before the colon) is kept on err.code so a page can react to it (for example RESTORE_CLASH).
 * fix181 (15.4d): every username in a URL is encoded.
 */
const fail = (error) => {
    const e = new Error(errorText(error));
    const raw = error?.response?.data?.message || error?.response?.data?.error || '';
    const m = String(raw).match(/^([A-Z][A-Z0-9_]{2,}):/);
    e.code = m ? m[1] : (error?.response?.data?.error || null);
    e.status = error?.response?.status || null;
    throw e;
};

const settingsService = {
    /** Own key change. Answers a fresh token and user (other devices are signed out). */
    changePersonalPassword: (oldPassword, newPassword) =>
        api.put('/profile/change-password', { oldPassword, newPassword }).then(r => r.data).catch(fail),

    getAllOperators: () => api.get('/staff/all').then(r => r.data).catch(fail),

    registerManager: (staffData) =>
        api.post('/staff/create', { ...staffData, username: String(staffData.username || '').trim(), email: String(staffData.email || '').trim() })
            .then(r => r.data).catch(fail),

    updateOperatorRole: (username, newRole) =>
        api.patch(`/staff/${encodeURIComponent(username)}/role`, null, { params: { newRole } }).then(() => true).catch(fail),

    toggleOperator: (username, isActive) =>
        api.patch(`/staff/${encodeURIComponent(username)}/toggle`, null, { params: { active: isActive } }).then(() => true).catch(fail),

    resetOperatorKey: (username) =>
        api.post('/staff/reset-password', { username }).then(r => r.data.temporaryPassword).catch(fail),

    /**
     * DANGER ZONE: wipe all business data (Admin only). Needs the typed phrase AND the Admin's own key (14.4f).
     * Staff accounts and the audit trail are kept.
     */
    wipeAllData: (password, freshStart = false) =>
        api.post('/admin/system/wipe-all-data', { password, freshStart: !!freshStart }, { params: { confirm: 'WIPE-EVERYTHING' }, timeout: 180000 })
            .then(r => r.data).catch(fail),
};

export { fail as toPlainError };
export default settingsService;
