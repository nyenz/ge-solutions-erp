// PATH: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
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
    FiDollarSign, FiActivity
} from 'react-icons/fi';
import landService from '../../services/landService';
import recoveryService from '../../services/recoveryService';
import predictionService from '../../services/predictionService';
import HardwareModal from '../../components/common/HardwareModal';
import styles from './FolderPage.module.css';

const STAGE_LABELS = ['COMMITMENT', 'FIELD WORK', 'DOCUMENTATION', 'DEED PLAN', 'RELEASE'];
const EMAIL_DOMAINS = ['@gmail.com', '@yahoo.com', '@outlook.com', '@hotmail.com', '@icloud.com'];

const formatSinglePhone = (raw) => {
    const d = raw.replace(/\D/g, '');
    if (!d) return '';
    return [d.slice(0, 4), d.slice(4, 7), d.slice(7, 10)].filter(Boolean).join(' ');
};
const formatPhoneEntry = (raw) =>
    raw.split('/').map(p => formatSinglePhone(p.trim())).filter(Boolean).join(' / ');

const validateBuffer = (buffer) => {
    const errors = [];
    if (!buffer.plotNumber?.trim()) errors.push('PLOT ID IS REQUIRED');
    if (!buffer.district?.trim())   errors.push('DISTRICT IS REQUIRED');
    if (!buffer.tenure?.trim())     errors.push('TENURE IS REQUIRED');
    buffer.owners?.forEach((o, i) => {
        if (!o.fullName?.trim()) errors.push(`OWNER ${i + 1}: LEGAL NAME IS REQUIRED`);
    });
    return errors;
};

const TOAST_ICONS = {
    success: <FiCheckSquare aria-hidden="true" />,
    error:   <FiAlertCircle aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo aria-hidden="true" />,
};

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
    return createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
                    <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
                    <span className={styles.toastMsg}>{t.message}</span>
                    <button className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss">
                        <FiX aria-hidden="true" />
                    </button>
                </div>
            ))}
        </div>,
        document.body
    );
};

const SavingOverlay = ({ visible }) => {
    if (!visible || typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.savingOverlay} role="status" aria-label="Committing to archive">
            <div className={styles.savingSpinner} aria-hidden="true" />
            <span className={styles.savingLabel}>COMMITTING TO ARCHIVE...</span>
        </div>,
        document.body
    );
};

const SkeletonPanel = () => (
    <div className={styles.skeletonPanel} aria-hidden="true">
        <div className={styles.skeletonHeader} />
        <div className={styles.skeletonBody}>
            {[1,2,3,4].map(i => <div key={i} className={styles.skeletonLine} />)}
        </div>
    </div>
);
const SkeletonPage = () => (
    <div className={styles.skeletonPage} aria-busy="true" aria-label="Loading record">
        <div className={styles.skeletonHUD} />
        <div className={styles.skeletonTermHeader} />
        <SkeletonPanel /><SkeletonPanel /><SkeletonPanel />
    </div>
);

const DrawerHeader = ({ label, count, isOpen, onClick, icon: Icon }) => (
    <div className={styles.drawerHeader} onClick={onClick} role="button" tabIndex={0}
        aria-expanded={isOpen} aria-label={`${label} section, ${isOpen ? 'collapse' : 'expand'}`}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}>
        <div className={styles.drawerTitle}>
            {Icon && <Icon className={styles.drawerIcon} aria-hidden="true" />}
            {label}
            {count !== undefined && <span className={styles.drawerCount}>{count}</span>}
        </div>
        <FiChevronDown className={`${styles.chevron} ${isOpen ? styles.rotated : ''}`} aria-hidden="true" />
    </div>
);

const SmartInput = React.forwardRef(({
    label, value, onChange, onBlur, placeholder,
    suggestions = [], inputMode, maxLength, hint,
    showCaps, required = false, error = null, id: propId,
}, ref) => {
    const inputId    = propId || 'inp-' + (label || '').replace(/\W/g, '-').toLowerCase();
    const errorId    = inputId + '_err';
    const hintId     = inputId + '_hint';
    const datalistId = suggestions.length ? 'dl-' + inputId : undefined;
    return (
        <div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>
                    {label}{required && <span className={styles.reqStar} aria-hidden="true"> *</span>}
                </label>
                {showCaps && <span className={styles.capsBadge}>CAPS</span>}
            </div>
            <input id={inputId} ref={ref} type="text"
                className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                value={value} onChange={onChange} onBlur={onBlur}
                placeholder={placeholder} inputMode={inputMode} maxLength={maxLength}
                list={datalistId} autoComplete="off"
                aria-required={required ? 'true' : undefined}
                aria-invalid={error ? 'true' : 'false'}
            />
            {datalistId && <datalist id={datalistId}>{suggestions.map((s,i) => <option key={i} value={s} />)}</datalist>}
            {error && <span id={errorId} className={styles.fieldError} role="alert">{error}</span>}
            {!error && hint && <span id={hintId} className={styles.inputHint}>{hint}</span>}
        </div>
    );
});
SmartInput.displayName = 'SmartInput';

