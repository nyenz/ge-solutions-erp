// PATH: erp-frontend/src/utils/format.js
// fix284 (B3): ONE date style and ONE money style for everything a person reads on screen or on a print-out.
//   day        "5 Oct 2026"
//   day + time "5 Oct 2026, 14:05"   (24-hour clock)
//   money      "1,234,567"  (commas, whole shillings, the same on every phone and computer)
// Dates are read straight from the server's text (it is already Uganda time), so nothing is shifted by the device's
// own time zone or language. Files meant for a computer (CSV, the audit quote) keep the plain 2026-10-05 form on purpose.

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const ISO = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/;

/** { y, m, d, hh, mm } from a server text ("2026-10-05" or "2026-10-05T14:05:00") or a Date; null when unreadable. */
const parts = (v) => {
    if (v === null || v === undefined || v === '') return null;
    if (v instanceof Date) {
        if (Number.isNaN(v.getTime())) return null;
        const p2 = (n) => String(n).padStart(2, '0');
        return { y: String(v.getFullYear()), m: p2(v.getMonth() + 1), d: p2(v.getDate()), hh: p2(v.getHours()), mm: p2(v.getMinutes()) };
    }
    const text = String(v);
    // a text that names its own zone ("...Z" or "+03:00") is a real moment: show it in the device's own time
    if (/(Z|[+-]\d{2}:?\d{2})$/.test(text) && text.includes('T')) return parts(new Date(text));
    const m = text.match(ISO);
    return m ? { y: m[1], m: m[2], d: m[3], hh: m[4], mm: m[5] } : null;
};

/** "5 Oct 2026" ('' when there is no date). */
export const fmtDay = (v) => {
    const p = parts(v);
    return p ? Number(p.d) + ' ' + MONTHS[Number(p.m) - 1] + ' ' + p.y : '';
};

/** "14:05" ('' when the text has no time). */
export const fmtTime = (v) => {
    const p = parts(v);
    return p && p.hh ? p.hh + ':' + p.mm : '';
};

/** "5 Oct 2026, 14:05", or just the day when there is no time. */
export const fmtDayTime = (v) => {
    const day = fmtDay(v);
    const time = fmtTime(v);
    return day && time ? day + ', ' + time : day;
};

/** Whole shillings with commas: 1234567 -> "1,234,567". Empty or unreadable counts as 0. */
export const fmtMoney = (n) => {
    const x = Number(n || 0);
    return (Number.isFinite(x) ? x : 0).toLocaleString('en-US');
};

/** "UGX 1,234,567" */
export const fmtUgx = (n) => 'UGX ' + fmtMoney(n);
