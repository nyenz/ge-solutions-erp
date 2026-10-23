// PATH: erp-frontend/src/components/notes/NotesTimeline.jsx
// fix215 (David): ONE Notes timeline -- typed notes, decisions (every reason window), money (payments with their method),
// events (stages, problem flags, hand-overs) and recovery calls, newest first. Summary first: each line is one sentence;
// press it to open the details (a dropdown). Filter pills on top, a search box, pinned notes stay on top, a note may carry
// a follow-up day (the bell reminds the office that morning) and one file. Money lines only reach the Manager and above
// (the server leaves them out for everyone else). Used on the project Folder (scope "project") and the client page ("client").
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiX, FiChevronDown, FiEdit3, FiTrash2, FiPaperclip, FiClock, FiDollarSign, FiFileText, FiFlag,
    FiPhoneCall, FiCheckCircle, FiStar, FiAlertTriangle, FiExternalLink } from 'react-icons/fi';
import TabDock, { accentOf } from '../common/TabDock';
import HardwareModal from '../common/HardwareModal';
import HardwareDatePicker from '../common/HardwareDatePicker';
import modalStyles from '../common/HardwareModal.module.css';
import timelineService from '../../services/timelineService';
import { errorText } from '../../utils/errorText';
import { prepareUploads, DOC_ACCEPT } from '../../utils/imageShrink';
import { KINDS, TOPICS, kindWord, todayISO, followUpState, visibleRows, countKinds, summaryOf, fmtWhen } from '../../utils/timeline';
import ReasonPrompt from '../common/ReasonPrompt';   // fix223
import { useReasonPrompt, DELETE_PICKS } from '../common/useReasonPrompt';
import styles from './NotesTimeline.module.css';

const NOTE_MAX = 2000;
const PAGE = 30;
const ICON = { NOTE: FiFileText, MONEY: FiDollarSign, REASON: FiFlag, EVENT: FiCheckCircle, CALL: FiPhoneCall };
const plusDays = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return todayISO(d); };
const EMPTY_FORM = { id: null, content: '', topic: '', followUpOn: '', pinned: false, file: null, fileNote: '' };

/**
 * scope     'project' | 'client'
 * id        the project id or the client id
 * canWrite  false on a deleted project (read only)
 * refreshKey  anything that changes when the page reloads its data (a payment or a reason was just saved)
 * onOpenDoc   (documentId) => void -- opens an attached file (the Folder has the preview window)
 * onToast     (text, kind) => void
 */
