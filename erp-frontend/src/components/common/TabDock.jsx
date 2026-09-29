// PATH: erp-frontend/src/components/common/TabDock.jsx
import React from 'react';
import styles from './TabDock.module.css';

/**
 * TabDock -- THE tab / filter control for the whole app.
 *
 * One tray, pill buttons inside it, the active pill solid orange. This is
 * the Settings page tab bar (and Report Studio's dataset row) turned into a
 * component, so Ledger, Clients, Payments and Recovery all look identical.
 * Do NOT hand-roll filter buttons on a page any more -- use this.
 *
 * items    [{ key, label, count?, icon?, accent?, title? }]
 *            count  -> small Space Mono number after the label
 *            icon   -> a react-icons / lucide component (optional)
 *            accent -> 'orange' (default) | 'red' | 'green' | 'yellow' | 'cyan'
 *                      tints the hover + active colour, like Settings does
 * value    the active key
 * onChange (key) => void
 * mode     'filter' (default: buttons, aria-pressed)  |  'tab' (role=tablist)
 * label    accessible name for the group
 * end      optional node shown after the tray (e.g. a "5 SECTIONS" badge)
 */
const TabDock = ({ items, value, onChange, mode = 'filter', label, end = null, className = '' }) => {
    const isTab = mode === 'tab';
    return (
        <div className={`${styles.dockRow} ${className}`}>
            <div className={styles.tabDock}>
                <div
                    className={styles.tabRow}
                    role={isTab ? 'tablist' : 'group'}
                    aria-label={label}
                >
                    {items.map(({ key, label: text, count, icon: Icon, accent = 'orange', title }) => {
                        const on = value === key;
                        return (
                            <button
                                key={key}
                                type="button"
                                className={on ? styles.tabOn : styles.tab}
                                data-accent={accent}
                                title={title}
                                onClick={() => onChange(key)}
                                {...(isTab
                                    ? { role: 'tab', 'aria-selected': on }
                                    : { 'aria-pressed': on })}
                            >
                                {Icon && <Icon aria-hidden="true" />}
                                <span>{text}</span>
                                {count !== undefined && count !== null && (
                                    <span className={styles.tabCount}>{count}</span>
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>
            {end}
        </div>
    );
};

// fix147: accent of the ACTIVE pill, for tinting the panel below it.
// 'orange' (or no accent) -> undefined, so the panel keeps its normal look.
export const accentOf = (items, value) => {
    const a = (items.find((i) => i.key === value) || {}).accent;
    return a && a !== 'orange' ? a : undefined;
};

export default TabDock;
