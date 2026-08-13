// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import {
    FiMap, FiUsers, FiCreditCard, FiUploadCloud,
    FiInfo, FiPlusSquare, FiTrash2, FiSend, FiSave, FiCopy,
    FiCheckCircle, FiAlertCircle, FiAlertTriangle, FiX, FiCheckSquare, FiAlertOctagon,
    FiEdit3
} from 'react-icons/fi';
import landService from '../../services/landService';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import predictionService from '../../services/predictionService';
import stageTemplateService from '../../services/stageTemplateService';
import clientService from '../../services/clientService';
import styles from './IntakePage.module.css';

// ── TOAST ────────────────────────────────────────────────────────
const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4500) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);
    const dismiss = useCallback(id => setToasts(prev => prev.filter(t => t.id !== id)), []);
    return { toasts, toast, dismissToast: dismiss };
};
const TOAST_ICONS = {
    success: <FiCheckSquare aria-hidden="true" />,
    error:   <FiAlertCircle aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiAlertCircle aria-hidden="true" />,
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

// ── SAVING OVERLAY ────────────────────────────────────────────────
const SavingOverlay = ({ visible }) => {
    if (!visible || typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.savingOverlay} role="status" aria-label="Saving">
            <div className={styles.savingRing} aria-hidden="true" />
            <span className={styles.savingLabel}>COMMITTING TO ARCHIVE...</span>
        </div>,
        document.body
    );
};

// ── DRAWER HEADER ─────────────────────────────────────────────────
const DrawerHeader = ({ label, isOpen, onClick, icon: Icon, badge }) => (
    <div className={styles.drawerHeader} onClick={onClick} role="button" tabIndex={0}
        aria-expanded={isOpen}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}>
        <div className={styles.drawerTitle}>
            {Icon && <Icon className={styles.drawerIcon} aria-hidden="true" />}
            {label}
            {badge !== undefined && <span className={styles.drawerBadge}>{badge}</span>}
        </div>
        <span className={`${styles.chevron} ${isOpen ? styles.rotated : ''}`} aria-hidden="true">▾</span>
    </div>
);

