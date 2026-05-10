// PATH: erp-frontend/src/components/common/UnsavedChangesModal.jsx
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiAlertTriangle, FiX, FiSave, FiLogOut } from 'react-icons/fi';
import styles from './UnsavedChangesModal.module.css';

/**
 * GOLDEN SEED — UNSAVED CHANGES GUARD
 *
 * Custom-styled replacement for the browser's default "Leave site?" dialog.
 * Shows whenever the user tries to navigate away with unsaved changes.
 *
 * Props:
 *   isOpen     — whether to show the modal
 *   onStay     — user chose to stay and keep editing
 *   onLeave    — user confirmed they want to leave (lose changes)
 *   context    — optional string describing what will be lost (e.g. "New Plot")
 */
const UnsavedChangesModal = ({ isOpen, onStay, onLeave, context = 'this form' }) => {
    // Trap focus inside modal when open
    useEffect(() => {
        if (!isOpen) return;
        const handler = (e) => {
            if (e.key === 'Escape') onStay();
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [isOpen, onStay]);

    if (!isOpen || typeof document === 'undefined') return null;

    return createPortal(
        <div className={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="ucm-title">
            <div className={styles.card}>
                {/* Animated warning icon */}
                <div className={styles.iconWrap} aria-hidden="true">
                    <div className={styles.iconRing} />
                    <div className={styles.iconRing2} />
                    <FiAlertTriangle className={styles.icon} />
                </div>

                <div className={styles.body}>
                    <h2 id="ucm-title" className={styles.title}>UNSAVED CHANGES</h2>
                    <p className={styles.message}>
                        You have unsaved changes in <strong>{context}</strong>.
                        If you leave now, all your entered data will be permanently lost.
                    </p>

                    <div className={styles.divider}>
                        <span>WHAT WOULD YOU LIKE TO DO?</span>
                    </div>

                    <div className={styles.actions}>
                        <button
                            className={styles.stayBtn}
                            onClick={onStay}
                            autoFocus
                            aria-label="Stay on page and keep editing"
                        >
                            <FiSave aria-hidden="true" />
                            KEEP EDITING
                        </button>
                        <button
                            className={styles.leaveBtn}
                            onClick={onLeave}
                            aria-label="Leave page and discard changes"
                        >
                            <FiLogOut aria-hidden="true" />
                            DISCARD &amp; LEAVE
                        </button>
                    </div>
                </div>

                {/* Dismiss with X goes to "stay" */}
                <button className={styles.closeBtn} onClick={onStay} aria-label="Close and keep editing">
                    <FiX aria-hidden="true" />
                </button>
            </div>
        </div>,
        document.body
    );
};

export default UnsavedChangesModal;
