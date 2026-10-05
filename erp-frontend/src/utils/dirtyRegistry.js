// PATH: erp-frontend/src/utils/dirtyRegistry.js
// fix181 (21.9): which forms on the page have unsaved changes. The router guard only catches page changes, but
// SIGN OUT reloads the page, so the Header asks here first and shows its own short confirm.
const dirty = new Set();
let leaving = false;

export const setDirty = (key, isDirty) => { if (isDirty) dirty.add(key); else dirty.delete(key); };
export const anyDirty = () => dirty.size > 0;
/** Called after the person confirmed: the browser's own "leave this page?" box is skipped once. */
export const allowLeave = () => { leaving = true; };
export const isLeaving = () => leaving;
