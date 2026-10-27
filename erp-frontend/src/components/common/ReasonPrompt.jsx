// PATH: erp-frontend/src/components/common/ReasonPrompt.jsx
import React, { useEffect, useRef, useState } from 'react';
import { FiTrash2, FiAlertCircle } from 'react-icons/fi';
import HardwareModal from './HardwareModal';
import modalStyles from './HardwareModal.module.css';
import styles from './ReasonPrompt.module.css';
import { REASON_MIN } from './useReasonPrompt';
import errorText from '../../utils/errorText';

/** fix223: the "delete -- why?" window. State comes from useReasonPrompt(). */
const ReasonPrompt = ({ state, onClose }) => {
    const [text, setText] = useState('');
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState('');
    const boxRef = useRef(null);
    useEffect(() => {
        if (!state.open) return;
        setText(''); setErr(''); setBusy(false);
        const t = setTimeout(() => boxRef.current && boxRef.current.focus(), 60);
        return () => clearTimeout(t);
    }, [state.open, state.seq]);

    const ready = text.trim().length >= REASON_MIN;
    const submit = async () => {
        if (busy) return;
        if (!ready) { setErr('Type why this is being deleted (a few words).'); boxRef.current && boxRef.current.focus(); return; }
        setBusy(true); setErr('');
        try { await state.run(text.trim()); onClose(); }
        catch (e) { setErr(errorText(e)); }
        finally { setBusy(false); }
    };
    const picks = state.picks || [];
    return (
        <HardwareModal isOpen={!!state.open} stacked lockBackdrop onClose={() => { if (!busy) onClose(); }} title={state.title || 'DELETE'}>
            <div className={styles.modalBody}>
            {state.message && <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>{state.message}</div>}
            <div className={modalStyles.modalField}>
                <label className={modalStyles.modalLabel} htmlFor="delete-reason">WHY? <span className={styles.need}>(needed)</span></label>
                <textarea id="delete-reason" ref={boxRef} className={`${modalStyles.modalTextarea} ${err ? styles.boxErr : ''}`} rows={3} maxLength={500}
                    value={text} onChange={e => { setText(e.target.value); if (err) setErr(''); }}
                    onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submit(); }}
                    placeholder="A few words, e.g. uploaded by mistake" disabled={busy} />
                {picks.length > 0 && (
                    <div className={styles.picks} role="group" aria-label="Common reasons">
                        {picks.map(p => (
                            <button key={p} type="button" className={`${styles.pick} ${text === p ? styles.pickOn : ''}`}
                                onClick={() => { setText(p); setErr(''); }} disabled={busy} title="Use this reason">{p}</button>
                        ))}
                    </div>
                )}
                {err && <p className={styles.err} role="alert"><FiAlertCircle aria-hidden="true" /> {err}</p>}
                <p className={modalStyles.modalHint}>The reason is kept in the audit log{state.noteKept ? ' and in the project’s Notes' : ''}.</p>
            </div>
            </div>
            <div className={modalStyles.modalFooter}>
                <button type="button" className={styles.danger} onClick={submit} disabled={busy} aria-disabled={!ready}>
                    <FiTrash2 aria-hidden="true" /> {busy ? 'DELETING...' : (state.okLabel || 'DELETE')}
                </button>
            </div>
        </HardwareModal>
    );
};

export default ReasonPrompt;
