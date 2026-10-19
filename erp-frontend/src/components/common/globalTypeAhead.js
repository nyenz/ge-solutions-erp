// PATH: erp-frontend/src/components/common/globalTypeAhead.js
// fix217 (David): "the dropdowns seem not to have the thing where I press a letter and it goes to the item that begins
// with it -- this was supposed to be throughout the app". The shared lists (HardwareSelect, HardwareModalSelect, the
// Folder SmartSelect) already do it themselves. THIS one listener, installed once in App.jsx, gives the same behaviour to
// every OTHER open pick-list in the app: any element marked data-ta-list (or role="listbox") that is on screen.
//  - a letter (or a quick run of letters) moves the focus to the next option whose words start with it, and scrolls to it;
//  - Enter then picks it (the option is a real button), Escape is left to the list itself;
//  - typing inside a text box is never touched, and a list that already handled the key (preventDefault) is left alone.
// New pick-lists: put data-ta-list on the list box and make every option a <button> (or role="option").
import { useEffect } from 'react';
import { findTypeAhead, isTypeAheadKey } from '../../utils/typeAhead';

const RESET_MS = 800;
const OPTION = 'button:not([disabled]), [role="option"], label';

const visible = (el) => !!el && el.isConnected && el.getClientRects().length > 0;

function openList(from) {
    const own = from && from.closest ? from.closest('[data-ta-list], [role="listbox"]') : null;
    if (own && visible(own)) return own;
    // the list that belongs to the focused toggle (inside the same field), else the only list open on the page
    const field = from && from.closest ? from.closest('[data-ta-field]') : null;
    const near = field ? field.querySelector('[data-ta-list], [role="listbox"]') : null;
    if (near && visible(near)) return near;
    const all = Array.from(document.querySelectorAll('[data-ta-list], [role="listbox"]')).filter(visible);
    return all.length === 1 ? all[0] : null;
}

export function installGlobalTypeAhead() {
    if (typeof document === 'undefined') return () => {};
    let buf = '', at = 0;
    const onKey = (e) => {
        if (e.defaultPrevented) return;
        const t = e.target;
        if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) && !(t.closest && t.closest('[data-ta-list]'))) return;
        const now = Date.now();
        if (now - at > RESET_MS) buf = '';
        if (!isTypeAheadKey(e, buf.length > 0)) return;
        const list = openList(t);
        if (!list) return;
        const options = Array.from(list.querySelectorAll(OPTION)).filter(visible);
        if (!options.length) return;
        at = now;
        buf += e.key;
        const current = options.indexOf(document.activeElement && document.activeElement.closest ? document.activeElement.closest(OPTION) : null);
        const hit = findTypeAhead(options.map(o => o.textContent || ''), buf, current);
        if (hit < 0) return;
        e.preventDefault();
        const el = options[hit];
        if (el.tabIndex < 0 && el.tagName !== 'BUTTON') el.setAttribute('tabindex', '-1');
        el.focus({ preventScroll: true });
        if (el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
}

/** Installs it once for the whole app (App.jsx). */
export function useGlobalTypeAhead() {
    useEffect(() => installGlobalTypeAhead(), []);
}
