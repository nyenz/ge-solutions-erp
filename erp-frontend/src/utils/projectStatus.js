// PATH: erp-frontend/src/utils/projectStatus.js
// fix184: THE words for a project, in ONE place. Two different things, never mixed again:
//
//   STAGE  = one step of the project's checklist (Field Measurement, Invoice / Contract Number ... Titled).
//            A project has many stages. Staff tick them one by one.
//   STATUS = the overall state of the whole project. A project has exactly ONE status at a time:
//            PENDING, ACTIVE, RECEIVABLES, HANDED OVER (or DELETED).
//
// On top of the status a project can carry a MONEY word (WAITING FOR PRICES, CRITICAL, FULLY PAID) and flags
// (PROBLEM). Every page reads the words and their hover explainers from here; no page invents its own.
// The same names are still called "status" in the server's data (project.statuses = the stages); that is only
// the old technical name and is renamed in a later, separate fix.

export const PROJECT_STATUS = {
    PENDING: {
        key: 'PENDING', label: 'PENDING', tone: 'slate',
        tip: 'Entered from the field. The office has not accepted and priced it yet. It is in no money total and no Recovery list.',
    },
    ACTIVE: {
        key: 'ACTIVE', label: 'ACTIVE', tone: 'plain',
        tip: 'Accepted by the office and being worked on.',
    },
    RECEIVABLES: {
        key: 'RECEIVABLES', label: 'RECEIVABLES', tone: 'red',
        tip: 'The client stopped paying. The project is in receivables: a storage fee is added every 30 days.',
    },
    HANDED_OVER: {
        key: 'HANDED_OVER', label: 'HANDED OVER', tone: 'cyan',
        tip: 'The title was handed over to the client. The record is locked.',
    },
    DELETED: {
        key: 'DELETED', label: 'DELETED', tone: 'red',
        tip: 'Deleted. Hidden from every list. A Director or the Admin can restore it from Settings > Archive.',
    },
};

/** Status keys in the order they are shown in lists and legends. */
export const STATUS_ORDER = ['PENDING', 'ACTIVE', 'RECEIVABLES', 'HANDED_OVER', 'DELETED'];

export const MONEY_WORD = {
    NO_PRICE: {
        key: 'NO_PRICE', label: 'WAITING FOR PRICES', tone: 'slate',
        tip: 'No price has been set yet, so nothing is owed and nothing is paid. A Secretary or above sets the prices.',
    },
    FULLY_PAID: {
        key: 'FULLY_PAID', label: 'FULLY PAID', tone: 'green',
        tip: 'The price is set and nothing is owed.',
    },
    CRITICAL: {
        key: 'CRITICAL', label: 'CRITICAL', tone: 'red',
        tip: 'Less than 25% of the title money has been paid (the same rule on every page).',
    },
};

const num = (v) => { const n = Number(v); return Number.isFinite(n) ? n : 0; };
const isDone = (s) => !!(s && (s.isCompleted ?? s.completed));
const byOrder = (a, b) => num(a.displayOrder) - num(b.displayOrder);

/** The ONE status of a project. Never returns nothing. */
export function statusOf(p) {
    if (!p) return PROJECT_STATUS.ACTIVE;
    if (p.deleted) return PROJECT_STATUS.DELETED;
    if (p.pending) return PROJECT_STATUS.PENDING;
    if (p.landTitle && (p.landTitle.isReleased ?? p.landTitle.released)) return PROJECT_STATUS.HANDED_OVER;
    if (p.isReceivable ?? p.receivable) return PROJECT_STATUS.RECEIVABLES;
    return PROJECT_STATUS.ACTIVE;
}

/** true when the project has a real price. A project with no price is never "paid" and never "critical". */
export const hasPrice = (p) => num(p && p.totalCost) > 0;

/** What the project still owes. The server's own figure (owedNow) when it sent one; never below 0. */
export function owedOf(p) {
    if (!p) return 0;
    if (p.owedNow !== null && p.owedNow !== undefined) return Math.max(0, num(p.owedNow));
    const cost = num(p.totalCost), paid = num(p.amountPaid), fees = num(p.storageFeesAccumulated);
    return Math.max(0, (p.isReceivable ? cost + fees : cost) - paid);
}

/**
 * The money words of a project, most important first. An empty list means "priced, something paid, something owed"
 * (nothing special to say). A project with NO PRICE only ever gets WAITING FOR PRICES.
 */
