// PATH: erp-frontend/src/components/print/ClientFilePrint.jsx
// fix212 (David, 17 Oct 2026): a PRINT for the Client folder, in the same layout as the Project File he liked
// (navy band, big two-line title, reference details, bands that alternate pale tint / white, sign-off lines).
// It shares the Project File's paper styles (ProjectFilePrint.module.css). Money parts print only when showMoney
// is true (the Client page shows money to the Director and above only).
import React from 'react';
import { PROJECT_STATUS } from '../../utils/projectStatus';
import s from './ProjectFilePrint.module.css';

const money = (n) => 'UGX ' + Number(n || 0).toLocaleString();
const num = (n) => Number(n || 0).toLocaleString();
const day = (d) => (d ? new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : '');
const dash = (v) => (v === null || v === undefined || v === '' ? '—' : v);
const isJoint = (p) => String(p.ownershipType || 'SOLO').toUpperCase() === 'JOINT';
const statusWord = (p) => (p.released ? PROJECT_STATUS.HANDED_OVER : p.receivable ? PROJECT_STATUS.RECEIVABLES : PROJECT_STATUS.ACTIVE).label;
const pctPaid = (p) => { const owed = Number(p.owed || 0); const paid = Number(p.paid || 0); const total = Number(p.billed || 0) || (owed + paid); return total > 0 ? Math.min(Math.round((paid / total) * 100), 100) : (p.released ? 100 : 0); };

function H({ children }) { return <h2 className={s.h2}>{children}</h2>; }
function Band({ tint = false, children, className = '' }) {
    return <section className={`${s.band} ${tint ? s.tint : ''} ${className}`}>{children}</section>;
}
function KV({ k, v, mono = false }) {
    return <div className={s.kv}><span className={s.k}>{k}</span><span className={`${s.v} ${mono ? s.mono : ''}`}>{v}</span></div>;
}

