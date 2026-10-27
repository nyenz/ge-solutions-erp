// PATH: erp-frontend/src/pages/Reports/reportPdf.js
// fix217 (David: "a significant blunder on the PDF downloads of the Reports page"). The old export drew the table from
// the TOP of the first page, so its dark heading band and rows landed on top of the cover and the chart; the chart was
// a stretched picture of the screen (the bar chart was not even a picture, so it was missing) and every cell was cut at
// 26 letters. THIS file is the ONE PDF writer of the Reports page:
//   page 1  : a white page with a navy title band, the scope line, the description (wrapped), then the chart, drawn with
//             real lines and shapes (bars, columns, line or donut) from the same numbers as the screen;
//   page 2+ : the table in landscape -- columns sized to what they hold, long text wrapped (never cut in the middle of
//             a word), numbers and money on the right, the heading row repeated on every page, zebra rows;
//   footer  : "GE Solutions · <report> · Page x of y" on every page.
// The layout maths (column widths, chart scale) are plain functions so they can be tested (tests/reportPdf.test.mjs).

// fix227 (David): the GES website colours -- navy #0b2545, orange #ea580c, body #4b5563, line #e5e7eb, cream #fdfaf4
const NAVY = [11, 37, 69];
const ORANGE = [234, 88, 12];
const INK = [31, 41, 55];
const MUTED = [75, 85, 99];
const LINE = [229, 231, 235];
const ZEBRA = [253, 250, 244];
// fix260 (David): the SAME colour ramp as the charts on the screen (Charts.jsx RAMP, orange first), so a bar, column
// or slice has the same colour on paper as in the app and each one is told apart from its neighbour
const PALETTE = [[234, 88, 12], [79, 163, 165], [194, 100, 63], [126, 155, 84], [155, 111, 168],
    [78, 124, 168], [212, 166, 60], [176, 90, 120], [91, 140, 123], [138, 114, 80]];
const colour = (i) => PALETTE[i % PALETTE.length];
const NUMERIC = new Set(['money', 'number', 'percent']);

/**
 * Column widths that fit the page: each column asks for the width of its longest text (heading included, capped),
 * then the widths are scaled so they fill the usable width exactly. A column never gets less than `min` points.
 * wants: [number] (points each column would like), usable: total points available.
 */
export function fitColumns(wants, usable, min = 40) {
    const n = wants.length;
    if (!n) return [];
    const w = wants.map(x => Math.max(min, Number(x) || min));
    const sum = w.reduce((a, b) => a + b, 0);
    if (sum <= usable) {
        const extra = (usable - sum) / n;
        return w.map(x => x + extra);
    }
    // too wide: shrink the wide columns first, never below min
    let out = w.slice();
    for (let pass = 0; pass < 6; pass++) {
        const total = out.reduce((a, b) => a + b, 0);
        if (total <= usable + 0.5) break;
        const over = total - usable;
        const flexible = out.map(x => Math.max(0, x - min));
        const flexSum = flexible.reduce((a, b) => a + b, 0);
        if (flexSum <= 0) { out = out.map(() => usable / n); break; }
        out = out.map((x, i) => x - over * (flexible[i] / flexSum));
    }
    return out;
}

/** "nice" top value for a chart axis: 1, 2 or 5 times a power of ten, at or above max */
export function niceMax(max) {
    const m = Math.abs(Number(max) || 0);
    if (m === 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(m)));
    for (const k of [1, 2, 2.5, 5, 10]) if (k * p >= m) return k * p;
    return 10 * p;
}

/** Short money / number words for chart labels: 1250000 -> "1.25M", 85000 -> "85K" */
export function shortNumber(v) {
    const n = Number(v) || 0, a = Math.abs(n);
    const s = a >= 1e9 ? (a / 1e9).toFixed(a >= 1e10 ? 0 : 2) + 'B' : a >= 1e6 ? (a / 1e6).toFixed(a >= 1e7 ? 1 : 2) + 'M'
        : a >= 1e3 ? (a / 1e3).toFixed(a >= 1e4 ? 0 : 1) + 'K' : String(Math.round(a));
    return (n < 0 ? '-' : '') + s.replace(/\.0+([KMB])$/, '$1').replace(/(\.\d*?)0+([KMB])$/, '$1$2');
}

