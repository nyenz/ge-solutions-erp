// PATH: erp-frontend/src/components/common/MoneyInput.jsx
// fix285 (David): one money box for every page. The commas appear WHILE you type (1,500,000) and the cursor stays where
// it was. The page receives plain digits ('1500000'), so nothing the server gets changes. A dot, a letter or a minus is
// refused out loud (a short red line under the box), never silently dropped (fix199).
import React, { useLayoutEffect, useRef, useState } from 'react';
import { typeMoney, withCommas } from '../../utils/moneyTyping';
import s from './MoneyInput.module.css';

export default function MoneyInput({ value, onChange, className, id, ariaLabel, placeholder = '0', disabled, onBlur, autoFocus }) {
    const ref = useRef(null);
    const caret = useRef(null);
    const [refused, setRefused] = useState(false);
    const timer = useRef(null);
    const shown = withCommas(value);
    useLayoutEffect(() => {
        if (caret.current !== null && ref.current && document.activeElement === ref.current) {
            try { ref.current.setSelectionRange(caret.current, caret.current); } catch { /* not a text box */ }
        }
        caret.current = null;
    });
    const handle = (e) => {
        const r = typeMoney(e.target.value, e.target.selectionStart);
        if (!r.ok) {
            setRefused(true);
            clearTimeout(timer.current);
            timer.current = setTimeout(() => setRefused(false), 3500);
            return;
        }
        setRefused(false);
        caret.current = r.caret;
        onChange(r.digits);
    };
    return (<>
        <input ref={ref} id={id} className={className} aria-label={ariaLabel} inputMode="numeric" autoComplete="off"
            value={shown} placeholder={placeholder} disabled={disabled} onChange={handle} onBlur={onBlur} autoFocus={autoFocus} />
        {refused && <span className={s.refused} role="alert">Digits only (whole shillings). Commas come by themselves.</span>}
    </>);
}