export function moneyWordsOf(p) {
    if (!p) return [];
    // fix199: a Pending project may already carry a saved price, but it is in no money figure, so no money word either
    if (p.pending && hasPrice(p)) return [];
    if (!hasPrice(p)) return [MONEY_WORD.NO_PRICE];
    const out = [];
    const critical = typeof p.critical === 'boolean'
        ? p.critical
        : (Math.max(0, num(p.amountPaid) - num(p.storageFeesPaid)) * 4 < num(p.totalCost));
    const handedOver = statusOf(p).key === 'HANDED_OVER';
    if (owedOf(p) === 0) out.push(MONEY_WORD.FULLY_PAID);
    else if (critical && !handedOver) out.push(MONEY_WORD.CRITICAL);
    return out;
}

/** The stages of a project in order, each with done: true / false. */
export function stagesOf(p, stages) {
    const list = stages || (p && p.statuses) || [];
    return list.map(s => ({ ...s, done: isDone(s) })).sort(byOrder);
}

/**
 * "WAITING FOR ..." -- the ONE thing a project is waiting for now, or null when there is nothing to say.
 * THE RULE (first match wins):
 *   1. deleted, or handed over                      -> nothing
 *   2. Pending                                      -> the office (to set the prices and start it)
 *   3. no price yet                                 -> prices
 *   4. flagged PROBLEM                              -> the problem to be cleared
 *   5. a stage is not ticked yet                    -> that stage (the first one not ticked, in list order)
 *   6. every stage is ticked (the last is "Titled") -> nothing
 * Money that is owed is NOT part of this line: the debt already has its own figures and its own words.
 */
export function waitingFor(p, stages) {
    if (!p) return null;
    const st = statusOf(p).key;
    if (st === 'DELETED' || st === 'HANDED_OVER') return null;
    if (st === 'PENDING') {
        // fix196: a project leaves Pending once it has the invoice number, the contract number and the price.
        // fix199 (test note 9): the office may save them one at a time, so the line names only what is still missing.
        const missing = [];
        if (!String(p.invoiceNumber || '').trim()) missing.push('INVOICE NUMBER');
        if (!String(p.contractNumber || '').trim()) missing.push('CONTRACT NUMBER');
        if (!(p.priceSet || Number(p.totalCost) > 0)) missing.push('PRICES');
        const list = missing.length <= 1 ? missing.join('') : missing.slice(0, -1).join(', ') + ' AND ' + missing[missing.length - 1];
        return { key: 'OFFICE', text: 'WAITING FOR THE OFFICE: ' + (list || 'START PROJECT'),
            tip: 'This project is Pending. A Secretary or above enters the invoice number, the contract number and the price (one at a time is fine). It starts when all three are in.' };
    }
    if (!hasPrice(p)) {
        return { key: 'PRICES', text: 'WAITING FOR PRICES',
            tip: 'No price has been set on this project yet. A Secretary or above sets the prices.' };
    }
    if (p.problem) {
        return { key: 'PROBLEM', text: 'WAITING FOR THE PROBLEM TO BE CLEARED',
            tip: 'This plot is flagged as a PROBLEM. Work and the hand-over wait until the flag is cleared (with a reason).' };
    }
    const next = stagesOf(p, stages).find(s => !s.done);
    if (next) {
        return { key: 'STAGE', text: 'WAITING FOR: ' + String(next.statusName || '').toUpperCase(), stage: next,
            tip: 'The next stage that is not ticked yet is "' + (next.statusName || '') + '". Tick it on the stage checklist when it is done.' };
    }
    return null;
}

// ---- fix185: stage list rules shared by New Project and the Folder page -------------------------------------------
const nameOf = (s) => String((s && (s.statusName ?? s.name)) || '');

/** true for the stage that holds the invoice and contract numbers ("Invoice / Contract Number"). */
export const isInvoiceContractStage = (s) => { const n = nameOf(s).toLowerCase(); return n.includes('invoice') && n.includes('contract'); };

/**
 * NO STAGE MAY BE ADDED ABOVE THE INVOICE / CONTRACT STAGE (David, October 2026): a project is accepted by the office at
 * that stage, so nothing may be slipped in before it. "Insert below row i" is allowed only from the Invoice / Contract
 * row downwards. A list without that stage keeps the old rule (anywhere below the first row).
 */
export function canInsertStageBelow(list, i) {
    const k = (list || []).findIndex(isInvoiceContractStage);
    if (k < 0) return i >= 0;
    return i >= k;
}

/** Every stage except the first can carry its own documents (the first is ticked at intake, before any paper exists). */
export const stageTakesDocuments = (list, i) => i > 0;

/** fix197: true for the stage that means "the title exists" (same test as the server's LandService.isTitledStatus). */
export const isTitledStage = (s) => { const n = nameOf(s).trim().toLowerCase(); return n === 'titled' || n.includes('registration'); };

/** fix196: true when the project has BOTH its invoice number and its contract number. */
export const hasNumbers = (p) => !!(p && String(p.invoiceNumber || '').trim() && String(p.contractNumber || '').trim());
