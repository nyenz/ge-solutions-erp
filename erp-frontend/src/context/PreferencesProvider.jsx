// PATH: erp-frontend/src/context/PreferencesProvider.jsx
/**
 * GOLDEN SEED -- APPEARANCE PREFERENCES
 *
 * Everything here is applied by writing data-attributes and CSS variables onto
 * <html>, which is the only way a preference can reach every page without
 * every page having to opt in. The CSS that reads them lives in index.css.
 *
 * Choices are per-device, in localStorage, not per-account on the server. That
 * is deliberate: "this screen is too small to read" is a fact about the screen
 * in front of you, not about who you are, and the office shares logins across
 * a desktop and two phones.
 *
 * WHAT EACH ONE ACTUALLY DOES -- no setting here is decorative:
 *   theme     swaps the page background and the sidebar rail between the
 *             cream original and a slate dark. Panels stay dark navy in both,
 *             because the panel palette is still hard-coded per page; a full
 *             inversion needs that tokenised first.
 *   uiScale   zoom on #root. The app is laid out in px and clamp(), not rem,
 *             so a root font-size would move almost nothing -- zoom moves all
 *             of it. Tooltips portal into #root rather than <body> so they
 *             scale and stay aligned with it.
 *   statSize  the --stat-* tokens the summary cards read off.
 *   motion    kills animation and transition app-wide.
 *   tips      hover-explainer dwell, or off entirely.
 *   contrast  strengthens table rules and panel edges.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PreferencesContext, DEFAULT_PREFS } from './PreferencesContext';

const KEY = 'goldenseed.prefs.v1';

const readStored = () => {
    try {
        const raw = window.localStorage.getItem(KEY);
        if (!raw) return DEFAULT_PREFS;
        return { ...DEFAULT_PREFS, ...JSON.parse(raw) };
    } catch {
        return DEFAULT_PREFS;
    }
};

// Plain (non-hook) localStorage read, exported for callers -- such as
// App.jsx's pre-provider route elements -- that need a preference value
// before PreferencesProvider has mounted and can't use the context/hook.
export const readPrefs = readStored;

const STAT_SIZES = {
    small:    { label: 'clamp(8px, 0.8vw, 9.5px)',  value: 'clamp(12px, 1.3vw, 15px)',   valueSm: 'clamp(10px, 1.1vw, 12px)', note: 'clamp(7px, 0.75vw, 9px)' },
    standard: { label: 'clamp(8px, 0.85vw, 10px)',  value: 'clamp(13px, 1.45vw, 16.5px)', valueSm: 'clamp(11px, 1.2vw, 13px)', note: 'clamp(7px, 0.8vw, 9px)' },
    large:    { label: 'clamp(9px, 0.95vw, 11px)',  value: 'clamp(16px, 1.8vw, 21px)',    valueSm: 'clamp(13px, 1.4vw, 16px)', note: 'clamp(8px, 0.85vw, 10px)' },
};

export const PreferencesProvider = ({ children }) => {
    const [prefs, setPrefs] = useState(readStored);

    useEffect(() => {
        const root = document.documentElement;
        root.setAttribute('data-theme', prefs.theme);
        root.setAttribute('data-motion', prefs.motion);
        root.setAttribute('data-tips', prefs.tips);
        root.setAttribute('data-contrast', prefs.contrast);
        root.style.setProperty('--ui-scale', String(Number(prefs.uiScale || 100) / 100));

        const s = STAT_SIZES[prefs.statSize] || STAT_SIZES.standard;
        root.style.setProperty('--stat-label', s.label);
        root.style.setProperty('--stat-value', s.value);
        root.style.setProperty('--stat-value-sm', s.valueSm);
        root.style.setProperty('--stat-note', s.note);

        try { window.localStorage.setItem(KEY, JSON.stringify(prefs)); } catch { /* private mode */ }
    }, [prefs]);

    const setPref = useCallback((key, value) => setPrefs(p => ({ ...p, [key]: value })), []);
    const resetPrefs = useCallback(() => setPrefs(DEFAULT_PREFS), []);

    const value = useMemo(() => ({ prefs, setPref, resetPrefs }), [prefs, setPref, resetPrefs]);

    return (
        <PreferencesContext.Provider value={value}>
            {children}
        </PreferencesContext.Provider>
    );
};

export default PreferencesProvider;
