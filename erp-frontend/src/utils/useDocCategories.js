// PATH: erp-frontend/src/utils/useDocCategories.js
// fix210: one way for every page to read the document types. The list is shared (landService caches it), it is asked
// again a few times when the server is waking up (utils/retry.js), and the page knows whether it is still loading,
// so a pick-list says "Loading..." instead of "No categories available" while it waits.
import { useCallback, useEffect, useRef, useState } from 'react';
import landService from '../services/landService';

export const CAT_EMPTY_TEXT = {
    loading: 'Loading the document types...',
    failed: 'Could not load the document types. Close this window and open it again.',
    ready: 'No document types yet',
};

export default function useDocCategories() {
    const [cats, setCats] = useState([]);
    const [state, setState] = useState('loading');
    const alive = useRef(true);
    const reload = useCallback(() => landService.getDocumentCategories()
        .then(list => { if (alive.current) { setCats(list || []); setState('ready'); } return list || []; })
        .catch(() => { if (alive.current) setState(s => (s === 'ready' ? s : 'failed')); return null; }), []);
    useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
    useEffect(() => { reload(); }, [reload]);
    /** call when a window that needs the list opens: asks again only if the list is not there yet */
    const ensure = useCallback(() => {
        if (state === 'ready') return cats;
        setState('loading'); reload();
        return null;
    }, [state, cats, reload]);
    return { cats, setCats, state, reload, ensure, emptyText: CAT_EMPTY_TEXT[state] };
}
