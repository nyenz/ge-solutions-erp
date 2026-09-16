// PATH: erp-frontend/src/components/common/glossary.js

/**
 * THE GLOSSARY -- one place for every bit of in-app shorthand, so the same
 * word never gets two different explanations on two different pages.
 * Business rules here come straight from the project's rule sheet.
 */
export const GLOSSARY = {
    LOCKED: 'The 24-hour edit window has closed. Ask a Director if this entry still needs changing.',
    EDITED: 'This entry was changed after it was first logged. The audit trail has the full history.',
    SPENT_BY: 'The person who actually spent the cash, when that is not the person who logged it.',
    CATEGORY: 'What the money went on. Preset categories come from the tiles above; anything else was typed in under OTHER.',
    BACKLOG: 'Work that has been started but is not finished yet.',
    RECEIVABLES: 'All money owed to the company, whether the work was legacy or regular.',
    LEGACY: 'Triggered automatically after 365 days with no payment, or set manually by an admin.',
    STORAGE_FEE: 'UGX 50,000 every 30 days. The 30-day clock only starts once the work becomes Legacy.',
    TWO_FOURTEEN: 'The 2-14 rule: at most 2 calls per client per month, and at least 14 days between calls.',
    NIN: 'National ID Number. This is what makes an owner unique in the system -- not their phone number.',
};

