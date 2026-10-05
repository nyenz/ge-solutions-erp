// PATH: erp-frontend/src/components/common/HardwareInput.jsx
import React, { useState, useRef, useId } from 'react';
import { FiMapPin, FiLoader, FiZap, FiCommand } from 'react-icons/fi';
import styles from './HardwareInput.module.css';

/**
 * GOLDEN SEED - UPGRADED HARDWARE INPUT (V4)
 * Features: Live Filtering (Type "WA" -> "WAKISO") and Visual Shortcuts.
 */
const HardwareInput = ({ 
    label, type = "text", placeholder, value, onChange, name,
    required = false, isPinned = false, onTogglePin = null,
    isLoading = false, tabIndex, suggestions = [],
    // fix181 (15.6d): a real label link, a name and the browser's autocomplete hint (password managers, screen readers)
    id, autoComplete = 'off',
    // fix181 (15.4c): adding "@gmail.com" on blur invented addresses; it is now off unless a page asks for it
    autoSuffix = false,
    onKeyDown, autoCapitalize, spellCheck,
}) => {
    const autoId = useId();
    const inputId = id || autoId;
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [highlight, setHighlight] = useState(false); 
    const wrapperRef = useRef(null);

    // --- INTELLIGENT EVENT HANDLERS ---

    const handleBlur = (e) => {
        let val = e.target.value;
        
        // LOGIC 1: SMART EMAIL SUFFIX
        if (autoSuffix && type === 'email' && val && !val.includes('@')) {
            val = val + '@gmail.com';
            triggerChange(val);
            flashHighlight();
        }

        // Delay closing so click can register
        setTimeout(() => setShowSuggestions(false), 200);
    };

    const handleFocus = () => {
        if (suggestions.length > 0) setShowSuggestions(true);
    };

    const handleChange = (e) => {
        onChange(e);
        // Re-open suggestions if user is typing and we have matches
        if (suggestions.length > 0 && !showSuggestions) {
            setShowSuggestions(true);
        }
    };

    const selectSuggestion = (val) => {
        triggerChange(val);
        setShowSuggestions(false);
        flashHighlight();
    };

    const triggerChange = (newValue) => {
        const event = { target: { value: newValue, name: name } };
        onChange(event);
    };

    const flashHighlight = () => {
        setHighlight(true);
        setTimeout(() => setHighlight(false), 500);
    };

    // --- FILTERING ENGINE (The "Blurry" Matcher) ---
    // Only show suggestions that match what the user has typed so far
    const filteredSuggestions = suggestions.filter(s => 
        !value || s.toUpperCase().includes(value.toUpperCase())
    );

    // --- VISUAL LOGIC ---
    // Show email hint if typing in email field and no '@' yet
    const showEmailHint = autoSuffix && type === 'email' && value && !value.includes('@');
    const needsFullEmail = !autoSuffix && type === 'email' && value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value);

    return (
        <div className={styles.fieldWrapper} ref={wrapperRef}>
            <div className={styles.labelRow}>
                <label className={styles.label} htmlFor={inputId}>
                    {label} {required && <span className={styles.requiredMark}>*</span>}
                </label>
                {onTogglePin && (
                    <button type="button" className={`${styles.pinBtn} ${isPinned ? styles.pinnedActive : ''}`} onClick={onTogglePin} tabIndex="-1">
                        <FiMapPin />
                    </button>
                )}
            </div>

            <div className={`${styles.inputContainer} ${highlight ? styles.flash : ''}`}>
                <input 
                    id={inputId} type={type} name={name} placeholder={placeholder} value={value}
                    onChange={handleChange} onBlur={handleBlur} onFocus={handleFocus} onKeyDown={onKeyDown}
                    required={required} className={styles.input} tabIndex={tabIndex} disabled={isLoading}
                    autoComplete={autoComplete} autoCapitalize={autoCapitalize} spellCheck={spellCheck}
                    aria-describedby={needsFullEmail ? inputId + '-hint' : undefined}
                />
                
                {/* RIGHT-SIDE ICONS */}
                <div className={styles.iconZone}>
                    {isLoading ? (
                        <FiLoader className={styles.loadingSpinner} />
                    ) : highlight ? (
                        <FiZap className={styles.zapIcon} />
                    ) : showEmailHint ? (
                        <div className={styles.ghostHint}>
                            <span>@gmail.com</span> <FiCommand />
                        </div>
                    ) : (
                        <div className={styles.glowCorner}></div>
                    )}
                </div>

                {/* THE INTELLIGENT DROPDOWN (FILTERED) */}
                {showSuggestions && filteredSuggestions.length > 0 && (
                    <div className={styles.suggestionBox}>
                        <div className={styles.suggHeader}>SUGGESTED HISTORY</div>
                        {filteredSuggestions.map((s, i) => (
                            <div key={i} className={styles.suggItem} onMouseDown={() => selectSuggestion(s)}>
                                {/* Highlight the matching part (Simple bolding) */}
                                {s}
                            </div>
                        ))}
                    </div>
                )}
            </div>
            {needsFullEmail && <div id={inputId + '-hint'} className={styles.fieldHint}>Enter the full email address (name@example.com).</div>}
        </div>
    );
};

export default HardwareInput;