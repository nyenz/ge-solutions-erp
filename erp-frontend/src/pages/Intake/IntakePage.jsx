// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import {
    FiMap, FiUsers, FiCreditCard, FiUploadCloud,
    FiInfo, FiPlusSquare, FiTrash2, FiSend,
    FiCheckCircle, FiAlertCircle, FiAlertTriangle, FiX, FiCheckSquare, FiAlertOctagon
} from 'react-icons/fi';
import landService from '../../services/landService';
import predictionService from '../../services/predictionService';
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
const SmartInput = ({ label, value, onChange, placeholder, suggestions = [], showCaps, required, error, inputMode, maxLength, hint, id }) => {
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
                type="text" value={value} onChange={onChange} placeholder={placeholder}
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
        </div>
    );
};

// ── MAIN COMPONENT ────────────────────────────────────────────────
const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const IntakePage = () => {
    const navigate = useNavigate();
    const { toasts, toast, dismissToast } = useToast();
    const fileInputRef = useRef(null);

    // UNSAVED DATA PROTECTION via window.beforeunload
    // Form is "dirty" if any meaningful field has been touched

    useEffect(() => {
        const handler = (e) => {
            if (isDirty && !saving) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);

    const [saving, setSaving] = useState(false);
    const [drawers, setDrawers] = useState({ plot: true, owners: true, finance: true, docs: false, notes: false });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));

    const [errors, setErrors] = useState({});


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
    const [totalCost,      setTotalCost]      = useState('');
    const [initialPayment, setInitialPayment] = useState('');
    const [isBacklog,      setIsBacklog]      = useState(false);

    // Docs & notes
    const [fileQueue, setFileQueue] = useState([]);
    const [noteText,  setNoteText]  = useState('');

    // isDirty must be defined AFTER all useState hooks to avoid
    // "Cannot access before initialization" error in the minified bundle
    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        noteText.trim() !== '',
    [plotNumber, owners, totalCost, fileQueue, noteText]);

    // Warn on browser refresh / tab close
    useEffect(() => {
        const handleBeforeUnload = (e) => {
            if (isDirty && !saving) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [isDirty, saving]);

    const sg = key => predictionService.getSuggestions(key) || [];

    const validate = () => {
        const e = {};
        if (!plotNumber.trim())        e.plotNumber = 'Required';
        if (!district.trim())          e.district   = 'Required';
        if (!totalCost)                e.totalCost  = 'Required';
        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
        });
        setErrors(e);
        return Object.keys(e).length === 0;
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
                isLegacy: false,
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: noteText.trim() ? [{ content: noteText.trim() }] : [],
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Plot registered successfully!', 'success', 3000);
            setTimeout(() => navigate('/land/projects'), 1800);
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
        setFileQueue(prev => {
            const existing = new Set(prev.map(f => f.name));
            const newFiles = Array.from(files).filter(f => !existing.has(f.name));
            return [...prev, ...newFiles];
        });
    };

    const arrears = (Number(totalCost) || 0) - (Number(initialPayment) || 0);

    return (
        <div className={styles.container}>

            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={saving} />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Plot Registration</h1>
                    <p className={styles.subtitle}>Register a new land title into the system</p>
                </div>
            </header>

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
                                        <SmartInput label="NATIONAL ID (NIN)" value={o.nationalId} showCaps
                                            maxLength={14}
                                            onChange={e => updateOwner(idx, 'nationalId', e.target.value.toUpperCase().replace(/\s/g,''))} />
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
                                        <label className={styles.fieldLabel}>ARREARS</label>
                                        <span className={styles.capsBadge} style={{ background: 'rgba(6,182,212,0.15)', color:'#06b6d4' }}>AUTO</span>
                                    </div>
                                    <div className={styles.diagBox}>
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
                                    <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, fontSize: '0.82rem', color: '#fca5a5' }}>
                                        This plot will immediately start accumulating UGX 50,000 / month storage fees.
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── DOCUMENTS ── */}
                <div className={styles.splitGrid}>
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')}
                            icon={FiUploadCloud} badge={fileQueue.length || undefined} />
                        <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                <div className={styles.vaultWrapper}>
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
                                        onChange={e => { if (e.target.files?.length) addFiles(e.target.files); e.target.value=''; }} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ── NOTES ── */}
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="NOTES" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                <textarea className={styles.notesArea}
                                    value={noteText}
                                    onChange={e => setNoteText(e.target.value)}
                                    placeholder="Add an intake note (e.g. client visited in person, documents pending...)" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── SUBMIT ── */}
                <div className={styles.submitSection}>
                    <button type="button" className={styles.primaryCommitBtn}
                        onClick={handleSubmit} disabled={saving}>
                        <FiSend aria-hidden="true" />
                        {saving ? 'SAVING...' : 'SAVE NEW PLOT'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default IntakePage;