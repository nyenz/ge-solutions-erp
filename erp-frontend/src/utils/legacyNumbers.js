// PATH: erp-frontend/src/utils/legacyNumbers.js
// fix285 (David, 3 Nov 2026): older (legacy) projects often have no NIN, no contract number, and an invoice number that
// was only unique inside one sub-county. The MISSING ticks on the forms fill these in the same way every time:
//   NIN missing       -> the person's full name in capitals, NO spaces  (NAMUGANZASARAH)
//   invoice missing   -> DISTRICT-SUBCOUNTY-NUMBER in initials          (KAM-NAM-0007)
//   contract missing  -> the same text as the invoice number            (KAM-NAM-0007)
// Initials: a one-word name gives its first 3 letters (KAMULI -> KAM); a name of several words gives the first letter
// of each word (CENTRAL DIVISION -> CD). The number is the old paper number (4 digits), or the next free one.

const words = (name) => String(name || '').toUpperCase().replace(/[^A-Z0-9 ]+/g, ' ').trim().split(/\s+/).filter(Boolean);

/** KAMULI -> KAM, CENTRAL DIVISION -> CD, '' -> '' */
export function placeInitials(name) {
    const w = words(name);
    if (w.length === 0) return '';
    if (w.length === 1) return w[0].slice(0, 3);
    return w.map(x => x[0]).join('').slice(0, 4);
}

/** KAM-NAM ('' when the district or the sub-county is still empty) */
export function invoicePrefix(district, subCounty) {
    const d = placeInitials(district), s = placeInitials(subCounty);
    return d && s ? d + '-' + s : '';
}

/** The paper number as 4 digits ('7' -> '0007'); '' when nothing usable was typed. Letters are kept (12A -> 012A). */
export function paperPart(paper) {
    const t = String(paper || '').toUpperCase().replace(/[^A-Z0-9]+/g, '');
    if (!t) return '';
    return t.length >= 4 ? t : t.padStart(4, '0');
}

/** KAM-NAM-0007 from the place and the old paper number; '' when the place or the number is missing. */
export function madeInvoiceNumber(district, subCounty, paper) {
    const pre = invoicePrefix(district, subCounty), num = paperPart(paper);
    return pre && num ? pre + '-' + num : '';
}

/** The NIN used for a person who has none: the full name in capitals with NO spaces (fix286, David). */
export function ninFromName(fullName) {
    return String(fullName || '').toUpperCase().replace(/\s+/g, '');
}
