// PATH: erp-frontend/e2e/screens.mjs
// fix229: takes a picture of every page, for every rank, at computer and phone size, from the REAL app running on the
// GitHub machine (server with its in-memory demo data + the built pages). Used for the phone pass and the user guide.
// It also writes report.txt: every page error and red console line seen while the pictures were taken.
// Run by .github/workflows/screens.yml. Never touches the live app or its data.
import { chromium } from 'playwright';
import fs from 'node:fs';

const API = process.env.API || 'http://localhost:8080/api/v1';
const WEB = process.env.WEB || 'http://localhost:4173';
const OUT = process.env.OUT || 'screens';
const PW = 'Screens-2026-Ok!';
fs.mkdirSync(OUT, { recursive: true });
const report = [];
const note = (t) => { console.log(t); report.push(t); };

async function call(path, body, token, method = 'POST') {
    const r = await fetch(API + path, {
        method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) },
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await r.text();
    let data; try { data = JSON.parse(text); } catch { data = text; }
    if (!r.ok) throw new Error(method + ' ' + path + ' -> ' + r.status + ' ' + text.slice(0, 300));
    return data;
}
const get = (path, token) => call(path, undefined, token, 'GET');

async function staff(username, role, tokens) {
    let made = null;
    for (const t of tokens) { try { made = await call('/staff/create', { username, email: username.replace('.', '_') + '@ges.test', role }, t); break; } catch (e) { note('create ' + username + ' with a token failed: ' + e.message); } }
    if (!made) throw new Error('could not create ' + username);
    const first = await call('/auth/login', { username, password: made.temporaryPassword });
    return call('/profile/change-password', { oldPassword: made.temporaryPassword, newPassword: PW }, first.token, 'PUT');
}

const firstId = (d, keys = ['id', 'projectId', 'clientId']) => {
    const list = Array.isArray(d) ? d : (d && (d.content || d.items || d.rows || d.clients || d.projects)) || [];
    for (const x of list) for (const k of keys) if (x && x[k]) return x[k];
    return null;
};

