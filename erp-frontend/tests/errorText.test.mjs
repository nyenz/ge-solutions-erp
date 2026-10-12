// fix205 (David): no status numbers or code words in front of people
import test from 'node:test';
import assert from 'node:assert/strict';
import { errorText, cleanMessage } from '../src/utils/errorText.js';

const err = (status, message) => ({ response: { status, data: message === undefined ? {} : { message } } });

test('the server sentence is kept, the code and number are not', () => {
    assert.equal(errorText(err(400, 'PLOT_TAKEN: Plot number "214" is already on another project.')), 'Plot number "214" is already on another project.');
    assert.equal(cleanMessage('PLOT_TAKEN: Plot taken. (HTTP 400)'), 'Plot taken.');
    assert.equal(errorText(err(403, 'Rank not authorized for this command.')), 'You do not have permission to do that.');
    assert.equal(errorText(err(500, 'NullPointerException at com.x')), 'The server had a problem, so nothing was saved. Try again in a minute.');
    assert.equal(errorText(err(404)), 'That item could not be found. It may have been removed. Refresh the page.');
    assert.equal(errorText(err(400, 'IDENTIFICATION_FAILED')), 'Wrong username or key.');
    for (const s of [400, 403, 404, 409, 413, 500, 502]) assert.doesNotMatch(errorText(err(s)), /\d{3}|HTTP/);
});
