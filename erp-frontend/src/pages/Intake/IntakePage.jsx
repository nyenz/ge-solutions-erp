// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
    FiMap, FiUsers, FiCreditCard, FiUploadCloud, FiShield,
    FiPlus, FiTrash2, FiInfo, FiX, FiAlertTriangle, FiEye, FiCopy,
    FiChevronDown, FiCheckSquare, FiAlertCircle, FiBookmark
} from 'react-icons/fi';
import HardwareModal from '../../components/common/HardwareModal';
import landService from '../../services/landService';
import predictionService from '../../services/predictionService';
import styles from './IntakePage.module.css';

/**
 * GOLDEN SEED - INTELLIGENT INTAKE TERMINAL (V6)
 * Full NYENZ ERP style compliance — zero browser-default UI anywhere.
 */

// ─────────────────────────────────────────────
// TOAST SYSTEM
// ─────────────────────────────────────────────
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

const TOAST_ICONS = {
    success: <FiCheckSquare aria-hidden="true" />,
    error:   <FiAlertCircle aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo aria-hidden="true" />,
};

const ToastContainer = ({ toasts, onDismiss }) => {
    // Portal: mounts directly on document.body so transform/filter
    // on any ancestor cannot trap the fixed positioning.
    if (typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles[`toast_${t.type}`]}`} role="alert">
                    <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
                    <span className={styles.toastMsg}>{t.message}</span>
                    <button className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss notification">
                        <FiX aria-hidden="true" />
                    </button>
                </div>
            ))}
        </div>,
        document.body
    );
};

// ─────────────────────────────────────────────
// SAVING OVERLAY
// ─────────────────────────────────────────────
const SavingOverlay = ({ visible }) => {
    if (!visible || typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.savingOverlay} role="status" aria-label="Committing to archive…">
            <div className={styles.savingRing} aria-hidden="true" />
            <span className={styles.savingLabel}>COMMITTING TO ARCHIVE...</span>
        </div>,
        document.body
    );
};

// ─────────────────────────────────────────────
// SKELETON LOADER
// ─────────────────────────────────────────────
const SkeletonPanel = () => (
    <div className={styles.skeletonPanel} aria-hidden="true">
        <div className={styles.skeletonHeader} />
        <div className={styles.skeletonBody}>
            <div className={styles.skeletonRow} />
            <div className={styles.skeletonRow} />
        </div>
    </div>
);

const SkeletonPage = () => (
    <div className={styles.skeletonPage} aria-busy="true" aria-label="Loading intake form…">
        <div className={styles.skeletonHUD} />
        <SkeletonPanel />
        <SkeletonPanel />
        <SkeletonPanel />
    </div>
);

// ─────────────────────────────────────────────
// DRAWER HEADER
// ─────────────────────────────────────────────
const DrawerHeader = ({ label, isOpen, onClick, icon: IconComponent, count }) => (
    <div
        className={styles.drawerHeader}
        onClick={onClick}
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        aria-label={`${label} section, ${isOpen ? 'collapse' : 'expand'}`}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}
    >
        <div className={styles.drawerTitle}>
            {IconComponent && <IconComponent className={styles.drawerIcon} aria-hidden="true" />}
            {label}
            {count != null && <span className={styles.drawerBadge}>{count}</span>}
        </div>
        <FiChevronDown className={`${styles.chevron} ${isOpen ? styles.rotated : ''}`} aria-hidden="true" />
    </div>
);

// ─────────────────────────────────────────────
// SMART INPUT
// ─────────────────────────────────────────────
const SmartInput = ({
    label, value, onChange, onBlur, required, type = 'text',
    inputMode, maxLength, placeholder, hint,
    fieldError, id, inputRef, tabIndex,
    isPinned, onTogglePin, suggestions, autoUppercase,
    disabled,
}) => {
    const inputId = id || `si_${label.replace(/\s+/g, '_').toLowerCase()}`;
    const errorId = `${inputId}_err`;
    const hintId  = `${inputId}_hint`;
    const listId  = suggestions?.length ? `${inputId}_list` : undefined;

    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}
                    {required && <span className={styles.requiredStar} aria-hidden="true"> *</span>}
                </label>
                {autoUppercase && <span className={styles.capsBadge}>CAPS</span>}
                {maxLength && (
                    <span
                        className={`${styles.charCount} ${value?.length === maxLength ? styles.charCountFull : value?.length > maxLength * 0.5 ? styles.charCountMid : ''}`}
                        aria-hidden="true"
                    >
                        {value?.length ?? 0}/{maxLength}
                    </span>
                )}
                {isPinned != null && (
                    <button
                        type="button"
                        className={`${styles.pinBtn} ${isPinned ? styles.pinned : ''}`}
                        onClick={onTogglePin}
                        aria-label={`${isPinned ? 'Unpin' : 'Pin'} ${label}`}
                        tabIndex={-1}
                    >
                        <FiBookmark aria-hidden="true" />
                    </button>
                )}
            </div>
            <input
                id={inputId}
                ref={inputRef}
                type={type}
                value={value}
                onChange={onChange}
                onBlur={onBlur}
                disabled={disabled}
                required={required}
                maxLength={maxLength}
                placeholder={placeholder}
                inputMode={inputMode}
                tabIndex={tabIndex}
                list={listId}
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''} ${disabled ? styles.hwInputDisabled : ''}`}
                aria-required={required ? 'true' : undefined}
                aria-invalid={fieldError ? 'true' : 'false'}
                aria-describedby={[fieldError ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ') || undefined}
                autoComplete="off"
            />
            {listId && (
                <datalist id={listId}>
                    {suggestions.map(s => <option key={s} value={s} />)}
                </datalist>
            )}
            {hint && !fieldError && <span id={hintId} className={styles.fieldHint}>{hint}</span>}
            {fieldError && <span id={errorId} className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );
};

// ─────────────────────────────────────────────
// SMART SELECT — fully custom, zero browser defaults
// ─────────────────────────────────────────────
const SmartSelect = ({ label, options, value, onChange, tabIndex, id, fieldError }) => {
    const [open, setOpen] = useState(false);
    const wrapRef  = useRef(null);
    const selectId = id || `ss_${label.replace(/\s+/g, '_').toLowerCase()}`;
    const errorId  = `${selectId}_err`;

    // Close on outside click
    useEffect(() => {
        const handler = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    // Keyboard navigation
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); }
        if (e.key === 'Escape') setOpen(false);
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const idx = options.indexOf(value);
            if (idx < options.length - 1) { onChange(options[idx + 1]); }
        }
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            const idx = options.indexOf(value);
            if (idx > 0) { onChange(options[idx - 1]); }
        }
    };

    const select = (opt) => { onChange(opt); setOpen(false); };

    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`} ref={wrapRef}>
            <div className={styles.labelRow}>
                <label id={`${selectId}_label`} className={styles.fieldLabel}>{label}</label>
            </div>
            {/* Trigger button */}
            <div
                id={selectId}
                role="combobox"
                aria-haspopup="listbox"
                aria-expanded={open}
                aria-labelledby={`${selectId}_label`}
                aria-invalid={fieldError ? 'true' : 'false'}
                aria-describedby={fieldError ? errorId : undefined}
                tabIndex={tabIndex ?? 0}
                className={`${styles.selectTrigger} ${open ? styles.selectTriggerOpen : ''} ${fieldError ? styles.hwInputErr : ''}`}
                onClick={() => setOpen(o => !o)}
                onKeyDown={handleKeyDown}
            >
                <span className={styles.selectValue}>{value}</span>
                <FiChevronDown className={`${styles.selectChevron} ${open ? styles.rotated : ''}`} aria-hidden="true" />
            </div>
            {/* Dropdown panel */}
            {open && (
                <ul
                    role="listbox"
                    aria-labelledby={`${selectId}_label`}
                    className={styles.selectDropdown}
                >
                    {options.map(opt => (
                        <li
                            key={opt}
                            role="option"
                            aria-selected={opt === value}
                            className={`${styles.selectOption} ${opt === value ? styles.selectOptionActive : ''}`}
                            onClick={() => select(opt)}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(opt); } }}
                            tabIndex={-1}
                        >
                            {opt === value && <span className={styles.selectTick} aria-hidden="true">✓</span>}
                            {opt}
                        </li>
                    ))}
                </ul>
            )}
            {fieldError && <span id={errorId} className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );
};


// ─────────────────────────────────────────────
// EMAIL INPUT — domain picker + auto-complete
// ─────────────────────────────────────────────
const EMAIL_DOMAINS = ['@gmail.com', '@yahoo.com', '@outlook.com', '@hotmail.com', '@icloud.com'];

const EmailInput = ({ label, value, onChange, tabIndex, fieldError, required, id }) => {
    const [showPicker, setShowPicker] = useState(false);
    const [activeIdx,  setActiveIdx]  = useState(-1);
    const wrapRef  = useRef(null);
    const inputId  = id || 'ei_email';
    const errorId  = `${inputId}_err`;
    const listId   = `${inputId}_list`;

    const localPart = value.includes('@') ? value.split('@')[0] : value;
    const hasAt     = value.includes('@');

    // Show picker only when there's a local part and no @ yet
    const pickerVisible = showPicker && localPart.length > 0 && !hasAt;

    const applyDomain = (domain) => {
        onChange(localPart + domain);
        setShowPicker(false);
        setActiveIdx(-1);
    };

    const handleChange = (e) => {
        const v = e.target.value.toLowerCase().replace(/\s/g, '');
        onChange(v);
        setShowPicker(true);
        setActiveIdx(-1);
    };

    const handleBlur = () => {
        // Delay so click on picker registers first
        setTimeout(() => {
            setShowPicker(false);
            // Auto-append @gmail.com if no domain typed
            if (value && !value.includes('@') && value.trim()) {
                onChange(value.trim() + '@gmail.com');
            }
        }, 160);
    };

    const handleKeyDown = (e) => {
        if (!pickerVisible) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActiveIdx(i => Math.min(i + 1, EMAIL_DOMAINS.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActiveIdx(i => Math.max(i - 1, 0));
        } else if (e.key === 'Enter' && activeIdx >= 0) {
            e.preventDefault();
            applyDomain(EMAIL_DOMAINS[activeIdx]);
        } else if (e.key === 'Escape') {
            setShowPicker(false);
        } else if (e.key === 'Tab' && activeIdx >= 0) {
            e.preventDefault();
            applyDomain(EMAIL_DOMAINS[activeIdx]);
        }
    };

    // Close on outside click
    useEffect(() => {
        const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setShowPicker(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);

    return (
        <div
            className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}
            ref={wrapRef}
        >
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}
                    {required && <span className={styles.requiredStar} aria-hidden="true"> *</span>}
                </label>
                <span className={styles.assistBadge}>@</span>
            </div>
            <div className={styles.inputAssistWrap}>
                <input
                    id={inputId}
                    type="email"
                    value={value}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    onFocus={() => setShowPicker(true)}
                    onKeyDown={handleKeyDown}
                    tabIndex={tabIndex}
                    placeholder="name@domain.com"
                    className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                    aria-required={required ? 'true' : undefined}
                    aria-invalid={fieldError ? 'true' : 'false'}
                    aria-describedby={fieldError ? errorId : undefined}
                    aria-autocomplete="list"
                    aria-controls={pickerVisible ? listId : undefined}
                    aria-activedescendant={activeIdx >= 0 ? `${listId}_${activeIdx}` : undefined}
                    autoComplete="off"
                    autoCapitalize="none"
                    inputMode="email"
                />
                {pickerVisible && (
                    <ul
                        id={listId}
                        role="listbox"
                        aria-label="Email domain suggestions"
                        className={styles.emailPickerList}
                    >
                        {EMAIL_DOMAINS.map((domain, idx) => (
                            <li
                                key={domain}
                                id={`${listId}_${idx}`}
                                role="option"
                                aria-selected={idx === activeIdx}
                                className={`${styles.emailPickerItem} ${idx === activeIdx ? styles.emailPickerActive : ''}`}
                                onMouseDown={() => applyDomain(domain)}
                            >
                                <span className={styles.emailLocalPart}>{localPart}</span>
                                <span className={styles.emailDomain}>{domain}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            {!hasAt && value.length > 0 && !pickerVisible && (
                <span className={styles.fieldHint}>Tab or click a domain · blurs to @gmail.com</span>
            )}
            {fieldError && <span id={errorId} className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );
};

// ─────────────────────────────────────────────
// PHONE INPUT — auto-format, dual-number via "/"
// ─────────────────────────────────────────────
// Single:  0712345678       → blur → 0712 345 678
// Dual:    0712345678/0701234567 → blur → 0712 345 678 / 0701 234 567

const formatSinglePhone = (raw) => {
    const d = raw.replace(/\D/g, '');
    if (!d) return '';
    return [d.slice(0, 4), d.slice(4, 7), d.slice(7, 10)].filter(Boolean).join(' ');
};

const formatPhoneEntry = (raw) => {
    return raw.split('/').map(p => formatSinglePhone(p.trim())).filter(Boolean).join(' / ');
};

const PhoneInput = ({ label, value, onChange, tabIndex, fieldError, required, id }) => {
    const [raw, setRaw] = useState(() => value || '');
    const inputId = id || 'phi_phone';
    const errorId = `${inputId}_err`;
    const hintId  = `${inputId}_hint`;

    const handleChange = (e) => {
        let v = e.target.value;
        v = v.replace(/[^0-9\s/]/g, '');   // digits, spaces, "/" only
        v = v.replace(/[/]+/g, '/');          // no double slashes
        if (v.startsWith('/')) v = v.slice(1);
        setRaw(v);
        onChange(v);
    };

    const handleBlur = () => {
        if (!raw.trim()) return;
        const formatted = formatPhoneEntry(raw);
        if (!formatted) return;
        setRaw(formatted);
        onChange(formatted);
    };

    const isDual = raw.includes('/');

    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}
                    {required && <span className={styles.requiredStar} aria-hidden="true"> *</span>}
                </label>
                <span className={`${styles.assistBadge} ${isDual ? styles.assistBadgeDual : ''}`}>
                    {isDual ? 'DUAL' : 'TEL'}
                </span>
            </div>
            <input
                id={inputId}
                type="tel"
                value={raw}
                onChange={handleChange}
                onBlur={handleBlur}
                tabIndex={tabIndex}
                placeholder="0712 345 678  ·  dual: 0712…/0701…"
                inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                aria-required={required ? 'true' : undefined}
                aria-invalid={fieldError ? 'true' : 'false'}
                aria-describedby={`${hintId}${fieldError ? ' ' + errorId : ''}`}
                autoComplete="tel-national"
            />
            <span id={hintId} className={styles.fieldHint}>
                Auto-spaces on blur · use / for two numbers
            </span>
            {fieldError && <span id={errorId} className={styles.fieldError} role="alert">{fieldError}</span>}
        </div>
    );
};

// ─────────────────────────────────────────────
// NIN INPUT — format guide + char counter
// ─────────────────────────────────────────────
const NINInput = ({ label, value, onChange, tabIndex, id }) => {
    const inputId = id || 'nin_input';
    const MAX = 14;

    // NIN format: CM + 2-digit year + 8 alphanumeric chars
    const handleChange = (e) => {
        const v = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, MAX);
        onChange(v);
    };

    const cntClass = value.length === MAX
        ? styles.charCountFull
        : value.length >= MAX * 0.5
            ? styles.charCountMid
            : '';

    // Detect segment for inline format hint
    const formatHint = () => {
        if (value.length === 0)  return 'CM · YY · XXXXXXXX';
        if (value.length < 2)    return 'Start with CM…';
        if (value.length < 4)    return `${value.slice(0,2)} · YY · XXXXXXXX`;
        if (value.length < 12)   return `${value.slice(0,2)}${value.slice(2,4)} · ${value.slice(4)}…`;
        return `${value.slice(0,4)} ${value.slice(4,12)} ${value.slice(12)}`;
    };

    return (
        <div className={styles.inputWrap}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>{label}</label>
                <span className={styles.capsBadge}>CAPS</span>
                <span className={`${styles.charCount} ${cntClass}`} aria-hidden="true">
                    {value.length}/{MAX}
                </span>
            </div>
            <input
                id={inputId}
                type="text"
                value={value}
                onChange={handleChange}
                tabIndex={tabIndex}
                maxLength={MAX}
                placeholder="CM90XXXXXXXX12"
                className={styles.hwInput}
                aria-describedby={`${inputId}_hint`}
                autoComplete="off"
                autoCapitalize="characters"
            />
            <span id={`${inputId}_hint`} className={styles.ninFormatHint} aria-live="polite">
                {formatHint()}
            </span>
        </div>
    );
};

// AddressInput — plain SmartInput (uniform height, matches all other fields)
const AddressInput = ({ label, value, onChange, tabIndex, id, fieldError }) => (
    <SmartInput
        label={label}
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        tabIndex={tabIndex}
        placeholder="Street, Town, District"
        fieldError={fieldError}
    />
);

// ─────────────────────────────────────────────
// UTILITY
// ─────────────────────────────────────────────
const validateForm = (formData, fileQueue) => {
    const errors = [];
    if (fileQueue.length === 0)             errors.push('AT LEAST 1 DOCUMENT SCAN IS MANDATORY');
    if (!formData.plotNumber?.trim())        errors.push('PLOT NUMBER IS REQUIRED');
    if (!formData.physicalBoxNumber?.trim()) errors.push('PHYSICAL BOX NUMBER IS REQUIRED');
    // Owner validation
    formData.owners.forEach((o, i) => {
        if (!o.fullName?.trim()) errors.push(`OWNER #${i + 1}: LEGAL NAME IS REQUIRED`);
        if (!o.phone?.trim())    errors.push(`OWNER #${i + 1}: PHONE NUMBER IS REQUIRED`);
    });
    // Financial validation
    if (!formData.totalCost?.trim() || parseFloat(formData.totalCost) <= 0)
        errors.push('TOTAL COST IS REQUIRED');
    if (!formData.initialPayment?.trim() || parseFloat(formData.initialPayment) < 0)
        errors.push('INITIAL PAYMENT IS REQUIRED');
    if (formData.totalCost && formData.initialPayment) {
        if (parseFloat(formData.initialPayment) > parseFloat(formData.totalCost))
            errors.push('INITIAL PAYMENT CANNOT EXCEED TOTAL COST');
    }
    return errors;
};

