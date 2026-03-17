// PATH: erp-frontend/src/services/reportService.js
import axios from 'axios';

const API_URL = 'http://localhost:8080/api/v1/reports';

/**
 * NYENZ INDUSTRIAL REPORTING SERVICE
 * 
 * Manages the conversion of binary streams into physical CSV downloads.
 * Synchronized with the 8-Pillar Intelligence Protocol.
 */
const reportService = {

    /**
     * MASTER DOWNLOAD ENGINE
     * Creates a virtual hardware bridge to the browser's download manager.
     */
    _triggerDownload: async (endpoint, fallbackName) => {
        const token = localStorage.getItem('gs_token');
        try {
            const response = await axios.get(`${API_URL}${endpoint}`, {
                headers: { 'Authorization': `Bearer ${token}` },
                responseType: 'blob'
            });

            // Create memory blob and virtual link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;

            // Filename extraction from Hardware Headers
            const disposition = response.headers['content-disposition'];
            let fileName = `${fallbackName}.csv`;
            if (disposition) {
                const match = disposition.match(/filename=(.+)/);
                if (match && match[1]) fileName = match[1].replace(/['"]/g, '');
            }

            link.setAttribute('download', fileName);
            document.body.appendChild(link);
            link.click();

            // Hardware Memory Cleanup
            link.remove();
            window.URL.revokeObjectURL(url);
            return true;
        } catch {
            throw new Error("ACCESS_DENIED: REPORT_PROTOCOL_LOCKED");
        }
    },

    /* --- THE 8 PILLARS OF NYENZ INTELLIGENCE --- */

    // Financial Pillars (Restricted to Root)
    downloadDebtLedger: () => reportService._triggerDownload('/debt-ledger', 'DEBT_LEDGER'),
    downloadPerformance: () => reportService._triggerDownload('/performance', 'RECOVERY_SPEED'),
    downloadLegalReady: () => reportService._triggerDownload('/legal-readiness', 'LEGAL_COMPLIANCE'),
    downloadAuditTrail: () => reportService._triggerDownload('/audit-trail', 'SYSTEM_AUDIT'),
    downloadRevenue: () => reportService._triggerDownload('/revenue', 'CASH_INFLOW_HISTORY'),

    // Operational Pillars (Open to Managers)
    downloadArchiveMap: () => reportService._triggerDownload('/archive-map', 'PHYSICAL_ARCHIVE_MAP'),
    downloadBottlenecks: () => reportService._triggerDownload('/bottlenecks', 'SURVEY_STAGES'),
    downloadReliability: () => reportService._triggerDownload('/reliability', 'CLIENT_RANKINGS')
};

export default reportService;