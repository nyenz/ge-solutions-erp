// fix216: the fallback explainers
import test from 'node:test';
import assert from 'node:assert/strict';
import { explainFor, normalizeLabel } from '../src/utils/explainers.js';

test('counts and arrows are ignored', () => {
    assert.equal(normalizeLabel('PENDING 3'), 'PENDING');
    assert.equal(normalizeLabel('date paid ↕'), 'DATE PAID');
    assert.equal(normalizeLabel('ALL CLIENTS 1,204'), 'ALL CLIENTS');
});

test('every Ledger tab and column has words', () => {
    for (const w of ['ALL PROJECTS', 'NO TITLE DETAILS', 'HAS TITLE DETAILS', 'LEGACY', 'RECEIVABLES', 'CRITICAL', 'PAID', 'PROBLEM', 'PENDING 1',
        'INDEX', 'CLIENT(S)', 'PHONE', 'PARISH', 'VILLAGE', 'STATUS', 'STAGE', 'PROGRESS']) {
        assert.ok(explainFor(w), 'no explainer for ' + w);
    }
    assert.equal(explainFor('SOMETHING NEW'), '');
});
