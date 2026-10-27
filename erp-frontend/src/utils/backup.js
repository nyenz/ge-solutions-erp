// PATH: erp-frontend/src/utils/backup.js
// fix268 (David): BACKUP TO MY COMPUTER. The server sends one full copy of every table (GET /admin/backup/data); this
// file turns it into the folders the root user keeps on a drive:
//
//   BACKUP 2026-10-28 0130/
//     START HERE.html                     every client, with a search box; click a name to open that client's file
//     CLIENTS/<NAME> (<NIN>)/
//       CLIENT FILE.html                  details, every project, stages, payments, notes and calls (opens in a browser,
//                                         prints like a page)
//       #034A - Plot 412 - Iganga/DOCUMENTS/<the uploaded files>
//     PROJECTS WITHOUT A CLIENT/...       (only when there are such projects)
//     DATABASE/full-copy.json             the whole copy, for restoring
//     DATABASE/READ ME.txt
//
// A joint project is copied into the folder of each of its clients, so every folder is complete on its own.
// Pure functions only (no browser calls), so tests can run them.

/** A backup older than this many days is due (the Settings line and the Dashboard reminder turn orange). */
export const BACKUP_DUE_DAYS = 30;
/** Whole days since a moment (null when there is none). */
export const daysSince = (iso, now = Date.now()) => (iso ? Math.max(0, Math.floor((now - new Date(iso).getTime()) / 864e5)) : null);

