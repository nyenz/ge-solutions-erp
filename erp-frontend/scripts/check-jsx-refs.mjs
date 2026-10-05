// PATH: erp-frontend/scripts/check-jsx-refs.mjs
// fix182: "FiUser is not defined" crashed New Project because an icon was used in JSX without being imported, and
// ESLint 9 does not see names used inside JSX. This check runs before every build (npm run build -> prebuild):
//   - an Fi* icon (react-icons/fi) used but not imported FAILS the build (that is exactly the crash);
//   - any other <Capitalised /> tag that is neither imported nor declared in the file is printed as a warning.
// Comments are ignored.
import fs from 'fs';
import path from 'path';

const SRC = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'src');
const walk = (d) => fs.readdirSync(d, { withFileTypes: true })
    .flatMap(e => (e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]));

let failed = 0;
for (const f of walk(SRC).filter(x => /\.jsx?$/.test(x))) {
    const s = fs.readFileSync(f, 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1');
    const declared = (name) => new RegExp(
        `import[^;]*\\b${name}\\b[^;]*from` +            // import { X } / import X
        `|(const|let|var|function|class)\\s+${name}\\b` +  // const X = / function X
        `|[{,]\\s*(\\w+\\s*:\\s*)?${name}\\s*(=[^,}]*)?[,}]`, // destructured { X } or { icon: X }
        's').test(s);
    const used = new Set();
    for (const m of s.matchAll(/<([A-Z][A-Za-z0-9]*)[\s/>]/g)) used.add(m[1]);
    for (const m of s.matchAll(/\b(Fi[A-Z][A-Za-z0-9]*)\b/g)) used.add(m[1]);
    for (const name of used) {
        if (declared(name)) continue;
        const rel = path.relative(SRC, f);
        if (/^Fi[A-Z]/.test(name)) { console.error(`[check-jsx-refs] ${rel}: ${name} is used but not imported from react-icons/fi`); failed++; }
        else console.warn(`[check-jsx-refs] warning: ${rel}: <${name}> is not imported or declared in this file`);
    }
}
if (failed) { console.error(`[check-jsx-refs] ${failed} missing icon import(s): the page would crash. Build stopped.`); process.exit(1); }
console.log('[check-jsx-refs] every icon used is imported');
