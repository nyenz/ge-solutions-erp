// fix181 (13.8): run with `npm test` (node --test)
import test from 'node:test';
import assert from 'node:assert/strict';
import { csvCell, toCSV, plainStamp } from '../src/utils/csv.js';

test('a text cell that looks like a formula is made plain text', () => {
    assert.equal(csvCell('=HYPERLINK("http://x","y")'), '"\'=HYPERLINK(""http://x"",""y"")"');
    assert.equal(csvCell('+256 700'), "'+256 700");
    assert.equal(csvCell('-5 days'), "'-5 days");
    assert.equal(csvCell('@sum'), "'@sum");
    assert.equal(csvCell('\tx'), "'\tx");
});

test('real numbers, plain text and timestamps are left alone', () => {
    assert.equal(csvCell(-500000), '-500000');
    assert.equal(csvCell('2026-10-04 22:39:00'), '2026-10-04 22:39:00');
    assert.equal(csvCell('Kampala'), 'Kampala');
    assert.equal(csvCell(null), '');
});

test('commas, quotes and new lines are quoted', () => {
    assert.equal(csvCell('a,b'), '"a,b"');
    assert.equal(csvCell('say "hi"'), '"say ""hi"""');
    assert.equal(toCSV(['A', 'B'], [[1, 'x\ny']]), 'A,B\n1,"x\ny"');
});

test('the export time is the server time without a zone change', () => {
    assert.equal(plainStamp('2026-10-04T22:39:00'), '2026-10-04 22:39:00');
    assert.equal(plainStamp('2026-10-04T22:39'), '2026-10-04 22:39:00');
    assert.equal(plainStamp('2026-10-04T22:39:05.123456'), '2026-10-04 22:39:05');
});
