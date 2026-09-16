// PATH: erp-frontend/src/components/common/Tooltip.jsx
import React, { useState, useRef, useCallback, useEffect, useLayoutEffect, useId } from 'react';
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
 * It renders into document.body through a portal so it is never clipped by a
 * panel's overflow:hidden -- which is exactly what would happen inside the
 * table wrappers and panel bodies.
 *
 * fix68 -- TWO THINGS CHANGED HERE:
 *
 * 1. EDGE CLIPPING. The old version centred the bubble on the anchor and then
 *    clamped that CENTRE to 80px from each edge. 80px is less than half the
 *    bubble's width, so anything anchored near an edge -- the sidebar nav
 *    being the obvious one -- still had its left side cut off the screen.
 *    Guessing at a safe centre can't work, because the bubble's width isn't
 *    known until it has text in it. So it now renders, measures itself, and
 *    nudges horizontally by exactly the overflow. One extra paint, no clip.
 *
 * 2. WEIGHT. It was a bordered card: orange 1.5px edge, heavy shadow, DM Sans
 *    600. Next to a dense table that reads as another panel, and the border
 *    is what made it feel crowded. It is now a plain translucent slab --
 *    no border, no pointer, blurred backdrop, Inter at normal weight.
 */
// fix69: dwell and auto-dismiss come from the user's Appearance setting,
// which the provider writes onto <html data-tips>. "off" means the explainer
// never opens at all -- some people find it noise, and that is a fair call.
const TIP_MODES = {
    normal: { delay: 120, life: 6000 },
    slow:   { delay: 500, life: 9000 },
    off:    { delay: 0,   life: 0, disabled: true },
};
const tipMode = () => {
    if (typeof document === 'undefined') return TIP_MODES.normal;
    return TIP_MODES[document.documentElement.getAttribute('data-tips')] || TIP_MODES.normal;
};

// Portal target is #root, not <body>: the UI-size setting applies zoom to
// #root, and a bubble outside it would render at 100% next to a page at 125%
// and sit in the wrong place.
const portalTarget = () => (typeof document === 'undefined'
    ? null
    : (document.getElementById('root') || document.body));

export const Tooltip = ({ label, children, placement = 'top', delay, disabled = false, block = false }) => {
    const [open, setOpen] = useState(false);
    const [box, setBox] = useState({ top: 0, left: 0, place: placement });
    const [shift, setShift] = useState(0);
    const anchorRef = useRef(null);
    const bubbleRef = useRef(null);
    const timerRef = useRef(null);
    const lifeRef = useRef(null);
    const tipId = useId();

    const measure = useCallback(() => {
        const el = anchorRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        // Flip to the underside if there isn't room above.
        const place = (placement === 'top' && r.top < 64) ? 'bottom' : placement;
        setShift(0);
        setBox({
            top: place === 'bottom' ? r.bottom + 8 : r.top - 8,
            left: r.left + r.width / 2,
            place,
        });
    }, [placement]);

    // Measured correction: run after the bubble is in the DOM and has a real
    // width. dx is zero on the second pass, so this settles immediately.
    useLayoutEffect(() => {
        if (!open) return;
        const el = bubbleRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        const margin = 10;
        let dx = 0;
        if (r.left < margin) dx = margin - r.left;
        else if (r.right > window.innerWidth - margin) dx = (window.innerWidth - margin) - r.right;
        if (Math.abs(dx) > 0.5) setShift(s => s + dx);
    }, [open, box, shift]);

    const show = useCallback(() => {
        const mode = tipMode();
        if (disabled || !label || mode.disabled) return;
        clearTimeout(timerRef.current);
        clearTimeout(lifeRef.current);
        timerRef.current = setTimeout(() => {
            measure();
            setOpen(true);
            // Auto-dismiss: an explainer you have already read should not keep
            // sitting on top of the row underneath it.
            if (mode.life > 0) {
                lifeRef.current = setTimeout(() => { setOpen(false); setShift(0); }, mode.life);
            }
        }, delay === undefined ? mode.delay : delay);
    }, [disabled, label, delay, measure]);

    const hide = useCallback(() => {
        clearTimeout(timerRef.current);
        clearTimeout(lifeRef.current);
        setOpen(false);
        setShift(0);
    }, []);

    useEffect(() => () => { clearTimeout(timerRef.current); clearTimeout(lifeRef.current); }, []);

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
                onTouchStart={() => { if (tipMode().disabled) return; measure(); setOpen(o => !o); }}
                aria-describedby={open ? tipId : undefined}
            >
                {children}
            </span>
            {open && portalTarget() && createPortal(
                <div
                    ref={bubbleRef}
                    id={tipId}
                    role="tooltip"
                    className={styles.bubble}
                    style={{
                        top: box.top,
                        left: box.left,
                        transform: `translate(calc(-50% + ${shift}px), ${box.place === 'bottom' ? '0' : '-100%'})`,
                    }}
                >
                    {label}
                </div>,
                portalTarget(),
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
