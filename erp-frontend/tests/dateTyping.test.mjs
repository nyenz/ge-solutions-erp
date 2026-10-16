// PATH: erp-frontend/tests/dateTyping.test.mjs (fix210)
import test from 'node:test';
import assert from 'node:assert/strict';
import { readTypedDate } from '../src/utils/dateTyping.js';

const NOW = new Date(2026, 9, 16);

test('day first, any separator', () => {
    assert.deepEqual(readTypedDate('14/03/2019', NOW), { value: '2019-03-14' });
    assert.deepEqual(readTypedDate('4-3-2019', NOW), { value: '2019-03-04' });
    assert.deepEqual(readTypedDate('04.03.2019', NOW), { value: '2019-03-04' });
    assert.deepEqual(readTypedDate(' 4 3 2019 ', NOW), { value: '2019-03-04' });
});

test('two-digit years', () => {
    assert.deepEqual(readTypedDate('14/3/19', NOW), { value: '2019-03-14' });
    assert.deepEqual(readTypedDate('14/3/85', NOW), { value: '1985-03-14' });
    assert.deepEqual(readTypedDate('1/1/26', NOW), { value: '2026-01-01' });
});

test('wrong dates are explained', () => {
    assert.ok(readTypedDate('31/02/2024', NOW).error.includes('29'));
    assert.ok(readTypedDate('12/13/2020', NOW).error.includes('month'));
    assert.ok(readTypedDate('2019-03-14', NOW).error);
    assert.ok(readTypedDate('hello', NOW).error);
    assert.deepEqual(readTypedDate('', NOW), {});
});
