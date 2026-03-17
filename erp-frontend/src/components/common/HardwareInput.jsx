// PATH: erp-frontend/src/components/common/HardwareInput.jsx
import React, { useState, useRef } from 'react';
import { FiMapPin, FiLoader, FiZap, FiCommand } from 'react-icons/fi';
import styles from './HardwareInput.module.css';

/**
 * GOLDEN SEED - UPGRADED HARDWARE INPUT (V4)
 * Features: Live Filtering (Type "WA" -> "WAKISO") and Visual Shortcuts.
 */
const HardwareInput = ({ 
    label, type = "text", placeholder, value, onChange, name, 
    required = false, isPinned = false, onTogglePin = null, 
    isLoading = false, tabIndex, suggestions = [] 
}) => {
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [highlight, setHighlight] = useState(false); 
    const wrapperRef = useRef(null);

    // --- INTELLIGENT EVENT HANDLERS ---

    const handleBlur = (e) => {
        let val = e.target.value;
        
        // LOGIC 1: SMART EMAIL SUFFIX
        if (type === 'email' && val && !val.includes('@')) {
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
    const showEmailHint = type === 'email' && value && !value.includes('@');

    return (
        <div className={styles.fieldWrapper} ref={wrapperRef}>
            <div className={styles.labelRow}>
                <label className={styles.label}>
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
                    type={type} name={name} placeholder={placeholder} value={value} 
                    onChange={handleChange} onBlur={handleBlur} onFocus={handleFocus}
                    required={required} className={styles.input} tabIndex={tabIndex} disabled={isLoading}
                    autoComplete="off" 
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
        </div>
    );
};

export default HardwareInput;