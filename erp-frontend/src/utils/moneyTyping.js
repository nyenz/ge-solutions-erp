// PATH: erp-frontend/src/utils/moneyTyping.js
// fix285 (David): money boxes show the commas WHILE you type (1500000 shows as 1,500,000). The box keeps the cursor in
// the same place among the digits. Only digits are kept: anything else is refused out loud by the box (fix199 rule:
// a box never changes what was typed without saying so).

/** Groups the digits with commas: '1500000' -> '1,500,000'. Leading zeros are dropped ('007' -> '7'). */
export function withCommas(digits) {
    let t = String(digits ?? '').trim();
    if (/^\d+\.\d*$/.test(t)) t = String(Math.round(Number(t)));   // a saved amount such as 15000.00 is whole shillings
    const d = t.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
    return d.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * One key press in a money box. text = what the box holds now, caret = where the cursor is.
 * Returns { ok, digits, shown, caret } -- ok is false when a character other than a digit, comma or space was typed.
 */
export function typeMoney(text, caret) {
    const t = String(text ?? '');
    if (!/^[0-9,\s]*$/.test(t)) return { ok: false };
    const before = t.slice(0, Math.max(0, caret ?? t.length)).replace(/\D/g, '').replace(/^0+(?=\d)/, '').length;
    const digits = t.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
    const shown = withCommas(digits);
    let pos = 0, seen = 0;
    while (pos < shown.length && seen < before) { if (/\d/.test(shown[pos])) seen++; pos++; }
    return { ok: true, digits, shown, caret: pos };
}