const SmartSelect = ({ label, options, value, onChange, id }) => {
    const [open, setOpen] = useState(false);
    const wrapRef  = useRef(null);
    const selectId = id || 'ss-' + (label || '').replace(/\W/g, '-').toLowerCase();
    useEffect(() => {
        const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);
    const handleKey = (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); }
        if (e.key === 'Escape') setOpen(false);
        if (e.key === 'ArrowDown') { e.preventDefault(); const i = options.indexOf(value); if (i < options.length - 1) onChange(options[i+1]); }
        if (e.key === 'ArrowUp')   { e.preventDefault(); const i = options.indexOf(value); if (i > 0) onChange(options[i-1]); }
    };
    return (
        <div className={styles.hwInputWrap} ref={wrapRef} style={{ position: 'relative' }}>
            <div className={styles.inputLabelRow}><label id={selectId + '_lbl'}>{label}</label></div>
            <div id={selectId} role="combobox" aria-haspopup="listbox" aria-expanded={open}
                aria-labelledby={selectId + '_lbl'} tabIndex={0}
                className={`${styles.selectTrigger} ${open ? styles.selectTriggerOpen : ''}`}
                onClick={() => setOpen(o => !o)} onKeyDown={handleKey}>
                <span className={styles.selectValue}>{value}</span>
                <FiChevronDown className={`${styles.selectChevron} ${open ? styles.rotated : ''}`} aria-hidden="true" />
            </div>
            {open && (
                <ul role="listbox" aria-labelledby={selectId + '_lbl'} className={styles.selectDropdown}>
                    {options.map(opt => (
                        <li key={opt} role="option" aria-selected={opt === value} tabIndex={-1}
                            className={`${styles.selectOption} ${opt === value ? styles.selectOptionActive : ''}`}
                            onClick={() => { onChange(opt); setOpen(false); }}>{opt}</li>
                    ))}
                </ul>
            )}
        </div>
    );
};

