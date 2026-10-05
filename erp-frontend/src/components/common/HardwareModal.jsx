// PATH: erp-frontend/src/components/common/HardwareModal.jsx
import { portalRoot } from './portalRoot';
import React from 'react';
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
    if (!isOpen) return null;

    // We attach the modal to the 'root' or a specific portal div to prevent clipping
    return createPortal(
        <div className={`${styles.backdrop} ${stacked ? styles.backdropStacked : ''}`} onClick={lockBackdrop ? undefined : onClose} role="dialog" aria-modal="true" aria-label={typeof title === 'string' ? title : undefined}>
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