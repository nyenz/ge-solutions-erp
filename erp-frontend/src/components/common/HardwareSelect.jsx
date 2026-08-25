// PATH: erp-frontend/src/components/common/HardwareSelect.jsx
import React, { useState, useRef, useEffect } from 'react';
import { FiChevronDown } from 'react-icons/fi';
import styles from './HardwareSelect.module.css';

const HardwareSelect = ({ label, options, value, onChange, required = false, placeholder = '', compact = false }) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className={`${styles.fieldWrapper} ${isOpen ? styles.openWrapper : ''} ${compact ? styles.compactWrapper : ''}`} ref={containerRef}>
            {label && (
                <label className={styles.label}>
                    {label}
                    {required && <span className={styles.requiredMark}>*</span>}
                </label>
            )}
            <div className={`${styles.selectBox} ${compact ? styles.compactBox : ''} ${isOpen ? styles.active : ''}`} onClick={() => setIsOpen(!isOpen)}>
                <span className={`${styles.currentValue} ${!value ? styles.placeholder : ''}`}>{value || placeholder}</span>
                <FiChevronDown className={styles.icon} />

                {isOpen && (
                    <div className={styles.dropdown}>
                        {options.map(opt => (
                            <div
                                key={opt}
                                className={`${styles.option} ${value === opt ? styles.selected : ''}`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onChange(opt);
                                    setIsOpen(false);
                                }}
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
