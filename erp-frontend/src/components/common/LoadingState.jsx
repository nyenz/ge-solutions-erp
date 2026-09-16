// PATH: erp-frontend/src/components/common/LoadingState.jsx
import React from 'react';
import styles from './LoadingState.module.css';

/**
 * GOLDEN SEED -- THE ONE LOADING / EMPTY STATE
 *
 * Every "syncing...", "loading...", "no records" message in the app renders
 * through here, so they all look the same and all pass the contrast rule
 * (no light text on the cream circuit background, no near-invisible white
 * on the navy panels).
 *
 * tone="panel" (default) -- draws its OWN dark navy card. Use when the state
 *                           sits directly on a page .container, which is
 *                           transparent and therefore cream.
 * tone="bare"            -- no card. Use when it is ALREADY inside a dark
 *                           panel (HardwarePanel, .timelineFrame, .hwPanel)
 *                           so you don't get a card inside a card.
 * size="page"            -- taller, for a whole-page boot screen.
 */
export const LoadingState = ({ label = 'LOADING...', tone = 'panel', size = 'block' }) => (
    <div
        className={[
            styles.shell,
            tone === 'bare' ? styles.shellBare : styles.shellPanel,
            size === 'page' ? styles.shellPage : '',
        ].filter(Boolean).join(' ')}
        role="status"
        aria-live="polite"
    >
        <div className={styles.spinner} aria-hidden="true" />
        <span className={styles.label}>{label}</span>
    </div>
);

/** Same thing, but as a table row -- for tbody loading states. */
export const LoadingRow = ({ colSpan = 1, label = 'LOADING...' }) => (
    <tr>
        <td colSpan={colSpan} className={styles.cell}>
            <span className={styles.cellInner} role="status" aria-live="polite">
                <span className={styles.spinnerSm} aria-hidden="true" />
                <span className={styles.label}>{label}</span>
            </span>
        </td>
    </tr>
);

/** No spinner -- the finished "there is nothing here" state. */
export const EmptyState = ({ label = 'NO RECORDS', icon: Icon, tone = 'panel', children }) => (
    <div
        className={[
            styles.shell,
            tone === 'bare' ? styles.shellBare : styles.shellPanel,
        ].join(' ')}
        role="status"
    >
        {Icon && <Icon className={styles.emptyIcon} aria-hidden="true" />}
        <span className={styles.label}>{label}</span>
        {children}
    </div>
);

export default LoadingState;
