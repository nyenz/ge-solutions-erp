// PATH: erp-frontend/scripts/tokenize-theme.mjs
// One-off codemod (fix182) that made the LIGHT page theme possible. It rewrites the hard-coded panel colours in every
// CSS module into theme variables whose DEFAULT is the exact old value, so CREAM and SLATE look the same as before and
// only :root[data-theme="bright"] (index.css) changes them. Safe to run again: it only touches raw values.
//   - dark surfaces (#1c3335, #213E40, #162a2c ...) in background / border / gradient values -> var(--sf-*)
//   - white washes and hairlines rgba(255,255,255,a<=0.35) and white text -> rgba(var(--ink-rgb), a) / var(--ink-solid)
//   - the light accent text colours made for navy (#fca5a5, #67e8f9 ...) -> var(--tx-*)
// White text on a solid accent fill (an orange button) is left white.
// Usage: node scripts/tokenize-theme.mjs [--check]
import fs from 'fs';
import path from 'path';

const SRC = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'src');
const CHECK = process.argv.includes('--check');

const SURFACE = {
    '#1c3335': '--sf-1', '#213e40': '--sf-2', '#162a2c': '--sf-head', '#16292b': '--sf-deep', '#1a2e30': '--sf-navy',
    '#3a5a5c': '--sf-raise-1', '#2a4a4c': '--sf-raise-2', '#4d5c5a': '--sf-dock', '#0a0a0a': '--sf-black',
    '#0f1f21': '--sf-black', '#122224': '--sf-deep', '#1e3a3c': '--sf-2', '#243f41': '--sf-2', '#1f3638': '--sf-1',
    '#14262a': '--sf-head', '#24454a': '--sf-2', '#2b5157': '--sf-raise-2', '#28383a': '--sf-readout', '#20403c': '--sf-2',
};
const TEXT = {
    '#fca5a5': '--tx-red', '#f87171': '--tx-red', '#fecaca': '--tx-red-soft', '#67e8f9': '--tx-cyan', '#22d3ee': '--tx-cyan',
    '#34d399': '--tx-green', '#4ade80': '--tx-green', '#6ee7b7': '--tx-green', '#fcd34d': '--tx-yellow', '#fbbf24': '--tx-amber',
    '#ffb46b': '--tx-orange', '#ee8c3a': '--tx-accent', '#a5f3fc': '--tx-cyan', '#86efac': '--tx-green', '#fde68a': '--tx-yellow',
};
const SOLID_FILL = /(#ee8c3a|#f0a050|#d97a2b|#ef4444|#dc2626|#b91c1c|#10b981|#22c55e|#059669|#06b6d4|#0891b2|#f59e0b|#eab308|#34d399|#22d3ee|var\(--(orange|red|green|accent|cyan|violet|slate|emerald|ruby)\))/i;

function walk(d) {
    return fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]);
}

const hexRe = /#[0-9a-fA-F]{6}\b/g;
const whiteRgba = /rgba\(\s*(?:255\s*,\s*255\s*,\s*255|244\s*,\s*242\s*,\s*239)\s*,\s*([0-9.]+)\s*\)/g;
const navyRgba = /rgba\(\s*(26\s*,\s*46\s*,\s*48|22\s*,\s*42\s*,\s*44|28\s*,\s*51\s*,\s*53|33\s*,\s*62\s*,\s*64)\s*,\s*([0-9.]+)\s*\)/g;
const blackRgba = /rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*([0-9.]+)\s*\)/g;

function surfaces(val) {
    return val.replace(hexRe, h => (SURFACE[h.toLowerCase()] ? `var(${SURFACE[h.toLowerCase()]}, ${h})` : h));
}

function transformDecl(prop, val, solidFill) {
    const p = prop.toLowerCase();
    if (/var\(--(sf|ink|tx)-/.test(val) && !/rgba\(\s*(255|244)/.test(val)) return val;   // already done
    if (p.startsWith('--')) {
        if (/^--(navy|text-dark|cream|bg|ink|accent-ink|fs-dark)/.test(p)) return val;
        // a variable that holds a TEXT colour for a panel: same rule as color:
        if (/(on-panel|ls-text|^--text)/.test(p)) return transformDecl('color', val, false);
        let v = surfaces(val);
        v = v.replace(whiteRgba, (m, a) => (Number(a) <= 0.35 ? `rgba(var(--ink-rgb), ${a})` : m));
        return v;
    }
    if (p === 'color' || p === '-webkit-text-fill-color' || p === 'caret-color' || p === 'fill' || p === 'stroke') {
        let v = val;
        if (!solidFill) {
            v = v.replace(/^\s*(#fff|#ffffff|white|#f4f2ef)(?![0-9a-f])/i, 'var(--ink-solid)');
            v = v.replace(whiteRgba, (m, a) => `rgba(var(--ink-rgb), ${a})`);
            v = v.replace(hexRe, h => (TEXT[h.toLowerCase()] ? `var(${TEXT[h.toLowerCase()]}, ${h})` : h));
        }
        return v;
    }
    if (p.startsWith('background') || p.startsWith('border') || p.startsWith('outline')) {
        let v = surfaces(val);
        v = v.replace(whiteRgba, (m, a) => (Number(a) <= 0.35 ? `rgba(var(--ink-rgb), ${a})` : m));
        v = v.replace(navyRgba, (m, _rgb, a) => (Number(a) >= 0.5 ? `rgba(var(--sf-navy-rgb), ${a})` : m));
        if (p.startsWith('background')) v = v.replace(blackRgba, (m, a) => (Number(a) <= 0.4 ? `rgba(var(--well), ${a})` : m));
        return v;
    }
    return val;
}

let changedFiles = 0;
for (const f of walk(SRC).filter(x => x.endsWith('.css') && !x.endsWith('index.css'))) {
    const src = fs.readFileSync(f, 'utf8');
    // innermost { declarations } blocks; comments are kept as they are
    const out = src.replace(/\{([^{}]*)\}/g, (block, body) => {
        const decls = body.replace(/\/\*[\s\S]*?\*\//g, '');
        const bg = (decls.match(/(^|;|\s)background(-color)?\s*:\s*([^;]+)/i) || [])[3] || '';
        const first = (bg.match(/#[0-9a-fA-F]{3,6}\b|var\(--[a-z-]+\)|rgba?\([^)]*\)|transparent|none/i) || [''])[0];
        const solidFill = SOLID_FILL.test(first);
        const nb = body.replace(/(^|[;\s{])([-a-zA-Z]+)(\s*:\s*)([^;{}]+)/g, (m, pre, prop, colon, val) => {
            if (/\/\*/.test(val)) {
                // value followed by a comment on the same line: transform only the part before it
                const i = val.indexOf('/*');
                return pre + prop + colon + transformDecl(prop, val.slice(0, i), solidFill) + val.slice(i);
            }
            return pre + prop + colon + transformDecl(prop, val, solidFill);
        });
        return '{' + nb + '}';
    });
    if (out !== src) {
        changedFiles++;
        if (!CHECK) fs.writeFileSync(f, out);
        else console.log('would change', path.relative(SRC, f));
    }
}
console.log(`${CHECK ? 'checked' : 'tokenised'} ${changedFiles} file(s)`);
