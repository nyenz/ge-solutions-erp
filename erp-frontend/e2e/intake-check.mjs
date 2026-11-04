// PATH: erp-frontend/e2e/intake-check.mjs
// fix287 (David, 4 Nov 2026): a real click test of New Project on the demo app (GitHub machine). It makes mistakes on
// purpose, fills a legacy-style entry with the MISSING ticks, saves with SAVE + DUPLICATE, follows the Ledger and back,
// and tries a number that is already used. One picture per step in screens/intake-check/, and check.txt says PASS/FAIL.
// Run after e2e/screens.mjs (it makes the staff accounts).
import { chromium } from 'playwright';
import fs from 'node:fs';

const API = process.env.API || 'http://localhost:8080/api/v1';
const WEB = process.env.WEB || 'http://localhost:5173';
const OUT = (process.env.OUT || 'screens') + '/intake-check';
const PW = 'Screens-2026-Ok!';
fs.mkdirSync(OUT, { recursive: true });
const lines = [];
const say = (t) => { console.log(t); lines.push(t); };
const check = (ok, what) => say((ok ? 'PASS  ' : 'FAIL  ') + what);

const post = async (path, body, token) => {
    const r = await fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(path + ' ' + r.status);
    return r.json();
};

// a tiny real PNG (1 x 1 pixel) as the scan
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
const SCAN = OUT + '/scan.png';
fs.writeFileSync(SCAN, PNG);

