// PATH: erp-frontend/src/services/auditService.js

// VITAL FIX: Import the pre-configured 'api' instance.
// It already carries the correct cloud URL and the JWT token automatically.
// We no longer need to manually attach the Authorization header in every call.
import api from '../api/axios';

/**
 * GOLDEN SEED INDUSTRIAL AUDIT SERVICE
 * Physically manages the acquisition of forensic footprints.
 */
const auditService = {

    /**
     * THE TRUTH MACHINE (Search Hub)
     * Fetches logs based on Operator, Action type, or Timeline range.
     */
    searchForensics: async (filters = {}, page = 0) => {
        try {
            const response = await api.get('/admin/audit/search', {
                params: {
                    operator: filters.operator || null,
                    action: filters.action || null,
                    start: filters.start || null,
                    end: filters.end || null,
                    page: page,
                    size: 50
                }
            });
            return response.data;
        } catch {
            throw new Error("FORENSIC_SIGNAL_LOST: ARCHIVE ACCESS DENIED");
        }
    },

    /**
     * ASSET INVESTIGATION (Keyword Drill-down)
     */
    investigateKeyword: async (keyword, page = 0) => {
        try {
            const response = await api.get('/admin/audit/investigate', {
                params: { keyword, page, size: 50 }
            });
            return response.data;
        } catch {
            throw new Error("INVESTIGATION_FAULT: SIGNAL_UNREACHABLE");
        }
    },

    /**
     * RAW TIMELINE STREAM
     */
    getRawStream: async (page = 0) => {
        try {
            const response = await api.get('/admin/audit/stream', {
                params: { page, size: 50 }
            });
            return response.data;
        } catch {
            throw new Error("STREAM_ERROR: DATABASE_SYNC_FAILED");
        }
    }
};

export default auditService;