// ─────────────────────────────────────────────
// OWNER MEMORY — localStorage keyed by normalised name
// Saves full owner objects on each submit.
// On name-field keystroke, returns ranked matches.
// ─────────────────────────────────────────────
const OWNER_MEMORY_KEY = 'gs_owner_memory';

const ownerMemory = {
    // Save an owner record (overwrites same name)
    save(owner) {
        if (!owner.fullName?.trim()) return;
        const key = owner.fullName.trim().toUpperCase();
        const store = ownerMemory.all();
        store[key] = {
            fullName:   owner.fullName.trim().toUpperCase(),
            phone:      owner.phone      || '',
            nationalId: owner.nationalId || '',
            address:    owner.address    || '',
            email:      owner.email      || '',
            _saved:     Date.now(),
        };
        localStorage.setItem(OWNER_MEMORY_KEY, JSON.stringify(store));
    },

    // Return all stored records as an object { NAME: {...} }
    all() {
        try { return JSON.parse(localStorage.getItem(OWNER_MEMORY_KEY) || '{}'); }
        catch { return {}; }
    },

    // Search by partial name — returns up to 5 ranked matches
    search(query) {
        const q = query.trim().toUpperCase();
        if (q.length < 2) return [];
        const store = ownerMemory.all();
        return Object.values(store)
            .filter(r => r.fullName.includes(q))
            .sort((a, b) => {
                // Exact start match ranks first, then by recency
                const aStarts = a.fullName.startsWith(q) ? 0 : 1;
                const bStarts = b.fullName.startsWith(q) ? 0 : 1;
                if (aStarts !== bStarts) return aStarts - bStarts;
                return b._saved - a._saved;
            })
            .slice(0, 5);
    },
};