const NotesTimeline = ({ scope = 'project', id, canWrite = true, refreshKey, onOpenDoc, onToast }) => {
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loadErr, setLoadErr] = useState('');
    const [kind, setKind] = useState('ALL');
    const [search, setSearch] = useState('');
    const [projectFilter, setProjectFilter] = useState('');
    const [open, setOpen] = useState(() => new Set());
    const [shown, setShown] = useState(PAGE);
    const [form, setForm] = useState(null);           // the add / edit window
    const [formErr, setFormErr] = useState('');
    const [busy, setBusy] = useState(false);
    const { reasonState, askReason, closeReason } = useReasonPrompt();   // fix223: deleting a note asks WHY
    const fileRef = useRef(null);
    const toast = useCallback((t, k) => { if (onToast) onToast(t, k); }, [onToast]);

    const load = useCallback(async () => {
        if (!id) return;
        try {
            const d = scope === 'client' ? await timelineService.client(id) : await timelineService.project(id);
            setData(d); setLoadErr('');
        } catch (e) { setLoadErr(errorText(e)); }
    }, [scope, id]);
    useEffect(() => { load(); }, [load, refreshKey]);

    const rows = useMemo(() => (data && data.entries) || [], [data]);
    const canSeeMoney = !!(data && data.canSeeMoney);
    const counts = useMemo(() => countKinds(rows), [rows]);
    const pills = KINDS.filter(k => !k.money || canSeeMoney).map(k => ({ ...k, count: counts[k.key] || 0 }));
    const { pinned, rest } = useMemo(() => visibleRows(rows, kind, search, projectFilter), [rows, kind, search, projectFilter]);
    const projects = (data && data.projects) || [];
    const today = todayISO();
    const dueCount = rows.filter(r => r.kind === 'NOTE' && followUpState(r.followUpOn, today) === 'due').length;
    // the client page writes a note on one of the client's projects: the one picked in the filter, else the only one
    const writeProject = scope === 'project' ? id : (projectFilter || (projects.length === 1 ? projects[0].id : ''));

    const toggle = (key) => setOpen(s => { const n = new Set(s); if (n.has(key)) n.delete(key); else n.add(key); return n; });

    // ── add / edit ──────────────────────────────────────────────────────────
    const startAdd = () => { setFormErr(''); setForm({ ...EMPTY_FORM }); };
    const startEdit = (r) => { setFormErr(''); setForm({ ...EMPTY_FORM, id: r.id, content: r.text || '', topic: r.topic || '', followUpOn: r.followUpOn ? String(r.followUpOn).slice(0, 10) : '' }); };
    const closeForm = () => { if (!busy) { setForm(null); setFormErr(''); } };
    const pickFile = async (f) => {
        if (!f) return;
        const { ok, bad } = await prepareUploads([f]);
        if (bad.length) { setFormErr('NOT ADDED: ' + bad.join('; ').toUpperCase()); return; }
        setForm(x => ({ ...x, file: ok[0].file, fileNote: ok[0].note }));
    };
    const save = async () => {
        if (busy || !form) return;
        const text = form.content.trim();
        if (text.length < 2) { setFormErr('WRITE THE NOTE FIRST (AT LEAST 2 CHARACTERS).'); return; }
        if (text.length > NOTE_MAX) { setFormErr('TOO LONG: ' + text.length + ' CHARACTERS. THE LIMIT IS ' + NOTE_MAX + '.'); return; }
        if (form.followUpOn && form.followUpOn < today && (!form.id)) { setFormErr('THE FOLLOW-UP DAY CANNOT BE IN THE PAST.'); return; }
        if (!form.id && !writeProject) { setFormErr('PICK THE PROJECT THIS NOTE IS ABOUT (THE PROJECT BUTTONS ABOVE THE LIST).'); return; }
        setBusy(true); setFormErr('');
        try {
            if (form.id) await timelineService.editNote(form.id, { content: text, topic: form.topic.trim(), followUpOn: form.followUpOn });
            else await timelineService.addNote(writeProject, { content: text, topic: form.topic.trim(), followUpOn: form.followUpOn, pinned: form.pinned, file: form.file });
            setForm(null);
            await load();
            toast(form.id ? 'Note changed' : 'Note saved', 'success');
        } catch (e) { setFormErr(errorText(e)); }
        finally { setBusy(false); }
    };
    const pin = async (r) => {
        try { await timelineService.pin(r.id, !r.pinned); await load(); toast(r.pinned ? 'Note unpinned' : 'Note pinned to the top', 'success'); }
        catch (e) { toast(errorText(e), 'error'); }
    };
    const askDelete = (r) => askReason({
        title: 'DELETE NOTE', okLabel: 'DELETE NOTE', picks: DELETE_PICKS.NOTE, noteKept: true,
        message: 'Delete this note? The audit trail keeps its words.',
        run: async (reason) => { await timelineService.remove(r.id, reason); await load(); toast('Note deleted', 'warn'); },
    });

    // ── one line ────────────────────────────────────────────────────────────
    const renderRow = (r) => {
        const key = r.source + ':' + r.id;
        const isOpen = open.has(key);
        const Icon = ICON[r.kind] || FiFileText;
        const fu = r.kind === 'NOTE' ? followUpState(r.followUpOn, today) : '';
        const negative = r.kind === 'MONEY' && Number(r.amount) < 0;
        return (
            <li key={key} className={`${styles.row} ${styles['k_' + r.kind] || ''} ${isOpen ? styles.rowOpen : ''}`} data-tone={r.tone || undefined}>
                <button type="button" className={styles.rowHead} aria-expanded={isOpen} onClick={() => toggle(key)}
                    title={isOpen ? 'Hide the details' : 'Show the details'}>
                    <span className={styles.icon} aria-hidden="true">{r.kind === 'EVENT' && r.tone === 'bad' ? <FiAlertTriangle /> : <Icon />}</span>
                    <span className={styles.main}>
                        <span className={styles.titleLine}>
                            <strong className={styles.title}>{r.title}</strong>
                            {r.pinned && <span className={styles.chipPin} title="Pinned: stays at the top"><FiStar aria-hidden="true" /> PINNED</span>}
                            {fu && <span className={fu === 'due' ? styles.chipDue : styles.chipSoon} title={fu === 'due' ? 'The follow-up day is today (or has passed).' : 'The day to follow this up.'}>
                                <FiClock aria-hidden="true" /> {fu === 'due' ? 'FOLLOW UP NOW' : 'FOLLOW UP ' + fmtWhen(r.followUpOn).toUpperCase()}</span>}
                            {r.documentId && <span className={styles.chipFile} title="A file is attached"><FiPaperclip aria-hidden="true" /></span>}
                            {scope === 'client' && r.projectIndex && <span className={styles.chipProject} title="The project this line is about">#{r.projectIndex}</span>}
                        </span>
                        {!isOpen && summaryOf(r) && <span className={`${styles.summary} ${negative ? styles.summaryNeg : ''}`}>{summaryOf(r)}</span>}
                    </span>
                    <span className={styles.meta}>
                        <time dateTime={r.at} title={fmtWhen(r.at, true)}>{fmtWhen(r.at)}</time>
                        <span className={styles.by}>{kindWord(r.kind)} · {r.by || 'SYSTEM'}</span>
                    </span>
                    <FiChevronDown className={styles.chev} aria-hidden="true" />
                </button>
                {isOpen && (
                    <div className={styles.body}>
                        {r.text && <p className={styles.text}>{r.kind === 'REASON' ? <><span className={styles.lbl}>Reason: </span>{r.text}</> : r.text}</p>}
                        {r.detail && <p className={styles.detail}>{r.detail}</p>}
                        <p className={styles.small}>{fmtWhen(r.at, true)} · {r.by || 'SYSTEM'}{r.edited ? ' · changed later' : ''}{r.locked ? ' · kept as a record (cannot be changed)' : ''}</p>
                        <div className={styles.actions}>
                            {r.documentId && (onOpenDoc
                                ? <button type="button" className={styles.act} onClick={() => onOpenDoc(r.documentId)} title="Open the attached file"><FiPaperclip aria-hidden="true" /> OPEN FILE</button>
                                : r.projectId && <button type="button" className={styles.act} onClick={() => navigate('/folder/' + r.projectId + '#notes')} title="The file is in the project's Documents"><FiExternalLink aria-hidden="true" /> OPEN PROJECT</button>)}
                            {scope === 'client' && r.projectId && !r.documentId && (
                                <button type="button" className={styles.act} onClick={() => navigate('/folder/' + r.projectId + '#notes')} title="Open this project's folder"><FiExternalLink aria-hidden="true" /> OPEN PROJECT</button>)}
                            {r.kind === 'NOTE' && canWrite && (
                                <button type="button" className={styles.act} onClick={() => pin(r)} title={r.pinned ? 'Let it move down with the others' : 'Keep this note at the top'}>
                                    <FiStar aria-hidden="true" /> {r.pinned ? 'UNPIN' : 'PIN TO TOP'}</button>)}
                            {r.kind === 'NOTE' && r.editable && canWrite && (<>
                                <button type="button" className={styles.act} onClick={() => startEdit(r)} title="Change the words, topic or follow-up day"><FiEdit3 aria-hidden="true" /> EDIT</button>
                                <button type="button" className={`${styles.act} ${styles.actDanger}`} onClick={() => askDelete(r)} title="Delete this note. The audit trail keeps its words."><FiTrash2 aria-hidden="true" /> DELETE</button>
                            </>)}
                        </div>
                    </div>
                )}
            </li>
        );
    };

    if (loadErr && !data) {
        return (<div className={styles.wrap}><div className={styles.err} role="alert">{loadErr}
            <button type="button" className={styles.act} onClick={load} title="Load the notes again">TRY AGAIN</button></div></div>);
    }
    if (!data) return <div className={styles.wrap}><p className={styles.loading}>Loading the notes...</p></div>;

    const list = rest.slice(0, shown);
    return (
        <div className={styles.wrap}>
            <div className={styles.top}>
                <TabDock items={pills} value={kind} onChange={v => { setKind(v); setShown(PAGE); }} label="Show only" />
                <div className={styles.tools}>
                    <label className={styles.search}>
                        <FiSearch aria-hidden="true" />
                        <input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search the notes, names, amounts..." aria-label="Search the notes" />
                        {search && <button type="button" onClick={() => setSearch('')} aria-label="Clear the search" title="Clear the search"><FiX aria-hidden="true" /></button>}
                    </label>
                    {canWrite && <button type="button" className={styles.add} onClick={startAdd} title="Write a note: what happened, what was agreed, what comes next."><FiPlus aria-hidden="true" /> ADD NOTE</button>}
                </div>
                {scope === 'client' && projects.length > 1 && (
                    <div className={styles.projects} role="group" aria-label="Project">
                        <button type="button" aria-pressed={!projectFilter} className={!projectFilter ? styles.projOn : styles.proj} onClick={() => setProjectFilter('')} title="Every project of this client">ALL PROJECTS</button>
                        {projects.map(p => (
                            <button key={p.id} type="button" aria-pressed={projectFilter === p.id} className={projectFilter === p.id ? styles.projOn : styles.proj}
                                onClick={() => setProjectFilter(projectFilter === p.id ? '' : p.id)} title={'Only project #' + p.index + ' (a new note goes on this project)'}>#{p.index}</button>
                        ))}
                    </div>
                )}
                {dueCount > 0 && <p className={styles.due} role="status"><FiClock aria-hidden="true" /> {dueCount} note{dueCount === 1 ? '' : 's'} to follow up today.</p>}
                {!canSeeMoney && <p className={styles.hint}>Payments and money decisions are shown to the Manager and above.</p>}
            </div>

            <div data-tab-accent={accentOf(pills, kind)}>
                {pinned.length > 0 && (<>
                    <div className={styles.groupLbl}>PINNED</div>
                    <ul className={styles.list}>{pinned.map(renderRow)}</ul>
                </>)}
                {pinned.length > 0 && rest.length > 0 && <div className={styles.groupLbl}>EVERYTHING ELSE</div>}
                {rest.length === 0 && pinned.length === 0
                    ? <p className={styles.empty}>{search ? 'Nothing matches "' + search + '".' : kind === 'ALL' ? 'Nothing written yet. Press ADD NOTE to write the first note.' : 'Nothing of this kind yet.'}</p>
                    : <ul className={styles.list}>{list.map(renderRow)}</ul>}
                {rest.length > shown && (
                    <button type="button" className={styles.more} onClick={() => setShown(s => s + PAGE)} title="Show older lines">SHOW {Math.min(PAGE, rest.length - shown)} OLDER</button>
                )}
            </div>

            <HardwareModal isOpen={!!form} lockBackdrop onClose={closeForm} title={form && form.id ? 'CHANGE NOTE' : 'ADD NOTE'}>
                {form && (<>
                    <div className={modalStyles.modalField}>
                        <label className={modalStyles.modalLabel}>TOPIC (OPTIONAL)</label>
                        <div className={styles.topics}>
                            {TOPICS.map(t => (
                                <button key={t} type="button" className={form.topic === t ? styles.topicOn : styles.topic} aria-pressed={form.topic === t}
                                    onClick={() => setForm(x => ({ ...x, topic: x.topic === t ? '' : t }))} title={'Mark this note as: ' + t}>{t}</button>
                            ))}
                        </div>
                    </div>
                    <div className={modalStyles.modalField}>
                        <label className={modalStyles.modalLabel} htmlFor="note-text">THE NOTE</label>
                        <textarea id="note-text" className={modalStyles.modalTextarea} rows={5} value={form.content} autoFocus maxLength={NOTE_MAX + 200}
                            onChange={e => { setForm(x => ({ ...x, content: e.target.value })); if (formErr) setFormErr(''); }}
                            placeholder="What happened, what was agreed, what comes next..." />
                        <small className={modalStyles.modalHint}>{form.content.trim().length}/{NOTE_MAX}</small>
                    </div>
                    <div className={modalStyles.modalField}>
                        <label className={modalStyles.modalLabel} htmlFor="note-follow">FOLLOW UP ON (OPTIONAL)</label>
                        <HardwareDatePicker id="note-follow" block className={modalStyles.modalInput} value={form.followUpOn} min={today} ariaLabel="Follow up on"
                            onChange={v => setForm(x => ({ ...x, followUpOn: v }))} />
                        <div className={styles.quick}>
                            <button type="button" className={styles.topic} onClick={() => setForm(x => ({ ...x, followUpOn: plusDays(1) }))} title="Tomorrow">TOMORROW</button>
                            <button type="button" className={styles.topic} onClick={() => setForm(x => ({ ...x, followUpOn: plusDays(7) }))} title="One week from today">IN 1 WEEK</button>
                            <button type="button" className={styles.topic} onClick={() => setForm(x => ({ ...x, followUpOn: plusDays(30) }))} title="One month from today">IN 1 MONTH</button>
                            {form.followUpOn && <button type="button" className={styles.topic} onClick={() => setForm(x => ({ ...x, followUpOn: '' }))} title="No follow-up day">CLEAR</button>}
                        </div>
                        <small className={modalStyles.modalHint}>That morning the bell reminds the office, and the note shows FOLLOW UP NOW.</small>
                    </div>
                    {!form.id && (<>
                        <div className={modalStyles.modalField}>
                            <label className={modalStyles.modalLabel}>FILE (OPTIONAL)</label>
                            <input ref={fileRef} type="file" accept={DOC_ACCEPT} style={{ display: 'none' }} aria-hidden="true" tabIndex={-1}
                                onChange={e => { const f = e.target.files && e.target.files[0]; e.target.value = ''; pickFile(f); }} />
                            {form.file
                                ? <div className={styles.file}><FiPaperclip aria-hidden="true" /><span>{form.file.name}{form.fileNote && <small> {form.fileNote}</small>}</span>
                                    <button type="button" onClick={() => setForm(x => ({ ...x, file: null, fileNote: '' }))} aria-label="Remove the file" title="Remove the file"><FiX aria-hidden="true" /></button></div>
                                : <button type="button" className={`${styles.topic} ${styles.fileBtn}`} onClick={() => fileRef.current && fileRef.current.click()} title="A letter, a photo, a screenshot of a message..."><FiPaperclip aria-hidden="true" /> ATTACH A FILE</button>}
                            <small className={modalStyles.modalHint}>Also filed in Documents under Note Attachments.</small>
                        </div>
                        <label className={styles.pinBox} title="Keep this note at the top of the list">
                            <input type="checkbox" checked={form.pinned} onChange={e => setForm(x => ({ ...x, pinned: e.target.checked }))} /> Pin to the top
                        </label>
                    </>)}
                    {formErr && <div className={styles.err} role="alert">{formErr}</div>}
                    <div className={modalStyles.modalFooter}>
                        <button type="button" className={modalStyles.modalBtnPrimary} onClick={save} disabled={busy}>{busy ? 'SAVING...' : form.id ? 'SAVE CHANGES' : 'SAVE NOTE'}</button>
                    </div>
                </>)}
            </HardwareModal>

            <ReasonPrompt state={reasonState} onClose={closeReason} />
        </div>
    );
};

export default NotesTimeline;
