// PATH: erp-frontend/src/components/ui/HardwareField.jsx
import React from 'react';
import styles from './HardwareField.module.css';

/**
 * REUSABLE HARDWARE FIELD (V1 Styling)
 * Implements the literal prototype: hover scaling, glowing dot, and navy typography.
 */
const HardwareField = ({ label, children, fullWidth = false }) => {
    return (
        <div className={`${styles.fieldV1} ${fullWidth ? styles.fullWidth : ''}`}>
            <label className={styles.labelV1}>{label}</label>
            <div className={styles.inputContainer}>
                {children}
            </div>
            {/* THE GLOWING HARDWARE DOT FROM PROTOTYPE */}
            <div className={styles.cornerAccentV1}></div>
        </div>
    );
};

export default HardwareField;