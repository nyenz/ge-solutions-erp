// PATH: erp-frontend/src/utils/stageCategory.js
// fix199 (David, test note 22): when a file is attached from a STAGE, the upload window starts with that stage's
// document type already picked. Staff can still change it (a default is only a starting value).
// The server has a type for every default stage (DocumentCategoryService.DEFAULTS); a stage added by hand is matched
// by its name when a type of the same name exists, otherwise nothing is picked.

const key = (v) => String(v || '').toLowerCase().replace(/\([^)]*\)/g, ' ').replace(/[^a-z]+/g, ' ').trim()
    .split(' ').filter(Boolean).map(w => (w.length > 3 && w.endsWith('s') ? w.slice(0, -1) : w)).join(' ');

const SPECIAL = [
    [(n) => n.includes('invoice') && n.includes('contract'), 'INVOICE'],
    [(n) => n === 'titled' || n === 'title', 'COPY_OF_TITLE'],
    [(n) => n.includes('invoice'), 'INVOICE'],
    [(n) => n.includes('progress') && n.includes('report') || n.includes('final report'), 'PROGRESS_REPORT'],
];

/** The document type code for a stage name, or '' when there is none. cats = [{ code, label }]. */
export function categoryForStage(stageName, cats) {
    const n = key(stageName);
    if (!n) return '';
    const list = cats || [];
    const has = (code) => list.some(c => c.code === code);
    for (const [test, code] of SPECIAL) if (test(n) && has(code)) return code;
    const hit = list.find(c => key(c.label) === n) || list.find(c => key(c.code) === n);
    return hit ? hit.code : '';
}
