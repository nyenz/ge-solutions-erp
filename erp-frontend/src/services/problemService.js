// PATH: erp-frontend/src/services/problemService.js
// fix289 (David): the Problems subsystem -- problem types, the list, site visits, add / change / solve / remove.
import api from '../api/axios';

const problemService = {
    kinds: () => api.get('/problems/kinds').then(r => r.data),
    list: (params) => api.get('/problems', { params }).then(r => r.data),
    openCounts: () => api.get('/problems/open-counts').then(r => r.data),
    siteVisits: () => api.get('/problems/site-visits').then(r => r.data),
    add: (body) => api.post('/problems', body).then(r => r.data),
    update: (id, body) => api.put('/problems/' + id, body).then(r => r.data),
    solve: (id, note) => api.post('/problems/' + id + '/solve', { note }).then(r => r.data),
    remove: (id, reason) => api.delete('/problems/' + id, { params: { reason } }).then(r => r.data),
};

// the words the pages show for a solution
export const SOLUTION_WORDS = { SITE_VISIT: 'Needs a site visit', CALL: 'Call the client', OFFICE: 'Fix in the office', LATER: 'Decide later' };
export const SOLUTION_OPTIONS = Object.entries(SOLUTION_WORDS).map(([value, label]) => ({ value, label }));

export default problemService;
