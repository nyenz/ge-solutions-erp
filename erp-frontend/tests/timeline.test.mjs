// fix215: the Notes timeline rules on the page
import test from 'node:test';
import assert from 'node:assert/strict';
import { visibleRows, countKinds, followUpState, summaryOf, fmtWhen, KINDS } from '../src/utils/timeline.js';

const rows = [
    { id: 1, kind: 'NOTE', title: 'Promise to pay', text: 'Will pay on Friday', pinned: true, projectId: 'a' },
    { id: 2, kind: 'MONEY', title: 'Payment received', detail: 'UGX 300,000 · Mobile Money', projectId: 'a' },
    { id: 3, kind: 'REASON', title: 'Storage fees added to the cost', text: 'Client agreed', projectId: 'b' },
    { id: 4, kind: 'CALL', title: 'Not picking up', text: 'Rang twice', clientName: 'Musoke Fred' },
];

test('filters by kind and search; pinned notes come out on their own', () => {
    const all = visibleRows(rows);
    assert.equal(all.pinned.length, 1);
    assert.equal(all.rest.length, 3);
    assert.deepEqual(visibleRows(rows, 'MONEY').rest.map(r => r.id), [2]);
    assert.deepEqual(visibleRows(rows, 'ALL', 'musoke').rest.map(r => r.id), [4]);
    assert.deepEqual(visibleRows(rows, 'ALL', '', 'b').rest.map(r => r.id), [3]);
});

test('counts per pill', () => {
    const c = countKinds(rows);
    assert.equal(c.ALL, 4); assert.equal(c.MONEY, 1); assert.equal(c.EVENT, undefined);
});

test('follow-up day: due today or late, else soon', () => {
    assert.equal(followUpState('2026-10-19', '2026-10-19'), 'due');
    assert.equal(followUpState('2026-10-18', '2026-10-19'), 'due');
    assert.equal(followUpState('2026-10-25', '2026-10-19'), 'soon');
    assert.equal(followUpState(null), '');
});

test('short summary and plain dates', () => {
    assert.equal(summaryOf({ text: 'x'.repeat(200) }).length, 110);
    assert.equal(fmtWhen('2026-10-19T14:05:00', true), '19 Oct 2026, 14:05');
    assert.equal(fmtWhen('2026-10-19'), '19 Oct 2026');
    assert.ok(KINDS.find(k => k.key === 'MONEY').money);
});
