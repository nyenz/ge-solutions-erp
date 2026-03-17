// PATH: erp-frontend/src/components/common/HardwareButton.jsx
import React from 'react';
import { FiLoader } from 'react-icons/fi';
import styles from './HardwareButton.module.css';

const HardwareButton = ({ 
    children, 
    onClick, 
    type = "button", 
    variant = "primary", // primary (orange), glass (translucent), danger (red)
    icon: Icon, 
    loading = false, 
    disabled = false 
}) => {
    return (
        <button 
            type={type}
            className={`${styles.btn} ${styles[variant]}`}
            onClick={onClick}
            disabled={loading || disabled}
        >
            {loading ? (
                <FiLoader className={styles.spin} />
            ) : (
                Icon && <Icon className={styles.icon} />
            )}
            <span className={styles.text}>
                {loading ? "COMMITTING DATA..." : children}
            </span>
            <div className={styles.hoverGlow}></div>
        </button>
    );
};

export default HardwareButton;