// PATH: erp-frontend/src/services/reportService.js

// VITAL FIX: Import the pre-configured 'api' instance.
// The old version manually attached the token in every call.
// Our 'api' instance does that automatically via the interceptor in axios.js.
// Special note: blob responses (file downloads) need responseType: 'blob'
// which api supports — we just pass it as a config option.
import api from '../api/axios';

/**
 * NYENZ INDUSTRIAL REPORTING SERVICE
 * Manages the conversion of binary streams into physical CSV downloads.
 * Synchronized with the 8-Pillar Intelligence Protocol.
 */
const reportService = {

    /**
     * MASTER DOWNLOAD ENGINE
     * Creates a virtual hardware bridge to the browser's download manager.
     */
    _triggerDownload: async (endpoint, fallbackName) => {
        try {
            const response = await api.get(`/reports${endpoint}`, {
                // VITAL: This tells axios to treat the response as a
                // raw binary file (blob), not as text or JSON.
                // Without this, the downloaded CSV would be corrupted.
                responseType: 'blob'
            });

            // Create a temporary invisible link and click it to trigger download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;

            // Try to read the filename from the server's response headers
            const disposition = response.headers['content-disposition'];
            let fileName = `${fallbackName}.csv`;
            if (disposition) {
                const match = disposition.match(/filename=(.+)/);
                if (match && match[1]) fileName = match[1].replace(/['"]/g, '');
            }

            link.setAttribute('download', fileName);
            document.body.appendChild(link);
            link.click();

            // Cleanup memory
            link.remove();
            window.URL.revokeObjectURL(url);
            return true;

        } catch {
            throw new Error("ACCESS_DENIED: REPORT_PROTOCOL_LOCKED");
        }
    },

    /* --- THE 8 PILLARS OF NYENZ INTELLIGENCE --- */

    // Financial Pillars (Restricted to Root)
    downloadDebtLedger:  () => reportService._triggerDownload('/debt-ledger',      'DEBT_LEDGER'),
    downloadPerformance: () => reportService._triggerDownload('/performance',       'RECOVERY_SPEED'),
    downloadLegalReady:  () => reportService._triggerDownload('/legal-readiness',   'LEGAL_COMPLIANCE'),
    downloadAuditTrail:  () => reportService._triggerDownload('/audit-trail',       'SYSTEM_AUDIT'),
    downloadRevenue:     () => reportService._triggerDownload('/revenue',           'CASH_INFLOW_HISTORY'),

    // Operational Pillars (Open to Managers)
    downloadArchiveMap:  () => reportService._triggerDownload('/archive-map',       'PHYSICAL_ARCHIVE_MAP'),
    downloadBottlenecks: () => reportService._triggerDownload('/bottlenecks',       'SURVEY_STAGES'),
    downloadReliability: () => reportService._triggerDownload('/reliability',       'CLIENT_RANKINGS'),

    // Priority 2 Reports (Admin only)
    downloadReceivableBreakdown:  () => reportService._triggerDownload('/receivable-breakdown',  'RECEIVABLE_BREAKDOWN'),
    downloadCompletedTitles:   () => reportService._triggerDownload('/completed-titles',   'COMPLETED_TITLES'),
    downloadOperatorReconciliation: () => reportService._triggerDownload('/payment-history', 'OPERATOR_CASH_RECONCILIATION'),
    downloadMonthlyCollection: () => reportService._triggerDownload('/monthly-collection', 'MONTHLY_COLLECTION'),
};

export default reportService;