// PATH: erp-frontend/src/components/ui/CornerDecor.jsx
import React from 'react';
import styles from './CornerDecor.module.css';
// hideTop            -> hide top corners AND top pins
// hideTopCorners     -> hide ONLY the two top corner brackets (keep top pins)
const CornerDecor = ({ hidePins = false, hideTop = false, hideTopCorners = false }) => {
    return (
        <>
            {!hideTop && !hideTopCorners && <div className={`${styles.cornerAccent} ${styles.topLeft}`}></div>}
            {!hideTop && !hideTopCorners && <div className={`${styles.cornerAccent} ${styles.topRight}`}></div>}
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