// eslint-disable-next-line no-control-regex -- names must not hold control characters
const SAFE = /[\\/:*?"<>|\u0000-\u001f]+/g;
/** A name that every computer accepts as a folder or file name. */
export const safeName = (s, max = 80) => {
    let t = String(s ?? '').replace(SAFE, ' ').replace(/\s+/g, ' ').trim();
    if (t.length > max) {
        const dot = t.lastIndexOf('.');
        const ext = dot > 0 && t.length - dot <= 8 ? t.slice(dot) : '';
        t = t.slice(0, max - ext.length).trim() + ext;
    }
    t = t.replace(/[. ]+$/, '');
    return t || 'UNNAMED';
};

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = (v) => { const n = Number(v); return Number.isFinite(n) ? n : 0; };
const money = (v) => 'UGX ' + Math.round(num(v)).toLocaleString('en-US');
const day = (v) => (v ? String(v).slice(0, 10) : '');
const when = (v) => (v ? String(v).replace('T', ' ').slice(0, 16) : '');
const truthy = (v) => v === true || v === 1 || v === 'true' || v === 't';
const pad = (n) => String(n).padStart(2, '0');
/** A link to a path: every part encoded (names hold # and spaces). */
const href = (path) => path.split('/').map(encodeURIComponent).join('/');

/** "BACKUP 2026-10-28 0130" for a moment in time. */
export const backupFolderName = (d = new Date()) =>
    `BACKUP ${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}${pad(d.getMinutes())}`;

const groupBy = (rows, key) => {
    const m = new Map();
    for (const r of rows || []) { const k = r[key]; if (k == null) continue; if (!m.has(k)) m.set(k, []); m.get(k).push(r); }
    return m;
};

const PAGE_CSS = `*{box-sizing:border-box}body{margin:0;background:#F4EFE6;color:#0B2250;font:14px/1.5 "Segoe UI",Roboto,Arial,sans-serif}
a{color:#C9550A;text-decoration:none;font-weight:700}a:hover{color:#F26A0D}
.wrap{max-width:1000px;margin:0 auto;padding:24px 16px 60px}
.top{background:#FFFFFC;border-left:6px solid #F26A0D;border-radius:0 12px 12px 0;padding:18px 22px;box-shadow:0 6px 18px rgba(17,47,102,.12);margin-bottom:18px}
h1{margin:0;font-size:24px;letter-spacing:1.5px;text-transform:uppercase;color:#112F66}
.sub{margin-top:4px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;color:#5B6B8C}
.card{background:#FFFFFC;border:1px solid rgba(17,47,102,.14);border-radius:12px;margin-bottom:16px;overflow:hidden;break-inside:avoid}
.head{background:#112F66;color:#F58232;padding:10px 18px;font-weight:800;font-size:12px;letter-spacing:2px;text-transform:uppercase}
.body{padding:14px 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px 18px}
.item{border-left:2px solid #F26A0D;padding-left:12px}
.lbl{font-size:10px;font-weight:900;letter-spacing:1.5px;text-transform:uppercase;color:#5B6B8C}
.val{font-family:Consolas,"Courier New",monospace;font-weight:700;color:#0B2250;overflow-wrap:anywhere}
.grp{font-size:11px;font-weight:900;letter-spacing:2px;color:#C9550A;margin:14px 0 8px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-size:10px;letter-spacing:1.4px;text-transform:uppercase;color:#5B6B8C;padding:6px 8px;border-bottom:1px solid rgba(17,47,102,.2)}
td{padding:7px 8px;border-bottom:1px solid rgba(17,47,102,.08);vertical-align:top}
tr:nth-child(even) td{background:#F1EFE9}
.r{text-align:right;white-space:nowrap}.mono{font-family:Consolas,"Courier New",monospace}
.tag{display:inline-block;padding:1px 7px;border-radius:5px;font-size:10px;font-weight:900;letter-spacing:1px;background:#E4E3DD;color:#3E4A63}
.tag.red{background:#FDE2E2;color:#7F1D1D}.tag.green{background:#DCF5EA;color:#065F46}
.done{color:#065F46;font-weight:800}.todo{color:#5B6B8C}
.muted{color:#5B6B8C}.proj{border-top:3px solid #F26A0D}
.search{width:100%;height:44px;border:1px solid rgba(17,47,102,.25);border-radius:8px;padding:0 14px;font-size:15px;margin-bottom:14px;background:#fff;color:#0B2250}
.search:focus{outline:none;border-color:#F26A0D;box-shadow:0 0 0 3px rgba(242,106,13,.16)}
.list a{display:grid;grid-template-columns:2fr 1.2fr 1fr .8fr;gap:12px;padding:11px 16px;border-bottom:1px solid rgba(17,47,102,.08);color:#0B2250;font-weight:600}
.list a:nth-child(even){background:#F1EFE9}.list a:hover{background:#FDEBD7}
.list b{color:#112F66}
@media(max-width:640px){.list a{grid-template-columns:1fr}}
@media print{body{background:#fff}.top,.card{box-shadow:none}.search{display:none}a{color:#0B2250}}`;

const page = (title, inner) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><style>${PAGE_CSS}</style></head><body><div class="wrap">${inner}</div></body></html>`;

const item = (label, value) => (value === null || value === undefined || value === '' ? '' :
    `<div class="item"><div class="lbl">${esc(label)}</div><div class="val">${esc(value)}</div></div>`);

/**
 * Builds the list of files. Each entry is { path, text } (written as it is) or { path, doc: { filePath, fileName } }
 * (the page fetches that stored file). Paths use "/" and start inside the backup folder.
 */
export function buildBackup(data, now = new Date()) {
    const T = (data && data.tables) || {};
    const clients = T.clients || [];
    const projects = T.land_projects || [];
    const titles = new Map((T.land_titles || []).map(t => [t.id, t]));
    const clientsOf = groupBy(T.project_clients, 'project_id');
    const ownersOf = groupBy(T.project_proprietors, 'project_id');
    const projectsOfClient = new Map();
    for (const l of [...(T.project_clients || []), ...(T.project_proprietors || [])]) {
        if (!projectsOfClient.has(l.client_id)) projectsOfClient.set(l.client_id, new Set());
        projectsOfClient.get(l.client_id).add(l.project_id);
    }
    const clientById = new Map(clients.map(c => [c.id, c]));
    const stages = groupBy(T.project_statuses, 'project_id');
    const pays = groupBy(T.payment_records, 'project_id');
    const docs = groupBy(T.project_documents, 'project_id');
    const timeline = groupBy(T.project_timeline, 'project_id');
    const follow = groupBy(T.follow_up_logs, 'project_id');
    const followByClient = groupBy((T.follow_up_logs || []).filter(f => !f.project_id), 'client_id');
    const recovery = groupBy(T.recovery_notes, 'client_id');
    const neighbors = groupBy(T.project_neighbors, 'project_id');
    const projById = new Map(projects.map(p => [p.id, p]));

    const files = [];
    const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;   // local time, like the folder name
    const used = new Set();
    const unique = (path) => {   // two clients with the same name, two files with the same name
        let p = path; let n = 2;
        const dot = path.lastIndexOf('.'); const slash = path.lastIndexOf('/');
        const base = dot > slash ? path.slice(0, dot) : path; const ext = dot > slash ? path.slice(dot) : '';
        while (used.has(p.toLowerCase())) p = `${base} (${n++})${ext}`;
        used.add(p.toLowerCase());
        return p;
    };

    const projectLabel = (p) => {
        const t = titles.get(p.title_id) || {};
        return safeName(['#' + (p.project_index || '---'), t.plot_number ? 'Plot ' + t.plot_number : '', p.district || '',
            truthy(p.deleted) ? 'DELETED' : truthy(p.pending) ? 'PENDING' : ''].filter(Boolean).join(' - '));
    };

    /** One project's part of a client file, plus its documents copied under folder. */
    const projectSection = (p, folder, base) => {
        const t = titles.get(p.title_id) || {};
        const owed = num(p.total_cost) - num(p.amount_paid);
        const people = (ids) => (ids || []).map(l => clientById.get(l.client_id)).filter(Boolean).map(c => esc(c.full_name)).join(', ');
        const st = (stages.get(p.id) || []).slice().sort((a, b) => num(a.display_order) - num(b.display_order));
        const pr = (pays.get(p.id) || []).slice().sort((a, b) => String(a.paid_on || a.timestamp).localeCompare(String(b.paid_on || b.timestamp)));
        const nb = neighbors.get(p.id) || [];
        const notes = [...(timeline.get(p.id) || []).map(n => ({ at: n.created_at, by: n.recorded_by, what: [n.title, n.reason, n.detail].filter(Boolean).join(' - ') })),
            ...(follow.get(p.id) || []).map(n => ({ at: n.timestamp, by: n.recorded_by, what: (n.topic ? n.topic + ': ' : '') + (n.notes || '') }))]
            .sort((a, b) => String(b.at).localeCompare(String(a.at)));
        const dl = (docs.get(p.id) || []).map(d => {
            const path = unique(`${folder}/DOCUMENTS/${safeName((d.category ? d.category + ' - ' : '') + (d.file_name || 'document'))}`);
            files.push({ path, doc: { filePath: d.file_path, fileName: d.file_name } });
            return { d, path };
        });
        const status = truthy(p.deleted) ? '<span class="tag red">DELETED</span>' : truthy(p.pending) ? '<span class="tag">PENDING</span>'
            : `<span class="tag ${truthy(p.is_problem) ? 'red' : 'green'}">${esc(p.status || 'ACTIVE')}</span>`;
        return { label: projectLabel(p), dl, html: `<div class="card proj"><div class="head">PROJECT #${esc(p.project_index || '---')} ${status}</div><div class="body">
<div class="grp">LOCATION</div><div class="grid">${item('District', p.district)}${item('County', p.county)}${item('Sub-county', p.sub_county)}${item('Parish', p.parish)}${item('Village', p.village)}${item('Area', p.area)}${item('Start date', day(p.project_start_date))}${item('Type', String(p.project_type || '').replace(/_/g, ' '))}</div>
${t.id ? `<div class="grp">TITLE</div><div class="grid">${item('Plot', t.plot_number)}${item('Block', t.block_road)}${item('Tenure', t.tenure)}${item('Area (ha)', t.area_hectares)}${item('Volume', t.volume)}${item('Folio', t.folio)}${item('Title date', day(t.title_issue_date))}${truthy(t.is_released) ? item('Handed over', day(t.released_at)) : ''}</div>` : ''}
<div class="grp">MONEY</div><div class="grid">${item('Total cost', money(p.total_cost))}${item('Paid', money(p.amount_paid))}${item('Owed', money(owed))}${num(p.storage_fees_accumulated) ? item('Storage fees', money(p.storage_fees_accumulated)) : ''}${item('Invoice', p.invoice_number)}${item('Contract', p.contract_number)}</div>
<div class="grp">PEOPLE</div><div class="grid">${item('Clients', people(clientsOf.get(p.id)))}${item('Owners', people(ownersOf.get(p.id)))}</div>
${nb.length ? `<div class="grp">NEIGHBORS</div><table><tr><th>Name</th><th>Side</th><th>Phone</th></tr>${nb.map(n => `<tr><td>${esc(n.full_name)}</td><td>${esc(n.side)}</td><td class="mono">${esc(n.phone)}</td></tr>`).join('')}</table>` : ''}
${st.length ? `<div class="grp">STAGES</div><table><tr><th>Stage</th><th>Done</th></tr>${st.map(s => `<tr><td>${esc(s.status_name)}</td><td class="${truthy(s.is_completed) ? 'done' : 'todo'}">${truthy(s.is_completed) ? 'Done ' + esc(day(s.completed_at)) + (s.completed_by ? ' by ' + esc(s.completed_by) : '') : 'Not yet'}</td></tr>`).join('')}</table>` : ''}
${pr.length ? `<div class="grp">PAYMENTS</div><table><tr><th>Date</th><th class="r">Amount</th><th>Paid by</th><th>How</th><th>Recorded by</th></tr>${pr.map(x => `<tr><td class="mono">${esc(day(x.paid_on || x.timestamp))}</td><td class="r mono">${esc(money(x.amount_paid))}</td><td>${esc(x.payer_name || '')}</td><td>${esc([String(x.payment_method || '').replace(/_/g, ' '), x.payment_reference].filter(Boolean).join(' - '))}${x.payment_type && x.payment_type !== 'STANDARD' ? ' <span class="tag">' + esc(String(x.payment_type).replace(/_/g, ' ')) + '</span>' : ''}</td><td>${esc(x.recorded_by)}</td></tr>`).join('')}</table>` : ''}
${dl.length ? `<div class="grp">DOCUMENTS</div><table><tr><th>File</th><th>Type</th><th>Added</th></tr>${dl.map(({ d, path }) => `<tr><td><a href="${esc(href(path.slice(base.length + 1)))}">${esc(d.file_name)}</a></td><td>${esc(d.category || '')}</td><td class="mono">${esc(day(d.uploaded_at))}</td></tr>`).join('')}</table>` : ''}
${notes.length ? `<div class="grp">NOTES AND HISTORY</div><table><tr><th>When</th><th>By</th><th>What</th></tr>${notes.map(n => `<tr><td class="mono">${esc(when(n.at))}</td><td>${esc(n.by || '')}</td><td>${esc(n.what)}</td></tr>`).join('')}</table>` : ''}
${p.problem_note ? `<div class="grp">PROBLEM</div><div>${esc(p.problem_note)}</div>` : ''}${p.deleted_reason ? `<div class="grp">DELETED BECAUSE</div><div>${esc(p.deleted_reason)}</div>` : ''}
</div></div>` };
    };

    const index = [];
    for (const c of clients.slice().sort((a, b) => String(a.full_name).localeCompare(String(b.full_name)))) {
        const folder = unique(`CLIENTS/${safeName(`${c.full_name || 'NO NAME'}${c.national_id ? ' (' + c.national_id + ')' : ''}`)}`);
        const mine = [...(projectsOfClient.get(c.id) || [])].map(id => projById.get(id)).filter(Boolean)
            .sort((a, b) => String(a.project_index).localeCompare(String(b.project_index)));
        const parts = mine.map(p => projectSection(p, `${folder}/${projectLabel(p)}`, folder));
        const calls = [...(recovery.get(c.id) || []).map(n => ({ at: n.created_at, what: [n.tag, n.text, n.promise_date ? 'Promised for ' + day(n.promise_date) : ''].filter(Boolean).join(' - ') })),
            ...(followByClient.get(c.id) || []).map(n => ({ at: n.timestamp, what: (n.topic ? n.topic + ': ' : '') + (n.notes || '') + (n.recorded_by ? ' (' + n.recorded_by + ')' : '') }))]
            .sort((a, b) => String(b.at).localeCompare(String(a.at)));
        const owed = mine.filter(p => !truthy(p.deleted)).reduce((s, p) => s + num(p.total_cost) - num(p.amount_paid), 0);
        const paid = mine.filter(p => !truthy(p.deleted)).reduce((s, p) => s + num(p.amount_paid), 0);
        files.push({ path: `${folder}/CLIENT FILE.html`, text: page(c.full_name || 'Client', `<div class="top"><h1>${esc(c.full_name)}</h1><div class="sub">Client file - backup of ${esc(stamp)} - <a href="../../START%20HERE.html">all clients</a></div></div>
<div class="card"><div class="head">IDENTITY</div><div class="body"><div class="grid">${item('Full name', c.full_name)}${item('NIN', c.national_id)}${item('Phone', c.phone_number)}${item('Email', c.email)}${item('Address', c.home_address)}${item('Last contact', day(c.last_contacted_at))}${item('Projects', String(mine.length))}${item('Total paid', money(paid))}${item('Total owed', money(owed))}</div></div></div>
${parts.map(x => x.html).join('\n')}
${calls.length ? `<div class="card"><div class="head">CALL LOG AND RECOVERY NOTES</div><div class="body"><table><tr><th>When</th><th>What</th></tr>${calls.map(n => `<tr><td class="mono">${esc(when(n.at))}</td><td>${esc(n.what)}</td></tr>`).join('')}</table></div></div>` : ''}`) });
        index.push({ name: c.full_name || 'NO NAME', nin: c.national_id || '', phone: c.phone_number || '', projects: mine.length, href: `${folder}/CLIENT FILE.html` });
    }

    // projects nobody is linked to still get a folder
    const linked = new Set([...projectsOfClient.values()].flatMap(s => [...s]));
    const orphans = projects.filter(p => !linked.has(p.id));
    if (orphans.length) {
        const parts = orphans.map(p => projectSection(p, `PROJECTS WITHOUT A CLIENT/${projectLabel(p)}`, 'PROJECTS WITHOUT A CLIENT'));
        const html = page('Projects without a client', `<div class="top"><h1>Projects without a client</h1><div class="sub">Backup of ${esc(stamp)} - <a href="../START%20HERE.html">all clients</a></div></div>${parts.map(x => x.html).join('\n')}`);
        files.push({ path: 'PROJECTS WITHOUT A CLIENT/PROJECTS.html', text: html });
    }

    const docCount = files.filter(f => f.doc).length;
    files.unshift({ path: 'START HERE.html', text: page('Backup - all clients', `<div class="top"><h1>GE Solutions backup</h1><div class="sub">Made ${esc(stamp)} by ${esc(data?.createdBy || '')} - ${index.length} clients - ${projects.length} projects - ${docCount} documents</div></div>
<input class="search" id="q" placeholder="Search a name, NIN or phone" autocomplete="off">
<div class="card"><div class="head">CLIENTS</div><div class="list" id="list">${index.map(i => `<a href="${esc(href(i.href))}" data-k="${esc((i.name + ' ' + i.nin + ' ' + i.phone).toLowerCase())}"><b>${esc(i.name)}</b><span class="mono">${esc(i.nin)}</span><span class="mono">${esc(i.phone)}</span><span>${i.projects} project${i.projects === 1 ? '' : 's'}</span></a>`).join('')}</div></div>
${orphans.length ? '<p><a href="PROJECTS%20WITHOUT%20A%20CLIENT/PROJECTS.html">Projects without a client (' + orphans.length + ')</a></p>' : ''}
<p class="muted">Each client folder holds CLIENT FILE.html (open it in any browser, it prints like a page) and a folder per project with its documents. DATABASE holds the full copy for restoring.</p>
<script>var q=document.getElementById('q');q.addEventListener('input',function(){var v=q.value.toLowerCase().trim();document.querySelectorAll('#list a').forEach(function(a){a.style.display=!v||a.getAttribute('data-k').indexOf(v)>-1?'':'none'})});</script>`) });
    files.push({ path: 'DATABASE/full-copy.json', text: JSON.stringify(data) });
    files.push({ path: 'DATABASE/READ ME.txt', text: `GE Solutions backup made ${stamp}.\r\n\r\nfull-copy.json is the whole database at that moment (every table), for restoring.\r\nKeys (passwords) are not in it: after a restore every person gets a new key.\r\nKeep this drive somewhere safe: it holds every client's details.\r\n` });
    return { files, clients: index.length, projects: projects.length, documents: docCount };
}
