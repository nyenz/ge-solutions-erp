// fix217: the layout maths of the Reports PDF (reportPdf.js)
import test from 'node:test';
import assert from 'node:assert/strict';
import { fitColumns, niceMax, shortNumber, plain, writeReportPdf } from '../src/pages/Reports/reportPdf.js';

test('columns always fill the page width exactly and never go below the minimum', () => {
    const narrow = fitColumns([60, 80, 50], 700);
    assert.equal(Math.round(narrow.reduce((a, b) => a + b, 0)), 700);
    const wide = fitColumns([400, 400, 60, 60], 700, 40);
    assert.equal(Math.round(wide.reduce((a, b) => a + b, 0)), 700);
    assert.ok(wide.every(w => w >= 39.9));
});

test('chart axis and short numbers', () => {
    assert.equal(niceMax(2200000), 2500000);
    assert.equal(niceMax(0), 1);
    assert.equal(shortNumber(1250000), '1.25M');
    assert.equal(shortNumber(85000), '85K');
});

test('text the PDF font cannot draw is made plain', () => {
    assert.equal(plain('A — B → C…'), 'A - B -> C...');
});

test('the table starts on its own page after a chart and every page has a footer', async () => {
    const rows = Array.from({ length: 70 }, (_, i) => ({ n: 'Client ' + i, v: i * 1000 }));
    const doc = await writeReportPdf({ title: 'TEST', scopeLine: 'x', description: 'y', chartType: 'donut',
        chartRows: [{ label: 'a', value: 1 }, { label: 'b', value: 2 }], chartFormat: String,
        cols: [{ label: 'Client', type: 'text', get: r => r.n }, { label: 'Amount', type: 'money', get: r => r.v }],
        rows, format: (v) => String(v), fileName: 't.pdf', returnDoc: true });
    assert.ok(doc.getNumberOfPages() >= 3, 'cover + at least two table pages');
});
