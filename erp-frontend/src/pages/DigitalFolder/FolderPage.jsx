// PATH: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
// fix167: folder page review pass. Ticks show in view AND edit mode (and arrive from New Project), popups show their
// own red errors without blur or a duplicate toast, every money / flag / hand-over action needs a reason, who paid
// is recorded per owner, storage fees paid vs unpaid are shown, set-aside fees are visible, dead code removed.
import { roleFlags } from '../../utils/roles';
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiUnlock, FiX, FiMap, FiUsers, FiCreditCard,
    FiUploadCloud, FiFileText, FiClock,
    FiCheckCircle, FiTrash2, FiEdit3, FiChevronDown,
    FiPhoneCall, FiMail, FiMapPin, FiShield,
    FiInfo, FiAlertTriangle, FiAlertOctagon,
    FiCheckSquare, FiPrinter, FiAlertCircle, FiSave,
    FiDollarSign, FiActivity, FiHome, FiArchive,
    FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp, FiPaperclip, FiExternalLink
} from 'react-icons/fi';
import landService from '../../services/landService';
import statusTemplateService from '../../services/statusTemplateService';
import { projectTypeOf, showsTitle } from '../../constants/projectTypes';
import folderPortalService from '../../services/folderPortalService';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import NinMismatchModal from '../../components/common/NinMismatchModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import recoveryService from '../../services/recoveryService';
import predictionService from '../../services/predictionService';
import clientService from '../../services/clientService';
import { normalizePhones } from '../../utils/phone';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModalSelect from '../../components/common/HardwareModalSelect';
import HardwareDatePicker from '../../components/common/HardwareDatePicker';
import ErrorMessage from '../../components/common/ErrorMessage';
import CornerDecor from '../../components/ui/CornerDecor';
import { DocList, DocGroup, DocRow, DocDropzone } from '../../components/common/DocParts';
import { parseNote } from './noteTags';
import styles from './FolderPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

// fix165: a payment can NEVER be saved without its receipt scan (the server refuses it too).
const NOTE_MAX = 2000;
const SCAN_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'webp'];
// fix173: the default monthly storage fee is read from the server (landService.getStorageFeeDefault); no copy of it lives here.
const fileExt = (name) => { const m = String(name || '').toLowerCase().match(/[.]([a-z0-9]{1,6})$/); return m ? m[1] : ''; };
// fix165: ONE place that turns any failed request into a sentence a person can read (server words + HTTP number).
const errText = (err) => {
    const st = err && err.response && err.response.status;
    if (!st) return 'NO REPLY FROM THE SERVER (internet is down, or the server is waking up). Nothing was saved. Wait a few seconds and try again.';
    const d = err.response.data;
    let msg = '';
    if (d && typeof d === 'object') msg = d.message || d.error || '';
    else if (typeof d === 'string' && d.length < 300) msg = d;
    if (!msg) msg = err.message || 'Unknown error';
    return msg + ' (HTTP ' + st + ')';
};
// fix165/167: red error box INSIDE a popup. When a popup shows its own error, no toast is shown as well.
const ModalError = ({ text }) => (text ? (<div className={styles.modalErr} role="alert">
    <FiAlertCircle className={styles.modalErrIcon} aria-hidden="true" /><span>{text}</span></div>) : null);

