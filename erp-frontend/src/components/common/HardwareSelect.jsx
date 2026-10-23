// PATH: erp-frontend/src/components/common/HardwareSelect.jsx
// fix210 (David): the list now works from the keyboard like a normal select box -- Tab reaches it, Up/Down move,
// Enter picks, Esc closes -- and typing letters jumps to the matching item (utils/typeAhead.js).
import React, { useState, useRef, useEffect, useLayoutEffect, useId } from 'react';
import { applyFlip } from '../../utils/popFit';   // fix226
import { FiChevronDown } from 'react-icons/fi';
import styles from './HardwareSelect.module.css';
import { useTypeAhead } from '../../utils/typeAhead';

const HardwareSelect = ({ label, options, value, onChange, required = false, placeholder = '', compact = false }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [active, setActive] = useState(-1);
    const containerRef = useRef(null);
    const listRef = useRef(null);
    useLayoutEffect(() => { if (isOpen) applyFlip(containerRef.current, listRef.current); }, [isOpen, options]);   // fix226: never cut off
    const typeAhead = useTypeAhead();
    const listId = useId();
    const current = options.indexOf(value);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // keep the highlighted row in view
    useEffect(() => {
        if (!isOpen || active < 0 || !listRef.current) return;
        const row = listRef.current.querySelector('[data-idx="' + active + '"]');
        if (row && row.scrollIntoView) row.scrollIntoView({ block: 'nearest' });
    }, [isOpen, active]);

    const openList = () => { setActive(current >= 0 ? current : 0); setIsOpen(true); };
    const pick = (opt) => { onChange(opt); setIsOpen(false); };

    const onKeyDown = (e) => {
        const hit = typeAhead(e, options, isOpen ? active : current);
        if (hit >= 0) {
            e.preventDefault();
            if (isOpen) setActive(hit); else onChange(options[hit]);   // closed: a letter picks at once, like a normal select
            return;
        }
        if (!isOpen) {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); openList(); }
            return;
        }
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); setIsOpen(false); }
        else if (e.key === 'ArrowDown') { e.preventDefault(); setActive(i => Math.min(options.length - 1, i + 1)); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(i => Math.max(0, i - 1)); }
        else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (options[active] !== undefined) pick(options[active]); else setIsOpen(false); }
        else if (e.key === 'Tab') setIsOpen(false);
    };

    return (
        <div className={`${styles.fieldWrapper} ${isOpen ? styles.openWrapper : ''} ${compact ? styles.compactWrapper : ''}`} ref={containerRef}>
            {label && (
                <label className={styles.label}>
                    {label}
                    {required && <span className={styles.requiredMark}>*</span>}
                </label>
            )}
            <div className={`${styles.selectBox} ${compact ? styles.compactBox : ''} ${isOpen ? styles.active : ''}`}
                role="combobox" tabIndex={0} aria-haspopup="listbox" aria-expanded={isOpen} aria-controls={isOpen ? listId : undefined}
                aria-label={label || placeholder || undefined}
                onClick={() => (isOpen ? setIsOpen(false) : openList())} onKeyDown={onKeyDown}>
                <span className={`${styles.currentValue} ${!value ? styles.placeholder : ''}`}>{value || placeholder}</span>
                <FiChevronDown className={styles.icon} />

                {isOpen && (
                    <div className={styles.dropdown} role="listbox" id={listId} ref={listRef}>
                        {options.map((opt, i) => (
                            <div
                                key={opt}
                                data-idx={i}
                                role="option"
                                aria-selected={value === opt}
                                className={`${styles.option} ${value === opt ? styles.selected : ''} ${i === active ? styles.optionActive : ''}`}
                                onMouseEnter={() => setActive(i)}
                                onClick={(e) => { e.stopPropagation(); pick(opt); }}
                            >
                                {opt}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default HardwareSelect;
