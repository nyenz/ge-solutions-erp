// PATH: erp-frontend/src/utils/dateTyping.js
// fix210 (David): the calendar pop-up has a small box where a date can be typed instead of clicked.
// readTypedDate() turns what was typed into 'yyyy-mm-dd' (the value every date box uses), or explains what is wrong.
// Day comes first (Uganda writes 14/03/2019). Separators may be / - . or a space. A two-digit year is read as
// 20xx when that is not in the future, otherwise 19xx (so 19 -> 2019, 85 -> 1985).

const pad = (n) => String(n).padStart(2, '0');

/** { value: 'yyyy-mm-dd' } for a real date, { error: 'plain sentence' } otherwise, {} for an empty box */
export function readTypedDate(text, now = new Date()) {
    const t = String(text || '').trim();
    if (!t) return {};
    const hit = /^(\d{1,2})[/\-. ]+(\d{1,2})[/\-. ]+(\d{2}|\d{4})$/.exec(t);
    if (!hit) return { error: 'Type the date as day/month/year, for example 14/03/2019.' };
    const d = +hit[1], m = +hit[2];
    let y = +hit[3];
    if (hit[3].length === 2) {
        const thisYear = now.getFullYear() % 100;
        y = (y <= thisYear ? 2000 : 1900) + y;
    }
    if (m < 1 || m > 12) return { error: 'The month must be from 1 to 12.' };
    const last = new Date(y, m, 0).getDate();
    if (d < 1 || d > last) return { error: 'That month has only ' + last + ' days.' };
    if (y < 1900 || y > 2100) return { error: 'The year looks wrong.' };
    return { value: y + '-' + pad(m) + '-' + pad(d) };
}
