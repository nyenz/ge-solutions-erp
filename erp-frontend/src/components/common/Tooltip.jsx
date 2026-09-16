// PATH: erp-frontend/src/components/common/Tooltip.jsx
import React, { useState, useRef, useCallback, useEffect, useId } from 'react';
import { createPortal } from 'react-dom';
import styles from './Tooltip.module.css';

/**
 * GOLDEN SEED -- THE HOVER EXPLAINER
 *
 * Wrap anything whose meaning isn't obvious -- an icon-only button, a short
 * tag like LOCKED, an abbreviation -- and it explains itself on hover.
 *
 * Why not the browser's own title="" attribute:
 *   - it waits roughly a second before appearing
 *   - it can't be styled, so it ignores the app's contrast rule entirely
 *   - it does nothing on touch, and staff use this on phones
 *   - screen readers treat it inconsistently
 *
 * This one appears in 120ms, matches the app (navy card, orange edge, cream
 * text), works on hover AND keyboard focus AND tap, and closes on Escape.
 *
 * It renders into document.body through a portal so it is never clipped by a
 * panel's overflow:hidden -- which is exactly what would happen inside the
 * table wrappers and HardwarePanel bodies.
 */
export const Tooltip = ({ label, children, placement = 'top', delay = 120, disabled = false, block = false }) => {
    const [open, setOpen] = useState(false);
    const [box, setBox] = useState({ top: 0, left: 0, place: placement });
    const anchorRef = useRef(null);
    const timerRef = useRef(null);
    const tipId = useId();

    const measure = useCallback(() => {
        const el = anchorRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        // Flip to the underside if there isn't room above.
        const place = (placement === 'top' && r.top < 70) ? 'bottom' : placement;
        setBox({
            top: place === 'bottom' ? r.bottom + 8 : r.top - 8,
            left: Math.min(Math.max(r.left + r.width / 2, 80), window.innerWidth - 80),
            place,
        });
    }, [placement]);

    const show = useCallback(() => {
        if (disabled || !label) return;
        clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => { measure(); setOpen(true); }, delay);
    }, [disabled, label, delay, measure]);

    const hide = useCallback(() => {
        clearTimeout(timerRef.current);
        setOpen(false);
    }, []);

    useEffect(() => () => clearTimeout(timerRef.current), []);

    useEffect(() => {
        if (!open) return undefined;
        const onKey = (e) => { if (e.key === 'Escape') hide(); };
        // Any scroll moves the anchor out from under the bubble, so just close.
        window.addEventListener('keydown', onKey);
        window.addEventListener('scroll', hide, true);
        window.addEventListener('resize', hide);
        return () => {
            window.removeEventListener('keydown', onKey);
            window.removeEventListener('scroll', hide, true);
            window.removeEventListener('resize', hide);
        };
    }, [open, hide]);

    if (!label) return children;

    return (
        <>
            <span
                ref={anchorRef}
                className={block ? `${styles.anchor} ${styles.anchorBlock}` : styles.anchor}
                onMouseEnter={show}
                onMouseLeave={hide}
                onFocus={show}
                onBlur={hide}
                onTouchStart={() => { measure(); setOpen(o => !o); }}
                aria-describedby={open ? tipId : undefined}
            >
                {children}
            </span>
            {open && typeof document !== 'undefined' && createPortal(
                <div
                    id={tipId}
                    role="tooltip"
                    className={`${styles.bubble} ${box.place === 'bottom' ? styles.bubbleBottom : styles.bubbleTop}`}
                    style={{ top: box.top, left: box.left }}
                >
                    {label}
                </div>,
                document.body,
            )}
        </>
    );
};

/**
 * An icon-only button that explains itself. Use this instead of a bare
 * <button><FiSomething /></button>: the tooltip text doubles as the
 * aria-label, so it is impossible to ship an unlabelled icon button.
 */
export const IconButton = ({ tip, icon, onClick, className, size = 13, disabled = false }) => {
    const Icon = icon;
    return (
        <Tooltip label={tip} disabled={disabled}>
            <button
                type="button"
                className={className}
                onClick={onClick}
                disabled={disabled}
                aria-label={tip}
            >
                <Icon size={size} aria-hidden="true" />
            </button>
        </Tooltip>
    );
};

/**
 * Inline jargon. Renders the word with a dotted underline so people can SEE
 * there is an explanation waiting, rather than having to discover it.
 */
export const Term = ({ children, tip, className }) => (
    <Tooltip label={tip}>
        <span className={`${styles.term} ${className || ''}`} tabIndex={0}>{children}</span>
    </Tooltip>
);

export default Tooltip;
