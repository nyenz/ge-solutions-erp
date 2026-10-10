// fix199 (test note 22): a stage picks its own document type
import test from 'node:test';
import assert from 'node:assert/strict';
import { categoryForStage } from '../src/utils/stageCategory.js';

const cats = [
    { code: 'OFFER_LETTER', label: 'Offer Letters' }, { code: 'DEED_PLAN', label: 'Deed Plan' }, { code: 'INVOICE', label: 'Invoices' },
    { code: 'COPY_OF_TITLE', label: 'Copy of Title' }, { code: 'JOB_RECORD_JACKET', label: 'Job Record Jacket (JRJ)' },
    { code: 'AREA_LAND_COMMITTEE', label: 'Area Land Committee' }, { code: 'PROGRESS_REPORT', label: 'Progress Reports' },
];

test('each stage gets its own document type', () => {
    assert.equal(categoryForStage('Offer Letter', cats), 'OFFER_LETTER');
    assert.equal(categoryForStage('Deed Plan', cats), 'DEED_PLAN');
    assert.equal(categoryForStage('Invoice / Contract Number', cats), 'INVOICE');
    assert.equal(categoryForStage('Titled', cats), 'COPY_OF_TITLE');
    assert.equal(categoryForStage('Job Record Jacket (JRJ)', cats), 'JOB_RECORD_JACKET');
    assert.equal(categoryForStage('Area Land Committee', cats), 'AREA_LAND_COMMITTEE');
    assert.equal(categoryForStage('Progressive Reports', cats), 'PROGRESS_REPORT');
    assert.equal(categoryForStage('Something new', cats), '');
});
