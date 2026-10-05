// PATH: erp-frontend/scripts/check-audit-codes.mjs
// fix181 (10.2): lists audit codes the server writes that the Audit catalog does not know, and catalog codes no server
// code writes. It only WARNS (never fails the build): an unknown code still shows, just in grey with its raw name.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const backend = path.resolve(here, '../../erp-backend/src/main/java');
const catalog = path.resolve(here, '../src/pages/Audit/auditCatalog.js');
if (!fs.existsSync(backend) || !fs.existsSync(catalog)) process.exit(0);

const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => {
    const p = path.join(dir, e.name);
    return e.isDirectory() ? walk(p) : (p.endsWith('.java') ? [p] : []);
});
const server = new Set();
for (const file of walk(backend)) {
    if (file.endsWith('ScenarioSeeder.java')) continue;   // the demo seeder may write old codes for old-looking rows
    const lines = fs.readFileSync(file, 'utf8').split('\n');
    lines.forEach((line, i) => {
        const at = line.search(/logAction(As|AfterCommit)?\s*\(|reportFailures\s*\(/);
        if (at < 0) return;
        // only the call's own line, and the next line when the call continues there (not a following statement)
        let text = line.slice(at);
        if (!/;\s*$/.test(line)) text += ' ' + (lines[i + 1] || '');
        text = text.split(';')[0];
        for (const m of text.matchAll(/"([A-Z][A-Z0-9_]{2,})"/g)) server.add(m[1]);
    });
}
const known = new Set([...fs.readFileSync(catalog, 'utf8').matchAll(/code:\s*'([A-Z0-9_]+)'/g)].map(m => m[1]));
const missing = [...server].filter(c => !known.has(c)).sort();
const unused = [...known].filter(c => !server.has(c)).sort();
if (missing.length) console.warn('[audit-codes] written by the server but not in auditCatalog.js: ' + missing.join(', '));
if (unused.length) console.log('[audit-codes] in the catalog but not written by current server code (old rows / demo): ' + unused.join(', '));
if (!missing.length) console.log('[audit-codes] every server audit code is in the catalog.');
