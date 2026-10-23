// PATH: erp-frontend/src/components/print/ProjectFilePrint.jsx
// fix199 (David, test note 10): the PRINT of a project is a proper A4 document (a "Project File"), drawn only on paper.
// fix207: company colours. fix210 (David sent a "case study" sheet as the look he wants, "similar, not exact"):
//  - a full-width navy band at the top with the company name;
//  - a big two-line title on the left, the reference details on the right (small orange labels, thin lines);
//  - the body in wide bands that alternate pale tint / white, most bands split into two columns
//    (Overview | Key points, Clients | Owners, Documents | Notes);
//  - headings are plain coloured words (no numbered boxes), lists use round coloured dots;
//  - the stages are a two-column checklist with filled (done) and hollow (open) circles.
// Money stays a ruled statement with a totals box, and the page ends with sign-off lines.
import React from 'react';
import GesMark from './GesMark';   // fix227: the website's compass logo
import { statusOf, moneyWordsOf, stagesOf, waitingFor } from '../../utils/projectStatus';
import { methodLine } from '../../utils/paymentMethods';   // fix214
import s from './ProjectFilePrint.module.css';

const money = (n) => 'UGX ' + Number(n || 0).toLocaleString();
const day = (d) => (d ? new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : '');
const dash = (v) => (v === null || v === undefined || v === '' ? '—' : v);
const PAY_WORD = { STANDARD: 'Payment', INITIAL_DEPOSIT: 'Deposit at intake', RECEIVABLE_PARTIAL: 'Payment (receivables)', REVERSAL: 'Reversal' };

function H({ children }) { return <h2 className={s.h2}>{children}</h2>; }
function Band({ tint = false, children, className = '' }) {
    return <section className={`${s.band} ${tint ? s.tint : ''} ${className}`}>{children}</section>;
}
function KV({ k, v, mono = false }) {
    return <div className={s.kv}><span className={s.k}>{k}</span><span className={`${s.v} ${mono ? s.mono : ''}`}>{v}</span></div>;
}

function People({ rows }) {
    if (!rows || !rows.length) return <p className={s.none}>None recorded.</p>;
    return (
        <ul className={s.people}>
            {rows.map((p, i) => (
                <li key={p.id || i}>
                    <strong>{p.fullName}</strong>
                    <span className={s.mono}>NIN {dash(p.nationalId)}</span>
                    <span className={s.mono}>{dash(p.phoneNumber || p.phone)}</span>
                </li>
            ))}
        </ul>
    );
}

