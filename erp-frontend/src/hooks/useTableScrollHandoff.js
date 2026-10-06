// PATH: erp-frontend/src/hooks/useTableScrollHandoff.js
// fix146: the Project Ledger scroll behaviour as ONE shared hook.
//   scrolling DOWN -> the page scrolls first, the table takes over at the page bottom
//   scrolling UP   -> the table scrolls first, the page takes over at the table top
// Usage:  const tableRef = useTableScrollHandoff();  <div className={styles.tableScroll} ref={tableRef}>
// It is a callback ref, so it also works when the table only appears after loading.
// Pair it with CSS: .tableScroll { max-height; overflow:auto; overscroll-behavior:contain }
// and a sticky <th> (see LedgerPage.module.css).
//
// fix183: SIDEWAYS scrolling now works on a phone. Before, every finger move was taken over by the up/down rule
// above (even a mostly-sideways one), so a wide table could not be pulled left or right and its last columns
// looked "cut off". Now the first few pixels of a touch decide the direction: a sideways drag is left to the
// browser, an up/down drag keeps the rule above. The hook also marks the box with data-more-left /
// data-more-right (see hooks/useScrollEdges.js), which index.css uses to fade the edge that has more columns.
// Ledger and Client Ledger used to carry their own copy of this code; they use this hook now.
import { useCallback, useRef } from 'react';
import { attachScrollEdges } from './useScrollEdges';

function findScrollParent(el) {
    let node = el ? el.parentElement : null;
    while (node && node !== document.body && node !== document.documentElement) {
        const overflowY = window.getComputedStyle(node).overflowY;
        if (overflowY === 'auto' || overflowY === 'scroll') return node;
        node = node.parentElement;
    }
    return document.scrollingElement || document.documentElement;
}

function attach(tableScroll) {
    const pageScroll = findScrollParent(tableScroll);
    const EDGE_TOLERANCE = 2;
    const MAX_STEP_PX = 120;
    const AXIS_SLOP_PX = 6;   // how far a finger moves before we decide "sideways" or "up/down"
    const pageAtTop = () => pageScroll.scrollTop <= EDGE_TOLERANCE;
    const pageAtBottom = () =>
        pageScroll.scrollTop + pageScroll.clientHeight >= pageScroll.scrollHeight - EDGE_TOLERANCE;
    const tableAtTop = () => tableScroll.scrollTop <= EDGE_TOLERANCE;
    const tableAtBottom = () =>
        tableScroll.scrollTop + tableScroll.clientHeight >= tableScroll.scrollHeight - EDGE_TOLERANCE;
    const normalizeWheelDelta = (e) => {
        if (e.deltaMode === 1) return e.deltaY * 16;
        if (e.deltaMode === 2) return e.deltaY * window.innerHeight;
        return e.deltaY;
    };
    const clampStep = (px) => Math.sign(px) * Math.min(Math.abs(px), MAX_STEP_PX);
    const routeDelta = (deltaY, e) => {
        if (deltaY > 0) {
            if (!pageAtBottom()) { pageScroll.scrollTop += clampStep(deltaY); if (e.cancelable) e.preventDefault(); return; }
            if (tableAtBottom()) return;
            tableScroll.scrollTop += clampStep(deltaY);
            if (e.cancelable) e.preventDefault();
        } else if (deltaY < 0) {
            if (!tableAtTop()) { tableScroll.scrollTop += clampStep(deltaY); if (e.cancelable) e.preventDefault(); return; }
            if (pageAtTop()) return;
            pageScroll.scrollTop += clampStep(deltaY);
            if (e.cancelable) e.preventDefault();
        }
    };
    const handleWheel = (e) => {
        // a sideways wheel / trackpad swipe (or Shift + wheel) belongs to the table's own left-right scroll
        if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
        routeDelta(normalizeWheelDelta(e), e);
    };
    let startX = 0;
    let startY = 0;
    let touchLastY = 0;
    let axis = null;   // null = not decided yet, 'x' = sideways (browser scrolls), 'y' = up/down (rule above)
    const handleTouchStart = (e) => {
        const t = e.touches[0];
        startX = t.clientX; startY = t.clientY; touchLastY = t.clientY;
        axis = null;
    };
    const handleTouchMove = (e) => {
        const t = e.touches[0];
        if (axis === null) {
            const dx = Math.abs(t.clientX - startX);
            const dy = Math.abs(t.clientY - startY);
            if (dx < AXIS_SLOP_PX && dy < AXIS_SLOP_PX) return;
            const canGoSideways = tableScroll.scrollWidth - tableScroll.clientWidth > EDGE_TOLERANCE;
            axis = (canGoSideways && dx > dy) ? 'x' : 'y';
            touchLastY = t.clientY;
        }
        if (axis === 'x') return;   // the browser moves the table left / right by itself
        const deltaY = touchLastY - t.clientY;
        touchLastY = t.clientY;
        routeDelta(deltaY, e);
    };
    tableScroll.addEventListener('wheel', handleWheel, { passive: false });
    tableScroll.addEventListener('touchstart', handleTouchStart, { passive: true });
    tableScroll.addEventListener('touchmove', handleTouchMove, { passive: false });
    const detachEdges = attachScrollEdges(tableScroll);
    tableScroll.setAttribute('data-scroll-x', 'table');
    return () => {
        tableScroll.removeEventListener('wheel', handleWheel);
        tableScroll.removeEventListener('touchstart', handleTouchStart);
        tableScroll.removeEventListener('touchmove', handleTouchMove);
        detachEdges();
    };
}

export default function useTableScrollHandoff() {
    const cleanupRef = useRef(null);
    return useCallback((node) => {
        if (cleanupRef.current) { cleanupRef.current(); cleanupRef.current = null; }
        if (node) cleanupRef.current = attach(node);
    }, []);
}