(async () => {
    // 1. the people: the Admin (seeded), then a Director, Manager, Secretary and Employee with known keys
    const a0 = await call('/auth/login', { username: 'admin_root', password: 'TestPassword123' });
    const admin = await call('/profile/change-password', { oldPassword: 'TestPassword123', newPassword: PW }, a0.token, 'PUT');
    const director = await staff('test.director', 'ROLE_DIRECTOR', [admin.token]);
    const manager = await staff('test.manager', 'ROLE_MANAGER', [director.token, admin.token]);
    const secretary = await staff('test.secretary', 'ROLE_SECRETARY', [director.token, admin.token]);
    const employee = await staff('test.employee', 'ROLE_EMPLOYEE', [director.token, admin.token]);

    // 2. one project and one client of the demo data
    let projectId = null, clientId = null;
    try { projectId = firstId(await get('/land/ledger?page=0&size=20', director.token)); } catch (e) { note('ledger: ' + e.message); }
    try { clientId = firstId(await get('/recovery/clients/ledger', director.token), ['clientId', 'id']); } catch (e) { note('clients: ' + e.message); }
    note('project ' + projectId + ' | client ' + clientId);

    const PAGES = {
        director: ['dashboard', 'land/new', 'land/projects', projectId && 'folder/' + projectId, projectId && 'folder/' + projectId + '#notes', 'recovery', 'clients', clientId && 'client/' + clientId, 'payments', 'financials', 'reports', 'settings'],
        manager: ['dashboard', 'land/projects', projectId && 'folder/' + projectId, 'recovery', 'clients', 'payments', 'financials', 'reports', 'settings'],
        secretary: ['dashboard', 'land/new', 'land/projects', projectId && 'folder/' + projectId, 'recovery', 'clients', clientId && 'client/' + clientId, 'settings'],
        employee: ['land/new', 'my-entries', 'settings'],
        admin: ['audit', 'settings'],
    };
    const WHO = { director, manager, secretary, employee, admin };
    const SIZES = { pc: { width: 1366, height: 800 }, phone: { width: 390, height: 844 } };

    const browser = await chromium.launch();
    for (const [role, pages] of Object.entries(PAGES)) {
        for (const [size, viewport] of Object.entries(SIZES)) {
            const ctx = await browser.newContext({ viewport, deviceScaleFactor: size === 'phone' ? 2 : 1, isMobile: size === 'phone', hasTouch: size === 'phone' });
            const login = WHO[role];
            await ctx.addInitScript(([t, u]) => {
                try { localStorage.setItem('gs_token', t); localStorage.setItem('gs_user', u); } catch { /* ignore */ }
            }, [login.token, JSON.stringify(login.user)]);
            const page = await ctx.newPage();
            let where = '';
            page.on('pageerror', e => note('[' + role + ' ' + size + ' ' + where + '] PAGE ERROR ' + e.message));
            page.on('console', m => { if (m.type() === 'error') note('[' + role + ' ' + size + ' ' + where + '] console: ' + m.text().slice(0, 300)); });
            for (const p of pages.filter(Boolean)) {
                where = p;
                try {
                    await page.goto(WEB + '/' + p, { waitUntil: 'networkidle', timeout: 45000 });
                    await page.waitForTimeout(1500);
                    const name = role + '-' + size + '-' + p.replace(/[/#]/g, '_').replace(/_[0-9a-f-]{36}/, '') + '.png';
                    await page.screenshot({ path: OUT + '/' + name, fullPage: true });
                    // anything wider than the screen on a phone is a layout fault
                    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
                    if (over > 2) note('[' + role + ' ' + size + ' ' + p + '] page is ' + over + 'px wider than the screen');
                } catch (e) { note('[' + role + ' ' + size + ' ' + p + '] FAILED ' + e.message); }
            }
            await ctx.close();
        }
    }
    // TEMP (midnight-pictures branch only): MIDNIGHT options B and C painted over option A, for David to pick
    const OPTS = {
        A: ':root[data-theme="gesnavy"]{}',
        B: ':root[data-theme="gesnavy"]{--bg-base:#0B0F17;--bg-rgb:11,15,23;--sf-dock:#252E3E;--brand-1:#161C28;--brand-2:#1B2230;--brand-2-rgb:27,34,48;--brand-head:#11161F;--brand-deep:#11161F;--brand-raise-1:#3A4558;--brand-raise-2:#2B3445;--sf-1:#161C28;--sf-2:#1B2230;--sf-head:#11161F;--sf-deep:#11161F;--sf-navy:#1B2230;--sf-raise-1:#3A4558;--sf-raise-2:#2B3445;--sf-readout:#1D2533;--sf-navy-rgb:27,34,48;--scroll-track:#161C28}',
        C: ':root[data-theme="gesnavy"]{--bg-base:#0F1722;--bg-rgb:15,23,34;--sf-dock:#2C3B4E;--brand-1:#1C2838;--brand-2:#22303F;--brand-2-rgb:34,48,63;--brand-head:#16202D;--brand-deep:#16202D;--brand-raise-1:#44586F;--brand-raise-2:#34465C;--sf-1:#1C2838;--sf-2:#22303F;--sf-head:#16202D;--sf-deep:#16202D;--sf-navy:#22303F;--sf-raise-1:#44586F;--sf-raise-2:#34465C;--sf-readout:#243344;--sf-navy-rgb:34,48,63;--scroll-track:#1C2838}',
    };
    for (const [name, css] of Object.entries(OPTS)) {
        const ctx = await browser.newContext({ viewport: SIZES.pc });
        await ctx.addInitScript(([t, u]) => {
            try {
                localStorage.setItem('gs_token', t); localStorage.setItem('gs_user', u);
                localStorage.setItem('goldenseed.prefs.v1.' + JSON.parse(u).username.toLowerCase(), JSON.stringify({ theme: 'gesnavy' }));
            } catch { /* ignore */ }
        }, [director.token, JSON.stringify({ ...director.user, showGuide: false })]);
        const page = await ctx.newPage();
        for (const p of ['dashboard', 'land/projects', projectId && 'folder/' + projectId, 'land/new', 'payments', 'settings'].filter(Boolean)) {
            try {
                await page.goto(WEB + '/' + p, { waitUntil: 'networkidle', timeout: 45000 });
                await page.addStyleTag({ content: css });
                await page.waitForTimeout(1200);
                await page.screenshot({ path: OUT + '/midnight' + name + '-' + p.replace(/[/#]/g, '_').replace(/_[0-9a-f-]{36}/, '') + '.png' });
            } catch (e) { note('[midnight ' + name + ' ' + p + '] FAILED ' + e.message); }
        }
        await ctx.close();
    }
    // fix233: the Director's computer pages once more in each of the other looks (the main pass uses the default, GES DAY)
    for (const theme of ['gesnavy', 'classic']) {
        const ctx = await browser.newContext({ viewport: SIZES.pc });
        await ctx.addInitScript(([t, u, th]) => {
            try {
                localStorage.setItem('gs_token', t); localStorage.setItem('gs_user', u);
                localStorage.setItem('goldenseed.prefs.v1.' + JSON.parse(u).username.toLowerCase(), JSON.stringify({ theme: th }));
            } catch { /* ignore */ }
        }, [director.token, JSON.stringify(director.user), theme]);
        const page = await ctx.newPage();
        for (const p of PAGES.director.filter(Boolean)) {
            try {
                await page.goto(WEB + '/' + p, { waitUntil: 'networkidle', timeout: 45000 });
                await page.waitForTimeout(1200);
                await page.screenshot({ path: OUT + '/theme-' + theme + '-' + p.replace(/[/#]/g, '_').replace(/_[0-9a-f-]{36}/, '') + '.png', fullPage: true });
            } catch (e) { note('[theme ' + theme + ' ' + p + '] FAILED ' + e.message); }
        }
        await ctx.close();
    }
    await browser.close();
    fs.writeFileSync(OUT + '/report.txt', report.join('\n') + '\n');
    console.log('done: ' + fs.readdirSync(OUT).length + ' files');
})().catch(e => { console.error(e); fs.writeFileSync(OUT + '/report.txt', report.join('\n') + '\nFATAL ' + e.stack + '\n'); process.exit(1); });
