// PATH: erp-frontend/e2e/guide.mjs
// fix231 (David): records the step-by-step USER GUIDE from the real app (demo data on the GitHub machine): for every
// task, one picture per step plus the box to highlight and the words to show. Writes screens/guide/guide.json and the
// pictures; the app's Guide page (and the shareable guide page) play them. Run after e2e/screens.mjs (it makes the staff).
import { chromium } from 'playwright';
import fs from 'node:fs';

const API = process.env.API || 'http://localhost:8080/api/v1';
const WEB = process.env.WEB || 'http://localhost:5173';
const OUT = (process.env.OUT || 'screens') + '/guide';
const PW = 'Screens-2026-Ok!';
fs.mkdirSync(OUT, { recursive: true });
const log = [];
const note = (t) => { console.log(t); log.push(t); };

const post = async (path, body, token) => {
    const r = await fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(path + ' ' + r.status);
    return r.json();
};
const get = async (path, token) => { const r = await fetch(API + path, { headers: { Authorization: 'Bearer ' + token } }); return r.json(); };
const firstId = (d, keys) => {
    const list = Array.isArray(d) ? d : (d && (d.content || d.items || d.rows)) || [];
    for (const x of list) for (const k of keys) if (x && x[k]) return x[k];
    return null;
};

/* The tasks. Each step: go (a page), click (words of a button/tab to press first), hi (words or a CSS selector of the
   thing to highlight), cap (what to tell the reader). Plain words, one action per step. */
