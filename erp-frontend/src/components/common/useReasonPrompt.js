// PATH: erp-frontend/src/components/common/useReasonPrompt.js
import { useState, useCallback } from 'react';

/**
 * fix223 (David): every delete of something saved asks WHY first. One window for the whole app (ReasonPrompt.jsx).
 *
 *   const { reasonState, askReason, closeReason } = useReasonPrompt();
 *   askReason({ title: 'DELETE DOCUMENT', message: 'Delete "x.pdf"?', picks: ['Uploaded by mistake', ...],
 *               okLabel: 'DELETE', run: async (reason) => { await service.remove(id, reason); } });
 *   <ReasonPrompt state={reasonState} onClose={closeReason} />
 *
 * `run` is awaited inside the window: while it works the button says DELETING..., and a refusal from the server is
 * shown in red inside the same window (never hidden behind it).
 */
export const useReasonPrompt = () => {
    const [reasonState, setState] = useState({ open: false, seq: 0 });
    const askReason = useCallback((opts) => setState(s => ({ ...opts, open: true, seq: (s.seq || 0) + 1 })), []);
    const closeReason = useCallback(() => setState(s => ({ open: false, seq: s.seq })), []);
    return { reasonState, askReason, closeReason };
};

export const REASON_MIN = 3;

/** Ready-made quick reasons per kind of delete (three each, like the other reason boxes). */
export const DELETE_PICKS = {
    DOCUMENT: ['Uploaded by mistake', 'Wrong project', 'A clearer copy was uploaded'],
    STAGE: ['Not needed for this project', 'Added by mistake', 'Stage done another way'],
    NOTE: ['Written on the wrong project', 'Wrong details', 'Written twice'],
    CALL: ['Logged on the wrong client', 'Logged twice', 'Wrong call result'],
    EXPENSE: ['Logged twice', 'Wrong amount', 'Wrong category'],
};