/** jsPDF's built-in font only knows plain Latin text: dashes, quotes and arrows are swapped for plain ones. */
export function plain(text) {
    return String(text == null ? '' : text)
        .replace(/[\u2013\u2014]/g, '-').replace(/[\u2018\u2019]/g, "'").replace(/[\u201C\u201D]/g, '"')
        .replace(/\u2192/g, '->').replace(/\u2026/g, '...').replace(/[^\x20-\x7E\u00A0-\u00FF]/g, '');
}

// ── chart drawing ──────────────────────────────────────────────────────

/** fix233: the REAL GES globe logo (website logo-globe.png, passed in as opts.logoImage) on a white disc, so its navy
 *  letters show on the navy band. No image (tests) = just the white disc. */
function logo(doc, cx, cy, r, img) {
    doc.setFillColor(255, 255, 255);
    doc.circle(cx, cy, r, 'F');
    if (!img) return;
    const s = r * 1.78;
    try { doc.addImage(img, 'PNG', cx - s / 2, cy - s / 2, s, s); } catch { /* the band still prints without it */ }
}

function drawBars(doc, rows, fmt, x, y, w, h) {
    const list = rows.slice(0, 16);
    const rowH = Math.min(30, h / Math.max(list.length, 1));
    const labelW = Math.min(170, w * 0.3);
    const valueW = 90;
    const trackW = w - labelW - valueW - 12;
    const max = Math.max(0, ...list.map(r => Math.abs(Number(r.value) || 0))) || 1;
    const top = y + Math.max(0, (h - list.length * rowH) / 2);   // fix260: centred in its box, like the donut
    doc.setFontSize(rowH >= 24 ? 9 : 8);
    list.forEach((r, i) => {
        const cy = top + i * rowH;
        doc.setTextColor(...INK);
        const label = doc.splitTextToSize(plain(r.label), labelW - 6)[0] || '';
        doc.text(label, x, cy + rowH * 0.62);
        doc.setFillColor(238, 234, 227);
        doc.rect(x + labelW, cy + rowH * 0.22, trackW, rowH * 0.56, 'F');
        doc.setFillColor(...colour(i));
        doc.rect(x + labelW, cy + rowH * 0.22, Math.max(1.5, trackW * (Math.abs(Number(r.value) || 0) / max)), rowH * 0.56, 'F');
        doc.setTextColor(...INK);
        doc.text(plain(fmt(r.value)), x + w, cy + rowH * 0.62, { align: 'right' });
    });
    return h;
}

function drawColumns(doc, rows, x, y, w, h, asLine) {
    const list = rows.slice(0, 24);
    const top = niceMax(Math.max(0, ...list.map(r => Number(r.value) || 0)));
    const axisW = 44, baseH = 26;
    const pw = w - axisW, ph = h - baseH;
    doc.setFontSize(7);
    for (let k = 0; k <= 4; k++) {
        const gy = y + ph - ph * (k / 4);
        doc.setDrawColor(...LINE); doc.setLineWidth(0.5);
        doc.line(x + axisW, gy, x + w, gy);
        doc.setTextColor(...MUTED);
        doc.text(shortNumber(top * k / 4), x + axisW - 4, gy + 2.5, { align: 'right' });
    }
    const slot = pw / Math.max(list.length, 1);
    const pts = [];
    list.forEach((r, i) => {
        const v = Math.max(0, Number(r.value) || 0);
        const bh = ph * (v / top);
        const cx = x + axisW + slot * i + slot / 2;
        if (asLine) pts.push([cx, y + ph - bh]);
        else { doc.setFillColor(...colour(i)); doc.rect(cx - slot * 0.32, y + ph - bh, slot * 0.64, bh, 'F'); }   // fix260
        doc.setTextColor(...INK);
        const lbl = doc.splitTextToSize(plain(r.label), Math.max(slot - 2, 20))[0] || '';
        doc.text(lbl, cx, y + ph + 11, { align: 'center' });
    });
    if (asLine && pts.length) {
        doc.setDrawColor(...ORANGE); doc.setLineWidth(1.6);
        for (let i = 1; i < pts.length; i++) doc.line(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]);
        pts.forEach(([px, py], i) => { doc.setFillColor(...colour(i)); doc.circle(px, py, 2.6, 'F'); });   // fix260
    }
    return h;
}

