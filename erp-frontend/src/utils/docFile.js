// PATH: erp-frontend/src/utils/docFile.js
// fix261 (David): ONE way to fetch a stored document so a page can show it (the Folder's View, the Payments receipt).
// A PDF or picture comes back as a typed blob link the page can show in a frame / image; any other file (Word, Excel)
// is downloaded with its own name, because a browser cannot show it.

export const fileExt = (name) => { const m = String(name || '').toLowerCase().match(/[.]([a-z0-9]{1,6})$/); return m ? m[1] : ''; };

/** The address of a stored file: a full web address as it is, a server path under the vault. */
export const docUrl = (filePath) => {
    if (!filePath) return '#';
    if (filePath.startsWith('http')) return filePath;
    const parts = filePath.split(/ge_uploads[/]/);
    const rel = parts.length > 1 ? parts[1] : filePath;
    const base = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions.onrender.com/api/v1';
    return base + '/vault/' + rel.replace(/\\/g, '/');
};

/**
 * Fetches the file. Returns { name, url, isPdf, ratio } for something the page can show (url = a blob link the caller
 * must free with URL.revokeObjectURL), or null when the file was downloaded instead. Throws when it cannot be reached.
 */
export async function fetchDoc(filePath, fileName) {
    const url = docUrl(filePath);
    const isHttp = filePath.startsWith('http');
    const clean = filePath.split('?')[0];
    const ext = fileExt(fileName || clean) || fileExt(clean);
    const mime = { pdf: 'application/pdf', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' }[ext];
    let name = fileName;
    if (!name) { try { name = decodeURIComponent(clean.split(/[\\/]/).pop() || 'Document'); } catch { name = 'Document'; } }
    const r = await fetch(url, { headers: isHttp ? {} : { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } });
    if (!r.ok) throw new Error('not reachable');
    const raw = await r.blob();
    const blob = mime ? new Blob([raw], { type: mime }) : raw;
    const isPdf = ext === 'pdf' || blob.type === 'application/pdf';
    const isImg = !isPdf && String(blob.type || '').startsWith('image/');
    if (!isPdf && !isImg) {
        const o = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = o; a.download = name; document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(o), 60000);
        return null;
    }
    const href = URL.createObjectURL(blob);
    let ratio = 0.707;   // A4 portrait fallback
    try {
        if (isPdf) {
            const txt = new TextDecoder('latin1').decode(await blob.slice(0, 3000000).arrayBuffer());
            const mb = txt.match(/\/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]/);
            if (mb) {
                let w = Math.abs(mb[3] - mb[1]); let h = Math.abs(mb[4] - mb[2]);
                const rot = txt.match(/\/Rotate\s+(-?\d+)/);
                if (rot && Math.abs(parseInt(rot[1], 10)) % 180 === 90) { const t = w; w = h; h = t; }
                if (w > 0 && h > 0) ratio = w / h;
            }
        } else {
            ratio = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im.naturalWidth / im.naturalHeight); im.onerror = rej; im.src = href; });
        }
    } catch { /* keep the portrait default */ }
    return { name, url: href, isPdf, ratio: Math.min(4, Math.max(0.25, ratio || 0.707)) };
}
