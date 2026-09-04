// PATH: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
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
    FiDollarSign, FiActivity, FiHome, FiArchive
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
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import ErrorMessage from '../../components/common/ErrorMessage';
import BackToTopButton from '../../components/common/BackToTopButton';
import CornerDecor from '../../components/ui/CornerDecor';
import styles from './FolderPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const TOAST_ICONS = { success: <FiCheckSquare aria-hidden="true" />, error: <FiAlertCircle aria-hidden="true" />, warn: <FiAlertTriangle aria-hidden="true" />, info: <FiInfo aria-hidden="true" /> };
const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
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
const StageChecklistPanel = ({ projectId, canEdit, canRemove, toast }) => {
    const [stages, setStages] = useState([]); const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true); const [addModalOpen, setAddModalOpen] = useState(false);
    const [checkedTemplates, setCheckedTemplates] = useState({}); const [customName, setCustomName] = useState('');
    const [customCost, setCustomCost] = useState(''); const [editingId, setEditingId] = useState(null);
    const [editCost, setEditCost] = useState(''); const [editNotes, setEditNotes] = useState(''); const [saving, setSaving] = useState(false);
    const loadStages = useCallback(async () => { try { setStages(await stageTemplateService.getProjectStages(projectId) || []); } catch {} finally { setLoading(false); } }, [projectId]);
    useEffect(() => { loadStages(); }, [loadStages]);
    const openAddModal = async () => { try { setTemplates(await stageTemplateService.getTemplate() || []); } catch { setTemplates([]); } setCheckedTemplates({}); setCustomName(''); setCustomCost(''); setAddModalOpen(true); };
    const handleAttach = async () => {
        const requests = [];
        templates.forEach(t => { if (checkedTemplates[t.id]) requests.push({ stageTemplateId: t.id, cost: t.defaultCost, isCustom: false }); });
        if (customName.trim()) requests.push({ stageName: customName.trim(), cost: Number(customCost) || 0, isCustom: true });
        if (!requests.length) { toast && toast('Select at least one stage', 'error'); return; }
        setSaving(true);
        try { await stageTemplateService.attachStages(projectId, requests); await loadStages(); setAddModalOpen(false); toast && toast('Stage(s) added', 'success'); }
        catch { toast && toast('Failed to add stage(s)', 'error'); } finally { setSaving(false); }
    };
    const handleToggleComplete = async (stage) => { try { await stageTemplateService.toggleStageCompletion(projectId, stage.id, !stage.isCompleted); await loadStages(); } catch { toast && toast('Failed to update stage', 'error'); } };
    const saveEdit = async (stageId) => { try { await stageTemplateService.updateStageCost(projectId, stageId, Number(editCost) || 0, editNotes); setEditingId(null); await loadStages(); toast && toast('Stage updated', 'success'); } catch { toast && toast('Failed to save stage', 'error'); } };
    const handleRemove = async (stageId) => { try { await stageTemplateService.removeStage(projectId, stageId); await loadStages(); toast && toast('Stage removed', 'warn'); } catch { toast && toast('Failed to remove stage', 'error'); } };
    if (loading) return null;
    return (<div style={{ marginTop: 4 }}>
        {stages.length === 0 && <div className={styles.emptyState}><FiCheckCircle className={styles.emptyIcon} aria-hidden="true" /><span>NO STAGES ATTACHED YET</span></div>}
        {stages.map(stage => (<div key={stage.id} className={`${styles.stageRow} ${stage.isCompleted ? styles.stageRowDone : ''}`}>
            <input type="checkbox" checked={!!stage.isCompleted} onChange={() => handleToggleComplete(stage)} disabled={!canEdit}
                aria-label={`Mark ${stage.stageName} complete`} style={{ width: 18, height: 18, flexShrink: 0, accentColor: 'var(--fs-orange)' }} />
            <div style={{ flex: 1, minWidth: 0 }}>
                <strong className={`${styles.stageName} ${stage.isCompleted ? styles.stageNameDone : ''}`}>{stage.stageName}</strong>
                {editingId === stage.id ? (<div className={styles.stageEditRow}>
                    <input type="number" value={editCost} onChange={e => setEditCost(e.target.value)} placeholder="Cost" className={styles.dtInput} aria-label="Stage cost" />
                    <input type="text" value={editNotes} onChange={e => setEditNotes(e.target.value)} placeholder="Notes" className={styles.dtInput} aria-label="Stage notes" />
                    <HardwareButton type="button" onClick={() => saveEdit(stage.id)} icon={FiSave}>SAVE</HardwareButton>
                    <button type="button" className={styles.ghostBtn} onClick={() => setEditingId(null)}><FiX aria-hidden="true" /> CANCEL</button>
                </div>) : (<div className={styles.stageCost}>UGX {fmt(stage.cost)}</div>)}
            </div>
            {canEdit && editingId !== stage.id && (<div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                <button type="button" className={styles.iconBtn2} aria-label="Edit stage" onClick={() => { setEditingId(stage.id); setEditCost(String(stage.cost || 0)); setEditNotes(stage.notes || ''); }}><FiEdit3 /></button>
                {canRemove && <button type="button" className={styles.iconBtnDanger} aria-label="Remove stage" onClick={() => handleRemove(stage.id)}><FiTrash2 /></button>}
            </div>)}
        </div>))}
        {canEdit && <button type="button" className={styles.addStageBtn} onClick={openAddModal}>+ ADD STAGE</button>}
        <HardwareModal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title="ADD STAGE(S)">
            <div style={{ marginBottom: 14 }}>
                {templates.map(t => (<label key={t.id} className={styles.stageTplRow}>
                    <input type="checkbox" checked={!!checkedTemplates[t.id]} onChange={e => setCheckedTemplates(prev => ({ ...prev, [t.id]: e.target.checked }))} style={{ width: 16, height: 16, accentColor: 'var(--fs-orange)' }} />
                    <span style={{ flex: 1 }}>{t.stageName}</span>
                </label>))}
            </div>
            <div className={modalStyles.modalField}><input type="text" value={customName} onChange={e => setCustomName(e.target.value)} placeholder="Custom stage name" className={styles.dtInput} aria-label="Custom stage name" /></div>
            <div className={modalStyles.modalFooter}>
                <HardwareButton type="button" onClick={handleAttach} loading={saving} icon={FiCheckCircle}>ADD SELECTED</HardwareButton>
            </div>
        </HardwareModal>
    </div>);
};

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
    const [recvBusy, setRecvBusy] = useState(false);
    const [rateFee, setRateFee] = useState(''); const [rateDeadline, setRateDeadline] = useState('');
    const [activeTab, setActiveTab] = useState(() => {
        const h = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : '';
        return (h.includes('finance') || h.includes('payment')) ? 'FINANCIALS' : 'OVERVIEW';
    });
    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS', 'NOTES'];
    const [noteModal, setNoteModal] = useState({ open: false, id: null, content: '' });
    const [payModal, setPayModal] = useState({ open: false });
    const [payAmount, setPayAmount] = useState(''); const [payNotes, setPayNotes] = useState('');
    const [payType, setPayType] = useState('TITLE'); const [paying, setPaying] = useState(false);
    const [drawers, setDrawers] = useState({ overview: true, balance: true, recv: true, history: true, notes: true, owners: true, docs: true, stagesPanel: true });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));
    const { confirmState, confirm, handleAnswer } = useConfirm();
    const firstInputRef = useRef(null);
    const fileInputRef = useRef(null);
    const touchedRef = useRef(false);
    const touchedSetBuffer = React.useCallback((updater) => { touchedRef.current = true; setBuffer(updater); }, []);
    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(!committing && isEditing);
    const lastActiveRef = useRef(Date.now());
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
        if (action === 'pay') { setActiveTab('FINANCIALS'); setTimeout(() => { setPayType('TITLE'); setPayAmount(''); setPayNotes(''); setPayModal({ open: true }); }, 400); }
        else if (action === 'storage') { setActiveTab('FINANCIALS'); setTimeout(() => { setPayType('STORAGE'); setPayAmount(''); setPayNotes(''); setPayModal({ open: true }); }, 400); }
    }, [location.search, binder]);
    useEffect(() => {
        const t = setInterval(() => {
            if (!isEditing || committing) return;
            if (Date.now() - lastActiveRef.current > 5 * 60 * 1000) {
                lastActiveRef.current = Date.now();
                handleCommit();
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
            buffer.owners?.forEach((o, i) => { if (!o.fullName?.trim()) fe['owner_' + i + '_name'] = 'Required'; });
            setFieldErrors(fe); toast('VALIDATION FAILED: ' + errors[0], 'error', 6000); return;
        }
        setFieldErrors({}); setCommitting(true);
        try {
            await landService.updateMasterFolder(id, { ...buffer, totalCost: Number(buffer.totalCost) || 0, initialPayment: Number(buffer.initialPayment) || 0 });
            predictionService.learn(buffer); touchedRef.current = false; setIsEditing(false);
            await loadFolderData(); toast('Changes saved successfully', 'success');
        } catch (err) { toast('SAVE FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setCommitting(false); }
    };
    const handleRelease = async () => { const ok = await confirm('RELEASE TITLE', 'Mark this title as released to the client? This records the handover.', 'warn'); if (!ok) return; try { await landService.authorizeRelease(id, 'Released from folder page'); await loadFolderData(); toast('Title released.', 'success'); } catch (err) { toast(err.response?.data?.message || 'RELEASE FAILED', 'error', 8000); } };
    const handleToggleProblem = async () => { const was = project.problem; try { await folderPortalService.toggleProblem(id); await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };
    const handleRelease = async () => { const ok = await confirm('RELEASE TITLE', 'Mark this title as released to the client? This records the handover.', 'warn'); if (!ok) return; try { await landService.authorizeRelease(id, 'Released from folder page'); await loadFolderData(); toast('Title released.', 'success'); } catch (err) { toast(err.response?.data?.message || 'RELEASE FAILED', 'error', 8000); } };
    const handleToggleProblem = async () => { const was = project.problem; try { await folderPortalService.toggleProblem(id); await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };
    const handleUnlock = async () => { touchedRef.current = false; setIsEditing(true); try { await landService.logDossierUnlock(id); } catch {} };
    const handleAbort = async () => { const ok = await confirm('DISCARD CHANGES', 'All unsaved changes will be lost.', 'warn'); if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); } };
    const handleNuclearPurge = async () => { const ok = await confirm('DELETE', 'PERMANENTLY erase this entire archive entry. Cannot be undone.', 'danger'); if (!ok) return; try { await landService.purgeAsset(id); toast('Record permanently deleted', 'warn', 3000); setTimeout(() => navigate('/land/projects'), 1500); } catch { toast('Delete failed', 'error'); } };
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
    const handleVaultAction = async (files) => { if (!files?.length) return; setCommitting(true); try { await landService.addExtraDocuments(id, files); await loadFolderData(); toast(files.length + ' document(s) uploaded', 'success', 3000); } catch { toast('INGESTION FAILED', 'error', 8000); } finally { setCommitting(false); } };
    const handleDeleteDoc = async (docId, fileName) => { const ok = await confirm('DELETE DOCUMENT', 'Delete "' + fileName + '"?', 'danger'); if (!ok) return; try { await landService.deleteDocument(docId); await loadFolderData(); toast('Document removed', 'warn', 3000); } catch { toast('DELETE FAILED', 'error'); } };
    const handleNoteSave = async () => { if (!noteModal.content.trim()) return; try { if (noteModal.id) await landService.editStandaloneNote(noteModal.id, noteModal.content); else await landService.addStandaloneNote(id, noteModal.content); setNoteModal({ open: false, id: null, content: '' }); await loadFolderData(); toast('Note saved', 'success', 3000); } catch { toast('SAVE FAILED', 'error'); } };
    const handleDeleteNote = async (noteId) => { const ok = await confirm('DELETE NOTE', 'Delete this entry?', 'danger'); if (!ok) return; try { await landService.deleteStandaloneNote(noteId); await loadFolderData(); toast('Note deleted', 'warn', 3000); } catch { toast('DELETE FAILED', 'error'); } };
    const runReceivableAction = async (action) => {
        setRecvBusy(true);
        try {
            if (action === 'ENTER') await folderPortalService.enter(id);
            else if (action === 'SETTINGS') await folderPortalService.settings(id, { rate: rateFee, deadline: rateDeadline });
            else await folderPortalService.exit(id, action);
            await loadFolderData();
            toast(action === 'WAIVE' ? 'Storage fees waived.' : action === 'CAPITALIZE' ? 'Storage fees capitalized.' : action === 'SET_ASIDE' ? 'Receivable set aside — record retained.' : action === 'ENTER' ? 'Moved to receivables.' : 'Receivable settings saved.', 'success');
        } catch (err) { toast('RECEIVABLE ACTION FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setRecvBusy(false); }
    };
    const askReceivable = async (action) => {
        const msgs = {
            ENTER: ['MOVE TO RECEIVABLES', 'Freeze the balance and start monthly storage fees (default UGX 50,000). Continue?', 'warn'],
            SET_ASIDE: ['SET ASIDE', 'Stop fee accumulation but KEEP the fee record so the client can be re-entered later. Continue?', 'warn'],
            CAPITALIZE: ['CAPITALIZE FEES', 'Add accumulated storage fees to the total plot value. Continue?', 'warn'],
            WAIVE: ['WAIVE FEES', 'Permanently forgive the accumulated storage fees. This cannot be undone. Continue?', 'danger'],
            SETTINGS: ['SAVE SETTINGS', 'Update the monthly rate / freeze deadline for this project. Continue?', 'warn'],
        };
        const m = msgs[action];
        const ok = await confirm(m[0], m[1], m[2]);
        if (ok) runReceivableAction(action);
    };
    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        setPaying(true);
        try {
            const fullNotes = payType === 'STORAGE' ? ('[STORAGE FEE PAYMENT] ' + payNotes).trim() : payNotes;
            await recoveryService.recordPayment(id, payAmount, fullNotes);
            await loadFolderData(); setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            toast('Payment recorded successfully', 'success');
        } catch (err) { toast('PAYMENT FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
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
    const noteCount = (binder.notes || []).length;
    const paymentCount = payments.length;
    const totalValue = Number(project?.totalCost || 0);
    const amountPaid = Number(project?.amountPaid || 0);
    const storageFees = Number(project?.storageFeesAccumulated || 0);
    const receivableAmountOwed = Math.max(0, totalValue + storageFees - amountPaid);
    const activeAmountOwed = Math.max(0, totalValue - amountPaid);
    const amountOwed = isReceivable ? receivableAmountOwed : activeAmountOwed;
    const arrearsEdit = (Number(buffer?.totalCost) || 0) - (Number(buffer?.initialPayment) || 0);
    const lastPay = project?.lastPaymentDate ? new Date(project.lastPaymentDate) : null;
    const daysSincePay = lastPay ? Math.floor((Date.now() - lastPay.getTime()) / 86400000) : null;
    const statusBadge = isReceivable ? ['RECEIVABLE', 'badgeRecv']
        : project.landTitle?.isReleased ? ['RELEASED', 'badgeReleased']
        : (totalValue > 0 && amountPaid >= totalValue) ? ['PAID', 'badgePaid']
        : !project.landTitle ? ['PROCESSING', 'badgeProcessing']
        : (daysSincePay === null || daysSincePay > 30) ? ['CRITICAL', 'badgeCritical']
        : ['ACTIVE', 'badgeActive'];
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
                        
                        {isBacklog ? <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>
                            : <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span>}
                        {isReceivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>IN RECEIVABLES</span>
                            : amountPaid >= totalValue ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>FULLY PAID</span>
                            : <span className={`${styles.textBadge} ${styles.badgeActive}`}>ACTIVE</span>}
                        {project.landTitle?.isReleased && <span className={`${styles.textBadge} ${styles.badgeReleased}`}>RELEASED</span>}
                        {project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}
                        {project.storagePaused && <span className={`${styles.textBadge} ${styles.badgePaused}`}>STORAGE PAUSED</span>}
                        {project.negotiationDeadline && <span className={`${styles.textBadge} ${styles.badgePaused}`}>NEGOTIATION</span>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {!isEditing && (<div className={styles.ctrlGroup}>
                        <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record"><FiPrinter aria-hidden="true" /></button>
                        {canEdit && <button className={styles.ctrlBtnPay} onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}><FiDollarSign aria-hidden="true" /> PAYMENT</button>}
                        {canMoney && project.landTitle && !project.landTitle.isReleased && <button className={styles.releaseBtn} onClick={handleRelease}><FiCheckCircle aria-hidden="true" /> RELEASE</button>}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}><FiAlertTriangle aria-hidden="true" /> PROBLEM</button>}
                        {canMoney && project.landTitle && !project.landTitle.isReleased && <button className={styles.releaseBtn} onClick={handleRelease}><FiCheckCircle aria-hidden="true" /> RELEASE</button>}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}><FiAlertTriangle aria-hidden="true" /> PROBLEM</button>}
                        {canEdit && <button className={styles.unlockMasterBtn} onClick={handleUnlock}><FiUnlock aria-hidden="true" /> EDIT</button>}
                    </div>)}
                    {isEditing && (<div className={styles.ctrlGroup}>
                        {isRoot && <button className={styles.purgeBtn} onClick={handleNuclearPurge}><FiTrash2 aria-hidden="true" /> DELETE</button>}
                        <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}><FiX aria-hidden="true" /> CANCEL</button>
                        <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}><FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}</button>
                    </div>)}
                </div>
            </header>
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                {TABS.map(tab => (<button key={tab} role="tab" aria-selected={activeTab === tab}
                    className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`} onClick={() => setActiveTab(tab)} title={tab}>
                    <span className={styles.tabFull}>{tab}</span><span className={styles.tabShort}>{tab.substring(0, 2)}</span>
                </button>))}
            </div>
            <main className={styles.workstationBody} role="tabpanel">
                <section className={styles.hwPanel} aria-label="Plot Details" style={activeTab !== 'OVERVIEW' ? { display: 'none' } : {}}>
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.overview} onClick={() => toggleDrawer('overview')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.overview ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        {isEditing ? (<>
                            {!project.landTitle && (<div className={styles.convertRow}>
                                <button type="button" className={`${styles.convertBtn} ${buffer.convertToTitle ? styles.convertBtnActive : ''}`}
                                    onClick={() => touchedSetBuffer(p => ({ ...p, convertToTitle: !p.convertToTitle }))}><FiCheckCircle aria-hidden="true" /> {buffer.convertToTitle ? 'CONVERT TO FOLDER' : 'CONVERT TO TITLE'}</button>
                                <span className={styles.inputHint}>Unlocks Plot ID, Tenure and Title ID fields</span>
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
                            <div className={styles.readOnlyGrid}>
                                {[['DISTRICT', project.district], ['COUNTY', project.county], ['SUB-COUNTY', project.subCounty], ['PARISH', project.parish], ['VILLAGE', project.village], ['AREA', project.area]].map(([l, v], i) => (
                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                            </div>
                            {project.landTitle && (<div className={styles.readOnlyGrid}>
                                {[['PLOT ID', project.landTitle.plotNumber], ['TENURE', project.landTitle.tenure], ['TITLE ID', project.landTitle.titleId], ['BLOCK / ROAD', project.landTitle.blockRoad]].map(([l, v], i) => (
                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                            </div>)}
                        </>)}
                    </div></div>
                </section>
                {!project.landTitle && !buffer.convertToTitle && (
<section className={styles.hwPanel} aria-label="Stage Checklist" style={activeTab !== 'OVERVIEW' ? { display: 'none' } : {}}>
                    <DrawerHeader label="STAGE CHECKLIST" isOpen={drawers.stagesPanel} onClick={() => toggleDrawer('stagesPanel')} icon={FiCheckCircle} />
                    <div className={`${styles.panelBody} ${drawers.stagesPanel ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        <StageChecklistPanel projectId={id} canEdit={isEditing && canEdit} canRemove={isDirector} toast={toast} />
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
                                <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({ ...buffer, initialPayment: v })} />
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>AMOUNT OWED</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                    <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled /></div>
                            </div>) : isReceivable ? (<div className={styles.moneyStatsRow}>
                                <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalValue)}</strong></div>
                                <div className={styles.statBox}><label style={{ color: 'var(--fs-red)' }}>+ STORAGE FEES</label><strong style={{ color: 'var(--fs-red)' }}>UGX {fmt(storageFees)}</strong></div>
                                <div className={styles.statBox}><label style={{ color: 'var(--fs-green)' }}>PAID</label><strong style={{ color: 'var(--fs-green)' }}>UGX {fmt(amountPaid)}</strong></div>
                                <div className={`${styles.statBox} ${styles.statRed}`}><label>AMOUNT OWED</label><strong>UGX {fmt(receivableAmountOwed)}</strong></div>
                            </div>) : (<div className={styles.moneyStatsRow}>
                                <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalValue)}</strong></div>
                                <div className={styles.statBox}><label style={{ color: 'var(--fs-green)' }}>PAID</label><strong style={{ color: 'var(--fs-green)' }}>UGX {fmt(amountPaid)}</strong></div>
                                <div className={`${styles.statBox} ${styles.statRed}`}><label>AMOUNT OWED</label><strong>UGX {fmt(activeAmountOwed)}</strong></div>
                            </div>)}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Receivables and Portfolio" id="receivable-controls">
                        <DrawerHeader label="RECEIVABLES & PORTFOLIO" isOpen={drawers.recv} onClick={() => toggleDrawer('recv')} icon={FiAlertOctagon} count={portfolio.length || undefined} />
                        <div className={`${styles.panelBody} ${drawers.recv ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                            {canMoney && (<div className={styles.inputGrid3}>
                                <CurrencyInput label="MONTHLY STORAGE RATE" value={rateFee} onChange={v => setRateFee(v)} hint="Blank = default 50,000" />
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label htmlFor="freezeDeadline">FREEZE DEADLINE</label></div>
                                    <input id="freezeDeadline" type="datetime-local" className={styles.dtInput} value={rateDeadline} onChange={e => setRateDeadline(e.target.value)} /></div>
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>&nbsp;</label></div>
                                    <HardwareButton type="button" icon={FiSave} loading={recvBusy} onClick={() => askReceivable('SETTINGS')}>SAVE SETTINGS</HardwareButton></div>
                            </div>)}
                            <div className={styles.recvActionRow}>
                                {!isReceivable
                                    ? canEdit && <HardwareButton type="button" icon={FiAlertOctagon} loading={recvBusy} onClick={() => askReceivable('ENTER')}>+ RECEIVABLES</HardwareButton>
                                    : canMoney && (<>
                                        <HardwareButton type="button" icon={FiArchive} loading={recvBusy} onClick={() => askReceivable('SET_ASIDE')}>SET ASIDE</HardwareButton>
                                        <button type="button" className={styles.ghostBtn} onClick={() => askReceivable('CAPITALIZE')} disabled={recvBusy}><FiCreditCard aria-hidden="true" /> CAPITALIZE</button>
                                        <button type="button" className={styles.dangerBtn} onClick={() => askReceivable('WAIVE')} disabled={recvBusy}><FiTrash2 aria-hidden="true" /> WAIVE</button>
                                    </>)}
                            </div>
                            <h3 className={styles.sectionTitle}>OWNER PORTFOLIO</h3>
                            {portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO OTHER PROJECTS FOR THESE OWNERS</span></div>) : (
                                <table className={styles.portfolioTable}>
                                    <thead><tr><th>#</th><th>PLOT</th><th>SHARED OWNER</th><th>STATUS</th></tr></thead>
                                    <tbody>{portfolio.map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                        onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                        <td>{r.index}</td><td>{r.plot || '—'}</td><td>{r.sharedOwner}</td>
                                        <td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
                                    </tr>))}</tbody>
                                </table>
                            )}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                        <DrawerHeader label="PAYMENT HISTORY" isOpen={drawers.history} onClick={() => toggleDrawer('history')} icon={FiActivity} count={paymentCount} />
                        <div className={`${styles.panelBody} ${drawers.history ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                            {paymentCount === 0 ? (<div className={styles.emptyState}><FiDollarSign className={styles.emptyIcon} aria-hidden="true" /><span>NO PAYMENTS RECORDED YET</span></div>) : (
                                <div className={styles.paymentList}>{payments.map((pay, i) => (<div key={pay.id || i} id={'payment-' + pay.id} className={styles.paymentRow}>
                                    <div className={styles.payRowLeft}><div className={styles.payAmount}>UGX {fmt(pay.amountPaid)}</div>
                                        <div className={styles.payMeta}><span className={styles.payType}>{pay.paymentType}</span><span className={styles.payBy}>by {pay.recordedBy}</span></div></div>
                                    <div className={styles.payRowRight}><div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div></div>
                                </div>))}</div>)}
                        </div></div>
                    </section>
                </div>
                <section className={styles.hwPanel} aria-label="Owners" style={activeTab !== 'OWNERS' ? {display:'none'} : {}}>
                    <DrawerHeader label="OWNERS" isOpen={drawers.owners} onClick={() => toggleDrawer('owners')} icon={FiUsers} count={project.proprietors.length} />
                    <div className={`${styles.panelBody} ${drawers.owners ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <div className={styles.ownersGrid2}>
                            {isEditing ? buffer.owners.map((o, idx) => (<div key={idx} className={styles.ownerEditCard}>
                                <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                <SmartInput label="NIN" value={o.nationalId} required onChange={e => handleOwnerChange(idx,'nationalId',e.target.value)} onBlur={e => handleNinBlurCheck(idx, e.target.value)} id={`owner_${idx}_nin`} />
                                <SmartInput label="PHONE" value={o.phone} onChange={e => handleOwnerChange(idx,'phone',e.target.value)} id={`owner_${idx}_phone`} />
                                <SmartInput label="EMAIL" value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} id={`owner_${idx}_email`} />
                                <SmartInput label="ADDRESS" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />
                            </div>)) : project.proprietors.map((p, i) => (<div key={i} className={styles.ownerStaticCard}>
                                <h2 className={styles.ownerName}>{p.fullName}</h2>
                                <div className={styles.infoColumns}>
                                    <div className={styles.infoRow}><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber||'---'}</span></div>
                                    <div className={styles.infoRow}><FiMail aria-hidden="true" /><span>{p.email||'---'}</span></div>
                                    <div className={styles.infoRow}><FiShield aria-hidden="true" /><span>{p.nationalId||'---'}</span></div>
                                    <div className={styles.infoRow}><FiMapPin aria-hidden="true" /><span>{p.homeAddress||'---'}</span></div>
                                </div>
                                {(portfolio.filter(r => r.sharedOwner === p.fullName).length > 0) && (
                                    <div className={styles.ownerPortfolio}>
                                        <h3 className={styles.sectionTitle}>OTHER PROJECTS</h3>
                                        <table className={styles.portfolioTable}><tbody>
                                            {portfolio.filter(r => r.sharedOwner === p.fullName).map((r, k) => (
                                                <tr key={k} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                                    onKeyDown={ev => { if (ev.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                                    <td>#{r.index}</td><td>{r.plot || '—'}</td>
                                                    <td>{r.receivable ? 'RECEIVABLE' : r.titled ? 'TITLED' : 'BACKLOG'}</td>
                                                </tr>))}
                                        </tbody></table>
                                    </div>)}
                            </div>))}
                        </div>
                        <h3 className={styles.sectionTitle}>RELATED PROJECTS</h3>
                        {portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
                            <table className={styles.portfolioTable}>
                                <thead><tr><th>#</th><th>PLOT</th><th>OWNER</th><th>STATUS</th></tr></thead>
                                <tbody>{portfolio.map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                    onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                    <td>#{r.index}</td><td>{r.plot || '—'}</td><td>{r.sharedOwner}</td>
                                    <td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
                                </tr>))}</tbody>
                            </table>)}
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Documents" style={activeTab !== 'DOCUMENTS' ? { display: 'none' } : {}}>
                    <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')} icon={FiUploadCloud} count={docCount} />
                    <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
                        {docCount === 0 ? (<div className={styles.emptyState}><FiUploadCloud className={styles.emptyIcon} aria-hidden="true" /><span>NO DOCUMENTS ATTACHED</span>
                            {isEditing && canEdit && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}</div>) : (<>
                            <div className={styles.compactVault}>{binder.documents.map((doc, idx) => (<div key={idx} className={styles.docTag}>
                                <FiFileText className={styles.docIcon} aria-hidden="true" />
                                <button type="button" className={styles.docName} onClick={() => handleOpenDoc(doc.filePath)}>{doc.fileName}</button>
                                {isEditing && canEdit && <button type="button" className={styles.iconBtn} onClick={() => handleDeleteDoc(doc.id, doc.fileName)}><FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>}
                            </div>))}</div>
                            {isEditing && canEdit && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}
                        </>)}
                    </div></div>
                
                </section>


            <div style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>
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
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />
            <HardwareModal isOpen={noteModal.open} onClose={() => { setNoteModal({ open: false, id: null, content: '' }); }} title={noteModal.id ? 'EDIT NOTE' : 'ADD NOTE'}>
                <div className={modalStyles.modalField}><textarea className={modalStyles.modalTextarea} value={noteModal.content} onChange={e => setNoteModal({ ...noteModal, content: e.target.value })} placeholder="Enter interaction note..." aria-label="Note content" /></div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave}><FiSave aria-hidden="true" /> SAVE ENTRY</button>
                </div>
            </HardwareModal>
            <HardwareModal isOpen={payModal.open} onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={'RECORD PAYMENT - ' + (project.landTitle?.plotNumber || project.projectIndex || 'FOLDER')}>
                {isReceivable && (<div className={styles.payTypeRow}><div className={styles.payTypeButtons}>
                    <button type="button" className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`} onClick={() => setPayType('TITLE')}><FiHome size={12} /> TITLE PAYMENT</button>
                    <button type="button" className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`} onClick={() => setPayType('STORAGE')}><FiArchive size={12} /> STORAGE FEE</button>
                </div></div>)}
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="number" className={modalStyles.modalInput} placeholder={'e.g. ' + fmt(Math.max(0, amountOwed))} value={payAmount} onChange={e => setPayAmount(e.target.value)} /></div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea} value={payNotes} onChange={e => setPayNotes(e.target.value)} /></div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton type="button" onClick={handleRecordPayment} loading={paying} icon={FiDollarSign}>CONFIRM</HardwareButton>
                </div>
            </HardwareModal>
            <BackToTopButton />
        </div>
    );
};
export default FolderPage;
