// PATH: erp-frontend/src/components/common/NinMismatchModal.jsx
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiAlertTriangle, FiX, FiCheck, FiEdit3 } from 'react-icons/fi';
import styles from './UnsavedChangesModal.module.css';

/**
 * STAGE 3 -- NIN NAME MISMATCH GUARD
 *
 * Blocking confirmation shown when a typed NIN already belongs to a
 * different name on file. Forces an explicit choice before the intake
 * or edit form can be saved again -- prevents silently attaching a
 * project to the wrong person on a NIN typo. Reuses the existing
 * UnsavedChangesModal visual language rather than introducing a new
 * CSS file.
 *
 * Props:
 *   isOpen       -- whether to show the modal
 *   existingName -- the name already on file for this NIN
 *   enteredName  -- the name typed into the current form
 *   onConfirm    -- user confirmed it IS the same person
 *   onReject     -- user says it's NOT the same person (clear + fix the NIN)
 */
const NinMismatchModal = ({ isOpen, existingName, enteredName, onConfirm, onReject }) => {
    useEffect(() => {
        if (!isOpen) return;
        const handler = (e) => { if (e.key === 'Escape') onReject(); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [isOpen, onReject]);

    if (!isOpen || typeof document === 'undefined') return null;

    return createPortal(
        <div className={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="nin-mismatch-title">
            <div className={styles.card}>
                <div className={styles.iconWrap} aria-hidden="true">
                    <div className={styles.iconRing} />
                    <div className={styles.iconRing2} />
                    <FiAlertTriangle className={styles.icon} />
                </div>

                <div className={styles.body}>
                    <h2 id="nin-mismatch-title" className={styles.title}>NIN ALREADY REGISTERED</h2>
                    <p className={styles.message}>
                        This National ID is already registered to <strong>"{existingName}"</strong>,
                        but you entered <strong>"{enteredName}"</strong>. Confirm this is the same
                        person before continuing, or fix the NIN if it was a typo.
                    </p>

                    <div className={styles.divider}>
                        <span>IS THIS THE SAME PERSON?</span>
                    </div>

                    <div className={styles.actions}>
                        <button
                            className={styles.stayBtn}
                            onClick={onConfirm}
                            autoFocus
                            aria-label="Confirm this is the same person"
                        >
                            <FiCheck aria-hidden="true" />
                            YES, SAME PERSON
                        </button>
                        <button
                            className={styles.leaveBtn}
                            onClick={onReject}
                            aria-label="This is not the same person, fix the NIN"
                        >
                            <FiEdit3 aria-hidden="true" />
                            NO, LET ME FIX THE NIN
                        </button>
                    </div>
                </div>

                <button className={styles.closeBtn} onClick={onReject} aria-label="Close and fix the NIN">
                    <FiX aria-hidden="true" />
                </button>
            </div>
        </div>,
        document.body
    );
};

export default NinMismatchModal;
