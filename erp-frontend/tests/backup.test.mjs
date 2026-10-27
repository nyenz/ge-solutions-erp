// fix268: the backup turns the server's copy into a folder per client, with working links
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildBackup, safeName, backupFolderName, daysSince } from '../src/utils/backup.js';

const data = { createdBy: 'admin_root', tables: {
    clients: [{ id: 'c1', full_name: 'Kamya John', national_id: 'CM1', phone_number: '0772' }, { id: 'c2', full_name: 'Nakato/Mary', national_id: 'CM2' }],
    land_projects: [{ id: 'p1', project_index: '034A', district: 'Iganga', title_id: 't1', total_cost: '1000', amount_paid: '400' },
        { id: 'p2', project_index: '040A', district: 'Jinja', total_cost: '0', amount_paid: '0' }],
    land_titles: [{ id: 't1', plot_number: '412' }],
    project_clients: [{ project_id: 'p1', client_id: 'c1' }, { project_id: 'p1', client_id: 'c2' }],
    project_proprietors: [],
    project_documents: [{ project_id: 'p1', file_name: 'deed.pdf', category: 'TITLE', file_path: 'https://x/deed.pdf' }],
    payment_records: [{ project_id: 'p1', amount_paid: '400', payer_name: 'Kamya John', paid_on: '2026-10-01T00:00' }],
} };

test('a folder per client, documents copied into each joint client folder', () => {
    const b = buildBackup(data, new Date(2026, 9, 28, 1, 30));
    const paths = b.files.map(f => f.path);
    assert.equal(b.clients, 2);
    assert.ok(paths.includes('START HERE.html'));
    assert.ok(paths.includes('CLIENTS/Kamya John (CM1)/CLIENT FILE.html'));
    assert.ok(paths.includes('CLIENTS/Nakato Mary (CM2)/CLIENT FILE.html'), 'a slash never makes a sub-folder');
    const docs = b.files.filter(f => f.doc);
    assert.equal(docs.length, 2, 'the joint project is complete in both folders');
    assert.equal(docs[0].path, 'CLIENTS/Kamya John (CM1)/#034A - Plot 412 - Iganga/DOCUMENTS/TITLE - deed.pdf');
    assert.ok(paths.includes('PROJECTS WITHOUT A CLIENT/PROJECTS.html'));
    assert.ok(paths.includes('DATABASE/full-copy.json'));
    const page = b.files.find(f => f.path === 'CLIENTS/Kamya John (CM1)/CLIENT FILE.html').text;
    assert.ok(page.includes('href="%23034A%20-%20Plot%20412%20-%20Iganga/DOCUMENTS/TITLE%20-%20deed.pdf"'), 'the link opens the copied file');
    assert.ok(page.includes('UGX 600'), 'what is owed');
    assert.ok(!/text-decoration:\s*underline/.test(page));
});

test('names and dates', () => {
    assert.equal(safeName('a:b*c?'), 'a b c');
    assert.equal(safeName('  '), 'UNNAMED');
    assert.equal(safeName('end. '), 'end');
    assert.equal(backupFolderName(new Date(2026, 9, 28, 1, 5)), 'BACKUP 2026-10-28 0105');
    assert.equal(daysSince(null), null);
    assert.equal(daysSince('2026-10-01T00:00:00Z', Date.parse('2026-10-31T01:00:00Z')), 30);
});
