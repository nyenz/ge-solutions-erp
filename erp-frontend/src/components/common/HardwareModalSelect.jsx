// PATH: erp-frontend/src/components/common/HardwareModalSelect.jsx
import React, { useState, useRef, useEffect, useCallback, useId } from 'react';
import { createPortal } from 'react-dom';
import { FiChevronDown, FiCheck } from 'react-icons/fi';
import styles from './HardwareModalSelect.module.css';

/**
 * GOLDEN SEED - HARDWARE MODAL SELECT (fix137)
 *
 * The dropdown for use INSIDE a HardwareModal. It replaces the browser's own
 * <select>, whose white option list cannot be themed.
 *
 * The list is drawn on document.body (fixed position), so the modal's scroll
 * box and the file list can never clip it. It flips upward when there is no
 * room below.
 *
 * options = [{ value, label }]
 * onChange receives the chosen value.
 * Keyboard: Up/Down/Home/End move, Enter or Space picks, Esc closes.
 */
const GAP = 6;
const EDGE = 10;
const MAX_H = 260;
const MIN_W = 190;

const HardwareModalSelect = ({
    value,
    options,
    onChange,
    placeholder = 'Choose',
    emptyText = 'Nothing to choose from',
    ariaLabel,
    compact = false,
    disabled = false,
    className = '',
}) => {
    const [open, setOpen] = useState(false);
    const [active, setActive] = useState(-1);
    const [pos, setPos] = useState(null);
    const triggerRef = useRef(null);
    const panelRef = useRef(null);
    const listId = useId();

    const selectedIdx = options.findIndex(o => o.value === value);
    const selected = selectedIdx >= 0 ? options[selectedIdx] : null;

    const place = useCallback(() => {
        const el = triggerRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const width = Math.min(Math.max(r.width, MIN_W), vw - EDGE * 2);
        const left = Math.max(EDGE, Math.min(r.left, vw - width - EDGE));
        const below = vh - r.bottom - GAP - EDGE;
        const above = r.top - GAP - EDGE;
        const flip = below < 170 && above > below;
        const maxHeight = Math.max(120, Math.min(MAX_H, flip ? above : below));
        setPos(flip
            ? { left, width, bottom: vh - r.top + GAP, maxHeight }
            : { left, width, top: r.bottom + GAP, maxHeight });
    }, []);

    const openPanel = () => {
        if (disabled) return;
        place();
        setActive(selectedIdx >= 0 ? selectedIdx : (options.length ? 0 : -1));
        setOpen(true);
    };

    const choose = (opt) => {
        onChange(opt.value);
        setOpen(false);
        if (triggerRef.current) triggerRef.current.focus();
    };

    // close on outside click, follow the trigger on scroll / resize
    useEffect(() => {
        if (!open) return undefined;
        const onDown = (e) => {
            if (triggerRef.current && triggerRef.current.contains(e.target)) return;
            if (panelRef.current && panelRef.current.contains(e.target)) return;
            setOpen(false);
        };
        const onScroll = (e) => {
            if (panelRef.current && panelRef.current.contains(e.target)) return;
            place();
        };
        document.addEventListener('mousedown', onDown);
        window.addEventListener('resize', place);
        window.addEventListener('scroll', onScroll, true);
        return () => {
            document.removeEventListener('mousedown', onDown);
            window.removeEventListener('resize', place);
            window.removeEventListener('scroll', onScroll, true);
        };
    }, [open, place]);

    // keep the highlighted row inside the visible part of the list
    useEffect(() => {
        if (!open || active < 0) return;
        const panel = panelRef.current;
        if (!panel) return;
        const row = panel.querySelector('[data-idx="' + active + '"]');
        if (!row) return;
        if (row.offsetTop < panel.scrollTop) {
            panel.scrollTop = row.offsetTop;
        } else if (row.offsetTop + row.offsetHeight > panel.scrollTop + panel.clientHeight) {
            panel.scrollTop = row.offsetTop + row.offsetHeight - panel.clientHeight;
        }
    }, [open, active, pos]);

    const onKeyDown = (e) => {
        if (disabled) return;
        if (!open) {
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openPanel();
            }
            return;
        }
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            setOpen(false);
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActive(i => Math.min(options.length - 1, i + 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActive(i => Math.max(0, i - 1));
        } else if (e.key === 'Home') {
            e.preventDefault();
            setActive(options.length ? 0 : -1);
        } else if (e.key === 'End') {
            e.preventDefault();
            setActive(options.length - 1);
        } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (options[active]) choose(options[active]); else setOpen(false);
        } else if (e.key === 'Tab') {
            setOpen(false);
        }
    };

    return (
        <div className={`${styles.root} ${className}`}>
            <div
                ref={triggerRef}
                role="combobox"
                tabIndex={disabled ? -1 : 0}
                aria-haspopup="listbox"
                aria-expanded={open}
                aria-controls={open ? listId : undefined}
                aria-activedescendant={open && active >= 0 ? listId + '-' + active : undefined}
                aria-label={ariaLabel}
                aria-disabled={disabled || undefined}
                className={`${styles.trigger} ${compact ? styles.compact : ''} ${open ? styles.triggerOpen : ''} ${disabled ? styles.disabled : ''}`}
                onClick={() => (open ? setOpen(false) : openPanel())}
                onKeyDown={onKeyDown}
            >
                <span className={`${styles.value} ${selected ? '' : styles.placeholder}`}>
                    {selected ? selected.label : placeholder}
                </span>
                <FiChevronDown className={styles.chevron} aria-hidden="true" />
            </div>

            {open && pos && createPortal(
                <div
                    ref={panelRef}
                    id={listId}
                    role="listbox"
                    aria-label={ariaLabel}
                    className={styles.panel}
                    style={pos}
                    onMouseDown={(e) => e.preventDefault()}
                >
                    {options.length === 0 && <div className={styles.empty}>{emptyText}</div>}
                    {options.map((opt, i) => (
                        <div
                            key={opt.value}
                            id={listId + '-' + i}
                            data-idx={i}
                            role="option"
                            aria-selected={opt.value === value}
                            title={opt.label}
                            className={`${styles.option} ${i === active ? styles.optionActive : ''} ${opt.value === value ? styles.optionSelected : ''}`}
                            onMouseEnter={() => setActive(i)}
                            onClick={() => choose(opt)}
                        >
                            <span className={styles.optionText}>{opt.label}</span>
                            {opt.value === value && <FiCheck className={styles.check} aria-hidden="true" />}
                        </div>
                    ))}
                </div>,
                document.body
            )}
        </div>
    );
};

export default HardwareModalSelect;
