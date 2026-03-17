// PATH: erp-frontend/src/components/common/HardwareSelect.jsx
import React, { useState, useRef, useEffect } from 'react';
import { FiChevronDown } from 'react-icons/fi';
import styles from './HardwareSelect.module.css';

const HardwareSelect = ({ label, options, value, onChange }) => {
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
        /* FIXED: Added dynamic z-index class when open to prevent clipping */
        <div className={`${styles.fieldWrapper} ${isOpen ? styles.openWrapper : ''}`} ref={containerRef}>
            <label className={styles.label}>{label}</label>
            <div className={`${styles.selectBox} ${isOpen ? styles.active : ''}`} onClick={() => setIsOpen(!isOpen)}>
                <span className={styles.currentValue}>{value}</span>
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