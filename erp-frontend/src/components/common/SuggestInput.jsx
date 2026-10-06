// PATH: erp-frontend/src/components/common/SuggestInput.jsx
import React, { useEffect, useId, useRef, useState } from 'react';
import styles from './SuggestInput.module.css';

/**
 * SuggestInput -- a normal text box that OFFERS things typed before (fix188, data entry helpers).
 * It looks like the app's own dropdown (HardwareSelect): white list, orange border, orange row when picked.
 * Never the browser's own autocomplete list or <datalist>.
 *
 * It only offers. What is in the box changes ONLY when the person types or picks a row.
 *
 * value        the text in the box
 * onChange     (text) => void          the person typed
 * suggestions  [{ key, value, label?, detail? }]   already worked out by the page (see utils/entryMemory.js)
 * onPick       (suggestion) => void    the person picked a row (default: onChange(suggestion.value))
 * className    the page's own input class (so the box looks like the page's other boxes)
 * hint         small text under the list rows, e.g. "From past projects"
 * + any normal <input> prop (placeholder, inputMode, onBlur, aria-label, autoFocus ...)
 *
 * Keys: Down / Up move, Enter or Tab picks the marked row, Escape closes. Touch: tap a row.
 */
const SuggestInput = ({ value, onChange, suggestions = [], onPick, className = '', hint = '', onBlur, onFocus, onKeyDown, ...rest }) => {
    const [open, setOpen] = useState(false);
    const [at, setAt] = useState(-1);
    const wrapRef = useRef(null);
    const listId = useId();
    const list = suggestions || [];
    const show = open && list.length > 0;

    // the marked row never points past the end of a list that just got shorter
    const mark = at >= list.length ? -1 : at;

    useEffect(() => {
        if (!show) return undefined;
        const away = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', away);
        document.addEventListener('touchstart', away, { passive: true });
        return () => { document.removeEventListener('mousedown', away); document.removeEventListener('touchstart', away); };
    }, [show]);

    const pick = (s) => {
        if (!s) return;
        if (onPick) onPick(s); else onChange(s.value);
        setOpen(false); setAt(-1);
    };

    const keys = (e) => {
        if (onKeyDown) onKeyDown(e);
        if (e.defaultPrevented) return;
        if (e.key === 'ArrowDown') {
            if (!list.length) return;
            e.preventDefault();
            if (!open) { setOpen(true); setAt(0); return; }
            setAt(mark + 1 >= list.length ? 0 : mark + 1);
        } else if (e.key === 'ArrowUp') {
            if (!show) return;
            e.preventDefault();
            setAt(mark <= 0 ? list.length - 1 : mark - 1);
        } else if (e.key === 'Enter') {
            if (show && mark >= 0) { e.preventDefault(); pick(list[mark]); }
        } else if (e.key === 'Tab') {
            if (show && mark >= 0) pick(list[mark]);   // Tab still moves on to the next box
            else setOpen(false);
        } else if (e.key === 'Escape') {
            if (show) { e.preventDefault(); e.stopPropagation(); setOpen(false); setAt(-1); }
        }
    };

    return (
        <div className={styles.wrap} ref={wrapRef}>
            <input
                {...rest}
                className={className}
                value={value}
                autoComplete="off" autoCorrect="off" spellCheck={false}
                role="combobox" aria-autocomplete="list" aria-expanded={show} aria-controls={show ? listId : undefined}
                aria-activedescendant={show && mark >= 0 ? listId + '-' + mark : undefined}
                onChange={(e) => { onChange(e.target.value); setOpen(true); setAt(-1); }}
                onFocus={(e) => { setOpen(true); if (onFocus) onFocus(e); }}
                onBlur={(e) => { if (onBlur) onBlur(e); }}
                onKeyDown={keys}
            />
            {show && (
                <ul className={styles.list} id={listId} role="listbox">
                    {list.map((s, i) => (
                        <li key={s.key || s.value + i} id={listId + '-' + i} role="option" aria-selected={i === mark}
                            className={`${styles.row} ${i === mark ? styles.rowOn : ''}`}
                            /* mousedown, not click: the box must not lose focus before the pick lands */
                            onMouseDown={(e) => { e.preventDefault(); pick(s); }}
                            onMouseEnter={() => setAt(i)}>
                            <span className={styles.main}>{s.label || s.value}</span>
                            {s.detail && <span className={styles.detail}>{s.detail}</span>}
                        </li>
                    ))}
                    {hint && <li className={styles.hint} aria-hidden="true">{hint}</li>}
                </ul>
            )}
        </div>
    );
};

export default SuggestInput;
