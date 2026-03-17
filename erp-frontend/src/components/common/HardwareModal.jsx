// PATH: erp-frontend/src/components/common/HardwareModal.jsx
import React from 'react';
import { createPortal } from 'react-dom';
import { FiX } from 'react-icons/fi';
import styles from './HardwareModal.module.css';

/**
 * GOLDEN SEED - HARDWARE MODAL PORTAL
 * Breaks out of DOM hierarchy to ensure the note popup is always on top.
 */
const HardwareModal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;

    // We attach the modal to the 'root' or a specific portal div to prevent clipping
    return createPortal(
        <div className={styles.backdrop} onClick={onClose}>
            <div className={styles.modalBody} onClick={(e) => e.stopPropagation()}>
                
                <header className={styles.header}>
                    <span className={styles.title}>{title}</span>
                    <button className={styles.closeBtn} onClick={onClose}>
                        <FiX />
                    </button>
                </header>

                <div className={styles.content}>
                    {children}
                </div>

                <div className={styles.footerGlow}></div>
            </div>
        </div>,
        document.body
    );
};

export default HardwareModal;