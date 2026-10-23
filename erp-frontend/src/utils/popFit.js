// PATH: erp-frontend/src/utils/popFit.js
// fix226 (David): "the calendar seems to be cut off ... make sure such things don't happen ... whole app".
// Every pop-out (calendar, pick-list, suggestion list) is measured AFTER it has drawn and moved so all of it is on the
// screen: under its box when there is room, else above it, else as high as needed. Positions are in the CSS pixels of
// the zoomed #root (Interface size), like the rest of the pop-ups.
import { uiScale } from '../components/common/portalRoot.js';

const GAP = 6, EDGE = 8;

/** Where a pop-out of this size should go next to this box. Pure (tested). */
export function fitBelowOrAbove(anchor, pop, view) {
    const { top: aTop, bottom: aBottom, left: aLeft } = anchor;
    const { width: w, height: h } = pop;
    const { width: vw, height: vh } = view;
    const left = Math.max(EDGE, Math.min(aLeft, vw - w - EDGE));
    let top = aBottom + GAP;
    let above = false;
    if (top + h > vh - EDGE) {
        if (aTop - GAP - h >= EDGE) { top = aTop - GAP - h; above = true; }
        else top = Math.max(EDGE, vh - h - EDGE);   // taller than both sides: as much as fits, top kept on screen
    }
    return { top, left, above, maxHeight: vh - 2 * EDGE };
}

/** Measures the drawn pop-out and the box it belongs to, then returns its fitted place (zoomed #root pixels). */
export function fitPopup(anchorEl, popEl) {
    if (!anchorEl || !popEl || typeof window === 'undefined') return null;
    const k = uiScale();
    const a = anchorEl.getBoundingClientRect();
    const p = popEl.getBoundingClientRect();
    return fitBelowOrAbove(
        { top: a.top / k, bottom: a.bottom / k, left: a.left / k },
        { width: p.width / k, height: p.height / k },
        { width: window.innerWidth / k, height: window.innerHeight / k },
    );
}

/**
 * fix226: for a list drawn right under its box (position: absolute). Returns an inline style: open UPWARD when there
 * is not enough room below and more above, and never taller than the room on the chosen side (the list scrolls).
 * Call after the list has drawn (in a layout effect) with the box and the list elements.
 */
export function flipStyle(boxEl, listEl) {
    if (!boxEl || !listEl || typeof window === 'undefined') return null;
    const k = uiScale();
    const b = boxEl.getBoundingClientRect();
    const want = listEl.scrollHeight;                      // its full height (screen pixels)
    const vh = window.innerHeight;
    const below = vh - b.bottom - 4 - EDGE;
    const above = b.top - 4 - EDGE;
    const up = want > below && above > below;
    const room = Math.max(120, up ? above : below);
    return up
        ? { top: 'auto', bottom: 'calc(100% + 4px)', maxHeight: Math.round(room / k) + 'px', overflowY: 'auto' }
        : { maxHeight: Math.round(room / k) + 'px', overflowY: 'auto' };
}

/** fix226: the same, written straight onto the list (no re-render). Safe to call with missing elements. */
export function applyFlip(boxEl, listEl) {
    if (!listEl) return;
    listEl.style.top = ''; listEl.style.bottom = ''; listEl.style.maxHeight = ''; listEl.style.overflowY = '';
    const f = flipStyle(boxEl, listEl);
    if (f) Object.assign(listEl.style, f);
}

/** fix226: moves a fixed pop-out (calendar) so all of it is on screen, straight onto the element. */
export function applyFit(anchorEl, popEl) {
    const f = fitPopup(anchorEl, popEl);
    if (f) { popEl.style.top = f.top + 'px'; popEl.style.left = f.left + 'px'; }
}