/** props: client (the dossier), plots, totals, printedBy, showMoney */
export default function ClientFilePrint({ client: d, plots = [], totals = {}, printedBy, showMoney = false, className = '' }) {
    if (!d) return null;
    const printed = new Date();
    const solo = plots.filter(p => !isJoint(p)).length;
    const joint = plots.length - solo;
    const handed = plots.filter(p => p.released).length;
    const inRec = plots.filter(p => p.receivable).length;
    const problems = plots.filter(p => p.problem).length;
    const districts = [...new Set(plots.map(p => p.district).filter(Boolean))];
    const pays = plots.flatMap(p => (p.payments || []).map(x => ({ ...x, index: p.index })))
        .sort((a, b) => String(b.paidOn || '').localeCompare(String(a.paidOn || '')));
    const calls = d.notes || [];

    const keyPoints = [
        plots.length + (plots.length === 1 ? ' project' : ' projects') + ' (' + solo + ' solo, ' + joint + ' joint)',
        handed ? handed + ' title' + (handed === 1 ? '' : 's') + ' handed over' : 'No title handed over yet',
        inRec ? inRec + ' in receivables (storage fees apply)' : null,
        problems ? problems + ' flagged as a PROBLEM' : null,
        showMoney ? (Number(totals.owed) > 0 ? 'Balance owed: ' + money(totals.owed) : 'Nothing owed') : null,
        'Last contact: ' + (d.lastContact ? day(d.lastContact) : 'never'),
        calls.length ? calls.length + ' call note' + (calls.length === 1 ? '' : 's') + ' on file' : 'No calls logged',
    ].filter(Boolean);

    return (
        <div className={`${s.doc} ${className}`} aria-hidden="true">
            <header className={s.banner}>
                <div className={s.brand}>
                    <span className={s.mark} aria-hidden="true">GE</span>
                    <span>
                        <span className={s.company}>GE SOLUTIONS</span>
                        <span className={s.tagline}>Land surveying and title processing</span>
                    </span>
                </div>
                <div className={s.bannerRight}>
                    <span>Client file</span>
                    <span>Printed {day(printed)}{printedBy ? ' by ' + printedBy : ''}</span>
                </div>
            </header>

            <div className={s.hero}>
                <div className={s.heroLeft}>
                    <div className={s.title}>Client<br />File</div>
                    <div className={s.refChip}>{d.name}</div>
                </div>
                <div className={s.heroGrid}>
                    <KV k="Full name" v={dash(d.name)} />
                    <KV k="NIN" v={dash(d.nin)} mono />
                    <KV k="Phone" v={dash(d.phone)} mono />
                    <KV k="Email" v={dash(d.email)} />
                    <KV k="Address" v={dash(d.address)} />
                    <KV k="Last contact" v={d.lastContact ? day(d.lastContact) : 'Never'} />
                </div>
            </div>

            <Band tint className={s.cols}>
                <div>
                    <H>Overview</H>
                    <p className={s.lead}>
                        {d.name} holds {plots.length} {plots.length === 1 ? 'project' : 'projects'} with GE Solutions
                        {districts.length ? ', in ' + districts.join(', ') : ''}.
                    </p>
                    {showMoney && (
                        <div className={s.miniGrid}>
                            <KV k="Billed" v={money(totals.billed)} mono />
                            <KV k="Paid" v={money(totals.paid)} mono />
                            <KV k="Owed" v={money(totals.owed)} mono />
                            <KV k="Storage fees" v={money(totals.storage)} mono />
                            <KV k="Fees paid" v={money(totals.storagePaid)} mono />
                            <KV k="Fees unpaid" v={money(totals.storageUnpaid)} mono />
                        </div>
                    )}
                </div>
                <div>
                    <H>Key points</H>
                    <ul className={s.dots}>{keyPoints.map((k, i) => <li key={i}>{k}</li>)}</ul>
                </div>
            </Band>

            <Band>
                <H>Projects <small>{plots.length}</small></H>
                {plots.length ? (
                    <table className={s.table}>
                        <thead><tr><th>Index</th><th>Type</th><th>District</th><th>Ownership</th><th>Status</th>
                            {showMoney && <><th className={s.right}>Owed</th><th className={s.right}>Paid</th><th className={s.right}>Paid %</th></>}</tr></thead>
                        <tbody>{plots.map((p, i) => (
                            <tr key={p.projectId || i}>
                                <td className={s.mono}>{dash(p.index)}</td>
                                <td>{dash(p.projectTypeLabel)}</td>
                                <td>{dash(p.district)}</td>
                                <td>{isJoint(p) ? 'Joint' + ((p.coOwners || []).length ? ' with ' + p.coOwners.map(c => c.fullName).join(', ') : '') : 'Solo'}</td>
                                <td>{statusWord(p)}{p.problem ? ' · Problem' : ''}{p.critical ? ' · Critical' : ''}</td>
                                {showMoney && <>
                                    <td className={`${s.right} ${s.mono}`}>{num(p.owed)}</td>
                                    <td className={`${s.right} ${s.mono}`}>{num(p.paid)}</td>
                                    <td className={`${s.right} ${s.mono}`}>{pctPaid(p)}%</td>
                                </>}
                            </tr>
                        ))}</tbody>
                    </table>
                ) : <p className={s.none}>No projects registered.</p>}
            </Band>

            {showMoney && (
                <Band tint>
                    <H>Statement of account</H>
                    {pays.length ? (
                        <table className={s.table}>
                            <thead><tr><th>Date paid</th><th>Project</th><th>For</th><th>Paid by</th><th className={s.right}>Amount</th></tr></thead>
                            <tbody>{pays.map((x, i) => (
                                <tr key={x.id || i}>
                                    <td>{x.paidOn ? day(x.paidOn) : '—'}</td>
                                    <td className={s.mono}>#{x.index}</td>
                                    <td>{x.allocation === 'STORAGE' ? 'Storage fees' : 'Title work'}{x.reversal ? ' · Reversal' : ''}{x.reversed ? ' · Reversed' : ''}</td>
                                    <td>{dash(x.payerName)}</td>
                                    <td className={`${s.right} ${s.mono}`}>{num(x.amount)}</td>
                                </tr>
                            ))}</tbody>
                        </table>
                    ) : <p className={s.none}>No payments recorded.</p>}
                    <div className={s.totals}>
                        <div><span>Total billed</span><span className={s.mono}>{money(totals.billed)}</span></div>
                        {Number(totals.storage) > 0 && <div><span>Storage fees</span><span className={s.mono}>{money(totals.storage)}</span></div>}
                        <div><span>Paid</span><span className={s.mono}>{money(totals.paid)}</span></div>
                        <div className={s.grand}><span>Balance owed</span><span className={s.mono}>{money(totals.owed)}</span></div>
                    </div>
                </Band>
            )}

            <Band tint={!showMoney}>
                <H>Call log <small>{calls.length}</small></H>
                {calls.length ? (
                    <ul className={s.notes}>{calls.map((n, i) => (
                        <li key={i}><span className={s.noteMeta}>{day(n.createdAt)}{n.author ? ' · ' + n.author : ''}{n.tag ? ' · ' + n.tag : ''}</span>{n.text || ''}</li>
                    ))}</ul>
                ) : <p className={s.none}>No calls logged for this client.</p>}
            </Band>

            <div className={s.sign}>
                <div><div className={s.line} /><span>Prepared by (name and signature)</span></div>
                <div><div className={s.line} /><span>Checked by (name and signature)</span></div>
                <div><div className={s.line} /><span>Date</span></div>
            </div>

            <footer className={s.foot}>GE Solutions · Client file · {d.name} · printed {day(printed)}{printedBy ? ' by ' + printedBy : ''}</footer>
        </div>
    );
}
