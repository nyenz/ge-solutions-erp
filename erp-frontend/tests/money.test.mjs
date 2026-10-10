// fix199 (test note 23): money boxes refuse a dot instead of silently dropping it
import test from 'node:test';
import assert from 'node:assert/strict';
import { readShillings, isShillings } from '../src/utils/money.js';

test('whole shillings are read, anything else is refused', () => {
    assert.deepEqual(readShillings('1500'), { ok: true, value: '1500' });
    assert.deepEqual(readShillings('1,500,000'), { ok: true, value: '1500000' });
    assert.deepEqual(readShillings(' 2 500 '), { ok: true, value: '2500' });
    assert.deepEqual(readShillings(''), { ok: true, value: '' });
    assert.equal(isShillings('1500.50'), false);
    assert.equal(isShillings('15k'), false);
    assert.equal(isShillings('-200'), false);
});
