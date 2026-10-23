// fix215 (David): the Notes timeline of a project or a client (server: TimelineController, /timeline).
import api from '../api/axios';

const timelineService = {
    project: (id) => api.get('/timeline/project/' + id).then(r => r.data),
    client: (id) => api.get('/timeline/client/' + id).then(r => r.data),
    addNote: (projectId, { content, topic, followUpOn, pinned, file }) => {
        const fd = new FormData();
        fd.append('content', content);
        if (topic) fd.append('topic', topic);
        if (followUpOn) fd.append('followUpOn', followUpOn);
        if (pinned) fd.append('pinned', 'true');
        if (file) fd.append('file', file, file.name);
        return api.post('/timeline/project/' + projectId + '/notes', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data);
    },
    // fix225: a note about the client alone (no project, no file)
    addClientNote: (clientId, { content, topic, followUpOn, pinned }) =>
        api.post('/timeline/client/' + clientId + '/notes', { content, topic: topic || '', followUpOn: followUpOn || '', pinned: !!pinned }).then(r => r.data),
    editNote: (noteId, { content, topic, followUpOn }) => api.put('/timeline/notes/' + noteId, { content, topic: topic || '', followUpOn: followUpOn || '' }).then(r => r.data),
    pin: (noteId, pinned) => api.patch('/timeline/notes/' + noteId + '/pin', { pinned }).then(r => r.data),
    remove: (noteId, reason) => api.delete('/timeline/notes/' + noteId, { params: { reason } }),   // fix223
};
export default timelineService;
