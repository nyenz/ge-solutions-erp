// PATH: erp-frontend/src/components/ui/CollapsibleSection.jsx
import React, { useState } from 'react';
import { FiChevronDown } from 'react-icons/fi';
import styles from './CollapsibleSection.module.css';

/**
 * Generic expand/contract card used to break long forms and pages into
 * scannable chunks. Click the header (or press Enter/Space on it) to
 * toggle. Uncontrolled by default (defaultOpen) but can be driven
 * externally via `open` + `onToggle` when a parent needs to know state.
 */
const CollapsibleSection = ({
    icon,
    title,
    right,
    defaultOpen = true,
    open: controlledOpen,
    onToggle,
    accent = false,
    className = '',
    children,
}) => {
    const [internalOpen, setInternalOpen] = useState(defaultOpen);
    const isControlled = controlledOpen !== undefined;
    const open = isControlled ? controlledOpen : internalOpen;

    const toggle = () => {
        if (isControlled) onToggle?.(!open);
        else setInternalOpen(o => !o);
    };

    return (
        <section className={`${styles.section} ${accent ? styles.accent : ''} ${className}`}>
            <button
                type="button"
                className={styles.header}
                onClick={toggle}
                aria-expanded={open}
            >
                <span className={styles.headerLeft}>
                    {icon}
                    <h2 className={styles.title}>{title}</h2>
                </span>
                <span className={styles.headerRight}>
                    {right && <span onClick={e => e.stopPropagation()}>{right}</span>}
                    <FiChevronDown
                        aria-hidden="true"
                        className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`}
                    />
                </span>
            </button>
            {open && <div className={styles.body}>{children}</div>}
        </section>
    );
};

export default CollapsibleSection;
