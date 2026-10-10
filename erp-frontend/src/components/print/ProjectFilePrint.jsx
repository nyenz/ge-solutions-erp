// PATH: erp-frontend/src/components/print/ProjectFilePrint.jsx
// fix199 (David, test note 10): the PRINT of a project is now a proper document (an A4 "Project File"), drawn only on
// paper. It replaces the old print, which was the screen layout with the buttons hidden. David's sample pictures
// (a statement of work, an invoice) were used as a guide for the style only: a letterhead, a reference block,
// numbered sections with ruled tables, a statement of account with a totals box, and sign-off lines.
import React from 'react';
import { statusOf, moneyWordsOf, stagesOf } from '../../utils/projectStatus';
import s from './ProjectFilePrint.module.css';

const money = (n) => 'UGX ' + Number(n || 0).toLocaleString();
const day = (d) => (d ? new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : '');
const dash = (v) => (v === null || v === undefined || v === '' ? '—' : v);
const PAY_WORD = { STANDARD: 'Payment', INITIAL_DEPOSIT: 'Deposit at intake', RECEIVABLE_PARTIAL: 'Payment (receivables)', REVERSAL: 'Reversal' };

function Section({ n, title, children }) {
    return (
        <section className={s.section}>
            <h2 className={s.h2}><span className={s.num}>{n}</span>{title}</h2>
            {children}
        </section>
    );
}

function People({ rows }) {
    if (!rows || !rows.length) return <p className={s.none}>None recorded.</p>;
    return (
        <table className={s.table}>
            <thead><tr><th className={s.narrow}>#</th><th>Name</th><th>National ID (NIN)</th><th>Phone</th></tr></thead>
            <tbody>{rows.map((p, i) => (
                <tr key={p.id || i}><td>{i + 1}</td><td>{p.fullName}</td><td className={s.mono}>{dash(p.nationalId)}</td><td className={s.mono}>{dash(p.phoneNumber || p.phone)}</td></tr>
            ))}</tbody>
        </table>
    );
}

/**
 * props: project, stages, payments, documents, notes, neighbors, typeLabel, catLabel(code), printedBy, showMoney
 * Rendered hidden on screen; the Folder page's print rules show ONLY this when printing.
 */
