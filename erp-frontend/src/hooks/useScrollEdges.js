// PATH: erp-frontend/src/hooks/useScrollEdges.js
// fix183: ONE helper for every box that scrolls SIDEWAYS (tab bars, filter bars, legends, tables).
// It does three small jobs, the same way everywhere:
//   1. marks the box with data-more-left / data-more-right while there is more to see on that side.
//      index.css fades that edge, so people can SEE that the row continues (the scrollbar itself is hidden).
//   2. (rails only) lets a normal mouse wheel move the row sideways. Touch already works on its own.
//   3. (rails only) brings the picked tab into view when it changes.
// Usage:
//   const railRef = useScrollEdges({ wheel: true, activeKey: value });
//   <div ref={railRef} className={styles.tabDock}> ... </div>
// It returns a callback ref, so it also works for a box that only appears after loading.
import { useCallback, useEffect, useRef } from 'react';

const EDGE = 2;   // sub-pixel rounding on phones: never "stuck" one pixel short of the end

/** Writes data-more-left / data-more-right on el. Safe to call often. */
export function markEdges(el) {
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    const left = el.scrollLeft > EDGE;
    const right = max > EDGE && el.scrollLeft < max - EDGE;
    if (left) el.setAttribute('data-more-left', ''); else el.removeAttribute('data-more-left');
    if (right) el.setAttribute('data-more-right', ''); else el.removeAttribute('data-more-right');
}

/** Scrolls el sideways (never the page) so that child is fully in view, with a little room next to it. */
export function revealChild(el, child, smooth = true) {
    if (!el || !child) return;
    const box = el.getBoundingClientRect();
    const c = child.getBoundingClientRect();
    const pad = 28;
    let next = el.scrollLeft;
    if (c.left < box.left + pad) next -= (box.left + pad - c.left);
    else if (c.right > box.right - pad) next += (c.right - (box.right - pad));
    next = Math.max(0, Math.min(next, el.scrollWidth - el.clientWidth));
    if (Math.abs(next - el.scrollLeft) < 1) return;
    try { el.scrollTo({ left: next, behavior: smooth ? 'smooth' : 'auto' }); } catch { el.scrollLeft = next; }
}

export function attachScrollEdges(el, { wheel = false } = {}) {
    const onScroll = () => markEdges(el);
    el.addEventListener('scroll', onScroll, { passive: true });
    let ro = null;
    if (typeof ResizeObserver !== 'undefined') {
        ro = new ResizeObserver(onScroll);
        ro.observe(el);
        // the row inside can grow (a count arrives, a tab is added) without the box itself changing size
        Array.from(el.children).forEach(ch => ro.observe(ch));
    }
    window.addEventListener('resize', onScroll);
    let onWheel = null;
    if (wheel) {
        onWheel = (e) => {
            if (el.scrollWidth - el.clientWidth <= EDGE) return;             // nothing to scroll: leave the page alone
            if (e.ctrlKey || Math.abs(e.deltaX) >= Math.abs(e.deltaY)) return; // a real sideways gesture already works
            const before = el.scrollLeft;
            el.scrollLeft += e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
            if (el.scrollLeft !== before) e.preventDefault();                 // at the end the page scrolls as usual
        };
        el.addEventListener('wheel', onWheel, { passive: false });
    }
    if (wheel) el.setAttribute('data-rail', '');   // index.css turns the box into a one-line, sideways-scrolling rail
    markEdges(el);
    return () => {
        el.removeEventListener('scroll', onScroll);
        window.removeEventListener('resize', onScroll);
        if (ro) ro.disconnect();
        if (onWheel) el.removeEventListener('wheel', onWheel);
    };
}

const ACTIVE = '[aria-selected="true"], [aria-pressed="true"], [data-active="true"]';

export default function useScrollEdges({ wheel = false, activeKey } = {}) {
    const nodeRef = useRef(null);
    const cleanupRef = useRef(null);
    const ref = useCallback((node) => {
        if (cleanupRef.current) { cleanupRef.current(); cleanupRef.current = null; }
        nodeRef.current = node;
        if (node) {
            cleanupRef.current = attachScrollEdges(node, { wheel });
            revealChild(node, node.querySelector(ACTIVE), false);
            markEdges(node);
        }
    }, [wheel]);
    // the picked tab changed: bring it into view (never jumps the page up or down)
    useEffect(() => {
        const el = nodeRef.current;
        if (!el || activeKey === undefined) return undefined;
        const id = requestAnimationFrame(() => { revealChild(el, el.querySelector(ACTIVE)); markEdges(el); });
        return () => cancelAnimationFrame(id);
    }, [activeKey]);
    return ref;
}
