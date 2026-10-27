// PATH: erp-frontend/src/utils/upperCase.js
// fix263 (David, test note): words typed into the form boxes are kept in CAPITALS, like the paper forms -- names,
// places, NIN, plot and block, titles. Never touched: e-mail addresses, user names, keys / passwords, search boxes,
// web links, references, number and date boxes, the notes (big text boxes), and anything inside [data-keep-case].
// The pure rule lives here so it can be tested; utils/../components/common/globalUpper.js applies it when a box is left.

const SKIP_WORDS = /(mail|user|login|pass|key|search|url|link|web|reference|ref\b|code|token|otp)/i;

/** true when this text box should keep what was typed exactly as it is */
export function keepsCase(info) {
    const type = String(info.type || 'text').toLowerCase();
    if (type !== 'text') return true;
    if (info.inKeepCase) return true;
    const hay = [info.name, info.id, info.autoComplete, info.ariaLabel, info.placeholder, info.inputMode].filter(Boolean).join(' ');
    if (SKIP_WORDS.test(hay)) return true;
    if (String(info.inputMode || '').toLowerCase() === 'email') return true;
    return false;
}

/** the capitals version, or null when nothing changes (e-mail looking text is left alone) */
export function toUpperValue(value) {
    const v = String(value == null ? '' : value);
    if (!/[a-z]/.test(v)) return null;
    if (/@/.test(v) || /^https?:\/\//i.test(v) || /^www\./i.test(v)) return null;
    return v.toUpperCase();
}
