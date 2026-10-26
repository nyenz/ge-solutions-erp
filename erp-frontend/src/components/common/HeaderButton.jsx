// PATH: erp-frontend/src/components/common/HeaderButton.jsx
import React from 'react';
import { FiCheck } from 'react-icons/fi';
import { Tooltip } from './Tooltip';
import useActionFeedback from './useActionFeedback';
import styles from './HeaderButton.module.css';

/**
 * GOLDEN SEED -- THE PAGE HEADER BUTTON
 *
 * One button spec for every page header in the app. It is the Payment Records
 * refresh button's look -- translucent navy on the frosted header bar, thin
 * navy edge, orange on hover -- at the Expenses button's size, which is the
 * smaller of the two the app was shipping.
 *
 * Before this there were three dialects: Payments' 40px light button,
 * Expenses' 34px one, and the Dossier's dark navy pills. Same job, same
 * position on screen, three different sizes and two different colour schemes.
 *
 * ON SMALL SCREENS IT BECOMES AN ICON. Page headers stack on phones and a row
 * of word-buttons is the thing that forces the stack. Below 640px the label is
 * dropped and the button goes square -- the tooltip already carries the words,
 * and aria-label keeps it announced.
 *
 * Variants:
 *   (default) ghost   -- on the frosted white page header
 *   primary           -- the one affirmative action, orange filled
 *   danger            -- destructive
 *   onDark            -- same spec, for a header sitting on a dark panel
 */
export const HeaderActions = ({ children, className = '' }) => (
    <div className={`${styles.actions} ${className}`}>{children}</div>
);

export const HeaderButton = ({
    icon: Icon,
    label,
    onClick,
    tip,
    variant = 'ghost',
    busy = false,
    disabled = false,
    type = 'button',
    ariaLabel,
}) => {
    // fix (feedback): the arrows spin while it works and a tick shows when it is done, even if the page answered at once
    const [phase, run] = useActionFeedback(onClick);
    const working = busy || phase === 'working';
    return (
        <Tooltip label={tip || label}>
            <button
                type={type}
                className={`${styles.btn} ${styles[variant] || ''} ${phase === 'done' ? styles.done : ''}`}
                onClick={onClick ? run : undefined}
                disabled={disabled || working}
                aria-label={ariaLabel || label}
                aria-busy={working}
            >
                {Icon && (
                    <span className={`${styles.icon} ${working ? styles.spin : ''}`} aria-hidden="true">
                        {phase === 'done' && !busy ? <FiCheck /> : <Icon />}
                    </span>
                )}
                <span className={styles.label}>{label}</span>
            </button>
        </Tooltip>
    );
};

export default HeaderButton;
