// PATH: erp-frontend/src/components/ui/CollapsibleSection.jsx
import React, { useState } from 'react';
import { FiChevronDown } from 'react-icons/fi';
import CornerDecor from './CornerDecor';
import styles from './CollapsibleSection.module.css';

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
    const [active, setActive] = useState(false); // user is working inside
    const isControlled = controlledOpen !== undefined;
    const open = isControlled ? controlledOpen : internalOpen;

    const toggle = () => {
        if (isControlled) onToggle?.(!open);
        else setInternalOpen(o => !o);
    };

    const handleBlur = (e) => {
        // deactivate only when focus truly leaves the section
        if (!e.currentTarget.contains(e.relatedTarget)) setActive(false);
    };

    // orange "active" border only while the user is actually inside
    const showAccent = accent && active;

    return (
        <section
            className={`${styles.section} ${showAccent ? styles.accent : ''} ${className}`}
            onFocusCapture={() => setActive(true)}
            onBlurCapture={handleBlur}
        >
            <button
                type="button"
                className={`${styles.header} ${open ? styles.headerOpen : ''}`}
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
            {open && (
                <div className={styles.body}>
                    <CornerDecor hideTop />
                    {children}
                </div>
            )}
        </section>
    );
};

export default CollapsibleSection;
