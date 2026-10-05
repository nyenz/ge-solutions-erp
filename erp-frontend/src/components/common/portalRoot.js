// PATH: erp-frontend/src/components/common/portalRoot.js
// fix181 (15.1b): every pop-up is drawn INSIDE #root, so the Interface size (zoom on #root) applies to it too.
// Positions measured with getBoundingClientRect are screen pixels; inside the zoomed #root they must be divided by
// the scale (checked in Chromium at 125%), which is what toZoomed() does.
export const portalRoot = () => (typeof document === 'undefined' ? null : (document.getElementById('root') || document.body));

export const uiScale = () => {
    if (typeof document === 'undefined') return 1;
    const v = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui-scale'));
    return Number.isFinite(v) && v > 0 ? v : 1;
};

/** Screen pixels -> CSS pixels inside the zoomed #root. */
export const toZoomed = (px) => px / uiScale();
