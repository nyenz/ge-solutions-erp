// PATH: erp-frontend/src/components/ui/CornerDecor.jsx
import React from 'react';
import styles from './CornerDecor.module.css';

/**
 * REUSABLE UI ACCENT: CornerDecor
 * hideTop=true renders ONLY the bottom brackets + bottom pins
 * (used by collapsible sections so decor sits at the expanded foot).
 */
const CornerDecor = ({ hidePins = false, hideTop = false }) => {
    return (
        <>
            {!hideTop && <div className={`${styles.cornerAccent} ${styles.topLeft}`}></div>}
            {!hideTop && <div className={`${styles.cornerAccent} ${styles.topRight}`}></div>}
            <div className={`${styles.cornerAccent} ${styles.bottomLeft}`}></div>
            <div className={`${styles.cornerAccent} ${styles.bottomRight}`}></div>

            {!hidePins && !hideTop && (
                <div className={`${styles.pins} ${styles.top}`}>
                    {[...Array(4)].map((_, i) => <div key={i} className={styles.pin}></div>)}
                </div>
            )}
            {!hidePins && (
                <div className={`${styles.pins} ${styles.bottom}`}>
                    {[...Array(4)].map((_, i) => <div key={i} className={styles.pin}></div>)}
                </div>
            )}
        </>
    );
};

export default CornerDecor;
