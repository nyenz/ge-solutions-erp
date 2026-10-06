// PATH: erp-frontend/src/utils/imageShrink.js
// fix186: a GENTLE shrink for photos before they are uploaded (IDs, receipts, deed plans).
// The aim is smaller files with no visible loss. When in doubt the ORIGINAL is kept.
//
// THE RULES (David, October 2026) -- all the numbers live in SHRINK below:
//   1. Only JPG, PNG and WEBP photos are ever touched. A PDF is NEVER touched.
//   2. A file under about 1 MB is never touched.
//   3. The picture is made smaller only when its long side is above about 3000 px (it becomes 3000 px).
//   4. The result is saved as a JPEG at about 91% quality.
//   5. The original is ALWAYS kept unless the new file is clearly smaller (at least 25% smaller).
//   6. Anything that goes wrong (the phone cannot open the photo, not enough memory) keeps the original.
// Staff see the size before and after next to each file (sizeNote).
//
// The decisions (planShrink, isClearlySmaller, shrunkName, fmtSize, sizeNote) are plain functions with tests in
// tests/imageShrink.test.mjs. Only shrinkImage() needs a browser (it draws the photo on a canvas).

export const SHRINK = {
    maxSide: 3000,              // long side above this is scaled down to this
    quality: 0.91,              // JPEG quality (0.90 - 0.92 asked)
    minBytes: 1024 * 1024,      // files under 1 MB are never touched
    minSaving: 0.25,            // keep the new file only when it is at least 25% smaller
    types: ['image/jpeg', 'image/png', 'image/webp'],
    exts: ['jpg', 'jpeg', 'png', 'webp'],
};

const extOf = (name) => { const m = String(name || '').toLowerCase().match(/\.([a-z0-9]+)$/); return m ? m[1] : ''; };

/** true for a JPG / PNG / WEBP photo (by type, or by file ending when the phone sends no type). Never for a PDF. */
export function isShrinkablePhoto(file) {
    if (!file) return false;
    const ext = extOf(file.name);
    if (ext === 'pdf' || file.type === 'application/pdf') return false;
    if (file.type) return SHRINK.types.includes(String(file.type).toLowerCase());
    return SHRINK.exts.includes(ext);
}

/**
 * What to do with a picked file, BEFORE opening it.
 *  -> { action: 'keep', reason }  or  { action: 'try' }
 */
export function planShrink(file) {
    if (!isShrinkablePhoto(file)) return { action: 'keep', reason: 'not a photo' };
    if (!(Number(file.size) >= SHRINK.minBytes)) return { action: 'keep', reason: 'already small' };
    return { action: 'try' };
}

/** The size the picture is drawn at: unchanged, or the long side brought down to maxSide (never made bigger). */
export function targetSize(width, height, maxSide = SHRINK.maxSide) {
    const w = Math.max(1, Math.round(Number(width) || 0));
    const h = Math.max(1, Math.round(Number(height) || 0));
    const long = Math.max(w, h);
    if (long <= maxSide) return { width: w, height: h, resized: false };
    const k = maxSide / long;
    return { width: Math.max(1, Math.round(w * k)), height: Math.max(1, Math.round(h * k)), resized: true };
}

/** Rule 5: the new file replaces the original only when it is clearly smaller. */
export function isClearlySmaller(originalBytes, newBytes, minSaving = SHRINK.minSaving) {
    const a = Number(originalBytes), b = Number(newBytes);
    if (!(a > 0) || !(b > 0)) return false;
    return b <= a * (1 - minSaving);
}

/** "scan.PNG" -> "scan.jpg" (the result is always a JPEG); a name without an ending just gets ".jpg". */
export function shrunkName(name) {
    const n = String(name || 'photo');
    return /\.[A-Za-z0-9]+$/.test(n) ? n.replace(/\.[A-Za-z0-9]+$/, '.jpg') : n + '.jpg';
}

/** 5,242,880 -> "5.0 MB"; 734,003 -> "717 KB" */
export function fmtSize(bytes) {
    const b = Number(bytes) || 0;
    if (b >= 1024 * 1024) return (b / (1024 * 1024)).toFixed(1) + ' MB';
    if (b >= 1024) return Math.round(b / 1024) + ' KB';
    return b + ' B';
}

/** The short text staff read next to a file: "4.8 MB -> 1.2 MB (75% smaller)" or just "2.1 MB". */
export function sizeNote(result) {
    if (!result) return '';
    if (result.shrunk) {
        const pct = Math.round((1 - result.after / result.before) * 100);
        return fmtSize(result.before) + ' -> ' + fmtSize(result.after) + ' (' + pct + '% smaller)';
    }
    return fmtSize(result.before);
}

