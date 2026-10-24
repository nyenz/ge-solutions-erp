// PATH: erp-frontend/src/utils/fieldError.js
// fix213 (David, 19 Oct 2026): when a form is refused, the box that is wrong is marked (a soft red ring, its label turns
// red, one gentle nudge) and the page scrolls to it and puts the cursor in it. The mark goes away as soon as the box is
// changed. Works on any page: the box is found by its accessible name (aria-label) or by the text of its label.
//
//   flagField('Plot Number')                       -> the box labelled "Plot Number"
//   flagField('NIN of Client 2')                   -> the NIN box on the 2nd client row
//   flagField('Title date', { section: 'Title' })  -> opens the closed panel whose heading contains "Title" first
//   flagField(fieldForError(err, MAP))             -> the box named for a server answer such as "PLOT_TAKEN: ..."

import { calmMotion } from './motion.js';

const ATTR = 'data-field-error';
const norm = (t) => String(t || '').replace(/[*:]/g, '').replace(/\s+/g, ' ').trim().toLowerCase();

function findControl(name, root) {
    const want = norm(name);
    if (!want) return null;
    const controls = root.querySelectorAll('input, textarea, select, button, [role="combobox"], [role="button"], [contenteditable="true"]');
    for (const el of controls) {
        if (norm(el.getAttribute('aria-label')) === want && el.offsetParent !== null) return el;
    }
    for (const lab of root.querySelectorAll('label, [data-field-label]')) {
        // a label that wraps its box: compare only the label's own words (not the words of a list inside it)
        const words = lab.querySelector('[class*="label" i]') || lab;
        if (norm(words.textContent) !== want || lab.offsetParent === null) continue;
        const forId = lab.getAttribute('for');
        if (forId) { const el = root.querySelector('#' + CSS.escape(forId)); if (el) return el; }
        const inside = lab.querySelector('input, textarea, select, [role="combobox"], button');
        if (inside) return inside;
        const box = lab.parentElement;
        const el = box && box.querySelector('input, textarea, select, [role="combobox"], button');
        return el || lab;
    }
    return null;
}

function wrapperOf(el) {
    // the field's own box: the closest element whose class name mentions "field" (CSS-module names keep it), else the parent
    const w = el.closest('[class*="field" i], [class*="Field"]');
    return w && w !== document.body ? w : (el.parentElement || el);
}

function openSection(hint, root) {
    const h = norm(hint);
    for (const head of root.querySelectorAll('[aria-expanded="false"]')) {
        if (norm(head.textContent).includes(h)) { head.click(); return true; }
    }
    return false;
}

/** No single box to point at (for example "add at least one document"): mark the whole panel instead. */
function markSection(hint, root) {
    const h = norm(hint);
    for (const head of root.querySelectorAll('[aria-expanded="true"]')) {
        if (!norm(head.textContent).includes(h)) continue;
        const panel = head.closest('section') || head.parentElement;
        return mark(panel.querySelector('button, input') || head, panel);
    }
    return false;
}

export function clearFieldErrors(root = document) {
    root.querySelectorAll('[' + ATTR + ']').forEach(n => n.removeAttribute(ATTR));
}

function mark(el, boxOverride) {
    const box = boxOverride || wrapperOf(el);
    clearFieldErrors();
    box.setAttribute(ATTR, '');
    const done = () => { box.removeAttribute(ATTR); box.removeEventListener('input', done, true); box.removeEventListener('change', done, true); };
    box.addEventListener('input', done, true);
    box.addEventListener('change', done, true);
    const calm = calmMotion();   // fix226: also Settings > Animation = REDUCED
    box.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'center' });
    const focusable = el.matches('input, textarea, select, button, [tabindex]') ? el : box.querySelector('input, textarea, select, button');
    if (focusable) setTimeout(() => { try { focusable.focus({ preventScroll: true }); } catch { /* old browser */ } }, calm ? 0 : 380);
    return true;
}

/** fix241 (David, D2): a box can be in the page but inside a FOLDED panel (its body is 0 px high). Then it is not shown. */
function hiddenNow(el) {
    if (!el || el.offsetParent === null) return true;
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
        const cs = getComputedStyle(n);
        if (cs.display === 'none' || cs.visibility === 'hidden') return true;
        if (n.clientHeight === 0 && cs.overflow !== 'visible') return true;
    }
    return false;
}

/** fix241: opens the folded panel that holds the box (the closest section's own "open" header), then marks the box. */
function revealAndMark(el, section, root) {
    if (section && openSection(section, root)) { setTimeout(() => mark(el), 380); return true; }
    const sec = el.closest('section, [class*="panel" i], [class*="Panel"]');
    const head = sec && Array.from(sec.querySelectorAll('[aria-expanded="false"]')).find(h => !h.contains(el));
    if (head) { head.click(); setTimeout(() => mark(el), 380); return true; }
    return mark(el);
}

/** Marks the box and scrolls to it. Returns true when the box was found. Never throws. */
export function flagField(name, { section, root = document } = {}) {
    try {
        if (!name && !section) return false;
        const el = name ? findControl(name, root) : null;
        if (el && hiddenNow(el)) return revealAndMark(el, section, root);
        if (el) return mark(el);
        if (section && openSection(section, root)) {
            // the panel draws its boxes on the next paint
            later(() => {
                const again = name ? findControl(name, root) : null;
                if (again) mark(again); else markSection(section, root);
            });
            return true;
        }
        if (section) return markSection(section, root);
    } catch { /* never block the message itself */ }
    return false;
}