const TASKS = (P, C) => [
    { id: 'start', role: 'All staff', who: 'secretary', title: 'Find your way around', why: 'Where everything is, and how to get help on any button.', steps: [
        { go: 'dashboard', hi: { css: 'header' }, cap: 'The top bar: the menu button on the left, your name and rank, the bell for alerts, and sign out on the right.' },
        { go: 'dashboard', hi: { css: 'aside' }, cap: 'The menu: every page you may open. Your rank decides which pages show.' },
        { go: 'dashboard', hi: { css: 'main section, [class*="hero"], [class*="greet"]' }, cap: 'The Dashboard: today’s work first. Press a box to jump to that list.' },
        { go: 'settings', hi: 'HOVER EXPLAINERS', cap: 'Hold the mouse on any button, tab or column for a short explainer. Turn them FAST or OFF in Settings > Appearance.' },
    ] },
    { id: 'new-project', role: 'Secretary', who: 'secretary', title: 'Register a new project', why: 'Enter a new job: who pays, where the land is, the stages and the money.', steps: [
        { go: 'land/new', hi: 'ENTRY MODE', cap: 'New Project. Pick the project type first. The index number is given by the app.' },
        { go: 'land/new', hi: { css: 'h2:has-text("Clients")' }, cap: 'Clients: the people who pay. Type the NIN first — a person already saved is filled in for you.' },
        { go: 'land/new', hi: 'LOCATION', cap: 'Location: district down to village, and the size in hectares (digits only).' },
        { go: 'land/new', hi: 'STAGES', cap: 'Stages: the steps of the work. The usual list is ready; tick what is already done.' },
        { go: 'land/new', hi: 'FINANCIALS', cap: 'Financials: invoice number, contract number and total cost. Without all three the project is saved as Pending.' },
        { go: 'land/new', hi: 'DOCUMENTS', cap: 'Documents: add scans and choose their type. PDF, photos, Word and Excel are accepted.' },
        { go: 'land/new', hi: 'SAVE', cap: 'Press SAVE. A missing box is marked in red and the page takes you straight to it.' },
    ] },
    { id: 'find', role: 'Secretary', who: 'secretary', title: 'Find a project and open its folder', why: 'Every project lives in its folder: details, stages, money, documents and notes.', steps: [
        { go: 'land/projects', hi: { css: 'input[type="search"], input[placeholder*="Search"]' }, cap: 'Project Ledger: type any part of a name, phone, plot, NIN or index in the search box.' },
        { go: 'land/projects', hi: 'ALL PROJECTS', cap: 'The tabs narrow the list: no title details yet, legacy, receivables, critical, problem, pending.' },
        { go: 'land/projects', hi: { css: 'tbody tr' }, cap: 'Press a row to open that project’s folder.' },
        { go: P, hi: { css: 'header h1, h1' }, cap: 'The folder title: PLOT and its number (or PROJECT and the index). Under it: type, status and what the project is waiting for.' },
        { go: P, hi: { css: 'button:has-text("OVERVIEW"), [role="tab"]:has-text("OVERVIEW")' }, cap: 'The folder tabs: Overview, Financials, People, Documents, Notes.' },
    ] },
    { id: 'stage', role: 'Secretary', who: 'secretary', title: 'Tick a stage and attach its document', why: 'Keep the work up to date; every tick is saved with your name and the date.', steps: [
        { go: P, hi: 'STAGE CHECKLIST', cap: 'On the Overview tab, the Stage checklist shows every step and how many are done.' },
        { go: P, hi: { css: '[class*="statusItem"] input[type="checkbox"], [class*="statusItem"]' }, cap: 'Tick a stage when it is done. It saves the moment you click it.' },
        { go: P, hi: { css: 'button[title*="ttach"], button[aria-label*="ttach"]' }, cap: 'The paperclip attaches that stage’s document (it is filed in Documents under the stage).' },
    ] },
    { id: 'notes', role: 'Secretary', who: 'secretary', title: 'Write a note and set a follow-up', why: 'What happened, what was agreed, what comes next — the office remembers it for you.', steps: [
        { go: P + '#notes', hi: 'NOTES AND HISTORY', cap: 'Notes tab: everything that happened on this project — notes, decisions, money, events and calls.' },
        { go: P + '#notes', hi: 'ADD NOTE', cap: 'Press ADD NOTE. Pick a topic, write the note, and choose a follow-up day if needed.' },
        { go: P + '#notes', click: 'ADD NOTE', hi: 'FOLLOW UP ON (OPTIONAL)', cap: 'On the follow-up day the bell reminds the office. Pin a note to keep it on top (the bell tells the office too).' },
    ] },
    { id: 'call', role: 'Secretary', who: 'secretary', title: 'Log a recovery call', why: 'Call clients who owe; every call is counted and the queue sorts itself.', steps: [
        { go: 'recovery', hi: 'ALL DUE', cap: 'Recovery: the clients to call now. The tabs show who was contacted, missed, needs a site visit or is resting.' },
        { go: 'recovery', hi: { css: 'button:has-text("CALL LOG")' }, cap: 'Open a client and press CALL LOG.' },
        { go: 'recovery', click: { css: 'button:has-text("CALL LOG")' }, hi: { css: 'label:has-text("HISTORY")' }, cap: 'Pick what happened (answered, not picking up ...), add a short note or a promise date, then save. The history is underneath.' },
    ] },
    { id: 'payment', role: 'Manager', who: 'manager', title: 'Record a payment', why: 'Money in: the balance, receipts and reports all follow.', steps: [
        { go: P, click: 'FINANCIALS', hi: 'RECORD PAYMENT', cap: 'Folder > Financials: press RECORD PAYMENT.' },
        { go: P, click: ['FINANCIALS', 'RECORD PAYMENT'], hi: { css: '[class*="modalBody"]' }, cap: 'Enter the amount, how it was paid (Office, Mobile Money, Bank, Other), who paid, and attach the receipt. Then save.' },
        { go: P, click: 'FINANCIALS', hi: 'PAYMENT HISTORY', cap: 'Every payment is listed in Payment History. A mistake is REVERSED (never deleted) and the reason is kept.' },
    ] },
    { id: 'expense', role: 'Manager', who: 'manager', title: 'Log an expense', why: 'Money out of the office, in two taps.', steps: [
        { go: 'financials', hi: 'LOG AN EXPENSE', cap: 'Expenses: tap a category to log money spent. Anything else goes under OTHER.' },
        { go: 'financials', hi: 'RECENT ENTRIES', cap: 'Entries can be corrected for 24 hours. Deleting asks why, and the reason is kept.' },
    ] },
    { id: 'payments', role: 'Manager', who: 'manager', title: 'Check the payments', why: 'See every payment line, find missing receipts.', steps: [
        { go: 'payments', hi: { css: 'input[type="search"]' }, cap: 'Payments: search by project, client, phone, amount or reference.' },
        { go: 'payments', hi: 'PAID WITH', cap: 'Filter by dates, missing receipt, and how it was paid.' },
        { go: 'payments', hi: { css: 'tbody tr' }, cap: 'Press a line to open its project. The receipt button opens the receipt.' },
    ] },
    { id: 'report', role: 'Director', who: 'director', title: 'Run a report and download the PDF', why: 'Numbers for meetings, in the company colours.', steps: [
        { go: 'reports', hi: { css: 'text=/^SCOPE$/' }, cap: 'Reports: pick the data at the top (Projects, Clients, Payments, Expenses, Company) and the period.' },
        { go: 'reports', hi: 'REPORT CATALOGUE', cap: 'Pick a ready report in the catalogue and press Use This Report.' },
        { go: 'reports', click: { css: 'button:has-text("Use This Report")' }, hi: 'PDF -- THE DOCUMENT', cap: 'Choose one or more charts, then download the CSV (for Excel) or the PDF document.' },
    ] },
    { id: 'receivables', role: 'Director', who: 'director', title: 'Receivables and storage fees', why: 'Long-owing projects and the storage fees of kept titles.', steps: [
        { go: 'land/projects', click: 'RECEIVABLES', hi: 'RECEIVABLES', cap: 'Ledger > Receivables: projects owing for a long time. Storage fees grow every 30 days.' },
        { go: P, click: { css: 'button:has-text("FINANCIALS")' }, hi: { css: 'text=/^STORAGE FEES/i' }, cap: 'In a folder, Financials holds the fee buttons: rate, pause, reduce, set aside, waive or add to the cost. Each one asks why.' },
    ] },
    { id: 'staff', role: 'Director', who: 'director', title: 'Staff and settings', why: 'Add staff, reset a key, and set how the app looks for you.', steps: [
        { go: 'settings', click: { css: 'button:has-text("STAFF")' }, hi: { css: 'button:has-text("ADD STAFF")' }, cap: 'Settings > Staff: add a person and give them a rank. They get a temporary key and choose their own at first sign-in.' },
        { go: 'settings', click: { css: 'button:has-text("APPEARANCE")' }, hi: { css: '[class*="panelHeadTitle"]' }, cap: 'Settings > Appearance: theme, size, explainers, animation — saved for you on this device.' },
    ] },
    { id: 'field', role: 'Employee', who: 'employee', title: 'Enter a project from the field', why: 'Field staff enter the land and the people; the office adds the money.', steps: [
        { go: 'land/new', hi: 'ENTRY MODE', cap: 'New Project: enter the type, clients, owners, neighbours, location and stages. No money boxes for field staff.' },
        { go: 'land/new', hi: 'SAVE', cap: 'Press SAVE. The entry waits as Pending until the office adds the invoice, contract and price.' },
        { go: 'my-entries', hi: { css: 'h1' }, cap: 'My Entries: your entries and whether the office has started them.' },
    ] },
];

