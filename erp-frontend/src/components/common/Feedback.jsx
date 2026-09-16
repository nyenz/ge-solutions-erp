// PATH: erp-frontend/src/components/common/Feedback.jsx
import React from 'react';
import { createPortal } from 'react-dom';
import {
    FiCheckCircle, FiAlertTriangle, FiAlertOctagon, FiInfo, FiX, FiTrash2,
} from 'react-icons/fi';
import styles from './Feedback.module.css';

/**
 * GOLDEN SEED -- TALKING BACK TO THE USER (the visible half)
 *
 * <ToastStack />   -- the floating messages, bottom right
 * <ConfirmDialog /> -- the styled replacement for window.confirm()
 *
 * The state for both lives in the useToasts / useConfirm hooks next door in
 * useFeedback.js. They are split because this project's ESLint config
 * enforces react-refresh's "a file exports components OR it exports other
 * things, not both" rule.
 */

const TOAST_ICONS = {
    success: <FiCheckCircle aria-hidden="true" />,
    error: <FiAlertOctagon aria-hidden="true" />,
    warn: <FiAlertTriangle aria-hidden="true" />,
    info: <FiInfo aria-hidden="true" />,
};

export const ToastStack = ({ toasts, onDismiss }) => {
    if (!toasts.length || typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
                    <span className={styles.toastIcon}>{TOAST_ICONS[t.type] || TOAST_ICONS.info}</span>
                    <span className={styles.toastMsg}>{t.message}</span>
                    <button type="button" className={styles.toastClose}
                        onClick={() => onDismiss(t.id)} aria-label="Dismiss">
                        <FiX aria-hidden="true" />
                    </button>
                </div>
            ))}
        </div>,
        document.body,
    );
};

export const ConfirmDialog = ({ state, onAnswer }) => {
    if (!state.open || typeof document === 'undefined') return null;
    const isDanger = state.variant === 'danger';
    return createPortal(
        <div className={styles.confirmOverlay} role="dialog" aria-modal="true"
            onClick={(e) => { if (e.target === e.currentTarget) onAnswer(false); }}>
            <div className={styles.confirmBox}>
                <button type="button" className={styles.confirmClose}
                    onClick={() => onAnswer(false)} aria-label="Close">
                    <FiX aria-hidden="true" />
                </button>
                <div className={`${styles.confirmHeader} ${isDanger ? styles.confirmHeaderDanger : styles.confirmHeaderWarn}`}>
                    {isDanger
                        ? <FiAlertOctagon className={styles.confirmIcon} aria-hidden="true" />
                        : <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" />}
                    <span className={styles.confirmTitle}>{state.title}</span>
                </div>
                <p className={styles.confirmMessage}>{state.message}</p>
                <div className={styles.confirmFooter}>
                    <button type="button" className={styles.confirmCancelBtn} onClick={() => onAnswer(false)}>
                        CANCEL
                    </button>
                    <button type="button"
                        className={`${styles.confirmOkBtn} ${isDanger ? styles.confirmOkDanger : styles.confirmOkWarn}`}
                        onClick={() => onAnswer(true)}>
                        {isDanger
                            ? <><FiTrash2 aria-hidden="true" /> CONFIRM DELETE</>
                            : <><FiCheckCircle aria-hidden="true" /> CONFIRM</>}
                    </button>
                </div>
            </div>
        </div>,
        document.body,
    );
};