// ── SMART INPUT ───────────────────────────────────────────────────
const SmartInput = ({ label, value, onChange, onBlur, placeholder, suggestions = [], showCaps, required, error, inputMode, maxLength, hint, id }) => {
    const inputId = id || 'si-' + (label || '').replace(/\W/g, '-').toLowerCase();
    return (
        <div className={`${styles.inputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
                {showCaps && <span className={styles.capsBadge}>CAPS</span>}
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                type="text" value={value} onChange={onChange} onBlur={onBlur} placeholder={placeholder}
                inputMode={inputMode} maxLength={maxLength} autoComplete="off"
                list={suggestions.length ? inputId + '_dl' : undefined} />
            {suggestions.length > 0 && (
                <datalist id={inputId + '_dl'}>
                    {suggestions.map((s,i) => <option key={i} value={s} />)}
                </datalist>
            )}
            {error && <span className={styles.fieldError}>{error}</span>}
            {!error && hint && <span className={styles.fieldHint}>{hint}</span>}
        </div>
    );
};

// ── SMART SELECT ──────────────────────────────────────────────────
const SmartSelect = ({ label, options, value, onChange, id }) => {
    const [open, setOpen] = useState(false);
    const ref = useRef(null);
    const selectId = id || 'ss-' + (label || '').replace(/\W/g, '-').toLowerCase();
    useEffect(() => {
        const h = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);
    return (
        <div className={styles.inputWrap} ref={ref} style={{ position: 'relative' }}>
            <div className={styles.labelRow}>
                <label id={selectId + '_lbl'} className={styles.fieldLabel}>{label}</label>
            </div>
            <div id={selectId} role="combobox" aria-haspopup="listbox" aria-expanded={open}
                aria-labelledby={selectId + '_lbl'} tabIndex={0}
                className={`${styles.selectTrigger} ${open ? styles.selectTriggerOpen : ''}`}
                onClick={() => setOpen(o => !o)}
                onKeyDown={e => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); }
                    if (e.key === 'Escape') setOpen(false);
                }}>
                <span className={styles.selectValue}>{value}</span>
                <span className={`${styles.selectChevron} ${open ? styles.rotated : ''}`} aria-hidden="true">▾</span>
            </div>
            {open && (
                <ul role="listbox" aria-labelledby={selectId + '_lbl'} className={styles.selectDropdown}>
                    {options.map(opt => (
                        <li key={opt} role="option" aria-selected={opt === value}
                            className={`${styles.selectOption} ${opt === value ? styles.selectOptionActive : ''}`}
                            onClick={() => { onChange(opt); setOpen(false); }}>{opt}</li>
                    ))}
                </ul>
            )}
        </div>
    );
};

// ── CURRENCY INPUT ────────────────────────────────────────────────
const CurrencyInput = ({ label, value, onChange, error, id, required }) => {
    const [focused, setFocused] = useState(false);
    const inputId = id || 'cur-' + (label||'').replace(/\W/g,'-').toLowerCase();
    const display = focused ? String(value||'') : (value ? Number(value).toLocaleString() : '');
    return (
        <div className={`${styles.inputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
                <span className={styles.capsBadge} style={{ background: 'rgba(238,140,58,0.18)', color: '#EE8C3A' }}>UGX</span>
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                inputMode="numeric" value={display}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                onChange={e => onChange(e.target.value.replace(/\D/g, ''))}
                placeholder="0" />
            {error && <span className={styles.fieldError}>{error}</span>}
        </div>
    );
};

// ── PHONE INPUT ───────────────────────────────────────────────────
const PhoneInput = ({ label='PHONE NUMBER', value, onChange, onBlur, id, required, fieldError }) => {
    const inputId = id || 'phi';
    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
            </div>
            <input id={inputId} type="tel" value={value}
                onChange={e => onChange(e.target.value.replace(/[^0-9\s/]/g, ''))}
                onBlur={onBlur ? e => onBlur(e.target.value) : undefined}
                placeholder="0712 345 678"
                inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`} />
            {fieldError && <span className={styles.fieldError}>{fieldError}</span>}
            <span className={styles.fieldHint}>Use &#39;/&#39; to separate multiple numbers (e.g. 077... / 075...)</span>
        </div>
    );
};

// ── CONFIRM HOOK (mirrors FolderPage pattern) ─────────────────────
const useIntakeConfirm = () => {
    const [state, setState] = useState({ open: false, title: '', message: '', variant: 'warn', resolve: null });
    const confirm = useCallback((title, message, variant = 'warn') =>
        new Promise(resolve => setState({ open: true, title, message, variant, resolve })), []);
    const handleAnswer = useCallback((answer) => {
        setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; });
    }, []);
    return { confirmState: state, confirm, handleAnswer };
};

const IntakeConfirmModal = ({ state, onAnswer }) => {
    if (!state.open || typeof document === 'undefined') return null;
    return (
        <div style={{
            position:'fixed',inset:0,zIndex:99998,
            background:'rgba(10,20,22,0.82)',backdropFilter:'blur(6px)',
            display:'flex',alignItems:'center',justifyContent:'center',padding:24
        }} role="dialog" aria-modal="true">
            <div style={{
                background:'linear-gradient(160deg,#1c3335 0%,#213E40 100%)',
                border:'1.5px solid rgba(238,140,58,0.35)',borderRadius:12,
                maxWidth:460,width:'100%',overflow:'hidden',
                boxShadow:'0 20px 60px rgba(0,0,0,0.6)'
            }}>
                <div style={{
                    display:'flex',alignItems:'center',gap:12,
                    padding:'14px 20px',borderBottom:'1px solid rgba(255,255,255,0.08)',
                    background:'rgba(245,158,11,0.14)'
                }}>
                    <span style={{fontSize:20,color:'#f59e0b'}}>⚠</span>
                    <span style={{fontFamily:'Space Mono,monospace',fontSize:11,fontWeight:900,textTransform:'uppercase',letterSpacing:1.5,color:'#fcd34d'}}>{state.title}</span>
                </div>
                <p style={{padding:'16px 20px',fontFamily:'DM Sans,sans-serif',fontSize:13,fontWeight:800,lineHeight:1.6,color:'rgba(255,255,255,0.8)',margin:0}}>{state.message}</p>
                <div style={{display:'flex',justifyContent:'flex-end',gap:10,padding:'12px 20px',background:'rgba(0,0,0,0.2)',borderTop:'1px solid rgba(255,255,255,0.06)'}}>
                    <button onClick={() => onAnswer(false)} autoFocus style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'rgba(255,255,255,0.06)',border:'1.5px solid rgba(255,255,255,0.2)',color:'rgba(255,255,255,0.7)',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                        CANCEL
                    </button>
                    <button onClick={() => onAnswer(true)} style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'#EE8C3A',border:'none',color:'#1a2e30',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                        DISCARD
                    </button>
                </div>
            </div>
        </div>
    );
};

// ── MAIN COMPONENT ────────────────────────────────────────────────
const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const IntakePage = () => {
    const navigate = useNavigate();
    const DEFAULT_START_DATE = React.useMemo(() => new Date().toISOString().split('T')[0], []);
    const { toasts, toast, dismissToast } = useToast();

    // Unsaved changes guard -- wired below once isDirty is defined
    const fileInputRef = useRef(null);
    const { confirmState: noteConfirmState, confirm: confirmNote, handleAnswer: handleNoteAnswer } = useIntakeConfirm();

    const [saving, setSaving] = useState(false);
    const [drawers, setDrawers] = useState({ plot: true, owners: true, finance: true, stages: true, docs: false, notes: false });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));

    const [errors, setErrors] = useState({});

    // PHASE 6: Legacy Receivables Entry Mode -- simplified path for old
    // titles already in storage. Single lump total cost, no stage checklist.
    const [isLegacyMode, setIsLegacyMode] = useState(false);

    // Plot fields
    const [plotNumber,        setPlotNumber]        = useState('');
    const [tenure,            setTenure]            = useState('MAILO');
    const [physicalBoxNumber, setPhysicalBoxNumber] = useState('');
    const [district,          setDistrict]          = useState('');
    const [county,            setCounty]            = useState('');
    const [blockRoad,         setBlockRoad]         = useState('');
    const [volume,            setVolume]            = useState('');
    const [folio,             setFolio]             = useState('');
    const [instrumentNo,      setInstrumentNo]      = useState('');

    // Owners
    const [owners, setOwners] = useState([EMPTY_OWNER()]);

    // Financials — SIMPLIFIED: only totalCost, initialPayment, isBacklog
    const [totalCost,         setTotalCost]         = useState('');
    const [initialPayment,    setInitialPayment]    = useState('');
    const [isBacklog,         setIsBacklog]         = useState(false);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState('50000');
    const [initialStorageFee, setInitialStorageFee] = useState('');
    const [surveyDate,        setSurveyDate]        = useState('');
    const [projectStartDate,  setProjectStartDate]  = useState(() => new Date().toISOString().split('T')[0]);
    const [titleIssueDate,    setTitleIssueDate]    = useState('');

    // Stages (Phase 4B)
    const [stageTemplates, setStageTemplates] = useState([]);
    const [checkedStages,  setCheckedStages]  = useState({});
    const [stageCosts,     setStageCosts]     = useState({});
    const [stageNotes,     setStageNotes]     = useState({});
    const [customStages,   setCustomStages]   = useState([]);
    const [newCustomName,  setNewCustomName]  = useState('');
    const [newCustomCost,  setNewCustomCost]  = useState('');

    // Docs & notes
    const [fileQueue,    setFileQueue]    = useState([]);
    const [notesList,    setNotesList]    = useState([]);
    const [noteModalOpen, setNoteModalOpen] = useState(false);
    const [noteModalText, setNoteModalText] = useState('');
    const [editingNoteIdx, setEditingNoteIdx] = useState(null);



    // isDirty must be defined AFTER all useState hooks to avoid
    // "Cannot access before initialization" error in the minified bundle
    // Guard only fires when the user has meaningfully started filling the form:
    // plotNumber set AND (owner name/phone filled OR cost set OR files attached)
    // Any single character entered in any field makes the form dirty
    const isDirty = React.useMemo(() => {
        if (plotNumber !== '') return true;
        if (district !== '') return true;
        if (county !== '') return true;
        if (blockRoad !== '') return true;
        if (physicalBoxNumber !== '') return true;
        if (volume !== '') return true;
        if (folio !== '') return true;
        if (instrumentNo !== '') return true;
        if (totalCost !== '') return true;
        if (initialPayment !== '') return true;
        if (monthlyStorageFee !== '50000') return true;
        if (initialStorageFee !== '') return true;
        if (surveyDate !== '') return true;
        if (titleIssueDate !== '') return true;
        if (projectStartDate !== DEFAULT_START_DATE) return true;
        if (fileQueue.length > 0) return true;
        if (notesList.length > 0) return true;
        if (owners.some(o =>
            o.fullName !== '' || o.phone !== '' || o.email !== '' ||
            o.nationalId !== '' || o.address !== ''
        )) return true;
        return false;
    }, [plotNumber, district, county, blockRoad, physicalBoxNumber,
        volume, folio, instrumentNo, totalCost, initialPayment,
        monthlyStorageFee, initialStorageFee, fileQueue, notesList, owners]);

    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =
        useRouterBlock(!saving && isDirty);

    // beforeunload -- catches tab close, hard refresh, browser back button to external site
    useEffect(() => {
        if (!isDirty || saving) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
            return '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);

    // NOTE: beforeunload is also handled by useRouterBlock hook

    const sg = key => predictionService.getSuggestions(key) || [];

    // Load the master stage checklist once on mount (Phase 4B)
    useEffect(() => {
        stageTemplateService.getTemplate()
            .then(data => setStageTemplates(data || []))
            .catch(() => {});
    }, []);

    const validate = () => {
        const e = {};
        if (!plotNumber.trim())        e.plotNumber = 'Required';
        if (!district.trim())          e.district   = 'Required';
        if (!totalCost)                e.totalCost  = 'Required';
        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
            if (!o.nationalId.trim())  e['owner_' + i + '_nin']   = 'Required';
        });
        if (fileQueue.length === 0) {
            e.docs = true;
            toast('At least one document scan is required.', 'error', 6000);
            setDrawers(prev => ({ ...prev, docs: true }));
        }
        setErrors(e);
        return Object.keys(e).length === 0 && fileQueue.length > 0;
    };

    // Duplicate: save current plot first, then pre-fill form for a similar new plot
    const handleDuplicatePlot = async () => {
        if (!validate()) {
            toast('Fix the highlighted fields before duplicating', 'error');
            return;
        }
        setSaving(true);
        try {
            const payload = {
                plotNumber: plotNumber.trim().toUpperCase(),
                tenure,
                physicalBoxNumber: physicalBoxNumber.trim().toUpperCase(),
                district:   district.trim().toUpperCase(),
                county:     county.trim().toUpperCase(),
                blockRoad:  blockRoad.trim().toUpperCase(),
                volume,
                folio,
                instrumentNo: instrumentNo.trim().toUpperCase(),
                totalCost:      Number(totalCost)      || 0,
                initialPayment: Number(initialPayment) || 0,
                isStartAsBacklog: isBacklog,
                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
                isLegacy: isLegacyMode,
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
                selectedStages: isLegacyMode ? [] : [
                    ...Object.entries(checkedStages).filter(([, v]) => v).map(([tid]) => ({
                        stageTemplateId: tid,
                        cost: stageCosts[tid] !== undefined ? Number(stageCosts[tid]) : undefined,
                        notes: stageNotes[tid] || undefined,
                        isCustom: false,
                    })),
                    ...customStages.map(cs => ({
                        stageName: cs.name,
                        cost: Number(cs.cost) || 0,
                        isCustom: true,
                    })),
                ],
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Saved! Now enter a new Plot ID for the duplicate', 'success', 4000);
            // Pre-fill everything except the unique fields
            setPlotNumber('');
            setInitialPayment('');
            setInitialStorageFee('');
            setSurveyDate('');
            setFileQueue([]);
            setNotesList([]);
            setErrors({});
            // Keep: tenure, physicalBoxNumber, district, county, blockRoad,
            //       volume, folio, instrumentNo, totalCost, isBacklog,
            //       monthlyStorageFee, owners
        } catch (err) {
            const msg = err.response?.data?.message || err.message || 'Save failed';
            toast(msg, 'error', 8000);
        } finally {
            setSaving(false);
        }
    };

    const handleSubmit = async () => {
        if (!validate()) {
            toast('Please fix the highlighted fields', 'error');
            return;
        }
        setSaving(true);
        try {
            const payload = {
                plotNumber: plotNumber.trim().toUpperCase(),
                tenure,
                physicalBoxNumber: physicalBoxNumber.trim().toUpperCase(),
                district:   district.trim().toUpperCase(),
                county:     county.trim().toUpperCase(),
                blockRoad:  blockRoad.trim().toUpperCase(),
                volume,
                folio,
                instrumentNo: instrumentNo.trim().toUpperCase(),
                totalCost:      Number(totalCost)      || 0,
                initialPayment: Number(initialPayment) || 0,
                isStartAsBacklog: isBacklog,
                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,
                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,
                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
                isLegacy: isLegacyMode, // Section 17.6: staff flips ENTRY MODE toggle to mark a Legacy Receivable
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
                selectedStages: isLegacyMode ? [] : [
                    ...Object.entries(checkedStages).filter(([, v]) => v).map(([tid]) => ({
                        stageTemplateId: tid,
                        cost: stageCosts[tid] !== undefined ? Number(stageCosts[tid]) : undefined,
                        notes: stageNotes[tid] || undefined,
                        isCustom: false,
                    })),
                    ...customStages.map(cs => ({
                        stageName: cs.name,
                        cost: Number(cs.cost) || 0,
                        isCustom: true,
                    })),
                ],
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Plot registered successfully!', 'success', 3000);
            setTimeout(() => navigate('/land/projects'), 1800); // safe: data saved
        } catch (err) {
            const msg = err.response?.data?.message || err.message || 'Save failed';
            toast(msg, 'error', 8000);
        } finally {
            setSaving(false);
        }
    };

    const updateOwner = (idx, field, val) => {
        setOwners(prev => prev.map((o, i) => i === idx ? { ...o, [field]: val } : o));
    };

    const addOwner = () => setOwners(prev => [...prev, EMPTY_OWNER()]);

    // PHASE 2: NIN duplicate/auto-fill check. Warns on likely typo (NIN already
    // registered under a different name), auto-fills known details on a real match.
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            toast(`WARNING: This NIN is already registered to "${result.fullName}". Check for a typo.`, 'warn', 6000);
            return;
        }

        setOwners(prev => prev.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                fullName: o.fullName.trim() ? o.fullName : (result.fullName || o.fullName),
                phone:    o.phone.trim()    ? o.phone    : (result.phoneNumber || o.phone),
                email:    o.email.trim()    ? o.email    : (result.email || o.email),
                address:  o.address.trim()  ? o.address  : (result.homeAddress || o.address),
            };
        }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };

    // Warn if a phone number is already used by another owner on this form
    const handlePhoneBlurCheck = (idx, val) => {
        if (!val.trim()) return;
        const normalized = val.replace(/\s+/g, '');
        const duplicate = owners.some((o, i) => i !== idx && o.phone.replace(/\s+/g, '') === normalized);
        if (duplicate) {
            toast('WARNING: This phone number is already used by another owner on this form.', 'warn', 5000);
        }
    };
    const removeOwner = idx => setOwners(prev => prev.filter((_, i) => i !== idx));

    const addFiles = files => {
        const incoming = Array.from(files);
        if (!incoming.length) return;
        setFileQueue(prev => {
            const existing = new Set(prev.map(f => f.name));
            const newFiles = incoming.filter(f => !existing.has(f.name));
            if (!newFiles.length) return prev;
            return [...prev, ...newFiles];
        });
    };

    const arrears = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));
    const selectedStageCount = Object.values(checkedStages).filter(Boolean).length + customStages.length;

    return (
        <div className={styles.container}>

            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={saving} />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Plot Registration</h1>
                    <p className={styles.subtitle}>
                        {isLegacyMode
                            ? 'Legacy Receivable -- lump-sum entry for a title already in storage'
                            : 'Register a new land title into the system'}
                    </p>
                </div>
            </header>

            <div className={styles.hwPanel} style={{ marginBottom: 16 }}>
                <div className={styles.panelInner}>
                    <div className={styles.modeRow} style={{ marginTop: 0 }}>
                        <label>ENTRY MODE</label>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button type="button"
                                className={!isLegacyMode ? styles.toggleLegacy : styles.toggleStandard}
                                onClick={() => setIsLegacyMode(false)}>
                                ✓ STANDARD PROJECT
                            </button>
                            <button type="button"
                                className={isLegacyMode ? styles.toggleLegacy : styles.toggleStandard}
                                style={isLegacyMode ? { borderColor: '#06b6d4', color: '#06b6d4', background: 'rgba(6,182,212,0.12)' } : {}}
                                onClick={() => setIsLegacyMode(true)}>
                                ⚠ LEGACY RECEIVABLE
                            </button>
                        </div>
                        {isLegacyMode && (
                            <div className={styles.backlogFeeNote} style={{ borderColor: 'rgba(6,182,212,0.25)', background: 'rgba(6,182,212,0.08)', color: 'rgba(255,255,255,0.55)' }}>
                                Enter the real total cost from the ledger in the Financials section below.
                                No stage checklist needed for legacy titles -- this behaves like a normal
                                project for payment tracking once saved.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className={styles.formFlow}>

                {/* ── PLOT DETAILS ── */}
                <div className={styles.hwPanel}>
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.plot} onClick={() => toggleDrawer('plot')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.plot ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            <div className={styles.grid3}>
                                <SmartInput label="PLOT ID" value={plotNumber} showCaps required
                                    error={errors.plotNumber}
                                    onChange={e => setPlotNumber(e.target.value.toUpperCase())} />
                                <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']}
                                    value={tenure} onChange={setTenure} />
                                <SmartInput label="BOX LOCATION" value={physicalBoxNumber} showCaps
                                    onChange={e => setPhysicalBoxNumber(e.target.value.toUpperCase())} />
                            </div>
                            <div className={styles.grid3}>
                                <SmartInput label="DISTRICT" value={district} showCaps required
                                    error={errors.district} suggestions={sg('district')}
                                    onChange={e => setDistrict(e.target.value.toUpperCase())} />
                                <SmartInput label="COUNTY" value={county} showCaps suggestions={sg('county')}
                                    onChange={e => setCounty(e.target.value.toUpperCase())} />
                                <SmartInput label="BLOCK / ROAD" value={blockRoad} showCaps suggestions={sg('blockRoad')}
                                    onChange={e => setBlockRoad(e.target.value.toUpperCase())} />
                            </div>
                            <div className={styles.grid3}>
                                <SmartInput label="INSTRUMENT NO." value={instrumentNo} showCaps
                                    onChange={e => setInstrumentNo(e.target.value.toUpperCase())} />
                                <SmartInput label="VOLUME" value={volume} inputMode="numeric"
                                    onChange={e => setVolume(e.target.value.replace(/\D/g,''))} />
                                <SmartInput label="FOLIO" value={folio} inputMode="numeric"
                                    onChange={e => setFolio(e.target.value.replace(/\D/g,''))} />
                            </div>
                            <div className={styles.grid2}>
                                <div className={styles.inputWrap}>
                                    <div className={styles.labelRow}>
                                        <label className={styles.fieldLabel}>PROJECT START DATE</label>
                                    </div>
                                    <input type="date" className={styles.hwInput}
                                        value={projectStartDate}
                                        onChange={e => setProjectStartDate(e.target.value)} />
                                    <span className={styles.fieldHint}>Auto-filled with today. Edit if the project actually started earlier.</span>
                                </div>
                                <div className={styles.inputWrap}>
                                    <div className={styles.labelRow}>
                                        <label className={styles.fieldLabel}>TITLE ISSUE DATE (OPTIONAL)</label>
                                    </div>
                                    <input type="date" className={styles.hwInput}
                                        value={titleIssueDate}
                                        onChange={e => setTitleIssueDate(e.target.value)} />
                                    <span className={styles.fieldHint}>Leave blank if not yet received. Can be backdated.</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── OWNERS ── */}
                <div className={styles.hwPanel}>
                    <DrawerHeader label="OWNERS" isOpen={drawers.owners} onClick={() => toggleDrawer('owners')}
                        icon={FiUsers} badge={owners.length} />
                    <div className={`${styles.panelBody} ${drawers.owners ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            {owners.map((o, idx) => (
                                <div key={idx} className={styles.ownerBlock}>
                                    <div className={styles.ownerHeader}>
                                        OWNER #{idx + 1} {idx === 0 ? '(PRIMARY)' : '(JOINT)'}
                                        {idx > 0 && (
                                            <button type="button" className={styles.miniTrash}
                                                onClick={() => removeOwner(idx)} aria-label="Remove owner">
                                                <FiTrash2 />
                                            </button>
                                        )}
                                    </div>
                                    <div className={styles.grid2}>
                                        <SmartInput label="FULL NAME" value={o.fullName} showCaps required
                                            error={errors['owner_'+idx+'_name']}
                                            onChange={e => updateOwner(idx, 'fullName', e.target.value.toUpperCase())} />
                                        <PhoneInput value={o.phone} required
                                            fieldError={errors['owner_'+idx+'_phone']}
                                            onChange={v => updateOwner(idx, 'phone', v)}
                                            onBlur={v => handlePhoneBlurCheck(idx, v)}
                                            id={'owner_'+idx+'_phone'} />
                                    </div>
                                    <div className={styles.grid3}>
                                        <SmartInput label="NATIONAL ID (NIN)" value={o.nationalId} showCaps required
                                            error={errors['owner_'+idx+'_nin']}
                                            maxLength={14}
                                            onChange={e => updateOwner(idx, 'nationalId', e.target.value.toUpperCase().replace(/\s/g,''))}
                                            onBlur={e => handleNinBlurCheck(idx, e.target.value)} />
                                        <SmartInput label="EMAIL" value={o.email}
                                            onChange={e => updateOwner(idx, 'email', e.target.value.toLowerCase())} />
                                        <SmartInput label="HOME ADDRESS" value={o.address}
                                            onChange={e => updateOwner(idx, 'address', e.target.value)} />
                                    </div>
                                </div>
                            ))}
                            <button type="button" className={styles.addBtn} onClick={addOwner}>
                                <FiPlusSquare aria-hidden="true" /> ADD JOINT OWNER
                            </button>
                        </div>
                    </div>
                </div>

                {/* ── FINANCIALS — CLEANED UP ── */}
                <div className={styles.hwPanel}>
                    <DrawerHeader label="FINANCIALS" isOpen={drawers.finance} onClick={() => toggleDrawer('finance')} icon={FiCreditCard} />
                    <div className={`${styles.panelBody} ${drawers.finance ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            <div className={styles.grid3}>
                                <CurrencyInput label="TOTAL COST" value={totalCost} required
                                    error={errors.totalCost}
                                    onChange={setTotalCost} id="totalCost" />
                                <CurrencyInput label="INITIAL PAYMENT" value={initialPayment}
                                    onChange={setInitialPayment} id="initialPayment" />
                                <div className={styles.inputWrap}>
                                    <div className={styles.labelRow}>
                                        <label className={styles.fieldLabel}>AMOUNT OWED</label>
                                        <span className={styles.capsBadge} style={{ background: 'rgba(6,182,212,0.15)', color:'#06b6d4' }}>AUTO</span>
                                    </div>
                                    <div className={styles.diagBox} style={{color: arrears > 0 ? '#fca5a5' : '#22c55e'}}>
                                        UGX {arrears >= 0 ? arrears.toLocaleString() : 0}
                                    </div>
                                </div>
                            </div>

                            {/* BACKLOG STATUS — single clean toggle */}
                            <div className={styles.modeRow}>
                                <label>BACKLOG STATUS</label>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    <button type="button"
                                        className={!isBacklog ? styles.toggleLegacy : styles.toggleStandard}
                                        onClick={() => setIsBacklog(false)}>
                                        ✓ STANDARD — NOT BACKLOG
                                    </button>
                                    <button type="button"
                                        className={isBacklog ? styles.toggleLegacy : styles.toggleStandard}
                                        style={isBacklog ? { borderColor:'#ef4444', color:'#ef4444', background:'rgba(239,68,68,0.12)' } : {}}
                                        onClick={() => setIsBacklog(true)}>
                                        ⚠ ENTER AS BACKLOG
                                    </button>
                                </div>
                                {isBacklog && (
                                    <div className={styles.backlogFeeNote}>
                                        Storage fees accumulate monthly until balance is cleared.
                                    </div>
                                )}
                            </div>

                            {/* BACKLOG FEE CONFIG -- only visible when entering as backlog */}
                            {isBacklog && (
                                <div className={styles.backlogFeeConfig}>
                                    <div className={styles.backlogFeeConfigTitle}>
                                        BACKLOG FEE CONFIGURATION
                                    </div>
                                    <div className={styles.grid2} style={{marginBottom: 12}}>
                                        <div className={styles.inputWrap}>
                                            <div className={styles.labelRow}>
                                                <label className={styles.fieldLabel}>DATE OF SURVEY</label>
                                            </div>
                                            <input
                                                type="date"
                                                className={styles.hwInput}
                                                value={surveyDate}
                                                onChange={e => setSurveyDate(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <div className={styles.grid2} style={{marginBottom: 0}}>
                                        <CurrencyInput
                                            label="MONTHLY STORAGE FEE (UGX)"
                                            value={monthlyStorageFee}
                                            onChange={setMonthlyStorageFee}
                                            id="monthlyFee"
                                        />
                                        <CurrencyInput
                                            label="INITIAL ACCUMULATED FEES (UGX)"
                                            value={initialStorageFee}
                                            onChange={setInitialStorageFee}
                                            id="initialStorageFee"
                                        />
                                    </div>
                                    <div className={styles.backlogFeeHint}>
                                        Set initial fees if this title was entered late into the system
                                        (e.g. was in backlog for 3 months before being registered here).
                                        Leave at 0 if starting fresh.
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* ── STAGES (Phase 4B) -- hidden for Legacy Receivables (Section 17.6) ── */}
                {!isLegacyMode && (
                <div className={styles.hwPanel}>
                    <DrawerHeader label="STAGES" isOpen={drawers.stages} onClick={() => toggleDrawer('stages')}
                        icon={FiCheckSquare} badge={selectedStageCount || undefined} />
                    <div className={`${styles.panelBody} ${drawers.stages ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            <div style={{ marginBottom: 10, fontFamily: "'DM Sans',sans-serif", fontSize: 11,
                                fontWeight: 700, color: 'rgba(255,255,255,0.4)' }}>
                                Optional -- pick which stages apply to this plot. Costs default from the master
                                checklist and can be edited per plot. You can also add stages later from the folder.
                            </div>
                            {stageTemplates.map(t => {
                                const checked = !!checkedStages[t.id];
                                return (
                                    <div key={t.id} style={{ marginBottom: 8 }}>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer',
                                            fontFamily: "'DM Sans',sans-serif", fontSize: 12, fontWeight: 800, color: '#fff' }}>
                                            <input type="checkbox" checked={checked}
                                                onChange={e => setCheckedStages(prev => ({ ...prev, [t.id]: e.target.checked }))}
                                                style={{ width: 17, height: 17 }} />
                                            <span style={{ flex: 1 }}>{t.stageName}</span>
                                        </label>
                                        {checked && (
                                            <div style={{ display: 'flex', gap: 8, marginTop: 6, marginLeft: 27, flexWrap: 'wrap' }}>
                                                <input type="number"
                                                    value={stageCosts[t.id] !== undefined ? stageCosts[t.id] : String(t.defaultCost || 0)}
                                                    onChange={e => setStageCosts(prev => ({ ...prev, [t.id]: e.target.value }))}
                                                    placeholder="Cost (UGX)"
                                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                                        padding: '7px 10px', fontFamily: "'Space Mono',monospace", fontWeight: 700,
                                                        fontSize: 12, color: '#1a2e30', width: 140 }} />
                                                <input type="text"
                                                    value={stageNotes[t.id] || ''}
                                                    onChange={e => setStageNotes(prev => ({ ...prev, [t.id]: e.target.value }))}
                                                    placeholder="Notes (optional)"
                                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                                        padding: '7px 10px', fontFamily: "'DM Sans',sans-serif", fontWeight: 700,
                                                        fontSize: 12, color: '#1a2e30', flex: 1, minWidth: 140 }} />
                                            </div>
                                        )}
                                    </div>
                                );
                            })}

                            {customStages.length > 0 && (
                                <div style={{ marginTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10 }}>
                                    {customStages.map((cs, i) => (
                                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                            <span style={{ flex: 1, fontFamily: "'DM Sans',sans-serif", fontSize: 12,
                                                fontWeight: 800, color: '#EE8C3A' }}>{cs.name}</span>
                                            <span style={{ fontFamily: "'Space Mono',monospace", fontSize: 11,
                                                color: 'rgba(255,255,255,0.5)' }}>UGX {Number(cs.cost || 0).toLocaleString()}</span>
                                            <button type="button" onClick={() => setCustomStages(prev => prev.filter((_, j) => j !== i))}
                                                style={{ background: 'transparent', border: 'none', color: '#ef4444',
                                                    cursor: 'pointer', fontSize: 14, padding: 4 }}>
                                                <FiX />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                                <input type="text" value={newCustomName} onChange={e => setNewCustomName(e.target.value)}
                                    placeholder="Custom stage name"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '8px 12px', fontFamily: "'DM Sans',sans-serif", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', flex: 1, minWidth: 160 }} />
                                <input type="number" value={newCustomCost} onChange={e => setNewCustomCost(e.target.value)}
                                    placeholder="Cost"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '8px 12px', fontFamily: "'Space Mono',monospace", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', width: 120 }} />
                                <button type="button" onClick={() => {
                                        if (!newCustomName.trim()) return;
                                        setCustomStages(prev => [...prev, { name: newCustomName.trim(), cost: Number(newCustomCost) || 0 }]);
                                        setNewCustomName('');
                                        setNewCustomCost('');
                                    }}
                                    style={{ background: 'rgba(238,140,58,0.15)', border: '1.5px solid rgba(238,140,58,0.4)',
                                        color: '#EE8C3A', borderRadius: 6, padding: '8px 16px', fontFamily: "'DM Sans',sans-serif",
                                        fontWeight: 900, fontSize: 11, textTransform: 'uppercase', cursor: 'pointer',
                                        whiteSpace: 'nowrap' }}>
                                    + ADD
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                )}

                {/* ── DOCUMENTS ── */}
                <div className={styles.splitGrid}>
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')}
                            icon={FiUploadCloud} badge={fileQueue.length || undefined} />
                        <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                <div className={`${styles.vaultWrapper} ${errors.docs ? styles.vaultError : ''}`}>
                                    <div className={styles.fileDisplay}>
                                        {fileQueue.length === 0 ? (
                                            <div className={styles.emptyState}>
                                                <FiUploadCloud className={styles.emptyIcon} aria-hidden="true" />
                                                <span>No files selected</span>
                                            </div>
                                        ) : fileQueue.map((f, i) => {
                                            const isPDF = f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf');
                                            const previewUrl = !isPDF ? URL.createObjectURL(f) : null;
                                            return (
                                            <div key={i} className={styles.fileTag}>
                                                <a
                                                    href={isPDF ? '#' : previewUrl}
                                                    target={isPDF ? undefined : '_blank'}
                                                    rel="noreferrer"
                                                    className={styles.fileClickable}
                                                    onClick={isPDF ? (e) => {
                                                        e.preventDefault();
                                                        const url = URL.createObjectURL(f);
                                                        window.open(url, '_blank');
                                                        setTimeout(() => URL.revokeObjectURL(url), 5000);
                                                    } : undefined}
                                                    title={`Open ${f.name}`}
                                                >
                                                    <span className={styles.fileName}>{isPDF ? '📄 ' : '🖼 '}{f.name}</span>
                                                </a>
                                                <button type="button" className={styles.removeFile}
                                                    onClick={() => setFileQueue(prev => prev.filter((_,j) => j !== i))}>
                                                    <FiX />
                                                </button>
                                            </div>
                                            );
                                        })}
                                    </div>
                                    <button type="button" className={styles.uploadBtn}
                                        onClick={() => fileInputRef.current?.click()}>
                                        <FiUploadCloud aria-hidden="true" /> SELECT SCANS
                                    </button>
                                    <input ref={fileInputRef} type="file" multiple
                                        accept=".pdf,.jpg,.jpeg,.png,.webp"
                                        style={{ display: 'none' }}
                                        onChange={e => {
                                const files = e.target.files;
                                if (files && files.length > 0) {
                                    addFiles(files);
                                }
                                // Reset so same file can be selected again
                                setTimeout(() => { e.target.value = ''; }, 100);
                            }} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ── NOTES ── */}
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="NOTES" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')}
                            icon={FiInfo} badge={notesList.length || undefined} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                <div className={styles.notebookTimeline}>
                                    {notesList.length === 0 && (
                                        <div className={styles.emptyState} style={{ padding: '20px 0' }}>
                                            <FiInfo className={styles.emptyIcon} />
                                            <span>No notes added yet</span>
                                        </div>
                                    )}
                                    {notesList.map((note, i) => (
                                        <div key={i} className={styles.ruledNote}>
                                            <div className={styles.noteMeta}>
                                                <span className={styles.noteTime}>NOTE {i + 1}</span>
                                                <div className={styles.actionBlock}>
                                                    <button type="button" className={styles.iconBtn}
                                                        onClick={() => { setEditingNoteIdx(i); setNoteModalText(note); setNoteModalOpen(true); }}>
                                                        <FiEdit3 className={styles.editIcon} />
                                                    </button>
                                                    <button type="button" className={styles.iconBtn}
                                                        onClick={() => setNotesList(prev => prev.filter((_, j) => j !== i))}>
                                                        <FiTrash2 className={styles.redIcon} />
                                                    </button>
                                                </div>
                                            </div>
                                            <p className={styles.noteContent}>{note}</p>
                                        </div>
                                    ))}
                                </div>
                                <button type="button" className={styles.addNoteBtn}
                                    onClick={() => { setEditingNoteIdx(null); setNoteModalText(''); setNoteModalOpen(true); }}>
                                    + ADD NOTE
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── SUBMIT ── */}
                <div className={styles.submitSection}>
                    <button type="button" className={styles.duplicateBtn}
                        onClick={handleDuplicatePlot} disabled={saving}
                        title="Copy all fields except Plot ID to quickly register a similar plot">
                        <FiCopy aria-hidden="true" />
                        DUPLICATE PLOT
                    </button>
                    <button type="button" className={styles.primaryCommitBtn}
                        onClick={handleSubmit} disabled={saving}>
                        <FiSend aria-hidden="true" />
                        {saving ? 'SAVING...' : 'SAVE NEW PLOT'}
                    </button>
                </div>
            </div>

            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="New Plot Registration"
            />

            {/* NOTE DISCARD CONFIRM MODAL */}
            <IntakeConfirmModal state={noteConfirmState} onAnswer={handleNoteAnswer} />

            {/* NOTE MODAL */}
            {noteModalOpen && (
                <div className={styles.noteModalOverlay} onClick={async () => {
                    if (noteModalText.trim() !== '') {
                        const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                        if (!ok) return;
                    }
                    setNoteModalOpen(false);
                    setNoteModalText('');
                }}>
                    <div className={styles.noteModalBox} onClick={e => e.stopPropagation()}>
                        <div className={styles.noteModalHeader}>
                            <span>{editingNoteIdx !== null ? 'EDIT NOTE' : 'ADD NOTE'}</span>
                            <button type="button" className={styles.noteModalClose} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>
                                <FiX />
                            </button>
                        </div>
                        <textarea
                            className={styles.noteModalArea}
                            value={noteModalText}
                            onChange={e => setNoteModalText(e.target.value)}
                            placeholder="Enter note (e.g. client visited in person, documents pending...)"
                            autoFocus
                        />
                        <div className={styles.noteModalFooter}>
                            <button type="button" className={styles.noteModalCancel} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>
                                CANCEL
                            </button>
                            <button type="button" className={styles.noteModalSave} onClick={() => {
                                if (!noteModalText.trim()) return;
                                if (editingNoteIdx !== null) {
                                    setNotesList(prev => prev.map((n, i) => i === editingNoteIdx ? noteModalText.trim() : n));
                                } else {
                                    setNotesList(prev => [...prev, noteModalText.trim()]);
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                                setEditingNoteIdx(null);
                            }}>
                                SAVE NOTE
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default IntakePage;