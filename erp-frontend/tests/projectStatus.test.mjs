// fix184: the project words (status, money word, "waiting for"). Run with `npm test`.
import test from 'node:test';
import assert from 'node:assert/strict';
import { statusOf, moneyWordsOf, waitingFor, owedOf, PROJECT_STATUS, MONEY_WORD, STATUS_ORDER, canInsertStageBelow, isInvoiceContractStage, stageTakesDocuments } from '../src/utils/projectStatus.js';

const stage = (name, done, order) => ({ statusName: name, isCompleted: done, displayOrder: order });

test('every status and money word has a label and a hover explainer', () => {
    for (const k of STATUS_ORDER) {
        assert.ok(PROJECT_STATUS[k].label.length > 0);
        assert.ok(PROJECT_STATUS[k].tip.length > 20, k + ' needs an explainer');
    }
    for (const w of Object.values(MONEY_WORD)) assert.ok(w.label && w.tip.length > 20);
});

test('a project has exactly one status, in a fixed priority', () => {
    assert.equal(statusOf({}).key, 'ACTIVE');
    assert.equal(statusOf({ pending: true, isReceivable: true }).key, 'PENDING');
    assert.equal(statusOf({ isReceivable: true }).key, 'RECEIVABLES');
    assert.equal(statusOf({ isReceivable: true, landTitle: { isReleased: true } }).key, 'HANDED_OVER');
    assert.equal(statusOf({ deleted: true, pending: true }).key, 'DELETED');
    assert.equal(statusOf(null).key, 'ACTIVE');
});

test('a Pending project with no price is NEVER "fully paid" (the Ledger bug)', () => {
    const pending = { pending: true, totalCost: 0, amountPaid: 0, owedNow: 0 };
    assert.deepEqual(moneyWordsOf(pending).map(w => w.key), ['NO_PRICE']);
    assert.equal(moneyWordsOf(pending)[0].label, 'WAITING FOR PRICES');
    // the same for a started project whose price is still empty
    assert.deepEqual(moneyWordsOf({ totalCost: null, amountPaid: 0 }).map(w => w.key), ['NO_PRICE']);
});

test('money words of a priced project', () => {
    assert.deepEqual(moneyWordsOf({ totalCost: 1000, amountPaid: 1000, owedNow: 0 }).map(w => w.key), ['FULLY_PAID']);
    assert.deepEqual(moneyWordsOf({ totalCost: 1000, amountPaid: 100, owedNow: 900, critical: true }).map(w => w.key), ['CRITICAL']);
    assert.deepEqual(moneyWordsOf({ totalCost: 1000, amountPaid: 600, owedNow: 400, critical: false }), []);
    // without the server flag the 25% rule is worked out here, on title money only
    assert.deepEqual(moneyWordsOf({ totalCost: 1000, amountPaid: 300, storageFeesPaid: 100 }).map(w => w.key), ['CRITICAL']);
    // a handed-over project is never shown as critical
    assert.deepEqual(moneyWordsOf({ totalCost: 1000, amountPaid: 100, owedNow: 900, critical: true, landTitle: { isReleased: true } }), []);
});

test('owed is the server figure when sent, and never below zero', () => {
    assert.equal(owedOf({ owedNow: 250, totalCost: 1, amountPaid: 0 }), 250);
    assert.equal(owedOf({ totalCost: 1000, amountPaid: 1500 }), 0);
    assert.equal(owedOf({ isReceivable: true, totalCost: 1000, storageFeesAccumulated: 200, amountPaid: 300 }), 900);
});

test('"waiting for" follows the rule, first match wins', () => {
    const stages = [stage('Titled', false, 2), stage('Field Measurement', true, 0), stage('Invoice / Contract Number', false, 1)];
    assert.equal(waitingFor({ deleted: true, pending: true }, stages), null);
    assert.equal(waitingFor({ totalCost: 5, landTitle: { isReleased: true } }, stages), null);
    assert.equal(waitingFor({ pending: true }, stages).key, 'OFFICE');
    assert.match(waitingFor({ pending: true }, stages).text, /^WAITING FOR THE OFFICE/);
    assert.equal(waitingFor({ totalCost: 0 }, stages).text, 'WAITING FOR PRICES');
    assert.equal(waitingFor({ totalCost: 5, problem: true }, stages).key, 'PROBLEM');
    // the first stage NOT ticked, by list order (not by array order)
    assert.equal(waitingFor({ totalCost: 5 }, stages).text, 'WAITING FOR: INVOICE / CONTRACT NUMBER');
    // stages can also arrive on the project itself
    assert.equal(waitingFor({ totalCost: 5, statuses: stages }).key, 'STAGE');
});

test('a project with every stage ticked (Titled) shows no "waiting for" line', () => {
    const done = [stage('Field Measurement', true, 0), stage('Titled', true, 1)];
    assert.equal(waitingFor({ totalCost: 5, amountPaid: 1 }, done), null);
    assert.equal(waitingFor({ totalCost: 5 }, []), null);
});

test('no stage can be added above the Invoice / Contract stage', () => {
    const list = [{ name: 'Field Measurement' }, { statusName: 'Invoice / Contract Number' }, { name: 'Area Land Committee' }];
    assert.equal(isInvoiceContractStage(list[1]), true);
    assert.equal(isInvoiceContractStage(list[0]), false);
    assert.equal(canInsertStageBelow(list, 0), false);   // would land between Field Measurement and Invoice / Contract
    assert.equal(canInsertStageBelow(list, 1), true);
    assert.equal(canInsertStageBelow(list, 2), true);
    // a list without that stage keeps the old rule
    assert.equal(canInsertStageBelow([{ name: 'A' }, { name: 'B' }], 0), true);
});

test('every stage except the first takes documents', () => {
    assert.equal(stageTakesDocuments([], 0), false);
    assert.equal(stageTakesDocuments([], 1), true);
});

// fix196 + fix197: the two special stages and the project numbers
test('the Invoice / Contract stage, the Titled stage and "has both numbers" are recognised', async () => {
    const { isInvoiceContractStage, isTitledStage, hasNumbers } = await import('../src/utils/projectStatus.js');
    assert.equal(isInvoiceContractStage({ statusName: 'Invoice / Contract Number' }), true);
    assert.equal(isInvoiceContractStage({ statusName: 'Progressive Invoice' }), false);
    assert.equal(isTitledStage({ statusName: ' Titled ' }), true);
    assert.equal(isTitledStage({ name: 'Title Registration' }), true);
    assert.equal(isTitledStage({ statusName: 'Deed Plan' }), false);
    assert.equal(hasNumbers({ invoiceNumber: 'INV 1', contractNumber: 'C-9' }), true);
    assert.equal(hasNumbers({ invoiceNumber: 'INV 1', contractNumber: '  ' }), false);
    assert.equal(hasNumbers(null), false);
});
