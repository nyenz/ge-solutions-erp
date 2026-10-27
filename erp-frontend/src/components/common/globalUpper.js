// PATH: erp-frontend/src/components/common/globalUpper.js
// fix263 (David): ONE listener, installed in App.jsx: when a form text box is left, its words turn into CAPITALS (see
// utils/upperCase.js for what is never touched). The page's own state is told through a normal input event, so saving
// sends the capitals. A box can opt out with data-keep-case (on itself or on any parent).
import { useEffect } from 'react';
import { keepsCase, toUpperValue } from '../../utils/upperCase';

const setter = typeof window !== 'undefined' ? Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set : null;

export function installGlobalUpper() {
    if (typeof document === 'undefined' || !setter) return () => {};
    const onLeave = (e) => {
        const el = e.target;
        if (!(el instanceof HTMLInputElement) || el.readOnly || el.disabled) return;
        if (keepsCase({ type: el.getAttribute('type'), name: el.name, id: el.id, autoComplete: el.getAttribute('autocomplete'),
            ariaLabel: el.getAttribute('aria-label'), placeholder: el.placeholder, inputMode: el.getAttribute('inputmode'),
            inKeepCase: !!el.closest('[data-keep-case]') })) return;
        const next = toUpperValue(el.value);
        if (next === null) return;
        setter.call(el, next);
        el.dispatchEvent(new Event('input', { bubbles: true }));
    };
    document.addEventListener('focusout', onLeave, true);
    return () => document.removeEventListener('focusout', onLeave, true);
}

export function useGlobalUpper() {
    useEffect(() => installGlobalUpper(), []);
}