// ─────────────────────────────────────────────
// OWNER NAME INPUT — name field with autofill dropdown
// When the user types ≥2 chars, matching past owners
// appear as suggestions. Selecting one fills ALL fields.
// ─────────────────────────────────────────────
const OwnerNameInput = ({ value, onChange, onAutofill, required, tabIndex, id, fieldError }) => {
    const [matches,   setMatches]   = useState([]);
    const [activeIdx, setActiveIdx] = useState(-1);
    const [open,      setOpen]      = useState(false);
    const wrapRef  = useRef(null);
    const inputId  = id || 'owner_name';
    const listId   = inputId + '_suggestions';

    const handleChange = (e) => {
        const val = e.target.value.toUpperCase();
        onChange(val);
        const results = ownerMemory.search(val);
        setMatches(results);
        setOpen(results.length > 0);
        setActiveIdx(-1);
    };

    const handleKeyDown = (e) => {
        if (!open) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, matches.length - 1)); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)); }
        else if (e.key === 'Enter' && activeIdx >= 0) { e.preventDefault(); apply(matches[activeIdx]); }
        else if (e.key === 'Escape') { setOpen(false); setActiveIdx(-1); }
    };

    const apply = (record) => {
        onAutofill(record);
        setOpen(false);
        setMatches([]);
        setActiveIdx(-1);
    };

    // Highlight the matching portion of the name
    const highlight = (name, query) => {
        const idx = name.toUpperCase().indexOf(query.toUpperCase());
        if (idx === -1 || query.length < 2) return <span>{name}</span>;
        return (
            <span>
                {name.slice(0, idx)}
                <span className={styles.ownerSuggestMatch}>{name.slice(idx, idx + query.length)}</span>
                {name.slice(idx + query.length)}
            </span>
        );
    };

    useEffect(() => {
        const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);

    return (
        <div
            className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}
            ref={wrapRef}
            style={{ position: 'relative' }}
        >
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    Legal Name
                    {required && <span className={styles.requiredStar} aria-hidden="true"> *</span>}
                </label>
                <span className={styles.capsBadge}>CAPS</span>
                {matches.length > 0 && open && (
                    <span className={styles.ownerMemoryBadge}>
                        {matches.length} MATCH{matches.length > 1 ? 'ES' : ''}
                    </span>
                )}
            </div>
            <input
                id={inputId}
                type="text"
                value={value}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                onFocus={() => {
                    const results = ownerMemory.search(value);
                    if (results.length > 0) { setMatches(results); setOpen(true); }
                }}
                tabIndex={tabIndex}
                placeholder="FULL LEGAL NAME"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                autoComplete="off"
                aria-autocomplete="list"
                aria-controls={open ? listId : undefined}
                aria-activedescendant={activeIdx >= 0 ? listId + '_' + activeIdx : undefined}
                aria-required={required ? 'true' : undefined}
                aria-invalid={fieldError ? 'true' : 'false'}
            />
            {open && matches.length > 0 && (
                <ul
                    id={listId}
                    role="listbox"
                    aria-label="Known owners"
                    className={styles.ownerSuggestList}
                >
                    {matches.map((record, idx) => (
                        <li
                            key={record.fullName}
                            id={listId + '_' + idx}
                            role="option"
                            aria-selected={idx === activeIdx}
                            className={`${styles.ownerSuggestItem} ${idx === activeIdx ? styles.ownerSuggestActive : ''}`}
                            onMouseDown={() => apply(record)}
                        >
                            <div className={styles.ownerSuggestName}>
                                {highlight(record.fullName, value)}
                            </div>
                            <div className={styles.ownerSuggestMeta}>
                                {record.phone && <span>{record.phone}</span>}
                                {record.nationalId && <span>{record.nationalId}</span>}
                                {record.email && <span>{record.email}</span>}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
            {fieldError && <span className={styles.fieldError} role="alert">{fieldError}</span>}
            {!fieldError && !open && value.length >= 2 && matches.length === 0 && (
                <span className={styles.fieldHint}>New owner — details will be saved for future entries</span>
            )}
        </div>
    );
};

// ─────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────
const IntakePage = () => {
    const { toasts, toast, dismissToast } = useToast();
    const [pageReady,   setPageReady]   = useState(false);
    const [committing,  setCommitting]  = useState(false);
    const [submitMode,  setSubmitMode]  = useState('');
    const [fileQueue,   setFileQueue]   = useState([]);
    const [fieldErrors, setFieldErrors] = useState({});

    const firstInputRef = useRef(null);
    const fileInputRef   = useRef(null);

    const [drawers, setDrawers] = useState({ tech: true, identity: true, finance: true, vault: true, notes: true });
    const toggleDrawer = (key) => setDrawers(prev => ({ ...prev, [key]: !prev[key] }));

    const [pinned, setPinned] = useState(() => JSON.parse(localStorage.getItem('gs_pins') || '{}'));
    const initialMemory = JSON.parse(localStorage.getItem('gs_pin_memory') || '{}');

    const blankOwner = () => ({ fullName: '', phone: '', nationalId: '', address: '', email: '' });

    const [formData, setFormData] = useState({
        plotNumber:       '',
        tenure:           initialMemory.tenure || 'MAILO',
        blockRoad:        initialMemory.blockRoad || '',
        district:         initialMemory.district || 'WAKISO',
        county:           initialMemory.county || '',
        volume:           initialMemory.volume || '',
        folio:            initialMemory.folio || '',
        instrumentNo:     initialMemory.instrumentNo || '',
        physicalBoxNumber: initialMemory.physicalBoxNumber || '',
        totalCost:        '',
        initialPayment:   '',
        planType:         'Plan 1: Fast-Track (1 Year)',
        weeklyInstallment: 0,
        isLegacy:         false,
        owners:           [blankOwner()],
        notes:            [{ content: '' }],
    });

    const [previewContent, setPreviewContent] = useState({ url: null, type: null, name: '' });
    const [isPreviewOpen,  setIsPreviewOpen]  = useState(false);

    // Page init
    useEffect(() => {
        const t = setTimeout(() => setPageReady(true), 300);
        return () => clearTimeout(t);
    }, []);

    useEffect(() => {
        if (pageReady) setTimeout(() => firstInputRef.current?.focus(), 120);
    }, [pageReady]);

    // Sticky memory sync
    useEffect(() => {
        const memory = {};
        Object.keys(pinned).forEach(key => { if (pinned[key]) memory[key] = formData[key]; });
        localStorage.setItem('gs_pin_memory', JSON.stringify(memory));
    }, [formData, pinned]);

    const togglePin = (field) => {
        const updated = { ...pinned, [field]: !pinned[field] };
        setPinned(updated);
        localStorage.setItem('gs_pins', JSON.stringify(updated));
    };

    // Smart legacy defaults
    useEffect(() => {
        if (formData.isLegacy && !formData.totalCost) {
            setFormData(prev => ({ ...prev, totalCost: '2500000', planType: 'Plan 2: Balanced (2 Year)' }));
        }
    }, [formData.isLegacy, formData.totalCost]);

    // Financial engine
    const calculateInstallment = useCallback(() => {
        const cost = parseFloat(formData.totalCost) || 0;
        const init = parseFloat(formData.initialPayment) || 0;
        const remaining = cost - init;
        if (remaining <= 0) return 0;
        const years = formData.planType.includes('2 Year') ? 2 : formData.planType.includes('3 Year') ? 3 : 1;
        return Math.ceil(remaining / (years * 39));
    }, [formData.totalCost, formData.initialPayment, formData.planType]);

    useEffect(() => {
        setFormData(prev => ({ ...prev, weeklyInstallment: calculateInstallment() }));
    }, [calculateInstallment]);

    // Owner helpers
    const updateOwner = (idx, field, val) => {
        const updated = [...formData.owners];
        if (field === 'fullName')   val = val.toUpperCase();
        if (field === 'email')      val = val.toLowerCase().replace(/\s/g, '');
        // phone: PhoneInput passes already-formatted string — pass through as-is
        if (field === 'nationalId') val = val.toUpperCase().replace(/\s/g, '');
        updated[idx][field] = val;
        setFormData(p => ({ ...p, owners: updated }));
    };
    // Autofill all owner fields from memory record
    const autofillOwner = (idx, record) => {
        const updated = formData.owners.map((o, i) => i === idx ? {
            fullName:   record.fullName,
            phone:      record.phone,
            nationalId: record.nationalId,
            address:    record.address,
            email:      record.email,
        } : o);
        setFormData(p => ({ ...p, owners: updated }));
        // Clear any existing errors for this owner
        setFieldErrors(prev => {
            const next = { ...prev };
            delete next[`owner_${idx}_fullName`];
            delete next[`owner_${idx}_phone`];
            return next;
        });
        toast(`OWNER DATA RESTORED: ${record.fullName}`, 'success', 3000);
    };

    // blurPhone removed — PhoneInput handles formatting internally
    const addOwner    = () => setFormData(p => ({ ...p, owners: [...p.owners, blankOwner()] }));
    const removeOwner = (idx) => {
        setFormData(p => ({ ...p, owners: p.owners.filter((_, i) => i !== idx) }));
        toast(`OWNER #${idx + 1} REMOVED`, 'warn', 3000);
    };

    // Preview
    const triggerPreview = (file) => {
        const url = URL.createObjectURL(file);
        setPreviewContent({ url, type: file.type, name: file.name });
        setIsPreviewOpen(true);
    };
    const closePreview = () => {
        if (previewContent.url) URL.revokeObjectURL(previewContent.url);
        setPreviewContent({ url: null, type: null, name: '' });
        setIsPreviewOpen(false);
    };

    const removeFile = (idx) => {
        setFileQueue(prev => prev.filter((_, i) => i !== idx));
        toast('DOCUMENT REMOVED', 'warn', 3000);
    };

    // Submission
    const executeSubmit = useCallback(async (mode) => {
        const errors = validateForm(formData, fileQueue);
        if (errors.length) {
            const fe = {};
            if (fileQueue.length === 0)              fe.vault             = 'At least 1 scan required';
            if (!formData.plotNumber?.trim())         fe.plotNumber        = 'Required';
            if (!formData.physicalBoxNumber?.trim())  fe.physicalBoxNumber = 'Required';
            if (!formData.totalCost?.trim() || parseFloat(formData.totalCost) <= 0)
                                                      fe.totalCost         = 'Total cost is required';
            if (!formData.initialPayment?.trim() || parseFloat(formData.initialPayment) < 0)
                                                      fe.initialPayment    = 'Initial payment is required';
            else if (formData.totalCost && formData.initialPayment &&
                parseFloat(formData.initialPayment) > parseFloat(formData.totalCost))
                                                      fe.initialPayment    = 'Cannot exceed total cost';
            formData.owners.forEach((o, i) => {
                if (!o.fullName?.trim()) fe[`owner_${i}_fullName`] = 'Required';
                if (!o.phone?.trim())   fe[`owner_${i}_phone`]    = 'Required';
            });
            setFieldErrors(fe);
            toast(errors[0], 'error', 6000);
            return;
        }
        setFieldErrors({});
        setCommitting(true);
        setSubmitMode(mode);
        try {
            await landService.createAtomicEntry(formData, fileQueue);
            predictionService.learn(formData);
            // Save each owner to memory for future autofill
            formData.owners.forEach(o => ownerMemory.save(o));

            if (mode === 'DUPLICATE') {
                setFormData(prev => ({ ...prev, plotNumber: '', notes: [{ content: '' }] }));
                setFileQueue([]);
                toast('PLOT SECURED — CONTEXT RETAINED FOR NEXT ENTRY', 'success');
            } else {
                const memory = JSON.parse(localStorage.getItem('gs_pin_memory') || '{}');
                setFormData({
                    plotNumber: '', tenure: memory.tenure || 'MAILO',
                    blockRoad: memory.blockRoad || '', district: memory.district || 'WAKISO',
                    county: memory.county || '', volume: memory.volume || '',
                    folio: memory.folio || '', instrumentNo: memory.instrumentNo || '',
                    physicalBoxNumber: memory.physicalBoxNumber || '',
                    totalCost: '', initialPayment: '',
                    planType: 'Plan 1: Fast-Track (1 Year)',
                    weeklyInstallment: 0, isLegacy: false,
                    owners: [blankOwner()], notes: [{ content: '' }],
                    ...memory,
                });
                setFileQueue([]);
                toast('SECURE COMMIT SUCCESSFUL — ARCHIVE CLEANED', 'success');
            }
            setTimeout(() => firstInputRef.current?.focus(), 120);
        } catch (err) {
            console.error(err);
            toast(`COMMIT FAILED: ${err.message || 'UNKNOWN SYSTEM FAULT'}`, 'error', 8000);
        } finally {
            setCommitting(false);
            setSubmitMode('');
        }
    }, [formData, fileQueue, toast]);

    // Hotkey: Ctrl+Enter
    useEffect(() => {
        const handler = (e) => { if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); executeSubmit('CLEAR'); } };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [executeSubmit]);

    // ── Render ────────────────────────────────
    if (!pageReady) return <div className={styles.container}><SkeletonPage /></div>;

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <SavingOverlay visible={committing} />

            {/* ── MASTER HEADER ── */}
            <header className={styles.header}>
                <h1 className={styles.title}>Asset Ingestion Terminal</h1>
                <p className={styles.subtitle}>Continuous Data Flow Enabled | Ctrl+Enter to Commit</p>
            </header>

            <div className={styles.formFlow}>

                {/* ── 1. PLOT DETAILS ── */}
                <section className={styles.hwPanel} aria-label="Plot Details">
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.tech} onClick={() => toggleDrawer('tech')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.tech ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.tech}>
                        <div className={styles.panelInner}>
                            <div className={styles.grid3}>
                                <SmartInput
                                    label="Plot Number / ID" id="intake-plot-id"
                                    value={formData.plotNumber}
                                    onChange={e => setFormData({ ...formData, plotNumber: e.target.value.toUpperCase() })}
                                    required autoUppercase inputRef={firstInputRef} tabIndex={1}
                                    fieldError={fieldErrors.plotNumber}
                                />
                                <SmartSelect
                                    label="Land Tenure"
                                    options={['MAILO', 'FREEHOLD', 'LEASEHOLD', 'CUSTOMARY']}
                                    value={formData.tenure}
                                    onChange={v => setFormData({ ...formData, tenure: v })}
                                    tabIndex={2}
                                />
                                <SmartInput
                                    label="Physical Box No." value={formData.physicalBoxNumber}
                                    onChange={e => setFormData({ ...formData, physicalBoxNumber: e.target.value.toUpperCase() })}
                                    required autoUppercase tabIndex={3}
                                    isPinned={pinned.physicalBoxNumber} onTogglePin={() => togglePin('physicalBoxNumber')}
                                    suggestions={predictionService.getSuggestions('physicalBoxNumber')}
                                    fieldError={fieldErrors.physicalBoxNumber}
                                />
                            </div>
                            <div className={styles.grid3}>
                                <SmartInput
                                    label="District" value={formData.district}
                                    onChange={e => setFormData({ ...formData, district: e.target.value.toUpperCase() })}
                                    autoUppercase tabIndex={4}
                                    isPinned={pinned.district} onTogglePin={() => togglePin('district')}
                                    suggestions={predictionService.getSuggestions('district')}
                                />
                                <SmartInput
                                    label="County / Division" value={formData.county}
                                    onChange={e => setFormData({ ...formData, county: e.target.value.toUpperCase() })}
                                    autoUppercase tabIndex={5}
                                    isPinned={pinned.county} onTogglePin={() => togglePin('county')}
                                    suggestions={predictionService.getSuggestions('county')}
                                />
                                <SmartInput
                                    label="Block / Road" value={formData.blockRoad}
                                    onChange={e => setFormData({ ...formData, blockRoad: e.target.value.toUpperCase() })}
                                    autoUppercase tabIndex={6}
                                    isPinned={pinned.blockRoad} onTogglePin={() => togglePin('blockRoad')}
                                    suggestions={predictionService.getSuggestions('blockRoad')}
                                />
                            </div>
                            <div className={styles.grid3}>
                                <SmartInput
                                    label="Instrument No." value={formData.instrumentNo}
                                    onChange={e => setFormData({ ...formData, instrumentNo: e.target.value.toUpperCase() })}
                                    autoUppercase tabIndex={7}
                                    isPinned={pinned.instrumentNo} onTogglePin={() => togglePin('instrumentNo')}
                                />
                                <SmartInput
                                    label="Volume" value={formData.volume}
                                    onChange={e => setFormData({ ...formData, volume: e.target.value.replace(/\D/g, '') })}
                                    inputMode="numeric" hint="Numbers only" tabIndex={8}
                                    isPinned={pinned.volume} onTogglePin={() => togglePin('volume')}
                                />
                                <SmartInput
                                    label="Folio" value={formData.folio}
                                    onChange={e => setFormData({ ...formData, folio: e.target.value.replace(/\D/g, '') })}
                                    inputMode="numeric" hint="Numbers only" tabIndex={9}
                                    isPinned={pinned.folio} onTogglePin={() => togglePin('folio')}
                                />
                            </div>
                        </div>
                    </div>
                </section>

                {/* ── 2. OWNERS ── */}
                <section className={styles.hwPanel} aria-label="Owners">
                    <DrawerHeader
                        label="OWNERS" isOpen={drawers.identity}
                        onClick={() => toggleDrawer('identity')} icon={FiUsers}
                        count={formData.owners.length}
                    />
                    <div className={`${styles.panelBody} ${drawers.identity ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.identity}>
                        <div className={styles.panelInner}>
                            <div role="list">
                                {formData.owners.map((owner, i) => (
                                    <article key={i} className={styles.ownerBlock} role="listitem">
                                        <div className={styles.ownerHeader}>
                                            ENTITY #{i + 1} {i === 0 && '(PRIMARY)'}
                                        </div>
                                        <div className={styles.grid2}>
                                            <PhoneInput
                                                label="Recovery Phone"
                                                value={owner.phone}
                                                onChange={v => updateOwner(i, 'phone', v)}
                                                required tabIndex={10 + i * 5}
                                                id={`owner_${i}_phone`}
                                                fieldError={fieldErrors[`owner_${i}_phone`]}
                                            />
                                            <OwnerNameInput
                                                value={owner.fullName}
                                                onChange={v => updateOwner(i, 'fullName', v)}
                                                onAutofill={record => autofillOwner(i, record)}
                                                required tabIndex={11 + i * 5}
                                                id={`owner_${i}_name`}
                                                fieldError={fieldErrors[`owner_${i}_fullName`]}
                                            />
                                        </div>
                                        <div className={styles.grid3}>
                                            <NINInput
                                                label="National ID / NIN"
                                                value={owner.nationalId}
                                                onChange={v => updateOwner(i, 'nationalId', v)}
                                                tabIndex={12 + i * 5}
                                                id={`owner_${i}_nin`}
                                            />
                                            <AddressInput
                                                label="Home Address"
                                                value={owner.address}
                                                onChange={v => updateOwner(i, 'address', v)}
                                                tabIndex={13 + i * 5}
                                                id={`owner_${i}_address`}
                                            />
                                            <div className={styles.inputWithAction}>
                                                <EmailInput
                                                    label="Email"
                                                    value={owner.email}
                                                    onChange={v => updateOwner(i, 'email', v)}
                                                    tabIndex={14 + i * 5}
                                                    id={`owner_${i}_email`}
                                                />
                                                {i > 0 && (
                                                    <button
                                                        type="button"
                                                        className={styles.miniTrash}
                                                        onClick={() => removeOwner(i)}
                                                        aria-label={`Remove Owner ${i + 1}`}
                                                    >
                                                        <FiTrash2 aria-hidden="true" />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </article>
                                ))}
                            </div>
                            <button
                                type="button" className={styles.addBtn} onClick={addOwner}
                                aria-label="Register an additional joint proprietor"
                            >
                                <FiPlus aria-hidden="true" /> REGISTER JOINT PROPRIETOR
                            </button>
                        </div>
                    </div>
                </section>

                {/* ── 3. FINANCIALS ── */}
                <section className={styles.hwPanel} aria-label="Financials">
                    <DrawerHeader label="FINANCIALS" isOpen={drawers.finance} onClick={() => toggleDrawer('finance')} icon={FiCreditCard} />
                    <div className={`${styles.panelBody} ${drawers.finance ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.finance}>
                        <div className={styles.panelInner}>
                            <div className={styles.grid4}>
                                <SmartInput
                                    label="Total Cost (UGX)"
                                    value={formData.totalCost ? Number(formData.totalCost).toLocaleString() : ''}
                                    onChange={e => setFormData({ ...formData, totalCost: e.target.value.replace(/\D/g, '') })}
                                    required inputMode="numeric" tabIndex={50}
                                    fieldError={fieldErrors.totalCost}
                                />
                                <SmartInput
                                    label="Initial Payment (UGX)"
                                    value={formData.initialPayment ? Number(formData.initialPayment).toLocaleString() : ''}
                                    onChange={e => setFormData({ ...formData, initialPayment: e.target.value.replace(/\D/g, '') })}
                                    inputMode="numeric" tabIndex={51}
                                    fieldError={fieldErrors.initialPayment}
                                />
                                <SmartSelect
                                    label="Payment Plan"
                                    options={['Plan 1: Fast-Track (1 Year)', 'Plan 2: Balanced (2 Year)', 'Plan 3: VIP (3 Year)']}
                                    value={formData.planType}
                                    onChange={v => setFormData({ ...formData, planType: v })}
                                    tabIndex={52}
                                />
                                <div className={styles.diagBox} role="status" aria-label={`Weekly installment: ${formData.weeklyInstallment.toLocaleString()} UGX`}>
                                    <FiInfo aria-hidden="true" />
                                    <span>{formData.weeklyInstallment.toLocaleString()} UGX / WK</span>
                                </div>
                            </div>
                            <div className={styles.modeRow}>
                                <label id="mode-label">Operational Mode:</label>
                                <button
                                    type="button"
                                    className={formData.isLegacy ? styles.toggleLegacy : styles.toggleStandard}
                                    onClick={() => setFormData({ ...formData, isLegacy: !formData.isLegacy })}
                                    aria-pressed={formData.isLegacy}
                                    aria-labelledby="mode-label"
                                >
                                    {formData.isLegacy
                                        ? 'BACKLOG ARCHIVE MODE (Smart Defaults Active)'
                                        : 'STANDARD INTAKE MODE'}
                                </button>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ── 4. DOCUMENTS & NOTES ── */}
                <div className={styles.splitGrid}>

                    {/* DOCUMENTS */}
                    <section className={styles.hwPanel} aria-label="Documents">
                        <DrawerHeader
                            label="DOCUMENTS" isOpen={drawers.vault}
                            onClick={() => toggleDrawer('vault')} icon={FiUploadCloud}
                            count={fileQueue.length || undefined}
                        />
                        <div className={`${styles.panelBody} ${drawers.vault ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.vault}>
                            <div className={styles.panelInner}>
                                <div className={styles.vaultWrapper}>
                                    <div
                                        className={`${styles.fileDisplay} ${fieldErrors.vault ? styles.fileDisplayError : ''}`}
                                        role="list"
                                        aria-label="Attached documents"
                                    >
                                        {fileQueue.length === 0 && (
                                            <div className={styles.emptyState} role="status">
                                                <FiUploadCloud className={styles.emptyIcon} aria-hidden="true" />
                                                <span>NO SCANS ATTACHED</span>
                                            </div>
                                        )}
                                        {fileQueue.map((f, i) => (
                                            <div key={i} className={styles.fileTag} role="listitem">
                                                <button
                                                    type="button" className={styles.fileClickable}
                                                    onClick={() => triggerPreview(f)}
                                                    aria-label={`Preview ${f.name}`}
                                                >
                                                    <FiEye aria-hidden="true" />
                                                    <span className={styles.fileName}>{f.name}</span>
                                                </button>
                                                <button
                                                    type="button" className={styles.removeFile}
                                                    onClick={() => removeFile(i)}
                                                    aria-label={`Remove ${f.name}`}
                                                >
                                                    <FiX aria-hidden="true" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                    {fieldErrors.vault && (
                                        <span className={styles.fieldError} role="alert">{fieldErrors.vault}</span>
                                    )}
                                    <button
                                        type="button"
                                        className={styles.uploadBtn}
                                        onClick={() => fileInputRef.current?.click()}
                                        tabIndex={60}
                                        aria-label="Add document scan"
                                    >
                                        <FiPlus aria-hidden="true" /> ADD DOCUMENT SCAN (PDF / JPG)
                                    </button>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* NOTES */}
                    <section className={styles.hwPanel} aria-label="Notes">
                        <DrawerHeader label="NOTES" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.notes}>
                            <div className={styles.panelInner}>
                                <label htmlFor="intake-notes" className={styles.fieldLabel}>Boundary / Case Notes</label>
                                <textarea
                                    id="intake-notes"
                                    className={styles.notesArea}
                                    placeholder="Add boundary notes, special conditions, or case remarks…"
                                    value={formData.notes[0].content}
                                    onChange={e => setFormData({ ...formData, notes: [{ content: e.target.value }] })}
                                    tabIndex={61}
                                    aria-label="Boundary and case notes"
                                />
                            </div>
                        </div>
                    </section>
                </div>

                {/* ── DUAL SUBMIT WORKSTATION ── */}
                <div className={styles.submitSection}>
                    <div className={styles.dualActionGroup}>
                        <button
                            type="button" className={styles.secondaryCommitBtn}
                            onClick={() => executeSubmit('DUPLICATE')}
                            disabled={committing} tabIndex={70}
                            aria-label="Commit entry and duplicate context for next plot"
                        >
                            {committing && submitMode === 'DUPLICATE'
                                ? 'COMMITTING...'
                                : <><FiCopy aria-hidden="true" /> COMMIT &amp; DUPLICATE FILE</>}
                        </button>
                        <button
                            type="button" className={styles.primaryCommitBtn}
                            onClick={() => executeSubmit('CLEAR')}
                            disabled={committing} tabIndex={71}
                            aria-label="Commit entry and clear form for next plot (Ctrl+Enter)"
                        >
                            {committing && submitMode === 'CLEAR'
                                ? 'COMMITTING...'
                                : <><FiShield aria-hidden="true" /> COMMIT &amp; CLEAR FOR NEXT</>}
                        </button>
                    </div>
                </div>
            </div>

            {/* Global file input — ref-driven, always mounted, never blocks pointer events */}
            <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                onChange={e => {
                    if (!e.target.files?.length) return;
                    const files = Array.from(e.target.files);
                    setFileQueue(prev => [...prev, ...files]);
                    toast(`${files.length} DOCUMENT${files.length > 1 ? 'S' : ''} ATTACHED`, 'success', 3000);
                    e.target.value = '';
                }}
                style={{ display: 'none' }}
                aria-hidden="true"
                tabIndex={-1}
            />

            {/* ── UNIVERSAL VIEWER MODAL ── */}
            <HardwareModal isOpen={isPreviewOpen} onClose={closePreview} title={`VIEWER: ${previewContent.name}`}>
                <div className={styles.previewContainer}>
                    {previewContent.type?.includes('pdf') ? (
                        <iframe src={previewContent.url} title="PDF Preview" className={styles.previewPDF} />
                    ) : (
                        <img src={previewContent.url} alt={`Scan preview of ${previewContent.name}`} className={styles.previewImg} />
                    )}
                    <div className={styles.previewActions}>
                        <button type="button" className={styles.btnDanger} onClick={closePreview} aria-label="Close viewer">
                            <FiX aria-hidden="true" /> CLOSE VIEWER
                        </button>
                    </div>
                </div>
            </HardwareModal>
        </div>
    );
};

export default IntakePage;