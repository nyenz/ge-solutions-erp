// fix186: the photo shrink rules (the decisions; the drawing itself needs a browser). Run with `npm test`.
import test from 'node:test';
import assert from 'node:assert/strict';
import { SHRINK, isShrinkablePhoto, planShrink, targetSize, isClearlySmaller, shrunkName, fmtSize, sizeNote, shrinkImage, shrinkFiles, prepareUploads, anyToShrink } from '../src/utils/imageShrink.js';

const MB = 1024 * 1024;
const f = (name, type, size) => ({ name, type, size });

test('the numbers are the ones David asked for', () => {
    assert.equal(SHRINK.maxSide, 3000);
    assert.ok(SHRINK.quality >= 0.90 && SHRINK.quality <= 0.92);
    assert.equal(SHRINK.minBytes, MB);
    assert.equal(SHRINK.minSaving, 0.25);
});

test('a PDF is never touched, whatever its size or type', () => {
    assert.equal(isShrinkablePhoto(f('deed.pdf', 'application/pdf', 40 * MB)), false);
    assert.equal(isShrinkablePhoto(f('deed.PDF', '', 40 * MB)), false);
    assert.equal(isShrinkablePhoto(f('odd.pdf', 'image/jpeg', 40 * MB)), false);
    assert.deepEqual(planShrink(f('deed.pdf', 'application/pdf', 40 * MB)), { action: 'keep', reason: 'not a photo' });
});

test('only JPG, PNG and WEBP are photos', () => {
    assert.equal(isShrinkablePhoto(f('id.jpg', 'image/jpeg', 5 * MB)), true);
    assert.equal(isShrinkablePhoto(f('id.png', 'image/png', 5 * MB)), true);
    assert.equal(isShrinkablePhoto(f('id.webp', 'image/webp', 5 * MB)), true);
    assert.equal(isShrinkablePhoto(f('ID.JPEG', '', 5 * MB)), true);          // a phone that sends no type
    assert.equal(isShrinkablePhoto(f('id.heic', 'image/heic', 5 * MB)), false);
    assert.equal(isShrinkablePhoto(f('sheet.xlsx', '', 5 * MB)), false);
    assert.equal(isShrinkablePhoto(null), false);
});

test('a file under 1 MB is never touched', () => {
    assert.deepEqual(planShrink(f('id.jpg', 'image/jpeg', MB - 1)), { action: 'keep', reason: 'already small' });
    assert.deepEqual(planShrink(f('id.jpg', 'image/jpeg', MB)), { action: 'try' });
    assert.deepEqual(planShrink(f('id.jpg', 'image/jpeg', 0)), { action: 'keep', reason: 'already small' });
});

test('the picture is resized only when its long side is above 3000 px, and never stretched', () => {
    assert.deepEqual(targetSize(3000, 2000), { width: 3000, height: 2000, resized: false });
    assert.deepEqual(targetSize(1200, 800), { width: 1200, height: 800, resized: false });
    assert.deepEqual(targetSize(6000, 4000), { width: 3000, height: 2000, resized: true });
    assert.deepEqual(targetSize(3000, 4000), { width: 2250, height: 3000, resized: true });   // a tall phone photo
    assert.deepEqual(targetSize(12000, 9000), { width: 3000, height: 2250, resized: true });
});

test('the original is kept unless the new file is at least 25% smaller', () => {
    assert.equal(isClearlySmaller(4 * MB, 3 * MB), true);        // exactly 25% smaller
    assert.equal(isClearlySmaller(4 * MB, 3 * MB + 1), false);
    assert.equal(isClearlySmaller(4 * MB, 5 * MB), false);       // bigger: keep the original
    assert.equal(isClearlySmaller(4 * MB, 0), false);
    assert.equal(isClearlySmaller(0, 10), false);
});

test('names and sizes shown to staff', () => {
    assert.equal(shrunkName('ID front.PNG'), 'ID front.jpg');
    assert.equal(shrunkName('receipt.webp'), 'receipt.jpg');
    assert.equal(shrunkName('scan'), 'scan.jpg');
    assert.equal(fmtSize(5 * MB), '5.0 MB');
    assert.equal(fmtSize(734003), '717 KB');
    assert.equal(sizeNote({ shrunk: true, before: 4 * MB, after: MB }), '4.0 MB -> 1.0 MB (75% smaller)');
    assert.equal(sizeNote({ shrunk: false, before: 2 * MB, after: 2 * MB }), '2.0 MB');
    assert.equal(sizeNote(null), '');
});

test('without a browser nothing is changed and nothing breaks (the original is kept)', async () => {
    const pdf = f('deed.pdf', 'application/pdf', 9 * MB);
    const small = f('id.jpg', 'image/jpeg', 300000);
    const big = f('id.jpg', 'image/jpeg', 6 * MB);     // would be tried; node has no canvas, so the original stays
    const [a, b, c] = await shrinkFiles([pdf, small, big]);
    assert.equal(a.file, pdf); assert.equal(a.shrunk, false);
    assert.equal(b.file, small); assert.equal(b.shrunk, false);
    assert.equal(c.file, big); assert.equal(c.shrunk, false); assert.equal(c.before, 6 * MB);
    assert.equal((await shrinkImage(big)).reason, 'could not be opened');
});

test('prepareUploads: wrong kind, empty and too-big files are refused; the rest pass with a size note', async () => {
    const files = [f('a.docx', '', 5000), f('b.pdf', 'application/pdf', 0), f('c.pdf', 'application/pdf', 60 * MB),
        f('d.pdf', 'application/pdf', 2 * MB), f('e.jpg', 'image/jpeg', 300000)];
    const r = await prepareUploads(files);
    assert.deepEqual(r.bad, ['a.docx (use PDF, JPG, PNG or WEBP)', 'b.pdf (the file is empty)', 'c.pdf (over 50 MB)']);
    assert.deepEqual(r.ok.map(x => x.file.name), ['d.pdf', 'e.jpg']);
    assert.equal(r.ok[0].note, '2.0 MB');
    assert.equal(r.ok[0].shrunk, false);
    // the receipt limit is 10 MB
    const rc = await prepareUploads([f('r.pdf', 'application/pdf', 11 * MB)], { maxBytes: 10 * MB });
    assert.deepEqual(rc.bad, ['r.pdf (over 10 MB)']);
});

test('anyToShrink is true only for a photo of 1 MB or more', () => {
    assert.equal(anyToShrink([f('a.pdf', 'application/pdf', 9 * MB), f('b.jpg', 'image/jpeg', 2000)]), false);
    assert.equal(anyToShrink([f('b.jpg', 'image/jpeg', 2 * MB)]), true);
    assert.equal(anyToShrink(null), false);
});