const fmt = (n) => Number(n || 0).toLocaleString();
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : '');
const fmtDateTime = (d) => (d ? new Date(d).toLocaleString(undefined, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '');
// fix167: the server sends isCompleted (fix167) -- older answers said "completed"
const statusDone = (s) => !!(s && (s.isCompleted ?? s.completed));
const todayISO = () => new Date().toISOString().slice(0, 10);

const TOAST_ICONS = { success: <FiCheckSquare aria-hidden="true" />, error: <FiAlertCircle aria-hidden="true" />, warn: <FiAlertTriangle aria-hidden="true" />, info: <FiInfo aria-hidden="true" /> };
const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        // fix165: an error stays on screen for at least 12 seconds (or until closed) so it can be read
        const ms = type === 'error' && duration > 0 ? Math.max(duration, 12000) : duration;
        if (ms > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), ms);
    }, []);
    const dismissToast = useCallback((id) => setToasts(prev => prev.filter(t => t.id !== id)), []);
    return { toasts, toast, dismissToast };
};
const ToastContainer = ({ toasts, onDismiss }) => {
    if (typeof document === 'undefined') return null;
    return createPortal(<div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
        {toasts.map(t => (<div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
            <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
            <span className={styles.toastMsg}>{t.message}</span>
            <button type="button" className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss" title="Close"><FiX aria-hidden="true" /></button>
        </div>))}
    </div>, document.body);
};
const SavingOverlay = ({ visible }) => {
    if (!visible || typeof document === 'undefined') return null;
    return createPortal(<div className={styles.savingOverlay} role="status" aria-label="Saving">
        <div className={styles.savingSpinner} aria-hidden="true" /><span className={styles.savingLabel}>SAVING...</span>
    </div>, document.body);
};
const DrawerHeader = ({ label, count, isOpen, onClick, icon: Icon }) => (
    <div className={styles.drawerHeader} onClick={onClick} role="button" tabIndex={0} aria-expanded={isOpen}
        aria-label={`${label} section, ${isOpen ? 'collapse' : 'expand'}`} title={isOpen ? 'Click to fold this section' : 'Click to open this section'}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}>
        <div className={styles.drawerTitle}>{Icon && <Icon className={styles.drawerIcon} aria-hidden="true" />}{label}
            {count !== undefined && <span className={styles.drawerCount}>{count}</span>}</div>
        <FiChevronDown className={`${styles.chevron} ${isOpen ? styles.rotated : ''}`} aria-hidden="true" />
    </div>
);
const SmartInput = React.forwardRef(({ label, value, onChange, onBlur, placeholder, suggestions = [], inputMode, maxLength, hint, showCaps, required = false, error = null, id: propId }, ref) => {
    const inputId = propId || 'inp-' + (label || '').replace(/\W/g, '-').toLowerCase();
    const datalistId = suggestions.length ? 'dl-' + inputId : undefined;
    return (<div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
        <div className={styles.inputLabelRow}>
            <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar} aria-hidden="true"> *</span>}</label>
            {showCaps && <span className={styles.capsBadge} title="Typed in CAPITAL letters automatically">CAPS</span>}
        </div>
        <input id={inputId} ref={ref} type="text" className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
            value={value} onChange={onChange} onBlur={onBlur} placeholder={placeholder} inputMode={inputMode} maxLength={maxLength}
            list={datalistId} autoComplete="off" aria-required={required ? 'true' : undefined} aria-invalid={error ? 'true' : 'false'} />
        {datalistId && <datalist id={datalistId}>{suggestions.map((s, i) => <option key={i} value={s} />)}</datalist>}
        {error && <span className={styles.fieldError} role="alert"><FiAlertCircle aria-hidden="true" /> {error}</span>}
        {!error && hint && <span className={styles.inputHint}>{hint}</span>}
    </div>);
});
SmartInput.displayName = 'SmartInput';
const SmartSelect = ({ label, options, value, onChange, id }) => {
    const [open, setOpen] = useState(false); const wrapRef = useRef(null);
    const selectId = id || 'ss-' + (label || '').replace(/\W/g, '-').toLowerCase();
    useEffect(() => { const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); }; document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h); }, []);
    return (<div className={styles.hwInputWrap} ref={wrapRef} style={{ position: 'relative' }}>
        <div className={styles.inputLabelRow}><label id={selectId + '_lbl'}>{label}</label></div>
        <div id={selectId} role="combobox" aria-haspopup="listbox" aria-expanded={open} aria-labelledby={selectId + '_lbl'} tabIndex={0}
            className={`${styles.selectTrigger} ${open ? styles.selectTriggerOpen : ''}`} onClick={() => setOpen(o => !o)}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); } if (e.key === 'Escape') setOpen(false); }}>
            <span className={styles.selectValue}>{value}</span>
            <FiChevronDown className={`${styles.selectChevron} ${open ? styles.rotated : ''}`} aria-hidden="true" />
        </div>
        {open && (<ul role="listbox" aria-labelledby={selectId + '_lbl'} className={styles.selectDropdown}>
            {options.map(opt => (<li key={opt} role="option" aria-selected={opt === value} tabIndex={-1}
                className={`${styles.selectOption} ${opt === value ? styles.selectOptionActive : ''}`}
                onClick={() => { onChange(opt); setOpen(false); }}>{opt}</li>))}
        </ul>)}
    </div>);
};
// fix167: the hint is shown now (it was passed in but never drawn)
const CurrencyInput = ({ label, value, onChange, error, id, disabled, hint, placeholder = '0' }) => {
    const [focused, setFocused] = useState(false);
    const inputId = id || 'cur-' + (label || '').replace(/\W/g, '-').toLowerCase();
    const display = focused ? String(value ?? '') : (value !== '' && value !== null && value !== undefined ? Number(value).toLocaleString() : '');
    return (<div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
        <div className={styles.inputLabelRow}><label htmlFor={inputId}>{label}</label><span className={styles.currencyTag}>UGX</span>
            {disabled && <span className={styles.autoCalcBadge}>LOCKED</span>}</div>
        <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''} ${disabled ? styles.calcInput : ''}`}
            inputMode="numeric" value={display} onFocus={() => { if (!disabled) setFocused(true); }} onBlur={() => setFocused(false)}
            onChange={e => { if (!disabled) onChange(e.target.value.replace(/\D/g, '')); }} placeholder={placeholder} disabled={disabled} />
        {error && <span className={styles.fieldError} role="alert"><FiAlertCircle aria-hidden="true" /> {error}</span>}
        {!error && hint && <span className={styles.inputHint}>{hint}</span>}
    </div>);
};
// fix167: one confirm window built on the shared popup (Recovery design). Opened on top of another popup it uses
// `stacked`: no blur, so whatever is behind it (and its red error) stays readable.
const useConfirm = () => {
    const [state, setState] = useState({ open: false, title: '', message: '', variant: 'warn', confirmLabel: 'CONFIRM', resolve: null });
    const confirm = useCallback((title, message, variant = 'warn', confirmLabel = 'CONFIRM') => new Promise(resolve => setState({ open: true, title, message, variant, confirmLabel, resolve })), []);
    const handleAnswer = useCallback((answer) => { setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; }); }, []);
    return { confirmState: state, confirm, handleAnswer };
};
const ConfirmModal = ({ state, onAnswer }) => {
    const isDanger = state.variant === 'danger';
    return (<HardwareModal isOpen={state.open} stacked lockBackdrop onClose={() => onAnswer(false)} title={state.title}>
        <div className={`${modalStyles.modalInfoBox} ${isDanger ? modalStyles.modalInfoBoxDanger : ''}`}>{state.message}</div>
        <div className={modalStyles.modalFooter}>
            <button type="button" className={isDanger ? styles.modalDangerBtn : modalStyles.modalBtnPrimary} onClick={() => onAnswer(true)}>
                {isDanger ? <FiTrash2 aria-hidden="true" /> : <FiCheckCircle aria-hidden="true" />} {state.confirmLabel}</button>
        </div>
    </HardwareModal>);
};

/* STATUS CHECKLIST (fix116/117 Intake mirror, fix167; fix180: was the Stage checklist):
   - ticks are drawn ORANGE in view mode too (a disabled checkbox was grey and looked unticked)
   - hovering a ticked status says when and by whom; the date shows on the row
   - no auto-tick on opening EDIT (New Project ticks the first status; the tick really arrives)
   - remove asks first; RESTORE DEFAULTS is one server step, director only (it removes statuses)
   - fix180: the list belongs to the project type and is no longer tied to the Title Details; every status can carry
     its own documents (ATTACH opens the upload window for that status) */
const StatusChecklistPanel = ({ projectId, canEdit, canRemove, toast, confirm, docsByStatus, canAttach, onAttach, onViewDoc }) => {
    const [statuses, setStatuses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadErr, setLoadErr] = useState('');
    const [addingStatus, setAddingStatus] = useState(false);
    const [newStatusName, setNewStatusName] = useState('');
    const [insertAfterId, setInsertAfterId] = useState(null);
    const [insertAfterName, setInsertAfterName] = useState('');
    const [saving, setSaving] = useState(false);
    const [toggling, setToggling] = useState(false);
    const loadStatuses = useCallback(async () => {
        try {
            const list = await statusTemplateService.getProjectStatuses(projectId) || [];
            setStatuses(list); setLoadErr('');
        } catch (err) { setLoadErr('STATUSES COULD NOT BE LOADED: ' + errText(err)); }
        finally { setLoading(false); }
    }, [projectId]);
    useEffect(() => { loadStatuses(); }, [loadStatuses]);
    const openInsertBelow = (status) => { setInsertAfterId(status.id); setInsertAfterName(status.statusName); setNewStatusName(''); setAddingStatus(true); };
    const cancelInsert = () => { setAddingStatus(false); setNewStatusName(''); setInsertAfterId(null); setInsertAfterName(''); };
    const handleAddStatus = async () => {
        const name = newStatusName.trim();
        if (!name) { toast && toast('Enter a status name first.', 'error'); return; }
        if (statuses.some(s => (s.statusName || '').toLowerCase() === name.toLowerCase())) { toast && toast('That status is already on the list.', 'error'); return; }
        setSaving(true);
        let created;
        try { created = await statusTemplateService.attachStatuses(projectId, [{ statusName: name, cost: 0, isCustom: true }]); }
        catch (err) { setSaving(false); toast && toast('STATUS NOT ADDED: ' + errText(err), 'error'); return; }
        try {
            const createdIds = (created || []).map(c => c.id).filter(Boolean);
            if (createdIds.length && insertAfterId) {
                const currentIds = statuses.map(s => s.id);
                const idx = currentIds.indexOf(insertAfterId);
                const ordered = idx >= 0 ? [...currentIds.slice(0, idx + 1), ...createdIds, ...currentIds.slice(idx + 1)] : [...currentIds, ...createdIds];
                await statusTemplateService.reorderProjectStatuses(projectId, ordered);
            }
            toast && toast('Status inserted.', 'success');
        } catch (err) { toast && toast('Status added, but at the END of the list (moving it failed: ' + errText(err) + ').', 'warn', 12000); }
        finally { await loadStatuses(); cancelInsert(); setSaving(false); }
    };
    const handleToggleComplete = async (status) => {
        if (toggling || !canEdit) return;   // fix166: a double click used to send two ticks and flip the status back
        setToggling(true);
        const next = !statusDone(status);
        try {
            await statusTemplateService.toggleStatusCompletion(projectId, status.id, next);
            await loadStatuses();
        } catch (err) { await loadStatuses(); toast && toast('STATUS NOT UPDATED: ' + errText(err), 'error'); }
        finally { setToggling(false); }
    };
    const handleRemove = async (status) => {
        const ok = confirm ? await confirm('REMOVE STATUS', 'Remove "' + status.statusName + '" from this project? Its tick goes with it (its documents stay in Documents). The audit log keeps a record.', 'danger', 'REMOVE STATUS') : true;
        if (!ok) return;
        try { await statusTemplateService.removeStatus(projectId, status.id); await loadStatuses(); toast && toast('Status removed.', 'warn'); }
        catch (err) { toast && toast('STATUS NOT REMOVED: ' + errText(err), 'error'); }
    };
    const handleRestoreDefaults = async () => {
        if (confirm) { const ok = await confirm('RESTORE DEFAULTS', 'Replace this project\'s status list with the master list of its project type? Every current tick and every custom status is removed; only the first status stays ticked. The old list is written to the audit log.', 'danger', 'RESTORE DEFAULTS'); if (!ok) return; }
        setSaving(true);
        try { await statusTemplateService.restoreProjectDefaults(projectId); await loadStatuses(); cancelInsert(); toast && toast('Default statuses restored.', 'success'); }
        catch (err) { await loadStatuses(); toast && toast('DEFAULTS NOT RESTORED: ' + errText(err), 'error'); }
        finally { setSaving(false); }
    };
    if (loading) return null;
    const doneCount = statuses.filter(statusDone).length;
    return (<div className={styles.statusList}>
        {loadErr && <div className={styles.modalErr} role="alert"><FiAlertCircle className={styles.modalErrIcon} aria-hidden="true" /><span>{loadErr}</span></div>}
        <div className={styles.statusListTop}>
            <span className={styles.statusProgress} title="Statuses ticked so far">{doneCount} OF {statuses.length} DONE</span>
            {canEdit && <span className={styles.inputHint}>Ticks save the moment you click them. CANCEL does not undo them.</span>}
            {canRemove && <button type="button" className={styles.ghostBtn} onClick={handleRestoreDefaults} disabled={saving} title="Replace this project's statuses with its type's master list (director only)."><FiRefreshCw aria-hidden="true" /> RESTORE DEFAULTS</button>}
        </div>
        {statuses.length === 0 && <div className={styles.emptyState}><FiCheckCircle className={styles.emptyIcon} aria-hidden="true" /><span>NO STATUSES ATTACHED YET</span></div>}
        {statuses.map((status, i) => {
            const isFirst = i === 0;
            const done = statusDone(status);
            const when = status.completedAt ? fmtDate(status.completedAt) : '';
            const tip = done ? ('Done' + (when ? ' on ' + when : '') + (status.completedBy ? ' by ' + status.completedBy : '') + '.') : 'Not done yet.';
            const docs = (docsByStatus && docsByStatus.get(status.id)) || [];
            return (<React.Fragment key={status.id}>
                <label className={`${styles.statusItem} ${done ? styles.statusItemChecked : ''} ${canEdit ? '' : styles.statusItemRO}`} title={canEdit ? tip + ' Click to ' + (done ? 'untick.' : 'tick.') : tip}>
                    <input type="checkbox" className={styles.statusCheckbox} checked={done} readOnly={!canEdit} tabIndex={canEdit ? 0 : -1}
                        aria-readonly={!canEdit} disabled={canEdit && toggling}
                        onChange={() => handleToggleComplete(status)} aria-label={`${status.statusName}: ${done ? 'done' : 'not done'}`} />
                    <span className={styles.statusItemName}>{status.statusName}{status.isCustom ? <span className={styles.statusCustomTag} title="Added on this project only (not in the master list)">CUSTOM</span> : null}</span>
                    {done && when && <span className={styles.statusMeta}>{when}{status.completedBy ? ' - ' + status.completedBy : ''}</span>}
                    <span className={styles.statusActions}>
                        {canAttach && (<button type="button" className={styles.plusBtn} title={'Attach documents to "' + status.statusName + '"'}
                            aria-label={`Attach documents to ${status.statusName}`}
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onAttach && onAttach(status); }}><FiPaperclip size={12} /></button>)}
                        {canEdit && (<button type="button" className={styles.plusBtn} title="Insert a status below this one"
                            aria-label={`Insert status below ${status.statusName}`}
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(status); }}><FiPlus size={12} /></button>)}
                        {canEdit && canRemove && !isFirst && (<button type="button" className={styles.iconBtnDanger} title="Remove this status (director only)"
                            aria-label={`Remove ${status.statusName}`}
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleRemove(status); }}><FiTrash2 size={12} /></button>)}
                    </span>
                </label>
                {docs.length > 0 && (<div className={styles.statusDocs}>
                    {docs.map(d => (<button type="button" key={d.id} className={styles.statusDocLink} onClick={() => onViewDoc && onViewDoc(d)} title={'View ' + d.fileName}>
                        <FiFileText aria-hidden="true" /> {d.fileName}</button>))}
                </div>)}
                {addingStatus && insertAfterId === status.id && (<div className={styles.insertRow}>
                    <span className={styles.insertCtx}>INSERT UNDER: {insertAfterName}</span>
                    <input type="text" className={styles.insertInput} value={newStatusName} autoFocus maxLength={200}
                        onChange={e => setNewStatusName(e.target.value)} placeholder="New status name"
                        aria-label="New status name"
                        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddStatus(); } if (e.key === 'Escape') cancelInsert(); }} />
                    <HardwareButton type="button" onClick={handleAddStatus} loading={saving} icon={FiCheckCircle}>ADD</HardwareButton>
                    <button type="button" className={styles.ghostBtn} onClick={cancelInsert} aria-label="Cancel insert" title="Close without adding"><FiX aria-hidden="true" /></button>
                </div>)}
            </React.Fragment>);
        })}
    </div>);
};

// fix167: every reason popup, set up in ONE place. danger = red button + red info box; the rest are neutral.
const REASON_KINDS = {
    REVERSE:       { danger: true,  ph: 'e.g. The client paid into the wrong account; the bank reversed it.' },
    REDUCE:        { danger: false, ph: 'e.g. Director agreed a lower figure with the client on the phone.', agree: true },
    RATE:          { danger: false, ph: 'e.g. Agreed rate after negotiation with the client.', agree: true },
    PAUSE:         { danger: false, ph: 'e.g. Client is negotiating; bereavement in the family.', agree: true },
    RESUME:        { danger: false, ph: 'e.g. Negotiation ended without an agreement.' },
    WAIVE:         { danger: true,  ph: 'e.g. Fees forgiven as part of the final settlement.', agree: true },
    UNDO_RELEASE:  { danger: true,  ph: 'e.g. Hand-over was recorded on the wrong plot.' },
    ENTER:         { danger: false, ph: 'e.g. No payment for 9 months; client not answering.' },
    SET_ASIDE:     { danger: false, ph: 'e.g. Court case pending; stop billing until it is decided.' },
    CAPITALIZE:    { danger: false, ph: 'e.g. Client agreed to pay the fees with the title balance.', agree: true },
    CLEAR_PROBLEM: { danger: false, ph: 'e.g. The corrected deed plan now matches the National ID.' },
    DELETE:        { danger: true,  ph: 'e.g. Entered twice by mistake; the real record is #014A.' },
    REVERT_TITLE:  { danger: true,  ph: 'e.g. Title details were typed on the wrong project.' },
    RELEASE:       { danger: false, ph: 'e.g. Collected by JOHN DOE in person, NIN checked against the ID card.' },
};
const TYPE_LABELS = { STANDARD: 'PAYMENT', INITIAL_DEPOSIT: 'DEPOSIT AT INTAKE', RECEIVABLE_PARTIAL: 'PAYMENT (IN RECEIVABLES)', REVERSAL: 'REVERSAL' };
const TAB_SHORT = { OVERVIEW: 'OV', FINANCIALS: 'FIN', PEOPLE: 'PPL', DOCUMENTS: 'DOC', NOTES: 'NTS' };
// fix180: one Client / Owner row and one Neighbor row in the EDIT buffer
const personToRow = (p) => ({ fullName: p.fullName || '', phone: p.phoneNumber || '', nationalId: p.nationalId || '', address: p.homeAddress || '', email: p.email || '' });
const EMPTY_PERSON = () => ({ fullName: '', phone: '', nationalId: '', address: '', email: '' });
const EMPTY_NEIGHBOR = () => ({ fullName: '', phone: '', side: '', plotNumber: '' });

const FolderPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();

    /* UNIFIED ROLE MATRIX */
    const flags = roleFlags(user);   // fix181: one rank helper
    const isDirector = flags.isOwnerLevel;
    const isManager = flags.isManager;
    const canEditRole = isManager;    // edit record, statuses, docs, payments, problem flag
    const canMoney = isDirector;      // receivable money actions, hand-over, reversals
    const canUploadDocs = flags.canUploadDocs; // add scans without edit mode

    const [binder, setBinder] = useState(null);
    const [buffer, setBuffer] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [committing, setCommitting] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [ninMismatch, setNinMismatch] = useState(null);
    const [payments, setPayments] = useState([]);
    const [portfolio, setPortfolio] = useState([]);
    const [recoveryCalls, setRecoveryCalls] = useState([]);
    const [freezeOpen, setFreezeOpen] = useState(false);
    const [rateFee, setRateFee] = useState(''); const [pauseUntil, setPauseUntil] = useState('');
    const [defaultRate, setDefaultRate] = useState(0);   // fix173: system default monthly fee, from the server
    useEffect(() => { landService.getStorageFeeDefault().then(setDefaultRate).catch(() => {}); }, []);
    const [activeTab, setActiveTab] = useState(() => {
        const h = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : '';
        return (h.includes('finance') || h.includes('payment')) ? 'FINANCIALS' : 'OVERVIEW';
    });
    const TABS = ['OVERVIEW', 'FINANCIALS', 'PEOPLE', 'DOCUMENTS', 'NOTES'];
    const TAB_ACCENTS = { OVERVIEW: 'orange', FINANCIALS: 'cyan', PEOPLE: 'violet', DOCUMENTS: 'slate', NOTES: 'red' };
    const [noteModal, setNoteModal] = useState({ open: false, id: null, content: '' });
    const [noteErr, setNoteErr] = useState(''); const [noteBusy, setNoteBusy] = useState(false);
    const [payModal, setPayModal] = useState({ open: false });
    const [payAmount, setPayAmount] = useState(''); const [payNotes, setPayNotes] = useState('');
    // fix181 (16.12b): one id per payment; a retry after a slow network sends the same id and the server refuses a second save
    const payRequestId = useRef(null);
    const [payType, setPayType] = useState('TITLE'); const [paying, setPaying] = useState(false);
    const [payerId, setPayerId] = useState('');
    const [payReceipt, setPayReceipt] = useState(null);
    const payReceiptRef = useRef(null);
    const [payErr, setPayErr] = useState('');
    const [problemModal, setProblemModal] = useState({ open: false, note: '' });
    const [reasonModal, setReasonModal] = useState({ open: false, kind: '', title: '', info: '', confirmLabel: '', amountLabel: '', amount: '', reason: '', paymentId: null, agreedWith: '' });
    const [reasonBusy, setReasonBusy] = useState(false);
    const [probBusy, setProbBusy] = useState(false);
    const [probErr, setProbErr] = useState('');
    const [reasonErr, setReasonErr] = useState('');
    const [drawers, setDrawers] = useState({ overview: true, balance: true, recv: true, history: true, notes: true, calls: true, clients: true, owners: true, neighbors: true, subdivisions: true, related: true, docs: true, statusesPanel: true });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));
    const { confirmState, confirm, handleAnswer } = useConfirm();
    const firstInputRef = useRef(null);
    const fileInputRef = useRef(null);
    // fix136: document categories + the UPLOAD DOCUMENTS window
    const [docCats, setDocCats] = useState([]);
    const [uploadDraft, setUploadDraft] = useState(null); // { batch, files: [{ file, category }], statusId, statusName }
    const [attachTo, setAttachTo] = useState(null);       // fix180: the status the next picked files are attached to
    const [newCatOpen, setNewCatOpen] = useState(false);
    const [newCatName, setNewCatName] = useState('');
    const [catBusy, setCatBusy] = useState(false);
    const loadDocCats = useCallback(async () => { try { setDocCats(await landService.getDocumentCategories()); } catch { /* headings fall back to the raw code */ } }, []);
    useEffect(() => { loadDocCats(); }, [loadDocCats]);
    const touchedSetBuffer = React.useCallback((updater) => { setBuffer(updater); }, []);
    const { blocked: guardModalOpen, proceed: routerProceed, reset: handleStay } = useRouterBlock(!committing && isEditing);
    const lastActiveRef = useRef(Date.now());
    const [showTopBtn, setShowTopBtn] = useState(false);
    useEffect(() => {
        const onScroll = () => { const h = document.querySelector('[class*="terminalHeader"]'); setShowTopBtn(!!h && h.getBoundingClientRect().bottom < 0); };
        window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
        return () => window.removeEventListener('scroll', onScroll);
    }, []);
    useEffect(() => {
        const mark = () => { lastActiveRef.current = Date.now(); };
        window.addEventListener('click', mark); window.addEventListener('keydown', mark);
        return () => { window.removeEventListener('click', mark); window.removeEventListener('keydown', mark); };
    }, []);
    // the folder page is wide: fold the sidebar away when it opens
    useEffect(() => {
        const t = setTimeout(() => {
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
        }, 150);
        return () => clearTimeout(t);
    }, []);
    // links into the page: #financials / #payment-<id> (Payments page) / #notes / #owners / #documents
    // fix167: the old #record-payment, #storage-fees and ?action=pay links are gone (nothing used them, and ?action
    // re-opened the payment window every time the page reloaded its data).
    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-')) {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                if (hash.startsWith('payment-')) { const el = document.getElementById(hash); if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.classList.add(styles.highlightRow); setTimeout(() => el.classList.remove(styles.highlightRow), 3000); } }
                else { const el = document.getElementById('paymentHistorySection'); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
            }, 350);
        } else if (hash === 'notes' || hash === 'calls') setActiveTab('NOTES');
        else if (hash === 'identity' || hash === 'owners' || hash === 'clients' || hash === 'people') setActiveTab('PEOPLE');
        else if (hash === 'vault' || hash === 'documents') setActiveTab('DOCUMENTS');
        else window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [id]);
    useEffect(() => { if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120); }, [isEditing]);
    // fix166: nothing is saved by itself; after 10 quiet minutes the page only reminds
    useEffect(() => {
        const t = setInterval(() => {
            if (!isEditing || committing) return;
            if (Date.now() - lastActiveRef.current > 10 * 60 * 1000) {
                lastActiveRef.current = Date.now();
                toast('You have unsaved edits open. Nothing is saved automatically - press SAVE, or CANCEL to throw them away.', 'warn', 15000);
            }
        }, 15000);
        return () => clearInterval(t);
    }, [isEditing, committing, toast]);
    useEffect(() => {
        if (!isEditing || committing) return;
        const handler = (e) => { e.preventDefault(); e.returnValue = ''; return ''; };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);

    const loadPortfolio = useCallback(async () => { try { setPortfolio(await folderPortalService.getPortfolio(id) || []); } catch { setPortfolio([]); } }, [id]);
    const loadFolderData = useCallback(async () => {
        try {
            const data = await landService.getDeepBinder(id);
            if (!data) throw new Error('NULL_SIGNAL');
            setBinder(data); setPayments(data.payments || []); setLoadError(false);
            if (!isEditing) {
                const t = data.project?.landTitle;
                setBuffer({
                    plotNumber: t?.plotNumber || '', tenure: t?.tenure || 'FREEHOLD',
                    block: t?.block || '', areaHectares: t?.areaHectares != null ? String(t.areaHectares) : '',
                    volume: t?.volume || '', folio: t?.folio || '', titleIssueDate: t?.titleIssueDate || '',
                    titleDetailsEnabled: !!data.project?.titleDetailsEnabled,
                    subdivisionCount: data.project?.subdivisionCount != null ? String(data.project.subdivisionCount) : '',
                    district: data.project?.district || '',
                    county: data.project?.county || '', subCounty: data.project?.subCounty || '',
                    parish: data.project?.parish || '', village: data.project?.village || '', area: data.project?.area || '',
                    totalCost: String(data.project?.totalCost || 0), initialPayment: String(Math.max(0, Number(data.project?.amountPaid || 0) - Number(data.project?.storageFeesPaid || 0))),
                    isLegacy: !!data.project?.isLegacy,
                    // fix180: clients first (old projects with none show their owners), owners, neighbors
                    clients: ((data.project?.clients || []).length ? data.project.clients : (data.project?.proprietors || [])).map(personToRow),
                    owners: (data.project?.proprietors || []).map(personToRow),
                    neighbors: (data.neighbors || []).map(n => ({ fullName: n.fullName || '', phone: n.phone || '', side: n.side || '', plotNumber: n.plotNumber || '' })),
                });
                setFieldErrors({});
            }
        } catch { setLoadError(true); } finally { setLoading(false); }
    }, [id, isEditing]);
    useEffect(() => { loadFolderData(); loadPortfolio(); }, [loadFolderData, loadPortfolio]);
    // fix167: the Recovery calls are loaded AND shown. fix180: Recovery calls the CLIENTS, so these are the clients' calls.
    useEffect(() => {
        if (!binder?.project) return;
        const owners = (binder.project.clients || []).length ? binder.project.clients : (binder.project.proprietors || []);
        Promise.all(owners.map(p => recoveryService.getNotes(p.id).then(r => (r && r.data ? r.data : r) || []).catch(() => [])))
            .then(lists => {
                const all = [];
                lists.forEach((list, i) => (Array.isArray(list) ? list : []).forEach(n => all.push({ ...n, ownerName: owners[i].fullName })));
                setRecoveryCalls(all.filter(n => n.source === 'RECOVERY')
                    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 20));
            });
    }, [binder]);
    useEffect(() => {
        if (!binder?.project) return;
        const o = binder.project.storageFeeOverride;
        setRateFee(o !== null && o !== undefined ? String(Math.round(Number(o))) : '');
        setPauseUntil(binder.project.negotiationDeadline ? String(binder.project.negotiationDeadline).slice(0, 10) : '');
    }, [binder]);
    // fix180: Title Details are kept when the project type always has them, when Topographic Survey switched them on,
    // and always when a title is already saved (data is never hidden).
    const titleShown = (proj, buf) => !!proj.landTitle || showsTitle(projectTypeOf(proj).value, !!(buf && buf.titleDetailsEnabled));

    const validateBuffer = (buf, hasTitle) => {
        const errors = [];
        const fe = {};
        if (hasTitle) {
            if (!buf.plotNumber?.trim()) { errors.push('PLOT NUMBER IS REQUIRED'); fe.plotNumber = 'Required'; }
            if (!buf.tenure?.trim()) errors.push('TENURE IS REQUIRED');
            if (!buf.block?.trim()) { errors.push('BLOCK IS REQUIRED'); fe.block = 'Required'; }
            if (!(Number(buf.areaHectares) > 0)) { errors.push('AREA (HECTARES) IS REQUIRED'); fe.areaHectares = 'Required'; }
        }
        if (!buf.district?.trim()) { errors.push('DISTRICT IS REQUIRED'); fe.district = 'Required'; }
        if (projectTypeOf(project).value === 'SUBDIVISION' && !(Number(buf.subdivisionCount) >= 1)) { errors.push('NUMBER OF SUBDIVISIONS IS REQUIRED'); fe.subdivisionCount = 'Required'; }
        [['clients', 'CLIENT'], ['owners', 'OWNER']].forEach(([key, what]) => {
            if (!(buf[key] || []).length) errors.push('KEEP AT LEAST ONE ' + what);
            (buf[key] || []).forEach((o, i) => {
                if (!o.fullName?.trim()) { errors.push(what + ' ' + (i + 1) + ': LEGAL NAME IS REQUIRED'); fe[key + '_' + i + '_name'] = 'Required'; }
                if (!o.nationalId?.trim()) { errors.push(what + ' ' + (i + 1) + ': NATIONAL ID (NIN) IS REQUIRED'); fe[key + '_' + i + '_nin'] = 'Required'; }
                if (o.phone?.trim()) { const ph = normalizePhones(o.phone); if (!ph.ok) { errors.push(what + ' ' + (i + 1) + ': ' + ph.error.toUpperCase()); fe[key + '_' + i + '_phone'] = 'Check number'; } }
            });
        });
        (buf.neighbors || []).forEach((nb, i) => {
            if (!nb.fullName?.trim()) { errors.push('NEIGHBOR ' + (i + 1) + ': NAME IS REQUIRED (OR REMOVE THE ROW)'); fe['neighbors_' + i + '_name'] = 'Required'; }
            if (nb.phone?.trim() && !normalizePhones(nb.phone).ok) { errors.push('NEIGHBOR ' + (i + 1) + ': CHECK THE PHONE NUMBER'); fe['neighbors_' + i + '_phone'] = 'Check number'; }
        });
        return { errors, fe };
    };

    const handleCommit = async () => {
        if (ninMismatch) { toast('Confirm or fix the NIN mismatch warning before saving.', 'error', 6000); return; }
        const hasTitle = titleShown(project, buffer);
        const { errors, fe } = validateBuffer(buffer, hasTitle);
        if (errors.length) {
            setFieldErrors(fe); toast('NOT SAVED: ' + errors[0], 'error', 6000); return;
        }
        if ((Number(buffer.totalCost) || 0) !== (Number(project.totalCost) || 0) && (buffer.costChangeReason || '').trim().length < 5) {
            setFieldErrors({ costChangeReason: 'Write why (5+ characters)' }); setActiveTab('FINANCIALS'); toast('WRITE WHY THE TOTAL COST CHANGED (AT LEAST 5 CHARACTERS)', 'error', 6000); return;
        }
        setFieldErrors({}); setCommitting(true);
        try {
            const cleanPerson = (o) => ({ ...o, phone: o.phone?.trim() ? (normalizePhones(o.phone).value || o.phone.trim()) : '' });
            await landService.updateMasterFolder(id, {
                ...buffer,
                areaHectares: hasTitle ? Number(buffer.areaHectares) : null,
                subdivisionCount: buffer.subdivisionCount === '' ? null : Number(buffer.subdivisionCount),
                titleIssueDate: buffer.titleIssueDate || null,
                clients: (buffer.clients || []).map(cleanPerson),
                owners: (buffer.owners || []).map(cleanPerson),
                neighbors: (buffer.neighbors || []).map(n => ({ ...n, fullName: n.fullName.trim().toUpperCase(), side: (n.side || '').trim().toUpperCase(), plotNumber: (n.plotNumber || '').trim().toUpperCase(), phone: n.phone?.trim() ? (normalizePhones(n.phone).value || n.phone.trim()) : '' })),
                totalCost: Number(buffer.totalCost) || 0, initialPayment: Number(buffer.initialPayment) || 0, costChangeReason: (buffer.costChangeReason || '').trim(), expectedTotalCost: Number(project.totalCost) || 0 });
            predictionService.learn(buffer); setIsEditing(false);
            await loadFolderData(); toast('Changes saved.', 'success');
        } catch (err) { toast('NOT SAVED: ' + errText(err), 'error'); }
        finally { setCommitting(false); }
    };
    const handleLeave = () => routerProceed();

    // fix165/167: PROBLEM flag needs words (5+); the page says it WANTS to flag (two clicks cannot cancel each other)
    const handleProblemConfirm = async () => {
        if (probBusy) return;
        const note = (problemModal.note || '').trim();
        if (note.length < 5) { setProbErr('WRITE WHAT THE PROBLEM IS (AT LEAST 5 CHARACTERS).'); return; }
        setProbBusy(true); setProbErr('');
        try {
            await folderPortalService.toggleProblem(id, note, true);
            setProblemModal({ open: false, note: '' });
            await loadFolderData(); toast('Flagged as PROBLEM. Staff have been notified.', 'warn');
        } catch (err) { setProbErr(errText(err)); }
        finally { setProbBusy(false); }
    };
    const handleToggleProblem = () => {
        if (project.problem) openReasonModal({ kind: 'CLEAR_PROBLEM', title: 'CLEAR PROBLEM FLAG', confirmLabel: 'CLEAR FLAG', info: 'This removes the PROBLEM flag from this plot. Write why it is no longer a problem; your words go into the notes and the audit log.' });
        else { setProbErr(''); setProblemModal({ open: true, note: '' }); }
    };
    const closeProblemModal = () => { if (!probBusy) { setProbErr(''); setProblemModal({ open: false, note: '' }); } };
    const openReasonModal = (cfg) => { setReasonErr(''); setReasonModal({ open: true, kind: '', title: '', info: '', confirmLabel: 'CONFIRM', amountLabel: '', amount: '', reason: '', paymentId: null, agreedWith: '', ...cfg }); };
    const closeReasonModal = () => { if (!reasonBusy) { setReasonErr(''); setReasonModal(m => ({ ...m, open: false })); } };
    const submitReasonModal = async () => {
        if (reasonBusy) return;
        const m = reasonModal; const typed = (m.reason || '').trim();
        if (typed.length < 5) { setReasonErr('WRITE THE REASON (AT LEAST 5 CHARACTERS).'); return; }
        if (m.kind === 'REDUCE') {
            const n = Number(m.amount);
            if (m.amount === '' || !Number.isInteger(n) || n < 0 || n >= storageFees) { setReasonErr('ENTER A NEW TOTAL (WHOLE SHILLINGS) THAT IS LOWER THAN THE CURRENT UGX ' + fmt(storageFees) + '.'); return; }
            if (n < storagePaid) { setReasonErr('UGX ' + fmt(storagePaid) + ' OF FEES IS ALREADY PAID, SO THE NEW TOTAL CANNOT BE LOWER THAN THAT.'); return; }
        }
        // fix167: for fee deals with joint owners, record WHICH owner agreed (fees belong to the whole project)
        const who = m.agreedWith ? (payers.find(p => p.id === m.agreedWith)?.fullName || '') : '';
        const why = (who ? '[Agreed with ' + who + '] ' : '') + typed;
        setReasonBusy(true); setReasonErr('');
        try {
            if (m.kind === 'REVERSE') { await landService.reversePayment(id, m.paymentId, why); toast('Payment reversed.', 'warn'); }
            else if (m.kind === 'REDUCE') { await folderPortalService.reduceFees(id, m.amount, why); toast('Storage fees reduced.', 'success'); }
            else if (m.kind === 'RATE') { await folderPortalService.settings(id, { rate: rateFee, reason: why }); toast('Monthly storage rate saved.', 'success'); }
            else if (m.kind === 'PAUSE') { await folderPortalService.settings(id, { deadline: pauseUntil, reason: why }); setFreezeOpen(false); toast('Storage fees paused.', 'info'); }
            else if (m.kind === 'RESUME') { await folderPortalService.settings(id, { deadline: '', reason: why }); toast('Storage fees resumed. The paused days are not charged.', 'info'); }
            else if (m.kind === 'WAIVE') { await folderPortalService.exit(id, 'WAIVE', why); toast('Unpaid storage fees waived.', 'success'); }
            else if (m.kind === 'UNDO_RELEASE') { await landService.undoRelease(id, why); toast('Hand-over undone.', 'warn'); }
            else if (m.kind === 'ENTER') { await folderPortalService.enter(id, why); toast('Moved to receivables.', 'success'); }
            else if (m.kind === 'SET_ASIDE') { await folderPortalService.exit(id, 'SET_ASIDE', why); toast('Set aside. Unpaid fees are kept on the project.', 'success'); }
            else if (m.kind === 'CAPITALIZE') { await folderPortalService.exit(id, 'CAPITALIZE', why); toast('Storage fees added to the total cost.', 'success'); }
            else if (m.kind === 'CLEAR_PROBLEM') { await folderPortalService.toggleProblem(id, why, false); toast('Problem flag removed.', 'info'); }
            else if (m.kind === 'RELEASE') { await landService.authorizeRelease(id, why); toast('Title handed over. Plot is now RELEASED.', 'success'); }
            else if (m.kind === 'DELETE') {
                await landService.purgeAsset(id, why);
                setIsEditing(false);
                setReasonModal(x => ({ ...x, open: false }));
                toast('Project deleted. The root user can restore it from Settings > Archive.', 'warn', 6000);
                setTimeout(() => navigate('/land/projects'), 1500);
                return;
            }
            else if (m.kind === 'REVERT_TITLE') { await landService.revertTitle(id, why); toast('Title Details removed from this project.', 'warn'); }
            setReasonModal(x => ({ ...x, open: false }));
            await loadFolderData(); loadPortfolio();
        } catch (err) { setReasonErr(errText(err)); }
        finally { setReasonBusy(false); }
    };
    const handleUnlock = async () => {
        setIsEditing(true);
        try { await landService.logDossierUnlock(id); } catch { /* audit only */ }
    };
    const handleAbort = async () => {
        const ok = await confirm('DISCARD CHANGES', 'Unsaved field changes will be lost. Status ticks are saved the moment you click them, so they stay as they are.', 'warn', 'DISCARD');
        if (!ok) return;
        setIsEditing(false); setFieldErrors({}); loadFolderData();
    };
    // fix166: DELETE is a soft delete (the root user can restore it) and needs a written reason.
    const handleNuclearPurge = () => openReasonModal({ kind: 'DELETE', title: 'DELETE THIS PROJECT', confirmLabel: 'DELETE PROJECT',
        info: 'This takes the whole project (payments, notes and documents included) out of every list. It is NOT erased: the root user can restore it from Settings > Archive. Write why it is being deleted.' });
    // fix180: the NIN check, field changes, add and remove work on any person list: 'clients', 'owners' or 'neighbors'
    const handleNinBlurCheck = async (list, idx, val) => {
        if (!val.trim()) return;
        try {
            const result = await clientService.lookupNin(val.trim());
            if (!result.exists) return;
            const existingName = (result.fullName || '').trim().toUpperCase();
            const enteredName = (buffer[list][idx]?.fullName || '').trim().toUpperCase();
            if (existingName && enteredName && existingName !== enteredName) { setNinMismatch({ list, idx, existingName: result.fullName, enteredName: buffer[list][idx]?.fullName || '' }); return; }
            const rows = buffer[list].map((o, i) => i !== idx ? o : { ...o, phone: o.phone.trim() ? o.phone : (result.phoneNumber || o.phone), email: o.email.trim() ? o.email : (result.email || o.email), address: o.address.trim() ? o.address : (result.homeAddress || o.address) });
            touchedSetBuffer(p => ({ ...p, [list]: rows }));
            toast('NIN matched ' + result.fullName + '. Details auto-filled.', 'info', 4500);
        } catch (err) { toast('NIN LOOKUP FAILED: ' + errText(err), 'error'); }
    };
    const handleNinMismatchConfirm = () => setNinMismatch(null);
    const handleNinMismatchReject = () => { if (!ninMismatch) return; const { list, idx } = ninMismatch; handlePersonChange(list, idx, 'nationalId', ''); setNinMismatch(null); setTimeout(() => { const el = document.getElementById(list + '_' + idx + '_nin'); if (el) el.focus(); }, 50); };
    const handlePersonChange = (list, idx, field, val) => {
        setBuffer(p => ({ ...p, [list]: p[list].map((o, i) => { if (i !== idx) return o; let v = val; if (field === 'fullName') v = val.toUpperCase(); if (field === 'nationalId') v = val.toUpperCase().replace(/\s/g, ''); if (field === 'email') v = val.toLowerCase().replace(/\s/g, ''); return { ...o, [field]: v }; }) }));
    };
    const addPerson = (list) => setBuffer(p => ({ ...p, [list]: [...(p[list] || []), list === 'neighbors' ? EMPTY_NEIGHBOR() : EMPTY_PERSON()] }));
    const removePerson = (list, idx) => setBuffer(p => ({ ...p, [list]: p[list].filter((_, i) => i !== idx) }));
    const copyClientsToOwners = () => setBuffer(p => ({ ...p, owners: (p.clients || []).map(c => ({ ...c })) }));
    // fix165: wrong type / empty / oversized files are turned away here with the reason, before any upload starts
    const handleVaultAction = (files) => {
        if (!files?.length) return;
        const ok = []; const bad = [];
        files.forEach(f => {
            if (!SCAN_EXT.includes(fileExt(f.name))) bad.push(f.name + ' (use PDF, JPG, PNG or WEBP)');
            else if (!f.size) bad.push(f.name + ' (the file is empty)');
            else if (f.size > 50 * 1024 * 1024) bad.push(f.name + ' (over 50 MB)');
            else ok.push(f);
        });
        if (bad.length) toast('NOT ADDED: ' + bad.join('; '), 'error');
        if (!ok.length) { setAttachTo(null); return; }
        // fix180: files picked from a status row's ATTACH button belong to that status
        setUploadDraft({ batch: '', error: '', files: ok.map(file => ({ file, category: '' })), statusId: attachTo ? attachTo.id : null, statusName: attachTo ? attachTo.statusName : '' });
        setAttachTo(null);
    };
    const attachToStatus = (status) => { setAttachTo(status); fileInputRef.current?.click(); };
    const closeUploadDraft = () => { if (committing) return; setUploadDraft(null); setNewCatOpen(false); setNewCatName(''); };
    const setBatchCategory = (code) => setUploadDraft(d => d && ({ ...d, error: '', batch: code, files: d.files.map(f => ({ ...f, category: code })) }));
    const setFileCategory = (i, code) => setUploadDraft(d => d && ({ ...d, error: '', files: d.files.map((f, j) => (j === i ? { ...f, category: code } : f)) }));
    const handleAddCategory = async () => {
        const name = newCatName.trim();
        if (name.length < 2 || catBusy) return;
        setCatBusy(true);
        try {
            const cat = await landService.addDocumentCategory(name);
            await loadDocCats();
            setNewCatName(''); setNewCatOpen(false);
            setUploadDraft(d => d && ({ ...d, error: '', batch: d.batch || cat.code, files: d.files.map(f => (f.category ? f : { ...f, category: cat.code })) }));
            toast('Category "' + cat.label + '" ready', 'success', 3000);
        } catch (err) { setUploadDraft(d => d && ({ ...d, error: 'COULD NOT ADD CATEGORY: ' + errText(err) })); } finally { setCatBusy(false); }
    };
    const handleUploadConfirm = async () => {
        if (!uploadDraft || committing) return;
        if (uploadDraft.files.some(f => !f.category)) { setUploadDraft(d => d && ({ ...d, error: 'PICK A CATEGORY FOR EVERY FILE.' })); return; }
        const count = uploadDraft.files.length;
        setCommitting(true);
        try {
            await landService.addExtraDocuments(id, uploadDraft.files.map(f => f.file), uploadDraft.files.map(f => f.category), uploadDraft.statusId);
            setUploadDraft(null); setNewCatOpen(false); setNewCatName('');
            await loadFolderData();
            toast(count + ' document(s) uploaded', 'success', 3000);
        } catch (err) { setUploadDraft(d => d && ({ ...d, error: errText(err) })); } finally { setCommitting(false); }
    };
    const handleDeleteDoc = async (docId, fileName) => { const ok = await confirm('DELETE DOCUMENT', 'Delete "' + fileName + '"? The file is removed from storage; the audit log keeps the name.', 'danger', 'DELETE DOCUMENT'); if (!ok) return; try { await landService.deleteDocument(docId); await loadFolderData(); toast('Document removed', 'warn', 3000); } catch (err) { toast('DOCUMENT NOT DELETED: ' + errText(err), 'error'); } };
    // fix165: the note popup shows its own errors, cannot be thrown away by a stray click, asks before discarding.
    const noteOriginal = () => (noteModal.id ? ((binder?.notes || []).find(n => n.id === noteModal.id) || {}).notes || '' : '');
    const closeNoteModal = async () => {
        if (noteBusy) return;
        const dirty = noteModal.content.trim() !== '' && noteModal.content !== noteOriginal();
        if (dirty) { const ok = await confirm('DISCARD NOTE', 'This note is not saved. Close it and lose what you typed?', 'warn', 'DISCARD NOTE'); if (!ok) return; }
        setNoteErr(''); setNoteModal({ open: false, id: null, content: '' });
    };
    const handleNoteSave = async () => {
        if (noteBusy) return;
        const text = noteModal.content.trim();
        if (text.length < 2) { setNoteErr('WRITE THE NOTE FIRST (AT LEAST 2 CHARACTERS).'); return; }
        if (text.length > NOTE_MAX) { setNoteErr('TOO LONG: ' + text.length + ' CHARACTERS. THE LIMIT IS ' + NOTE_MAX + '.'); return; }
        setNoteBusy(true); setNoteErr('');
        try {
            if (noteModal.id) await landService.editStandaloneNote(noteModal.id, text); else await landService.addStandaloneNote(id, text);
            setNoteModal({ open: false, id: null, content: '' });
            await loadFolderData(); toast('Note saved', 'success', 3000);
        } catch (err) { setNoteErr(errText(err)); }
        finally { setNoteBusy(false); }
    };
    const handleDeleteNote = async (noteId) => { const ok = await confirm('DELETE NOTE', 'Delete this note? The audit log keeps its words.', 'danger', 'DELETE NOTE'); if (!ok) return; try { await landService.deleteStandaloneNote(noteId); await loadFolderData(); toast('Note deleted', 'warn', 3000); } catch (err) { toast('NOTE NOT DELETED: ' + errText(err), 'error'); } };
    // fix165/167: the payment and its receipt travel TOGETHER; the payer (one owner) and what it is for are recorded.
    // fix173: openPayModal('STORAGE') opens it on the STORAGE FEE choice (used by COLLECT SET-ASIDE FEES)
    const openPayModal = (startType) => {
        setPayAmount(''); setPayNotes(''); setPayErr(''); setPayReceipt(null);
        setPayType(startType === 'STORAGE' ? 'STORAGE' : 'TITLE');
        setPayerId(payers.length === 1 ? payers[0].id : '');
        setPayModal({ open: true });
    };
    const closePayModal = () => { if (paying) return; setPayModal({ open: false }); setPayErr(''); setPayReceipt(null); };
    const handleRecordPayment = async () => {
        if (paying) return;
        const amt = Number(payAmount);
        const limit = payType === 'STORAGE' ? feesUnpaid : workOwed;
        if (!payAmount || !Number.isFinite(amt) || amt <= 0) { setPayErr('ENTER A VALID AMOUNT.'); return; }
        if (!Number.isInteger(amt)) { setPayErr('ENTER WHOLE SHILLINGS ONLY (NO DECIMALS).'); return; }
        if (amt > limit) { setPayErr('TOO MUCH: ONLY UGX ' + fmt(limit) + (payType === 'STORAGE' ? ' OF STORAGE FEES IS UNPAID.' : ' IS OWED ON THE TITLE WORK.') + ' YOU TYPED UGX ' + fmt(amt) + '.'); return; }
        if (payers.length > 1 && !payerId) { setPayErr('PICK WHICH CLIENT PAID.'); return; }
        if (!payReceipt) { setPayErr('ATTACH THE PAYMENT RECEIPT. A PAYMENT CANNOT BE SAVED WITHOUT IT.'); return; }
        if (!SCAN_EXT.includes(fileExt(payReceipt.name))) { setPayErr('THE RECEIPT MUST BE A PDF, JPG, PNG OR WEBP FILE.'); return; }
        if (!payReceipt.size) { setPayErr('THE RECEIPT FILE IS EMPTY. SCAN OR PHOTOGRAPH IT AGAIN.'); return; }
        if (payReceipt.size > 10 * 1024 * 1024) { setPayErr('THE RECEIPT IS OVER 10 MB. USE A SMALLER SCAN.'); return; }
        setPaying(true); setPayErr('');
        if (!payRequestId.current) payRequestId.current = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : String(Date.now()) + Math.random().toString(36).slice(2);
        try {
            const stamp = todayISO();
            const receiptName = 'Receipt - ' + (payType === 'STORAGE' ? 'Storage Fee' : 'Title Payment') + ' - UGX ' + amt + ' - ' + stamp + '.' + fileExt(payReceipt.name);
            await recoveryService.recordPayment(id, amt, payNotes.trim(), new File([payReceipt], receiptName, { type: payReceipt.type }), payerId || null, payType, payRequestId.current);
            payRequestId.current = null;
            setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE'); setPayReceipt(null);
            await loadFolderData();
            toast('Payment recorded. Receipt filed under Payment Receipts.', 'success', 4500);
        } catch (err) { setPayErr(errText(err)); }
        finally { setPaying(false); }
    };
    const getDocUrl = (filePath) => { if (!filePath) return '#'; if (filePath.startsWith('http')) return filePath; const parts = filePath.split(/ge_uploads[/]/); const rel = parts.length > 1 ? parts[1] : filePath; const base = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1'; return base + '/vault/' + rel.replace(/\\/g, '/'); };
    // fix175: View opens the file in a tab as a typed blob so PDFs/images show in the browser instead of downloading
    // fix177: View opens the Intake-style preview window (sized to the document, always on screen) instead of a new tab
    const [docPreview, setDocPreview] = useState(null);
    const docUrlRef = useRef(null);
    const closeDocPreview = () => { if (docUrlRef.current) { URL.revokeObjectURL(docUrlRef.current); docUrlRef.current = null; } setDocPreview(null); };
    useEffect(() => {
        if (!docPreview) return undefined;
        const onKey = (e) => { if (e.key === 'Escape') closeDocPreview(); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [docPreview]);
    useEffect(() => () => { if (docUrlRef.current) URL.revokeObjectURL(docUrlRef.current); }, []);
    const handleOpenDoc = async (filePath, fileName) => {
        if (!filePath) return;
        const url = getDocUrl(filePath);
        const isHttp = filePath.startsWith('http');
        const clean = filePath.split('?')[0];
        const ext = fileExt(clean);
        const mime = { pdf: 'application/pdf', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' }[ext];
        let name = fileName;
        if (!name) { try { name = decodeURIComponent(clean.split(/[\\/]/).pop() || 'Document'); } catch (e) { name = 'Document'; } }
        try {
            const r = await fetch(url, { headers: isHttp ? {} : { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } });
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const raw = await r.blob();
            const blob = mime ? new Blob([raw], { type: mime }) : raw;
            const isPdf = ext === 'pdf' || blob.type === 'application/pdf';
            const isImg = !isPdf && String(blob.type || '').startsWith('image/');
            if (!isPdf && !isImg) { const o = URL.createObjectURL(blob); window.open(o, '_blank'); setTimeout(() => URL.revokeObjectURL(o), 60000); return; }
            const href = URL.createObjectURL(blob);
            let ratio = 0.707; // A4 portrait fallback
            try {
                if (isPdf) {
                    const txt = new TextDecoder('latin1').decode(await blob.slice(0, 3000000).arrayBuffer());
                    const mb = txt.match(/\/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]/);
                    if (mb) {
                        let w = Math.abs(mb[3] - mb[1]); let h = Math.abs(mb[4] - mb[2]);
                        const rot = txt.match(/\/Rotate\s+(-?\d+)/);
                        if (rot && Math.abs(parseInt(rot[1], 10)) % 180 === 90) { const t = w; w = h; h = t; }
                        if (w > 0 && h > 0) ratio = w / h;
                    }
                } else {
                    ratio = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im.naturalWidth / im.naturalHeight); im.onerror = rej; im.src = href; });
                }
            } catch (err) { /* keep the portrait default */ }
            ratio = Math.min(4, Math.max(0.25, ratio || 0.707));
            if (docUrlRef.current) URL.revokeObjectURL(docUrlRef.current);
            docUrlRef.current = href;
            setDocPreview({ name, url: href, isPdf, ratio });
        } catch (err) { window.open(url, '_blank'); }
    };
    const sg = useMemo(() => (key) => predictionService.getSuggestions(key) || [], []);

    if (loading) return (<div className={styles.container}><div className={styles.skeletonPage}><div className={styles.skeletonTermHeader} /><div className={styles.skeletonHUD} /><div className={styles.skeletonPanel}><div className={styles.skeletonHeader} /><div className={styles.skeletonBody}><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /></div></div><div className={styles.skeletonPanel}><div className={styles.skeletonHeader} /><div className={styles.skeletonBody}><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /></div></div></div></div>);
    if (loadError || !binder || !buffer) return (<div style={{ padding: 'clamp(40px,8vw,80px) clamp(20px,4vw,40px)' }}><ErrorMessage type="error" title="Record not found" message="This archive entry could not be loaded." onRetry={loadFolderData} retryLabel="Try Again" /></div>);

    const project = binder.project;
    const isDeleted = !!project.deleted;
    const isReleased = !!project.landTitle?.isReleased;
    const isReceivable = !!project.isReceivable;
    const isLegacyProject = !!project.isLegacy;
    const isBacklog = !project.landTitle;
    const canEdit = canEditRole && !isDeleted;
    // fix180: project type, Title Details by type, clients (who pay) / owners / neighbors, subdivision plots
    const pType = projectTypeOf(project);
    const showTitleFields = titleShown(project, buffer);
    const owners = project.proprietors || [];
    const clients = project.clients || [];
    const payers = clients.length ? clients : owners;
    const ownerOptions = payers.map(o => ({ value: o.id, label: o.fullName }));
    const neighbors = binder.neighbors || [];
    const subdivisions = binder.subdivisions || [];
    const docsByStatus = new Map();
    (binder.documents || []).forEach(d => { if (d.statusId) { if (!docsByStatus.has(d.statusId)) docsByStatus.set(d.statusId, []); docsByStatus.get(d.statusId).push(d); } });
    const docCount = (binder.documents || []).length;
    const UNCATEGORISED = '__NONE__';
    const catLabel = (code) => (docCats.find(c => c.code === code)?.label) || String(code).replace(/_/g, ' ');
    const catOptions = docCats.map(c => ({ value: c.code, label: c.label }));
    const docGroups = (() => {
        const groups = new Map();
        (binder.documents || []).forEach(d => {
            const key = d.category || (docCats.some(c => c.code === d.fileType) ? d.fileType : UNCATEGORISED);
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(d);
        });
        const rank = (k) => { if (k === UNCATEGORISED) return 9999; const i = docCats.findIndex(c => c.code === k); return i < 0 ? 9000 : i; };
        return [...groups.entries()].sort((a, b) => rank(a[0]) - rank(b[0]));
    })();
    const docsById = new Map((binder.documents || []).map(d => [d.id, d]));
    // fix180: the status a document was attached to (names come from the documents' own status list on the page)
    const statusNamesById = new Map((binder.statuses || []).map(st => [st.id, st.statusName]));
    const statusNameOf = (sid) => statusNamesById.get(sid) || '';
    const notes = binder.notes || [];
    const noteCount = notes.length;
    const paymentCount = payments.length;
    // fix162: which payments have been reversed (a REVERSAL line points at its original by id)
    const reversedIds = new Set(payments.filter(p => p.paymentType === 'REVERSAL' && p.notes)
        .map(p => { const m = String(p.notes).match(/^\[REVERSAL OF ([0-9a-fA-F-]{36})\]/); return m ? m[1] : null; }).filter(Boolean));
    const totalValue = Number(project.totalCost || 0);
    const amountPaid = Number(project.amountPaid || 0);
    const storageFees = Number(project.storageFeesAccumulated || 0);
    const storagePaid = Number(project.storageFeesPaid || 0);
    const feesUnpaid = Math.max(0, storageFees - storagePaid);
    const keptFees = !isReceivable ? feesUnpaid : 0;                 // fix167: fees kept by SET ASIDE
    const workOwed = Math.max(0, totalValue - (amountPaid - storagePaid));
    const receivableAmountOwed = Math.max(0, totalValue + storageFees - amountPaid);
    const activeAmountOwed = Math.max(0, totalValue - amountPaid);
    const amountOwed = isReceivable ? receivableAmountOwed : activeAmountOwed;
    const arrearsEdit = (Number(buffer?.totalCost) || 0) - (Number(buffer?.initialPayment) || 0);
    const costChanged = isEditing && (Number(buffer?.totalCost) || 0) !== (Number(project.totalCost) || 0);
    const paidPct = totalValue > 0 ? amountPaid / totalValue : 1;
    const isCritical = !isReceivable && !isReleased && totalValue > 0 && paidPct < 0.25;   // same rule as the Ledger
    const fullyPaid = totalValue > 0 && amountOwed <= 0;
    const effectiveRate = project.storageFeeOverride !== null && project.storageFeeOverride !== undefined ? Number(project.storageFeeOverride) : defaultRate;
    const pausedUntil = project.negotiationDeadline ? fmtDate(project.negotiationDeadline) : '';
    const isPaused = !!project.negotiationDeadline || !!project.storagePaused;
    const plotName = project.landTitle?.plotNumber || ('#' + project.projectIndex);
    const reasonCfg = REASON_KINDS[reasonModal.kind] || {};

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing && !uploadDraft} />
            <div className={styles.printDossierHeader} aria-hidden="true">
                <div className={styles.printDossierMeta}>
                    <span><strong>PLOT NUMBER:</strong> {project.landTitle?.plotNumber || '#' + project.projectIndex}</span>
                    <span><strong>TYPE:</strong> {pType.label}</span>
                    <span><strong>TENURE:</strong> {project.landTitle?.tenure || '---'}</span>
                    {project.district && <span><strong>DISTRICT:</strong> {project.district}</span>}
                    <span><strong>STATUS:</strong> {project.status}</span>
                </div>
            </div>
            <div className={styles.printStatement} aria-hidden="true">
                <h3>PAYMENT STATEMENT - PROJECT #{project.projectIndex}</h3>
                <table><thead><tr><th>DATE</th><th>TYPE</th><th>FOR</th><th>PAID BY</th><th>AMOUNT (UGX)</th><th>RECORDED BY</th></tr></thead>
                    <tbody>{payments.map((p, i) => (<tr key={p.id || i}><td>{fmtDate(p.timestamp)}</td><td>{TYPE_LABELS[p.paymentType] || p.paymentType}</td><td>{p.allocation === 'STORAGE' ? 'STORAGE FEES' : 'TITLE'}</td><td>{p.payerName || '---'}</td><td>{fmt(p.amountPaid)}</td><td>{p.recordedBy}</td></tr>))}</tbody></table>
                <p>TOTAL PAID: UGX {fmt(amountPaid)} | STORAGE FEES: UGX {fmt(storageFees)} | BALANCE OWED: UGX {fmt(amountOwed)}</p>
            </div>
            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{plotName}</h1>
                    <div className={styles.metaLine}>
                        {project.landTitle && <span className={styles.idSub} title="Project index (never changes)">#{project.projectIndex}</span>}
                        <span className={`${styles.textBadge} ${styles.badgeActive}`} title="Project type">{pType.label.toUpperCase()}</span>
                        {project.parentProjectId && <button type="button" className={`${styles.textBadge} ${styles.badgeLegacy} ${styles.typeBadgeLink}`} onClick={() => navigate('/folder/' + project.parentProjectId)}
                            title="This Transfer of Title was made from a subdivision plot. Open the subdivision project.">FROM #{binder.parentProjectIndex || '---'} PLOT {project.parentSubdivisionNo}</button>}
                        {isDeleted && <span className={`${styles.textBadge} ${styles.badgeProblem}`} title={'Deleted' + (project.deletedAt ? ' on ' + fmtDate(project.deletedAt) : '') + '. The root user can restore it from Settings > Archive.'}>DELETED</span>}
                        {isBacklog ? <span className={`${styles.textBadge} ${styles.badgeBacklog}`} title="No title details saved on this project.">PROCESSING</span>
                            : <span className={`${styles.textBadge} ${styles.badgeTitled}`} title="The title details are saved.">TITLED</span>}
                        {isReceivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`} title="In receivables: storage fees are added every 30 days.">IN RECEIVABLES</span>
                            : fullyPaid ? <span className={`${styles.textBadge} ${styles.badgeTitled}`} title="Nothing is owed on this project.">FULLY PAID</span>
                            : isCritical ? <span className={`${styles.textBadge} ${styles.badgeCritical}`} title="Less than 25% of the total cost has been paid (same rule as the Ledger).">CRITICAL</span>
                            : totalValue > 0 ? <span className={`${styles.textBadge} ${styles.badgeActive}`} title={'UGX ' + fmt(amountOwed) + ' still owed.'}>ACTIVE</span> : null}
                        {isReleased && <span className={`${styles.textBadge} ${styles.badgeReleased}`} title={'Handed over' + (project.landTitle.releasedAt ? ' on ' + fmtDate(project.landTitle.releasedAt) : '') + (project.landTitle.releasedBy ? ' by ' + project.landTitle.releasedBy : '') + '.'}>RELEASED</span>}
                        {isLegacyProject && <span className={`${styles.textBadge} ${styles.badgeLegacy}`} title="Entered as a Legacy Titles project (an old title brought into the system).">LEGACY</span>}
                        {project.problem && <span className={`${styles.textBadge} ${styles.badgeProblem}`} title={'PROBLEM' + (project.problemBy ? ' flagged by ' + project.problemBy : '') + (project.problemAt ? ' on ' + fmtDate(project.problemAt) : '') + (project.problemNote ? ': ' + project.problemNote : '')}>PROBLEM</span>}
                        {isReceivable && isPaused && <span className={`${styles.textBadge} ${styles.badgePaused}`} title="No storage fees are added while paused. The paused days are not charged later.">{pausedUntil ? 'FEES PAUSED UNTIL ' + pausedUntil : 'FEES PAUSED'}</span>}
                        {keptFees > 0 && <span className={`${styles.textBadge} ${styles.badgePaused}`} title="Storage fees kept when this project was set aside. They are not owed now, but block the hand-over until they are paid, or a director waives them or adds them to the cost.">SET-ASIDE FEES UGX {fmt(keptFees)}</span>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {!isEditing && (<div className={styles.ctrlGroup}>
                        <button type="button" className={styles.printBtn} onClick={() => window.print()} aria-label="Print record" title="Print this record (payment statement included)"><FiPrinter aria-hidden="true" /></button>
                        {canEdit && <button type="button" className={styles.ctrlBtnPay} disabled={amountOwed <= 0} title={amountOwed <= 0 ? 'Nothing is owed on this project.' : 'Record a payment with its receipt.'} onClick={openPayModal}><FiDollarSign aria-hidden="true" /> RECORD PAYMENT</button>}
                        {canMoney && !isDeleted && project.landTitle && (isReleased
                            ? (<>
                                <button type="button" className={`${styles.releaseBtn} ${styles.releaseBtnDone}`} disabled title="The client has received the title deed."><FiCheckCircle aria-hidden="true" /> HANDED OVER</button>
                                <button type="button" className={styles.ghostBtn} title="Mark the title as NOT handed over again (reason required)."
                                    onClick={() => openReasonModal({ kind: 'UNDO_RELEASE', title: 'UNDO HAND-OVER', confirmLabel: 'UNDO HAND-OVER',
                                        info: 'This marks the title as NOT handed over again and unlocks the record (status goes back to ' + (isReceivable ? 'RECEIVABLE' : 'ACTIVE') + '). Use it only if the hand-over was recorded by mistake.' })}><FiUnlock aria-hidden="true" /> UNDO</button>
                              </>)
                            : <button type="button" className={styles.releaseBtn} disabled={amountOwed > 0 || !!project.problem || keptFees > 0}
                                onClick={() => openReasonModal({ kind: 'RELEASE', title: 'HAND OVER TITLE', confirmLabel: 'HAND OVER',
                                    info: 'Confirm the client has received the title deed for ' + plotName + '. The record is then locked (a director can UNDO it). Write who collected it and how they were identified.' })}
                                title={amountOwed > 0 ? 'Cannot hand over yet: UGX ' + fmt(amountOwed) + ' is still owed.' : project.problem ? 'Cannot hand over while this plot is flagged as a PROBLEM. Clear the flag first.' : keptFees > 0 ? 'Cannot hand over: UGX ' + fmt(keptFees) + ' of set-aside storage fees must be paid, waived or added to the cost first.' : 'Record that the client has received the title deed (note required).'}><FiCheckCircle aria-hidden="true" /> HAND OVER TITLE</button>)}
                        {canMoney && !isDeleted && project.landTitle && !isReleased && !isLegacyProject && !isReceivable && pType.titleMode !== 'ALWAYS' && (
                            <button type="button" className={styles.ghostBtn} title="Take the saved Title Details off this project (reason required)."
                                onClick={() => openReasonModal({ kind: 'REVERT_TITLE', title: 'REMOVE TITLE DETAILS', confirmLabel: 'REMOVE TITLE DETAILS',
                                    info: 'This removes the saved Title Details (plot ' + (project.landTitle.plotNumber || '---') + ') and un-ticks the Titled status. The old values stay in the audit log. Use it only if the title was entered by mistake. To fix a typo, use EDIT instead.' })}><FiRefreshCw aria-hidden="true" /> REMOVE TITLE DETAILS</button>)}
                        {canEdit && <button type="button" className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem} title={project.problem ? 'Remove the problem flag from this plot (reason required).' : 'Flag this plot as having a problem and alert staff (say what it is).'}><FiAlertTriangle aria-hidden="true" /> {project.problem ? 'CLEAR PROBLEM' : 'FLAG PROBLEM'}</button>}
                        {canEdit && <button type="button" className={styles.unlockMasterBtn} onClick={handleUnlock} disabled={isReleased} title={isReleased ? 'The title has been handed over, so this record is locked. A director can UNDO the hand-over first.' : 'Edit this record.'}><FiUnlock aria-hidden="true" /> EDIT</button>}
                    </div>)}
                    {isEditing && (<div className={styles.ctrlGroup}>
                        {flags.canUseArchive && <button type="button" className={styles.purgeBtn} onClick={handleNuclearPurge} title="Take this project out of every list (Director or Admin, reason required, can be restored)."><FiTrash2 aria-hidden="true" /> DELETE</button>}
                        <button type="button" className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort} title="Throw away the field changes (ticks already saved stay)."><FiX aria-hidden="true" /> CANCEL</button>
                        <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing} title="Save the changes."><FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}</button>
                    </div>)}
                </div>
            </header>
            {isDeleted && (<div className={`${styles.infoStrip} ${styles.infoStripBad}`} role="status"><FiAlertOctagon aria-hidden="true" />
                <span>This project is DELETED{project.deletedAt ? ' (since ' + fmtDate(project.deletedAt) + ')' : ''}. It is hidden from every list and nothing on it can be changed. The root user can restore it from Settings &gt; Archive.</span></div>)}
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                <div className={styles.tabDock}>
                    <div className={styles.tabRow}>
                        {TABS.map(tab => (<button type="button" key={tab} role="tab" aria-selected={activeTab === tab}
                            data-accent={TAB_ACCENTS[tab]}
                            className={activeTab === tab ? styles.tabOn : styles.tab} onClick={() => setActiveTab(tab)} title={'Show ' + tab.toLowerCase()}>
                            <span className={styles.tabFull}>{tab}</span><span className={styles.tabShort}>{TAB_SHORT[tab]}</span>
                        </button>))}
                    </div>
                </div>
            </div>
            <main className={styles.workstationBody} role="tabpanel">
                {activeTab === 'OVERVIEW' && project.problem && (<div className={`${styles.infoStrip} ${styles.infoStripBad}`} role="status"><FiAlertTriangle aria-hidden="true" />
                    <span><strong>PROBLEM</strong>{project.problemBy ? ' flagged by ' + project.problemBy : ''}{project.problemAt ? ' on ' + fmtDateTime(project.problemAt) : ''}: {project.problemNote || 'see the notes.'}</span></div>)}
                {activeTab === 'OVERVIEW' && isReleased && (<div className={`${styles.infoStrip} ${styles.infoStripInfo}`} role="status"><FiCheckCircle aria-hidden="true" />
                    <span><strong>HANDED OVER</strong>{project.landTitle.releasedAt ? ' on ' + fmtDateTime(project.landTitle.releasedAt) : ''}{project.landTitle.releasedBy ? ' by ' + project.landTitle.releasedBy : ''}{project.landTitle.releaseNote ? ': ' + project.landTitle.releaseNote : ''}. The record is locked.</span></div>)}
                {activeTab === 'OVERVIEW' && !project.landTitle && pType.titleMode === 'ALWAYS' && !isEditing && (<div className={`${styles.infoStrip} ${styles.infoStripWarn}`} role="status"><FiInfo aria-hidden="true" />
                    <span>A {pType.label} project keeps Title Details, and they are not saved yet. {canEdit ? 'Press EDIT to enter them.' : 'A manager needs to enter them.'}</span></div>)}
                <section className={styles.hwPanel} aria-label="Plot Details" style={activeTab !== 'OVERVIEW' ? { display: 'none' } : {}}>
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.overview} onClick={() => toggleDrawer('overview')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.overview ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <CornerDecor hideTop />
                        {isEditing ? (<>
                            {!project.landTitle && pType.titleMode === 'OPTIONAL' && (<div className={styles.convertRow}>
                                <button type="button" className={`${styles.convertBtn} ${buffer.titleDetailsEnabled ? styles.convertBtnActive : ''}`}
                                    title={buffer.titleDetailsEnabled ? 'Hide the Title Details fields.' : 'This Topographic Survey has a title: show the Title Details fields.'}
                                    onClick={() => setBuffer(p => ({ ...p, titleDetailsEnabled: !p.titleDetailsEnabled }))}>
                                    <FiCheckCircle aria-hidden="true" /> {buffer.titleDetailsEnabled ? 'NO TITLE DETAILS' : 'ADD TITLE DETAILS'}</button>
                                <span className={styles.inputHint}>Title Details are optional on a Topographic Survey. Saved with SAVE.</span>
                            </div>)}
                            {pType.value === 'SUBDIVISION' && (<div className={styles.inputGrid3}>
                                <SmartInput label="NUMBER OF SUBDIVISIONS" value={buffer.subdivisionCount} required inputMode="numeric" error={fieldErrors.subdivisionCount}
                                    hint="Cannot go below a plot that was already transferred." onChange={e => touchedSetBuffer({ ...buffer, subdivisionCount: e.target.value.replace(/[^0-9]/g, '') })} />
                            </div>)}
                            <div className={styles.inputGrid3}>
                                <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({ ...buffer, district: e.target.value.toUpperCase() })} />
                                <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({ ...buffer, county: e.target.value.toUpperCase() })} />
                                <SmartInput label="SUB-COUNTY" value={buffer.subCounty} showCaps onChange={e => touchedSetBuffer({ ...buffer, subCounty: e.target.value.toUpperCase() })} />
                                <SmartInput label="PARISH" value={buffer.parish} showCaps onChange={e => touchedSetBuffer({ ...buffer, parish: e.target.value.toUpperCase() })} />
                                <SmartInput label="VILLAGE" value={buffer.village} showCaps onChange={e => touchedSetBuffer({ ...buffer, village: e.target.value.toUpperCase() })} />
                                <SmartInput label="AREA" value={buffer.area} onChange={e => touchedSetBuffer({ ...buffer, area: e.target.value })} />
                            </div>
                            {showTitleFields && (<div className={styles.inputGrid3}>
                                <SmartInput ref={firstInputRef} label="PLOT NUMBER" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({ ...buffer, plotNumber: e.target.value.toUpperCase() })} />
                                <SmartSelect label="TENURE" options={['FREEHOLD', 'MAILO', 'LEASEHOLD', 'CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({ ...buffer, tenure: v })} />
                                <SmartInput label="BLOCK" value={buffer.block} showCaps required error={fieldErrors.block} suggestions={sg('block')} onChange={e => touchedSetBuffer({ ...buffer, block: e.target.value.toUpperCase() })} />
                                <SmartInput label="AREA (HECTARES)" value={buffer.areaHectares} required inputMode="decimal" error={fieldErrors.areaHectares} onChange={e => touchedSetBuffer({ ...buffer, areaHectares: e.target.value.replace(/[^0-9.]/g, '') })} />
                                <SmartInput label="VOLUME" value={buffer.volume} showCaps onChange={e => touchedSetBuffer({ ...buffer, volume: e.target.value.toUpperCase() })} />
                                <SmartInput label="FOLIO" value={buffer.folio} showCaps onChange={e => touchedSetBuffer({ ...buffer, folio: e.target.value.toUpperCase() })} />
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>TITLE DATE</label></div>
                                    <HardwareDatePicker value={buffer.titleIssueDate || ''} onChange={v => touchedSetBuffer({ ...buffer, titleIssueDate: v })} ariaLabel="Title date" /></div>
                            </div>)}
                        </>) : (<>
                            <div className={styles.specGroup}>
                                <div className={styles.sectionSubHeader}>LOCATION</div>
                                <div className={styles.readOnlyGrid}>
                                    {[['DISTRICT', project.district], ['COUNTY', project.county], ['SUB-COUNTY', project.subCounty], ['PARISH', project.parish], ['VILLAGE', project.village], ['AREA', project.area]].map(([l, v]) => (
                                        <div key={l} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                                </div>
                            </div>
                            {project.landTitle && (<div className={`${styles.specGroup} ${styles.specGroupDivided}`}>
                                <div className={styles.sectionSubHeader}>TITLE</div>
                                <div className={styles.readOnlyGrid}>
                                    {[['PLOT NUMBER', project.landTitle.plotNumber], ['BLOCK', project.landTitle.block], ['AREA (HA)', project.landTitle.areaHectares != null ? Number(project.landTitle.areaHectares).toLocaleString(undefined, { maximumFractionDigits: 4 }) : ''], ['VOLUME', project.landTitle.volume], ['FOLIO', project.landTitle.folio], ['TENURE', project.landTitle.tenure], ['TITLE DATE', fmtDate(project.landTitle.titleIssueDate)]].map(([l, v]) => (
                                        <div key={l} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                                </div>
                            </div>)}
                        </>)}
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Status Checklist" style={activeTab !== 'OVERVIEW' ? { display: 'none' } : {}}>
                    <DrawerHeader label={'STATUS CHECKLIST - ' + pType.label.toUpperCase()} isOpen={drawers.statusesPanel} onClick={() => toggleDrawer('statusesPanel')} icon={FiCheckCircle} />
                    <div className={`${styles.panelBody} ${drawers.statusesPanel ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <CornerDecor hideTop />
                        <StatusChecklistPanel projectId={id}
                            canEdit={canEdit && isEditing && !isReleased} canRemove={isDirector && !isDeleted && isEditing && !isReleased}
                            toast={toast} confirm={confirm}
                            docsByStatus={docsByStatus} canAttach={canUploadDocs && !isDeleted && !isReleased}
                            onAttach={attachToStatus} onViewDoc={(d) => handleOpenDoc(d.filePath, d.fileName)} />
                        {!isEditing && canEdit && !isReleased && <span className={styles.inputHint}>Press EDIT to tick statuses. The paperclip attaches documents to a status.</span>}
                    </div></div>
                </section>
                {pType.value === 'SUBDIVISION' && (<section className={styles.hwPanel} aria-label="Subdivisions" style={activeTab !== 'OVERVIEW' ? { display: 'none' } : {}}>
                    <DrawerHeader label="SUBDIVISIONS" count={subdivisions.length} isOpen={drawers.subdivisions} onClick={() => toggleDrawer('subdivisions')} icon={FiFolderPlus} />
                    <div className={`${styles.panelBody} ${drawers.subdivisions ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <CornerDecor hideTop />
                        {subdivisions.length === 0 ? (<div className={styles.emptyState}><FiFolderPlus className={styles.emptyIcon} aria-hidden="true" /><span>NO NUMBER OF SUBDIVISIONS SET. PRESS EDIT TO ENTER IT.</span></div>) : (
                            <div className={styles.subdivGrid}>{subdivisions.map(sp => (<div key={sp.number} className={styles.subdivCard}>
                                <span className={styles.subdivNo}>PLOT {sp.number}</span>
                                {sp.transferProjectId
                                    ? (<button type="button" className={styles.subdivLink} onClick={() => navigate('/folder/' + sp.transferProjectId)} title="Open the Transfer of Title project made for this plot">
                                        TRANSFERRED - #{sp.transferProjectIndex}{sp.transferPlotNumber ? ' (' + sp.transferPlotNumber + ')' : ''}</button>)
                                    : (canUploadDocs && !isDeleted
                                        ? <button type="button" className={styles.ghostBtn} title="Start a Transfer of Title project for this plot. Clients and Owners are copied; Title Details and Neighbors start blank."
                                            onClick={() => navigate('/land/new?transferFrom=' + id + '&plot=' + sp.number)}><FiExternalLink aria-hidden="true" /> TRANSFER</button>
                                        : <span className={styles.inputHint}>Not transferred</span>)}
                            </div>))}</div>)}
                        <span className={styles.inputHint}>TRANSFER opens New Project as a Transfer of Title for that plot. The new project is linked back here.</span>
                    </div></div>
                </section>)}
                <div className={styles.financialsStack} style={activeTab !== 'FINANCIALS' ? { display: 'none' } : {}}>
                    <section className={styles.hwPanel} aria-label="Balance Summary">
                        <DrawerHeader label="BALANCE SUMMARY" isOpen={drawers.balance} onClick={() => toggleDrawer('balance')} icon={FiCreditCard} />
                        <div className={`${styles.panelBody} ${drawers.balance ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            <CornerDecor hideTop />
                            {isEditing ? (<div className={styles.inputGrid3}>
                                <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({ ...buffer, totalCost: v })} hint="Changing it needs a reason (box appears below)." />
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>AMOUNT PAID</label><span className={styles.autoCalcBadge}>LOCKED</span></div>
                                    <input className={`${styles.hwInput} ${styles.calcInput}`} value={(Number(buffer.initialPayment) || 0).toLocaleString()} disabled />
                                    <span className={styles.inputHint}>Changes only through RECORD PAYMENT, or REVERSE in Payment History.</span></div>
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>AMOUNT OWED</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                    <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled /></div>
                                {costChanged && (<SmartInput label="REASON FOR COST CHANGE" value={buffer.costChangeReason || ''} required error={fieldErrors.costChangeReason}
                                    onChange={e => touchedSetBuffer({ ...buffer, costChangeReason: e.target.value })} />)}
                            </div>) : (<div className={styles.moneyStatsRow}>
                                <div className={styles.statBox} title="What the work costs (agreed price)."><label>TOTAL COST</label><strong>UGX {fmt(totalValue)}</strong></div>
                                {isReceivable && <div className={`${styles.statBox} ${styles.statRed}`} title="Storage fees added while in receivables."><label>+ STORAGE FEES</label><strong>UGX {fmt(storageFees)}</strong></div>}
                                <div className={`${styles.statBox} ${styles.statGreen}`} title="Every shilling received (title work and storage fees)."><label>PAID</label><strong>UGX {fmt(amountPaid)}</strong></div>
                                <div className={`${styles.statBox} ${amountOwed > 0 ? styles.statRed : styles.statGreen}`} title="What the client still owes right now."><label>AMOUNT OWED</label><strong>UGX {fmt(amountOwed)}</strong></div>
                            </div>)}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Storage Fees" id="receivable-controls">
                        <DrawerHeader label="STORAGE FEES" isOpen={drawers.recv} onClick={() => toggleDrawer('recv')} icon={FiAlertOctagon} />
                        <div className={`${styles.panelBody} ${drawers.recv ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            <CornerDecor hideTop />
                            {!isReceivable ? (<>
                                {keptFees > 0 && (<div className={styles.moneyStatsRow}>
                                    <div className={`${styles.statBox} ${styles.statAmber}`} title="Kept when the project was set aside. Not owed now; they block the hand-over until they are paid, waived or added to the cost."><label>SET-ASIDE FEES (KEPT)</label><strong>UGX {fmt(keptFees)}</strong></div>
                                </div>)}
                                <div className={styles.recvActionRow}>
                                    {canEdit && !isReleased && keptFees > 0 && <button type="button" className={styles.ctrlBtnPay}
                                        title={'Take a payment for the kept fees (receipt required). The project stays set aside and no new fees start. Unpaid: UGX ' + fmt(keptFees)}
                                        onClick={() => openPayModal('STORAGE')}><FiDollarSign aria-hidden="true" /> COLLECT SET-ASIDE FEES</button>}
                                    {canMoney && !isDeleted && !isReleased && amountOwed + keptFees > 0 && <button type="button" className={styles.ghostBtn}
                                        title="Start monthly storage fees on this project (director only, reason required)."
                                        onClick={() => openReasonModal({ kind: 'ENTER', title: 'MOVE TO RECEIVABLES', confirmLabel: 'MOVE TO RECEIVABLES',
                                            info: 'This freezes the balance (UGX ' + fmt(amountOwed + keptFees) + ' owed' + (keptFees > 0 ? ', set-aside fees included' : '') + ') and starts a monthly storage fee of UGX ' + fmt(defaultRate) + ' unless a different rate is set, added every 30 days. Write why.' })}><FiAlertOctagon aria-hidden="true" /> MOVE TO RECEIVABLES</button>}
                                    {canMoney && !isDeleted && keptFees > 0 && (<>
                                        <button type="button" className={styles.ghostBtn} title="Add the kept fees to the total cost (reason required)."
                                            onClick={() => openReasonModal({ kind: 'CAPITALIZE', title: 'ADD FEES TO COST', confirmLabel: 'ADD FEES TO COST', info: 'This adds the UGX ' + fmt(keptFees) + ' of set-aside fees to the total cost (UGX ' + fmt(totalValue) + ' becomes UGX ' + fmt(totalValue + keptFees) + '). Write why.' })}><FiCreditCard aria-hidden="true" /> ADD FEES TO COST</button>
                                        <button type="button" className={styles.ghostBtnDanger} title="Forgive the kept fees (reason required, cannot be undone)."
                                            onClick={() => openReasonModal({ kind: 'WAIVE', title: 'WAIVE SET-ASIDE FEES', confirmLabel: 'WAIVE FEES', info: 'This forgives the UGX ' + fmt(keptFees) + ' of set-aside storage fees. It cannot be undone.' })}><FiTrash2 aria-hidden="true" /> WAIVE FEES</button>
                                    </>)}
                                </div>
                                <span className={styles.inputHint}>Receivables = clients who owe money and have stopped paying. Moving a project there freezes the balance and adds a monthly storage fee (UGX {fmt(defaultRate)} unless another rate is set) every 30 days. Titled projects with no payment for 365 days move there by themselves.</span>
                            </>) : (<>
                                <div className={styles.moneyStatsRow}>
                                    <div className={`${styles.statBox} ${styles.statRed}`} title="All storage fees added so far."><label>FEES ADDED</label><strong>UGX {fmt(storageFees)}</strong></div>
                                    <div className={`${styles.statBox} ${styles.statGreen}`} title="Payments recorded as STORAGE FEE."><label>FEES PAID</label><strong>UGX {fmt(storagePaid)}</strong></div>
                                    <div className={`${styles.statBox} ${feesUnpaid > 0 ? styles.statRed : styles.statGreen}`} title="Storage fees still to pay."><label>FEES UNPAID</label><strong>UGX {fmt(feesUnpaid)}</strong></div>
                                    <div className={styles.statBox} title={'Added every 30 days since ' + fmtDate(project.receivableStartDate) + '.'}><label>MONTHLY RATE</label><strong>{effectiveRate === 0 ? 'NO FEE' : 'UGX ' + fmt(effectiveRate)}</strong></div>
                                </div>
                                {canMoney && !isDeleted && (<div className={styles.storageBlock}>
                                    <div className={styles.rateRow}>
                                        <CurrencyInput label="MONTHLY STORAGE RATE" value={rateFee} onChange={v => setRateFee(v)} placeholder={fmt(defaultRate) + ' (default)'} hint={'Blank = the default ' + fmt(defaultRate) + '. 0 = no more fees. Applies to the coming months only.'} />
                                        <button type="button" className={styles.ghostBtn} title="Save the new monthly rate (reason required)."
                                            onClick={() => openReasonModal({ kind: 'RATE', title: 'CHANGE MONTHLY STORAGE RATE', confirmLabel: 'SAVE RATE',
                                                info: 'New monthly rate: ' + (rateFee === '' ? 'the default (UGX ' + fmt(defaultRate) + ')' : Number(rateFee) === 0 ? 'NO FEE (UGX 0)' : 'UGX ' + fmt(Number(rateFee))) + '. It applies to future months only; fees already added stay as they are. Write why it is changing.' })}><FiSave aria-hidden="true" /> SAVE RATE</button>
                                    </div>
                                    <div className={styles.recvActionRow}>
                                        {isPaused ? (<>
                                            <span className={styles.frozenChip} title="No fees are added while paused; the paused days are never charged.">{pausedUntil ? 'FEES PAUSED UNTIL ' + pausedUntil : 'FEES PAUSED (NO END DATE)'}</span>
                                            <button type="button" className={styles.ghostBtn} title="Start the storage fees again now (reason required)."
                                                onClick={() => openReasonModal({ kind: 'RESUME', title: 'RESUME STORAGE FEES', confirmLabel: 'RESUME FEES', info: 'Fees start again from today. The paused days are not charged. Write why the pause is ending early.' })}><FiUnlock aria-hidden="true" /> RESUME FEES</button>
                                        </>) : freezeOpen ? (<>
                                            <div className={styles.pausePick}><HardwareDatePicker value={pauseUntil} onChange={v => setPauseUntil(v)} ariaLabel="Pause storage fees until" /></div>
                                            <button type="button" className={styles.ghostBtn} title="Pause the fees until the chosen date (reason required)."
                                                onClick={() => {
                                                    if (!pauseUntil) { toast('PICK THE DATE THE PAUSE ENDS FIRST.', 'error'); return; }
                                                    if (pauseUntil <= todayISO()) { toast('THE PAUSE MUST END AFTER TODAY.', 'error'); return; }
                                                    openReasonModal({ kind: 'PAUSE', title: 'PAUSE STORAGE FEES', confirmLabel: 'PAUSE FEES', info: 'No storage fees are added until ' + fmtDate(pauseUntil + 'T12:00:00') + ' (at most 365 days). The paused days are never charged. Write why.' });
                                                }}><FiCheckCircle aria-hidden="true" /> PAUSE FEES</button>
                                            <button type="button" className={styles.ghostBtn} onClick={() => setFreezeOpen(false)} title="Close without pausing"><FiX aria-hidden="true" /></button>
                                        </>) : (
                                            <button type="button" className={styles.ghostBtn} onClick={() => setFreezeOpen(true)} title="Stop adding fees until a date (for example while the client negotiates)."><FiClock aria-hidden="true" /> PAUSE FEES UNTIL A DATE</button>
                                        )}
                                    </div>
                                </div>)}
                                {canMoney && !isDeleted && (<>
                                    <div className={styles.recvActionRow}>
                                        {storageFees > storagePaid && <button type="button" className={styles.ghostBtn} title="Lower the total storage fees after a negotiation (stays in receivables)."
                                            onClick={() => openReasonModal({ kind: 'REDUCE', title: 'REDUCE STORAGE FEES', confirmLabel: 'REDUCE FEES', amountLabel: 'NEW TOTAL STORAGE FEES (UGX)',
                                                info: 'Fees added so far: UGX ' + fmt(storageFees) + (storagePaid > 0 ? ' (UGX ' + fmt(storagePaid) + ' already paid, so the new total cannot go below that)' : '') + '. Type the agreed lower total; the project stays in receivables.' })}><FiDollarSign aria-hidden="true" /> REDUCE FEES</button>}
                                        <button type="button" className={styles.ghostBtn} title="Leave receivables, stop billing, keep the unpaid fees on record (reason required)."
                                            onClick={() => openReasonModal({ kind: 'SET_ASIDE', title: 'SET ASIDE', confirmLabel: 'SET ASIDE',
                                                info: 'This takes the project out of receivables and stops new fees. The UGX ' + fmt(feesUnpaid) + ' of unpaid fees is KEPT on the project (shown as SET-ASIDE FEES) and blocks the hand-over until it is paid, waived or added to the cost.' + (storagePaid > 0 ? ' The UGX ' + fmt(storagePaid) + ' already paid toward fees is moved into the total cost.' : '') })}><FiArchive aria-hidden="true" /> SET ASIDE (KEEP FEES)</button>
                                        <button type="button" className={styles.ghostBtn} title="Leave receivables and add the fees to the total cost (reason required)."
                                            onClick={() => openReasonModal({ kind: 'CAPITALIZE', title: 'ADD FEES TO COST', confirmLabel: 'ADD FEES TO COST',
                                                info: 'This adds the UGX ' + fmt(storageFees) + ' of storage fees to the total cost (UGX ' + fmt(totalValue) + ' becomes UGX ' + fmt(totalValue + storageFees) + ') and takes the project out of receivables.' })}><FiCreditCard aria-hidden="true" /> ADD FEES TO COST</button>
                                        <button type="button" className={styles.ghostBtnDanger} title="Forgive the unpaid fees and leave receivables (reason required, cannot be undone)."
                                            onClick={() => openReasonModal({ kind: 'WAIVE', title: 'WAIVE STORAGE FEES', confirmLabel: 'WAIVE FEES',
                                                info: 'This forgives the UGX ' + fmt(feesUnpaid) + ' of UNPAID storage fees and takes this project out of receivables.' + (storagePaid > 0 ? ' The UGX ' + fmt(storagePaid) + ' already paid stays counted (it moves into the total cost).' : '') + ' It cannot be undone.' })}><FiTrash2 aria-hidden="true" /> WAIVE FEES</button>
                                    </div>
                                    <div className={styles.inputHint}>Fees belong to the whole project. With joint owners, pick who agreed in the reason window; each payment records which owner paid. SET ASIDE, ADD FEES TO COST and WAIVE FEES take the project OUT of receivables. REDUCE FEES keeps it in.</div>
                                </>)}
                            </>)}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                        <DrawerHeader label="PAYMENT HISTORY" isOpen={drawers.history} onClick={() => toggleDrawer('history')} icon={FiActivity} count={paymentCount} />
                        <div className={`${styles.panelBody} ${drawers.history ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            <CornerDecor hideTop />
                            {paymentCount === 0 ? (<div className={styles.emptyState}><FiDollarSign className={styles.emptyIcon} aria-hidden="true" /><span>NO PAYMENTS RECORDED YET</span></div>) : (
                                <div className={styles.paymentList}>{payments.map((pay, i) => {
                                    const isRev = pay.paymentType === 'REVERSAL';
                                    const isStorage = pay.allocation === 'STORAGE' || String(pay.notes || '').startsWith('[STORAGE FEE PAYMENT]');
                                    const receipt = pay.receiptDocumentId ? docsById.get(pay.receiptDocumentId) : null;
                                    const noteText = isRev ? String(pay.notes || '').replace(/^\[REVERSAL OF [^\]]*\]\s*/, '') : String(pay.notes || '').replace(/^\[STORAGE FEE PAYMENT\]\s*/, '');
                                    return (<div key={pay.id || i} id={'payment-' + pay.id} className={styles.paymentRow}>
                                        <div className={styles.payRowLeft}><div className={`${styles.payAmount} ${isRev ? styles.payAmountNeg : ''}`}>UGX {fmt(pay.amountPaid)}</div>
                                            <div className={styles.payMeta}>
                                                <span className={styles.payType}>{TYPE_LABELS[pay.paymentType] || pay.paymentType}</span>
                                                {isStorage && <span className={styles.payStorageChip} title="Paid toward storage fees">STORAGE FEES</span>}
                                                {pay.payerName && <span className={styles.payPayer} title="The owner who paid">paid by {pay.payerName}</span>}
                                                <span className={styles.payBy} title="The staff member who recorded it">recorded by {pay.recordedBy}</span>
                                                {reversedIds.has(pay.id) && <span className={styles.payReversed} title="This payment was cancelled by a REVERSAL line.">REVERSED</span>}
                                            </div>
                                            {noteText && noteText !== 'Payment received' && <div className={styles.payNoteText}>{noteText}</div>}
                                        </div>
                                        <div className={styles.payRowRight}><div className={styles.payDate} title={fmtDateTime(pay.timestamp)}>{fmtDate(pay.timestamp)}</div>
                                            {receipt && <button type="button" className={styles.receiptLink} onClick={() => handleOpenDoc(receipt.filePath, receipt.fileName)} title={'Open the receipt: ' + receipt.fileName}><FiExternalLink aria-hidden="true" /> RECEIPT</button>}
                                            {canMoney && !isDeleted && !isRev && Number(pay.amountPaid) > 0 && !reversedIds.has(pay.id) && !isReleased && (
                                                <button type="button" className={styles.reverseBtn} title="Cancel this payment. The original line stays; a negative REVERSAL line is added (reason required)."
                                                    onClick={() => openReasonModal({ kind: 'REVERSE', paymentId: pay.id, title: 'REVERSE PAYMENT', confirmLabel: 'REVERSE PAYMENT',
                                                        info: 'This cancels UGX ' + fmt(pay.amountPaid) + ' paid on ' + fmtDate(pay.timestamp) + (pay.payerName ? ' by ' + pay.payerName : '') + '. The original line stays in the history, a negative REVERSAL line is added, and the amount paid goes down by the same amount. The receipt stays as proof.' })}>REVERSE</button>)}
                                        </div>
                                    </div>);
                                })}</div>)}
                        </div></div>
                    </section>
                </div>
                {[['clients', 'CLIENTS', 'Client', clients.length ? clients : owners, FiUsers], ['owners', 'OWNERS', 'Owner', owners, FiUsers]].map(([list, title, what, people, Icon]) => (
                <section key={list} className={styles.hwPanel} aria-label={title} style={activeTab !== 'PEOPLE' ? { display: 'none' } : {}}>
                    <DrawerHeader label={title} isOpen={drawers[list]} onClick={() => toggleDrawer(list)} icon={Icon} count={people.length} />
                    <div className={`${styles.panelBody} ${drawers[list] ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <CornerDecor hideTop />
                        {list === 'clients' && !isEditing && <span className={styles.inputHint}>The people who pay for the work. Recovery calls the clients; payments name which client paid.</span>}
                        <div className={styles.ownersGrid2}>
                            {isEditing ? (buffer[list] || []).map((o, idx) => (<div key={idx} className={styles.ownerEditCard}>
                                <SmartInput label={`LEGAL NAME #${idx + 1}`} value={o.fullName} showCaps required error={fieldErrors[list + '_' + idx + '_name']} onChange={e => handlePersonChange(list, idx, 'fullName', e.target.value)} id={`${list}_${idx}_name`} />
                                <SmartInput label="NIN" value={o.nationalId} required error={fieldErrors[list + '_' + idx + '_nin']} onChange={e => handlePersonChange(list, idx, 'nationalId', e.target.value)} onBlur={e => handleNinBlurCheck(list, idx, e.target.value)} id={`${list}_${idx}_nin`} />
                                <SmartInput label="PHONE" value={o.phone} error={fieldErrors[list + '_' + idx + '_phone']} hint="Several numbers: separate with /" onChange={e => handlePersonChange(list, idx, 'phone', e.target.value)} onBlur={e => { const r = normalizePhones(e.target.value); if (r.ok && r.value !== e.target.value) handlePersonChange(list, idx, 'phone', r.value); }} id={`${list}_${idx}_phone`} />
                                <SmartInput label="EMAIL" value={o.email} onChange={e => handlePersonChange(list, idx, 'email', e.target.value)} id={`${list}_${idx}_email`} />
                                <SmartInput label="ADDRESS" value={o.address} onChange={e => handlePersonChange(list, idx, 'address', e.target.value)} id={`${list}_${idx}_addr`} />
                                {(buffer[list] || []).length > 1 && <button type="button" className={styles.ghostBtnDanger} onClick={() => removePerson(list, idx)} title={'Remove this ' + what.toLowerCase()}><FiTrash2 aria-hidden="true" /> REMOVE</button>}
                            </div>)) : people.map((p, i) => (<div key={p.id || i} className={styles.ownerStaticCard}>
                                {p.id ? (
                                    <button type="button" className={styles.ownerNameLink}
                                        onClick={() => navigate('/client/' + p.id)}
                                        title={`Open ${p.fullName}'s full portfolio`}>
                                        {p.fullName}
                                    </button>
                                ) : <h2 className={styles.ownerName}>{p.fullName}</h2>}
                                <div className={styles.infoColumns}>
                                    <div className={styles.infoRow} title="Phone"><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber || '---'}</span></div>
                                    <div className={styles.infoRow} title="Email"><FiMail aria-hidden="true" /><span>{p.email || '---'}</span></div>
                                    <div className={styles.infoRow} title="National ID (NIN)"><FiShield aria-hidden="true" /><span>{p.nationalId || '---'}</span></div>
                                    <div className={styles.infoRow} title="Home address"><FiMapPin aria-hidden="true" /><span>{p.homeAddress || '---'}</span></div>
                                </div>
                            </div>))}
                        </div>
                        {isEditing && (<div className={styles.peopleActions}>
                            <button type="button" className={styles.ghostBtn} onClick={() => addPerson(list)}><FiPlus aria-hidden="true" /> ADD {what.toUpperCase()}</button>
                            {list === 'owners' && <button type="button" className={styles.ghostBtn} onClick={copyClientsToOwners} title="Replace the owners with a copy of the clients"><FiRefreshCw aria-hidden="true" /> COPY FROM CLIENTS</button>}
                        </div>)}
                        {isEditing && <span className={styles.inputHint}>Changes to names and NINs are written to the audit log as OLD -&gt; NEW.</span>}
                    </div></div>
                </section>))}
                <section className={styles.hwPanel} aria-label="Neighbors" style={activeTab !== 'PEOPLE' ? { display: 'none' } : {}}>
                    <DrawerHeader label="NEIGHBORS" isOpen={drawers.neighbors} onClick={() => toggleDrawer('neighbors')} icon={FiMap} count={neighbors.length} />
                    <div className={`${styles.panelBody} ${drawers.neighbors ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <CornerDecor hideTop />
                        {isEditing ? (<>
                            <div className={styles.ownersGrid2}>{(buffer.neighbors || []).map((nb, idx) => (<div key={idx} className={styles.ownerEditCard}>
                                <SmartInput label={`NAME #${idx + 1}`} value={nb.fullName} showCaps required error={fieldErrors['neighbors_' + idx + '_name']} onChange={e => handlePersonChange('neighbors', idx, 'fullName', e.target.value)} id={`neighbors_${idx}_name`} />
                                <SmartInput label="PHONE" value={nb.phone} error={fieldErrors['neighbors_' + idx + '_phone']} onChange={e => handlePersonChange('neighbors', idx, 'phone', e.target.value)} id={`neighbors_${idx}_phone`} />
                                <SmartInput label="SIDE" value={nb.side} showCaps placeholder="e.g. NORTH" onChange={e => handlePersonChange('neighbors', idx, 'side', e.target.value.toUpperCase())} id={`neighbors_${idx}_side`} />
                                <SmartInput label="THEIR PLOT" value={nb.plotNumber} showCaps onChange={e => handlePersonChange('neighbors', idx, 'plotNumber', e.target.value.toUpperCase())} id={`neighbors_${idx}_plot`} />
                                <button type="button" className={styles.ghostBtnDanger} onClick={() => removePerson('neighbors', idx)} title="Remove this neighbor"><FiTrash2 aria-hidden="true" /> REMOVE</button>
                            </div>))}</div>
                            <div className={styles.peopleActions}><button type="button" className={styles.ghostBtn} onClick={() => addPerson('neighbors')}><FiPlus aria-hidden="true" /> ADD NEIGHBOR</button></div>
                        </>) : neighbors.length === 0 ? (<div className={styles.emptyState}><FiMap className={styles.emptyIcon} aria-hidden="true" /><span>NO NEIGHBORS RECORDED</span></div>) : (
                            <div className={styles.ownersGrid2}>{neighbors.map((nb, i) => (<div key={nb.id || i} className={styles.ownerStaticCard}>
                                <h2 className={styles.ownerName}>{nb.fullName}</h2>
                                <div className={styles.infoColumns}>
                                    <div className={styles.infoRow} title="Phone"><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{nb.phone || '---'}</span></div>
                                    <div className={styles.infoRow} title="Which side of the plot"><FiMapPin aria-hidden="true" /><span>{nb.side || '---'}</span></div>
                                    <div className={styles.infoRow} title="Their plot"><FiMap aria-hidden="true" /><span>{nb.plotNumber || '---'}</span></div>
                                </div>
                            </div>))}</div>)}
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Related Projects" style={activeTab !== 'PEOPLE' ? { display: 'none' } : {}}>
                    <DrawerHeader label="RELATED PROJECTS" isOpen={drawers.related} onClick={() => toggleDrawer('related')} icon={FiFolderPlus} count={portfolio.length || undefined} />
                    <div className={`${styles.panelBody} ${drawers.related ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <CornerDecor hideTop />
                        {portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO OTHER PROJECTS FOR THESE OWNERS</span></div>) : (
                            [...new Set(portfolio.map(r => r.sharedOwner))].map(owner => (
                                <div key={owner} className={styles.ownerRelGroup}>
                                    <h4 className={styles.ownerRelName}>{owner}</h4>
                                    <table className={styles.portfolioTable}>
                                        <thead><tr><th>#</th><th>PLOT</th><th>STATUS</th></tr></thead>
                                        <tbody>{portfolio.filter(r => r.sharedOwner === owner).map((r) => (<tr key={r.projectId} onClick={() => navigate('/folder/' + r.projectId)} tabIndex={0} title="Open this folder"
                                            onKeyDown={e => { if (e.key === 'Enter') navigate('/folder/' + r.projectId); }}>
                                            <td>#{r.index}</td><td>{r.plot || '---'}</td>
                                            <td className={styles.relStatus}>
                                                {r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span>
                                                    : r.released ? <span className={`${styles.textBadge} ${styles.badgeReleased}`}>RELEASED</span>
                                                    : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span>
                                                    : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>PROCESSING</span>}
                                                {r.problem && <span className={`${styles.textBadge} ${styles.badgeProblem}`}>PROBLEM</span>}
                                            </td>
                                        </tr>))}</tbody>
                                    </table>
                                </div>)))}
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Documents" style={activeTab !== 'DOCUMENTS' ? { display: 'none' } : {}}>
                    <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')} icon={FiUploadCloud} count={docCount} />
                    <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <CornerDecor hideTop />
                        {docCount === 0 ? ((canUploadDocs && !isDeleted)
                            ? <DocDropzone className={styles.docPrintHide} onClick={() => fileInputRef.current?.click()} title="Add scans (PDF, JPG, PNG or WEBP, up to 50 MB each). You pick a category for each file." />
                            : <div className={styles.emptyState}><FiUploadCloud className={styles.emptyIcon} aria-hidden="true" /><span>NO DOCUMENTS ATTACHED</span></div>) : (
                            <>
                                <DocList className={styles.compactVault}>{docGroups.map(([cat, docs]) => (
                                    <DocGroup key={cat} label={cat === UNCATEGORISED ? 'UNCATEGORISED' : catLabel(cat)} count={docs.length}>
                                        {docs.map((doc) => (
                                            <DocRow key={doc.id} className={styles.docPrintRow} name={doc.fileName}
                                                meta={(doc.statusId && statusNameOf(doc.statusId) ? '[' + statusNameOf(doc.statusId) + '] ' : '') + (doc.uploadedBy || '---') + (doc.uploadedAt ? ' - ' + fmtDate(doc.uploadedAt) : '')} metaTitle="Status / uploaded by / on"
                                                onView={() => handleOpenDoc(doc.filePath, doc.fileName)}
                                                onDelete={(canEdit && !isReleased && doc.category !== 'PAYMENT_RECEIPT') ? () => handleDeleteDoc(doc.id, doc.fileName) : undefined}
                                                locked={doc.category === 'PAYMENT_RECEIPT'} lockTitle="A payment receipt is proof of money received and can never be deleted. Reverse the payment instead." />
                                        ))}
                                    </DocGroup>))}
                                </DocList>
                                {canUploadDocs && !isDeleted && <DocDropzone compact className={styles.docPrintHide} onClick={() => fileInputRef.current?.click()} title="Add scans (PDF, JPG, PNG or WEBP, up to 50 MB each). You pick a category for each file." />}
                            </>)}
                    </div></div>
                </section>
                <div className={styles.tabWrap} style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>
                    <section className={styles.hwPanel} aria-label="Notes">
                        <DrawerHeader label="NOTES" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} count={noteCount} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            <CornerDecor hideTop />
                            {!isDeleted && <button type="button" className={styles.addNoteBtn} onClick={() => { setNoteErr(''); setNoteModal({ open: true, id: null, content: '' }); }} title="Write a note on this project (anyone can).">+ ADD NOTE</button>}
                            {noteCount === 0 ? (<div className={styles.emptyState}><FiInfo className={styles.emptyIcon} aria-hidden="true" /><span>NO NOTES LOGGED YET</span></div>) : (
                                <div className={styles.notebookTimeline}>{notes.map((log, i) => {
                                    const { tag, meta, body } = parseNote(log.notes);
                                    const system = ['PROBLEM', 'PROBLEM CLEARED', 'HANDED OVER', 'HAND-OVER UNDONE'].includes(tag);
                                    return (<article key={log.id || i} className={styles.ruledNote}>
                                        <div className={styles.noteMeta}><time className={styles.noteTime} dateTime={log.timestamp} title={fmtDateTime(log.timestamp)}>{fmtDateTime(log.timestamp)}</time><span className={styles.noteAuthor}>by {log.recordedBy}</span>
                                            {tag && <span className={`${styles.noteChip} ${styles['noteChip_' + (tag === 'PROBLEM CLEARED' || tag === 'HANDED OVER' ? 'ok' : (meta?.tone || 'info'))]}`}>{tag === 'HANDED OVER' || tag === 'PROBLEM CLEARED' || tag === 'HAND-OVER UNDONE' ? tag : (meta?.label || tag)}</span>}
                                            {canEdit && !system && (<div className={styles.actionBlock}>
                                                <button type="button" className={styles.iconBtn} onClick={() => { setNoteErr(''); setNoteModal({ open: true, id: log.id, content: log.notes }); }} title="Edit this note" aria-label="Edit note"><FiEdit3 className={styles.editIcon} aria-hidden="true" /></button>
                                                <button type="button" className={styles.iconBtn} onClick={() => handleDeleteNote(log.id)} title="Delete this note" aria-label="Delete note"><FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>
                                            </div>)}
                                            {system && <span className={styles.lockTag} title="Written by the system for a PROBLEM flag or a hand-over. Kept as a record.">RECORD</span>}
                                        </div>
                                        <p className={styles.noteContent}>{body}</p>
                                    </article>);
                                })}</div>)}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Recovery Calls">
                        <DrawerHeader label="RECOVERY CALLS" isOpen={drawers.calls} onClick={() => toggleDrawer('calls')} icon={FiPhoneCall} count={recoveryCalls.length} />
                        <div className={`${styles.panelBody} ${drawers.calls ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            <CornerDecor hideTop />
                            {recoveryCalls.length === 0 ? (<div className={styles.emptyState}><FiPhoneCall className={styles.emptyIcon} aria-hidden="true" /><span>NO CALLS LOGGED FOR THESE OWNERS</span></div>) : (
                                <div className={styles.callList}>{recoveryCalls.map((c, i) => (<div key={c.id || i} className={styles.callRow}>
                                    <span className={c.tone === 'POSITIVE' ? styles.callGood : c.tone === 'NEGATIVE' ? styles.callBad : styles.callNone}>{c.tag || 'note'}</span>
                                    <span className={styles.callWho}>{c.ownerName}</span>
                                    <span className={styles.callText}>{c.text || ''}</span>
                                    <span className={styles.callWhen} title={fmtDateTime(c.createdAt)}>{fmtDate(c.createdAt)}{c.author ? ' - ' + c.author : ''}</span>
                                </div>))}</div>)}
                            <span className={styles.inputHint}>Calls are logged on the Recovery page (2 calls a month, 14 days apart). Showing the last 20.</span>
                        </div></div>
                    </section>
                </div>
            </main>
            <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp" style={{ display: 'none' }} aria-hidden="true" tabIndex={-1}
                onChange={e => { if (!e.target.files?.length) return; handleVaultAction(Array.from(e.target.files)); e.target.value = ''; }} />
            <UnsavedChangesModal isOpen={guardModalOpen} onStay={handleStay} onLeave={handleLeave} context="Plot Record Edit" />
            <NinMismatchModal isOpen={!!ninMismatch} existingName={ninMismatch?.existingName} enteredName={ninMismatch?.enteredName} onConfirm={handleNinMismatchConfirm} onReject={handleNinMismatchReject} />
            {docPreview && typeof document !== 'undefined' && createPortal(
                <div className={styles.pvOverlay} onClick={closeDocPreview} role="dialog" aria-modal="true" aria-label={docPreview.name}>
                    <div className={styles.pvPanel} onClick={e => e.stopPropagation()}>
                        <header className={styles.pvHead}>
                            <span className={styles.pvTitle} title={docPreview.name}>{docPreview.name}</span>
                            <span className={styles.pvTag}>{docPreview.ratio >= 1 ? 'Landscape' : 'Portrait'}</span>
                            <button type="button" className={modalStyles.closeBtn} onClick={closeDocPreview} aria-label="Close preview" title="Close"><FiX aria-hidden="true" /></button>
                        </header>
                        <div className={styles.pvStage} style={{ '--pv-ratio': docPreview.ratio }}>
                            {docPreview.isPdf
                                ? <iframe className={styles.pvMedia} src={docPreview.url} title={docPreview.name} />
                                : <img className={`${styles.pvMedia} ${styles.pvImg}`} src={docPreview.url} alt={docPreview.name} />}
                        </div>
                    </div>
                </div>, document.body)}
            <HardwareModal isOpen={!!uploadDraft} lockBackdrop onClose={closeUploadDraft} title={uploadDraft && uploadDraft.statusName ? 'UPLOAD DOCUMENTS - ' + uploadDraft.statusName.toUpperCase() : 'UPLOAD DOCUMENTS'}>
                {uploadDraft && (<>
                    {uploadDraft.statusName && <div className={modalStyles.modalInfoBox}>These files are attached to the status &quot;{uploadDraft.statusName}&quot;. They also show in Documents.</div>}
                    <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>CATEGORY FOR ALL {uploadDraft.files.length} FILE(S)</label>
                        <HardwareModalSelect value={uploadDraft.batch} options={catOptions} onChange={setBatchCategory} placeholder="Choose category" emptyText="No categories available" ariaLabel="Category for all files" /></div>
                    <div className={styles.upFileList}>{uploadDraft.files.map((f, i) => (<div key={i} className={styles.upFileRow}>
                        <span className={styles.upFileName} title={f.file.name}>{f.file.name}</span>
                        <HardwareModalSelect compact className={styles.upFileSelect} value={f.category} options={catOptions} onChange={code => setFileCategory(i, code)} placeholder="Category" emptyText="No categories available" ariaLabel={'Category for ' + f.file.name} /></div>))}</div>
                    {newCatOpen ? (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NEW CATEGORY NAME</label>
                        <input type="text" className={modalStyles.modalInput} value={newCatName} maxLength={120} placeholder="e.g. Survey Report" onChange={e => setNewCatName(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleAddCategory(); }} />
                        <div className={styles.upCatActions}>
                            <button type="button" className={styles.addDocBtn} onClick={handleAddCategory} disabled={catBusy || newCatName.trim().length < 2}>SAVE CATEGORY</button>
                            <button type="button" className={styles.addDocBtn} onClick={() => { setNewCatOpen(false); setNewCatName(''); }}>CLOSE</button>
                        </div></div>)
                        : (<button type="button" className={styles.addDocBtn} onClick={() => setNewCatOpen(true)} title="Add a category that is not in the list yet">+ NEW CATEGORY</button>)}
                    <ModalError text={uploadDraft.error} />
                    <div className={modalStyles.modalFooter}>
                        <HardwareButton type="button" onClick={handleUploadConfirm} loading={committing} icon={FiUploadCloud}>UPLOAD</HardwareButton>
                    </div>
                </>)}
            </HardwareModal>
            <HardwareModal isOpen={noteModal.open} lockBackdrop onClose={closeNoteModal} title={noteModal.id ? 'EDIT NOTE' : 'ADD NOTE'}>
                <div className={modalStyles.modalField}><textarea className={`${modalStyles.modalTextarea} ${styles.probBox}`} value={noteModal.content} autoFocus onChange={e => { setNoteModal({ ...noteModal, content: e.target.value }); if (noteErr) setNoteErr(''); }} placeholder="What happened, what was agreed, what comes next..." aria-label="Note content" />
                    <span className={`${styles.probCount} ${noteModal.content.trim().length > NOTE_MAX ? styles.probCountOver : ''}`}>{noteModal.content.trim().length}/{NOTE_MAX}</span></div>
                <ModalError text={noteErr} />
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave} disabled={noteBusy}><FiSave aria-hidden="true" /> {noteBusy ? 'SAVING...' : 'SAVE NOTE'}</button>
                </div>
            </HardwareModal>
            <HardwareModal isOpen={payModal.open} lockBackdrop onClose={closePayModal} title={'RECORD PAYMENT - ' + plotName}>
                {(isReceivable || keptFees > 0) && (<div className={styles.payTypeRow}><div className={styles.payTypeButtons}>
                    <button type="button" className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`} onClick={() => { setPayType('TITLE'); setPayErr(''); }} title={'Money for the title work. Owed: UGX ' + fmt(workOwed)}><FiHome size={12} /> TITLE PAYMENT</button>
                    <button type="button" className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`} onClick={() => { setPayType('STORAGE'); setPayErr(''); }} disabled={feesUnpaid <= 0} title={feesUnpaid <= 0 ? 'No storage fees are unpaid.' : 'Money for storage fees. Unpaid: UGX ' + fmt(feesUnpaid)}><FiArchive size={12} /> STORAGE FEE</button>
                </div></div>)}
                <div className={modalStyles.modalInfoBox}>{payType === 'STORAGE' ? 'Storage fees unpaid: UGX ' + fmt(feesUnpaid) : 'Owed on the title work: UGX ' + fmt(workOwed)}</div>
                {payers.length > 1 && (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>WHICH CLIENT PAID? (REQUIRED)</label>
                    <HardwareModalSelect value={payerId} options={ownerOptions} onChange={v => { setPayerId(v); setPayErr(''); }} placeholder="Choose the client" ariaLabel="Client who paid" /></div>)}
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="text" inputMode="numeric" className={modalStyles.modalInput} placeholder={'e.g. ' + fmt(payType === 'STORAGE' ? feesUnpaid : workOwed)} value={payAmount ? Number(payAmount).toLocaleString() : ''} onChange={e => { setPayAmount(e.target.value.replace(/[^0-9]/g, '')); if (payErr) setPayErr(''); }} /></div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea} value={payNotes} maxLength={500} onChange={e => setPayNotes(e.target.value)} placeholder="e.g. Mobile money, ref 5521..." /></div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>PAYMENT RECEIPT (REQUIRED)</label>
                    <input ref={payReceiptRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" style={{ display: 'none' }} aria-hidden="true" tabIndex={-1} onChange={e => { const f = e.target.files && e.target.files[0]; if (f) { setPayReceipt(f); setPayErr(''); } e.target.value = ''; }} />
                    {payReceipt ? (<div className={styles.recFile}><FiFileText aria-hidden="true" /><span className={styles.recName} title={payReceipt.name}>{payReceipt.name}</span><button type="button" className={styles.recRemove} onClick={() => setPayReceipt(null)} aria-label="Remove receipt" title="Remove this file"><FiX aria-hidden="true" /></button></div>)
                        : (<button type="button" className={styles.addDocBtn} onClick={() => payReceiptRef.current && payReceiptRef.current.click()} title="Choose the receipt scan or photo"><FiPaperclip aria-hidden="true" />&nbsp;ATTACH RECEIPT SCAN</button>)}
                    <span className={styles.recHint}>Saved in this folder's Documents under Payment Receipts. PDF, JPG, PNG or WEBP, up to 10 MB. The payment is NOT saved without it.</span></div>
                <ModalError text={payErr} />
                <div className={modalStyles.modalFooter}>
                    <HardwareButton type="button" onClick={handleRecordPayment} loading={paying} icon={FiDollarSign}>SAVE PAYMENT</HardwareButton>
                </div>
            </HardwareModal>
            <HardwareModal isOpen={reasonModal.open} lockBackdrop onClose={closeReasonModal} title={reasonModal.title}>
                <div className={`${modalStyles.modalInfoBox} ${reasonCfg.danger ? modalStyles.modalInfoBoxDanger : ''}`}>{reasonModal.info}</div>
                {reasonModal.kind === 'REDUCE' && (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>{reasonModal.amountLabel}</label>
                    <input type="text" inputMode="numeric" className={modalStyles.modalInput} value={reasonModal.amount === '' ? '' : Number(reasonModal.amount).toLocaleString()} autoFocus aria-label="New total storage fees"
                        onChange={e => { setReasonModal(m => ({ ...m, amount: e.target.value.replace(/[^0-9]/g, '') })); if (reasonErr) setReasonErr(''); }} /></div>)}
                {reasonCfg.agree && payers.length > 1 && (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>AGREED WITH (OPTIONAL - FEES ARE FOR THE WHOLE PROJECT)</label>
                    <HardwareModalSelect value={reasonModal.agreedWith} options={[{ value: '', label: 'All clients / not one person' }, ...ownerOptions]} onChange={v => setReasonModal(m => ({ ...m, agreedWith: v }))} placeholder="Choose the client" ariaLabel="Client who agreed" /></div>)}
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>{reasonModal.kind === 'RELEASE' ? 'WHO COLLECTED IT? (REQUIRED - SAVED IN THE AUDIT LOG)' : 'REASON (REQUIRED - SAVED IN THE AUDIT LOG)'}</label>
                    <textarea className={`${modalStyles.modalTextarea} ${styles.probBox}`} value={reasonModal.reason} maxLength={300} autoFocus={reasonModal.kind !== 'REDUCE'} placeholder={reasonCfg.ph || 'Write the reason...'} aria-label="Reason"
                        onChange={e => { setReasonModal(m => ({ ...m, reason: e.target.value })); if (reasonErr) setReasonErr(''); }} />
                    <span className={styles.probCount}>{reasonModal.reason.length}/300</span></div>
                <ModalError text={reasonErr} />
                <div className={modalStyles.modalFooter}>
                    <HardwareButton type="button" variant={reasonCfg.danger ? 'danger' : 'primary'} onClick={submitReasonModal} loading={reasonBusy} icon={reasonCfg.danger ? FiAlertTriangle : FiCheckCircle}>{reasonModal.confirmLabel}</HardwareButton>
                </div>
            </HardwareModal>
            <HardwareModal isOpen={problemModal.open} lockBackdrop onClose={closeProblemModal} title={'FLAG PROBLEM - ' + plotName}>
                <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>This flags the plot as a <strong>PROBLEM</strong> and notifies staff. While flagged, the title cannot be handed over. What you write goes into the notes and the audit trail.</div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>WHAT IS THE PROBLEM? (REQUIRED)</label>
                    <textarea className={`${modalStyles.modalTextarea} ${styles.probBox}`} value={problemModal.note} maxLength={500} autoFocus placeholder="e.g. Owner name on the deed plan does not match the ID..." aria-label="Problem description" onChange={e => { setProblemModal(m => ({ ...m, note: e.target.value })); if (probErr) setProbErr(''); }} />
                    <span className={styles.probCount}>{problemModal.note.length}/500</span></div>
                <ModalError text={probErr} />
                <div className={modalStyles.modalFooter}>
                    <HardwareButton type="button" variant="danger" onClick={handleProblemConfirm} loading={probBusy} icon={FiAlertTriangle}>FLAG PROBLEM</HardwareButton>
                </div>
            </HardwareModal>
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />
            {showTopBtn && (<button type="button" className={styles.scrollTopBtn} onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Back to top" title="Back to the top (EDIT, SAVE and the other buttons)"><FiArrowUp aria-hidden="true" /></button>)}
        </div>
    );
};
export default FolderPage;
