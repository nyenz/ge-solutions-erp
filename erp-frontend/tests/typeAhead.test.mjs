// PATH: erp-frontend/tests/typeAhead.test.mjs (fix210)
import test from 'node:test';
import assert from 'node:assert/strict';
import { findTypeAhead, isTypeAheadKey } from '../src/utils/typeAhead.js';

const L = ['Application Forms', 'Offer Letters', 'Forwarding Letters', 'Deed Plan', 'Copy of Title', 'Field Measurement', 'Deed of Transfer'];

test('one letter jumps to the first match, again moves to the next', () => {
    assert.equal(findTypeAhead(L, 'd', -1), 3);
    assert.equal(findTypeAhead(L, 'd', 3), 6);
    assert.equal(findTypeAhead(L, 'd', 6), 3);          // wraps round
    assert.equal(findTypeAhead(L, 'f', -1), 2);
});

test('repeated letter cycles, several letters match the start of the words', () => {
    assert.equal(findTypeAhead(L, 'dd', 3), 6);
    assert.equal(findTypeAhead(L, 'deed o', 3), 6);
    assert.equal(findTypeAhead(L, 'deed p', 3), 3);     // the current item still matches: it stays
    assert.equal(findTypeAhead(L, 'co', -1), 4);
});

test('no match, empty list and case', () => {
    assert.equal(findTypeAhead(L, 'z', -1), -1);
    assert.equal(findTypeAhead([], 'a', -1), -1);
    assert.equal(findTypeAhead(['FREEHOLD', 'LEASEHOLD', 'MAILO'], 'l', -1), 1);
});

test('which keys count', () => {
    assert.equal(isTypeAheadKey({ key: 'a' }), true);
    assert.equal(isTypeAheadKey({ key: ' ' }), false);
    assert.equal(isTypeAheadKey({ key: ' ' }, true), true);
    assert.equal(isTypeAheadKey({ key: 'ArrowDown' }), false);
    assert.equal(isTypeAheadKey({ key: 'c', ctrlKey: true }), false);
});
