// PATH: erp-frontend/tests/retry.test.mjs (fix210)
import test from 'node:test';
import assert from 'node:assert/strict';
import { retrying, worthRetry } from '../src/utils/retry.js';

test('asks again while the server cannot be reached, then succeeds', async () => {
    let n = 0;
    const out = await retrying(async () => { n++; if (n < 3) throw { message: 'Network Error' }; return 'ok'; }, [1, 1, 1]);
    assert.equal(out, 'ok');
    assert.equal(n, 3);
});

test('a refusal is not repeated', async () => {
    let n = 0;
    await assert.rejects(retrying(async () => { n++; throw { response: { status: 403 } }; }, [1, 1, 1]));
    assert.equal(n, 1);
});

test('gives up after the last wait', async () => {
    let n = 0;
    await assert.rejects(retrying(async () => { n++; throw { response: { status: 502 } }; }, [1, 1]));
    assert.equal(n, 3);
});

test('which failures are worth another try', () => {
    assert.equal(worthRetry({ message: 'timeout' }), true);
    assert.equal(worthRetry({ response: { status: 503 } }), true);
    assert.equal(worthRetry({ response: { status: 400 } }), false);
    assert.equal(worthRetry({ code: 'ERR_CANCELED' }), false);
});
