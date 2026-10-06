// fix190: report periods use the device's own calendar. Run with `npm test`.
// The time zone is set to Kampala BEFORE any date is made, so the old one-day-early fault would show here.
process.env.TZ = 'Africa/Kampala';
import test from 'node:test';
import assert from 'node:assert/strict';
const { periodRange, localISO } = await import('../src/utils/reportPeriod.js');

const now = new Date(2026, 9, 6, 1, 30);   // Tuesday 6 Oct 2026, 01:30 at night in Kampala (still 5 Oct in London)

test('today is today on the device, even just after midnight', () => {
    assert.equal(localISO(now), '2026-10-06');
    assert.deepEqual(periodRange('TODAY', '', '', now), ['2026-10-06', '2026-10-06']);
});

test('months, quarters and years start on the 1st and end on the last day', () => {
    assert.deepEqual(periodRange('THIS MONTH', '', '', now), ['2026-10-01', '2026-10-06']);
    assert.deepEqual(periodRange('LAST MONTH', '', '', now), ['2026-09-01', '2026-09-30']);
    assert.deepEqual(periodRange('THIS QUARTER', '', '', now), ['2026-10-01', '2026-10-06']);
    assert.deepEqual(periodRange('THIS YEAR', '', '', now), ['2026-01-01', '2026-10-06']);
    assert.deepEqual(periodRange('LAST YEAR', '', '', now), ['2025-01-01', '2025-12-31']);
    assert.deepEqual(periodRange('LAST MONTH', '', '', new Date(2026, 0, 15)), ['2025-12-01', '2025-12-31']);
});

test('weeks run Monday to Sunday', () => {
    assert.deepEqual(periodRange('THIS WEEK', '', '', now), ['2026-10-05', '2026-10-06']);
    assert.deepEqual(periodRange('LAST WEEK', '', '', now), ['2026-09-28', '2026-10-04']);
    assert.deepEqual(periodRange('THIS WEEK', '', '', new Date(2026, 9, 4, 12)), ['2026-09-28', '2026-10-04']);   // a Sunday
});

test('custom dates are used as typed; no dates means no period', () => {
    assert.deepEqual(periodRange('CUSTOM', '2026-03-01', '2026-03-31', now), ['2026-03-01', '2026-03-31']);
    assert.deepEqual(periodRange('CUSTOM', '2026-03-31', '2026-03-01', now), ['2026-03-01', '2026-03-31']);
    assert.equal(periodRange('CUSTOM', '2026-03-01', '', now), null);
    assert.equal(periodRange('ALL TIME', '', '', now), null);
});
