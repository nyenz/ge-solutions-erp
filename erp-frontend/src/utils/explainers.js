// fix216 (David): "some of these are not having the explainer on hover ... and anything like that throughout the app".
// The ONE fallback list of explainers. When a tab, filter pill, table heading or small button has no title="..." of its
// own, the global explainer (components/common/globalTips.js) looks its visible words up here. Counts and arrows are
// ignored ("PENDING 3" -> PENDING). A title written in the code always wins over this list.
// Keep each line short and plain. Add a line here when a new tab, pill or column appears.
export const EXPLAIN = {
    // ── Ledger tabs
    'ALL PROJECTS': 'Every project, Pending entries included.',
    'NO TITLE DETAILS': 'Projects whose title details (plot, block, area, title date) are not saved yet.',
    'HAS TITLE DETAILS': 'Projects whose title details are saved. Not the same as the stage called Titled.',
    'LEGACY': 'Legacy Titles: old titles kept in storage. They can carry monthly storage fees.',
    'RECEIVABLES': 'Projects in receivables: money owed for a long time. Storage fees grow every 30 days.',
    'IN RECEIVABLES': 'Clients with at least one project in receivables.',
    'CRITICAL': 'Less than 25% of the title money is paid.',
    'PAID': 'Projects with a price and nothing owed.',
    'PAID UP': 'Clients who owe nothing on any project.',
    'PROBLEM': 'Projects flagged as a problem. The reason is in the project\'s Notes.',
    'PENDING': 'Entries still waiting for the office: invoice number, contract number or price.',
    'PENDING ONLY': 'Clients whose only projects are Pending entries.',
    'ALL CLIENTS': 'Every client.',
    'OWING': 'Clients who still owe money.',
    'NO PROJECTS': 'People saved in the app with no live project.',
    'JOINT PROJECTS': 'Projects with more than one client.',
    'SOLO PROJECTS': 'Projects with one client.',
    // ── Recovery tabs
    'ALL DUE': 'Clients to call now: they owe money and are not resting.',
    'CONTACTED': 'Clients who answered a call recently.',
    'MISSED': 'Calls that did not get through (not picking up, not going through, wrong number).',
    'SITE VISIT': '4 missed days in 30 days and no good call: someone should visit.',
    'LOCKED': 'Resting: paid in the last 30 days, or 2 good calls in 30 days. No calls until the date shown.',
    // ── Payments tabs and the Notes timeline pills
    'ALL': 'Show everything.',
    'TITLE': 'Money paid for the title work.',
    'STORAGE FEES': 'Money paid toward storage fees.',
    'STORAGE FEE': 'Money paid toward storage fees.',
    'OPENING DEPOSITS': 'Money already received when the project was entered.',
    'REVERSALS': 'Payments that were cancelled (minus lines). The original line stays.',
    'NOTES': 'Notes typed by staff.',
    'MONEY': 'Payments and reversals, with how they were paid.',
    'DECISIONS': 'Changes that needed a reason: fees added to the cost, pauses, deletions.',
    'EVENTS': 'What the app recorded by itself: stages ticked, project started, problem flags.',
    'CALLS': 'Recovery calls to the clients.',
    // ── Settings tabs
    'APPEARANCE': 'How the app looks for you: theme, size, explainers, animation.',
    'SECURITY': 'Change your own key (password).',
    'STAFF': 'Staff accounts: add people, change ranks, suspend, new temporary keys.',
    'ARCHIVE': 'Deleted projects. A Director can restore them.',
    'DANGER ZONE': 'Wipe the app data. Admin only.',
    // ── table headings
    '#': 'Row number.',
    'INDEX': 'The project index: the project\'s own number, for life.',
    'CLIENT(S)': 'The clients: the people who pay. Recovery calls them.',
    'CLIENT': 'The client: a person who pays.',
    'CLIENT WHO PAID': 'The client who paid this money.',
    'PHONE': 'The client\'s phone number(s).',
    'CONTACT': 'Phone number(s) of the client.',
    'DISTRICT': 'The district of the land.',
    'SUB-COUNTY': 'The sub-county of the land.',
    'PARISH': 'The parish of the land.',
    'VILLAGE': 'The village of the land.',
    'STATUS': 'Where the whole project stands: PENDING, ACTIVE, RECEIVABLES or HANDED OVER, plus a money word.',
    'STAGE': 'One step of the project\'s checklist. The dots are all its stages.',
    'PROGRESS': 'How much of the price is paid.',
    'PROJECT': 'The project index.',
    'PROJECTS': 'How many live projects this client has.',
    'PLOT': 'The plot number on the title.',
    'DATE': 'The day.',
    'DATE PAID': 'The day the money was paid. "Entered" is when it was typed in.',
    'FOR': 'What the money was for: the title work or storage fees.',
    'METHOD': 'How the money was paid: Office, Mobile Money, Bank or Other.',
    'AMOUNT': 'The amount in Uganda shillings. A reversal is a minus amount.',
    'AMOUNT (UGX)': 'The amount in Uganda shillings.',
    'RECEIPT': 'The receipt scan filed with the payment.',
    'RECORDED BY': 'The staff member who typed it in.',
    'PAID BY': 'The client who paid.',
    'TYPE': 'The kind of line.',
    'KIND': 'The kind of line.',
    'OWED': 'Money still owed.',
    'PAID %': 'Share of the price that is paid.',
    'HEALTH': 'Days since the last payment.',
    'LAST CONTACT': 'The last recovery call.',
    'OWNERSHIP': 'Whether this client pays alone or with others.',
    'CATEGORY': 'What the expense was for.',
    'LOGGED BY': 'The staff member who logged it.',
    'TIME': 'The time.',
    'NOTE': 'A note.',
    // ── common buttons with no words of their own
    'REFRESH': 'Load the page again from the server.',
    'PRINT': 'Print a clean document of this page.',
    'PREV': 'The page before.',
    'NEXT': 'The next page.',
};

/** "PENDING 3" -> "PENDING", "DATE PAID ↕" -> "DATE PAID" */
export const normalizeLabel = (text) => String(text || '')
    .toUpperCase()
    .replace(/[←-⇿↕]/g, ' ')
    .replace(/(^|\s)\d[\d,]*(?=\s|$)/g, ' ')
    .replace(/[^A-Z0-9#%()&\-' ]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

/** The explainer for an element's visible words, or '' */
export const explainFor = (text) => EXPLAIN[normalizeLabel(text)] || '';
