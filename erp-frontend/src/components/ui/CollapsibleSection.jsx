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
            {/* fix183: the head bar is a div that acts as a button (Enter / Space / click). It used to be a real <button>
                with the panel's own buttons (SAVE PRESET, RESTORE DEFAULTS ...) inside it, and a button inside a button
                is not valid HTML. The chevron sits right after the title, so it stays on the first line when the
                panel's buttons drop to a second line on a phone (the title no longer shrinks to "6. ST..."). */}
            <div
                role="button"
                tabIndex={0}
                className={`${styles.header} ${open ? styles.headerOpen : ''}`}
                onClick={toggle}
                onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); toggle(); } }}
                aria-expanded={open}
            >
                <span className={styles.headerLeft}>
                    {icon}
                    <h2 className={styles.title}>{title}</h2>
                </span>
                <FiChevronDown
                    aria-hidden="true"
                    className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`}
                />
                {right && <span className={styles.headerRight} onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()}>{right}</span>}
            </div>
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
