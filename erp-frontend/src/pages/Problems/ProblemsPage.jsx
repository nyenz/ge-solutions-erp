// PATH: erp-frontend/src/pages/Problems/ProblemsPage.jsx
// fix289 (David, 5 Nov 2026): every problem in the company in one place, and the Site Visits list.
//  - OPEN: what is still wrong, filtered by problem, solution, district or any words (client, plot, project #).
//  - SITE VISITS: one row per project that needs a visit -- from problems ("Needs a site visit") and from Recovery
//    (clients who missed calls) -- grouped by district and sub-county, so one trip can cover many plots.
//  - SOLVED: what was fixed, and how.
import React, { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FiAlertTriangle, FiMapPin, FiCheckCircle, FiRefreshCw, FiCheck } from 'react-icons/fi';
import TabDock from '../../components/common/TabDock';
import HardwareSelect from '../../components/common/HardwareSelect';
import { LoadingState } from '../../components/common/LoadingState';
import problemService, { SOLUTION_WORDS } from '../../services/problemService';
import { errorText } from '../../utils/errorText';
import { fmtDay } from '../../utils/format';
import page from '../Audit/AuditPage.module.css';
import card from '../../components/common/ProjectProblemsPanel.module.css';
import s from './ProblemsPage.module.css';

const ALL = 'All problems', ALL_SOL = 'All solutions', ALL_DIST = 'All districts';   // each filter says what it filters

