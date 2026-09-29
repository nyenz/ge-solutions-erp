// PATH: erp-frontend/src/hooks/useTableScrollHandoff.js
// fix146: the Project Ledger scroll behaviour as ONE shared hook.
//   scrolling DOWN -> the page scrolls first, the table takes over at the page bottom
//   scrolling UP   -> the table scrolls first, the page takes over at the table top
// Usage:  const tableRef = useTableScrollHandoff();  <div className={styles.tableScroll} ref={tableRef}>
// It is a callback ref, so it also works when the table only appears after loading.
// Pair it with CSS: .tableScroll { max-height; overflow:auto; overscroll-behavior:contain }
// and a sticky <th> (see LedgerPage.module.css).
import { useCallback, useRef } from 'react';

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
            if (!pageAtBottom()) { pageScroll.scrollTop += clampStep(deltaY); e.preventDefault(); return; }
            if (tableAtBottom()) return;
            tableScroll.scrollTop += clampStep(deltaY);
            e.preventDefault();
        } else if (deltaY < 0) {
            if (!tableAtTop()) { tableScroll.scrollTop += clampStep(deltaY); e.preventDefault(); return; }
            if (pageAtTop()) return;
            pageScroll.scrollTop += clampStep(deltaY);
            e.preventDefault();
        }
    };
    const handleWheel = (e) => routeDelta(normalizeWheelDelta(e), e);
    let touchLastY = 0;
    const handleTouchStart = (e) => { touchLastY = e.touches[0].clientY; };
    const handleTouchMove = (e) => {
        const currentY = e.touches[0].clientY;
        const deltaY = touchLastY - currentY;
        touchLastY = currentY;
        routeDelta(deltaY, e);
    };
    tableScroll.addEventListener('wheel', handleWheel, { passive: false });
    tableScroll.addEventListener('touchstart', handleTouchStart, { passive: true });
    tableScroll.addEventListener('touchmove', handleTouchMove, { passive: false });
    return () => {
        tableScroll.removeEventListener('wheel', handleWheel);
        tableScroll.removeEventListener('touchstart', handleTouchStart);
        tableScroll.removeEventListener('touchmove', handleTouchMove);
    };
}

export default function useTableScrollHandoff() {
    const cleanupRef = useRef(null);
    return useCallback((node) => {
        if (cleanupRef.current) { cleanupRef.current(); cleanupRef.current = null; }
        if (node) cleanupRef.current = attach(node);
    }, []);
}