(async () => {
    const login = await post('/auth/login', { username: 'test.director', password: PW });
    try { await post('/profile/guide-seen', {}, login.token); } catch { /* older server */ }
    if (login.user) login.user.showGuide = false;

    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
    await ctx.addInitScript(([tk, u]) => { try { localStorage.setItem('gs_token', tk); localStorage.setItem('gs_user', u); } catch { /* */ } }, [login.token, JSON.stringify(login.user)]);
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(String(e.message || e)));
    let n = 0;
    const shot = async (name, full = false) => { n += 1; await page.waitForTimeout(500); await page.screenshot({ path: `${OUT}/${String(n).padStart(2, '0')}-${name}.png`, fullPage: full }); };
    const top = async () => { await page.waitForTimeout(600); await page.evaluate(() => { window.scrollTo(0, 0); document.querySelectorAll('[class*="scrollArea"], [class*="mainContent"]').forEach(el => el.scrollTo(0, 0)); }); await page.waitForTimeout(400); };
    const byLabel = (text) => page.locator(`xpath=//label[normalize-space()="${text}"]/following::input[1]`).first();
    const fillLabel = async (text, value) => { const el = byLabel(text); await el.click(); await el.fill(value); await page.keyboard.press('Escape'); };
    const addScan = async () => {
        await page.locator('input[type="file"]').first().setInputFiles(SCAN);
        await page.getByRole('combobox', { name: 'Category for all files' }).click();
        await page.getByRole('option').first().click();
        await page.getByRole('button', { name: 'ADD', exact: true }).click();
        await page.waitForTimeout(400);
    };
    const value = async (aria) => page.locator(`[aria-label="${aria}"]`).first().inputValue().catch(() => '');

    try {
        // 1. the empty form, then SAVE with nothing in it
        await page.goto(WEB + '/land/new');
        await page.waitForSelector('text=New Project', { timeout: 30000 });
        await page.getByRole('radio', { name: /Fresh Survey/ }).click();
        await shot('empty-form');
        await page.getByRole('button', { name: /Save Project/ }).click();
        await page.waitForTimeout(800);
        await top();
        const box = page.locator('[role="alert"]').filter({ hasText: 'NOT SAVED' }).first();
        const many = await box.locator('li').count().catch(() => 0);
        check(many >= 5, 'SAVE on an empty form lists every problem at once (' + many + ' lines)');
        await shot('all-problems-listed');

        // 2. fill the client with NIN missing, and the place: the list gets shorter by itself
        await page.getByLabel('NIN missing for client 1').check();
        await page.getByLabel('Full name of client 1').fill('Test Legacy Person');
        await page.keyboard.press('Escape');
        await page.getByLabel('Phone of client 1').fill('0772405913');
        await page.keyboard.press('Escape');
        check((await value('NIN of client 1')) === 'TESTLEGACYPERSON', 'NIN missing gives the name in capitals with no spaces');
        await fillLabel('District', 'KAMULI');
        await fillLabel('County', 'BUGABULA');
        await fillLabel('Sub-county', 'NAMWENDWA');
        await fillLabel('Parish', 'BUKONTE');
        await fillLabel('Village', 'KASAMBIRA');
        await top();
        const fewer = await box.locator('li').count().catch(() => 0);
        check(fewer < many, 'the red list shrinks while the boxes are fixed (' + many + ' -> ' + fewer + ')');
        await shot('list-shrinks');

        // 3. the numbers: invoice missing + paper number 7, contract missing, price typed with commas showing
        await page.getByLabel('Invoice number missing').check();
        await page.getByLabel('Old paper number').fill('7');
        await page.getByLabel('Contract number missing').check();
        const cost = page.getByLabel('Total Cost');
        await cost.click(); await cost.press('Control+A'); await cost.pressSequentially('1500000');
        await page.waitForTimeout(500);
        check((await value('Invoice Number')) === 'KAM-NAM-0007', 'invoice number made from the place: ' + (await value('Invoice Number')));
        check((await value('Contract Number')) === 'KAM-NAM-0007', 'contract number copies the invoice number');
        check((await cost.inputValue()) === '1,500,000', 'price shows commas while typing: ' + (await cost.inputValue()));
        await page.locator('[aria-label="Invoice Number"]').first().scrollIntoViewIfNeeded();
        await shot('numbers-and-commas');
        await top();
        await shot('missing-strip-on');

        // 4. the document, then SAVE + DUPLICATE: the Ledger shows it, then the form comes back for the next plot
        await addScan();
        await page.getByRole('button', { name: /Save \+ Duplicate/ }).click();
        await page.waitForURL(/land\/projects/, { timeout: 20000 });
        await page.waitForTimeout(1200);
        check(await page.locator('text=Back to New Project').count() > 0, 'the Ledger says it goes back to New Project');
        await shot('ledger-shows-it');
        await page.waitForURL(/land\/new/, { timeout: 15000 });
        await page.waitForTimeout(1500);
        await top();
        check(await page.locator('text=Ready for the next plot').count() > 0, 'back on the form with the green "Ready for the next plot" box');
        check((await page.getByLabel('NIN missing for client 1').isChecked().catch(() => false)), 'NIN missing is still ticked');
        check((await page.getByLabel('Invoice number missing').isChecked().catch(() => false)), 'Invoice number missing is still ticked');
        check((await byLabel('District').inputValue()) === 'KAMULI', 'the place is kept');
        check(await page.locator('text=CLICK TO UPLOAD').count() > 0, 'the documents are empty for the next plot');
        const focused = await page.evaluate(() => document.activeElement && document.activeElement.getAttribute('aria-label'));
        check(focused === 'Total Cost', 'the cursor goes to the first box that must change (no title on this type, prices not kept): ' + focused);
        check(await page.getByRole('button', { name: 'Location', exact: true }).count() > 0, 'KEEP FOR NEXT offers Location');
        await top();
        await shot('back-ready-for-next');
        const nextInv = await value('Invoice Number');
        check(nextInv === 'KAM-NAM-0008', 'empty paper number takes the next free one: ' + nextInv);

        // 5. a number that is already used: the server refuses, the red box says so and offers the project
        await page.getByLabel('Old paper number').fill('7');
        const cost2 = page.getByLabel('Total Cost');
        await cost2.click(); await cost2.press('Control+A'); await cost2.pressSequentially('900000');
        await addScan();
        await page.getByRole('button', { name: /Save Project/ }).click();
        await page.waitForTimeout(2500);
        await top();
        const refused = page.locator('[role="alert"]').filter({ hasText: 'NOT SAVED' }).first();
        check(await refused.count() > 0, 'a used invoice number is refused and shown in the red box');
        check(await page.locator('button:has-text("FIND PROJECT")').count() > 0, 'the red box offers FIND PROJECT');
        check(/land\/new/.test(page.url()), 'the form stays open (nothing cleared)');
        await shot('server-refused');

        // 6. SAVE (single) after the fix, pressed twice fast: saved once, always the Ledger, the new row lit up
        await page.getByLabel('Old paper number').fill('');
        await page.waitForTimeout(800);
        const btn = page.getByRole('button', { name: /Save Project/ });
        await btn.click(); await btn.click({ force: true }).catch(() => {});
        await page.waitForURL(/land\/projects\?new=/, { timeout: 20000 });
        await page.waitForTimeout(2000);
        check(await page.locator('[class*="rowNew"]').count() > 0, 'SAVE goes to the Ledger with the new row lit up');
        await shot('save-goes-to-ledger');
    } catch (e) {
        say('FAIL  the test stopped: ' + (e && e.message ? e.message.split('\n')[0] : e));
        try { await shot('where-it-stopped', true); } catch { /* */ }
    }
    if (errors.length) say('PAGE ERRORS: ' + errors.join(' | ')); else say('PASS  no page errors');
    fs.writeFileSync(OUT + '/check.txt', lines.join('\n') + '\n');
    await browser.close();
})();