export default function ProblemsPage() {
    const [params, setParams] = useSearchParams();
    const tab = ['OPEN', 'VISITS', 'SOLVED'].includes((params.get('tab') || '').toUpperCase()) ? params.get('tab').toUpperCase()
        : (params.get('tab') || '').toLowerCase() === 'visits' ? 'VISITS' : 'OPEN';
    const [open, setOpen] = useState(null);
    const [solved, setSolved] = useState(null);
    const [visits, setVisits] = useState(null);
    const [fault, setFault] = useState('');
    const [q, setQ] = useState(params.get('q') || '');
    const [kind, setKind] = useState(ALL);
    const [solution, setSolution] = useState(ALL_SOL);
    const [district, setDistrict] = useState(ALL_DIST);
    const [visiting, setVisiting] = useState(null);   // fix291: { projectId, note } -- VISIT DONE
    const [busy, setBusy] = useState(false);
    const [okMsg, setOkMsg] = useState('');
    const toast = (t, kind) => { if (kind === 'error') { setOkMsg(''); setFault(t); } else { setFault(''); setOkMsg(t); } };

    const load = useCallback(async () => {
        setFault('');
        try {
            const [o, v] = await Promise.all([problemService.list({ status: 'OPEN' }), problemService.siteVisits()]);
            setOpen(o || []); setVisits(v || []);
        } catch (err) { setFault(errorText(err)); setOpen(o => o || []); setVisits(v => v || []); }
    }, []);
    useEffect(() => { Promise.resolve().then(load); }, [load]);
    useEffect(() => {
        if (tab !== 'SOLVED' || solved !== null) return;
        problemService.list({ status: 'SOLVED' }).then(r => setSolved(r || [])).catch(err => { setSolved([]); setFault(errorText(err)); });
    }, [tab, solved]);

    const rows = tab === 'SOLVED' ? (solved || []) : (open || []);
    const kinds = [ALL, ...Array.from(new Set(rows.map(r => r.label))).sort()];
    const districts = [ALL_DIST, ...Array.from(new Set([...(open || []), ...(visits || [])].map(r => r.district).filter(Boolean))).sort()];
    const words = q.trim().toLowerCase();
    const hit = (r) => !words || [r.label, r.detail, r.clientName, r.personName, r.clientPhone, r.plotNumber, r.projectIndex, r.district, r.subCounty, r.parish, r.village]
        .some(x => x && String(x).toLowerCase().includes(words));
    const shown = rows.filter(r => (kind === ALL || r.label === kind) && (solution === ALL_SOL || SOLUTION_WORDS[r.solution] === solution)
        && (district === ALL_DIST || r.district === district) && hit(r));
    const shownVisits = (visits || []).filter(v => (district === ALL_DIST || v.district === district)
        && (!words || [v.clientName, v.clientPhone, v.plotNumber, v.projectIndex, v.district, v.subCounty, v.parish, v.village, ...(v.reasons || [])]
            .some(x => x && String(x).toLowerCase().includes(words))));
    const groupMap = new Map();
    shownVisits.forEach(v => { const k = (v.district || 'NO DISTRICT') + ' / ' + (v.subCounty || 'no sub-county'); if (!groupMap.has(k)) groupMap.set(k, []); groupMap.get(k).push(v); });
    const groups = Array.from(groupMap.entries());

    // fix291: VISIT DONE -- solves the plot's visit problems and writes "site visit done" on Recovery
    const visitDone = async () => {
        if (busy || !visiting) return;
        if (String(visiting.note || '').trim().length < 3) { toast('Write what was found on the visit.', 'error'); return; }
        setBusy(true);
        try {
            const r = await problemService.visitDone(visiting.projectId, visiting.note);
            toast('Visit recorded' + (r && r.solved ? '; ' + r.solved + ' problem' + (r.solved === 1 ? '' : 's') + ' solved.' : '.') + ' A note was written.', 'success');
            setVisiting(null); setSolved(null); await load();
        } catch (err) { toast(errorText(err), 'error'); }
        finally { setBusy(false); }
    };

    const setTab = (t) => { const p = new URLSearchParams(params); p.set('tab', t.toLowerCase()); setParams(p, { replace: true }); };
    const place = (r) => [r.village, r.parish, r.subCounty, r.district].filter(Boolean).join(', ');
    const projectLink = (r) => (<Link className={card.link} to={'/folder/' + r.projectId + '#problems'}>#{r.projectIndex}{r.plotNumber ? ' (plot ' + r.plotNumber + ')' : ''}</Link>);

    return (
        <div className={page.container} data-page="problems">
            <header className={page.pageHeader}>
                <div className={page.headerLeft}>
                    <h1 className={page.title}>Problems</h1>
                    <p className={page.subtitle}>What is wrong on which project, what will be done, and the site visits</p>
                </div>
                <button type="button" className={card.btnGhost} onClick={() => { setSolved(null); load(); }}><FiRefreshCw aria-hidden="true" /> REFRESH</button>
            </header>

            <TabDock label="Problem lists" mode="tab" value={tab} onChange={setTab} items={[
                { key: 'OPEN', label: 'OPEN', count: open ? open.length : undefined, icon: FiAlertTriangle, accent: 'red' },
                { key: 'VISITS', label: 'SITE VISITS', count: visits ? visits.length : undefined, icon: FiMapPin, accent: 'yellow' },
                { key: 'SOLVED', label: 'SOLVED', count: solved ? solved.length : undefined, icon: FiCheckCircle, accent: 'green' },
            ]} />

            <div className={s.filters}>
                <input className={s.search} value={q} onChange={e => setQ(e.target.value)} aria-label="Search problems" placeholder="Search: client, phone, plot, project #, place, words" />
                {tab !== 'VISITS' && <HardwareSelect compact label="" placeholder="Problem" options={kinds} value={kind} onChange={setKind} />}
                {tab !== 'VISITS' && <HardwareSelect compact label="" placeholder="Solution" options={[ALL_SOL, ...Object.values(SOLUTION_WORDS)]} value={solution} onChange={setSolution} />}
                <HardwareSelect compact label="" placeholder="District" options={districts} value={district} onChange={setDistrict} />
            </div>
            {fault && <p className={s.fault} role="alert">{fault}</p>}
            {okMsg && <p className={s.ok} role="status">{okMsg}</p>}

            {tab !== 'VISITS' && ((tab === 'SOLVED' ? solved : open) === null ? <LoadingState label="Loading problems" /> : (
                <div className={s.list}>
                    {shown.length === 0 && <p className={s.empty}>{rows.length === 0 ? (tab === 'SOLVED' ? 'Nothing solved yet.' : 'No open problems.') : 'Nothing matches the filters.'}</p>}
                    {shown.map(r => (
                        <div key={r.id} className={`${card.card} ${r.status === 'OPEN' ? '' : card.cardSolved}`}>
                            <div className={card.cardHead}>
                                <strong>{r.label}</strong>
                                <span className={`${card.chip} ${r.solution === 'SITE_VISIT' ? card.chipVisit : ''}`}>{SOLUTION_WORDS[r.solution] || r.solution}</span>
                                {projectLink(r)}
                            </div>
                            <p className={card.line}>{r.personName || r.clientName || 'No client name'}{(r.personPhone || r.clientPhone) ? ' | ' + (r.personPhone || r.clientPhone) : ' | no phone'}{place(r) ? ' | ' + place(r) : ''}</p>
                            {r.detail && <p className={card.line}>{r.detail}</p>}
                            <p className={card.meta}>Added by {r.createdBy || '-'} on {fmtDay(r.createdAt)}{r.status !== 'OPEN' ? ' | Solved by ' + (r.solvedBy || '-') + ' on ' + fmtDay(r.solvedAt) + (r.solvedNote ? ': ' + r.solvedNote : '') : ''}</p>
                        </div>
                    ))}
                </div>
            ))}

            {tab === 'VISITS' && (visits === null ? <LoadingState label="Loading site visits" /> : (
                <div className={s.list}>
                    {groups.length === 0 && <p className={s.empty}>No site visits needed.</p>}
                    {groups.map(([where, list]) => (
                        <section key={where} className={s.group}>
                            <h2 className={s.groupHead}><FiMapPin aria-hidden="true" /> {where} <span>{list.length} plot{list.length === 1 ? '' : 's'}</span></h2>
                            {list.map(v => (
                                <div key={v.projectId} className={card.card}>
                                    <div className={card.cardHead}>{projectLink(v)}<strong>{v.clientName || 'No client name'}</strong><span className={card.chip}>{v.clientPhone || 'no phone'}</span></div>
                                    <p className={card.line}>{[v.village, v.parish].filter(Boolean).join(', ') || 'Village not known'}</p>
                                    <ul className={s.reasons}>{(v.reasons || []).map((x, i) => <li key={i}>{x}</li>)}</ul>
                                    {visiting && visiting.projectId === v.projectId ? (
                                        <div className={card.visitBox}>
                                            <input className={card.input} value={visiting.note} maxLength={500} autoFocus aria-label="What was found on the visit"
                                                placeholder="What was found on the visit? (it goes in the Notes and on Recovery)" onChange={e => setVisiting({ ...visiting, note: e.target.value })}
                                                onKeyDown={e => { if (e.key === 'Enter') visitDone(); }} />
                                            <button type="button" className={card.btn} disabled={busy} onClick={visitDone}><FiCheck aria-hidden="true" /> CONFIRM</button>
                                            <button type="button" className={card.btnGhost} onClick={() => setVisiting(null)}>CANCEL</button>
                                        </div>
                                    ) : (
                                        <div className={card.actions}>
                                            <button type="button" className={card.btn} onClick={() => setVisiting({ projectId: v.projectId, note: '' })}><FiCheck aria-hidden="true" /> VISIT DONE</button>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </section>
                    ))}
                </div>
            ))}
        </div>
    );
}
