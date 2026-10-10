// PATH: erp-frontend/src/utils/money.js
// fix199 (David, test note 23): a money box must NEVER change what was typed without saying so. Before, "1500.50"
// silently became 150050 (every character that was not a digit was thrown away). Now a box keeps exactly what was
// typed, and anything other than digits (commas and spaces are fine) is refused with this message.

export const MONEY_BAD = 'Whole shillings only. Type the digits without a dot, cents or letters (commas are fine).';

/** { ok, value } -- value is the plain digits ('' when the box is empty); ok is false for anything else. */
export function readShillings(text) {
    const t = String(text ?? '').trim();
    if (!t) return { ok: true, value: '' };
    if (!/^[0-9][0-9,\s]*$/.test(t)) return { ok: false, value: null };
    return { ok: true, value: t.replace(/[,\s]/g, '') };
}

/** true when the text is empty or plain whole shillings. */
export const isShillings = (text) => readShillings(text).ok;
