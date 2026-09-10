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
    },

    // Client dossier "EDIT PORTFOLIO" action: contact-detail corrections
    // only (name/phone/email/address). NIN and money figures are not sent
    // here -- see ClientController.updateClient for why.
    updateClient: (id, payload) => api.put('/clients/' + id, payload).then((response) => response.data),
};

export default clientService;
