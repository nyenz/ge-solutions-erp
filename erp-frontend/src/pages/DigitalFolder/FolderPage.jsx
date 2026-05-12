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
    FiDollarSign, FiActivity, FiHome, FiArchive
} from 'react-icons/fi';
import landService from '../../services/landService';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import recoveryService from '../../services/recoveryService';
import predictionService from '../../services/predictionService';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import ErrorMessage from '../../components/common/ErrorMessage';
import styles from './FolderPage.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

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

const PhoneInput = ({ label = 'RECOVERY PHONE', value, onChange, onBlur, id, required, fieldError }) => {
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
        if (onBlur) onBlur(raw);
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
// BACKLOG FEE ADMIN CONTROLS
// ═══════════════════════════════════════════════════════════════
const BacklogFeeControls = ({ project, projectId, onRefresh, toast }) => {
    const [feeInput,    setFeeInput]    = React.useState('');
    const [rateInput,   setRateInput]   = React.useState('');
    const [saving,      setSaving]      = React.useState(false);

    const handlePause = async () => {
        try {
            await recoveryService.pauseStorageFees(projectId, !project.storagePaused);
            await onRefresh();
            toast(project.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED', 'info');
        } catch { toast('ACTION FAILED', 'error'); }
    };

    const handleSetRate = async () => {
        const val = Number(rateInput);
        if (!rateInput || val < 0) { toast('ENTER A VALID RATE (0 or more)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setStorageRate(projectId, val);
            setRateInput('');
            await onRefresh();
            toast('MONTHLY RATE UPDATED', 'success');
        } catch { toast('RATE UPDATE FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const handleSetFees = async () => {
        const val = Number(feeInput);
        if (feeInput === '' || val < 0) { toast('ENTER A VALID AMOUNT (0 to waive all)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setAccumulatedFees(projectId, val);
            setFeeInput('');
            await onRefresh();
            toast('ACCUMULATED FEES ADJUSTED', 'success');
        } catch { toast('FEE ADJUSTMENT FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const boxStyle = { background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 8, padding: '12px 14px', marginTop: 12 };
    const labelStyle = { display: 'block', fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 };
    const inputStyle = { background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6, color: '#1a2e30', fontFamily: 'Space Mono,monospace', fontWeight: 700, fontSize: 13, padding: '6px 10px', outline: 'none', width: '100%', boxSizing: 'border-box' };
    const btnStyle = (color) => ({ background: color + '22', border: '1.5px solid ' + color, color: color, borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 10, fontWeight: 900, fontFamily: 'DM Sans,sans-serif', textTransform: 'uppercase', letterSpacing: 1, marginTop: 6 });

    return (
        <div style={boxStyle}>
            <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#ef4444', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 10 }}>
                ADMIN: STORAGE FEE CONTROLS
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div>
                    <span style={labelStyle}>PAUSE / RESUME FEES</span>
                    <button onClick={handlePause} style={btnStyle(project.storagePaused ? '#22c55e' : '#f59e0b')}>
                        {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                    </button>
                    {project.storagePaused && <div style={{ fontSize: 9, color: '#f59e0b', marginTop: 4, fontWeight: 700 }}>Fees currently PAUSED</div>}
                </div>
                <div>
                    <span style={labelStyle}>SET MONTHLY RATE (UGX)</span>
                    <input style={inputStyle} type="number" value={rateInput} placeholder={project.storageFeeOverride ? String(project.storageFeeOverride) : '50000'} onChange={e => setRateInput(e.target.value)} />
                    <button onClick={handleSetRate} style={btnStyle('#EE8C3A')} disabled={saving}>APPLY RATE</button>
                </div>
                <div>
                    <span style={labelStyle}>ADJUST TOTAL FEES (UGX)</span>
                    <input style={inputStyle} type="number" value={feeInput} placeholder={String(project.storageFeesAccumulated || 0)} onChange={e => setFeeInput(e.target.value)} />
                    <button onClick={handleSetFees} style={btnStyle('#ef4444')} disabled={saving}>SET TOTAL</button>
                    <div style={{ fontSize: 8, color: 'rgba(255,255,255,0.4)', marginTop: 3, fontWeight: 700 }}>Enter 0 to waive all fees</div>
                </div>
            </div>
        </div>
    );
};

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

    const [activeTab, setActiveTab] = useState(() => {
    const h = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : '';
    return (h.includes('finance') || h.includes('payment')) ? 'FINANCIALS' : 'OVERVIEW';
});
    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS'];

    const [noteModal,  setNoteModal]  = useState({ open:false, id:null, content:'' });
    const [payModal,   setPayModal]   = useState({ open:false });
    const [payAmount,  setPayAmount]  = useState('');
    const [payNotes,   setPayNotes]   = useState('');
    const [payType,    setPayType]    = useState('TITLE');
    const [paying,     setPaying]     = useState(false);

    const { confirmState, confirm, handleAnswer } = useConfirm();

    const firstInputRef = useRef(null);
    const fileInputRef  = useRef(null);
    // Track whether any field was actually changed since edit mode opened
    // MUST be declared before useRouterBlock to avoid TDZ crash in minified build
    const touchedRef    = useRef(false);
    // Wrap setBuffer so any change marks the form as touched
    const touchedSetBuffer = React.useCallback((updater) => {
        touchedRef.current = true;
        setBuffer(updater);
    }, []);

    // Unsaved changes guard -- active only while in edit mode and not mid-save
    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =
        useRouterBlock(!committing && isEditing);

    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-')) {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    const el = document.getElementById('paymentHistorySection');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                }
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {
            setActiveTab('OWNERS');
        } else if (hash === 'vault' || hash === 'documents') {
            setActiveTab('DOCUMENTS');
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id]);



    useEffect(() => {
        if (isEditing) setTimeout(() => firstInputRef.current?.focus(), 120);
    }, [isEditing]);

    // beforeunload -- catches tab close, hard refresh, browser back to external site
    useEffect(() => {
        if (!isEditing || committing) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);

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
            touchedRef.current = false;
            setIsEditing(false);
            await loadFolderData();
            toast('ARCHIVE REWRITTEN SUCCESSFULLY', 'success');
        } catch (err) { toast('SAVE FAILED: ' + err.message, 'error', 8000); }
        finally { setCommitting(false); }
    };

    const handleUnlock = async () => {
        touchedRef.current = false; // reset touch tracking
        setIsEditing(true);
        try { await landService.logDossierUnlock(id); } catch { /* non-fatal */ }
    };

    const handleAbort = async () => {
        const ok = await confirm('DISCARD CHANGES', 'All unsaved changes will be lost.', 'warn');
        if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); }
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

    const handlePhoneBlurCheck = (idx, val) => {
        if (!val.trim()) return;
        const normalized = val.replace(/\s+/g, '');
        const duplicate = (buffer.owners || []).some((o, i) =>
            i !== idx && o.phone.replace(/\s+/g, '') === normalized
        );
        if (duplicate) {
            toast('WARNING: This phone number is already used by another owner on this plot.', 'warn', 5000);
        }
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
        touchedRef.current = true;
        setBuffer(p => ({ ...p, owners }));
    };

    const handleEmailCommit = (idx, val) => {
        const owners = buffer.owners.map((o,i) => i===idx ? { ...o, email:val } : o);
        touchedRef.current = true;
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
            const fullNotes = payType === 'STORAGE'
                ? `[STORAGE FEE PAYMENT] ${payNotes}`.trim()
                : payNotes;
            await recoveryService.recordPayment(id, payAmount, fullNotes);
            await loadFolderData();
            setPayModal({ open: false });
            setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            toast('PAYMENT RECORDED', 'success');
        } catch { toast('PAYMENT FAILED', 'error', 8000); }
        finally { setPaying(false); }
    };

    const getDocUrl = (filePath) => {
        if (!filePath) return '#';
        if (filePath.startsWith('http')) return filePath;
        const parts = filePath.split(/ge_uploads[/]/);
        const rel   = parts.length > 1 ? parts[1] : filePath;
        const base  = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';
        return `${base}/vault/` + rel.replace(/\\/g, '/');
    };

    const handleOpenDoc = (filePath) => {
        if (!filePath) return;
        const url = getDocUrl(filePath);
        if (filePath.startsWith('http')) {
            window.open(url, '_blank', 'noopener,noreferrer');
        } else {
            fetch(url, { headers: { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } })
                .then(r => r.blob())
                .then(blob => {
                    const blobUrl = URL.createObjectURL(blob);
                    window.open(blobUrl, '_blank', 'noopener,noreferrer');
                    setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
                })
                .catch(() => window.open(url, '_blank', 'noopener,noreferrer'));
        }
    };

    const isPDF = (filePath) => {
        if (!filePath) return false;
        const lower = filePath.toLowerCase();
        return lower.includes('.pdf') || lower.includes('application/pdf') ||
               (lower.includes('cloudinary') && lower.includes('/raw/'));
    };

    const sg = useMemo(() => (key) => predictionService.getSuggestions(key) || [], []);

    if (loading) return <div className={styles.container}><SkeletonPage /></div>;

    if (loadError || !binder || !buffer) return (
        <div style={{ padding: 'clamp(40px,8vw,80px) clamp(20px,4vw,40px)' }}>
            <ErrorMessage
                type="error"
                title="Record not found"
                message="This archive entry could not be loaded. It may have been deleted or the server is temporarily unavailable."
                onRetry={loadFolderData}
                retryLabel="Try Again"
            />
        </div>
    );

    const project      = binder.project;
    const isBacklog    = project?.isBacklog || false;
    const docCount     = (binder.documents||[]).length;
    const noteCount    = (binder.notes||[]).length;
    const paymentCount = payments.length;

    // Financial figures
    const totalCost          = Number(project?.totalCost || 0);
    const amountPaid         = Number(project?.amountPaid || 0);
    const origDebt           = Number(project?.originalDebt || 0);
    const storageFees        = Number(project?.storageFeesAccumulated || 0);
    const backlogOwed        = origDebt + storageFees - amountPaid;
    const activeOwed         = totalCost - amountPaid;
    const remaining          = isBacklog ? Math.max(0, backlogOwed) : Math.max(0, activeOwed);
    const arrearsEdit        = (Number(buffer?.totalCost)||0) - (Number(buffer?.initialPayment)||0);
    // Dynamic monthly fee — uses override if set, otherwise system default 50,000
    const effectiveMonthlyFee = Number(project?.storageFeeOverride) > 0
        ? Number(project.storageFeeOverride)
        : 50000;

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing || paying} />

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
                            ? <span className={styles.metaTag} style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', borderColor: 'rgba(239,68,68,0.4)' }}>BACKLOG</span>
                            : project.landTitle?.isReleased
                            ? <span className={styles.metaTag} style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', borderColor: 'rgba(16,185,129,0.4)' }}>RELEASED</span>
                            : amountPaid >= totalCost
                            ? <span className={styles.metaTag} style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', borderColor: 'rgba(16,185,129,0.4)' }}>FULLY PAID</span>
                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>
                        }
                        {isEditing && <div className={styles.editBadge}>EDIT MODE ENABLED</div>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {/* VIEW MODE ACTIONS */}
                    {!isEditing && (
                        <div className={styles.ctrlGroup}>
                            <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record">
                                <FiPrinter aria-hidden="true" />
                            </button>
                            {isAdmin && (
                                <button className={styles.ctrlBtnPay}
                                    onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>
                                    <FiDollarSign aria-hidden="true" /> PAYMENT
                                </button>
                            )}
                            {isAdmin && !isBacklog && (
                                <button className={styles.ctrlBtnBacklog} onClick={handleMoveToBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG
                                </button>
                            )}
                            {isAdmin && isBacklog && (
                                <button className={styles.ctrlBtnBacklog} onClick={handleExitBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> EXIT BACKLOG
                                </button>
                            )}
                            <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                                <FiUnlock aria-hidden="true" /> EDIT
                            </button>
                        </div>
                    )}
                    {/* EDIT MODE ACTIONS */}
                    {isEditing && (
                        <div className={styles.ctrlGroup}>
                            {user?.isRoot && (
                                <button className={styles.purgeBtn} onClick={handleNuclearPurge} title="Permanently delete this record">
                                    <FiTrash2 aria-hidden="true" /> DELETE
                                </button>
                            )}
                            <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}>
                                <FiX aria-hidden="true" /> ABORT
                            </button>
                            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}>
                                <FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}
                            </button>
                        </div>
                    )}
                </div>
            </header>

            {/* TAB BAR */}
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                {TABS.map(tab => (
                    <button
                        key={tab}
                        role="tab"
                        aria-selected={activeTab === tab}
                        className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`}
                        onClick={() => setActiveTab(tab)}
                        title={tab}
                    >
                        <span className={styles.tabFull}>{tab}</span>
                        <span className={styles.tabShort}>{tab.substring(0, 2)}</span>
                    </button>
                ))}
            </div>

            <main className={styles.workstationBody} role="tabpanel">

                {/* ════════════════════════════════════════════════════
                    OVERVIEW TAB — Plot technical details
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'OVERVIEW' && (
                    <section className={styles.hwPanel} aria-label="Plot Details">
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                        <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />
                                        <SmartInput label="BOX LOCATION" value={buffer.physicalBoxNumber} showCaps onChange={e => touchedSetBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                        <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                        <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="INSTRUMENT NO." value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />
                                        <SmartInput label="VOLUME" value={buffer.volume} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\D/g,'')})} />
                                        <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\D/g,'')})} />
                                    </div>
                                </>
                            ) : (
                                <div className={styles.readOnlyGrid}>
                                    {[
                                        ['PLOT ID',      project.landTitle.plotNumber],
                                        ['TENURE',       project.landTitle.tenure],
                                        ['BOX',          project.landTitle.physicalBoxNumber],
                                        ['DISTRICT',     project.landTitle.district],
                                        ['COUNTY',       project.landTitle.county],
                                        ['BLOCK / ROAD', project.landTitle.blockRoad],
                                        ['VOLUME',       project.landTitle.volume],
                                        ['FOLIO',        project.landTitle.folio],
                                        ['INSTRUMENT',   project.landTitle.instrumentNo],
                                    ].map(([l,v],i) => (
                                        <div key={i} className={styles.specItem}>
                                            <span className={styles.specLabel}>{l}</span>
                                            <span className={styles.specValue}>{v || '---'}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </section>
                )}

                {/* ════════════════════════════════════════════════════
                    FINANCIALS TAB — Central hub:
                    1. Balance Summary
                    2. Record Payment (admin)
                    3. Backlog Controls (admin, if backlog)
                    4. Payment History
                    5. Notes & Call Log
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'FINANCIALS' && (
                    <div className={styles.financialsStack}>

                        {/* ── 1. BALANCE SUMMARY ── */}
                        <section className={styles.hwPanel} aria-label="Balance Summary">
                            <div className={styles.finPanelHeader}>
                                <FiCreditCard aria-hidden="true" />
                                BALANCE SUMMARY
                            </div>
                            <div className={styles.panelInner}>
                                {isEditing ? (
                                    <>
                                        <div className={styles.inputGrid3}>
                                            <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />
                                            <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}><label>ARREARS</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                                <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                            </div>
                                        </div>
                                    </>
                                ) : isBacklog ? (
                                    <>
                                        <div className={styles.backlogNotice}>
                                            <FiAlertOctagon className={styles.backlogNoticeIcon} size={14} />
                                            <div className={styles.backlogNoticeText}>
                                                <strong>STORAGE FEES ACTIVE</strong>
                                                <span>UGX {fmt(effectiveMonthlyFee)}/month accumulates until full balance is cleared</span>
                                            </div>
                                        </div>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox}>
                                                <label>ORIGINAL DEBT</label>
                                                <strong>UGX {fmt(origDebt)}</strong>
                                            </div>
                                            <div className={styles.statBox}>
                                                <label style={{color:'#ef4444'}}>+ STORAGE FEES</label>
                                                <strong className={styles.redGlow}>UGX {fmt(storageFees)}</strong>
                                                <small style={{opacity:0.5,fontSize:'0.7rem'}}>
                                                    {project.backlogStartDate
                                                        ? `Since ${new Date(project.backlogStartDate).toLocaleDateString()}`
                                                        : 'UGX ' + fmt(effectiveMonthlyFee) + '/month'}
                                                </small>
                                            </div>
                                            <div className={styles.statBox}>
                                                <label>- PAYMENTS MADE</label>
                                                <strong style={{color:'#86efac'}}>UGX {fmt(amountPaid)}</strong>
                                            </div>
                                        </div>
                                        <div className={styles.totalOwedBanner}>
                                            <span>TOTAL NOW OWED</span>
                                            <strong>UGX {fmt(Math.max(0, backlogOwed))}</strong>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalCost)}</strong></div>
                                            <div className={styles.statBox}><label>COLLECTED</label><strong style={{color:'#86efac'}}>UGX {fmt(amountPaid)}</strong></div>
                                            <div className={styles.statBox}><label>ARREARS</label><strong className={styles.redGlow}>UGX {fmt(remaining)}</strong></div>
                                        </div>
                                        <div className={styles.collectionBar}>
                                            <div className={styles.collectionFill}
                                                style={{width: totalCost > 0 ? `${Math.min(100,(amountPaid/totalCost)*100)}%` : '0%'}} />
                                        </div>
                                        <div className={styles.velocityNote}>
                                            <FiClock aria-hidden="true" />
                                            <span>COLLECTION: <strong>{(binder.collectionPercentage||0).toFixed(1)}%</strong></span>
                                        </div>
                                    </>
                                )}

                            </div>
                        </section>

                        {/* ── 2. BACKLOG CONTROLS (admin only, shown when backlog) ── */}
                        {isAdmin && isBacklog && (
                            <section className={styles.hwPanel} aria-label="Backlog Controls">
                                <div className={styles.finPanelHeader} style={{color:'#fca5a5', borderBottomColor:'rgba(239,68,68,0.3)'}}>
                                    <FiAlertOctagon aria-hidden="true" />
                                    BACKLOG CONTROLS
                                </div>
                                <div className={styles.panelInner}>
                                    {isEditing ? (
                                        <>
                                            <div className={styles.inputGrid3}>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>MONTHLY STORAGE FEE (UGX)</label></div>
                                                    <input type="number" className={styles.hwInput}
                                                        defaultValue={project.storageFeeOverride || 50000}
                                                        onBlur={async e => {
                                                            const val = Number(e.target.value);
                                                            if (val >= 0) {
                                                                try { await recoveryService.setStorageRate(project.id, val); await loadFolderData(); toast('RATE UPDATED', 'success'); }
                                                                catch { /* silent */ }
                                                            }
                                                        }}
                                                        placeholder="50000" />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>ADJUST ACCUMULATED FEES (UGX)</label></div>
                                                    <input type="number" className={styles.hwInput}
                                                        defaultValue={project.storageFeesAccumulated || 0}
                                                        onBlur={async e => {
                                                            const val = Number(e.target.value);
                                                            if (val >= 0) {
                                                                try { await recoveryService.setAccumulatedFees(project.id, val); await loadFolderData(); toast('FEES ADJUSTED', 'success'); }
                                                                catch { /* silent */ }
                                                            }
                                                        }}
                                                        placeholder={String(project.storageFeesAccumulated || 0)} />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>FEES STATUS</label></div>
                                                    <button type="button"
                                                        className={project.storagePaused ? styles.btnResumeActive : styles.btnPauseGrey}
                                                        onClick={async () => {
                                                            try {
                                                                await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                                await loadFolderData();
                                                                toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                            } catch { toast('ACTION FAILED', 'error'); }
                                                        }}>
                                                        {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                                    </button>
                                                </div>
                                            </div>
                                            <div className={styles.inputGrid3} style={{marginTop:8}}>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>NEGOTIATION DEADLINE</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        defaultValue={project.negotiationDeadline ? project.negotiationDeadline.substring(0,10) : ''}
                                                        onBlur={async e => {
                                                            try { await recoveryService.setNegotiationDeadline(project.id, e.target.value || null); await loadFolderData(); toast('DEADLINE UPDATED', 'info', 2000); }
                                                            catch { /* silent */ }
                                                        }} />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>BACKLOG START DATE OVERRIDE</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        defaultValue={project.backlogStartDate ? project.backlogStartDate.substring(0,10) : ''}
                                                        onBlur={async e => {
                                                            if (!e.target.value) return;
                                                            try { await recoveryService.setBacklogStartOverride(project.id, e.target.value); await loadFolderData(); toast('START DATE OVERRIDDEN', 'info', 2000); }
                                                            catch { /* silent */ }
                                                        }} />
                                                </div>
                                            </div>
                                            <div className={styles.editBacklogFeeHint}>
                                                Current monthly fee: UGX {fmt(effectiveMonthlyFee)}. Negotiation deadline pauses fees automatically until that date.
                                            </div>
                                        </>
                                    ) : (
                                        <div className={styles.readOnlyGrid}>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>MONTHLY STORAGE FEE</span>
                                                <span className={styles.specValue}>UGX {fmt(effectiveMonthlyFee)}</span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>FEES STATUS</span>
                                                <span className={styles.specValue} style={{ color: project.storagePaused ? '#fcd34d' : '#86efac' }}>
                                                    {project.storagePaused ? 'PAUSED' : 'ACTIVE'}
                                                </span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>ACCUMULATED FEES</span>
                                                <span className={styles.specValue}>UGX {fmt(project.storageFeesAccumulated)}</span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>NEGOTIATION DEADLINE</span>
                                                <span className={styles.specValue}>
                                                    {project.negotiationDeadline ? new Date(project.negotiationDeadline).toLocaleDateString() : 'NONE'}
                                                </span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>BACKLOG START DATE</span>
                                                <span className={styles.specValue}>
                                                    {project.backlogStartDate ? new Date(project.backlogStartDate).toLocaleDateString() : 'UNKNOWN'}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </section>
                        )}

                        {/* ── 3. PAYMENT HISTORY ── */}
                        <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                            <div className={styles.finPanelHeader}>
                                <FiActivity aria-hidden="true" />
                                PAYMENT HISTORY
                                <span className={styles.finPanelCount}>{paymentCount}</span>
                            </div>
                            <div className={styles.panelInner}>
                                {paymentCount === 0 ? (
                                    <div className={styles.emptyState} role="status">
                                        <FiDollarSign className={styles.emptyIcon} aria-hidden="true" />
                                        <span>NO PAYMENTS RECORDED YET</span>
                                    </div>
                                ) : (
                                    <div className={styles.paymentList}>
                                        {payments.map((pay, i) => (
                                            <div key={pay.id || i} id={`payment-${pay.id}`} className={styles.paymentRow}
                                                style={{borderLeftColor: pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#06b6d4' : '#22c55e'}}>
                                                <div className={styles.payRowLeft}>
                                                    <div className={styles.payAmount}>UGX {fmt(pay.amountPaid)}</div>
                                                    <div className={styles.payMeta}>
                                                        <span className={styles.payType}
                                                            style={{color: pay.paymentType === 'BACKLOG_PARTIAL' ? '#fca5a5' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#67e8f9' : '#86efac'}}>
                                                            {pay.paymentType === 'STANDARD' ? 'Title Payment'
                                                            : pay.paymentType === 'INITIAL_DEPOSIT' ? 'Initial Deposit'
                                                            : pay.paymentType === 'BACKLOG_PARTIAL' ? 'Backlog Payment'
                                                            : pay.paymentType}
                                                        </span>
                                                        <span className={styles.payBy}>by {pay.recordedBy}</span>
                                                        {pay.notes && <span className={styles.payNotes}>{pay.notes}</span>}
                                                    </div>
                                                </div>
                                                <div className={styles.payRowRight}>
                                                    <div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div>
                                                    {pay.balanceAfter != null && (
                                                        <div className={styles.payBalance}>Bal: UGX {fmt(pay.balanceAfter)}</div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </section>

                        {/* ── 4. NOTES & CALL LOG ── */}
                        <section className={styles.hwPanel} aria-label="Notes and Call Log">
                            <div className={styles.finPanelHeader}>
                                <FiInfo aria-hidden="true" />
                                NOTES & CALL LOG
                                <span className={styles.finPanelCount}>{noteCount}</span>
                                {isEditing && (
                                    <button type="button" className={styles.addNoteInlineBtn}
                                        onClick={() => setNoteModal({open:true,id:null,content:''})}>
                                        + ADD NOTE
                                    </button>
                                )}
                            </div>
                            <div className={styles.panelInner}>
                                {noteCount === 0 ? (
                                    <div className={styles.emptyState} role="status">
                                        <FiInfo className={styles.emptyIcon} aria-hidden="true" />
                                        <span>NO NOTES LOGGED YET</span>
                                    </div>
                                ) : (
                                    <div className={styles.notebookTimeline} role="list">
                                        {binder.notes.map((log, i) => (
                                            <article key={i} className={styles.ruledNote} role="listitem">
                                                <div className={styles.noteMeta}>
                                                    <div className={styles.noteMetaLeft}>
                                                        <time className={styles.noteTime} dateTime={log.timestamp}>
                                                            {new Date(log.timestamp).toLocaleDateString()}
                                                        </time>
                                                        <span className={styles.noteAuthor}>by {log.recordedBy}</span>
                                                    </div>
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
                                )}
                            </div>
                        </section>

                    </div>
                )}

                {/* ════════════════════════════════════════════════════
                    OWNERS TAB
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'OWNERS' && (
                    <section className={styles.hwPanel} aria-label="Owners">
                        <div className={styles.panelInner}>
                            <div className={styles.ownersScroll}>
                                <div className={styles.ownersGrid2} role="list">
                                    {isEditing ? buffer.owners.map((o, idx) => (
                                        <div key={idx} className={styles.ownerEditCard} role="listitem">
                                            <div className={styles.ownerCardLabel}>ENTITY #{idx+1} {idx===0&&'(PRIMARY)'}</div>
                                            <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                            <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} onBlur={v => handlePhoneBlurCheck(idx, v)} id={`owner_${idx}_phone`} />
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
                    </section>
                )}

                {/* ════════════════════════════════════════════════════
                    DOCUMENTS TAB — Files + upload
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'DOCUMENTS' && (
                    <section className={styles.hwPanel} aria-label="Documents">
                        <div className={styles.finPanelHeader}>
                            <FiUploadCloud aria-hidden="true" />
                            DOCUMENTS
                            <span className={styles.finPanelCount}>{docCount}</span>
                            {isEditing && (
                                <button type="button" className={styles.addNoteInlineBtn}
                                    onClick={() => fileInputRef.current?.click()}>
                                    + UPLOAD SCANS
                                </button>
                            )}
                        </div>
                        <div className={styles.panelInner}>
                            {docCount === 0 ? (
                                <div className={styles.emptyState} role="status">
                                    <FiUploadCloud className={styles.emptyIcon} aria-hidden="true" />
                                    <span>NO DOCUMENTS ATTACHED</span>
                                    {isEditing && (
                                        <button type="button" className={styles.addDocBtn}
                                            onClick={() => fileInputRef.current?.click()}>
                                            + INGEST NEW SCANS
                                        </button>
                                    )}
                                </div>
                            ) : (
                                <>
                                    <div className={styles.compactVault} role="list">
                                        {binder.documents.map((doc, idx) => (
                                            <div key={idx} className={styles.docTag} role="listitem">
                                                <FiFileText className={styles.docIcon} aria-hidden="true" />
                                                <button type="button" className={styles.docName}
                                                    style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}
                                                    onClick={() => handleOpenDoc(doc.filePath, doc.fileName)}
                                                    title={isPDF(doc.filePath) ? 'Open PDF in new tab' : 'Open ' + doc.fileName}>
                                                    {isPDF(doc.filePath) ? '📄 ' : '🖼 '}{doc.fileName}
                                                </button>
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
                                        <button type="button" className={styles.addDocBtn}
                                            onClick={() => fileInputRef.current?.click()}>
                                            + INGEST MORE SCANS
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                    </section>
                )}

            </main>

            <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp"
                style={{ display:'none' }} aria-hidden="true" tabIndex={-1}
                onChange={e => { if (!e.target.files?.length) return; handleVaultAction(Array.from(e.target.files)); e.target.value=''; }} />

            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="Plot Record Edit"
            />

            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />


            {/* NOTE MODAL */}
            <HardwareModal isOpen={noteModal.open} onClose={() => {
                if (noteModal.content.trim() !== '') {
                    if (!window.confirm('Discard unsaved note?')) return;
                }
                setNoteModal({open:false, id:null, content:''});
            }} title="ADD NOTE">
                <div className={modalStyles.modalField}>
                    <textarea className={modalStyles.modalTextarea} value={noteModal.content}
                        onChange={e => setNoteModal({...noteModal,content:e.target.value})}
                        placeholder="Enter interaction note..." aria-label="Note content" />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setNoteModal({open:false,id:null,content:''})}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave}>
                        <FiSave aria-hidden="true" /> SAVE ENTRY
                    </button>
                </div>
            </HardwareModal>

            {/* PAYMENT MODAL */}
            <HardwareModal isOpen={payModal.open} onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={`RECORD PAYMENT — ${project.landTitle.plotNumber}`}>
                <div className={styles.payBreakdownBox}>
                    {isBacklog ? (
                        <>
                            <div className={styles.payBreakdownTitle}>
                                <FiAlertOctagon size={11} /> BACKLOG BALANCE BREAKDOWN
                            </div>
                            <div className={styles.payBreakdownGrid}>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel}>ORIGINAL TITLE DEBT</span>
                                    <span className={styles.pbVal}>UGX {fmt(origDebt)}</span>
                                </div>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel} style={{color:'#fca5a5'}}>STORAGE FEES (MONTHLY)</span>
                                    <span className={styles.pbVal} style={{color:'#ef4444'}}>+ UGX {fmt(storageFees)}</span>
                                </div>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel}>PAYMENTS MADE</span>
                                    <span className={styles.pbVal} style={{color:'#86efac'}}>- UGX {fmt(amountPaid)}</span>
                                </div>
                                <div className={styles.pbItemTotal}>
                                    <span className={styles.pbLabel}>TOTAL NOW OWED</span>
                                    <span className={styles.pbValTotal}>UGX {fmt(Math.max(0, backlogOwed))}</span>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className={styles.payBreakdownGrid}>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel}>TITLE COST</span>
                                <span className={styles.pbVal}>UGX {fmt(totalCost)}</span>
                            </div>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel}>PAID SO FAR</span>
                                <span className={styles.pbVal} style={{color:'#86efac'}}>UGX {fmt(amountPaid)}</span>
                            </div>
                            <div className={styles.pbItemTotal}>
                                <span className={styles.pbLabel}>REMAINING BALANCE</span>
                                <span className={styles.pbValTotal}>UGX {fmt(Math.max(0, activeOwed))}</span>
                            </div>
                        </div>
                    )}
                </div>

                {isBacklog && (
                    <div className={styles.payTypeRow}>
                        <div className={styles.payTypeLabel}>WHAT IS THIS PAYMENT FOR?</div>
                        <div className={styles.payTypeButtons}>
                            <button type="button" className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`} onClick={() => setPayType('TITLE')}>
                                <FiHome size={12} />
                                <div>
                                    <div className={styles.payTypeBtnName}>TITLE PAYMENT</div>
                                    <div className={styles.payTypeBtnSub}>Reduces the original title debt</div>
                                </div>
                            </button>
                            <button type="button" className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`} onClick={() => setPayType('STORAGE')}>
                                <FiArchive size={12} />
                                <div>
                                    <div className={styles.payTypeBtnName}>STORAGE FEE</div>
                                    <div className={styles.payTypeBtnSub}>Covers monthly storage charges</div>
                                </div>
                            </button>
                        </div>
                    </div>
                )}

                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="number" className={modalStyles.modalInput}
                        placeholder={isBacklog && payType === 'STORAGE' ? "e.g. 50000 (1 month)" : `e.g. ${fmt(Math.max(0, remaining))}`}
                        value={payAmount} onChange={e => setPayAmount(e.target.value)} />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="e.g. Paid via MTN Mobile Money..."
                        value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <HardwareButton type="button" onClick={handleRecordPayment} loading={paying} icon={FiDollarSign}>
                        CONFIRM {payType === 'STORAGE' ? 'STORAGE FEE' : 'PAYMENT'}
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default FolderPage;