// PATH: erp-frontend/src/pages/Pending/PendingViewPage.jsx
// fix181 (8.5, 8.7, 8.10, 12.1 to 12.3): ONE Pending project, with no money on screen.
//  - Employee (the person who entered it): reads it, adds notes and scans while it is still Pending.
//  - Secretary and above: checks the people, may correct a mistyped National ID, then STARTS it (price + any money
//    already received) or REJECTS it with a reason. Starting uses the same money rules as New Project (server side).
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { roleFlags } from '../../utils/roles';
import { errorText } from '../../utils/errorText';
import pendingService from '../../services/pendingService';
import landService from '../../services/landService';
import clientService from '../../services/clientService';
import styles from './Pending.module.css';

const day = (v) => (v ? String(v).slice(0, 10) : '');
const localISO = (d = new Date()) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
const digits = (v) => String(v || '').replace(/[^0-9]/g, '');

function Item({ label, value }) {
    if (value === null || value === undefined || value === '') return null;
    return (<div><div className={styles.label}>{label}</div><div className={styles.value}>{value}</div></div>);
}

function People({ title, people }) {
    if (!people || people.length === 0) return null;
    return (
        <div className={styles.card}>
            <div className={styles.label}>{title}</div>
            <ul className={styles.list}>
                {people.map(p => (
                    <li key={p.id || p.fullName}>
                        <span className={styles.value}>{p.fullName}</span>
                        <span className={styles.muted}> {p.phone ? '- ' + p.phone : ''} {p.nationalId ? '- NIN ' + p.nationalId : ''}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default function PendingViewPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const flags = roleFlags(user);
    const office = flags.isStaff;   // Secretary and above

    const [p, setP] = useState(null);
    const [error, setError] = useState('');
    const [msg, setMsg] = useState('');
    const [busy, setBusy] = useState(false);
    // Employee tools
    const [note, setNote] = useState('');
    const [files, setFiles] = useState([]);
    const [cats, setCats] = useState([]);
    const [cat, setCat] = useState('');
    // office tools
    const [cost, setCost] = useState('');
    const [deposit, setDeposit] = useState('');
    const [payerNin, setPayerNin] = useState('');
    const [paidDate, setPaidDate] = useState('');
    const [rejectWhy, setRejectWhy] = useState('');
    const [ninEdit, setNinEdit] = useState({});

    const load = useCallback(async () => {
        setError('');
        try { setP(await pendingService.view(id)); }
        catch (e) { setError(errorText(e)); }
    }, [id]);
    useEffect(() => {
        let alive = true;
        pendingService.view(id).then(d => { if (alive) setP(d); }).catch(e => { if (alive) setError(errorText(e)); });
        return () => { alive = false; };
    }, [id]);
    useEffect(() => {
        if (office) return;
        landService.getDocumentCategories().then(list => { setCats(list || []); if (list && list[0]) setCat(list[0].code); }).catch(() => {});
    }, [office]);

    const run = async (fn, ok) => {
        setBusy(true); setError(''); setMsg('');
        try { await fn(); setMsg(ok); await load(); }
        catch (e) { setError(errorText(e)); }
        finally { setBusy(false); }
    };

    const start = () => {
        const total = Number(digits(cost));
        const dep = Number(digits(deposit) || 0);
        if (!total) { setError('Enter the total cost before starting the project.'); return; }
        if (dep > total) { setError('The money already received is more than the total cost.'); return; }
        const clients = (p && p.clients) || [];
        if (dep > 0 && clients.length > 1 && !payerNin) { setError('Pick which client paid the money already received.'); return; }
        const body = { totalCost: total, initialPayment: dep || null, initialPaymentPayerNin: payerNin || null,
            lastPaidDate: dep > 0 && paidDate ? paidDate : null };
        run(async () => {
            await pendingService.start(id, body);
            navigate('/folder/' + id);
        }, 'Project started.');
    };

    const reject = () => {
        if (rejectWhy.trim().length < 5) { setError('Write why this entry is rejected (at least 5 characters).'); return; }
        run(async () => { await pendingService.reject(id, rejectWhy.trim()); navigate('/land/projects'); }, 'Entry rejected.');
    };

    if (error && !p) return (<div className={styles.page}><div className={styles.error} role="alert">{error}</div>
        <button type="button" className={styles.btn} onClick={load}>Retry</button></div>);
    if (!p) return <div className={styles.page}><div className={styles.muted}>Loading...</div></div>;

    return (
        <div className={styles.page}>
            <div className={styles.head}>
                <h1 className={styles.title}>PROJECT #{p.projectIndex} <span className={`${styles.badge} ${styles.badgePending}`}>PENDING</span></h1>
                <span className={styles.sub}>{(p.projectType || '').replace(/_/g, ' ')} - entered {day(p.enteredAt)} by {p.enteredBy}{p.ageDays != null ? ' (' + p.ageDays + ' day(s) ago)' : ''}</span>
            </div>

            {office && <div className={styles.banner}>Waiting for prices. Check every name and National ID, fill in the prices and start this project.</div>}
            {error && <div className={styles.error} role="alert">{error}</div>}
            {msg && <div className={styles.ok}>{msg}</div>}

            <div className={styles.card}>
                <div className={styles.grid}>
                    <Item label="District" value={p.district} /><Item label="County" value={p.county} />
                    <Item label="Sub-county" value={p.subCounty} /><Item label="Parish" value={p.parish} />
                    <Item label="Village" value={p.village} /><Item label="Area" value={p.area} />
                    <Item label="Start date" value={day(p.projectStartDate)} />
                    <Item label="Plot" value={p.plotNumber} /><Item label="Block" value={p.block} />
                    <Item label="Tenure" value={p.tenure} /><Item label="Area (ha)" value={p.areaHectares} />
                    <Item label="Volume" value={p.volume} /><Item label="Folio" value={p.folio} />
                    <Item label="Title date" value={day(p.titleIssueDate)} />
                    <Item label="Subdivisions" value={p.subdivisionCount} />
                </div>
            </div>

            <People title="Clients" people={p.clients} />
            <People title="Owners" people={p.owners} />
            {p.neighbors && p.neighbors.length > 0 && (
                <div className={styles.card}>
                    <div className={styles.label}>Neighbors</div>
                    <ul className={styles.list}>{p.neighbors.map((n, i) => (<li key={i}><span className={styles.value}>{n.fullName}</span>
                        <span className={styles.muted}> {n.side ? '- ' + n.side : ''} {n.phone ? '- ' + n.phone : ''}</span></li>))}</ul>
                </div>
            )}

            {!office && (
                <>
                    <div className={styles.card}>
                        <div className={styles.label}>Add a note</div>
                        <div className={styles.form}>
                            <textarea className={styles.textarea} value={note} maxLength={1000} onChange={e => setNote(e.target.value)} aria-label="Note" />
                            <div className={styles.actions}>
                                <button type="button" className={styles.btn} disabled={busy || !note.trim()}
                                    onClick={() => run(async () => { await pendingService.addNote(id, note.trim()); setNote(''); }, 'Note saved.')}>SAVE NOTE</button>
                            </div>
                        </div>
                    </div>
                    <div className={styles.card}>
                        <div className={styles.label}>Add scans (PDF, JPG, PNG, WEBP)</div>
                        <div className={styles.form}>
                            <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={e => setFiles(Array.from(e.target.files || []))} aria-label="Scans" />
                            <select className={styles.input} value={cat} onChange={e => setCat(e.target.value)} aria-label="Document type">
                                {cats.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
                            </select>
                            <div className={styles.actions}>
                                <button type="button" className={styles.btn} disabled={busy || files.length === 0}
                                    onClick={() => run(async () => { await pendingService.addDocuments(id, files, files.map(() => cat)); setFiles([]); }, 'Scans saved.')}>UPLOAD</button>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {office && (
                <>
                    <div className={styles.card}>
                        <div className={styles.label}>Correct a National ID (only while every project of that client is Pending)</div>
                        <ul className={styles.list}>
                            {(p.clients || []).concat((p.owners || []).filter(o => !(p.clients || []).some(c => c.id === o.id))).map(c => (
                                <li key={c.id} className={styles.row}>
                                    <span className={styles.value}>{c.fullName}</span>
                                    <input className={styles.input} style={{ maxWidth: 220 }} value={ninEdit[c.id] ?? c.nationalId ?? ''} aria-label={'National ID of ' + c.fullName}
                                        onChange={e => setNinEdit({ ...ninEdit, [c.id]: e.target.value.toUpperCase() })} />
                                    <button type="button" className={`${styles.btn} ${styles.btnGhost}`} disabled={busy || !ninEdit[c.id] || ninEdit[c.id] === c.nationalId}
                                        onClick={() => run(() => clientService.correctNin(c.id, ninEdit[c.id]), 'National ID corrected.')}>SAVE NIN</button>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className={styles.card}>
                        <div className={styles.label}>Start this project</div>
                        <div className={styles.form}>
                            <label className={styles.field}><span className={styles.label}>Total cost (UGX)</span>
                                <input className={styles.input} inputMode="numeric" value={cost ? Number(digits(cost)).toLocaleString() : ''} onChange={e => setCost(digits(e.target.value))} /></label>
                            <label className={styles.field}><span className={styles.label}>Money already received (UGX, optional)</span>
                                <input className={styles.input} inputMode="numeric" value={deposit ? Number(digits(deposit)).toLocaleString() : ''} onChange={e => setDeposit(digits(e.target.value))} /></label>
                            {Number(digits(deposit)) > 0 && (p.clients || []).length > 1 && (
                                <label className={styles.field}><span className={styles.label}>Which client paid?</span>
                                    <select className={styles.input} value={payerNin} onChange={e => setPayerNin(e.target.value)}>
                                        <option value="">Choose the client</option>
                                        {(p.clients || []).map(c => <option key={c.id} value={c.nationalId}>{c.fullName}</option>)}
                                    </select></label>
                            )}
                            {Number(digits(deposit)) > 0 && (
                                <label className={styles.field}><span className={styles.label}>Date it was paid (leave empty if not known)</span>
                                    <input type="date" className={styles.input} value={paidDate} max={localISO()} onChange={e => setPaidDate(e.target.value)} /></label>
                            )}
                            <div className={styles.actions}>
                                <button type="button" className={styles.btn} disabled={busy} onClick={start}>START PROJECT</button>
                            </div>
                        </div>
                    </div>

                    <div className={styles.card}>
                        <div className={styles.label}>Reject this entry (a mistake or a duplicate)</div>
                        <div className={styles.form}>
                            <textarea className={styles.textarea} value={rejectWhy} maxLength={500} onChange={e => setRejectWhy(e.target.value)} placeholder="Why? The person who entered it will read this." aria-label="Reason for rejecting" />
                            <div className={styles.actions}>
                                <button type="button" className={`${styles.btn} ${styles.btnDanger}`} disabled={busy} onClick={reject}>REJECT ENTRY</button>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
