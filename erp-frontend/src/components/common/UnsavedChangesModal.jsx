// PATH: erp-frontend/src/components/common/UnsavedChangesModal.jsx
import { portalRoot } from './portalRoot';
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiAlertTriangle, FiLogOut, FiX } from 'react-icons/fi';
import modal from './HardwareModal.module.css';
import styles from './UnsavedChangesModal.module.css';

/**
 * GOLDEN SEED -- UNSAVED CHANGES GUARD (fix151)
 *
 * Built on the HardwareModal popup standard: same backdrop, card, Cinzel title
 * with the orange hairline, modalFooter and modalBtnPrimary / modalBtnSecondary.
 * fix152: the X is back (same closeBtn as the Recovery CALL LOG popup). X = KEEP EDITING, the safe choice.
 * fix159: the KEEP EDITING button is gone (it duplicated the X). The only button left is DISCARD & LEAVE.
 * Backdrop click and Esc both mean KEEP EDITING (the safe choice).
 *
 * Props:
 *   isOpen   -- whether to show the modal
 *   onStay   -- user chose to stay and keep editing
 *   onLeave  -- user confirmed they want to leave (lose changes)
 *   context  -- what will be lost (e.g. "Audit Filters")
 */
const UnsavedChangesModal = ({ isOpen, onStay, onLeave, context = 'this form' }) => {
    useEffect(() => {
        if (!isOpen) return;
        const handler = (e) => { if (e.key === 'Escape') onStay(); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [isOpen, onStay]);

    if (!isOpen || typeof document === 'undefined') return null;

    return createPortal(
        <div className={modal.backdrop} onClick={onStay} role="dialog" aria-modal="true" aria-labelledby="ucm-title">
            <div className={modal.modalBody} onClick={(e) => e.stopPropagation()}>
                <header className={modal.header}>
                    <FiAlertTriangle className={styles.warnIcon} aria-hidden="true" />
                    <span id="ucm-title" className={modal.title}>UNSAVED CHANGES</span>
                    <button type="button" className={modal.closeBtn} onClick={onStay} autoFocus aria-label="Close and keep editing">
                        <FiX aria-hidden="true" />
                    </button>
                </header>

                <div className={`${modal.modalInfoBox} ${styles.warnBox}`}>
                    You have unsaved changes in <strong>{context}</strong>.
                    If you leave now, everything you entered will be permanently lost.
                </div>

                <div className={modal.modalFooter}>
                    <button className={`${modal.modalBtnSecondary} ${styles.leaveBtn}`} onClick={onLeave}
                        aria-label="Leave page and discard changes">
                        <FiLogOut aria-hidden="true" /> DISCARD &amp; LEAVE
                    </button>
                </div>

                <div className={modal.footerGlow} />
            </div>
        </div>, portalRoot());
};

export default UnsavedChangesModal;