const EmailInput = ({ label = 'EMAIL', value, onChange, onCommit, id, required }) => {
    const [showDomains, setShowDomains] = useState(false);
    const [activeIdx,   setActiveIdx]   = useState(-1);
    const wrapRef = useRef(null);
    const inputId = id || 'ei_email';
    const listId  = inputId + '_list';
    const localPart    = value.includes('@') ? value.split('@')[0] : value;
    const hasAt        = value.includes('@');
    const pickerVisible = showDomains && localPart.length > 0 && !hasAt;
    const applyDomain = (domain) => { onCommit(localPart + domain); setShowDomains(false); setActiveIdx(-1); };
    const handleBlur = () => setTimeout(() => {
        setShowDomains(false);
        if (value && !value.includes('@') && value.trim()) onCommit(value.trim() + '@gmail.com');
    }, 160);
    const handleKey = (e) => {
        if (!pickerVisible) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i+1, EMAIL_DOMAINS.length-1)); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i-1, 0)); }
        else if ((e.key === 'Enter' || e.key === 'Tab') && activeIdx >= 0) { e.preventDefault(); applyDomain(EMAIL_DOMAINS[activeIdx]); }
        else if (e.key === 'Escape') setShowDomains(false);
    };
    useEffect(() => {
        const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setShowDomains(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);
    return (
        <div className={styles.hwInputWrap} ref={wrapRef}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={styles.assistBadge}>@</span>
            </div>
            <div className={styles.emailWrap}>
                <input id={inputId} className={styles.hwInput} type="email" value={value}
                    onChange={e => { onChange(e.target.value.toLowerCase().replace(/\s/g,'')); setShowDomains(true); setActiveIdx(-1); }}
                    onBlur={handleBlur} onFocus={() => setShowDomains(true)} onKeyDown={handleKey}
                    placeholder="name@domain.com" autoComplete="off" autoCapitalize="none" inputMode="email" />
                {pickerVisible && (
                    <ul id={listId} role="listbox" className={styles.domainPicker}>
                        {EMAIL_DOMAINS.map((domain, idx) => (
                            <li key={domain} id={listId + '_' + idx} role="option" aria-selected={idx === activeIdx}
                                className={`${styles.domainOption} ${idx === activeIdx ? styles.domainOptionActive : ''}`}
                                onMouseDown={() => applyDomain(domain)}>
                                <span className={styles.emailLocalPart}>{localPart}</span>
                                <span className={styles.emailDomainPart}>{domain}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

const PhoneInput = ({ label = 'RECOVERY PHONE', value, onChange, id, required, fieldError }) => {
    const [raw, setRaw] = useState(() => value || '');
    const inputId = id || 'phi_phone';
    const isDual  = raw.includes('/');
    const handleChange = (e) => {
        let v = e.target.value.replace(/[^0-9\s/]/g, '').replace(/[/]+/g, '/');
        if (v.startsWith('/')) v = v.slice(1);
        setRaw(v); onChange(v);
    };
    const handleBlur = () => {
        if (!raw.trim()) return;
        const f = formatPhoneEntry(raw);
        if (f) { setRaw(f); onChange(f); }
    };
    return (
        <div className={`${styles.hwInputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={`${styles.assistBadge} ${isDual ? styles.assistBadgeDual : ''}`}>{isDual ? 'DUAL' : 'TEL'}</span>
            </div>
            <input id={inputId} type="tel" value={raw} onChange={handleChange} onBlur={handleBlur}
                placeholder="0712 345 678  ·  dual: 0712.../0701..." inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                autoComplete="tel-national" />
            {fieldError && <span className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );
};

const NINInput = ({ label = 'NATIONAL ID / NIN', value, onChange, id }) => {
    const inputId = id || 'nin_input';
    const MAX = 14;
    const handleChange = (e) => onChange(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,MAX));
    return (
        <div className={styles.hwInputWrap}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}</label>
                <span className={styles.capsBadge}>CAPS</span>
            </div>
            <input id={inputId} type="text" value={value} onChange={handleChange}
                maxLength={MAX} placeholder="CM90XXXXXXXX12"
                className={styles.hwInput} autoComplete="off" autoCapitalize="characters" />
        </div>
    );
};

const AddressInput = (props) => <SmartInput {...props} placeholder="Street, Town, District" />;

const CurrencyInput = ({ label, value, onChange, error, id }) => {
    const [focused, setFocused] = useState(false);
    const inputId = id || 'cur-' + (label||'').replace(/\W/g,'-').toLowerCase();
    const display = focused ? String(value||'') : (value ? Number(value).toLocaleString() : '');
    return (
        <div className={`${styles.hwInputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}</label>
                <span className={styles.currencyTag}>UGX</span>
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                inputMode="numeric" value={display}
                onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
                onChange={e => onChange(e.target.value.replace(/\D/g,''))}
                placeholder="0" aria-invalid={error ? 'true' : 'false'} />
            {error && <span className={styles.fieldError} role="alert">{error}</span>}
        </div>
    );
};

const useConfirm = () => {
    const [state, setState] = useState({ open: false, title: '', message: '', variant: 'warn', resolve: null });
    const confirm = useCallback((title, message, variant = 'warn') =>
        new Promise(resolve => setState({ open: true, title, message, variant, resolve })), []);
    const handleAnswer = useCallback((answer) => {
        setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; });
    }, []);
    return { confirmState: state, confirm, handleAnswer };
};

const ConfirmModal = ({ state, onAnswer }) => {
    if (!state.open || typeof document === 'undefined') return null;
    const isDanger = state.variant === 'danger';
    return createPortal(
        <div className={styles.confirmOverlay} role="dialog" aria-modal="true">
            <div className={styles.confirmBox}>
                <div className={`${styles.confirmHeader} ${isDanger ? styles.confirmHeaderDanger : styles.confirmHeaderWarn}`}>
                    {isDanger ? <FiAlertOctagon className={styles.confirmIcon} aria-hidden="true" />
                              : <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" />}
                    <span className={styles.confirmTitle}>{state.title}</span>
                </div>
                <p className={styles.confirmMessage}>{state.message}</p>
                <div className={styles.confirmFooter}>
                    <button type="button" className={styles.confirmCancelBtn} onClick={() => onAnswer(false)} autoFocus>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button type="button" className={`${styles.confirmOkBtn} ${isDanger ? styles.confirmOkDanger : styles.confirmOkWarn}`}
                        onClick={() => onAnswer(true)}>
                        {isDanger ? <><FiTrash2 aria-hidden="true" /> CONFIRM ERASE</>
                                  : <><FiCheckCircle aria-hidden="true" /> CONFIRM</>}
                    </button>
                </div>
            </div>
        </div>,
        document.body
    );
};

const fmt = (n) => Number(n || 0).toLocaleString();

// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════
const FolderPage = () => {
    const { id }   = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;

    const [binder,      setBinder]      = useState(null);
    const [buffer,      setBuffer]      = useState(null);
    const [loading,     setLoading]     = useState(true);
    const [loadError,   setLoadError]   = useState(false);
    const [isEditing,   setIsEditing]   = useState(false);
    const [committing,  setCommitting]  = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [payments,    setPayments]    = useState([]);

    const [drawers, setDrawers] = useState({ tech:true, identity:true, finance:true, vault:true, intel:true, payments:false });
    const toggleDrawer = (key) => setDrawers(p => ({ ...p, [key]: !p[key] }));

    const [noteModal,  setNoteModal]  = useState({ open:false, id:null, content:'' });
    const [payModal,   setPayModal]   = useState({ open:false });
    const [payAmount,  setPayAmount]  = useState('');
    const [payNotes,   setPayNotes]   = useState('');
    const [paying,     setPaying]     = useState(false);

    const { confirmState, confirm, handleAnswer } = useConfirm();
    const firstInputRef = useRef(null);
    const fileInputRef  = useRef(null);

    useEffect(() => { window.scrollTo({ top:0, behavior:'smooth' }); }, [id]);

    useEffect(() => {
        const h = (e) => { if (isEditing) { e.preventDefault(); e.returnValue=''; } };
        window.addEventListener('beforeunload', h);
        return () => window.removeEventListener('beforeunload', h);
    }, [isEditing]);

    useEffect(() => {
        if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120);
    }, [isEditing]);

    const loadFolderData = useCallback(async () => {
        try {
            const data = await landService.getDeepBinder(id);
            if (!data) throw new Error('NULL_SIGNAL');
            setBinder(data);
            setPayments(data.payments || []);
            setLoadError(false);
            if (!isEditing) {
                setBuffer({
                    plotNumber:        data.project?.landTitle?.plotNumber        || '',
                    tenure:            data.project?.landTitle?.tenure            || 'MAILO',
                    blockRoad:         data.project?.landTitle?.blockRoad         || '',
                    district:          data.project?.landTitle?.district          || '',
                    county:            data.project?.landTitle?.county            || '',
                    volume:            data.project?.landTitle?.volume            || '',
                    folio:             data.project?.landTitle?.folio             || '',
                    instrumentNo:      data.project?.landTitle?.instrumentNo      || '',
                    physicalBoxNumber: data.project?.landTitle?.physicalBoxNumber || '',
                    totalCost:         String(data.project?.totalCost             || 0),
                    initialPayment:    String(data.project?.amountPaid            || 0),
                    isLegacy:          data.project?.isLegacy                     || false,
                    owners: (data.project?.proprietors || []).map(p => ({
                        fullName: p.fullName||'', phone: p.phoneNumber||'',
                        nationalId: p.nationalId||'', address: p.homeAddress||'', email: p.email||'',
                    })),
                });
                setFieldErrors({});
            }
        } catch { setLoadError(true); }
        finally  { setLoading(false); }
    }, [id, isEditing]);

    useEffect(() => { loadFolderData(); }, [loadFolderData]);

    const handleCommit = async () => {
        const errors = validateBuffer(buffer);
        if (errors.length) {
            const fe = {};
            if (!buffer.plotNumber?.trim())  fe.plotNumber = 'Required';
            if (!buffer.district?.trim())    fe.district   = 'Required';
            buffer.owners?.forEach((o,i) => { if (!o.fullName?.trim()) fe['owner_'+i+'_name']='Required'; });
            setFieldErrors(fe);
            toast('VALIDATION FAILED: ' + errors[0], 'error', 6000);
            return;
        }
        setFieldErrors({});
        setCommitting(true);
        try {
            await landService.updateMasterFolder(id, {
                ...buffer,
                totalCost:      Number(buffer.totalCost) || 0,
                initialPayment: Number(buffer.initialPayment) || 0,
            });
            predictionService.learn(buffer);
            setIsEditing(false);
            await loadFolderData();
            toast('ARCHIVE REWRITTEN SUCCESSFULLY', 'success');
        } catch (err) { toast('SAVE FAILED: ' + err.message, 'error', 8000); }
        finally { setCommitting(false); }
    };

    const handleUnlock = async () => {
        setIsEditing(true);
        try { await landService.logDossierUnlock(id); } catch { /* non-fatal */ }
    };

    const handleAbort = async () => {
        const ok = await confirm('DISCARD CHANGES', 'All unsaved changes will be lost.', 'warn');
        if (ok) { setIsEditing(false); setFieldErrors({}); loadFolderData(); }
    };

    const handleNuclearPurge = async () => {
        const ok = await confirm('NUCLEAR PURGE',
            'PERMANENTLY erase this entire archive entry including all documents and notes. Cannot be undone.', 'danger');
        if (!ok) return;
        try {
            await landService.purgeAsset(id);
            toast('ASSET PURGED', 'warn', 3000);
            setTimeout(() => navigate('/land/projects'), 1500);
        } catch { toast('PURGE REJECTED', 'error'); }
    };

    const handleStageClick = async (num) => {
        if (!isEditing) return;
        try {
            await landService.setRealityStage(id, num);
            await loadFolderData();
            toast('STAGE SET: ' + STAGE_LABELS[num-1], 'info', 3000);
        } catch { toast('STAGE UPDATE FAILED', 'error'); }
    };

    const handleOwnerChange = (idx, field, val) => {
        const owners = buffer.owners.map((o,i) => {
            if (i !== idx) return o;
            let v = val;
            if (field==='fullName')   v = val.toUpperCase();
            if (field==='nationalId') v = val.toUpperCase().replace(/\s/g,'');
            if (field==='email')      v = val.toLowerCase().replace(/\s/g,'');
            return { ...o, [field]: v };
        });
        setBuffer(p => ({ ...p, owners }));
    };

    const handleEmailCommit = (idx, val) => {
        const owners = buffer.owners.map((o,i) => i===idx ? { ...o, email:val } : o);
        setBuffer(p => ({ ...p, owners }));
    };

    const handleVaultAction = async (files) => {
        if (!files?.length) return;
        setCommitting(true);
        try {
            await landService.addExtraDocuments(id, files);
            await loadFolderData();
            toast(files.length + ' DOCUMENT(S) INGESTED', 'success', 3000);
        } catch { toast('INGESTION FAILED', 'error', 8000); }
        finally { setCommitting(false); }
    };

    const handleDeleteDoc = async (docId, fileName) => {
        const ok = await confirm('DELETE DOCUMENT', `Delete "${fileName}"? Cannot be undone.`, 'danger');
        if (!ok) return;
        try {
            await landService.deleteDocument(docId);
            await loadFolderData();
            toast('DOCUMENT REMOVED', 'warn', 3000);
        } catch { toast('DELETE FAILED', 'error'); }
    };

    const handleNoteSave = async () => {
        if (!noteModal.content.trim()) return;
        try {
            if (noteModal.id) await landService.editStandaloneNote(noteModal.id, noteModal.content);
            else              await landService.addStandaloneNote(id, noteModal.content);
            setNoteModal({ open:false, id:null, content:'' });
            await loadFolderData();
            toast('INTERACTION LOGGED', 'success', 3000);
        } catch { toast('SAVE FAILED', 'error'); }
    };

    const handleDeleteNote = async (noteId) => {
        const ok = await confirm('DELETE NOTE', 'Delete this entry? Cannot be undone.', 'danger');
        if (!ok) return;
        try {
            await landService.deleteStandaloneNote(noteId);
            await loadFolderData();
            toast('NOTE DELETED', 'warn', 3000);
        } catch { toast('DELETE FAILED', 'error'); }
    };

    const handleMoveToBacklog = async () => {
        const ok = await confirm('MOVE TO BACKLOG',
            'This will freeze the current balance as original debt and start monthly storage fees of UGX 50,000. Continue?', 'warn');
        if (!ok) return;
        try {
            await recoveryService.moveToBacklog(id);
            await loadFolderData();
            toast('PLOT MOVED TO BACKLOG — STORAGE FEES NOW ACTIVE', 'warn');
        } catch (err) { toast('BACKLOG FAILED: ' + (err.response?.data?.message || err.message), 'error'); }
    };

    const handleExitBacklog = async () => {
        const ok = await confirm('EXIT BACKLOG',
            'This will clear backlog status and storage fees. The original debt amount stays. Continue?', 'warn');
        if (!ok) return;
        try {
            await recoveryService.exitBacklog(id);
            await loadFolderData();
            toast('PLOT REMOVED FROM BACKLOG', 'success');
        } catch (err) { toast('EXIT FAILED: ' + (err.response?.data?.message || err.message), 'error'); }
    };

    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        setPaying(true);
        try {
            await recoveryService.recordPayment(id, payAmount, payNotes);
            await loadFolderData();
            setPayModal({ open: false });
            setPayAmount(''); setPayNotes('');
            toast('PAYMENT RECORDED', 'success');
        } catch { toast('PAYMENT FAILED', 'error', 8000); }
        finally { setPaying(false); }
    };

    const getVaultUrl = (filePath) => {
        if (!filePath) return '#';
        if (filePath.startsWith('http')) return filePath;
        const parts = filePath.split(/ge_uploads[\\/]/);
        const rel   = parts.length > 1 ? parts[1] : filePath;
        const base  = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';
        return `${base}/vault/` + rel.replace(/\\/g, '/');
    };

    const sg = useMemo(() => (key) => predictionService.getSuggestions(key) || [], []);

    if (loading) return <div className={styles.container}><SkeletonPage /></div>;

    if (loadError || !binder || !buffer) return (
        <div className={styles.errorScreen}>
            <FiAlertTriangle className={styles.errorIcon} aria-hidden="true" />
            <h2>VAULT ACCESS DENIED</h2>
            <p>Could not load record. The archive may be unavailable.</p>
            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={loadFolderData}>RETRY</button>
        </div>
    );

    const project      = binder.project;
    const isBacklog    = project?.isBacklog || false;
    const docCount     = (binder.documents||[]).length;
    const noteCount    = (binder.notes||[]).length;
    const paymentCount = payments.length;

    // Financial figures
    const totalCost    = Number(project?.totalCost || 0);
    const amountPaid   = Number(project?.amountPaid || 0);
    const origDebt     = Number(project?.originalDebt || 0);
    const storageFees  = Number(project?.storageFeesAccumulated || 0);
    const backlogOwed  = origDebt + storageFees - amountPaid;
    const activeOwed   = totalCost - amountPaid;
    const remaining    = isBacklog ? Math.max(0, backlogOwed) : Math.max(0, activeOwed);
    const arrearsEdit  = (Number(buffer?.totalCost)||0) - (Number(buffer?.initialPayment)||0);

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing || paying} />

            {/* BACKLOG BANNER */}
            {isBacklog && (
                <div style={{
                    background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)',
                    borderRadius: 8, padding: '12px 20px', marginBottom: 16,
                    display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap'
                }}>
                    <FiAlertOctagon style={{ color: '#ef4444', flexShrink: 0 }} size={20} />
                    <div style={{ flex: 1 }}>
                        <strong style={{ color: '#ef4444' }}>BACKLOG STATUS — STORAGE FEES ACTIVE</strong>
                        <div style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: 2 }}>
                            UGX 50,000 is added to this plot every month until the full balance is cleared.
                        </div>
                    </div>
                    {isAdmin && (
                        <button onClick={handleExitBacklog}
                            style={{ background: 'rgba(239,68,68,0.2)', border: '1px solid #ef4444',
                                color: '#ef4444', borderRadius: 6, padding: '6px 14px',
                                cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700 }}>
                            EXIT BACKLOG
                        </button>
                    )}
                </div>
            )}

            {/* PIPELINE HUD */}
            <nav className={styles.pipelineHUD} aria-label="Project pipeline">
                <div className={styles.track}>
                    {STAGE_LABELS.map((label, idx) => {
                        const num    = idx + 1;
                        const active = project.currentStageIndex >= num;
                        return (
                            <div key={num} className={styles.stageModule}>
                                <div className={`${styles.dot} ${active ? styles.dotActive : ''} ${isEditing ? styles.dotInteractive : ''}`}
                                    onClick={() => handleStageClick(num)}
                                    role={isEditing ? 'button' : 'img'} tabIndex={isEditing ? 0 : -1}
                                    aria-label={`Stage ${num}: ${label}${active ? ' (complete)' : ''}`}
                                    onKeyDown={e => { if (isEditing && (e.key==='Enter'||e.key===' ')) { e.preventDefault(); handleStageClick(num); }}}>
                                    {active ? <FiCheckCircle aria-hidden="true" /> : num}
                                </div>
                                <span className={styles.stageLabel}>{label}</span>
                            </div>
                        );
                    })}
                </div>
                <div className={styles.protocolReadout}>
                    <strong>PROTOCOL: {project.status}</strong>
                    <span>REAL-TIME TRACKING ACTIVE</span>
                </div>
            </nav>

            {/* TERMINAL HEADER */}
            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle.plotNumber}</h1>
                    <div className={styles.metaLine}>
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>
                        {isBacklog
                            ? <span className={`${styles.metaTag}`} style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444' }}>BACKLOG</span>
                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>
                        }
                        {isEditing && <div className={styles.editBadge}>EDIT MODE ENABLED</div>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {!isEditing && <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record"><FiPrinter aria-hidden="true" /></button>}
                    {isAdmin && !isEditing && !isBacklog && (
                        <button onClick={handleMoveToBacklog}
                            style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)',
                                color: '#ef4444', borderRadius: 6, padding: '6px 14px',
                                cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700, display:'flex', alignItems:'center', gap:6 }}>
                            <FiAlertOctagon aria-hidden="true" /> MOVE TO BACKLOG
                        </button>
                    )}
                    {isAdmin && !isEditing && (
                        <button onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}
                            style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.4)',
                                color: '#22c55e', borderRadius: 6, padding: '6px 14px',
                                cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700, display:'flex', alignItems:'center', gap:6 }}>
                            <FiDollarSign aria-hidden="true" /> RECORD PAYMENT
                        </button>
                    )}
                    {isEditing && user?.isRoot && (
                        <button className={styles.purgeBtn} onClick={handleNuclearPurge}>
                            <FiTrash2 aria-hidden="true" /> PURGE
                        </button>
                    )}
                    {!isEditing ? (
                        <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                            <FiUnlock aria-hidden="true" /> UNLOCK MASTER HARDWARE
                        </button>
                    ) : (
                        <div className={styles.handshakeActions}>
                            <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}>
                                <FiX aria-hidden="true" /> ABORT
                            </button>
                            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}>
                                <FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE CHANGES'}
                            </button>
                        </div>
                    )}
                </div>
            </header>

            <main className={styles.workstationBody}>

                {/* PLOT DETAILS */}
                <section className={styles.hwPanel} aria-label="Plot Details">
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.tech} onClick={() => toggleDrawer('tech')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.tech ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.tech}>
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => setBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                        <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => setBuffer({...buffer, tenure: v})} />
                                        <SmartInput label="BOX LOCATION" value={buffer.physicalBoxNumber} showCaps onChange={e => setBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => setBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                        <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => setBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                        <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => setBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="INSTRUMENT NO." value={buffer.instrumentNo} showCaps onChange={e => setBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />
                                        <SmartInput label="VOLUME" value={buffer.volume} inputMode="numeric" hint="Numbers only" onChange={e => setBuffer({...buffer, volume: e.target.value.replace(/\D/g,'')})} />
                                        <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => setBuffer({...buffer, folio: e.target.value.replace(/\D/g,'')})} />
                                    </div>
                                </>
                            ) : (
                                <div className={styles.readOnlyGrid}>
                                    {[['PLOT ID',project.landTitle.plotNumber],['TENURE',project.landTitle.tenure],['BOX',project.landTitle.physicalBoxNumber],
                                      ['DISTRICT',project.landTitle.district],['COUNTY',project.landTitle.county],['BLOCK / ROAD',project.landTitle.blockRoad],
                                      ['VOLUME',project.landTitle.volume],['FOLIO',project.landTitle.folio],['INSTRUMENT',project.landTitle.instrumentNo]
                                    ].map(([l,v],i) => (
                                        <div key={i} className={styles.specItem}>
                                            <span className={styles.specLabel}>{l}</span>
                                            <span className={styles.specValue}>{v || '---'}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                {/* OWNERS */}
                <section className={styles.hwPanel} aria-label="Owners">
                    <DrawerHeader label="OWNERS" count={project.proprietors.length} isOpen={drawers.identity} onClick={() => toggleDrawer('identity')} icon={FiUsers} />
                    <div className={`${styles.panelBody} ${drawers.identity ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.identity}>
                        <div className={styles.panelInner}>
                            <div className={styles.ownersScroll}>
                                <div className={styles.ownersGrid2} role="list">
                                    {isEditing ? buffer.owners.map((o, idx) => (
                                        <div key={idx} className={styles.ownerEditCard} role="listitem">
                                            <div className={styles.ownerCardLabel}>ENTITY #{idx+1} {idx===0&&'(PRIMARY)'}</div>
                                            <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                            <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} id={`owner_${idx}_phone`} />
                                            <NINInput value={o.nationalId} onChange={v => handleOwnerChange(idx,'nationalId',v)} id={`owner_${idx}_nin`} />
                                            <EmailInput value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} onCommit={val => handleEmailCommit(idx,val)} id={`owner_${idx}_email`} />
                                            <AddressInput label="HOME ADDRESS" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />
                                        </div>
                                    )) : project.proprietors.map((p, i) => (
                                        <div key={i} className={styles.ownerStaticCard} role="listitem">
                                            <h2 className={styles.ownerName}>{p.fullName}</h2>
                                            <div className={styles.infoColumns}>
                                                <div className={styles.infoRow}><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMail   aria-hidden="true" /><span>{p.email||'---'}</span></div>
                                                <div className={styles.infoRow}><FiShield aria-hidden="true" /><span>{p.nationalId||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMapPin aria-hidden="true" /><span>{p.homeAddress||'---'}</span></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* FINANCIALS */}
                <section className={styles.hwPanel} aria-label="Financials">
                    <DrawerHeader label="FINANCIALS" isOpen={drawers.finance} onClick={() => toggleDrawer('finance')} icon={FiCreditCard} />
                    <div className={`${styles.panelBody} ${drawers.finance ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.finance}>
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <div className={styles.inputGrid3}>
                                    <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => setBuffer({...buffer, totalCost:v})} />
                                    <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => setBuffer({...buffer, initialPayment:v})} />
                                    <div className={styles.hwInputWrap}>
                                        <div className={styles.inputLabelRow}><label>ARREARS</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                        <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                    </div>
                                </div>
                            ) : isBacklog ? (
                                /* BACKLOG FINANCIAL BREAKDOWN */
                                <div>
                                    <div className={styles.moneyStatsRow}>
                                        <div className={styles.statBox}>
                                            <label>ORIGINAL DEBT</label>
                                            <strong>UGX {fmt(origDebt)}</strong>
                                        </div>
                                        <div className={styles.statBox}>
                                            <label style={{color:'#ef4444'}}>STORAGE FEES ADDED</label>
                                            <strong className={styles.redGlow}>UGX {fmt(storageFees)}</strong>
                                            <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                {project.backlogStartDate
                                                    ? `Since ${new Date(project.backlogStartDate).toLocaleDateString()}`
                                                    : ''}
                                            </small>
                                        </div>
                                        <div className={styles.statBox}>
                                            <label>TOTAL PAID (ALL)</label>
                                            <strong>UGX {fmt(amountPaid)}</strong>
                                        </div>
                                    </div>
                                    <div style={{ borderTop: '1px solid rgba(239,68,68,0.3)', marginTop: 12, paddingTop: 12 }}>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox} style={{ gridColumn: '1/-1' }}>
                                                <label style={{color:'#ef4444'}}>TOTAL NOW OWED</label>
                                                <strong className={styles.redGlow} style={{fontSize:'1.4rem'}}>
                                                    UGX {fmt(Math.max(0, backlogOwed))}
                                                </strong>
                                                <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                    = Original debt + storage fees − payments made
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                /* ACTIVE FINANCIAL */
                                <>
                                    <div className={styles.moneyStatsRow}>
                                        <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalCost)}</strong></div>
                                        <div className={styles.statBox}><label>COLLECTED</label><strong>UGX {fmt(amountPaid)}</strong></div>
                                        <div className={styles.statBox}><label>ARREARS</label><strong className={styles.redGlow}>UGX {fmt(remaining)}</strong></div>
                                    </div>
                                    <div className={styles.velocityNote}>
                                        <FiClock aria-hidden="true" />
                                        <span>COLLECTION PERFORMANCE: <strong>{(binder.collectionPercentage||0).toFixed(1)}%</strong></span>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </section>

                {/* PAYMENT HISTORY */}
                <section className={styles.hwPanel} aria-label="Payment History">
                    <DrawerHeader label="PAYMENT HISTORY" count={paymentCount} isOpen={drawers.payments} onClick={() => toggleDrawer('payments')} icon={FiActivity} />
                    <div className={`${styles.panelBody} ${drawers.payments ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.payments}>
                        <div className={styles.panelInner}>
                            {paymentCount === 0 ? (
                                <div className={styles.emptyState} role="status">
                                    <FiDollarSign className={styles.emptyIcon} aria-hidden="true" />
                                    <span>NO PAYMENTS RECORDED</span>
                                </div>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                    {payments.map((pay, i) => (
                                        <div key={pay.id || i} style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '10px 14px', background: 'rgba(255,255,255,0.04)',
                                            borderRadius: 6, borderLeft: `3px solid ${pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : '#22c55e'}`
                                        }}>
                                            <div>
                                                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                                                    UGX {fmt(pay.amountPaid)}
                                                </div>
                                                <div style={{ fontSize: '0.72rem', opacity: 0.6 }}>
                                                    {pay.paymentType} · by {pay.recordedBy}
                                                    {pay.notes ? ` · ${pay.notes}` : ''}
                                                </div>
                                            </div>
                                            <div style={{ textAlign: 'right' }}>
                                                <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                                                    {new Date(pay.timestamp).toLocaleDateString()}
                                                </div>
                                                {pay.balanceAfter != null && (
                                                    <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                                        Balance after: UGX {fmt(pay.balanceAfter)}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                {/* DOCUMENTS + NOTES */}
                <div className={styles.intelDoubleRow}>
                    <section className={styles.hwPanel} aria-label="Documents">
                        <DrawerHeader label="DOCUMENTS" count={docCount} isOpen={drawers.vault} onClick={() => toggleDrawer('vault')} icon={FiUploadCloud} />
                        <div className={`${styles.panelBody} ${drawers.vault ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.vault}>
                            <div className={styles.panelInner}>
                                <div className={styles.compactVault} role="list">
                                    {docCount === 0 && (
                                        <div className={styles.emptyState} role="status">
                                            <FiFileText className={styles.emptyIcon} aria-hidden="true" />
                                            <span>NO DOCUMENTS ATTACHED</span>
                                        </div>
                                    )}
                                    {binder.documents.map((doc, idx) => (
                                        <div key={idx} className={styles.docTag} role="listitem">
                                            <FiFileText className={styles.docIcon} aria-hidden="true" />
                                            <a href={getVaultUrl(doc.filePath)} target="_blank" rel="noreferrer"
                                                className={styles.docName}>
                                                {doc.fileName}
                                            </a>
                                            {isEditing && (
                                                <button type="button" className={styles.iconBtn}
                                                    onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>
                                                    <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                                {isEditing && (
                                    <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>
                                        + INGEST NEW SCANS
                                    </button>
                                )}
                            </div>
                        </div>
                    </section>

                    <section className={styles.hwPanel} aria-label="Notes">
                        <DrawerHeader label="NOTES" count={noteCount} isOpen={drawers.intel} onClick={() => toggleDrawer('intel')} icon={FiInfo} />
                        <div className={`${styles.panelBody} ${drawers.intel ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.intel}>
                            <div className={styles.panelInner}>
                                <div className={styles.notebookTimeline} role="list">
                                    {noteCount === 0 && (
                                        <div className={styles.emptyState} role="status">
                                            <FiInfo className={styles.emptyIcon} aria-hidden="true" />
                                            <span>NO NOTES LOGGED</span>
                                        </div>
                                    )}
                                    {binder.notes.map((log, i) => (
                                        <article key={i} className={styles.ruledNote} role="listitem">
                                            <div className={styles.noteMeta}>
                                                <time className={styles.noteTime} dateTime={log.timestamp}>
                                                    {new Date(log.timestamp).toLocaleDateString()}
                                                </time>
                                                {isEditing && (
                                                    <div className={styles.actionBlock}>
                                                        <button type="button" className={styles.iconBtn}
                                                            onClick={() => setNoteModal({open:true,id:log.id,content:log.notes})}>
                                                            <FiEdit3 className={styles.editIcon} aria-hidden="true" />
                                                        </button>
                                                        <button type="button" className={styles.iconBtn}
                                                            onClick={() => handleDeleteNote(log.id)}>
                                                            <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                            <p className={styles.noteContent}>{log.notes}</p>
                                        </article>
                                    ))}
                                </div>
                                {isEditing && (
                                    <button type="button" className={styles.addNoteBtn}
                                        onClick={() => setNoteModal({open:true,id:null,content:''})}>
                                        + LOG INTERACTION
                                    </button>
                                )}
                            </div>
                        </div>
                    </section>
                </div>
            </main>

            <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp"
                style={{ display:'none' }} aria-hidden="true" tabIndex={-1}
                onChange={e => { if (!e.target.files?.length) return; handleVaultAction(Array.from(e.target.files)); e.target.value=''; }} />

            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />

            {/* NOTE MODAL */}
            <HardwareModal isOpen={noteModal.open} onClose={() => setNoteModal({...noteModal,open:false})} title="ARCHIVE LOG ENTRY">
                <textarea className={styles.notebookArea} value={noteModal.content}
                    onChange={e => setNoteModal({...noteModal,content:e.target.value})}
                    placeholder="Enter interaction note..." aria-label="Note content" />
                <div className={styles.modalFooter}>
                    <button type="button" className={`${styles.btn} ${styles.btnDanger}`}
                        onClick={() => setNoteModal({open:false,id:null,content:''})}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleNoteSave}>
                        <FiSave aria-hidden="true" /> SAVE ENTRY
                    </button>
                </div>
            </HardwareModal>

            {/* PAYMENT MODAL */}
            <HardwareModal isOpen={payModal.open} onClose={() => setPayModal({ open: false })} title={`RECORD PAYMENT — ${project.landTitle.plotNumber}`}>
                <div style={{ padding: '0 4px' }}>
                    {isBacklog ? (
                        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                            borderRadius: 8, padding: 14, marginBottom: 16, display:'flex', gap: 12 }}>
                            <FiAlertOctagon style={{ color: '#ef4444', flexShrink:0, marginTop:2 }} />
                            <div style={{ fontSize: '0.85rem' }}>
                                <div>Original debt: <strong>UGX {fmt(origDebt)}</strong></div>
                                <div>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(storageFees)}</strong></div>
                                <div>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(Math.max(0,backlogOwed))}</strong></div>
                                <div style={{marginTop:6,opacity:0.6,fontSize:'0.75rem'}}>
                                    Storage fees continue until full balance is cleared.
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div style={{ marginBottom: 16, fontSize: '0.85rem' }}>
                            Current balance: <strong>UGX {fmt(remaining)}</strong>
                        </div>
                    )}
                    <div style={{ marginBottom: 12 }}>
                        <label style={{ display:'block', marginBottom:6, fontSize:'0.8rem', opacity:0.7 }}>AMOUNT RECEIVED (UGX)</label>
                        <input type="number" style={{ width:'100%', padding:'10px 14px', borderRadius:6,
                            background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.15)',
                            color:'inherit', fontSize:'1.1rem' }}
                            placeholder="Enter amount..." value={payAmount}
                            onChange={e => setPayAmount(e.target.value)} />
                    </div>
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display:'block', marginBottom:6, fontSize:'0.8rem', opacity:0.7 }}>NOTES (optional)</label>
                        <textarea style={{ width:'100%', padding:'10px 14px', borderRadius:6, height:80,
                            background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.15)',
                            color:'inherit', resize:'vertical' }}
                            placeholder="e.g. Paid via MTN Mobile Money..."
                            value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                    </div>
                    <div className={styles.modalFooter}>
                        <button type="button" className={`${styles.btn} ${styles.btnPrimary}`}
                            onClick={handleRecordPayment} disabled={paying}>
                            <FiDollarSign aria-hidden="true" /> {paying ? 'PROCESSING...' : 'CONFIRM PAYMENT'}
                        </button>
                    </div>
                </div>
            </HardwareModal>
        </div>
    );
};

export default FolderPage;