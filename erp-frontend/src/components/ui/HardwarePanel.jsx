// PATH: erp-frontend/src/components/ui/HardwarePanel.jsx
import React from 'react';
import CornerDecor from './CornerDecor';
import styles from './HardwarePanel.module.css';

const HardwarePanel = ({ title, icon: Icon, children, variant = "dark" }) => {
    return (
        <section className={`${styles.panel} ${styles[variant]}`}>
            {/* INJECTS BRACKETS AND PINS AUTOMATICALLY */}
            <CornerDecor hidePins={variant === "light"} />
            
            {(title || Icon) && (
                <div className={styles.header}>
                    {Icon && <Icon className={styles.icon} />}
                    {title && <h2 className={styles.title}>{title}</h2>}
                </div>
            )}

            <div className={styles.content}>
                {children}
            </div>
        </section>
    );
};

export default HardwarePanel;