function drawDonut(doc, rows, fmt, x, y, w, h) {
    const list = rows.slice(0, 10);
    const total = list.reduce((a, r) => a + Math.max(0, Number(r.value) || 0), 0);
    const r = Math.min(h / 2 - 4, 92);
    const cx = x + r + 6, cy = y + h / 2;
    if (total > 0) {
        let a0 = -Math.PI / 2;
        list.forEach((row, i) => {
            const v = Math.max(0, Number(row.value) || 0);
            if (!v) return;
            const a1 = a0 + (v / total) * Math.PI * 2;
            const steps = Math.max(2, Math.ceil((a1 - a0) / 0.08));
            const path = [[cx, cy]];
            for (let s = 0; s <= steps; s++) { const a = a0 + (a1 - a0) * (s / steps); path.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
            const lines = path.slice(1).map((p, k) => [p[0] - path[k][0], p[1] - path[k][1]]);
            doc.setFillColor(...colour(i));
            doc.lines(lines, cx, cy, [1, 1], 'F', true);
            a0 = a1;
        });
        doc.setFillColor(255, 255, 255);
        doc.circle(cx, cy, r * 0.58, 'F');
    }
    doc.setTextColor(...INK);
    doc.setFontSize(11); doc.setFont('helvetica', 'bold');
    doc.text(plain(fmt(total)), cx, cy + 1, { align: 'center' });
    doc.setFont('helvetica', 'normal'); doc.setFontSize(7); doc.setTextColor(...MUTED);
    doc.text('TOTAL', cx, cy + 11, { align: 'center' });
    // legend beside the ring
    const lx = cx + r + 30, lw = x + w - lx;
    const step = Math.min(18, h / Math.max(list.length, 1));
    doc.setFontSize(8);
    list.forEach((row, i) => {
        const ly = y + (h - step * list.length) / 2 + i * step + step / 2;
        doc.setFillColor(...colour(i)); doc.rect(lx, ly - 4, 8, 8, 'F');
        doc.setTextColor(...INK);
        const pct = total > 0 ? Math.round((Math.max(0, Number(row.value) || 0) / total) * 100) : 0;
        const right = plain(fmt(row.value)) + '  (' + pct + '%)';
        doc.text(right, lx + lw, ly + 2.5, { align: 'right' });
        const room = lw - 16 - doc.getTextWidth(right) - 10;
        doc.text(doc.splitTextToSize(plain(row.label), Math.max(room, 40))[0] || '', lx + 14, ly + 2.5);
    });
    return h;
}

// ── the document ───────────────────────────────────────────────────────

/**
 * Writes and downloads the report PDF.
 * opts: { title, scopeLine, description, chartTypes (['bars'|'column'|'line'|'donut'], fix227) or chartType, chartRows, chartFormat,
 *         cols: [{ label, type, get }], rows, format(value, type), fileName }
 */
export async function writeReportPdf(opts) {
    const { jsPDF } = await import('jspdf');
    const doc = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
    const pw = doc.internal.pageSize.getWidth();
    const ph = doc.internal.pageSize.getHeight();
    const m = 32;
    const usable = pw - m * 2;
    const fmtCell = (c, r) => plain(opts.format(c.get(r), c.type));

    // ── cover band
    const band = (small) => {
        doc.setFillColor(...NAVY);
        doc.rect(0, 0, pw, small ? 34 : 78, 'F');
        doc.setFillColor(...ORANGE);
        doc.rect(0, small ? 34 : 78, pw, 2.5, 'F');
        // fix233: the GES globe logo (the website's logo)
        const lx = m + (small ? 9 : 16), ly = small ? 17 : 36, lr = small ? 9 : 16;
        logo(doc, lx, ly, lr, opts.logoImage);
        const tx = lx + lr + (small ? 8 : 12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(small ? 9 : 11);
        if (!small) doc.text('GE Solutions', tx, 24);
        doc.setTextColor(...ORANGE);
        doc.setFontSize(small ? 10 : 18);
        doc.text(plain(small ? 'GE Solutions  |  ' + opts.title : opts.title), tx, small ? 22 : 42);
        doc.setFont('helvetica', 'normal');
        if (!small) {
            doc.setTextColor(255, 255, 255); doc.setFontSize(9);
            doc.text(plain(opts.scopeLine), tx, 58);
            doc.setTextColor(203, 213, 225); doc.setFontSize(8);
            doc.text('Generated ' + plain(new Date().toLocaleString()), tx, 70);
        }
    };
    band(false);
    let y = 104;
    if (opts.description) {
        doc.setTextColor(...MUTED); doc.setFontSize(9);
        const lines = doc.splitTextToSize(plain(opts.description), usable);
        doc.text(lines, m, y);
        y += lines.length * 11 + 10;
    }

    // ── charts (drawn, not pictures). fix227: one or more -- one fills the cover; two sit side by side; more go
    //    two per page after the cover, before the table.
    const chartRows = opts.chartRows || [];
    const types = (opts.chartTypes || (opts.chartType ? [opts.chartType] : [])).filter(Boolean);
    if (types.length && chartRows.length) {
        const fmt = opts.chartFormat || String;
        const draw = (t, x, top, w, h) => {
            if (t === 'donut') drawDonut(doc, chartRows, fmt, x, top, w, h);
            else if (t === 'column') drawColumns(doc, chartRows, x, top, w, h, false);
            else if (t === 'line') drawColumns(doc, chartRows, x, top, w, h, true);
            else drawBars(doc, chartRows, fmt, x, top, w, h);
        };
        if (types.length === 1) draw(types[0], m, y, usable, Math.min(ph - y - 50, 330));
        else {
            const gap = 24, half = (usable - gap) / 2;
            for (let i = 0; i < types.length; i += 2) {
                if (i > 0) { doc.addPage(); band(true); y = 60; }
                const h = Math.min(ph - y - 50, 330);
                draw(types[i], m, y, half, h);
                if (types[i + 1]) draw(types[i + 1], m + half + gap, y, half, h);
            }
        }
    }

    // ── table pages
    const cols = opts.cols;
    const rows = opts.rows;
    doc.setFontSize(8);
    const sample = rows.slice(0, 400);
    const wants = cols.map(c => {
        doc.setFont('helvetica', 'bold');
        let w = doc.getTextWidth(plain(c.label).toUpperCase()) + 12;
        doc.setFont('helvetica', 'normal');
        for (const r of sample) w = Math.max(w, doc.getTextWidth(fmtCell(c, r)) + 12);
        return Math.min(w, 260);
    });
    const widths = fitColumns(wants, usable);
    const xs = []; let acc = m;
    widths.forEach(w => { xs.push(acc); acc += w; });
    const lineH = 10, padY = 5;

    const headRow = () => {
        doc.setFont('helvetica', 'bold'); doc.setFontSize(7.5);
        const heads = cols.map((c, i) => doc.splitTextToSize(plain(c.label).toUpperCase(), widths[i] - 8));
        const hh = Math.max(...heads.map(l => l.length)) * 9 + padY * 2;
        doc.setFillColor(...NAVY);
        doc.rect(m, y, usable, hh, 'F');
        doc.setTextColor(...ORANGE);
        heads.forEach((l, i) => {
            const right = NUMERIC.has(cols[i].type);
            doc.text(l, right ? xs[i] + widths[i] - 4 : xs[i] + 4, y + padY + 7, right ? { align: 'right' } : undefined);
        });
        doc.setFont('helvetica', 'normal');
        y += hh;
    };
    const newPage = () => { doc.addPage(); band(true); y = 54; headRow(); };

    if ((types.length && chartRows.length) || y > ph - 120) newPage(); else headRow();
    doc.setFontSize(8);
    rows.forEach((r, ri) => {
        const cells = cols.map((c, i) => {
            const t = fmtCell(c, r);
            return NUMERIC.has(c.type) ? [t] : doc.splitTextToSize(t, widths[i] - 8).slice(0, 4);
        });
        const rh = Math.max(...cells.map(l => l.length)) * lineH + padY * 2 - 2;
        if (y + rh > ph - 34) newPage();
        if (ri % 2 === 1) { doc.setFillColor(...ZEBRA); doc.rect(m, y, usable, rh, 'F'); }
        doc.setTextColor(...INK); doc.setFontSize(8);
        cells.forEach((l, i) => {
            const right = NUMERIC.has(cols[i].type);
            doc.text(l, right ? xs[i] + widths[i] - 4 : xs[i] + 4, y + padY + 6, right ? { align: 'right' } : undefined);
        });
        doc.setDrawColor(...LINE); doc.setLineWidth(0.4);
        doc.line(m, y + rh, m + usable, y + rh);
        y += rh;
    });
    if (!rows.length) { doc.setTextColor(...MUTED); doc.text('No rows for this report.', m, y + 16); }

    // ── footer on every page
    const pages = doc.getNumberOfPages();
    for (let p = 1; p <= pages; p++) {
        doc.setPage(p);
        doc.setFontSize(7); doc.setTextColor(...MUTED);
        doc.text(plain('GE Solutions  |  ' + opts.title + '  |  Page ' + p + ' of ' + pages), pw / 2, ph - 16, { align: 'center' });
    }
    if (opts.returnDoc) return doc;   // tests
    doc.save(opts.fileName);
    return doc;
}
