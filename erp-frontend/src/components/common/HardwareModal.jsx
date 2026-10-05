// PATH: erp-frontend/src/components/common/HardwareModal.jsx
import { portalRoot } from './portalRoot';
import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { FiX } from 'react-icons/fi';
import styles from './HardwareModal.module.css';

/**
 * GOLDEN SEED - HARDWARE MODAL PORTAL
 * Breaks out of DOM hierarchy to ensure the note popup is always on top.
 */
// fix167: `stacked` = a popup opened ON TOP of another popup (a confirm). It sits above the first popup and only
// darkens it: no blur, so the first popup (and any red error inside it) stays readable behind it.
const HardwareModal = ({ isOpen, onClose, title, children, lockBackdrop = false, stacked = false }) => {
    // fix181 (14.5b): Escape closes the pop-up (not a locked one); only the top-most pop-up reacts
    const closeRef = useRef(onClose);
    useEffect(() => { closeRef.current = onClose; }, [onClose]);
    useEffect(() => {
        if (!isOpen || lockBackdrop) return undefined;
        const onKey = (e) => {
            if (e.key !== 'Escape' || e.defaultPrevented) return;
            const all = document.querySelectorAll('[data-hw-modal="1"]');
            if (all.length && all[all.length - 1] !== mine.current) return;
            e.preventDefault();
            if (closeRef.current) closeRef.current();
        };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [isOpen, lockBackdrop]);
    const mine = useRef(null);
    if (!isOpen) return null;

    // We attach the modal to the 'root' or a specific portal div to prevent clipping
    return createPortal(
        <div className={`${styles.backdrop} ${stacked ? styles.backdropStacked : ''}`} onClick={lockBackdrop ? undefined : onClose} ref={mine} data-hw-modal="1" role="dialog" aria-modal="true" aria-label={typeof title === 'string' ? title : undefined}>
            <div className={styles.modalBody} onClick={(e) => e.stopPropagation()}>
                
                <header className={styles.header}>
                    <span className={styles.title}>{title}</span>
                    <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close" title="Close">
                        <FiX />
                    </button>
                </header>

                <div className={styles.content}>
                    {children}
                </div>

                <div className={styles.footerGlow}></div>
            </div>
        </div>, portalRoot());
};

export default HardwareModal;