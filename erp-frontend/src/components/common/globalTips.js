// PATH: erp-frontend/src/components/common/globalTips.js
import { useEffect } from 'react';
import styles from './Tooltip.module.css';
import { portalRoot, uiScale } from './portalRoot';

/**
 * fix199 (David, test note 4): "the hover explainers should work throughout".
 *
 * Most pages explain a button or a tag with a plain title="..." attribute. The browser shows those late, unstyled,
 * and never on a phone. This ONE listener, installed once for the whole app, turns every title="..." into the same
 * explainer bubble the <Tooltip> component draws:
 *  - mouse: shows after the Appearance delay, hides when the pointer leaves, on scroll, on a click or Escape;
 *  - keyboard: shows while the element has keyboard focus;
 *  - phone: press and hold for about half a second (a normal tap still works as before);
 *  - a DISABLED button explains itself too (that is where the "why can I not press this" text usually is).
 * The title is moved to data-gs-tip the first time it is used, so the browser's own tip does not show as well.
 * Appearance > explainers OFF leaves the plain browser titles alone. New code can keep writing title="...".
 */
const MODES = { normal: { delay: 120, life: 6000 }, slow: { delay: 500, life: 9000 }, off: { off: true } };
const mode = () => MODES[document.documentElement.getAttribute('data-tips')] || MODES.normal;

function tipOf(el) {
    if (!el || el.nodeType !== 1) return '';
    const t = el.getAttribute('title');
    if (t) { el.setAttribute('data-gs-tip', t); el.removeAttribute('title'); }
    return el.getAttribute('data-gs-tip') || '';
}

const anchorOf = (node) => (node && node.closest ? node.closest('[title],[data-gs-tip]') : null);

export function installGlobalTips() {
    if (typeof document === 'undefined') return () => {};
    let bubble = null, anchor = null, showT = null, lifeT = null, pressT = null;

    const hide = () => {
        clearTimeout(showT); clearTimeout(lifeT);
        if (bubble) { bubble.remove(); bubble = null; }
        anchor = null;
    };

    const place = () => {
        if (!bubble || !anchor || !anchor.isConnected) { hide(); return; }
        const k = uiScale();
        const r = anchor.getBoundingClientRect();
        const below = r.top < 64;
        bubble.style.top = ((below ? r.bottom + 8 : r.top - 8) / k) + 'px';
        bubble.style.left = ((r.left + r.width / 2) / k) + 'px';
        bubble.style.transform = 'translate(-50%, ' + (below ? '0' : '-100%') + ')';
        const b = bubble.getBoundingClientRect();
        let dx = 0;
        if (b.left < 10) dx = 10 - b.left;
        else if (b.right > window.innerWidth - 10) dx = window.innerWidth - 10 - b.right;
        if (dx) bubble.style.transform = 'translate(calc(-50% + ' + (dx / k) + 'px), ' + (below ? '0' : '-100%') + ')';
    };

    const show = (el, wait) => {
        const m = mode();
        if (m.off) return;
        const text = tipOf(el);
        if (!text) return;
        hide();
        anchor = el;
        showT = setTimeout(() => {
            if (anchor !== el || !el.isConnected) return;
            bubble = document.createElement('div');
            bubble.className = styles.bubble;
            bubble.setAttribute('role', 'tooltip');
            bubble.textContent = text;
            (portalRoot() || document.body).appendChild(bubble);
            place();
            if (m.life) lifeT = setTimeout(hide, m.life);
        }, wait === undefined ? m.delay : wait);
    };

    const onOver = (e) => {
        if (e.pointerType === 'touch') return;
        const el = anchorOf(e.target);
        if (!el) return;
        if (el === anchor) return;
        show(el);
    };
    const onOut = (e) => {
        if (!anchor) return;
        if (e.relatedTarget && anchor.contains(e.relatedTarget)) return;
        hide();
    };
    const onFocus = (e) => {
        const el = anchorOf(e.target);
        if (el && el.matches && el.matches(':focus-visible')) show(el);
    };
    const onDown = (e) => {
        clearTimeout(pressT);
        if (e.pointerType !== 'touch') { hide(); return; }
        const el = anchorOf(e.target);
        if (!el) return;
        pressT = setTimeout(() => show(el, 0), 450);
    };
    const cancelPress = () => clearTimeout(pressT);
    const onKey = (e) => { if (e.key === 'Escape') hide(); };

    document.addEventListener('pointerover', onOver, true);
    document.addEventListener('pointerout', onOut, true);
    document.addEventListener('focusin', onFocus, true);
    document.addEventListener('focusout', hide, true);
    document.addEventListener('pointerdown', onDown, true);
    document.addEventListener('pointerup', cancelPress, true);
    document.addEventListener('pointercancel', cancelPress, true);
    document.addEventListener('keydown', onKey, true);
    window.addEventListener('scroll', hide, true);
    window.addEventListener('resize', hide);
    return () => {
        hide(); clearTimeout(pressT);
        document.removeEventListener('pointerover', onOver, true);
        document.removeEventListener('pointerout', onOut, true);
        document.removeEventListener('focusin', onFocus, true);
        document.removeEventListener('focusout', hide, true);
        document.removeEventListener('pointerdown', onDown, true);
        document.removeEventListener('pointerup', cancelPress, true);
        document.removeEventListener('pointercancel', cancelPress, true);
        document.removeEventListener('keydown', onKey, true);
        window.removeEventListener('scroll', hide, true);
        window.removeEventListener('resize', hide);
    };
}

/** Installs the explainer once for the whole app (App.jsx). */
export function useGlobalTips() {
    useEffect(() => installGlobalTips(), []);
}
