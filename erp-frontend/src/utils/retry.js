// PATH: erp-frontend/src/utils/retry.js
// fix210 (David, 15 Oct: "the stages and such options sometimes don't load"). The free server and the free database
// both fall asleep after a few quiet minutes. The first request after that can be slow or fail, and a list that is read
// ONCE when a page opens (document types, stage lists) used to stay empty for good. retrying() asks again a few times,
// waiting a little longer each time. It only retries when the server could not be reached or had a server fault;
// a refusal (wrong rank, bad input) is answered at once and never repeated.

const WAITS_MS = [1500, 3000, 6000];

/** true when asking again could help: no answer at all, a timeout, or a 5xx / 429 from the server */
export function worthRetry(err) {
    if (!err) return false;
    if (err.code === 'ERR_CANCELED') return false;
    const status = err.response && err.response.status;
    if (!status) return true;                      // network down, server asleep, timeout
    return status >= 500 || status === 429 || status === 408;
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

/** Runs fn(); on a failure that is worth retrying, waits and runs it again (up to waits.length more times). */
export async function retrying(fn, waits = WAITS_MS) {
    let lastErr;
    for (let i = 0; i <= waits.length; i++) {
        try {
            return await fn();
        } catch (err) {
            lastErr = err;
            if (i === waits.length || !worthRetry(err)) break;
            await sleep(waits[i]);
        }
    }
    throw lastErr;
}
