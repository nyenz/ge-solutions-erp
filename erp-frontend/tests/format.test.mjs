// fix284 (B3): one date style and one money style.
import test from 'node:test';
import assert from 'node:assert/strict';
import { fmtDay, fmtTime, fmtDayTime, fmtMoney, fmtUgx } from '../src/utils/format.js';

test('day reads the server text without shifting it', () => {
    assert.equal(fmtDay('2026-10-05'), '5 Oct 2026');
    assert.equal(fmtDay('2026-10-30T23:59:00'), '30 Oct 2026');
    assert.equal(fmtDay('2026-01-01 08:00:00'), '1 Jan 2026');
});
test('time is 24-hour and empty when there is none', () => {
    assert.equal(fmtTime('2026-10-05T14:05:09'), '14:05');
    assert.equal(fmtTime('2026-10-05'), '');
});
test('day and time together', () => {
    assert.equal(fmtDayTime('2026-10-05T07:08:00'), '5 Oct 2026, 07:08');
    assert.equal(fmtDayTime('2026-10-05'), '5 Oct 2026');
});
test('empty and unreadable dates give nothing, never "Invalid Date"', () => {
    for (const v of [null, undefined, '', 'garbage', new Date('x')]) assert.equal(fmtDay(v), '');
    assert.equal(fmtDayTime(null), '');
});
test('a Date object uses its own day and time', () => {
    assert.equal(fmtDayTime(new Date(2026, 9, 5, 14, 5)), '5 Oct 2026, 14:05');
});
test('money has commas whatever the device language', () => {
    assert.equal(fmtMoney(1234567), '1,234,567');
    assert.equal(fmtMoney('2500000'), '2,500,000');
    assert.equal(fmtMoney(null), '0');
    assert.equal(fmtMoney('abc'), '0');
    assert.equal(fmtUgx(50000), 'UGX 50,000');
});
test('a text with its own zone is shown in the device time, not cut', () => {
    const out = fmtDayTime('2026-10-30T11:30:00Z');
    assert.match(out, /^\d{1,2} [A-Z][a-z]{2} 2026, \d{2}:\d{2}$/);
});