/** Marks the box with this element id (for pages whose boxes already have ids). fix224: when the box is inside a
 *  closed panel, `section` (words of the panel heading) opens it first, then the box is marked. */
export function flagId(id, { section } = {}) {
    try {
        const el = id && document.getElementById(id);
        if (el && hiddenNow(el)) return revealAndMark(el, section, document);
        if (el) return mark(el);
        if (section && openSection(section, document)) {
            later(() => { const again = document.getElementById(id); if (again) mark(again); else markSection(section, document); });
            return true;
        }
    } catch { /* never block the message itself */ }
    return false;
}

/** fix224: run after the opened panel has drawn its boxes (two paints, then once more a little later if needed). */
function later(fn) {
    let done = false;
    const once = () => { if (!done) { done = true; fn(); } };
    requestAnimationFrame(() => requestAnimationFrame(() => { try { once(); } catch { /* ignore */ } }));
    setTimeout(() => { if (!done) once(); }, 250);
}

/** The code word at the front of a server answer ("PLOT_TAKEN: ..."), or ''. */
export function errorCode(err) {
    const d = err && err.response && err.response.data;
    const raw = d && typeof d === 'object' ? (d.message || d.error || '') : (typeof d === 'string' ? d : '');
    return (String(raw).match(/^([A-Z][A-Z0-9_]{2,}):/) || [])[1] || '';
}

/** Server codes that point at one box. A page passes its own map to add or change names. */
export const FIELD_FOR_CODE = {
    PLOT_TAKEN: ['Plot Number', 'Title'], PLOT_NUMBER_REQUIRED: ['Plot Number', 'Title'], PLOT_REQUIRED: ['Plot Number', 'Title'],
    BLOCK_REQUIRED: ['Block', 'Title'], TENURE_REQUIRED: ['Tenure', 'Title'],
    AREA_REQUIRED: ['Area (hectares)', 'Title'], TITLE_DATE_REQUIRED: ['Title date', 'Title'], TITLE_DATE_INVALID: ['Title date', 'Title'],
    DISTRICT_REQUIRED: ['District', 'Location'],
    INVOICE_NUMBER_TAKEN: ['Invoice Number', 'Financ'], CONTRACT_NUMBER_TAKEN: ['Contract Number', 'Financ'],
    PRICE_REQUIRED: ['Total Cost', 'Financ'], STORAGE_PAID_INVALID: ['Storage Fees Already Paid', 'Financ'],
    SUBDIVISIONS_REQUIRED: ['Number of Subdivisions'], NIN_TAKEN: ['NIN of Client 1', 'Client'], NIN_CONFLICT: ['NIN of Client 1', 'Client'],
    NIN_REQUIRED: ['NIN of Client 1', 'Client'], PHONE_INVALID: ['Phone of Client 1', 'Client'], EMAIL_INVALID: ['Email of Client 1', 'Client'],
    PAYMENT_METHOD_REQUIRED: ['Payment Method', 'Financ'], PAYMENT_METHOD_INVALID: ['Payment Method', 'Financ'],   // fix214
    MONEY_NEEDS_START: ['Invoice Number', 'Financ'], AREA_NOT_A_NUMBER: ['Area (hectares)', 'Location'],   // fix224
};

/** Marks the box a server refusal is about (when the code points at one). */
export function flagServerError(err, map = {}) {
    const code = errorCode(err);
    const hit = (map && map[code]) || FIELD_FOR_CODE[code];
    if (!hit) return false;
    const [name, section] = Array.isArray(hit) ? hit : [hit];
    return flagField(name, { section });
}

const STOP = new Set(['the', 'and', 'for', 'optional', 'required', 'ugx', 'this', 'that', 'with', 'from', 'your', 'must', 'more', 'than', 'only', 'are', 'not', 'can', 'cannot']);
const wordsOf = (t) => norm(t).replace(/[^a-z0-9 ]/g, ' ').split(' ').filter(w => w.length >= 3 && !STOP.has(w));

/** fix241 (David, test D1): a popup refused its save. Find the box the message is about by the words of the box labels
 *  (for example "ENTER A VALID AMOUNT." -> the box labelled AMOUNT RECEIVED), then mark it and scroll to it inside the
 *  popup. Returns true when a box was marked. Never throws. */
export function flagByWords(message, root = document) {
    try {
        const msg = new Set(wordsOf(message));
        if (msg.size === 0) return false;
        let best = null, bestScore = 0;
        const consider = (labelText, el) => {
            const w = wordsOf(labelText);
            if (!w.length || !el || el.offsetParent === null) return;
            const score = w.filter(x => msg.has(x)).length;
            if (score > bestScore) { best = el; bestScore = score; }
        };
        root.querySelectorAll('label, [data-field-label]').forEach(lab => {
            const forId = lab.getAttribute('for');
            let el = forId ? root.querySelector('#' + CSS.escape(forId)) : null;
            if (!el) el = lab.querySelector('input, textarea, select, [role="combobox"], button');
            if (!el && lab.parentElement) el = lab.parentElement.querySelector('input, textarea, select, [role="combobox"], button');
            consider(lab.textContent, el);
        });
        root.querySelectorAll('[aria-label]').forEach(el => {
            if (el.matches('input, textarea, select, [role="combobox"], button')) consider(el.getAttribute('aria-label'), el);
        });
        return best ? mark(best) : false;
    } catch { return false; }
}
