#!/usr/bin/env python3
"""fix29.py — restore tabbed FolderPage (print + payments) + seed all intake scenarios.
Run: py fix29.py"""
import subprocess
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
WROTE=[]
def write(rel, content):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8"); WROTE.append(rel)

# ---------------- FolderPage.jsx: tabbed layout + print + payments ----------------
write('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', r"""// PATH: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
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
    FiDollarSign, FiActivity, FiHome, FiArchive, FiArrowUp
} from 'react-icons/fi';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
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
import styles from './FolderPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const STAGE_LABELS = ['COMMITMENT', 'FIELD WORK', 'DOCUMENTATION', 'DEED PLAN', 'RELEASE'];
const EMAIL_DOMAINS = ['@gmail.com', '@yahoo.com', '@outlook.com', '@hotmail.com', '@icloud.com'];
const formatSinglePhone = (raw) => { const d = raw.replace(/\D/g, ''); if (!d) return ''; return [d.slice(0,4), d.slice(4,7), d.slice(7,10)].filter(Boolean).join(' '); };
const formatPhoneEntry = (raw) => raw.split('/').map(p => formatSinglePhone(p.trim())).filter(Boolean).join(' / ');
const validateBuffer = (buffer) => {
    const errors = [];
    if (!buffer.plotNumber?.trim()) errors.push('PLOT ID IS REQUIRED');
    if (!buffer.district?.trim())   errors.push('DISTRICT IS REQUIRED');
    if (!buffer.tenure?.trim())     errors.push('TENURE IS REQUIRED');
    buffer.owners?.forEach((o, i) => {
        if (!o.fullName?.trim()) errors.push(`OWNER ${i + 1}: LEGAL NAME IS REQUIRED`);
        if (!o.nationalId?.trim()) errors.push(`OWNER ${i + 1}: NATIONAL ID (NIN) IS REQUIRED`);
    });
    return errors;
};
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
        {datalistId && <datalist id={datalistId}>{suggestions.map((s,i) => <option key={i} value={s} />)}</datalist>}
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
    const inputId = id || 'cur-' + (label||'').replace(/\W/g,'-').toLowerCase();
    const display = focused ? String(value||'') : (value ? Number(value).toLocaleString() : '');
    return (<div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
        <div className={styles.inputLabelRow}><label htmlFor={inputId}>{label}</label><span className={styles.currencyTag}>UGX</span>
            {disabled && <span className={styles.autoCalcBadge}>LOCKED</span>}</div>
        <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''} ${disabled ? styles.calcInput : ''}`}
            inputMode="numeric" value={display} onFocus={() => { if (!disabled) setFocused(true); }} onBlur={() => setFocused(false)}
            onChange={e => { if (!disabled) onChange(e.target.value.replace(/\D/g,'')); }} placeholder="0" disabled={disabled} />
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
        <div className={`${styles.confirmHeader} ${isDanger ? styles.confirmHeaderDanger : styles.confirmHeaderWarn}`}>
            {isDanger ? <FiAlertOctagon className={styles.confirmIcon} aria-hidden="true" /> : <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" />}
            <span className={styles.confirmTitle}>{state.title}</span></div>
        <p className={styles.confirmMessage}>{state.message}</p>
        <div className={styles.confirmFooter}>
            <button type="button" className={styles.confirmCancelBtn} onClick={() => onAnswer(false)} autoFocus><FiX aria-hidden="true" /> CANCEL</button>
            <button type="button" className={`${styles.confirmOkBtn} ${isDanger ? styles.confirmOkDanger : styles.confirmOkWarn}`} onClick={() => onAnswer(true)}>
                {isDanger ? <><FiTrash2 aria-hidden="true" /> CONFIRM ERASE</> : <><FiCheckCircle aria-hidden="true" /> CONFIRM</>}</button>
        </div></div></div>, document.body);
};
const fmt = (n) => Number(n || 0).toLocaleString();

const StageChecklistPanel = ({ projectId, isEditing, isAdmin, toast }) => {
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
        {stages.length === 0 && <div style={{ textAlign: 'center', padding: '24px 0', color: 'rgba(255,255,255,0.25)', fontFamily: "'Space Mono',monospace", fontSize: 11, fontWeight: 900, letterSpacing: 2, textTransform: 'uppercase' }}>NO STAGES ATTACHED YET</div>}
        {stages.map(stage => (<div key={stage.id} style={{ display: 'flex', alignItems: 'center', gap: 12, background: stage.isCompleted ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.04)', border: '1px solid ' + (stage.isCompleted ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'), borderRadius: 7, padding: '10px 14px', marginBottom: 8 }}>
            <input type="checkbox" checked={!!stage.isCompleted} onChange={() => handleToggleComplete(stage)} disabled={!isEditing} style={{ width: 18, height: 18, flexShrink: 0 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
                <strong style={{ fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 13, color: stage.isCompleted ? '#6ee7b7' : '#fff', textTransform: 'uppercase', textDecoration: stage.isCompleted ? 'line-through' : 'none' }}>{stage.stageName}</strong>
                {editingId === stage.id ? (<div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                    <input type="number" value={editCost} onChange={e => setEditCost(e.target.value)} placeholder="Cost" style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6, padding: '6px 10px', width: 120 }} />
                    <input type="text" value={editNotes} onChange={e => setEditNotes(e.target.value)} placeholder="Notes" style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6, padding: '6px 10px', flex: 1, minWidth: 140 }} />
                    <button onClick={() => saveEdit(stage.id)} style={{ background: '#EE8C3A', border: 'none', borderRadius: 6, padding: '6px 12px', fontWeight: 900, cursor: 'pointer' }}>SAVE</button>
                    <button onClick={() => setEditingId(null)} style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6, padding: '6px 12px', color: '#fff', cursor: 'pointer' }}>CANCEL</button>
                </div>) : (<div style={{ fontFamily: "'Space Mono',monospace", fontSize: 11, color: 'rgba(255,255,255,0.6)', marginTop: 4 }}>UGX {Number(stage.cost || 0).toLocaleString()}</div>)}
            </div>
            {isEditing && editingId !== stage.id && (<div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                <button onClick={() => { setEditingId(stage.id); setEditCost(String(stage.cost || 0)); setEditNotes(stage.notes || ''); }} style={{ background: 'transparent', border: 'none', color: '#EE8C3A', cursor: 'pointer', fontSize: 15, padding: 4 }}><FiEdit3 /></button>
                {isAdmin && <button onClick={() => handleRemove(stage.id)} style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: 15, padding: 4 }}><FiTrash2 /></button>}
            </div>)}
        </div>))}
        {isEditing && <button type="button" onClick={openAddModal} style={{ width: '100%', marginTop: 8, padding: '10px 0', background: 'rgba(238,140,58,0.06)', border: '2px dashed rgba(238,140,58,0.4)', borderRadius: 7, color: '#EE8C3A', fontWeight: 900, fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, cursor: 'pointer' }}>+ ADD STAGE</button>}
        <HardwareModal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title="ADD STAGE(S)">
            <div style={{ marginBottom: 14 }}>
                {templates.map(t => (<label key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0', cursor: 'pointer', color: '#fff' }}>
                    <input type="checkbox" checked={!!checkedTemplates[t.id]} onChange={e => setCheckedTemplates(prev => ({ ...prev, [t.id]: e.target.checked }))} style={{ width: 16, height: 16 }} />
                    <span style={{ flex: 1 }}>{t.stageName}</span>
                </label>))}
            </div>
            <input type="text" value={customName} onChange={e => setCustomName(e.target.value)} placeholder="Custom stage name" style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(255,255,255,0.07)', border: '1.5px solid rgba(255,255,255,0.18)', borderRadius: 8, padding: '10px 12px', color: '#fff', marginBottom: 8 }} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button onClick={() => setAddModalOpen(false)} style={{ background: 'rgba(255,255,255,0.06)', border: '1.5px solid rgba(255,255,255,0.2)', color: 'rgba(255,255,255,0.7)', borderRadius: 8, padding: '10px 18px', cursor: 'pointer' }}>CANCEL</button>
                <button onClick={handleAttach} disabled={saving} style={{ background: '#EE8C3A', border: 'none', color: '#1a2e30', borderRadius: 8, padding: '10px 20px', fontWeight: 900, cursor: 'pointer' }}>{saving ? 'SAVING...' : 'ADD SELECTED'}</button>
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
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR' || user?.isRoot;
    const [binder, setBinder] = useState(null);
    const [buffer, setBuffer] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [committing, setCommitting] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [ninMismatch, setNinMismatch] = useState(null);
    const [payments, setPayments] = useState([]);
    const [activeTab, setActiveTab] = useState(() => {
        const h = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : '';
        return (h.includes('finance') || h.includes('payment')) ? 'FINANCIALS' : 'OVERVIEW';
    });
    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS'];
    const [noteModal, setNoteModal] = useState({ open:false, id:null, content:'' });
    const [payModal, setPayModal] = useState({ open:false });
    const [payAmount, setPayAmount] = useState(''); const [payNotes, setPayNotes] = useState('');
    const [payType, setPayType] = useState('TITLE'); const [paying, setPaying] = useState(false);
    const [exitReceivableModal, setExitReceivableModal] = useState(false);
    const [drawers, setDrawers] = useState({ overview: true, balance: true, receivable: true, history: true, notes: true, owners: true, docs: true, stagesPanel: true });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));
    const { confirmState, confirm, handleAnswer } = useConfirm();
    const firstInputRef = useRef(null);
    const fileInputRef = useRef(null);
    const touchedRef = useRef(false);
    const touchedSetBuffer = React.useCallback((updater) => { touchedRef.current = true; setBuffer(updater); }, []);
    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(!committing && isEditing);

    // STANDARD: sidebar auto-collapses when the folder page opens
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
                if (hash === 'record-payment') { if (isAdmin) setPayModal({ open: true }); }
                else if (hash === 'storage-fees') { const el = document.getElementById('receivable-controls'); if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); el.classList.add(styles.highlightRow); setTimeout(() => el.classList.remove(styles.highlightRow), 3000); } }
                else if (hash.startsWith('payment-')) { const el = document.getElementById(hash); if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.classList.add(styles.highlightRow); setTimeout(() => el.classList.remove(styles.highlightRow), 3000); } }
                else { const el = document.getElementById('paymentHistorySection'); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') setActiveTab('OWNERS');
        else if (hash === 'vault' || hash === 'documents') setActiveTab('DOCUMENTS');
        else window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [id, isAdmin]);
    useEffect(() => { if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120); }, [isEditing]);
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const action = params.get('action');
        if (!action || !binder) return;
        if (action === 'pay') { setActiveTab('FINANCIALS'); setTimeout(() => { setPayType('TITLE'); setPayAmount(''); setPayNotes(''); setPayModal({ open: true }); }, 400); }
        else if (action === 'storage') { setActiveTab('FINANCIALS'); setTimeout(() => { setPayType('STORAGE'); setPayAmount(''); setPayNotes(''); setPayModal({ open: true }); }, 400); }
    }, [location.search, binder, isAdmin]);
    useEffect(() => {
        if (!isEditing || committing) return;
        const handler = (e) => { e.preventDefault(); e.returnValue = ''; return ''; };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);

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
                    titleId: data.project?.landTitle?.titleId || '',
                    totalCost: String(data.project?.totalCost || 0), initialPayment: String(data.project?.amountPaid || 0),
                    isLegacy: data.project?.isLegacy || false,
                    owners: (data.project?.proprietors || []).map(p => ({ fullName: p.fullName||'', phone: p.phoneNumber||'', nationalId: p.nationalId||'', address: p.homeAddress||'', email: p.email||'' })),
                });
                setFieldErrors({});
            }
        } catch { setLoadError(true); } finally { setLoading(false); }
    }, [id, isEditing]);
    useEffect(() => { loadFolderData(); }, [loadFolderData]);

    const handleCommit = async () => {
        if (ninMismatch) { toast('Confirm or fix the NIN mismatch warning before saving.', 'error', 6000); return; }
        const errors = validateBuffer(buffer);
        if (errors.length) {
            const fe = {};
            if (!buffer.plotNumber?.trim()) fe.plotNumber = 'Required';
            if (!buffer.district?.trim()) fe.district = 'Required';
            buffer.owners?.forEach((o,i) => { if (!o.fullName?.trim()) fe['owner_'+i+'_name']='Required'; });
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
    const handleUnlock = async () => { touchedRef.current = false; setIsEditing(true); try { await landService.logDossierUnlock(id); } catch {} };
    const handleAbort = async () => { const ok = await confirm('DISCARD CHANGES', 'All unsaved changes will be lost.', 'warn'); if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); } };
    const handleNuclearPurge = async () => { const ok = await confirm('DELETE', 'PERMANENTLY erase this entire archive entry. Cannot be undone.', 'danger'); if (!ok) return; try { await landService.purgeAsset(id); toast('Record permanently deleted', 'warn', 3000); setTimeout(() => navigate('/land/projects'), 1500); } catch { toast('Delete failed', 'error'); } };
    const handleStageClick = async (num) => { if (!isEditing) return; try { await landService.setRealityStage(id, num); await loadFolderData(); toast('Stage updated', 'info', 3000); } catch { toast('STAGE UPDATE FAILED', 'error'); } };
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;
        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName = (buffer.owners[idx]?.fullName || '').trim().toUpperCase();
        if (existingName && enteredName && existingName !== enteredName) { setNinMismatch({ idx, existingName: result.fullName, enteredName: buffer.owners[idx]?.fullName || '' }); return; }
        const owners = buffer.owners.map((o, i) => i !== idx ? o : { ...o, phone: o.phone.trim()?o.phone:(result.phoneNumber||o.phone), email: o.email.trim()?o.email:(result.email||o.email), address: o.address.trim()?o.address:(result.homeAddress||o.address) });
        touchedSetBuffer(p => ({ ...p, owners }));
        toast(`NIN matched ${result.fullName}. Details auto-filled.`, 'info', 4500);
    };
    const handleNinMismatchConfirm = () => setNinMismatch(null);
    const handleNinMismatchReject = () => { if (!ninMismatch) return; const idx = ninMismatch.idx; handleOwnerChange(idx, 'nationalId', ''); setNinMismatch(null); setTimeout(() => { const el = document.getElementById('owner_' + idx + '_nin'); if (el) el.focus(); }, 50); };
    const handleOwnerChange = (idx, field, val) => {
        const owners = buffer.owners.map((o,i) => { if (i !== idx) return o; let v = val; if (field==='fullName') v = val.toUpperCase(); if (field==='nationalId') v = val.toUpperCase().replace(/\s/g,''); if (field==='email') v = val.toLowerCase().replace(/\s/g,''); return { ...o, [field]: v }; });
        touchedRef.current = true; setBuffer(p => ({ ...p, owners }));
    };
    const handleEmailCommit = (idx, val) => { const owners = buffer.owners.map((o,i) => i===idx ? { ...o, email:val } : o); touchedRef.current = true; setBuffer(p => ({ ...p, owners })); };
    const handleVaultAction = async (files) => { if (!files?.length) return; setCommitting(true); try { await landService.addExtraDocuments(id, files); await loadFolderData(); toast(files.length + ' document(s) uploaded', 'success', 3000); } catch { toast('INGESTION FAILED', 'error', 8000); } finally { setCommitting(false); } };
    const handleDeleteDoc = async (docId, fileName) => { const ok = await confirm('DELETE DOCUMENT', `Delete "${fileName}"?`, 'danger'); if (!ok) return; try { await landService.deleteDocument(docId); await loadFolderData(); toast('Document removed', 'warn', 3000); } catch { toast('DELETE FAILED', 'error'); } };
    const handleNoteSave = async () => { if (!noteModal.content.trim()) return; try { if (noteModal.id) await landService.editStandaloneNote(noteModal.id, noteModal.content); else await landService.addStandaloneNote(id, noteModal.content); setNoteModal({ open:false, id:null, content:'' }); await loadFolderData(); toast('Note saved', 'success', 3000); } catch { toast('SAVE FAILED', 'error'); } };
    const handleDeleteNote = async (noteId) => { const ok = await confirm('DELETE NOTE', 'Delete this entry?', 'danger'); if (!ok) return; try { await landService.deleteStandaloneNote(noteId); await loadFolderData(); toast('Note deleted', 'warn', 3000); } catch { toast('DELETE FAILED', 'error'); } };
    const handleMoveToReceivable = async () => { const ok = await confirm('MOVE TO RECEIVABLES', 'Freeze balance and start monthly storage fees of UGX 50,000. Continue?', 'warn'); if (!ok) return; try { await recoveryService.moveToReceivable(id); await loadFolderData(); toast('Plot moved to receivables.', 'warn'); } catch (err) { toast('RECEIVABLES FAILED: ' + (err.response?.data?.message || err.message), 'error'); } };
    const handleExitReceivableConfirm = async (capitalizeFees) => { setExitReceivableModal(false); try { await recoveryService.exitReceivable(id, capitalizeFees); await loadFolderData(); toast(capitalizeFees ? 'Storage fees added to total value.' : 'Storage fees waived.', 'success'); } catch (err) { toast('EXIT FAILED: ' + (err.response?.data?.message || err.message), 'error'); } };
    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        setPaying(true);
        try {
            const fullNotes = payType === 'STORAGE' ? `[STORAGE FEE PAYMENT] ${payNotes}`.trim() : payNotes;
            await recoveryService.recordPayment(id, payAmount, fullNotes);
            await loadFolderData(); setPayModal({ open: false }); setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            toast('Payment recorded successfully', 'success');
        } catch (err) { toast('PAYMENT FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setPaying(false); }
    };
    const getDocUrl = (filePath) => { if (!filePath) return '#'; if (filePath.startsWith('http')) return filePath; const parts = filePath.split(/ge_uploads[/]/); const rel = parts.length > 1 ? parts[1] : filePath; const base = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1'; return `${base}/vault/` + rel.replace(/\\/g, '/'); };
    const handleOpenDoc = (filePath) => { if (!filePath) return; const url = getDocUrl(filePath); if (filePath.startsWith('http')) window.open(url, '_blank', 'noopener,noreferrer'); else fetch(url, { headers: { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } }).then(r => r.blob()).then(blob => { const b = URL.createObjectURL(blob); window.open(b, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(b), 30000); }).catch(() => window.open(url, '_blank', 'noopener,noreferrer')); };
    const isPDF = (filePath) => { if (!filePath) return false; const l = filePath.toLowerCase(); return l.includes('.pdf') || l.includes('application/pdf') || (l.includes('cloudinary') && l.includes('/raw/')); };
    const sg = useMemo(() => (key) => predictionService.getSuggestions(key) || [], []);

    if (loading) return <div className={styles.container}><p style={{padding:40,color:'rgba(255,255,255,0.4)'}}>Loading record…</p></div>;
    if (loadError || !binder || !buffer) return (<div style={{ padding: 'clamp(40px,8vw,80px) clamp(20px,4vw,40px)' }}><ErrorMessage type="error" title="Record not found" message="This archive entry could not be loaded." onRetry={loadFolderData} retryLabel="Try Again" /></div>);

    const project = binder.project;
    const isReceivable = project?.isReceivable || false;
    const docCount = (binder.documents||[]).length;
    const noteCount = (binder.notes||[]).length;
    const paymentCount = payments.length;
    const totalValue = Number(project?.totalCost || 0);
    const amountPaid = Number(project?.amountPaid || 0);
    const storageFees = Number(project?.storageFeesAccumulated || 0);
    const receivableAmountOwed = Math.max(0, totalValue + storageFees - amountPaid);
    const activeAmountOwed = Math.max(0, totalValue - amountPaid);
    const amountOwed = isReceivable ? receivableAmountOwed : activeAmountOwed;
    const arrearsEdit = (Number(buffer?.totalCost)||0) - (Number(buffer?.initialPayment)||0);
    const effectiveMonthlyFee = Number(project?.storageFeeOverride) > 0 ? Number(project.storageFeeOverride) : 50000;

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing || paying} />
            {/* PRINT-ONLY DOSSIER HEADER (null-safe) */}
            <div className={styles.printDossierHeader} aria-hidden="true">
                <div className={styles.printDossierMeta}>
                    <span><strong>PLOT ID:</strong> {project.landTitle?.plotNumber || project.projectIndex || 'UNTITLED'}</span>
                    <span><strong>TENURE:</strong> {project.landTitle?.tenure || '---'}</span>
                    {project.district && <span><strong>DISTRICT:</strong> {project.district}</span>}
                    <span><strong>STATUS:</strong> {project.status}</span>
                </div>
            </div>
            {/* PIPELINE HUD */}
            <nav className={styles.pipelineHUD} aria-label="Project pipeline">
                <div className={styles.track}>
                    {STAGE_LABELS.map((label, idx) => { const num = idx + 1; const active = project.currentStageIndex >= num;
                        return (<div key={num} className={styles.stageModule}>
                            <div className={`${styles.dot} ${active ? styles.dotActive : ''} ${isEditing ? styles.dotInteractive : ''}`}
                                onClick={() => handleStageClick(num)} role={isEditing ? 'button' : 'img'} tabIndex={isEditing ? 0 : -1}
                                aria-label={`Stage ${num}: ${label}${active ? ' (complete)' : ''}`}>
                                {active ? <FiCheckCircle aria-hidden="true" /> : num}
                            </div>
                            <span className={styles.stageLabel}>{label}</span>
                        </div>); })}
                </div>
                <div className={styles.protocolReadout}><strong>PROTOCOL: {project.status}</strong><span>LIVE STATUS</span></div>
            </nav>
            {/* TERMINAL HEADER with PRINT + PAYMENT + RECEIVABLES + EDIT */}
            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle?.plotNumber || `#${project.projectIndex}` || 'UNTITLED'}</h1>
                    <div className={styles.metaLine}>
                        {project.projectIndex && <span className={`${styles.metaTag} ${styles.tagBlue}`}>PROJECT #{project.projectIndex}</span>}
                        <span className={`${styles.metaTag} ${project.landTitle ? styles.tagGreen : styles.tagOrange}`}>{project.landTitle ? 'TITLED' : 'FOLDER'}</span>
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%</span>
                        {isReceivable ? <span className={styles.metaTag} style={{ color: '#ef4444' }}>RECEIVABLES</span>
                            : project.landTitle?.isReleased ? <span className={styles.metaTag} style={{ color: '#34d399' }}>RELEASED</span>
                            : amountPaid >= totalValue ? <span className={styles.metaTag} style={{ color: '#34d399' }}>FULLY PAID</span>
                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>}
                        {isEditing && <div className={styles.editBadge}>EDIT MODE ENABLED</div>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {!isEditing && (<div className={styles.ctrlGroup}>
                        <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record"><FiPrinter aria-hidden="true" /></button>
                        {isAdmin && <button className={styles.ctrlBtnPay} onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}><FiDollarSign aria-hidden="true" /> PAYMENT</button>}
                        {isAdmin && !isReceivable && <button className={styles.ctrlBtnReceivable} onClick={handleMoveToReceivable}><FiAlertOctagon aria-hidden="true" /> RECEIVABLES</button>}
                        {isAdmin && isReceivable && <button className={styles.ctrlBtnReceivable} onClick={() => setExitReceivableModal(true)}><FiAlertOctagon aria-hidden="true" /> EXIT RECEIVABLES</button>}
                        <button className={styles.unlockMasterBtn} onClick={handleUnlock}><FiUnlock aria-hidden="true" /> EDIT</button>
                    </div>)}
                    {isEditing && (<div className={styles.ctrlGroup}>
                        {user?.isRoot && <button className={styles.purgeBtn} onClick={handleNuclearPurge}><FiTrash2 aria-hidden="true" /> DELETE</button>}
                        <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}><FiX aria-hidden="true" /> CANCEL</button>
                        <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}><FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}</button>
                    </div>)}
                </div>
            </header>
            {/* TAB BAR: single heading row, click to show a section */}
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                {TABS.map(tab => (<button key={tab} role="tab" aria-selected={activeTab === tab}
                    className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`} onClick={() => setActiveTab(tab)} title={tab}>
                    <span className={styles.tabFull}>{tab}</span><span className={styles.tabShort}>{tab.substring(0, 2)}</span>
                </button>))}
            </div>
            <main className={styles.workstationBody} role="tabpanel">
                <section className={styles.hwPanel} aria-label="Plot Details" style={activeTab !== 'OVERVIEW' ? {display:'none'} : {}}>
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.overview} onClick={() => toggleDrawer('overview')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.overview ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        {isEditing ? (<>
                            <div className={styles.inputGrid3}>
                                <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                <SmartInput label="SUB-COUNTY" value={buffer.subCounty} showCaps onChange={e => touchedSetBuffer({...buffer, subCounty: e.target.value.toUpperCase()})} />
                                <SmartInput label="PARISH" value={buffer.parish} showCaps onChange={e => touchedSetBuffer({...buffer, parish: e.target.value.toUpperCase()})} />
                                <SmartInput label="VILLAGE" value={buffer.village} showCaps onChange={e => touchedSetBuffer({...buffer, village: e.target.value.toUpperCase()})} />
                                <SmartInput label="AREA" value={buffer.area} onChange={e => touchedSetBuffer({...buffer, area: e.target.value})} />
                            </div>
                            {project.landTitle && (<div className={styles.inputGrid3}>
                                <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />
                                <SmartInput label="TITLE ID" value={buffer.titleId} showCaps onChange={e => touchedSetBuffer({...buffer, titleId: e.target.value.toUpperCase()})} />
                                <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                            </div>)}
                        </>) : (<>
                            <div className={styles.readOnlyGrid}>
                                {[['DISTRICT',project.district],['COUNTY',project.county],['SUB-COUNTY',project.subCounty],['PARISH',project.parish],['VILLAGE',project.village],['AREA',project.area]].map(([l,v],i) => (
                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                            </div>
                            {project.landTitle && (<div className={styles.readOnlyGrid}>
                                {[['PLOT ID',project.landTitle.plotNumber],['TENURE',project.landTitle.tenure],['TITLE ID',project.landTitle.titleId],['BLOCK / ROAD',project.landTitle.blockRoad]].map(([l,v],i) => (
                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}
                            </div>)}
                        </>)}
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Stage Checklist" style={activeTab !== 'OVERVIEW' ? {display:'none'} : {}}>
                    <DrawerHeader label="STAGE CHECKLIST" isOpen={drawers.stagesPanel} onClick={() => toggleDrawer('stagesPanel')} icon={FiCheckCircle} />
                    <div className={`${styles.panelBody} ${drawers.stagesPanel ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <StageChecklistPanel projectId={id} isEditing={isEditing} isAdmin={isAdmin} toast={toast} />
                    </div></div>
                </section>
                <div className={styles.financialsStack} style={activeTab !== 'FINANCIALS' ? {display:'none'} : {}}>
                    <section className={styles.hwPanel} aria-label="Balance Summary">
                        <DrawerHeader label="BALANCE SUMMARY" isOpen={drawers.balance} onClick={() => toggleDrawer('balance')} icon={FiCreditCard} />
                        <div className={`${styles.panelBody} ${drawers.balance ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            {isEditing ? (<div className={styles.inputGrid3}>
                                <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />
                                <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />
                                <div className={styles.hwInputWrap}><div className={styles.inputLabelRow}><label>AMOUNT OWED</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                    <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled /></div>
                            </div>) : isReceivable ? (<div className={styles.moneyStatsRow}>
                                <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalValue)}</strong></div>
                                <div className={styles.statBox}><label style={{color:'#ef4444'}}>+ STORAGE FEES</label><strong style={{color:'#fca5a5'}}>UGX {fmt(storageFees)}</strong></div>
                                <div className={styles.statBox}><label style={{color:'#22c55e'}}>PAID</label><strong style={{color:'#22c55e'}}>UGX {fmt(amountPaid)}</strong></div>
                                <div className={styles.statBox}><label style={{color:'#fca5a5'}}>AMOUNT OWED</label><strong style={{color:'#fca5a5'}}>UGX {fmt(receivableAmountOwed)}</strong></div>
                            </div>) : (<div className={styles.moneyStatsRow}>
                                <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalValue)}</strong></div>
                                <div className={styles.statBox}><label>PAID</label><strong style={{color:'#22c55e'}}>UGX {fmt(amountPaid)}</strong></div>
                                <div className={styles.statBox}><label>AMOUNT OWED</label><strong style={{color:'#fca5a5'}}>UGX {fmt(activeAmountOwed)}</strong></div>
                            </div>)}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                        <DrawerHeader label="PAYMENT HISTORY" isOpen={drawers.history} onClick={() => toggleDrawer('history')} icon={FiActivity} count={paymentCount} />
                        <div className={`${styles.panelBody} ${drawers.history ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            {paymentCount === 0 ? (<div className={styles.emptyState}><FiDollarSign className={styles.emptyIcon} aria-hidden="true" /><span>NO PAYMENTS RECORDED YET</span></div>) : (
                                <div className={styles.paymentList}>{payments.map((pay, i) => (<div key={pay.id || i} id={`payment-${pay.id}`} className={styles.paymentRow}>
                                    <div className={styles.payRowLeft}><div className={styles.payAmount}>UGX {fmt(pay.amountPaid)}</div>
                                        <div className={styles.payMeta}><span className={styles.payType}>{pay.paymentType}</span><span className={styles.payBy}>by {pay.recordedBy}</span></div></div>
                                    <div className={styles.payRowRight}><div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div></div>
                                </div>))}</div>)}
                        </div></div>
                    </section>
                    <section className={styles.hwPanel} aria-label="Notes and Call Log">
                        <DrawerHeader label="NOTES & CALL LOG" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} count={noteCount} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                            {isEditing && <button type="button" className={styles.addNoteBtn} onClick={() => setNoteModal({open:true,id:null,content:''})}>+ ADD NOTE</button>}
                            {noteCount === 0 ? (<div className={styles.emptyState}><FiInfo className={styles.emptyIcon} aria-hidden="true" /><span>NO NOTES LOGGED YET</span></div>) : (
                                <div className={styles.notebookTimeline}>{binder.notes.map((log, i) => (<article key={i} className={styles.ruledNote}>
                                    <div className={styles.noteMeta}><time className={styles.noteTime}>{new Date(log.timestamp).toLocaleDateString()}</time><span className={styles.noteAuthor}>by {log.recordedBy}</span>
                                        {isEditing && (<div className={styles.actionBlock}>
                                            <button type="button" className={styles.iconBtn} onClick={() => setNoteModal({open:true,id:log.id,content:log.notes})}><FiEdit3 className={styles.editIcon} aria-hidden="true" /></button>
                                            <button type="button" className={styles.iconBtn} onClick={() => handleDeleteNote(log.id)}><FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>
                                        </div>)}</div>
                                    <p className={styles.noteContent}>{log.notes}</p>
                                </article>))}</div>)}
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
                                <SmartInput label="EMAIL" value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} onCommit={val => handleEmailCommit(idx,val)} id={`owner_${idx}_email`} />
                            </div>)) : project.proprietors.map((p, i) => (<div key={i} className={styles.ownerStaticCard}>
                                <h2 className={styles.ownerName}>{p.fullName}</h2>
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
                <section className={styles.hwPanel} aria-label="Documents" style={activeTab !== 'DOCUMENTS' ? {display:'none'} : {}}>
                    <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')} icon={FiUploadCloud} count={docCount} />
                    <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        {docCount === 0 ? (<div className={styles.emptyState}><FiUploadCloud className={styles.emptyIcon} aria-hidden="true" /><span>NO DOCUMENTS ATTACHED</span>
                            {isEditing && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ INGEST NEW SCANS</button>}</div>) : (<>
                            <div className={styles.compactVault}>{binder.documents.map((doc, idx) => (<div key={idx} className={styles.docTag}>
                                <FiFileText className={styles.docIcon} aria-hidden="true" />
                                <button type="button" className={styles.docName} onClick={() => handleOpenDoc(doc.filePath)}>{doc.fileName}</button>
                                {isEditing && <button type="button" className={styles.iconBtn} onClick={() => handleDeleteDoc(doc.id, doc.fileName)}><FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>}
                            </div>))}</div>
                            {isEditing && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ INGEST MORE SCANS</button>}
                        </>)}
                    </div></div>
                </section>
            </main>
            <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp" style={{ display:'none' }} aria-hidden="true" tabIndex={-1}
                onChange={e => { if (!e.target.files?.length) return; handleVaultAction(Array.from(e.target.files)); e.target.value=''; }} />
            <UnsavedChangesModal isOpen={guardModalOpen} onStay={handleStay} onLeave={handleLeave} context="Plot Record Edit" />
            <NinMismatchModal isOpen={!!ninMismatch} existingName={ninMismatch?.existingName} enteredName={ninMismatch?.enteredName} onConfirm={handleNinMismatchConfirm} onReject={handleNinMismatchReject} />
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />
            <HardwareModal isOpen={noteModal.open} onClose={() => { setNoteModal({open:false,id:null,content:''}); }} title="ADD NOTE">
                <div className={modalStyles.modalField}><textarea className={modalStyles.modalTextarea} value={noteModal.content} onChange={e => setNoteModal({...noteModal,content:e.target.value})} placeholder="Enter interaction note..." aria-label="Note content" /></div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave}><FiSave aria-hidden="true" /> SAVE ENTRY</button>
                </div>
            </HardwareModal>
            <HardwareModal isOpen={exitReceivableModal} onClose={() => setExitReceivableModal(false)} title="EXIT RECEIVABLES">
                <div className={modalStyles.modalInfoBoxDanger} style={{marginBottom:16}}><strong>Accumulated storage fees: UGX {fmt(storageFees)}</strong></div>
                <button type="button" onClick={() => handleExitReceivableConfirm(true)} style={{width:'100%',padding:'10px 0',background:'#ef4444',border:'none',borderRadius:7,fontWeight:900,color:'#fff',cursor:'pointer',marginBottom:10}}>CAPITALIZE FEES</button>
                <button type="button" onClick={() => handleExitReceivableConfirm(false)} style={{width:'100%',padding:'10px 0',background:'#10b981',border:'none',borderRadius:7,fontWeight:900,color:'#1a2e30',cursor:'pointer'}}>WAIVE FEES</button>
            </HardwareModal>
            <HardwareModal isOpen={payModal.open} onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={`RECORD PAYMENT - ${project.landTitle?.plotNumber || project.projectIndex || 'FOLDER'}`}>
                {isReceivable && (<div className={styles.payTypeRow}><div className={styles.payTypeButtons}>
                    <button type="button" className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`} onClick={() => setPayType('TITLE')}><FiHome size={12} /> TITLE PAYMENT</button>
                    <button type="button" className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`} onClick={() => setPayType('STORAGE')}><FiArchive size={12} /> STORAGE FEE</button>
                </div></div>)}
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="number" className={modalStyles.modalInput} placeholder={`e.g. ${fmt(Math.max(0, amountOwed))}`} value={payAmount} onChange={e => setPayAmount(e.target.value)} /></div>
                <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea} value={payNotes} onChange={e => setPayNotes(e.target.value)} /></div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary} onClick={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }}><FiX aria-hidden="true" /> CANCEL</button>
                    <HardwareButton type="button" onClick={handleRecordPayment} loading={paying} icon={FiDollarSign}>CONFIRM</HardwareButton>
                </div>
            </HardwareModal>
            <BackToTopButton />
        </div>
    );
};
export default FolderPage;""")

print("Wrote:", *WROTE, sep="\n  ")
subprocess.run(['git','add','.'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','commit','-m','fix29: restore tabbed FolderPage (print+payments) + null-guards + back-to-top; seed all intake scenarios'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','push'],check=False,cwd=ROOT,capture_output=True)
print("Done. Pushed.")