// fix181 (16.10a, 9.x): every default column and every field a catalogue report names must exist in its dataset, so a
// typo can never silently drop a column again. Also checks the filter rules changed in 9.4 and 10.8.
import test from 'node:test';
import assert from 'node:assert/strict';
import { DATASET_META, fieldsFor, applyFilters } from '../src/pages/Reports/reportFields.js';
import { CATALOGUE, ENTITIES, DEFAULTS } from '../src/pages/Reports/reportsCatalog.js';

const visibleLabels = (ds) => new Set(fieldsFor(ds, true).map(f => f.label));
const allLabels = (ds) => new Set(ds.fields.map(f => f.label));

test('every default column is a real, visible field', () => {
    for (const ds of Object.values(DATASET_META)) {
        const keys = new Set(fieldsFor(ds, true).map(f => f.key));
        for (const k of ds.defaultColumns) assert.ok(keys.has(k), `${ds.key}: default column '${k}' does not exist`);
    }
});

test('every catalogue report names fields that exist in its dataset', () => {
    const ids = new Set();
    for (const r of CATALOGUE) {
        assert.ok(!ids.has(r.id), 'duplicate report id ' + r.id);
        ids.add(r.id);
        const ds = DATASET_META[r.ds];
        assert.ok(ds, `${r.id}: unknown dataset ${r.ds}`);
        const vis = visibleLabels(ds), all = allLabels(ds);
        for (const c of r.cols) assert.ok(vis.has(c), `${r.id}: column '${c}' is not a field of ${r.ds}`);
        if (r.groupBy) assert.ok(all.has(r.groupBy), `${r.id}: groupBy '${r.groupBy}' is not a field`);
        if (r.measure && r.measure.field) assert.ok(all.has(r.measure.field), `${r.id}: measure field '${r.measure.field}' is not a field`);
        for (const fl of [].concat(r.filter || [])) assert.ok(all.has(fl.field), `${r.id}: filter field '${fl.field}' is not a field`);
        if (r.sort && r.sort.col) assert.ok(vis.has(r.sort.col), `${r.id}: sort column '${r.sort.col}' is not a field`);
    }
});

test('entity pickers and the default report per scope exist', () => {
    for (const [ds, list] of Object.entries(ENTITIES)) {
        for (const e of list) assert.ok(allLabels(DATASET_META[ds]).has(e.field), `${ds}: entity field '${e.field}' missing`);
    }
    const titles = new Set(CATALOGUE.map(r => r.title));
    for (const [ds, map] of Object.entries(DEFAULTS)) {
        for (const t of Object.values(map)) assert.ok(titles.has(t), `${ds}: default report '${t}' missing`);
    }
});

test('"on or before" keeps the whole day and code lists filter exactly', () => {
    const ds = DATASET_META.COMPANY;
    const rows = [
        { timestamp: '2030-01-15T23:59:30', action: 'RECORD_DELETED', performedBy: 'mary' },
        { timestamp: '2030-01-16T00:00:01', action: 'LOGIN_SUCCESS', performedBy: 'SYSTEM' },
    ];
    assert.equal(applyFilters(rows, ds, [{ field: 'timestamp', op: 'before', value: '2030-01-15' }]).length, 1);
    assert.equal(applyFilters(rows, ds, [{ field: 'action', op: 'oneOf', value: ['RECORD_DELETED', 'RECORD_RESTORED'] }]).length, 1);
    assert.equal(applyFilters(rows, ds, [{ field: 'operator', op: 'noneOf', value: ['SYSTEM (automatic)'] }]).length, 1);
});
