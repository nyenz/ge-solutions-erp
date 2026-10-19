// PATH: erp-frontend/src/utils/fieldError.js
// fix213 (David, 19 Oct 2026): when a form is refused, the box that is wrong is marked (a soft red ring, its label turns
// red, one gentle nudge) and the page scrolls to it and puts the cursor in it. The mark goes away as soon as the box is
// changed. Works on any page: the box is found by its accessible name (aria-label) or by the text of its label.
//
//   flagField('Plot Number')                       -> the box labelled "Plot Number"
//   flagField('NIN of Client 2')                   -> the NIN box on the 2nd client row
//   flagField('Title date', { section: 'Title' })  -> opens the closed panel whose heading contains "Title" first
//   flagField(fieldForError(err, MAP))             -> the box named for a server answer such as "PLOT_TAKEN: ..."

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
    const calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    box.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'center' });
    const focusable = el.matches('input, textarea, select, button, [tabindex]') ? el : box.querySelector('input, textarea, select, button');
    if (focusable) setTimeout(() => { try { focusable.focus({ preventScroll: true }); } catch { /* old browser */ } }, calm ? 0 : 380);
    return true;
}

/** Marks the box and scrolls to it. Returns true when the box was found. Never throws. */
export function flagField(name, { section, root = document } = {}) {
    try {
        if (!name && !section) return false;
        const el = name ? findControl(name, root) : null;
        if (el) return mark(el);
        if (section && openSection(section, root)) {
            // the panel draws its boxes on the next paint
            requestAnimationFrame(() => requestAnimationFrame(() => {
                const again = name ? findControl(name, root) : null;
                if (again) mark(again); else markSection(section, root);
            }));
            return true;
        }
        if (section) return markSection(section, root);
    } catch { /* never block the message itself */ }
    return false;
}

/** Marks the box with this element id (for pages whose boxes already have ids). */
export function flagId(id) {
    try { const el = id && document.getElementById(id); return el ? mark(el) : false; } catch { return false; }
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
};

/** Marks the box a server refusal is about (when the code points at one). */
export function flagServerError(err, map = {}) {
    const code = errorCode(err);
    const hit = (map && map[code]) || FIELD_FOR_CODE[code];
    if (!hit) return false;
    const [name, section] = Array.isArray(hit) ? hit : [hit];
    return flagField(name, { section });
}