const keep = (file, reason) => ({ file, original: file, shrunk: false, before: file.size, after: file.size, reason });

async function openBitmap(file) {
    if (typeof createImageBitmap === 'function') {
        try { return await createImageBitmap(file, { imageOrientation: 'from-image' }); }
        catch { /* some browsers refuse the option: try the plain call, then the <img> way */ }
        try { return await createImageBitmap(file); } catch { /* fall through */ }
    }
    return await new Promise((resolve, reject) => {
        const url = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
        img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('the photo could not be opened')); };
        img.src = url;
    });
}

function draw(source, sw, sh, tw, th) {
    // Going down by more than half in one step makes fine print (ID numbers, stamps) jagged, so halve first.
    let cur = source, cw = sw, ch = sh;
    while (cw / 2 >= tw && ch / 2 >= th) {
        const half = document.createElement('canvas');
        half.width = Math.max(1, Math.round(cw / 2)); half.height = Math.max(1, Math.round(ch / 2));
        const hx = half.getContext('2d');
        hx.imageSmoothingEnabled = true; hx.imageSmoothingQuality = 'high';
        hx.drawImage(cur, 0, 0, half.width, half.height);
        cur = half; cw = half.width; ch = half.height;
    }
    const canvas = document.createElement('canvas');
    canvas.width = tw; canvas.height = th;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';            // a see-through PNG becomes white paper, not black
    ctx.fillRect(0, 0, tw, th);
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(cur, 0, 0, tw, th);
    return canvas;
}

/**
 * Shrinks ONE picked file by the rules above. Never throws.
 *  -> { file, original, shrunk, before, after, reason }   (file === original when nothing was changed)
 */
export async function shrinkImage(file) {
    const plan = planShrink(file);
    if (plan.action === 'keep') return keep(file, plan.reason);
    let bitmap = null;
    try {
        bitmap = await openBitmap(file);
        const sw = bitmap.width || bitmap.naturalWidth, sh = bitmap.height || bitmap.naturalHeight;
        if (!sw || !sh) return keep(file, 'could not be read');
        const t = targetSize(sw, sh);
        const canvas = draw(bitmap, sw, sh, t.width, t.height);
        const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', SHRINK.quality));
        canvas.width = 0; canvas.height = 0;   // give the memory back at once (phones)
        if (!blob || !blob.size) return keep(file, 'could not be saved');
        if (!isClearlySmaller(file.size, blob.size)) return keep(file, 'not clearly smaller');
        const out = new File([blob], shrunkName(file.name), { type: 'image/jpeg', lastModified: file.lastModified || Date.now() });
        return { file: out, original: file, shrunk: true, before: file.size, after: out.size, reason: t.resized ? 'resized' : 're-saved' };
    } catch {
        return keep(file, 'could not be opened');
    } finally {
        if (bitmap && typeof bitmap.close === 'function') bitmap.close();
    }
}

/** Shrinks a list, one file at a time (a phone cannot hold several big photos open at once). Same order. */
export async function shrinkFiles(files) {
    const out = [];
    for (const f of (files || [])) out.push(await shrinkImage(f));
    return out;
}

/**
 * THE one door every file picker uses (New Project, Folder documents, payment receipt, Pending page).
 * 1. refuses a wrong kind of file and an empty file,
 * 2. shrinks the photos by the rules above,
 * 3. applies the size limit to the file that will really be SENT (so a 14 MB phone photo of a receipt that shrinks
 *    to 2 MB passes the 10 MB receipt limit; a file that is still too big is refused as before).
 *  -> { ok: [{ file, note, shrunk, before, after }], bad: ['name (why)'] }
 */
export async function prepareUploads(files, { maxBytes = 50 * 1024 * 1024, exts = ['pdf', 'jpg', 'jpeg', 'png', 'webp'] } = {}) {
    const ok = [], bad = [];
    for (const f of Array.from(files || [])) {
        if (!exts.includes(extOf(f.name))) { bad.push(f.name + ' (use PDF, JPG, PNG or WEBP)'); continue; }
        if (!f.size) { bad.push(f.name + ' (the file is empty)'); continue; }
        const r = await shrinkImage(f);
        if (r.file.size > maxBytes) { bad.push(f.name + ' (over ' + Math.round(maxBytes / (1024 * 1024)) + ' MB)'); continue; }
        ok.push({ file: r.file, note: sizeNote(r), shrunk: r.shrunk, before: r.before, after: r.after });
    }
    return { ok, bad };
}

/** true when at least one picked file is a photo big enough to be worked on (so the page can say "preparing...") */
export const anyToShrink = (files) => Array.from(files || []).some(f => planShrink(f).action === 'try');
