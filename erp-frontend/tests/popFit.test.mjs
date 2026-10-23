// fix226 (David): pop-outs are never cut off by the screen edge.
import test from 'node:test';
import assert from 'node:assert/strict';
import { fitBelowOrAbove } from '../src/utils/popFit.js';

const view = { width: 1000, height: 700 };

test('room below: opens under the box', () => {
    const f = fitBelowOrAbove({ top: 100, bottom: 130, left: 50 }, { width: 288, height: 400 }, view);
    assert.equal(f.top, 136); assert.equal(f.left, 50); assert.equal(f.above, false);
});

test('no room below but room above: opens above the box', () => {
    const f = fitBelowOrAbove({ top: 600, bottom: 630, left: 50 }, { width: 288, height: 400 }, view);
    assert.equal(f.above, true); assert.equal(f.top, 600 - 6 - 400);
});

test('no room on either side: moved up so its top and as much as possible show', () => {
    const f = fitBelowOrAbove({ top: 300, bottom: 330, left: 50 }, { width: 288, height: 500 }, view);
    assert.equal(f.top, 700 - 500 - 8);
    assert.ok(f.top >= 8);
});

test('near the right edge: moved left to stay on screen', () => {
    const f = fitBelowOrAbove({ top: 100, bottom: 130, left: 900 }, { width: 288, height: 300 }, view);
    assert.equal(f.left, 1000 - 288 - 8);
});
