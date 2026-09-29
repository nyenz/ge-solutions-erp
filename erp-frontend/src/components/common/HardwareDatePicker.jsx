// PATH: erp-frontend/src/components/common/HardwareDatePicker.jsx
import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
    FiCalendar, FiChevronLeft, FiChevronRight, FiChevronsLeft, FiChevronsRight
} from 'react-icons/fi';
import styles from './HardwareDatePicker.module.css';

/**
 * GOLDEN SEED -- DATE PICKER (fix152)
 *
 * The browser's own calendar cannot be themed (it is drawn by the OS), so every date field in the
 * app uses this one instead. It looks like the popup standard: dark gradient card, orange border,
 * Cinzel month title, orange selected day.
 *
 * Contract is the same as <input type="date">:
 *   value     -- 'yyyy-mm-dd' or ''
 *   onChange  -- called with the NEW VALUE STRING (not an event)
 * Extra props:
 *   className -- put on the visible field, so each page keeps its own field styling
 *   block     -- true = field fills its parent's width (forms); false = shrink to fit (filter rows)
 *   ariaLabel -- accessible name
 */
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DOW = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
const POP_W = 288;
const POP_H = 352;

const pad = (n) => String(n).padStart(2, '0');
const toValue = (y, m, d) => y + '-' + pad(m + 1) + '-' + pad(d);
const parse = (v) => {
    const hit = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || '');
    return hit ? { y: +hit[1], m: +hit[2] - 1, d: +hit[3] } : null;
};
const show = (v) => {
    const p = parse(v);
    return p ? pad(p.d) + '/' + pad(p.m + 1) + '/' + p.y : '';
};
const todayParts = () => {
    const t = new Date();
    return { y: t.getFullYear(), m: t.getMonth(), d: t.getDate() };
};

const HardwareDatePicker = ({ value = '', onChange, className = '', block = false, ariaLabel = 'Date', placeholder = 'dd/mm/yyyy' }) => {
    const [open, setOpen] = useState(false);
    const [view, setView] = useState(() => {
        const p = parse(value) || todayParts();
        return { y: p.y, m: p.m };
    });
    const [pos, setPos] = useState({ top: 0, left: 0 });
    const wrapRef = useRef(null);
    const inputRef = useRef(null);
    const popRef = useRef(null);

    // open the card under the field (or above it when there is no room below)
    const openPicker = () => {
        const p = parse(value) || todayParts();
        setView({ y: p.y, m: p.m });
        if (inputRef.current) {
            const r = inputRef.current.getBoundingClientRect();
            const left = Math.max(8, Math.min(r.left, window.innerWidth - POP_W - 8));
            let top = r.bottom + 6;
            if (top + POP_H > window.innerHeight - 8 && r.top - POP_H - 6 > 8) top = r.top - POP_H - 6;
            setPos({ top, left });
        }
        setOpen(true);
    };

    useEffect(() => {
        if (!open) return;
        const onDown = (e) => {
            if (wrapRef.current && wrapRef.current.contains(e.target)) return;
            if (popRef.current && popRef.current.contains(e.target)) return;
            setOpen(false);
        };
        const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
        const onMove = (e) => {
            if (popRef.current && popRef.current.contains(e.target)) return;
            setOpen(false);
        };
        document.addEventListener('mousedown', onDown);
        document.addEventListener('keydown', onKey);
        window.addEventListener('resize', onMove);
        window.addEventListener('scroll', onMove, true);
        return () => {
            document.removeEventListener('mousedown', onDown);
            document.removeEventListener('keydown', onKey);
            window.removeEventListener('resize', onMove);
            window.removeEventListener('scroll', onMove, true);
        };
    }, [open]);

    const pick = (v) => { onChange(v); setOpen(false); };
    const shiftMonth = (n) => setView((v) => {
        const d = new Date(v.y, v.m + n, 1);
        return { y: d.getFullYear(), m: d.getMonth() };
    });
    const shiftYear = (n) => setView((v) => ({ y: v.y + n, m: v.m }));

    const sel = parse(value);
    const now = todayParts();
    const lead = (new Date(view.y, view.m, 1).getDay() + 6) % 7; // week starts on Monday
    const cells = [];
    for (let i = 0; i < 42; i++) {
        const dt = new Date(view.y, view.m, 1 - lead + i);
        cells.push({ y: dt.getFullYear(), m: dt.getMonth(), d: dt.getDate(), out: dt.getMonth() !== view.m });
    }

    return (
        <div className={`${styles.wrap} ${block ? styles.wrapBlock : ''}`} ref={wrapRef}>
            <input
                ref={inputRef}
                type="text"
                readOnly
                size={10}
                className={`${styles.field} ${className}`}
                value={show(value)}
                placeholder={placeholder}
                aria-label={ariaLabel}
                aria-haspopup="dialog"
                aria-expanded={open}
                onClick={() => (open ? setOpen(false) : openPicker())}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') { e.preventDefault(); if (!open) openPicker(); }
                }}
            />
            <FiCalendar className={styles.fieldIcon} aria-hidden="true" />

            {open && createPortal(
                <div ref={popRef} className={styles.pop} style={{ top: pos.top, left: pos.left, width: POP_W }} role="dialog" aria-label="Choose a date">
                    <div className={styles.nav}>
                        <button type="button" className={styles.navBtn} onClick={() => shiftYear(-1)} aria-label="Previous year"><FiChevronsLeft /></button>
                        <button type="button" className={styles.navBtn} onClick={() => shiftMonth(-1)} aria-label="Previous month"><FiChevronLeft /></button>
                        <span className={styles.navTitle}>{MONTHS[view.m]} {view.y}</span>
                        <button type="button" className={styles.navBtn} onClick={() => shiftMonth(1)} aria-label="Next month"><FiChevronRight /></button>
                        <button type="button" className={styles.navBtn} onClick={() => shiftYear(1)} aria-label="Next year"><FiChevronsRight /></button>
                    </div>

                    <div className={styles.dowRow}>
                        {DOW.map((d) => <span key={d}>{d}</span>)}
                    </div>

                    <div className={styles.grid}>
                        {cells.map((c) => {
                            const isSel = !!sel && sel.y === c.y && sel.m === c.m && sel.d === c.d;
                            const isNow = now.y === c.y && now.m === c.m && now.d === c.d;
                            return (
                                <button
                                    type="button"
                                    key={c.y + '-' + c.m + '-' + c.d}
                                    className={`${styles.day} ${c.out ? styles.dayOut : ''} ${isNow ? styles.dayNow : ''} ${isSel ? styles.daySel : ''}`}
                                    onClick={() => pick(toValue(c.y, c.m, c.d))}
                                    aria-label={c.d + ' ' + MONTHS[c.m] + ' ' + c.y}
                                    aria-pressed={isSel}
                                >
                                    {c.d}
                                </button>
                            );
                        })}
                    </div>

                    <div className={styles.foot}>
                        <button type="button" className={styles.footBtn} onClick={() => pick('')}>Clear</button>
                        <button type="button" className={`${styles.footBtn} ${styles.footBtnHot}`} onClick={() => pick(toValue(now.y, now.m, now.d))}>Today</button>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
};

export default HardwareDatePicker;
