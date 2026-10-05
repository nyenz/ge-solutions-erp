// PATH: erp-frontend/src/utils/csv.js
// fix181 (13.8): ONE CSV writer for the Audit page and the Report Studio.
//  - commas, quotes and new lines are quoted (as before), and a UTF-8 BOM tells Excel the file is UTF-8;
//  - a TEXT cell that starts with = + - @ tab or carriage return gets a ' in front, so a note typed as
//    =HYPERLINK(...) is shown as text in Excel and never runs. Real numbers are left alone (money can be negative).
const FORMULA_START = /^[=+\-@\t\r]/;

export const csvCell = (v) => {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number' || typeof v === 'bigint') return String(v);
    let s = String(v);
    if (FORMULA_START.test(s)) s = "'" + s;
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};

export const toCSV = (headers, matrix) =>
    [headers.map(csvCell).join(','), ...matrix.map(r => r.map(csvCell).join(','))].join('\n');

/** "2026-10-04 22:39:00" from the server's zone-less time, with no time-zone conversion (10.6b). */
export const plainStamp = (v) => {
    if (!v) return '';
    const m = String(v).match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(:\d{2})?/);
    return m ? m[1] + ' ' + m[2] + (m[3] || ':00') : String(v);
};

export const downloadCSV = (filename, csv) => {
    // Excel reads a bare UTF-8 CSV as Latin-1 and mangles anything non-ASCII. The BOM is what tells it otherwise.
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
};