export default function ProjectFilePrint({ project: p, stages, payments = [], documents = [], notes = [], neighbors = [],
    typeLabel, catLabel = (c) => c, statusNameOf = () => '', printedBy, showMoney = true, className = '' }) {
    if (!p) return null;
    const t = p.landTitle;
    const status = statusOf(p);
    const words = moneyWordsOf(p).map(w => w.label).join(' · ');
    const stageList = stagesOf(p, stages);
    const done = stageList.filter(x => x.done).length;
    const cost = Number(p.totalCost || 0);
    const paid = Number(p.amountPaid || 0);
    const fees = Number(p.storageFeesAccumulated || 0);
    const owed = typeof p.owedNow === 'number' ? p.owedNow : Math.max(0, cost + (p.isReceivable ? fees : 0) - paid);
    const printed = new Date();
    let n = 0;

    return (
        <div className={`${s.doc} ${className}`} aria-hidden="true">
            {/* letterhead */}
            <header className={s.letter}>
                <div>
                    <div className={s.company}>GE SOLUTIONS</div>
                    <div className={s.tagline}>Land surveying and title processing</div>
                </div>
                <div className={s.headRight}>
                    <div className={s.docTitle}>Project File</div>
                    <div className={s.ref}>Ref. #{p.projectIndex}</div>
                </div>
            </header>
            <div className={s.rule} />

            {/* reference block */}
            <div className={s.refGrid}>
                <div><span className={s.k}>Project</span><span className={s.v}>#{p.projectIndex}{t?.plotNumber ? ' · Plot ' + t.plotNumber : ''}</span></div>
                <div><span className={s.k}>Type</span><span className={s.v}>{typeLabel || dash(p.projectType)}</span></div>
                <div><span className={s.k}>Status</span><span className={s.v}>{status.label}{words ? ' · ' + words : ''}</span></div>
                <div><span className={s.k}>Invoice no.</span><span className={`${s.v} ${s.mono}`}>{dash(p.invoiceNumber)}</span></div>
                <div><span className={s.k}>Contract no.</span><span className={`${s.v} ${s.mono}`}>{dash(p.contractNumber)}</span></div>
                <div><span className={s.k}>Date started</span><span className={s.v}>{dash(day(p.projectStartDate))}</span></div>
                <div><span className={s.k}>Entered</span><span className={s.v}>{dash(day(p.entryDate || p.createdAt))}{p.createdBy ? ' by ' + p.createdBy : ''}</span></div>
                <div><span className={s.k}>Printed</span><span className={s.v}>{day(printed)}{printedBy ? ' by ' + printedBy : ''}</span></div>
            </div>
            {(p.problem || t?.isReleased || p.isReceivable) && (
                <p className={s.flag}>
                    {p.problem ? 'FLAGGED AS A PROBLEM. ' : ''}{t?.isReleased ? 'TITLE HANDED OVER TO THE CLIENT. ' : ''}{p.isReceivable ? 'IN RECEIVABLES (storage fees apply).' : ''}
                </p>
            )}

            <Section n={++n} title="Location">
                <table className={s.table}>
                    <thead><tr><th>District</th><th>County</th><th>Sub-county</th><th>Parish</th><th>Village</th><th>Area (ha)</th></tr></thead>
                    <tbody><tr><td>{dash(p.district)}</td><td>{dash(p.county)}</td><td>{dash(p.subCounty)}</td><td>{dash(p.parish)}</td><td>{dash(p.village)}</td><td>{dash(p.area)}</td></tr></tbody>
                </table>
            </Section>

            {t && (
                <Section n={++n} title="Title details">
                    <table className={s.table}>
                        <thead><tr><th>Plot</th><th>Block</th><th>Tenure</th><th>Area (ha)</th><th>Volume</th><th>Folio</th><th>Title date</th></tr></thead>
                        <tbody><tr><td>{dash(t.plotNumber)}</td><td>{dash(t.block)}</td><td>{dash(t.tenure)}</td><td>{dash(t.areaHectares)}</td><td>{dash(t.volume)}</td><td>{dash(t.folio)}</td><td>{dash(day(t.titleIssueDate))}</td></tr></tbody>
                    </table>
                </Section>
            )}

            <Section n={++n} title="Clients (they pay)"><People rows={p.clients} /></Section>
            <Section n={++n} title="Owners (on the title)"><People rows={p.proprietors} /></Section>
            {neighbors.length > 0 && (
                <Section n={++n} title="Neighbours">
                    <table className={s.table}>
                        <thead><tr><th className={s.narrow}>#</th><th>Name</th><th>Side</th><th>Plot</th><th>Phone</th></tr></thead>
                        <tbody>{neighbors.map((x, i) => (<tr key={i}><td>{i + 1}</td><td>{x.fullName}</td><td>{dash(x.side)}</td><td>{dash(x.plotNumber)}</td><td className={s.mono}>{dash(x.phone)}</td></tr>))}</tbody>
                    </table>
                </Section>
            )}

            <Section n={++n} title={'Stages (' + done + ' of ' + stageList.length + ' done)'}>
                <table className={s.table}>
                    <thead><tr><th className={s.narrow}>#</th><th>Stage</th><th className={s.center}>Done</th><th>Date</th><th>By</th></tr></thead>
                    <tbody>{stageList.map((x, i) => (
                        <tr key={x.id || i}><td>{i + 1}</td><td>{x.statusName || x.name}</td><td className={s.center}>{x.done ? '✓' : '—'}</td><td>{x.done ? dash(day(x.completedAt)) : ''}</td><td>{x.done ? dash(x.completedBy) : ''}</td></tr>
                    ))}</tbody>
                </table>
            </Section>

            {showMoney && (
                <Section n={++n} title="Statement of account">
                    {payments.length ? (
                        <table className={s.table}>
                            <thead><tr><th>Date paid</th><th>Kind</th><th>For</th><th>Paid by</th><th>Recorded by</th><th className={s.right}>Amount</th></tr></thead>
                            <tbody>{payments.map((x, i) => (
                                <tr key={x.id || i}><td>{dash(day(x.paidOn || x.timestamp))}</td><td>{PAY_WORD[x.paymentType] || x.paymentType}</td>
                                    <td>{x.allocation === 'STORAGE' ? 'Storage fees' : 'Title work'}</td><td>{dash(x.payerName)}</td><td>{dash(x.recordedBy)}</td>
                                    <td className={`${s.right} ${s.mono}`}>{Number(x.amountPaid || 0).toLocaleString()}</td></tr>
                            ))}</tbody>
                        </table>
                    ) : <p className={s.none}>No payments recorded.</p>}
                    <div className={s.totals}>
                        <div><span>Total cost</span><span className={s.mono}>{money(cost)}</span></div>
                        {fees > 0 && <div><span>Storage fees</span><span className={s.mono}>{money(fees)}</span></div>}
                        <div><span>Paid</span><span className={s.mono}>{money(paid)}</span></div>
                        <div className={s.grand}><span>Balance owed</span><span className={s.mono}>{money(owed)}</span></div>
                    </div>
                </Section>
            )}

            <Section n={++n} title={'Documents on file (' + documents.length + ')'}>
                {documents.length ? (
                    <table className={s.table}>
                        <thead><tr><th>Type</th><th>File</th><th>Stage</th><th>Added</th></tr></thead>
                        <tbody>{documents.map((d, i) => (
                            <tr key={d.id || i}><td>{catLabel(d.category)}</td><td className={s.wrap}>{d.fileName}</td><td>{dash(statusNameOf(d.statusId))}</td><td>{dash(day(d.uploadedAt))}{d.uploadedBy ? ' · ' + d.uploadedBy : ''}</td></tr>
                        ))}</tbody>
                    </table>
                ) : <p className={s.none}>No documents attached.</p>}
            </Section>

            {notes.length > 0 && (
                <Section n={++n} title="Notes">
                    <ol className={s.notes}>{notes.map((x, i) => (
                        <li key={x.id || i}><span className={s.noteMeta}>{day(x.timestamp)}{x.recordedBy ? ' · ' + x.recordedBy : ''}</span>{x.notes}</li>
                    ))}</ol>
                </Section>
            )}

            <div className={s.sign}>
                <div><div className={s.line} /><span>Prepared by (name and signature)</span></div>
                <div><div className={s.line} /><span>Checked by (name and signature)</span></div>
                <div><div className={s.line} /><span>Date</span></div>
            </div>

            <footer className={s.foot}>GE Solutions · Project #{p.projectIndex} · printed {day(printed)}{printedBy ? ' by ' + printedBy : ''}</footer>
        </div>
    );
}
