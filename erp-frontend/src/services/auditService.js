// PATH: erp-frontend/src/services/auditService.js
import axios from 'axios';

const API_URL = 'http://localhost:8080/api/v1/admin/audit';

/**
 * NYENZ INDUSTRIAL AUDIT SERVICE
 * 
 * Physically manages the acquisition of forensic footprints.
 * Bridges the Search/Filter HUD to the Java 'Black Box' logic.
 */
const auditService = {

    /**
     * THE TRUTH MACHINE (Search Hub)
     * Fetches logs based on Operator, Action type, or Timeline range.
     * @param {Object} filters - {operator, action, start, end}
     * @param {Number} page - Pagination index
     */
    searchForensics: async (filters = {}, page = 0) => {
        const token = localStorage.getItem('gs_token');
        try {
            const response = await axios.get(`${API_URL}/search`, {
                headers: { 'Authorization': `Bearer ${token}` },
                params: {
                    operator: filters.operator || null,
                    action: filters.action || null,
                    start: filters.start || null,
                    end: filters.end || null,
                    page: page,
                    size: 50 // High-density batch for auditing
                }
            });
            return response.data;
        } catch {
            throw new Error("FORENSIC_SIGNAL_LOST: ARCHIVE ACCESS DENIED");
        }
    },

    /**
     * ASSET INVESTIGATION (Keyword Drill-down)
     * Searches the RAW metadata details (e.g., UCL/2026/001).
     */
    investigateKeyword: async (keyword, page = 0) => {
        const token = localStorage.getItem('gs_token');
        try {
            const response = await axios.get(`${API_URL}/investigate`, {
                headers: { 'Authorization': `Bearer ${token}` },
                params: { keyword, page, size: 50 }
            });
            return response.data;
        } catch {
            throw new Error("INVESTIGATION_FAULT: SIGNAL_UNREACHABLE");
        }
    },

    /**
     * RAW TIMELINE STREAM
     * Fetches most recent footprints without filters.
     */
    getRawStream: async (page = 0) => {
        const token = localStorage.getItem('gs_token');
        try {
            const response = await axios.get(`${API_URL}/stream`, {
                headers: { 'Authorization': `Bearer ${token}` },
                params: { page, size: 50 }
            });
            return response.data;
        } catch {
            throw new Error("STREAM_ERROR: DATABASE_SYNC_FAILED");
        }
    }
};

export default auditService;