/**
 * props: project, stages, payments, documents, notes, neighbors, typeLabel, catLabel(code), statusNameOf(id), printedBy, showMoney
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
    const pct = stageList.length ? Math.round((done / stageList.length) * 100) : 0;
    const waiting = waitingFor(p, stages);
    const cost = Number(p.totalCost || 0);
    const paid = Number(p.amountPaid || 0);
    const fees = Number(p.storageFeesAccumulated || 0);
    const owed = typeof p.owedNow === 'number' ? p.owedNow : Math.max(0, cost + (p.isReceivable ? fees : 0) - paid);
    const printed = new Date();
    const place = [p.village, p.parish, p.subCounty, p.county, p.district].filter(Boolean).join(', ');
    const half = Math.ceil(stageList.length / 2);

    const keyPoints = [
        status.label + (words ? ' — ' + words : ''),
        done + ' of ' + stageList.length + ' stages done (' + pct + '%)',
        waiting ? (waiting.stage ? 'Waiting for: ' + (waiting.stage.statusName || waiting.stage.name) : waiting.text.charAt(0) + waiting.text.slice(1).toLowerCase()) : 'Nothing is waiting',
        showMoney ? (owed > 0 ? 'Balance owed: ' + money(owed) : 'Fully paid') : null,
        t ? 'Title: Plot ' + dash(t.plotNumber) + ', Block ' + dash(t.block) + (t.isReleased ? ' — handed over to the client' : '') : 'No title details yet',
        p.problem ? 'Flagged as a PROBLEM' : null,
        p.isReceivable ? 'In receivables (storage fees apply)' : null,
    ].filter(Boolean);

    return (
        <div className={`${s.doc} ${className}`} aria-hidden="true">
            {/* top band */}
            <header className={s.banner}>
                <div className={s.brand}>
                    <GesMark className={s.mark} />
                    <span>
                        <span className={s.company}>GE Solutions</span>
                        <span className={s.tagline}>Land surveying and title processing</span>
                    </span>
                </div>
                <div className={s.bannerRight}>
                    <span>Project #{p.projectIndex}</span>
                    <span>Printed {day(printed)}{printedBy ? ' by ' + printedBy : ''}</span>
                </div>
            </header>

            {/* title + reference details */}
            <div className={s.hero}>
                <div className={s.heroLeft}>
                    <div className={s.title}>Project<br />File</div>
                    <div className={s.refChip}>#{p.projectIndex}{t?.plotNumber ? ' · Plot ' + t.plotNumber : ''}</div>
                </div>
                <div className={s.heroGrid}>
                    <KV k="Type" v={typeLabel || dash(p.projectType)} />
                    <KV k="Status" v={status.label} />
                    <KV k="Invoice no." v={dash(p.invoiceNumber)} mono />
                    <KV k="Contract no." v={dash(p.contractNumber)} mono />
                    <KV k="Date started" v={dash(day(p.projectStartDate))} />
                    <KV k="Entered" v={dash(day(p.entryDate || p.createdAt)) + (p.createdBy ? ' · ' + p.createdBy : '')} />
                </div>
            </div>

            {/* overview | key points */}
            <Band tint className={s.cols}>
                <div>
                    <H>Overview</H>
                    <p className={s.lead}>
                        {typeLabel || 'Project'} for {(p.clients || []).map(c => c.fullName).join(' and ') || 'a client not yet named'}
                        {place ? ', at ' + place : ''}.
                    </p>
                    <div className={s.miniGrid}>
                        <KV k="District" v={dash(p.district)} />
                        <KV k="County" v={dash(p.county)} />
                        <KV k="Sub-county" v={dash(p.subCounty)} />
                        <KV k="Parish" v={dash(p.parish)} />
                        <KV k="Village" v={dash(p.village)} />
                        <KV k="Area (ha)" v={dash(t ? t.areaHectares : p.area)} />
                    </div>
                </div>
                <div>
                    <H>Key points</H>
                    <ul className={s.dots}>{keyPoints.map((k, i) => <li key={i}>{k}</li>)}</ul>
                </div>
            </Band>

            {t && (
                <Band>
                    <H>Title details</H>
                    <div className={s.titleGrid}>
                        <KV k="Plot" v={dash(t.plotNumber)} />
                        <KV k="Block" v={dash(t.block)} />
                        <KV k="Tenure" v={dash(t.tenure)} />
                        <KV k="Area (ha)" v={dash(t.areaHectares)} />
                        <KV k="Volume" v={dash(t.volume)} />
                        <KV k="Folio" v={dash(t.folio)} />
                        <KV k="Title date" v={dash(day(t.titleIssueDate))} />
                    </div>
                </Band>
            )}

            {/* people */}
            <Band tint={!!t} className={s.cols}>
                <div><H>Clients <small>they pay</small></H><People rows={p.clients} /></div>
                <div><H>Owners <small>on the title</small></H><People rows={p.proprietors} /></div>
            </Band>
            {neighbors.length > 0 && (
                <Band tint={!t}>
                    <H>Neighbours</H>
                    <ul className={s.neigh}>
                        {neighbors.map((x, i) => (
                            <li key={i}><strong>{x.fullName}</strong><span>{dash(x.side)}{x.plotNumber ? ' · Plot ' + x.plotNumber : ''}</span><span className={s.mono}>{dash(x.phone)}</span></li>
                        ))}
                    </ul>
                </Band>
            )}

            {/* stages */}
            <Band tint>
                <H>Stages <small>{done} of {stageList.length} done</small></H>
                <div className={s.progress}><span style={{ width: pct + '%' }} /></div>
                <div className={s.stageCols}>
                    {[stageList.slice(0, half), stageList.slice(half)].map((col, ci) => (
                        <ol key={ci} className={s.stages} start={ci * half + 1}>
                            {col.map((x, i) => (
                                <li key={x.id || i} className={x.done ? s.stageDone : ''}>
                                    <span className={s.stageDot} aria-hidden="true">{x.done ? '✓' : ''}</span>
                                    <span className={s.stageName}>{x.statusName || x.name}</span>
                                    <span className={s.stageMeta}>{x.done ? [day(x.completedAt), x.completedBy].filter(Boolean).join(' · ') : 'open'}</span>
                                </li>
                            ))}
                        </ol>
                    ))}
                </div>
            </Band>

            {showMoney && (
                <Band>
                    <H>Statement of account</H>
                    {payments.length ? (
                        <table className={s.table}>
                            <thead><tr><th>Date paid</th><th>Kind</th><th>For</th><th>Paid by</th><th>Method</th><th>Recorded by</th><th className={s.right}>Amount</th></tr></thead>
                            <tbody>{payments.map((x, i) => (
                                <tr key={x.id || i}><td>{dash(day(x.paidOn || x.timestamp))}</td><td>{PAY_WORD[x.paymentType] || x.paymentType}</td>
                                    <td>{x.allocation === 'STORAGE' ? 'Storage fees' : 'Title work'}</td><td>{dash(x.payerName)}</td><td>{methodLine(x.paymentMethod, x.paymentReference)}</td><td>{dash(x.recordedBy)}</td>
                                    <td className={`${s.right} ${s.mono}`}>{Number(x.amountPaid || 0).toLocaleString()}</td></tr>
                            ))}</tbody>
                        </table>
                    ) : null /* fix227: no payments = no empty line; the totals below say Paid UGX 0 */}
                    <div className={s.totals}>
                        <div><span>Total cost</span><span className={s.mono}>{money(cost)}</span></div>
                        {fees > 0 && <div><span>Storage fees</span><span className={s.mono}>{money(fees)}</span></div>}
                        <div><span>Paid</span><span className={s.mono}>{money(paid)}</span></div>
                        <div className={s.grand}><span>Balance owed</span><span className={s.mono}>{money(owed)}</span></div>
                    </div>
                </Band>
            )}

            {/* documents | notes -- fix227: left out when there is neither (never waste paper) */}
            {(documents.length > 0 || notes.length > 0) && <Band tint className={notes.length && documents.length ? s.cols : ''}>
                {documents.length > 0 && <div>
                    <H>Documents on file <small>{documents.length}</small></H>
                    {documents.length ? (
                        <ul className={s.docs}>
                            {documents.map((d, i) => (
                                <li key={d.id || i}>
                                    <span className={s.docType}>{catLabel(d.category)}{statusNameOf(d.statusId) ? ' · ' + statusNameOf(d.statusId) : ''}</span>
                                    <span className={s.docName}>{d.fileName}</span>
                                    <span className={s.docMeta}>{dash(day(d.uploadedAt))}{d.uploadedBy ? ' · ' + d.uploadedBy : ''}</span>
                                </li>
                            ))}
                        </ul>
                    ) : null}
                </div>}
                {notes.length > 0 && (
                    <div>
                        <H>Notes</H>
                        <ul className={s.notes}>{notes.map((x, i) => (
                            <li key={x.id || i}><span className={s.noteMeta}>{day(x.timestamp)}{x.recordedBy ? ' · ' + x.recordedBy : ''}</span>{x.notes}</li>
                        ))}</ul>
                    </div>
                )}
            </Band>}

            <div className={s.sign}>
                <div><div className={s.line} /><span>Prepared by (name and signature)</span></div>
                <div><div className={s.line} /><span>Checked by (name and signature)</span></div>
                <div><div className={s.line} /><span>Date</span></div>
            </div>
        </div>
    );
}
