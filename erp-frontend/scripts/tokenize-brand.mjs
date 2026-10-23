// PATH: erp-frontend/scripts/tokenize-brand.mjs
// One-off codemod (fix233) that makes the GES themes possible. Like tokenize-theme.mjs (fix182) it rewrites raw values in
// every CSS module into variables whose DEFAULT is the exact old value, so CREAM, SLATE and LIGHT look the same as before;
// only the GES themes in index.css (data-theme="ges" / "gesnavy") set the variables.
//   - the old orange #EE8C3A and its hover shades          -> var(--acc*, old)
//   - rgba(238,140,58,a)                                   -> rgba(var(--acc-rgb, 238, 140, 58), a)
//   - the old teal navy text / fills (#1a2e30, #213E40 ...) -> var(--brand-*, old)
//   - rgba(26,46,48,a) / rgba(33,62,64,a)                  -> rgba(var(--brand-*-rgb, old), a)
//   - the fonts Cinzel / Inter / DM Sans                   -> var(--font-head / --font-body / --font-ui, old)
// Safe to run again: it only touches raw values that are not already inside one of these variables.
// Usage: node scripts/tokenize-brand.mjs [--check]
import fs from 'fs';
import path from 'path';

const SRC = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'src');
const CHECK = process.argv.includes('--check');

const HEX = {
    '#ee8c3a': '--acc', '#f0a050': '--acc-hi', '#d97a2b': '--acc-dk', '#b8651d': '--acc-dk2',
    '#1a2e30': '--brand-ink', '#213e40': '--brand-2', '#1c3335': '--brand-1', '#162a2c': '--brand-head',
    '#16292b': '--brand-deep', '#2a4a4c': '--brand-raise-2', '#3a5a5c': '--brand-raise-1',
};
const RGB = [
    [/rgba\(\s*238\s*,\s*140\s*,\s*58\s*,/g, 'rgba(var(--acc-rgb, 238, 140, 58),'],
    [/rgba\(\s*26\s*,\s*46\s*,\s*48\s*,/g, 'rgba(var(--brand-ink-rgb, 26, 46, 48),'],
    [/rgba\(\s*33\s*,\s*62\s*,\s*64\s*,/g, 'rgba(var(--brand-2-rgb, 33, 62, 64),'],
];
const FONTS = [
    [/(?<!var\(--font-head, )'Cinzel'/g, "var(--font-head, 'Cinzel')"],
    [/(?<!var\(--font-body, )'Inter'/g, "var(--font-body, 'Inter')"],
    [/(?<!var\(--font-ui, )'DM Sans'/g, "var(--font-ui, 'DM Sans')"],
];

function walk(d) {
    return fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]);
}

// A hex that is already the fallback of one of our own variables is left alone (re-runs are no-ops).
const hexRe = /(var\(--(?:acc[a-z0-9-]*|brand-[a-z0-9-]+),\s*)?(#[0-9a-fA-F]{6})\b/g;

function rewriteLine(line) {
    if (/^\s*--(acc|brand-|font-)/.test(line)) return line;           // the variable definitions themselves
    if (/@import/.test(line)) return line;
    let out = line.replace(hexRe, (m, pre, h) => {
        if (pre) return m;
        const t = HEX[h.toLowerCase()];
        return t ? `var(${t}, ${h})` : h;
    });
    for (const [re, to] of RGB) out = out.replace(re, to);
    if (/font-family\s*:/.test(out) || /^\s*'(Cinzel|Inter|DM Sans)'/.test(out)) {
        for (const [re, to] of FONTS) out = out.replace(re, to);
    }
    return out;
}

let changed = 0, files = 0;
for (const f of walk(SRC).filter(p => p.endsWith('.css'))) {
    const src = fs.readFileSync(f, 'utf8');
    const out = src.split('\n').map(rewriteLine).join('\n');
    if (out !== src) {
        files++;
        changed += src.split('\n').filter((l, i) => l !== out.split('\n')[i]).length;
        if (!CHECK) fs.writeFileSync(f, out);
    }
}
console.log(`${CHECK ? 'would change' : 'changed'} ${changed} lines in ${files} files`);
