// PATH: erp-frontend/src/pages/settings/BackupPanel.jsx
// fix268 (David): BACKUP TO MY COMPUTER (root only). Two ways, the same folders:
//  - STRAIGHT INTO A FOLDER: the browser asks once for a folder (for example on the external hard drive) and the
//    client folders are written there, ready to open. Chrome or Edge on a computer.
//  - ONE ZIP FILE: works everywhere (phones too); one file downloads, unzip it only to look inside.
// What goes in the folders: utils/backup.js. Every saved backup is written to the audit trail, and the time feeds the
// "last backup" line here and the monthly reminder on the Dashboard.
import React, { useEffect, useState } from 'react';
import { zipSync, strToU8 } from 'fflate';
import { FiDownload, FiFolder, FiArchive, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi';
import settingsService from '../../services/settingsService';
import { buildBackup, backupFolderName, daysSince, BACKUP_DUE_DAYS } from '../../utils/backup';
import { fetchDocBytes } from '../../utils/docFile';
import styles from './BackupPanel.module.css';

const canPickFolder = () => typeof window !== 'undefined' && typeof window.showDirectoryPicker === 'function';

/** Writes bytes at "a/b/c.txt" under a folder the person picked. */
async function writeInto(dir, path, bytes) {
    const parts = path.split('/');
    let d = dir;
    for (const p of parts.slice(0, -1)) d = await d.getDirectoryHandle(p, { create: true });
    const fh = await d.getFileHandle(parts[parts.length - 1], { create: true });
    const w = await fh.createWritable();
    await w.write(bytes);
    await w.close();
}

export default function BackupPanel() {
    const [mode, setMode] = useState(canPickFolder() ? 'folder' : 'zip');
    const [last, setLast] = useState(undefined);   // undefined = loading, null = never
    const [busy, setBusy] = useState(false);
    const [step, setStep] = useState('');
    const [done, setDone] = useState(0);
    const [total, setTotal] = useState(0);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        let alive = true;
        settingsService.backupStatus().then(r => { if (alive) setLast(r?.lastBackupAt || null); }).catch(() => { if (alive) setLast(null); });
        return () => { alive = false; };
    }, []);

    const run = async () => {
        setError(''); setResult(null);
        let dir = null;
        if (mode === 'folder') {
            // asked first, while the click still counts as the person's own action
            try { dir = await window.showDirectoryPicker({ id: 'ges-backup', mode: 'readwrite', startIn: 'documents' }); }
            catch (e) { if (e?.name !== 'AbortError') setError('That folder could not be opened. Pick another folder, or use ONE ZIP FILE.'); return; }
        }
        setBusy(true); setDone(0); setTotal(0); setStep('Getting the data from the server...');
        try {
            const now = new Date();
            const data = await settingsService.backupData();
            const built = buildBackup(data, now);
            const root = backupFolderName(now);
            const files = built.files;
            setTotal(files.length); setStep('Saving the files...');
            const missing = [];
            const zipped = {};
            let n = 0;
            const bytesOf = async (f) => {
                if (f.doc) {
                    try { return await fetchDocBytes(f.doc.filePath); }
                    catch { missing.push(f.path); return null; }
                }
                return strToU8(f.text);
            };
            // documents are fetched four at a time; each one is written as soon as it arrives
            for (let i = 0; i < files.length; i += 4) {
                const batch = files.slice(i, i + 4);
                const got = await Promise.all(batch.map(bytesOf));
                for (let k = 0; k < batch.length; k++) {
                    if (got[k]) {
                        if (dir) await writeInto(dir, `${root}/${batch[k].path}`, got[k]);
                        else zipped[`${root}/${batch[k].path}`] = [got[k], { level: batch[k].doc ? 0 : 6 }];
                    }
                    n++;
                }
                setDone(n);
            }
            if (missing.length) {
                const txt = strToU8('These documents could not be copied (the file was not reachable on the server):\r\n\r\n' + missing.join('\r\n') + '\r\n');
                if (dir) await writeInto(dir, `${root}/MISSING FILES.txt`, txt);
                else zipped[`${root}/MISSING FILES.txt`] = txt;
            }
            if (!dir) {
                setStep('Packing the ZIP file...');
                await new Promise(r => setTimeout(r, 30));
                const blob = new Blob([zipSync(zipped)], { type: 'application/zip' });
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob); a.download = root + '.zip';
                document.body.appendChild(a); a.click(); a.remove();
                setTimeout(() => URL.revokeObjectURL(a.href), 120000);
            }
            const saved = files.length - missing.length;
            const r = await settingsService.backupDone({ mode, files: saved, clients: built.clients }).catch(() => null);
            setLast(r?.lastBackupAt || new Date().toISOString());
            setResult({ root, clients: built.clients, files: saved, missing: missing.length, mode });
        } catch (e) {
            setError((e?.message || 'The backup did not finish.') + ' Nothing is lost on the server. Try again.');
        } finally {
            setBusy(false); setStep('');
        }
    };

    const ago = daysSince(last);
    const due = last === null || (ago != null && ago >= BACKUP_DUE_DAYS);
    const pct = total ? Math.round((done / total) * 100) : 0;

    return (
        <div className={styles.box} data-backup="">
            <div className={styles.label}>Backup to my computer</div>
            <p className={styles.lead}>A copy of everything, arranged in a folder per client: their details, projects, payments, notes and documents, plus a full copy of the database. Keep it on your external hard drive. Once a month is a good habit.</p>

            <div className={`${styles.lastLine} ${due ? styles.lastDue : ''}`} role="status">
                {due ? <FiAlertTriangle aria-hidden="true" /> : <FiCheckCircle aria-hidden="true" />}
                <span>{last === undefined ? 'Checking the last backup...' : last === null ? 'No backup has been made yet.'
                    : `Last backup: ${new Date(last).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })} (${ago === 0 ? 'today' : ago === 1 ? 'yesterday' : ago + ' days ago'}).`}</span>
            </div>

            <div className={styles.choices} role="radiogroup" aria-label="How to save the backup">
                <button type="button" role="radio" aria-checked={mode === 'folder'} disabled={busy || !canPickFolder()}
                    className={`${styles.choice} ${mode === 'folder' ? styles.choiceOn : ''}`} onClick={() => setMode('folder')}>
                    <FiFolder aria-hidden="true" className={styles.choiceIcon} />
                    <span className={styles.choiceTitle}>STRAIGHT INTO A FOLDER</span>
                    <span className={styles.choiceText}>{canPickFolder()
                        ? 'Pick a folder (for example on your hard drive). The client folders are written there, ready to open. Nothing to unzip.'
                        : 'This browser cannot do this. Use Chrome or Edge on a computer, or choose ONE ZIP FILE.'}</span>
                </button>
                <button type="button" role="radio" aria-checked={mode === 'zip'} disabled={busy}
                    className={`${styles.choice} ${mode === 'zip' ? styles.choiceOn : ''}`} onClick={() => setMode('zip')}>
                    <FiArchive aria-hidden="true" className={styles.choiceIcon} />
                    <span className={styles.choiceTitle}>ONE ZIP FILE</span>
                    <span className={styles.choiceText}>One file downloads. Copy it to your hard drive. Unzip it only when you want to look inside. Works on a phone too.</span>
                </button>
            </div>

            {error && <div className={styles.err} role="alert"><FiAlertTriangle aria-hidden="true" /><span>{error}</span></div>}
            {result && (
                <div className={styles.ok} role="status"><FiCheckCircle aria-hidden="true" />
                    <span><strong>Backup saved.</strong> {result.mode === 'folder' ? `Folder "${result.root}"` : `File "${result.root}.zip" (in your downloads)`}: {result.clients} client folders, {result.files} files.
                        {result.missing > 0 ? ` ${result.missing} documents could not be copied; they are listed in MISSING FILES.txt.` : ''} Open START HERE.html inside it to look through.</span>
                </div>
            )}
            {busy && (
                <div className={styles.progress} aria-live="polite">
                    <div className={styles.progressText}>{step}{total ? ` ${done} of ${total}` : ''}</div>
                    <div className={styles.bar}><span style={{ width: pct + '%' }} /></div>
                </div>
            )}

            <div className={styles.actions}>
                <button type="button" className={styles.goBtn} onClick={run} disabled={busy}>
                    <FiDownload aria-hidden="true" /> {busy ? 'BACKING UP...' : 'BACK UP NOW'}
                </button>
            </div>
        </div>
    );
}
