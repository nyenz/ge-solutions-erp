// PATH: erp-frontend/src/utils/projectNumbers.js
// fix284 (B4): the ONE place that writes a project's invoice and contract number for a list row.
// A number that already starts with INV / CON / CTR is shown as typed; any other number gets the short word in front.
export const invoiceText = (n) => {
    const v = n == null ? '' : String(n).trim();
    return v ? (/^INV/i.test(v) ? v : 'INV ' + v) : '';
};
export const contractText = (n) => {
    const v = n == null ? '' : String(n).trim();
    return v ? (/^(CON|CTR)/i.test(v) ? v : 'CON ' + v) : '';
};
