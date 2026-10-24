// PATH: erp-frontend/src/components/common/PopupError.jsx
// fix241 (David, test D1): a popup never shows its error as a red box inside itself any more. The message comes as a
// toast ON TOP of the popup, and the box it is about is marked red, scrolled to (inside the popup) and given the
// cursor -- the same as on the pages. The same message twice in a row is said only once (typing does not repeat it).
import { useEffect, useRef } from 'react';
import { flagByWords } from '../../utils/fieldError';

const PopupError = ({ text, toast }) => {
    const anchor = useRef(null);
    const last = useRef('');
    useEffect(() => {
        if (!text) { last.current = ''; return; }
        if (text === last.current) return;
        last.current = text;
        if (toast) toast(text, 'error');
        const root = (anchor.current && anchor.current.closest('[role="dialog"]')) || document;
        // the popup may still be drawing its boxes: wait one paint
        requestAnimationFrame(() => flagByWords(text, root));
    }, [text, toast]);
    return <span ref={anchor} hidden aria-hidden="true" />;
};

export default PopupError;
