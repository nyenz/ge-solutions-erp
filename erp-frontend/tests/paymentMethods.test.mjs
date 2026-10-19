// fix214: the payment method words and checks (same rules as PaymentMethods.java)
import test from 'node:test';
import assert from 'node:assert/strict';
import { PAY_METHODS, methodLabel, methodCode, checkMethod, methodLine } from '../src/utils/paymentMethods.js';

test('four methods in David\'s order', () => {
    assert.deepEqual(PAY_METHODS.map(m => m.value), ['OFFICE', 'MOBILE_MONEY', 'BANK', 'OTHER']);
});

test('labels and codes go both ways; old payments say Not recorded', () => {
    assert.equal(methodLabel('MOBILE_MONEY'), 'Mobile Money');
    assert.equal(methodLabel(null), 'Not recorded');
    assert.equal(methodCode('Bank'), 'BANK');
    assert.equal(methodCode(''), '');
});

test('a method is required and Other needs a few words', () => {
    assert.match(checkMethod('', ''), /Pick how/);
    assert.match(checkMethod('OTHER', ' '), /For Other/);
    assert.equal(checkMethod('OTHER', 'Cheque 1042'), '');
    assert.equal(checkMethod('OFFICE', ''), '');
    assert.match(checkMethod('BANK', 'x'.repeat(81)), /80/);
});

test('one short line for lists', () => {
    assert.equal(methodLine('MOBILE_MONEY', 'MP2410'), 'Mobile Money - MP2410');
    assert.equal(methodLine('OFFICE', ''), 'Office');
});
