// PATH: erp-frontend/src/hooks/useTabMotion.js
// fix192: GENTLE MOVEMENT when a tab or filter changes. Two small helpers, used the same way on every page:
//
//   1. useTabThumb(activeKey)  -- the orange "pill" SLIDES from the old tab to the new one instead of jumping.
//        const rowRef = useTabThumb(value);
//        <div ref={rowRef} data-thumb-row> <span data-thumb aria-hidden="true" /> ...the tab buttons... </div>
//      The picked button is found by aria-selected / aria-pressed. The look of the pill is in index.css ([data-thumb]).
//      Until the pill has been measured the button keeps its own orange background, so nothing can look broken.
//
//   2. useSwapMotion(activeKey) -- the content under the tabs fades in and rises a few pixels when the tab changes.
//        const bodyRef = useSwapMotion(activeTab);
//        <main ref={bodyRef}> ... </main>
//      Nothing is re-made (typed text and scroll are kept); it is only a 0.22 second fade.
//
// Both respect Settings > Appearance > ANIMATION = reduced and the device's own "reduce motion" switch.
import { useCallback, useEffect, useLayoutEffect, useRef } from 'react';

const PICKED = ':scope > [aria-selected="true"], :scope > [aria-pressed="true"]';

export const motionOff = () => {
    try {
        if (document.documentElement.getAttribute('data-motion') === 'reduced') return true;
        return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    } catch { return true; }
};

/** Puts the pill behind the picked button of `row`. Safe to call often. */
export function placeThumb(row) {
    if (!row) return;
    const thumb = row.querySelector(':scope > [data-thumb]');
    const btn = row.querySelector(PICKED);
    if (!thumb || !btn || btn.offsetWidth === 0) { row.removeAttribute('data-thumb-ready'); return; }
    thumb.style.setProperty('--thumb-x', btn.offsetLeft + 'px');
    thumb.style.setProperty('--thumb-y', btn.offsetTop + 'px');
    thumb.style.setProperty('--thumb-w', btn.offsetWidth + 'px');
    thumb.style.setProperty('--thumb-h', btn.offsetHeight + 'px');
    thumb.setAttribute('data-accent', btn.getAttribute('data-accent') || 'orange');
    if (!row.hasAttribute('data-thumb-ready')) {
        // first time: jump into place, THEN switch the movement on (no slide-in from the corner on page load)
        const on = () => row.setAttribute('data-thumb-ready', '');
        if (typeof requestAnimationFrame === 'function') requestAnimationFrame(() => requestAnimationFrame(on)); else on();
    }
}

export function useTabThumb(activeKey) {
    const nodeRef = useRef(null);
    const roRef = useRef(null);
    const ref = useCallback((node) => {
        if (roRef.current) { roRef.current.disconnect(); roRef.current = null; }
        nodeRef.current = node;
        if (!node) return;
        placeThumb(node);
        if (typeof ResizeObserver !== 'undefined') {
            // a count arrives, the font loads, the window or the interface size changes: the pill follows its button
            const ro = new ResizeObserver(() => placeThumb(node));
            ro.observe(node);
            Array.from(node.children).forEach(ch => { if (!ch.hasAttribute('data-thumb')) ro.observe(ch); });
            roRef.current = ro;
        }
    }, []);
    useLayoutEffect(() => { placeThumb(nodeRef.current); });
    useEffect(() => () => { if (roRef.current) roRef.current.disconnect(); }, []);
    void activeKey;   // the key is only here so the caller's intent is clear; the layout effect runs on every render
    return ref;
}

export function useSwapMotion(activeKey) {
    const ref = useRef(null);
    const first = useRef(true);
    useEffect(() => {
        if (first.current) { first.current = false; return; }
        const el = ref.current;
        if (!el || typeof el.animate !== 'function' || motionOff()) return;
        try {
            el.animate(
                [{ opacity: 0.25, transform: 'translateY(6px)' }, { opacity: 1, transform: 'translateY(0)' }],
                { duration: 220, easing: 'cubic-bezier(0.2, 0.7, 0.2, 1)' },
            );
        } catch { /* an old browser: the tab still changes, just without the fade */ }
    }, [activeKey]);
    return ref;
}
