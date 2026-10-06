// PATH: erp-frontend/src/utils/reportPeriod.js
// fix190: the first and last day of a report period, as yyyy-mm-dd on THIS device's calendar.
// Before fix190 the days were turned into London time (toISOString), so in Uganda (3 hours ahead) every period
// started and ended one day early: "LAST MONTH" in October gave 31 Aug - 29 Sep.

/** yyyy-mm-dd of a date on the device's own calendar (never UTC). */
export const localISO = (d = new Date()) =>
    d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');

/**
 * [firstDay, lastDay] for a period name, or null when the period has no dates (ALL TIME, or CUSTOM not filled in).
 * `now` is only passed in by the tests.
 */
export function periodRange(period, fromArg, toArg, now = new Date()) {
    const y = now.getFullYear(), m = now.getMonth(), d = now.getDate();
    const mon = (now.getDay() + 6) % 7;          // days since Monday
    let start = null, end = null;
    if (period === 'TODAY') { start = now; end = now; }
    else if (period === 'THIS WEEK') { start = new Date(y, m, d - mon); end = now; }
    else if (period === 'LAST WEEK') { start = new Date(y, m, d - mon - 7); end = new Date(y, m, d - mon - 1); }
    else if (period === 'THIS MONTH') { start = new Date(y, m, 1); end = now; }
    else if (period === 'LAST MONTH') { start = new Date(y, m - 1, 1); end = new Date(y, m, 0); }
    else if (period === 'THIS QUARTER') { start = new Date(y, Math.floor(m / 3) * 3, 1); end = now; }
    else if (period === 'THIS YEAR') { start = new Date(y, 0, 1); end = now; }
    else if (period === 'LAST YEAR') { start = new Date(y - 1, 0, 1); end = new Date(y - 1, 11, 31); }
    else if (period === 'CUSTOM') {
        // the two boxes already hold yyyy-mm-dd; they are used as typed (swapped when the wrong way round)
        let a = fromArg || '', b = toArg || '';
        if (a && b && a > b) { const t = a; a = b; b = t; }
        if (!a || !b) return null;
        return [a.slice(0, 10), b.slice(0, 10)];
    } else return null;
    return [localISO(start), localISO(end)];
}
