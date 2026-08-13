// PATH: erp-frontend/src/services/clientService.js
import api from '../api/axios';

const clientService = {
    // PHASE 2: check a NIN before/while the form is filled in.
    // Returns { exists: false } on any error so the UI never blocks on this.
    lookupNin: async (nin) => {
        if (!nin || !nin.trim()) return { exists: false };
        try {
            const response = await api.get('/clients/lookup-nin', {
                params: { nin: nin.trim().toUpperCase() }
            });
            return response.data;
        } catch {
            return { exists: false };
        }
    }
};

export default clientService;
