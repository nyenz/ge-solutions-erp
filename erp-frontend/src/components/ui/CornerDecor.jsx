// PATH: erp-frontend/src/components/ui/CornerDecor.jsx
import React from 'react';
import styles from './CornerDecor.module.css';

/**
 * REUSABLE UI ACCENT: CornerDecor
 * Standardizes the industrial "Pin & Bracket" look across the ERP.
 * Drop this inside any 'relative' positioned container.
 */
const CornerDecor = ({ hidePins = false }) => {
    return (
        <>
            {/* CORNER BRACKETS */}
            <div className={`${styles.cornerAccent} ${styles.topLeft}`}></div>
            <div className={`${styles.cornerAccent} ${styles.topRight}`}></div>
            <div className={`${styles.cornerAccent} ${styles.bottomLeft}`}></div>
            <div className={`${styles.cornerAccent} ${styles.bottomRight}`}></div>

            {/* BORDER PINS (OPTIONAL) */}
            {!hidePins && (
                <>
                    <div className={`${styles.pins} ${styles.top}`}>
                        {[...Array(4)].map((_, i) => <div key={i} className={styles.pin}></div>)}
                    </div>
                    <div className={`${styles.pins} ${styles.bottom}`}>
                        {[...Array(4)].map((_, i) => <div key={i} className={styles.pin}></div>)}
                    </div>
                </>
            )}
        </>
    );
};

export default CornerDecor;