(async () => {
    const tok = {};
    for (const who of ['director', 'manager', 'secretary', 'employee']) {
        const r = await post('/auth/login', { username: 'test.' + who, password: PW });
        tok[who] = r;
    }
    const projectId = firstId(await get('/land/ledger?page=0&size=20', tok.director.token), ['id', 'projectId']);
    const clientId = firstId(await get('/recovery/clients/ledger', tok.director.token), ['clientId', 'id']);
    const P = 'folder/' + projectId;
    const tasks = TASKS(P, 'client/' + clientId);

    const browser = await chromium.launch();
    const out = { made: new Date().toISOString(), size: { width: 1280, height: 720 }, tasks: [] };
    for (const t of tasks) {
        const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
        const login = tok[t.who];
        await ctx.addInitScript(([tk, u]) => { try { localStorage.setItem('gs_token', tk); localStorage.setItem('gs_user', u); } catch { /* */ } }, [login.token, JSON.stringify(login.user)]);
        const page = await ctx.newPage();
        const steps = [];
        for (let i = 0; i < t.steps.length; i++) {
            const s = t.steps[i];
            try {
                await page.goto(WEB + '/' + s.go, { waitUntil: 'networkidle', timeout: 45000 });
                // the test machine's LOCAL badge is not part of the real app -- keep it out of the guide pictures
                await page.addStyleTag({ content: '[class*="localStrip"]{display:none!important}' });
                await page.waitForTimeout(1200);
                for (const c of [].concat(s.click || [])) {
                    const loc = (typeof c === 'string' ? page.getByText(c, { exact: false }) : page.locator(c.css)).filter({ visible: true }).first();
                    try { await loc.click({ timeout: 4000 }); await page.waitForTimeout(900); } catch { note(t.id + ' step ' + (i + 1) + ': could not press ' + JSON.stringify(c)); }
                }
                let box = null;
                // only something on screen counts (a hidden print copy or a menu word must never be picked)
                const target = (typeof s.hi === 'string' ? page.getByText(s.hi, { exact: false }) : page.locator(s.hi.css)).filter({ visible: true }).first();
                try {
                    await target.scrollIntoViewIfNeeded({ timeout: 4000 });
                    await page.waitForTimeout(400);
                    const b = await target.boundingBox();
                    if (b) box = { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) };
                } catch { note(t.id + ' step ' + (i + 1) + ': nothing to highlight for ' + JSON.stringify(s.hi)); }
                // a word is small: widen the box to its whole row / panel heading
                if (box && box.h < 40) { box = { x: Math.max(0, box.x - 10), y: Math.max(0, box.y - 8), w: box.w + 20, h: box.h + 16 }; }
                const img = t.id + '-' + (i + 1) + '.jpg';
                await page.screenshot({ path: OUT + '/' + img, type: 'jpeg', quality: 72 });
                steps.push({ img, cap: s.cap, box });
            } catch (e) { note(t.id + ' step ' + (i + 1) + ' FAILED ' + e.message); }
        }
        out.tasks.push({ id: t.id, role: t.role, title: t.title, why: t.why, steps });
        await ctx.close();
    }
    await browser.close();
    fs.writeFileSync(OUT + '/guide.json', JSON.stringify(out, null, 1));
    fs.writeFileSync(OUT + '/guide-log.txt', log.join('\n') + '\n');
    console.log('guide: ' + out.tasks.reduce((n, t) => n + t.steps.length, 0) + ' steps');
})().catch(e => { console.error(e); fs.writeFileSync(OUT + '/guide-log.txt', log.join('\n') + '\nFATAL ' + e.stack + '\n'); process.exit(1); });
