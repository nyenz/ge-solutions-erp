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
            styles.shellSkel,
            tone === 'bare' ? styles.shellBare : styles.shellPanel,
            size === 'page' ? styles.shellPage : '',
        ].filter(Boolean).join(' ')}
        role="status"
        aria-live="polite"
    >
        {/* fix149: the Folder page skeleton is the loading look everywhere */}
        <div className={styles.skelStack} aria-hidden="true">
            {size === 'page' && <div className={styles.skelHud} />}
            <div className={styles.skelPanel}>
                <div className={styles.skelHeader} />
                <div className={styles.skelBody}>
                    <div className={styles.skelLine} />
                    <div className={styles.skelLine} />
                    <div className={styles.skelLine} />
                </div>
            </div>
            {size === 'page' && (
                <div className={styles.skelPanel}>
                    <div className={styles.skelHeader} />
                    <div className={styles.skelBody}>
                        <div className={styles.skelLine} />
                        <div className={styles.skelLine} />
                    </div>
                </div>
            )}
        </div>
        <span className={styles.srOnly}>{label}</span>
    </div>
);

/** Same thing, but as a table row -- for tbody loading states. */
export const LoadingRow = ({ colSpan = 1, label = 'LOADING...' }) => (
    <React.Fragment>
        {['92%', '70%', '84%'].map((w, i) => (
            <tr key={i}>
                <td colSpan={colSpan} className={styles.skelCell}>
                    <span className={styles.skelRowBar} style={{ width: w }} aria-hidden="true" />
                    {i === 0 && <span className={styles.srOnly} role="status" aria-live="polite">{label}</span>}
                </td>
            </tr>
        ))}
    </React.Fragment>
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
