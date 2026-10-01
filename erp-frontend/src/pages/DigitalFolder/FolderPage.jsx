// PATH: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
import React, { useState, useEffect, useCallback, useRef, useMemo, forwardRef, useImperativeHandle } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiUnlock, FiX, FiMap, FiUsers, FiCreditCard,
    FiUploadCloud, FiFileText, FiClock,
    FiCheckCircle, FiTrash2, FiEdit3, FiChevronDown,
    FiPhoneCall, FiMail, FiMapPin, FiShield,
    FiInfo, FiAlertTriangle, FiAlertOctagon,
    FiCheckSquare, FiPrinter, FiAlertCircle, FiSave,
    FiDollarSign, FiActivity, FiHome, FiArchive,
FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp, FiPaperclip
} from 'react-icons/fi';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
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
import ErrorMessage from '../../components/common/ErrorMessage';
import CornerDecor from '../../components/ui/CornerDecor';
import styles from './FolderPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

// fix165: a payment can NEVER be saved without its receipt scan (the server refuses it too).
// Do not set this to false: the server would still refuse the payment.
const RECEIPT_REQUIRED = true;
const NOTE_MAX = 2000;
const SCAN_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'webp'];
const fileExt = (name) => { const m = String(name || '').toLowerCase().match(/[.]([a-z0-9]{1,6})$/); return m ? m[1] : ''; };
// fix165: ONE place that turns any failed request into a sentence a person can read.
// Always shows the server's own words and the HTTP number, so a popup error is never just "FAILED".
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
// fix165: red error box that sits INSIDE a popup, so a failure is read where the work is being done.
const ModalError = ({ text }) => (text ? (<div className={styles.modalErr} role="alert">
    <FiAlertCircle className={styles.modalErrIcon} aria-hidden="true" /><span>{text}</span></div>) : null);

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
            <button className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss"><FiX aria-hidden="true" /></button>
        </div>))}
    </div>, document.body);
};
const SavingOverlay = ({ visible }) => {
    if (!visible || typeof document === 'undefined') return null;
    return createPortal(<div className={styles.savingOverlay} role="status" aria-label="Committing to archive">
        <div className={styles.savingSpinner} aria-hidden="true" /><span className={styles.savingLabel}>COMMITTING TO ARCHIVE...</span>
    </div>, document.body);
};
const DrawerHeader = ({ label, count, isOpen, onClick, icon: Icon }) => (
    <div className={styles.drawerHeader} onClick={onClick} role="button" tabIndex={0} aria-expanded={isOpen}
        aria-label={`${label} section, ${isOpen ? 'collapse' : 'expand'}`}
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
            {showCaps && <span className={styles.capsBadge}>CAPS</span>}
        </div>
        <input id={inputId} ref={ref} type="text" className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
            value={value} onChange={onChange} onBlur={onBlur} placeholder={placeholder} inputMode={inputMode} maxLength={maxLength}
            list={datalistId} autoComplete="off" aria-required={required ? 'true' : undefined} aria-invalid={error ? 'true' : 'false'} />
        {datalistId && <datalist id={datalistId}>{suggestions.map((s, i) => <option key={i} value={s} />)}</datalist>}
        {error && <span className={styles.fieldError} role="alert">{error}</span>}
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
            className={`${styles.selectTrigger} ${open ? styles.selectTriggerOpen : ''}`} onClick={() => setOpen(o => !o)}>
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
const CurrencyInput = ({ label, value, onChange, error, id, disabled }) => {
    const [focused, setFocused] = useState(false);
    const inputId = id || 'cur-' + (label || '').replace(/\W/g, '-').toLowerCase();
    const display = focused ? String(value || '') : (value ? Number(value).toLocaleString() : '');
    return (<div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
        <div className={styles.inputLabelRow}><label htmlFor={inputId}>{label}</label><span className={styles.currencyTag}>UGX</span>
            {disabled && <span className={styles.autoCalcBadge}>LOCKED</span>}</div>
        <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''} ${disabled ? styles.calcInput : ''}`}
            inputMode="numeric" value={display} onFocus={() => { if (!disabled) setFocused(true); }} onBlur={() => setFocused(false)}
            onChange={e => { if (!disabled) onChange(e.target.value.replace(/\D/g, '')); }} placeholder="0" disabled={disabled} />
        {error && <span className={styles.fieldError} role="alert">{error}</span>}
    </div>);
};
const useConfirm = () => {
    const [state, setState] = useState({ open: false, title: '', message: '', variant: 'warn', resolve: null });
    const confirm = useCallback((title, message, variant = 'warn') => new Promise(resolve => setState({ open: true, title, message, variant, resolve })), []);
    const handleAnswer = useCallback((answer) => { setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; }); }, []);
    return { confirmState: state, confirm, handleAnswer };
};
const ConfirmModal = ({ state, onAnswer }) => {
    if (!state.open || typeof document === 'undefined') return null;
    const isDanger = state.variant === 'danger';
    return createPortal(<div className={styles.confirmOverlay} role="dialog" aria-modal="true"><div className={styles.confirmBox}>
        <button type="button" className={styles.confirmClose} onClick={() => onAnswer(false)} aria-label="Close"><FiX aria-hidden="true" /></button>
        <div className={`${styles.confirmHeader} ${isDanger ? styles.confirmHeaderDanger : styles.confirmHeaderWarn}`}>
            {isDanger ? <FiAlertOctagon className={styles.confirmIcon} aria-hidden="true" /> : <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" />}
            <span className={styles.confirmTitle}>{state.title}</span></div>
        <p className={styles.confirmMessage}>{state.message}</p>
        <div className={styles.confirmFooter}>
            
            <button type="button" className={`${styles.confirmOkBtn} ${isDanger ? styles.confirmOkDanger : styles.confirmOkWarn}`} onClick={() => onAnswer(true)}>
                {isDanger ? <><FiTrash2 aria-hidden="true" /> CONFIRM ERASE</> : <><FiCheckCircle aria-hidden="true" /> CONFIRM</>}</button>
        </div></div></div>, document.body);
};
const fmt = (n) => Number(n || 0).toLocaleString();

/* STAGE CHECKLIST — restyled to Intake/Ledger family (no inline styles) */
/* STAGE CHECKLIST - mirrors the Intake page stages panel (fix116).
   Rows = the project's attached stages, done stages pre-ticked.
   No money, no notes, no modal: tick to complete, plus to insert below,
   trash to remove. Nothing can be added after the last stage. */
/* STAGE CHECKLIST - Intake mirror (fix117): Intake/Recovery button tones,
   first stage auto-ticked, first & last stages locked from delete,
   RESTORE DEFAULTS like Intake, insert-below never after the last stage. */
const StageChecklistPanel = forwardRef(({ projectId, canEdit, canRemove, toast, confirm, onLastStageToggle, onLoaded }, ref) => {
    const [stages, setStages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [insertAfterId, setInsertAfterId] = useState(null);
    const [insertAfterName, setInsertAfterName] = useState('');
    const [saving, setSaving] = useState(false);
    const [toggling, setToggling] = useState(false);
    const autoTicked = useRef(false);
    const loadStages = useCallback(async () => { try { const list = await stageTemplateService.getProjectStages(projectId) || []; setStages(list); if (onLoaded) onLoaded(list.length); } catch {} finally { setLoading(false); } }, [projectId, onLoaded]);
    useEffect(() => { loadStages(); }, [loadStages]);
    useEffect(() => {
        if (!canEdit || autoTicked.current || loading || !stages.length) return;
        autoTicked.current = true;
        if (!stages[0].isCompleted) {
            stageTemplateService.toggleStageCompletion(projectId, stages[0].id, true).then(loadStages).catch(err => toast && toast('AUTO-TICK FAILED (HTTP ' + (err.response?.status || 'network') + ')', 'error', 6000));
        }
    }, [stages, loading, canEdit, projectId, loadStages]);
    const openInsertBelow = (stage) => { setInsertAfterId(stage.id); setInsertAfterName(stage.stageName); setNewStageName(''); setAddingStage(true); };
    const cancelInsert = () => { setAddingStage(false); setNewStageName(''); setInsertAfterId(null); setInsertAfterName(''); };
    const handleAddStage = async () => {
        const name = newStageName.trim();
        if (!name) { toast && toast('Enter a stage name first.', 'error'); return; }
        if (stages.some(s => (s.stageName || '').toLowerCase() === name.toLowerCase())) { toast && toast('That stage is already on the list.', 'error'); return; }
        setSaving(true);
        try {
            const created = await stageTemplateService.attachStages(projectId, [{ stageName: name, cost: 0, isCustom: true }]);
            const createdIds = (created || []).map(c => c.id).filter(Boolean);
            if (createdIds.length && insertAfterId) {
                const currentIds = stages.map(s => s.id);
                const idx = currentIds.indexOf(insertAfterId);
                const ordered = idx >= 0 ? [...currentIds.slice(0, idx + 1), ...createdIds, ...currentIds.slice(idx + 1)] : [...currentIds, ...createdIds];
            try { await stageTemplateService.reorderProjectStages(projectId, ordered); } catch { await stageTemplateService.reorderProjectStages(projectId, ordered); }
            }
            await loadStages(); cancelInsert(); toast && toast('Stage inserted.', 'success');
} catch (err) { await loadStages(); cancelInsert(); toast && toast('POSITION UPDATE FAILED (HTTP ' + (err.response?.status || 'network') + ') - stage added at the end.', 'error', 9000); } finally { setSaving(false); }
    };
    const handleToggleComplete = async (stage, isLast) => {
        if (toggling) return;   // fix166: a double click used to send two ticks and flip the stage back
        setToggling(true);
        const next = !stage.isCompleted;
        try {
            await stageTemplateService.toggleStageCompletion(projectId, stage.id, next);
            await loadStages();
            // Ticking the final stage means the title is now ready -- hand
            // off to the title panel. Unticking it (a correction) hands
            // back to the stage checklist. See onLastStageToggle in the
            // parent for what this actually does.
            if (isLast && onLastStageToggle) onLastStageToggle(next);
        } catch (err) { await loadStages(); toast && toast('STAGE NOT UPDATED: ' + errText(err), 'error', 12000); }
        finally { setToggling(false); }
    };
    // Lets the parent's single "TITLE READY" button drive the last stage's
    // tick too, so one button covers both "title is ready" and "final stage
    // done" instead of asking the user to keep two controls in sync.
    useImperativeHandle(ref, () => ({
        setLastStageCompletion: async (done) => {
            const last = stages[stages.length - 1];
            if (!last || last.isCompleted === done) return;
            try {
                await stageTemplateService.toggleStageCompletion(projectId, last.id, done);
                await loadStages();
            } catch (err) { toast && toast('Failed to update stage (HTTP ' + (err.response?.status || 'network') + ')', 'error'); }
        },
    }), [stages, projectId, toast, loadStages]);
    const handleRemove = async (stageId) => { try { await stageTemplateService.removeStage(projectId, stageId); await loadStages(); toast && toast('Stage removed.', 'warn'); } catch { toast && toast('Failed to remove stage', 'error'); } };
    const handleRestoreDefaults = async () => {
if (confirm) { const ok = await confirm('RESTORE DEFAULTS', 'Replace the current stage list with the master checklist? Current ticks and custom stages will be lost.', 'warn'); if (!ok) return; }
        setSaving(true);
        try {
            const tpls = await stageTemplateService.getTemplate() || [];
            if (!tpls.length) { toast && toast('The master checklist is empty, so nothing was changed.', 'error', 9000); return; }
            // fix166: the new list is added FIRST and the old one removed AFTER, so a failure half-way can never leave
            // the project with NO stages (it used to delete every stage first and only then try to add the new ones).
            const oldIds = stages.map(s => s.id);
            await stageTemplateService.attachStages(projectId, tpls.map((t, i) => ({ stageTemplateId: t.id, isCustom: false, cost: 0, isCompleted: i === 0 })));
            for (const sid of oldIds) { await stageTemplateService.removeStage(projectId, sid); }
            autoTicked.current = true;
            await loadStages(); cancelInsert(); toast && toast('Default stages restored.', 'success');
        } catch (err) { await loadStages(); toast && toast('DEFAULTS NOT RESTORED: ' + errText(err), 'error', 12000); } finally { setSaving(false); }
    };
    if (loading) return null;
    return (<div className={styles.stageList}>
        {canEdit && (<div className={styles.stageListTop}>
            <button type="button" className={styles.ghostBtn} onClick={handleRestoreDefaults} disabled={saving}><FiRefreshCw aria-hidden="true" /> RESTORE DEFAULTS</button>
            <span className={styles.inputHint}>Ticks save the moment you click them. CANCEL does not undo them.</span>
        </div>)}
        {stages.length === 0 && <div className={styles.emptyState}><FiCheckCircle className={styles.emptyIcon} aria-hidden="true" /><span>NO STAGES ATTACHED YET</span></div>}
        {stages.map((stage, i) => {
            const isFirst = i === 0;
            const isLast = i === stages.length - 1;
            return (<React.Fragment key={stage.id}>
                <label className={`${styles.stageItem} ${stage.isCompleted ? styles.stageItemChecked : ''}`}>
                    <input type="checkbox" className={styles.stageCheckbox} checked={!!stage.isCompleted} disabled={!canEdit || toggling}
                        onChange={() => handleToggleComplete(stage, isLast)} aria-label={`Mark ${stage.stageName} complete`} />
                    <span className={styles.stageItemName}>{stage.stageName}</span>
                    <span className={styles.stageActions}>
                        {canEdit && !isLast && (<button type="button" className={styles.plusBtn} title="Insert a stage below this one"
                            aria-label={`Insert stage below ${stage.stageName}`}
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(stage); }}><FiPlus size={12} /></button>)}
                        {canRemove && !isFirst && !isLast && (<button type="button" className={styles.iconBtnDanger} title="Remove stage"
                            aria-label={`Remove ${stage.stageName}`}
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleRemove(stage.id); }}><FiTrash2 size={12} /></button>)}
                    </span>
                </label>
                {addingStage && insertAfterId === stage.id && (<div className={styles.insertRow}>
                    <span className={styles.insertCtx}>INSERT UNDER: {insertAfterName}</span>
                    <input type="text" className={styles.insertInput} value={newStageName} autoFocus
                        onChange={e => setNewStageName(e.target.value)} placeholder="New stage name"
                        aria-label="New stage name"
                        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddStage(); } if (e.key === 'Escape') cancelInsert(); }} />
                    <HardwareButton type="button" onClick={handleAddStage} loading={saving} icon={FiCheckCircle}>ADD</HardwareButton>
                    <button type="button" className={styles.ghostBtn} onClick={cancelInsert} aria-label="Cancel insert"><FiX aria-hidden="true" /></button>
                </div>)}
            </React.Fragment>);
        })}
    </div>);
});

const FolderPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();

    /* UNIFIED ROLE MATRIX */
    const role = String(user?.role || '').toUpperCase();
    const isRoot = !!user?.isRoot;
    const isAdmin = isRoot || role === 'ROLE_ADMIN';
    const isDirector = isAdmin || role === 'ROLE_DIRECTOR';
    const isManager = isDirector || role === 'ROLE_MANAGER';
    const canEdit = isManager;    // edit record, stages, docs, payments
    const canMoney = isDirector;  // receivable money actions
    const canLog = true;          // any operator may log notes/calls
const canUploadDocs = isManager || role === 'ROLE_SECRETARY'; // add scans without edit mode; delete still needs edit

    const [binder, setBinder] = useState(null);
    const [buffer, setBuffer] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const stageChecklistRef = useRef(null);
    const [committing, setCommitting] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [ninMismatch, setNinMismatch] = useState(null);
    const [payments, setPayments] = useState([]);
    const [portfolio, setPortfolio] = useState([]);
  const [recoveryChips, setRecoveryChips] = useState([]);
    const [recvBusy, setRecvBusy] = useState(false);
    const [freezeOpen, setFreezeOpen] = useState(false);
    const [rateFee, setRateFee] = useState(''); const [rateDeadline, setRateDeadline] = useState('');
    const [activeTab, setActiveTab] = useState(() => {
        const h = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : '';
        return (h.includes('finance') || h.includes('payment')) ? 'FINANCIALS' : 'OVERVIEW';
    });
    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS', 'NOTES'];
    const TAB_ACCENTS = { OVERVIEW: 'orange', FINANCIALS: 'cyan', OWNERS: 'violet', DOCUMENTS: 'slate', NOTES: 'red' };
    const [noteModal, setNoteModal] = useState({ open: false, id: null, content: '' });
    const [noteErr, setNoteErr] = useState(''); const [noteBusy, setNoteBusy] = useState(false);
    const [payModal, setPayModal] = useState({ open: false });
    const [stageCount, setStageCount] = useState(0);
    const [payAmount, setPayAmount] = useState(''); const [payNotes, setPayNotes] = useState('');
    const [payType, setPayType] = useState('TITLE'); const [paying, setPaying] = useState(false);
    // fix138: receipt for the payment being recorded + the PROBLEM window
    const [payReceipt, setPayReceipt] = useState(null);
    const payReceiptRef = useRef(null);
    const [payErr, setPayErr] = useState('');
    useEffect(() => { if (!payModal.open) { setPayReceipt(null); setPayErr(''); } }, [payModal.open]);
    const [problemModal, setProblemModal] = useState({ open: false, note: '' });
    // fix162: ONE reason window for the money actions that need a written reason
    const [reasonModal, setReasonModal] = useState({ open: false, kind: '', title: '', info: '', confirmLabel: '', amountLabel: '', amount: '', reason: '', paymentId: null });
    const [reasonBusy, setReasonBusy] = useState(false);
    const [probBusy, setProbBusy] = useState(false);
    const [probErr, setProbErr] = useState('');
    const [reasonErr, setReasonErr] = useState('');
    const [drawers, setDrawers] = useState({ overview: true, balance: true, recv: true, history: true, notes: true, owners: true, related: true, docs: true, stagesPanel: true });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));
    const { confirmState, confirm, handleAnswer } = useConfirm();
    const firstInputRef = useRef(null);
    const fileInputRef = useRef(null);
    // fix136: document categories + the UPLOAD DOCUMENTS window
    const [docCats, setDocCats] = useState([]);
    const [uploadDraft, setUploadDraft] = useState(null); // { batch, files: [{ file, category }] }
    const [newCatOpen, setNewCatOpen] = useState(false);
    const [newCatName, setNewCatName] = useState('');
    const [catBusy, setCatBusy] = useState(false);
    const loadDocCats = useCallback(async () => { try { setDocCats(await landService.getDocumentCategories()); } catch { /* headings fall back to the raw code */ } }, []);
    useEffect(() => { loadDocCats(); }, [loadDocCats]);
    const touchedRef = useRef(false);
    const touchedSetBuffer = React.useCallback((updater) => { touchedRef.current = true; setBuffer(updater); }, []);
    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(!committing && isEditing);
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

    useEffect(() => {
        const t = setTimeout(() => {
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
        }, 150);
        return () => clearTimeout(t);
    }, []);
    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-') || hash === 'record-payment' || hash === 'storage-fees') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                if (hash === 'record-payment') { if (canEdit) setPayModal({ open: true }); }
                else if (hash === 'storage-fees') { const el = document.getElementById('receivable-controls'); if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); el.classList.add(styles.highlightRow); setTimeout(() => el.classList.remove(styles.highlightRow), 3000); } }
                else if (hash.startsWith('payment-')) { const el = document.getElementById(hash); if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.classList.add(styles.highlightRow); setTimeout(() => el.classList.remove(styles.highlightRow), 3000); } }
                else { const el = document.getElementById('paymentHistorySection'); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
            }, 350);
        } else if (hash === 'notes' || hash === 'calls') setActiveTab('NOTES');
        else if (hash === 'identity' || hash === 'owners') setActiveTab('OWNERS');
        else if (hash === 'vault' || hash === 'documents') setActiveTab('DOCUMENTS');
        else window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [id, canEdit]);
    useEffect(() => { if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120); }, [isEditing]);
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const action = params.get('action');
        if (!action || !binder) return;
        if (!canEdit && (action === 'pay' || action === 'storage')) { toast('Only a manager or director can record payments.', 'error', 6000); return; }
        if (action === 'pay') { setActiveTab('FINANCIALS'); setTimeout(() => { setPayType('TITLE'); setPayAmount(''); setPayNotes(''); setPayModal({ open: true }); }, 400); }
        else if (action === 'storage') { setActiveTab('FINANCIALS'); setTimeout(() => { setPayType(binder.project?.isReceivable ? 'STORAGE' : 'TITLE'); setPayAmount(''); setPayNotes(''); setPayModal({ open: true }); }, 400); }
    }, [location.search, binder]);
    useEffect(() => {
        const t = setInterval(() => {
            if (!isEditing || committing) return;
            // fix166: the page used to SAVE EVERYTHING BY ITSELF after 5 minutes of silence, whatever half-finished
            // thing was typed (a cost, an owner, a plot number). Nothing is saved without a click now; it only reminds.
            if (Date.now() - lastActiveRef.current > 10 * 60 * 1000) {
                lastActiveRef.current = Date.now();
                toast('You have unsaved edits open. Nothing is saved automatically - press SAVE, or CANCEL to throw them away.', 'warn', 15000);
            }
        }, 15000);
        return () => clearInterval(t);
    });
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
                setBuffer({
                    plotNumber: data.project?.landTitle?.plotNumber || '', tenure: data.project?.landTitle?.tenure || 'MAILO',
                    blockRoad: data.project?.landTitle?.blockRoad || '', district: data.project?.district || '',
                    county: data.project?.county || '', subCounty: data.project?.subCounty || '',
                    parish: data.project?.parish || '', village: data.project?.village || '', area: data.project?.area || '',
                    titleId: data.project?.landTitle?.titleId || '', convertToTitle: false,
                    totalCost: String(data.project?.totalCost || 0), initialPayment: String(data.project?.amountPaid || 0),
                    isLegacy: data.project?.isLegacy || false,
                    owners: (data.project?.proprietors || []).map(p => ({ fullName: p.fullName || '', phone: p.phoneNumber || '', nationalId: p.nationalId || '', address: p.homeAddress || '', email: p.email || '' })),
                });
                setFieldErrors({});
            }
        } catch { setLoadError(true); } finally { setLoading(false); }
    }, [id, isEditing]);
    useEffect(() => { loadFolderData(); loadPortfolio(); }, [loadFolderData, loadPortfolio]);
  useEffect(() => {
    if (!binder?.project?.proprietors) return;
    Promise.all(binder.project.proprietors.map(p => recoveryService.getNotes(p.id).catch(() => [])))
      .then(lists => {
        const all = lists.flat().filter(n => n.source === 'RECOVERY').sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 20);
        setRecoveryChips(all);
      });
  }, [binder]);
    useEffect(() => {
        if (!binder?.project) return;
        setRateFee(Number(binder.project.storageFeeOverride) > 0 ? String(binder.project.storageFeeOverride) : '');
        setRateDeadline(binder.project.negotiationDeadline ? String(binder.project.negotiationDeadline).slice(0, 16) : '');
    }, [binder]);

    const validateBuffer = (buf, hasTitle) => {
        const errors = [];
        if (hasTitle) {
            if (!buf.plotNumber?.trim()) errors.push('PLOT ID IS REQUIRED');
            if (!buf.tenure?.trim()) errors.push('TENURE IS REQUIRED');
        }
        if (!buf.district?.trim()) errors.push('DISTRICT IS REQUIRED');
        buf.owners?.forEach((o, i) => {
            if (!o.fullName?.trim()) errors.push('OWNER ' + (i + 1) + ': LEGAL NAME IS REQUIRED');
            if (!o.nationalId?.trim()) errors.push('OWNER ' + (i + 1) + ': NATIONAL ID (NIN) IS REQUIRED');
            if (o.phone?.trim()) { const ph = normalizePhones(o.phone); if (!ph.ok) errors.push('OWNER ' + (i + 1) + ': ' + ph.error.toUpperCase()); }
        });
        return errors;
    };

    const handleCommit = async () => {
        if (ninMismatch) { toast('Confirm or fix the NIN mismatch warning before saving.', 'error', 6000); return; }
        const hasTitle = !!project.landTitle || !!buffer.convertToTitle;
        const errors = validateBuffer(buffer, hasTitle);
        if (errors.length) {
            const fe = {};
            if (hasTitle && !buffer.plotNumber?.trim()) fe.plotNumber = 'Required';
            if (!buffer.district?.trim()) fe.district = 'Required';
            buffer.owners?.forEach((o, i) => { if (!o.fullName?.trim()) fe['owner_' + i + '_name'] = 'Required'; if (o.phone?.trim() && !normalizePhones(o.phone).ok) fe['owner_' + i + '_phone'] = 'Check number'; });
            setFieldErrors(fe); toast('VALIDATION FAILED: ' + errors[0], 'error', 6000); return;
        }
        if ((Number(buffer.totalCost) || 0) !== (Number(project.totalCost) || 0) && (buffer.costChangeReason || '').trim().length < 5) {
            setFieldErrors({ costChangeReason: 'Required' }); toast('WRITE WHY THE TOTAL COST CHANGED (AT LEAST 5 CHARACTERS)', 'error', 6000); return;
        }
        setFieldErrors({}); setCommitting(true);
        try {
            await landService.updateMasterFolder(id, { ...buffer, totalCost: Number(buffer.totalCost) || 0, initialPayment: Number(buffer.initialPayment) || 0, costChangeReason: (buffer.costChangeReason || '').trim(), expectedTotalCost: Number(project.totalCost) || 0 });
            predictionService.learn(buffer); touchedRef.current = false; setIsEditing(false);
            await loadFolderData(); toast('Changes saved successfully', 'success');
        } catch (err) { toast('SAVE FAILED: ' + errText(err), 'error', 12000); }
        finally { setCommitting(false); }
    };
    const handleUnfreeze = async () => { try { await folderPortalService.settings(id, { deadline: '' }); setRateDeadline(''); setFreezeOpen(false); await loadFolderData(); toast('Fees resumed.', 'info'); } catch (err) { toast('RESUME FAILED: ' + errText(err), 'error', 12000); } };
    const handleRelease = async () => { const ok = await confirm('HAND OVER TITLE', 'Confirm the client has received the title deed. This marks the plot RELEASED and is recorded in the audit log. It cannot be undone from this page.', 'warn'); if (!ok) return; try { await landService.authorizeRelease(id, 'Released from folder page'); await loadFolderData(); toast('Title handed over. Plot is now RELEASED.', 'success'); } catch (err) { toast('HAND OVER FAILED: ' + errText(err), 'error', 12000); } };
    // fix165: a PROBLEM flag must say what the problem is (5+ characters). The flag and its note are saved
    // as two steps; if the note step fails the flag stays and the person is told exactly that.
    const runToggleProblem = async (text) => {
        const was = project.problem; const note = (text || '').trim();
        if (!was && note.length < 5) { const m = 'WRITE WHAT THE PROBLEM IS (AT LEAST 5 CHARACTERS).'; setProbErr(m); toast(m, 'error', 8000); return false; }
        try { await folderPortalService.toggleProblem(id, note); }
        catch (err) { const m = errText(err); setProbErr(m); toast('FLAG FAILED: ' + m, 'error', 12000); return false; }
        let noteSaved = true;
        if (!was && note) { try { await landService.addStandaloneNote(id, '[PROBLEM] ' + note); } catch { noteSaved = false; } }
        await loadFolderData();
        if (!was && !noteSaved) toast('Flagged as PROBLEM, but the note did NOT save. Add it again from the NOTES tab.', 'warn', 12000);
        else toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn');
        return true;
    };
    // fix138: flagging opens the Golden Seed PROBLEM window (no browser prompt); clearing stays one click
    const handleToggleProblem = () => { if (project.problem) { openReasonModal({ kind: 'CLEAR_PROBLEM', title: 'CLEAR PROBLEM FLAG', confirmLabel: 'CLEAR FLAG', info: 'This removes the PROBLEM flag from this plot. Write why it is no longer a problem; your words go into the notes and the audit log.' }); } else { setProbErr(''); setProblemModal({ open: true, note: '' }); } };
    const closeProblemModal = () => { if (!probBusy) { setProbErr(''); setProblemModal({ open: false, note: '' }); } };
    const handleProblemConfirm = async () => { if (probBusy) return; setProbBusy(true); const ok = await runToggleProblem(problemModal.note); setProbBusy(false); if (ok) setProblemModal({ open: false, note: '' }); };
    const openReasonModal = (cfg) => { setReasonErr(''); setReasonModal({ open: true, kind: '', title: '', info: '', confirmLabel: 'CONFIRM', amountLabel: '', amount: '', reason: '', paymentId: null, ...cfg }); };
    const closeReasonModal = () => { if (!reasonBusy) { setReasonErr(''); setReasonModal(m => ({ ...m, open: false })); } };
    const submitReasonModal = async () => {
        if (reasonBusy) return;
        const m = reasonModal; const why = (m.reason || '').trim();
        if (why.length < 5) { const m = 'WRITE THE REASON (AT LEAST 5 CHARACTERS).'; setReasonErr(m); toast(m, 'error'); return; }
        if (m.kind === 'REDUCE' && (m.amount === '' || Number(m.amount) < 0 || Number(m.amount) >= storageFees)) { const m = 'ENTER A NEW TOTAL THAT IS LOWER THAN THE CURRENT FEES.'; setReasonErr(m); toast(m, 'error', 6000); return; }
        setReasonBusy(true); setReasonErr('');
        try {
            if (m.kind === 'REVERSE') { await landService.reversePayment(id, m.paymentId, why); toast('Payment reversed.', 'warn'); }
            else if (m.kind === 'REDUCE') { await folderPortalService.reduceFees(id, m.amount, why); toast('Storage fees reduced.', 'success'); }
            else if (m.kind === 'RATE') { await folderPortalService.settings(id, { rate: rateFee, reason: why }); toast('Monthly storage rate saved.', 'success'); }
            else if (m.kind === 'PAUSE') { await folderPortalService.settings(id, { deadline: rateDeadline, reason: why }); setFreezeOpen(false); toast('Storage fees paused.', 'info'); }
            else if (m.kind === 'WAIVE') { await folderPortalService.exit(id, 'WAIVE', why); toast('Storage fees waived.', 'success'); }
            else if (m.kind === 'UNDO_RELEASE') { await landService.undoRelease(id, why); toast('Hand-over undone.', 'warn'); }
            else if (m.kind === 'ENTER') { await folderPortalService.enter(id, why); toast('Moved to receivables.', 'success'); }
            else if (m.kind === 'SET_ASIDE') { await folderPortalService.exit(id, 'SET_ASIDE', why); toast('Receivable set aside - record retained.', 'success'); }
            else if (m.kind === 'CAPITALIZE') { await folderPortalService.exit(id, 'CAPITALIZE', why); toast('Storage fees added to the total cost.', 'success'); }
            else if (m.kind === 'CLEAR_PROBLEM') {
                await folderPortalService.toggleProblem(id, why);
                try { await landService.addStandaloneNote(id, '[PROBLEM CLEARED] ' + why); } catch { toast('Flag cleared, but the note did NOT save. Add it again from the NOTES tab.', 'warn', 12000); }
                toast('Problem flag removed.', 'info');
            }
            else if (m.kind === 'DELETE') {
                await landService.purgeAsset(id, why);
                touchedRef.current = false; setIsEditing(false);
                setReasonModal(x => ({ ...x, open: false }));
                toast('Project deleted. The root user can restore it from Settings > Archive.', 'warn', 6000);
                setTimeout(() => navigate('/land/projects'), 1500);
                return;
            }
            else if (m.kind === 'REVERT_TITLE') { await landService.revertTitle(id, why); setStageCount(0); toast('Title reverted. The project is back to stages.', 'warn'); }
            await loadFolderData();
            setReasonModal(x => ({ ...x, open: false }));
        } catch (err) { const m = errText(err); setReasonErr(m); toast('NOT DONE: ' + m, 'error', 12000); }
        finally { setReasonBusy(false); }
    };
    const handleUnlock = async () => { touchedRef.current = false; setIsEditing(true); try { await landService.logDossierUnlock(id); } catch {} };
    const handleAbort = async () => { const ok = await confirm('DISCARD CHANGES', 'Unsaved field changes will be lost. Stage ticks are saved the moment you click them, so they stay as they are.', 'warn'); if (ok) { if (buffer.convertToTitle && !project.landTitle) { try { await stageChecklistRef.current?.setLastStageCompletion(false); } catch {} } touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); } };
    // fix166: DELETE is a soft delete (the root user can restore it), so it no longer claims "permanent"; it needs a written reason.
    const handleNuclearPurge = () => openReasonModal({ kind: 'DELETE', title: 'DELETE THIS PROJECT', confirmLabel: 'DELETE PROJECT',
        info: 'This takes the whole project (payments, notes and documents included) out of every list. It is NOT erased: the root user can restore it from Settings > Archive. Write why it is being deleted.' });
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        try {
            const result = await clientService.lookupNin(val.trim());
            if (!result.exists) return;
            const existingName = (result.fullName || '').trim().toUpperCase();
            const enteredName = (buffer.owners[idx]?.fullName || '').trim().toUpperCase();
            if (existingName && enteredName && existingName !== enteredName) { setNinMismatch({ idx, existingName: result.fullName, enteredName: buffer.owners[idx]?.fullName || '' }); return; }
            const owners = buffer.owners.map((o, i) => i !== idx ? o : { ...o, phone: o.phone.trim() ? o.phone : (result.phoneNumber || o.phone), email: o.email.trim() ? o.email : (result.email || o.email), address: o.address.trim() ? o.address : (result.homeAddress || o.address) });
            touchedSetBuffer(p => ({ ...p, owners }));
            toast('NIN matched ' + result.fullName + '. Details auto-filled.', 'info', 4500);
        } catch { toast('NIN lookup failed', 'error'); }
    };
    const handleNinMismatchConfirm = () => setNinMismatch(null);
    const handleNinMismatchReject = () => { if (!ninMismatch) return; const idx = ninMismatch.idx; handleOwnerChange(idx, 'nationalId', ''); setNinMismatch(null); setTimeout(() => { const el = document.getElementById('owner_' + idx + '_nin'); if (el) el.focus(); }, 50); };
    const handleOwnerChange = (idx, field, val) => {
        const owners = buffer.owners.map((o, i) => { if (i !== idx) return o; let v = val; if (field === 'fullName') v = val.toUpperCase(); if (field === 'nationalId') v = val.toUpperCase().replace(/\s/g, ''); if (field === 'email') v = val.toLowerCase().replace(/\s/g, ''); return { ...o, [field]: v }; });
        touchedRef.current = true; setBuffer(p => ({ ...p, owners }));
    };
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
        if (bad.length) toast('NOT ADDED: ' + bad.join('; '), 'error', 12000);
        if (!ok.length) return;
        setUploadDraft({ batch: '', error: '', files: ok.map(file => ({ file, category: '' })) });
    };
    const closeUploadDraft = () => { if (committing) return; setUploadDraft(null); setNewCatOpen(false); setNewCatName(''); };
    const setBatchCategory = (code) => setUploadDraft(d => d && ({ batch: code, files: d.files.map(f => ({ ...f, category: code })) }));
    const setFileCategory = (i, code) => setUploadDraft(d => d && ({ ...d, files: d.files.map((f, j) => (j === i ? { ...f, category: code } : f)) }));
    const handleAddCategory = async () => {
        const name = newCatName.trim();
        if (name.length < 2 || catBusy) return;
        setCatBusy(true);
        try {
            const cat = await landService.addDocumentCategory(name);
            await loadDocCats();
            setNewCatName(''); setNewCatOpen(false);
            setUploadDraft(d => d && ({ ...d, batch: d.batch || cat.code, files: d.files.map(f => (f.category ? f : { ...f, category: cat.code })) }));
            toast('Category "' + cat.label + '" ready', 'success', 3000);
        } catch (err) { const m = errText(err); setUploadDraft(d => d && ({ ...d, error: 'COULD NOT ADD CATEGORY: ' + m })); toast('COULD NOT ADD CATEGORY: ' + m, 'error', 12000); } finally { setCatBusy(false); }
    };
    const handleUploadConfirm = async () => {
        if (!uploadDraft || committing) return;
        if (uploadDraft.files.some(f => !f.category)) { const m = 'PICK A CATEGORY FOR EVERY FILE.'; setUploadDraft(d => d && ({ ...d, error: m })); toast(m, 'warn', 6000); return; }
        const count = uploadDraft.files.length;
        setCommitting(true);
        try {
            await landService.addExtraDocuments(id, uploadDraft.files.map(f => f.file), uploadDraft.files.map(f => f.category));
            setUploadDraft(null); setNewCatOpen(false); setNewCatName('');
            await loadFolderData();
            toast(count + ' document(s) uploaded', 'success', 3000);
        } catch (err) { const m = errText(err); setUploadDraft(d => d && ({ ...d, error: m })); toast('UPLOAD FAILED: ' + m, 'error', 12000); } finally { setCommitting(false); }
    };
    const handleDeleteDoc = async (docId, fileName) => { const ok = await confirm('DELETE DOCUMENT', 'Delete "' + fileName + '"?', 'danger'); if (!ok) return; try { await landService.deleteDocument(docId); await loadFolderData(); toast('Document removed', 'warn', 3000); } catch (err) { toast('DOCUMENT NOT DELETED: ' + errText(err), 'error', 12000); } };
    // fix165: the note popup shows its own errors (the server's words), cannot be thrown away by a stray click
    // outside it, asks before discarding typed text, and a note over 2000 characters is refused before sending.
    const noteOriginal = () => (noteModal.id ? ((binder?.notes || []).find(n => n.id === noteModal.id) || {}).notes || '' : '');
    const closeNoteModal = async () => {
        if (noteBusy) return;
        const dirty = noteModal.content.trim() !== '' && noteModal.content !== noteOriginal();
        if (dirty) { const ok = await confirm('DISCARD NOTE', 'This note is not saved. Close it and lose what you typed?', 'warn'); if (!ok) return; }
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
        } catch (err) { const m = errText(err); setNoteErr(m); toast('NOTE NOT SAVED: ' + m, 'error', 12000); }
        finally { setNoteBusy(false); }
    };
    const handleDeleteNote = async (noteId) => { const ok = await confirm('DELETE NOTE', 'Delete this entry?', 'danger'); if (!ok) return; try { await landService.deleteStandaloneNote(noteId); await loadFolderData(); toast('Note deleted', 'warn', 3000); } catch (err) { toast('NOTE NOT DELETED: ' + errText(err), 'error', 12000); } };
    // fix166: runReceivableAction / askReceivable are gone. Every receivable move (enter, set aside, add fees to cost,
    // waive, reduce, rate, pause) now goes through the ONE reason window and the server refuses it without a reason.
    // fix165: the payment and its receipt travel to the server TOGETHER and are saved in ONE step. The server refuses a
    // payment with no receipt (wrong type, empty, over 10 MB) and rolls the payment back if the receipt cannot be filed.
    const handleRecordPayment = async () => {
        if (paying) return;
        const amt = Number(payAmount);
        const fail = (m) => { setPayErr(m); toast(m, 'error', 8000); };
        if (!payAmount || !Number.isFinite(amt) || amt <= 0) { fail('ENTER A VALID AMOUNT.'); return; }
        if (!Number.isInteger(amt)) { fail('ENTER WHOLE SHILLINGS ONLY (NO DECIMALS).'); return; }
        if (amt > Math.max(0, amountOwed)) { fail('OVERPAYMENT: THIS PROJECT ONLY OWES UGX ' + fmt(amountOwed) + '. YOU TYPED UGX ' + fmt(amt) + '.'); return; }
        if (RECEIPT_REQUIRED && !payReceipt) { fail('ATTACH THE PAYMENT RECEIPT. A PAYMENT CANNOT BE SAVED WITHOUT IT.'); return; }
        if (!SCAN_EXT.includes(fileExt(payReceipt.name))) { fail('THE RECEIPT MUST BE A PDF, JPG, PNG OR WEBP FILE.'); return; }
        if (!payReceipt.size) { fail('THE RECEIPT FILE IS EMPTY. SCAN OR PHOTOGRAPH IT AGAIN.'); return; }
        if (payReceipt.size > 10 * 1024 * 1024) { fail('THE RECEIPT IS OVER 10 MB. USE A SMALLER SCAN.'); return; }
        setPaying(true); setPayErr('');
        try {
            const fullNotes = payType === 'STORAGE' ? ('[STORAGE FEE PAYMENT] ' + payNotes).trim() : payNotes;
            const stamp = new Date().toISOString().slice(0, 10);
            const receiptName = 'Receipt - ' + (payType === 'STORAGE' ? 'Storage Fee' : 'Title Payment') + ' - UGX ' + amt + ' - ' + stamp + '.' + fileExt(payReceipt.name);
            await recoveryService.recordPayment(id, amt, fullNotes, new File([payReceipt], receiptName, { type: payReceipt.type }));
            await loadFolderData(); setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            toast('Payment recorded. Receipt filed under Payment Receipts.', 'success', 4500);
        } catch (err) { const m = errText(err); setPayErr(m); toast('PAYMENT NOT SAVED: ' + m, 'error', 12000); }
        finally { setPaying(false); }
    };
    const getDocUrl = (filePath) => { if (!filePath) return '#'; if (filePath.startsWith('http')) return filePath; const parts = filePath.split(/ge_uploads[/]/); const rel = parts.length > 1 ? parts[1] : filePath; const base = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1'; return base + '/vault/' + rel.replace(/\\/g, '/'); };
    const handleOpenDoc = (filePath) => { if (!filePath) return; const url = getDocUrl(filePath); if (filePath.startsWith('http')) window.open(url, '_blank', 'noopener,noreferrer'); else fetch(url, { headers: { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } }).then(r => r.blob()).then(blob => { const b = URL.createObjectURL(blob); window.open(b, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(b), 30000); }).catch(() => window.open(url, '_blank', 'noopener,noreferrer')); };
    const sg = useMemo(() => (key) => predictionService.getSuggestions(key) || [], []);

    if (loading) return (<div className={styles.container}><div className={styles.skeletonPage}><div className={styles.skeletonTermHeader} /><div className={styles.skeletonHUD} /><div className={styles.skeletonPanel}><div className={styles.skeletonHeader} /><div className={styles.skeletonBody}><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /></div></div><div className={styles.skeletonPanel}><div className={styles.skeletonHeader} /><div className={styles.skeletonBody}><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /></div></div></div></div>);
    if (loadError || !binder || !buffer) return (<div style={{ padding: 'clamp(40px,8vw,80px) clamp(20px,4vw,40px)' }}><ErrorMessage type="error" title="Record not found" message="This archive entry could not be loaded." onRetry={loadFolderData} retryLabel="Try Again" /></div>);

    const project = binder.project;
    const isReceivable = project?.isReceivable || false;
    const isBacklog = !project?.landTitle;
    const showTitleFields = !!project.landTitle || !!buffer.convertToTitle;
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
    const noteCount = (binder.notes || []).length;
    const paymentCount = payments.length;
    // fix162: which payments have been reversed (a REVERSAL line points at its original by id)
    const reversedIds = new Set(payments.filter(p => p.paymentType === 'REVERSAL' && p.notes)
        .map(p => { const m = String(p.notes).match(/^\[REVERSAL OF ([0-9a-fA-F-]{36})\]/); return m ? m[1] : null; }).filter(Boolean));
    const totalValue = Number(project?.totalCost || 0);
    const amountPaid = Number(project?.amountPaid || 0);
    const storageFees = Number(project?.storageFeesAccumulated || 0);
    const receivableAmountOwed = Math.max(0, totalValue + storageFees - amountPaid);
    const activeAmountOwed = Math.max(0, totalValue - amountPaid);
    const amountOwed = isReceivable ? receivableAmountOwed : activeAmountOwed;
    const arrearsEdit = (Number(buffer?.totalCost) || 0) - (Number(buffer?.initialPayment) || 0);
    const costChanged = isEditing && (Number(buffer?.totalCost) || 0) !== (Number(project?.totalCost) || 0);
    const lastPay = project?.lastPaymentDate ? new Date(project.lastPaymentDate) : null;
    const daysSincePay = lastPay ? Math.floor((Date.now() - lastPay.getTime()) / 86400000) : null;
    const statusBadge = isReceivable ? ['RECEIVABLE', 'badgeRecv']
        : project.landTitle?.isReleased ? ['RELEASED', 'badgeReleased']
        : (totalValue > 0 && amountPaid >= totalValue) ? ['PAID', 'badgePaid']
        : !project.landTitle ? ['PROCESSING', 'badgeProcessing']
        : (daysSincePay === null || daysSincePay > 30) ? ['CRITICAL', 'badgeCritical']
        : ['ACTIVE', 'badgeActive'];

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing || paying} />
            <div className={styles.printDossierHeader} aria-hidden="true">
                <div className={styles.printDossierMeta}>
                    <span><strong>PLOT ID:</strong> {project.landTitle?.plotNumber || project.projectIndex || 'UNTITLED'}</span>
                    <span><strong>TENURE:</strong> {project.landTitle?.tenure || '---'}</span>
                    {project.district && <span><strong>DISTRICT:</strong> {project.district}</span>}
                    <span><strong>STATUS:</strong> {project.status}</span>
                </div>
            </div>
            <div className={styles.printStatement} aria-hidden="true">
                <h3>PAYMENT STATEMENT — PROJECT #{project.projectIndex}</h3>
                <table><thead><tr><th>DATE</th><th>TYPE</th><th>AMOUNT (UGX)</th><th>RECORDED BY</th></tr></thead>
                    <tbody>{payments.map((p, i) => (<tr key={i}><td>{new Date(p.timestamp).toLocaleDateString()}</td><td>{p.paymentType}</td><td>{fmt(p.amountPaid)}</td><td>{p.recordedBy}</td></tr>))}</tbody></table>
                <p>TOTAL PAID: UGX {fmt(amountPaid)} | STORAGE FEES: UGX {fmt(storageFees)} | BALANCE OWED: UGX {fmt(amountOwed)}</p>
            </div>
            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle?.plotNumber || '#' + project.projectIndex || 'UNTITLED'}</h1>
                    <div className={styles.metaLine}>
                        
                        {isBacklog ? <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>PROCESSING</span>
                            : <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span>}
                        {isReceivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>IN RECEIVABLES</span>
                            : amountPaid >= totalValue ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>FULLY PAID</span>
                            : <span className={`${styles.textBadge} ${styles.badgeActive}`}>ACTIVE</span>}
                        {project.landTitle?.isReleased && <span className={`${styles.textBadge} ${styles.badgeReleased}`}>RELEASED</span>}
                        {project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}
                        {project.problem && <span className={`${styles.textBadge} ${styles.badgeProblem}`}>PROBLEM</span>}
                        {project.storagePaused && <span className={`${styles.textBadge} ${styles.badgePaused}`}>STORAGE PAUSED</span>}
                        {project.negotiationDeadline && <span className={`${styles.textBadge} ${styles.badgePaused}`}>FEES PAUSED</span>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {!isEditing && (<div className={styles.ctrlGroup}>
                        <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record"><FiPrinter aria-hidden="true" /></button>
                        {canEdit && <button className={styles.ctrlBtnPay} disabled={amountOwed <= 0} title={amountOwed <= 0 ? 'Nothing is owed on this project.' : 'Record a payment with its receipt.'} onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}><FiDollarSign aria-hidden="true" /> RECORD PAYMENT</button>}
                        {canMoney && project.landTitle && (project.landTitle.isReleased
                            ? (<>
                                <button className={`${styles.releaseBtn} ${styles.releaseBtnDone}`} disabled title="The client has received the title deed."><FiCheckCircle aria-hidden="true" /> HANDED OVER</button>
                                <button type="button" className={styles.ghostBtn} title="Mark the title as NOT handed over again (reason required)."
                                    onClick={() => openReasonModal({ kind: 'UNDO_RELEASE', title: 'UNDO HAND-OVER', confirmLabel: 'UNDO HAND-OVER',
                                        info: 'This marks the title as NOT handed over again and puts the plot back to ACTIVE. Use it only if the hand-over was recorded by mistake.' })}><FiUnlock aria-hidden="true" /> UNDO</button>
                              </>)
                            : <button className={styles.releaseBtn} onClick={handleRelease} disabled={amountOwed > 0 || !!project.problem}
                                title={amountOwed > 0 ? 'Cannot hand over yet: UGX ' + fmt(amountOwed) + ' is still owed.' : project.problem ? 'Cannot hand over while this plot is flagged as a PROBLEM. Clear the flag first.' : 'Record that the client has received the title deed.'}><FiCheckCircle aria-hidden="true" /> HAND OVER TITLE</button>)}
                        {canMoney && project.landTitle && !project.landTitle.isReleased && !project.isLegacy && !isReceivable && stageCount > 0 && (
                            <button type="button" className={styles.ghostBtn} title="Take the saved title off and go back to the stage checklist (reason required)."
                                onClick={() => openReasonModal({ kind: 'REVERT_TITLE', title: 'REVERT TO STAGES', confirmLabel: 'REVERT TO STAGES',
                                    info: 'This removes the saved title (plot ' + (project.landTitle.plotNumber || '---') + ') and un-ticks the final stage, so the project goes back to the stage checklist. The old title values stay in the audit log. Use it only if the title was entered by mistake. To fix a typo in the title, use EDIT instead.' })}><FiRefreshCw aria-hidden="true" /> REVERT TO STAGES</button>)}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem} title={project.problem ? 'Remove the problem flag from this plot.' : 'Flag this plot as having a problem and alert staff.'}><FiAlertTriangle aria-hidden="true" /> {project.problem ? 'CLEAR PROBLEM' : 'FLAG PROBLEM'}</button>}
                        {canEdit && <button className={styles.unlockMasterBtn} onClick={handleUnlock} disabled={!!project.landTitle?.isReleased} title={project.landTitle?.isReleased ? 'The title has been handed over, so this record is locked. A director can UNDO the hand-over first.' : 'Edit this record.'}><FiUnlock aria-hidden="true" /> EDIT</button>}
                    </div>)}
                    {isEditing && (<div className={styles.ctrlGroup}>
                        {isRoot && <button className={styles.purgeBtn} onClick={handleNuclearPurge}><FiTrash2 aria-hidden="true" /> DELETE</button>}
                        <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}><FiX aria-hidden="true" /> CANCEL</button>
                        <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}><FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}</button>
                    </div>)}
                </div>
            </header>
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                <div className={styles.tabDock}>
                    <div className={styles.tabRow}>
                        {TABS.map(tab => (<button key={tab} role="tab" aria-selected={activeTab === tab}
                            data-accent={TAB_ACCENTS[tab]}
                            className={activeTab === tab ? styles.tabOn : styles.tab} onClick={() => setActiveTab(tab)} title={tab}>
                            <span className={styles.tabFull}>{tab}</span><span className={styles.tabShort}>{tab.substring(0, 2)}</span>
                        </button>))}
                    </div>
                </div>
            </div>
            <main className={styles.workstationBody} role="tabpanel">
                <section className={styles.hwPanel} aria-label="Plot Details" style={activeTab !== 'OVERVIEW' ? { display: 'none' } : {}}>
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.overview} onClick={() => toggleDrawer('overview')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.overview ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        {isEditing ? (<>
                            {!project.landTitle && (<div className={styles.convertRow}>
                                <button type="button" className={`${styles.convertBtn} ${buffer.convertToTitle ? styles.convertBtnActive : ''}`}
                                    onClick={() => {
                                        const next = !buffer.convertToTitle;
                                        touchedSetBuffer(p => ({ ...p, convertToTitle: next }));
                                        stageChecklistRef.current?.setLastStageCompletion(next);
                                    }}><FiCheckCircle aria-hidden="true" /> {buffer.convertToTitle ? 'UNDO' : 'TITLE READY'}</button>
                                <span className={styles.inputHint}>Unlocks title fields and marks the final stage done</span>
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
                                <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({ ...buffer, plotNumber: e.target.value.toUpperCase() })} />
                                <SmartSelect label="TENURE" options={['MAILO', 'FREEHOLD', 'LEASEHOLD', 'CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({ ...buffer, tenure: v })} />
                                <SmartInput label="TITLE ID" value={buffer.titleId} showCaps onChange={e => touchedSetBuffer({ ...buffer, titleId: e.target.value.toUpperCase() })} />
                                <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({ ...buffer, blockRoad: e.target.value.toUpperCase() })} />
                            </div>)}
                        </>) : (<>
                            <div className={styles.specGroup}>
                                <div className={styles.sectionSubHeader}>LOCATION</div>
                                <div className={styles.readOnlyGrid}>
                                    {[['DISTRICT', project.district], ['COUNTY', project.county], ['SUB-COUNTY', project.subCounty], ['PARISH', project.parish], ['VILLAGE', project.village], ['AREA', project.area]].map(([l, v], i) => (
                                        <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                                </div>
                            </div>
                            {project.landTitle && (<div className={`${styles.specGroup} ${styles.specGroupDivided}`}>
                                <div className={styles.sectionSubHeader}>TITLE</div>
                                <div className={styles.readOnlyGrid}>
                                    {[['PLOT ID', project.landTitle.plotNumber], ['TENURE', project.landTitle.tenure], ['TITLE ID', project.landTitle.titleId], ['BLOCK / ROAD', project.landTitle.blockRoad]].map(([l, v], i) => (
                                        <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                                </div>
                            </div>)}
                        </>)}
                    </div></div>
                </section>
                {(
<section className={styles.hwPanel} aria-label="Stage Checklist" style={(activeTab !== 'OVERVIEW' || buffer.convertToTitle || (project.landTitle && stageCount < 1)) ? { display: 'none' } : {}}>
                    <DrawerHeader label="STAGE CHECKLIST" isOpen={drawers.stagesPanel} onClick={() => toggleDrawer('stagesPanel')} icon={FiCheckCircle} />
                    <div className={`${styles.panelBody} ${drawers.stagesPanel ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        <StageChecklistPanel key={project.landTitle ? 'titled' : 'folder'} ref={stageChecklistRef} projectId={id} canEdit={canEdit && isEditing && !project.landTitle} canRemove={isDirector && isEditing && !project.landTitle} toast={toast} confirm={confirm} onLoaded={setStageCount}
                            onLastStageToggle={(done) => touchedSetBuffer(p => ({ ...p, convertToTitle: done }))} />
                    </div></div>
                </section>
                )}
                <div className={styles.financialsStack} style={activeTab !== 'FINANCIALS' ? { display: 'none' } : {}}>
                    <section className={styles.hwPanel} aria-label="Balance Summary">
                        <DrawerHeader label="BALANCE SUMMARY" isOpen={drawers.balance} onClick={() => toggleDrawer('balance')} icon={FiCreditCard} />
                        <div className={`${styles.panelBody} ${drawers.balance ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                            {isEditing ? (<div className={styles.inputGrid3}>
                                <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({ ...buffer, totalCost: v })} />
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>AMOUNT PAID</label><span className={styles.autoCalcBadge}>LOCKED</span></div>
                                    <input className={`${styles.hwInput} ${styles.calcInput}`} value={(Number(buffer.initialPayment) || 0).toLocaleString()} disabled />
                                    <span className={styles.inputHint}>Changes only through RECORD PAYMENT, or REVERSE in Payment History.</span></div>
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>AMOUNT OWED</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                    <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled /></div>
                                {costChanged && (<SmartInput label="REASON FOR COST CHANGE" value={buffer.costChangeReason || ''} required error={fieldErrors.costChangeReason}
                                    onChange={e => touchedSetBuffer({ ...buffer, costChangeReason: e.target.value })} />)}
                            </div>) : isReceivable ? (<div className={styles.moneyStatsRow}>
                                <div className={styles.statBox}><label>TOTAL COST</label><strong>UGX {fmt(totalValue)}</strong></div>
                                <div className={styles.statBox}><label style={{ color: 'var(--fs-red)' }}>+ STORAGE FEES</label><strong style={{ color: 'var(--fs-red)' }}>UGX {fmt(storageFees)}</strong></div>
                                <div className={styles.statBox}><label style={{ color: 'var(--fs-green)' }}>PAID</label><strong style={{ color: 'var(--fs-green)' }}>UGX {fmt(amountPaid)}</strong></div>
                                <div className={`${styles.statBox} ${amountOwed > 0 ? styles.statRed : styles.statGreen}`}><label>AMOUNT OWED</label><strong>UGX {fmt(receivableAmountOwed)}</strong></div>
                            </div>) : (<div className={styles.moneyStatsRow}>
                                <div className={styles.statBox}><label>TOTAL COST</label><strong>UGX {fmt(totalValue)}</strong></div>
                                <div className={styles.statBox}><label style={{ color: 'var(--fs-green)' }}>PAID</label><strong style={{ color: 'var(--fs-green)' }}>UGX {fmt(amountPaid)}</strong></div>
                                <div className={`${styles.statBox} ${amountOwed > 0 ? styles.statRed : styles.statGreen}`}><label>AMOUNT OWED</label><strong>UGX {fmt(activeAmountOwed)}</strong></div>
                            </div>)}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Storage Fees" id="receivable-controls">
                    <DrawerHeader label="STORAGE FEES" isOpen={drawers.recv} onClick={() => toggleDrawer('recv')} icon={FiAlertOctagon} />
                    <div className={`${styles.panelBody} ${drawers.recv ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        {!isReceivable ? (
                            <div className={styles.recvActionRow}>
                                {canMoney && !project.landTitle?.isReleased && amountOwed > 0 && <HardwareButton type="button" icon={FiAlertOctagon} loading={recvBusy} onClick={() => openReasonModal({ kind: 'ENTER', title: 'MOVE TO RECEIVABLES', confirmLabel: 'MOVE TO RECEIVABLES',
                                    info: 'This freezes the balance (UGX ' + fmt(amountOwed) + ' owed) and starts a monthly storage fee of UGX 50,000 unless a different rate is set, added every 30 days. Write why this project is moving to receivables.' })}>MOVE TO RECEIVABLES</HardwareButton>}
                                <span className={styles.inputHint}>Receivables = clients who still owe after the work is done. Moving this project there freezes the balance and starts a monthly storage fee (UGX 50,000 unless you set another rate), added every 30 days.</span>
                            </div>
                        ) : (<>
                            <div className={styles.moneyStatsRow}>
                                <div className={`${styles.statBox} ${styles.statRed}`}><label>STORAGE FEES</label><strong>UGX {fmt(storageFees)}</strong></div>
                                <div className={styles.statBox}><label>COST + FEES</label><strong>UGX {fmt(totalValue + storageFees)}</strong></div>
                                <div className={`${styles.statBox} ${styles.statRed}`}><label>TOTAL OWED</label><strong>UGX {fmt(receivableAmountOwed)}</strong></div>
                            </div>
                            {canMoney && (<div className={styles.storageBlock}>
                                <div className={styles.inputGrid3}>
                                    <CurrencyInput label="MONTHLY STORAGE RATE" value={rateFee} onChange={v => setRateFee(v)} hint="Blank = default 50,000" />
                                    <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>&nbsp;</label></div>
                                        <HardwareButton type="button" icon={FiSave} loading={recvBusy} onClick={() => openReasonModal({ kind: 'RATE', title: 'CHANGE MONTHLY STORAGE RATE', confirmLabel: 'SAVE RATE',
                                            info: 'New monthly rate: ' + (rateFee ? 'UGX ' + fmt(Number(rateFee)) : 'the default (UGX 50,000)') + '. It applies to future months only; fees already added stay as they are. Write why it is changing (for example the agreed figure after negotiation).' })}>SAVE RATE</HardwareButton></div>
                                </div>
                                <div className={styles.recvActionRow}>
                                    {project.negotiationDeadline ? (<>
                                        <span className={styles.frozenChip}>FEES PAUSED UNTIL {String(project.negotiationDeadline).slice(0, 10)}</span>
                                        <button type="button" className={styles.ghostBtn} onClick={handleUnfreeze}><FiUnlock aria-hidden="true" /> RESUME FEES</button>
                                    </>) : freezeOpen ? (<>
                                        <input type="datetime-local" className={styles.dtInput} value={rateDeadline} onChange={e => setRateDeadline(e.target.value)} />
                                        <HardwareButton type="button" icon={FiCheckCircle} loading={recvBusy} onClick={() => { if (!rateDeadline) { toast('PICK THE DATE THE PAUSE ENDS FIRST', 'error'); return; } openReasonModal({ kind: 'PAUSE', title: 'PAUSE STORAGE FEES', confirmLabel: 'PAUSE FEES',
                                            info: 'No new storage fees will be added until ' + String(rateDeadline).slice(0, 10) + '. Write why (for example the client is negotiating).' }); }}>PAUSE FEES</HardwareButton>
                                        <button type="button" className={styles.ghostBtn} onClick={() => setFreezeOpen(false)}><FiX aria-hidden="true" /> CANCEL</button>
                                    </>) : (
                                        <button type="button" className={styles.ghostBtn} onClick={() => setFreezeOpen(true)}><FiClock aria-hidden="true" /> PAUSE FEES UNTIL A DATE</button>
                                    )}
                                </div>
                            </div>)}
                            <div className={styles.recvActionRow}>
                                {canMoney && (<>
                                    <HardwareButton type="button" icon={FiArchive} loading={recvBusy} onClick={() => openReasonModal({ kind: 'SET_ASIDE', title: 'SET ASIDE', confirmLabel: 'SET ASIDE',
                                        info: 'This takes the project out of receivables and stops new fees. The UGX ' + fmt(storageFees) + ' of fees is KEPT (hidden) so the project can be moved back later. Write why.' })}>SET ASIDE (KEEP FEES)</HardwareButton>
                                    <button type="button" className={styles.ghostBtn} onClick={() => openReasonModal({ kind: 'CAPITALIZE', title: 'ADD FEES TO COST', confirmLabel: 'ADD FEES TO COST',
                                        info: 'This adds the UGX ' + fmt(storageFees) + ' of storage fees to the total cost (UGX ' + fmt(totalValue) + ' becomes UGX ' + fmt(totalValue + storageFees) + ') and takes the project out of receivables. Write why.' })} disabled={recvBusy}><FiCreditCard aria-hidden="true" /> ADD FEES TO COST</button>
                                    <button type="button" className={styles.dangerBtn} onClick={() => openReasonModal({ kind: 'WAIVE', title: 'WAIVE STORAGE FEES', confirmLabel: 'WAIVE FEES',
                                        info: 'This forgives ALL UGX ' + fmt(storageFees) + ' of storage fees and takes this project out of receivables. It cannot be undone.' })} disabled={recvBusy}><FiTrash2 aria-hidden="true" /> WAIVE FEES</button>
                                    {storageFees > 0 && <button type="button" className={styles.ghostBtn} onClick={() => openReasonModal({ kind: 'REDUCE', title: 'REDUCE STORAGE FEES', confirmLabel: 'REDUCE FEES', amountLabel: 'NEW TOTAL STORAGE FEES (UGX)',
                                        info: 'The client negotiated a lower fee. Current fees are UGX ' + fmt(storageFees) + '. Type the agreed lower total; the project stays in receivables.' })} disabled={recvBusy}><FiDollarSign aria-hidden="true" /> REDUCE FEES</button>}
                                </>)}
                            </div>
                            {canMoney && <div className={styles.inputHint}>SET ASIDE, ADD FEES TO COST and WAIVE FEES each take this project OUT of receivables. REDUCE FEES keeps it in.</div>}
                        </>)}
                    </div></div>
                </section>
                    <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                        <DrawerHeader label="PAYMENT HISTORY" isOpen={drawers.history} onClick={() => toggleDrawer('history')} icon={FiActivity} count={paymentCount} />
                        <div className={`${styles.panelBody} ${drawers.history ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                            {paymentCount === 0 ? (<div className={styles.emptyState}><FiDollarSign className={styles.emptyIcon} aria-hidden="true" /><span>NO PAYMENTS RECORDED YET</span></div>) : (
                                <div className={styles.paymentList}>{payments.map((pay, i) => (<div key={pay.id || i} id={'payment-' + pay.id} className={styles.paymentRow}>
                                    <div className={styles.payRowLeft}><div className={styles.payAmount}>UGX {fmt(pay.amountPaid)}</div>
                                        <div className={styles.payMeta}><span className={styles.payType}>{pay.paymentType}</span><span className={styles.payBy}>by {pay.recordedBy}</span>
                                        {reversedIds.has(pay.id) && <span className={styles.payReversed}>REVERSED</span>}
                                        {pay.paymentType === 'REVERSAL' && pay.notes && <span className={styles.payBy}>{String(pay.notes).replace(/^\[REVERSAL OF [^\]]*\]\s*/, '')}</span>}</div></div>
                                    <div className={styles.payRowRight}><div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div>
                                        {canMoney && pay.paymentType !== 'REVERSAL' && Number(pay.amountPaid) > 0 && !reversedIds.has(pay.id) && !project.landTitle?.isReleased && (
                                            <button type="button" className={styles.reverseBtn} title="Cancel this payment. The original line stays; a negative REVERSAL line is added."
                                                onClick={() => openReasonModal({ kind: 'REVERSE', paymentId: pay.id, title: 'REVERSE PAYMENT', confirmLabel: 'REVERSE PAYMENT',
                                                    info: 'This cancels UGX ' + fmt(pay.amountPaid) + ' paid on ' + new Date(pay.timestamp).toLocaleDateString() + '. The original line stays in the history, a negative REVERSAL line is added, and the amount paid goes down by the same amount.' })}>REVERSE</button>)}
                                    </div>
                                </div>))}</div>)}
                        </div></div>
                    </section>
                </div>
<section className={styles.hwPanel} aria-label="Owners" style={activeTab !== 'OWNERS' ? { display: 'none' } : {}}>
                    <DrawerHeader label="OWNERS" isOpen={drawers.owners} onClick={() => toggleDrawer('owners')} icon={FiUsers} count={project.proprietors.length} />
                    <div className={`${styles.panelBody} ${drawers.owners ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <div className={styles.ownersGrid2}>
                            {isEditing ? buffer.owners.map((o, idx) => (<div key={idx} className={styles.ownerEditCard}>
                                <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                <SmartInput label="NIN" value={o.nationalId} required onChange={e => handleOwnerChange(idx,'nationalId',e.target.value)} onBlur={e => handleNinBlurCheck(idx, e.target.value)} id={`owner_${idx}_nin`} />
                                <SmartInput label="PHONE" value={o.phone} error={fieldErrors['owner_'+idx+'_phone']} onChange={e => handleOwnerChange(idx,'phone',e.target.value)} onBlur={e => { const r = normalizePhones(e.target.value); if (r.ok && r.value !== e.target.value) handleOwnerChange(idx,'phone',r.value); }} id={`owner_${idx}_phone`} />
                                <SmartInput label="EMAIL" value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} id={`owner_${idx}_email`} />
                                <SmartInput label="ADDRESS" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />
                            </div>)) : project.proprietors.map((p, i) => (<div key={i} className={styles.ownerStaticCard}>
                                {/* Every other client name in the app opens the
                                    dossier. This one used to be dead text. */}
                                {p.id ? (
                                    <button type="button" className={styles.ownerNameLink}
                                        onClick={() => navigate('/client/' + p.id)}
                                        title={`Open ${p.fullName}'s full portfolio`}>
                                        {p.fullName}
                                    </button>
                                ) : <h2 className={styles.ownerName}>{p.fullName}</h2>}
                                <div className={styles.infoColumns}>
                                    <div className={styles.infoRow}><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber||'---'}</span></div>
                                    <div className={styles.infoRow}><FiMail aria-hidden="true" /><span>{p.email||'---'}</span></div>
                                    <div className={styles.infoRow}><FiShield aria-hidden="true" /><span>{p.nationalId||'---'}</span></div>
                                    <div className={styles.infoRow}><FiMapPin aria-hidden="true" /><span>{p.homeAddress||'---'}</span></div>
                                </div>
                            </div>))}
                        </div>
</div></div>
</section>
<section className={styles.hwPanel} aria-label="Related Projects" style={activeTab !== 'OWNERS' ? { display: 'none' } : {}}>
<DrawerHeader label="RELATED PROJECTS" isOpen={drawers.related} onClick={() => toggleDrawer('related')} icon={FiFolderPlus} count={portfolio.length || undefined} />
<div className={`${styles.panelBody} ${drawers.related ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
{portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
[...new Set(portfolio.map(r => r.sharedOwner))].map(owner => (
<div key={owner} className={styles.ownerRelGroup}>
<h4 className={styles.ownerRelName}>{owner}</h4>
<table className={styles.portfolioTable}>
<thead><tr><th>#</th><th>PLOT</th><th>STATUS</th></tr></thead>
<tbody>{portfolio.filter(r => r.sharedOwner === owner).map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
<td>#{r.index}</td><td>{r.plot || '—'}</td>
<td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
</tr>))}</tbody>
</table>
</div>)))}
</div></div>
</section>
                <section className={styles.hwPanel} aria-label="Documents" style={activeTab !== 'DOCUMENTS' ? { display: 'none' } : {}}>
                    <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')} icon={FiUploadCloud} count={docCount} />
                    <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        {docCount === 0 ? (<div className={styles.emptyState}><FiUploadCloud className={styles.emptyIcon} aria-hidden="true" /><span>NO DOCUMENTS ATTACHED</span>
                            {canUploadDocs && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}</div>) : (<>
                            <div className={styles.compactVault}>{docGroups.map(([cat, docs]) => (<React.Fragment key={cat}><div className={styles.docGroupLabel}>{cat === UNCATEGORISED ? 'UNCATEGORISED' : catLabel(cat)}<span className={styles.docGroupCount}>{docs.length}</span></div>{docs.map((doc) => (<div key={doc.id} className={styles.docTag}>
                                <FiFileText className={styles.docIcon} aria-hidden="true" />
                                <button type="button" className={styles.docName} onClick={() => handleOpenDoc(doc.filePath)}>{doc.fileName}</button>
                                {isEditing && canEdit && doc.category !== 'PAYMENT_RECEIPT' && <button type="button" className={styles.iconBtn} onClick={() => handleDeleteDoc(doc.id, doc.fileName)}><FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>}
                            </div>))}</React.Fragment>))}</div>
                            {canUploadDocs && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}
                        </>)}
                    </div></div>
                
                </section>


            <div className={styles.tabWrap} style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>
<section className={styles.hwPanel} aria-label="Notes and Call Log">
                        <DrawerHeader label="NOTES & CALL LOG" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} count={noteCount} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                            {canLog && <button type="button" className={styles.addNoteBtn} onClick={() => setNoteModal({ open: true, id: null, content: '' })}>+ ADD NOTE</button>}
                            {noteCount === 0 ? (<div className={styles.emptyState}><FiInfo className={styles.emptyIcon} aria-hidden="true" /><span>NO NOTES LOGGED YET</span></div>) : (
                                <div className={styles.notebookTimeline}>{binder.notes.map((log, i) => (<article key={i} className={styles.ruledNote}>
                                    <div className={styles.noteMeta}><time className={styles.noteTime}>{new Date(log.timestamp).toLocaleDateString()}</time><span className={styles.noteAuthor}>by {log.recordedBy}</span>
                                        {isEditing && canEdit && (<div className={styles.actionBlock}>
                                            <button type="button" className={styles.iconBtn} onClick={() => setNoteModal({ open: true, id: log.id, content: log.notes })}><FiEdit3 className={styles.editIcon} aria-hidden="true" /></button>
                                            <button type="button" className={styles.iconBtn} onClick={() => handleDeleteNote(log.id)}><FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>
                                        </div>)}</div>
                                    <p className={styles.noteContent}>{log.notes}</p>
                                </article>))}</div>)}
                        </div></div>
                    </section>
</div>
            </main>
            <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp" style={{ display: 'none' }} aria-hidden="true" tabIndex={-1}
                onChange={e => { if (!e.target.files?.length) return; handleVaultAction(Array.from(e.target.files)); e.target.value = ''; }} />
            <UnsavedChangesModal isOpen={guardModalOpen} onStay={handleStay} onLeave={handleLeave} context="Plot Record Edit" />
            <NinMismatchModal isOpen={!!ninMismatch} existingName={ninMismatch?.existingName} enteredName={ninMismatch?.enteredName} onConfirm={handleNinMismatchConfirm} onReject={handleNinMismatchReject} />
            <HardwareModal isOpen={!!uploadDraft} lockBackdrop onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">
                {uploadDraft && (<>
                    <ModalError text={uploadDraft.error} />
                    <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>CATEGORY FOR ALL {uploadDraft.files.length} FILE(S)</label>
                        <HardwareModalSelect value={uploadDraft.batch} options={catOptions} onChange={setBatchCategory} placeholder="Choose category" emptyText="No categories available" ariaLabel="Category for all files" /></div>
                    <div className={styles.upFileList}>{uploadDraft.files.map((f, i) => (<div key={i} className={styles.upFileRow}>
                        <span className={styles.upFileName} title={f.file.name}>{f.file.name}</span>
                        <HardwareModalSelect compact className={styles.upFileSelect} value={f.category} options={catOptions} onChange={code => setFileCategory(i, code)} placeholder="Category" emptyText="No categories available" ariaLabel={'Category for ' + f.file.name} /></div>))}</div>
                    {newCatOpen ? (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NEW CATEGORY NAME</label>
                        <input type="text" className={modalStyles.modalInput} value={newCatName} maxLength={120} placeholder="e.g. Survey Report" onChange={e => setNewCatName(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleAddCategory(); }} />
                        <div className={styles.upCatActions}>
                            <button type="button" className={styles.addDocBtn} onClick={handleAddCategory} disabled={catBusy || newCatName.trim().length < 2}>SAVE CATEGORY</button>
                            <button type="button" className={styles.addDocBtn} onClick={() => { setNewCatOpen(false); setNewCatName(''); }}>CANCEL</button>
                        </div></div>)
                        : (<button type="button" className={styles.addDocBtn} onClick={() => setNewCatOpen(true)}>+ NEW CATEGORY</button>)}
                    <div className={modalStyles.modalFooter}>
                        <HardwareButton type="button" onClick={handleUploadConfirm} loading={committing} icon={FiUploadCloud}>UPLOAD</HardwareButton>
                    </div>
                </>)}
            </HardwareModal>
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />
            <HardwareModal isOpen={noteModal.open} lockBackdrop onClose={closeNoteModal} title={noteModal.id ? 'EDIT NOTE' : 'ADD NOTE'}>
                <ModalError text={noteErr} />
                <div className={modalStyles.modalField}><textarea className={modalStyles.modalTextarea} value={noteModal.content} onChange={e => { setNoteModal({ ...noteModal, content: e.target.value }); if (noteErr) setNoteErr(''); }} placeholder="Enter interaction note..." aria-label="Note content" />
                    <span className={styles.probCount}>{noteModal.content.trim().length}/{NOTE_MAX}</span></div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave} disabled={noteBusy}><FiSave aria-hidden="true" /> {noteBusy ? 'SAVING...' : 'SAVE ENTRY'}</button>
                </div>
            </HardwareModal>
            <HardwareModal isOpen={payModal.open} lockBackdrop onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={'RECORD PAYMENT - ' + (project.landTitle?.plotNumber || project.projectIndex || 'FOLDER')}>
                {isReceivable && (<div className={styles.payTypeRow}><div className={styles.payTypeButtons}>
                    <button type="button" className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`} onClick={() => setPayType('TITLE')}><FiHome size={12} /> TITLE PAYMENT</button>
                    <button type="button" className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`} onClick={() => setPayType('STORAGE')}><FiArchive size={12} /> STORAGE FEE</button>
                </div></div>)}
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="text" inputMode="numeric" className={modalStyles.modalInput} placeholder={'e.g. ' + fmt(Math.max(0, amountOwed))} value={payAmount} onChange={e => { setPayAmount(e.target.value.replace(/[^0-9]/g, '')); if (payErr) setPayErr(''); }} /></div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea} value={payNotes} onChange={e => setPayNotes(e.target.value)} /></div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>PAYMENT RECEIPT{RECEIPT_REQUIRED ? ' (REQUIRED)' : ' (OPTIONAL)'}</label>
                    <input ref={payReceiptRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" style={{ display: 'none' }} aria-hidden="true" tabIndex={-1} onChange={e => { const f = e.target.files && e.target.files[0]; if (f) setPayReceipt(f); e.target.value = ''; }} />
                    {payReceipt ? (<div className={styles.recFile}><FiFileText aria-hidden="true" /><span className={styles.recName} title={payReceipt.name}>{payReceipt.name}</span><button type="button" className={styles.recRemove} onClick={() => setPayReceipt(null)} aria-label="Remove receipt"><FiX aria-hidden="true" /></button></div>)
                        : (<button type="button" className={styles.addDocBtn} onClick={() => payReceiptRef.current && payReceiptRef.current.click()}><FiPaperclip aria-hidden="true" />&nbsp;ATTACH RECEIPT SCAN</button>)}
                    <span className={styles.recHint}>Saved in this folder's Documents under Payment Receipts. PDF, JPG, PNG or WEBP, up to 10 MB. The payment is NOT saved without it.</span></div>
                <ModalError text={payErr} />
                <div className={modalStyles.modalFooter}>
                    <HardwareButton type="button" onClick={handleRecordPayment} loading={paying} icon={FiDollarSign}>CONFIRM</HardwareButton>
                </div>
            </HardwareModal>
<HardwareModal isOpen={reasonModal.open} lockBackdrop onClose={closeReasonModal} title={reasonModal.title}>
                <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>{reasonModal.info}</div>
                {reasonModal.kind === 'REDUCE' && (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>{reasonModal.amountLabel}</label>
                    <input type="number" min="0" className={modalStyles.modalInput} value={reasonModal.amount} autoFocus aria-label="New total storage fees"
                        onChange={e => setReasonModal(m => ({ ...m, amount: e.target.value }))} /></div>)}
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>REASON (REQUIRED - SAVED IN THE AUDIT LOG)</label>
                    <textarea className={`${modalStyles.modalTextarea} ${styles.probBox}`} value={reasonModal.reason} maxLength={300} autoFocus={reasonModal.kind !== 'REDUCE'} placeholder="e.g. Client paid in the wrong account..." aria-label="Reason"
                        onChange={e => setReasonModal(m => ({ ...m, reason: e.target.value }))} />
                    <span className={styles.probCount}>{reasonModal.reason.length}/300</span></div>
                <ModalError text={reasonErr} />
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={closeReasonModal} disabled={reasonBusy}>CANCEL</button>
                    <HardwareButton type="button" variant="danger" onClick={submitReasonModal} loading={reasonBusy} icon={FiAlertTriangle}>{reasonModal.confirmLabel}</HardwareButton>
                </div>
            </HardwareModal>
<HardwareModal isOpen={problemModal.open} lockBackdrop onClose={closeProblemModal} title={'FLAG PROBLEM - ' + (project.landTitle?.plotNumber || project.projectIndex || 'FOLDER')}>
                <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>This flags the plot as a <strong>PROBLEM</strong> and notifies staff. What you write below goes into the notes and the audit trail.</div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>WHAT IS THE PROBLEM? (REQUIRED)</label>
                    <textarea className={`${modalStyles.modalTextarea} ${styles.probBox}`} value={problemModal.note} maxLength={500} autoFocus placeholder="e.g. Owner name on the deed plan does not match the ID..." aria-label="Problem description" onChange={e => setProblemModal(m => ({ ...m, note: e.target.value }))} />
                    <span className={styles.probCount}>{problemModal.note.length}/500</span></div>
                <ModalError text={probErr} />
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={closeProblemModal} disabled={probBusy}>CANCEL</button>
                    <HardwareButton type="button" variant="danger" onClick={handleProblemConfirm} loading={probBusy} icon={FiAlertTriangle}>FLAG PROBLEM</HardwareButton>
                </div>
            </HardwareModal>
            {showTopBtn && (<button type="button" className={styles.scrollTopBtn} onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Back to top to edit or save"><FiArrowUp aria-hidden="true" /></button>)}
        </div>
    );
};
export default FolderPage;
