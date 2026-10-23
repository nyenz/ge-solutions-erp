// PATH: docs/guide/build-guide.mjs
// fix231: makes the SHAREABLE guide -- one HTML file with every picture inside it -- from the app's guide player
// (erp-frontend/public/guide/index.html) and the recorded steps (guide.json + pictures, made by erp-frontend/e2e/guide.mjs).
//   node docs/guide/build-guide.mjs  ->  docs/guide/golden-seed-guide.html
import fs from 'node:fs';
import path from 'node:path';

const dir = path.resolve('erp-frontend/public/guide');
const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(dir, 'guide.json'), 'utf8'));
data.images = {};
for (const t of data.tasks) for (const s of t.steps) {
    const file = path.join(dir, s.img);
    if (fs.existsSync(file) && !data.images[s.img]) data.images[s.img] = 'data:image/jpeg;base64,' + fs.readFileSync(file).toString('base64');
}
const inject = '<script>window.GUIDE_DATA = ' + JSON.stringify(data) + ';</script>\n<script>';
const out = html.replace('<script>', inject);
fs.writeFileSync(path.resolve('docs/guide/golden-seed-guide.html'), out);
console.log('docs/guide/golden-seed-guide.html', Math.round(out.length / 1024) + ' KB');
