// PATH: erp-frontend/src/components/common/ProjectProblemsPanel.jsx
// fix289 (David, 5 Nov 2026): the problems of ONE project (the folder's PROBLEMS tab). Add a problem, change what will be
// done about it (the solution), mark it solved with what was done, or (Director and up) remove one added by mistake.
// Every change writes a note in the project's Notes on the server.
import React, { useCallback, useEffect, useState } from 'react';
import { FiAlertTriangle, FiCheck, FiPlus, FiX, FiMapPin } from 'react-icons/fi';
import { Link } from 'react-router-dom';
import problemService, { SOLUTION_WORDS } from '../../services/problemService';
import { errorText } from '../../utils/errorText';
import { fmtDay } from '../../utils/format';
import HardwareSelect from './HardwareSelect';
import SuggestInput from './SuggestInput';
import s from './ProjectProblemsPanel.module.css';

const codeOf = (map, word) => (Object.entries(map).find(([, w]) => w === word) || [])[0];

export default function ProjectProblemsPanel({ projectId, people = [], canWrite, canRemove, onToast, onChanged, onCount }) {
    const [rows, setRows] = useState(null);
    const [kinds, setKinds] = useState({ kinds: [], remembered: [] });
    const [adding, setAdding] = useState(null);      // { kind, label, detail, solution, clientId }
    const [solving, setSolving] = useState(null);    // { id, note, nin, phone, invoice, contract, personId }
    const [removing, setRemoving] = useState(null);  // { id, reason }
    const [showSolved, setShowSolved] = useState(false);
    const [busy, setBusy] = useState(false);
    const toast = useCallback((t, k) => { if (onToast) onToast(t, k); }, [onToast]);

    const load = useCallback(async () => {
        try {
            const list = await problemService.list({ projectId, status: 'ALL' });
            setRows(list || []);
            if (onCount) onCount((list || []).filter(r => r.status === 'OPEN').length);
        } catch (err) { setRows([]); toast(errorText(err), 'error'); }
    }, [projectId, onCount, toast]);

    useEffect(() => {
        let alive = true;
        Promise.resolve().then(() => { if (alive) load(); });
        problemService.kinds().then(k => { if (alive) setKinds(k || { kinds: [], remembered: [] }); }).catch(() => {});
        return () => { alive = false; };
    }, [load]);

    const KIND_WORDS = Object.fromEntries((kinds.kinds || []).map(k => [k.code, k.label]));
    const kindOf = (code) => (kinds.kinds || []).find(k => k.code === code) || {};
    const done = async (fn, okText) => {
        if (busy) return;
        setBusy(true);
        try { await fn(); toast(okText, 'success'); await load(); if (onChanged) onChanged(); return true; }
        catch (err) { toast(errorText(err), 'error'); return false; }
        finally { setBusy(false); }
    };

    const saveNew = async () => {
        const a = adding;
        if (!a.kind) { toast('Pick the problem.', 'error'); return; }
        if (a.kind === 'OTHER' && !String(a.label || '').trim()) { toast('Write what the other problem is.', 'error'); return; }
        const ok = await done(() => problemService.add({ projectId, kind: a.kind, label: a.label, detail: a.detail, solution: a.solution, clientId: a.clientId || '' }), 'Problem added. A note was written.');
        if (ok) setAdding(null);
    };

    // fix291 (David): solving a NIN / phone / number problem takes the real value and puts it on the project in the same step
    const FIX_WORDS = { nin: 'Real NIN', phone: 'Real phone number', invoice: 'Real invoice number', contract: 'Real contract number' };
    const FIX_HINTS = { nin: 'CM12345678ABCD', phone: '0772 123 456', invoice: 'Leave empty to keep it', contract: 'Leave empty to keep it' };
    const fixOf = (r) => (kindOf(r.kind).fix || []);
    const confirmSolve = (r) => {
        const values = {};
        ['nin', 'phone', 'invoice', 'contract', 'personId'].forEach(k => { if (solving[k] && String(solving[k]).trim()) values[k] = String(solving[k]).trim(); });
        const typed = ['nin', 'phone', 'invoice', 'contract'].some(k => values[k]);
        if (!typed && String(solving.note || '').trim().length < 3) { toast(fixOf(r).length ? 'Type the real value, or write what was done.' : 'Write what was done to solve it.', 'error'); return; }
        if (typed && (values.nin || values.phone) && !r.clientId && people.length > 1 && !values.personId) { toast('Pick which person the number belongs to.', 'error'); return; }
        done(() => problemService.solve(r.id, solving.note, values), typed ? 'Saved on the project and solved. A note was written.' : 'Problem solved. A note was written.')
            .then(ok => ok && setSolving(null));
    };
    const open = (rows || []).filter(r => r.status === 'OPEN');
    const solved = (rows || []).filter(r => r.status !== 'OPEN');
    const personWords = Object.fromEntries(people.map(p => [p.id, p.name]));

    const card = (r) => (
        <div key={r.id} className={`${s.card} ${r.status === 'OPEN' ? '' : s.cardSolved}`}>
            <div className={s.cardHead}>
                <strong>{r.label}</strong>
                <span className={`${s.chip} ${r.solution === 'SITE_VISIT' ? s.chipVisit : ''}`}>{r.solution === 'SITE_VISIT' && <FiMapPin aria-hidden="true" />} {SOLUTION_WORDS[r.solution] || r.solution}</span>
                {r.status !== 'OPEN' && <span className={`${s.chip} ${s.chipDone}`}>SOLVED</span>}
                {r.autoAdded && <span className={s.chipSoft}>from a tick</span>}
            </div>
            {(r.personName || r.clientId) && <p className={s.line}>Person: {r.personName || personWords[r.clientId] || 'a client'}{r.personPhone ? ' (' + r.personPhone + ')' : ''}</p>}
            {r.detail && <p className={s.line}>{r.detail}</p>}
            {r.linkedProjectId && <p className={s.line}>Other project: <Link className={s.link} to={'/folder/' + r.linkedProjectId}>#{r.linkedProjectIndex || 'open it'}</Link></p>}
            <p className={s.meta}>Added by {r.createdBy || '-'} on {fmtDay(r.createdAt)}{r.status !== 'OPEN' ? ' | Solved by ' + (r.solvedBy || '-') + ' on ' + fmtDay(r.solvedAt) + (r.solvedNote ? ': ' + r.solvedNote : '') : ''}</p>
            {r.status === 'OPEN' && canWrite && (
                <div className={s.actions}>
                    <div className={s.solutionPick}>
                        <HardwareSelect compact label="" placeholder="Solution" options={Object.values(SOLUTION_WORDS)} value={SOLUTION_WORDS[r.solution]}
                            onChange={w => { const v = codeOf(SOLUTION_WORDS, w); if (v && v !== r.solution) done(() => problemService.update(r.id, { solution: v }), 'Solution changed: ' + w + '.'); }} />
                    </div>
                    {solving && solving.id === r.id
                        ? (<div className={s.solveBox}>
                            {fixOf(r).length > 0 && !r.clientId && people.length > 1 && fixOf(r).some(k => k === 'nin' || k === 'phone') && (
                                <HardwareSelect compact label="" placeholder="Which person" options={people.map(p => p.name)} value={personWords[solving.personId] || ''}
                                    onChange={w => { const p = people.find(x => x.name === w); setSolving({ ...solving, personId: p ? p.id : '' }); }} />)}
                            {fixOf(r).map((k, i) => (
                                <input key={k} className={s.input} value={solving[k] || ''} maxLength={k === 'phone' ? 60 : 80} autoFocus={i === 0} aria-label={FIX_WORDS[k]}
                                    placeholder={FIX_WORDS[k] + ' (' + FIX_HINTS[k] + ')'}
                                    onChange={e => setSolving({ ...solving, [k]: k === 'nin' ? e.target.value.toUpperCase().replace(/\s+/g, '') : e.target.value })}
                                    onKeyDown={e => { if (e.key === 'Enter') confirmSolve(r); }} />
                            ))}
                            <input className={s.input} value={solving.note} maxLength={500} autoFocus={fixOf(r).length === 0} aria-label="What was done to solve it"
                                placeholder={fixOf(r).length ? 'What was done? (optional when the real value is typed)' : 'What was done to solve it?'}
                                onChange={e => setSolving({ ...solving, note: e.target.value })}
                                onKeyDown={e => { if (e.key === 'Enter') confirmSolve(r); }} />
                            <span className={s.solveBtns}>
                                <button type="button" className={s.btn} disabled={busy} onClick={() => confirmSolve(r)}><FiCheck /> CONFIRM</button>
                                <button type="button" className={s.btnGhost} onClick={() => setSolving(null)}>CANCEL</button>
                            </span>
                        </div>)
                        : <button type="button" className={s.btn} onClick={() => setSolving({ id: r.id, note: '', nin: '', phone: '', invoice: '', contract: '', personId: '' })}><FiCheck /> {fixOf(r).length ? 'FIX AND SOLVE' : 'SOLVED'}</button>}
                    {canRemove && !(solving && solving.id === r.id) && (removing && removing.id === r.id
                        ? (<>
                            <input className={s.input} value={removing.reason} maxLength={300} aria-label="Why remove it" placeholder="Why remove it? (added by mistake...)"
                                onChange={e => setRemoving({ ...removing, reason: e.target.value })} />
                            <button type="button" className={s.btnDanger} disabled={busy} onClick={() => done(() => problemService.remove(r.id, removing.reason), 'Problem removed.').then(ok => ok && setRemoving(null))}>REMOVE</button>
                            <button type="button" className={s.btnGhost} onClick={() => setRemoving(null)}>CANCEL</button>
                        </>)
                        : <button type="button" className={s.btnGhost} onClick={() => setRemoving({ id: r.id, reason: '' })}><FiX /> REMOVE</button>)}
                </div>
            )}
        </div>
    );

    return (
        <div className={s.wrap}>
            <div className={s.top}>
                <span className={s.count}><FiAlertTriangle aria-hidden="true" /> {rows === null ? 'Loading...' : open.length === 0 ? 'No open problems.' : open.length + ' open problem' + (open.length === 1 ? '' : 's') + '.'}</span>
                {canWrite && !adding && <button type="button" className={s.btn} onClick={() => setAdding({ kind: '', label: '', detail: '', solution: '', clientId: '' })}><FiPlus /> ADD A PROBLEM</button>}
            </div>
            {adding && (
                <div className={s.addBox}>
                    <div className={s.addGrid}>
                        <HardwareSelect label="Problem" required options={(kinds.kinds || []).map(k => k.label)} value={KIND_WORDS[adding.kind] || ''} placeholder="Pick one"
                            onChange={w => { const k = (kinds.kinds || []).find(x => x.label === w); setAdding({ ...adding, kind: k ? k.code : '', solution: adding.solution || (k ? k.solution : '') }); }} />
                        {adding.kind === 'OTHER' && (<div className={s.field}><label className={s.label}>What is it?</label>
                            <SuggestInput className={s.input} value={adding.label} aria-label="Other problem" hint="Problems used before"
                                suggestions={(kinds.remembered || []).filter(w => !adding.label || w.toLowerCase().includes(String(adding.label).toLowerCase())).slice(0, 12).map(w => ({ key: w, value: w }))}
                                onChange={v => setAdding({ ...adding, label: v })} onPick={sg => setAdding({ ...adding, label: (sg && sg.value) || '' })} /></div>)}
                        {kindOf(adding.kind).person && people.length > 0 && (
                            <HardwareSelect label="Which person" options={people.map(p => p.name)} value={personWords[adding.clientId] || ''} placeholder="Pick the person"
                                onChange={w => { const p = people.find(x => x.name === w); setAdding({ ...adding, clientId: p ? p.id : '' }); }} />)}
                        <div className={s.field}><label className={s.label}>Details</label>
                            <input className={s.input} value={adding.detail} maxLength={500} aria-label="Problem details" placeholder="What exactly is wrong? (optional)"
                                onChange={e => setAdding({ ...adding, detail: e.target.value })} /></div>
                        <HardwareSelect label="Solution" options={Object.values(SOLUTION_WORDS)} value={SOLUTION_WORDS[adding.solution] || ''} placeholder="What will be done"
                            onChange={w => setAdding({ ...adding, solution: codeOf(SOLUTION_WORDS, w) || '' })} />
                    </div>
                    <div className={s.actions}>
                        <button type="button" className={s.btn} disabled={busy} onClick={saveNew}><FiCheck /> SAVE PROBLEM</button>
                        <button type="button" className={s.btnGhost} onClick={() => setAdding(null)}>CANCEL</button>
                    </div>
                </div>
            )}
            {open.map(card)}
            {solved.length > 0 && (<>
                <button type="button" className={s.btnGhost} aria-expanded={showSolved} onClick={() => setShowSolved(v => !v)}>{showSolved ? 'HIDE' : 'SHOW'} SOLVED ({solved.length})</button>
                {showSolved && solved.map(card)}
            </>)}
        </div>
    );
}
