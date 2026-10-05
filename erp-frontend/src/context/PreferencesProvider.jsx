// PATH: erp-frontend/src/context/PreferencesProvider.jsx
/**
 * GOLDEN SEED -- APPEARANCE PREFERENCES
 *
 * Everything here is applied by writing data-attributes and CSS variables onto
 * <html>, which is the only way a preference can reach every page without
 * every page having to opt in. The CSS that reads them lives in index.css.
 *
 * fix181 (15.1i): choices are kept per person ON THE DEVICE (localStorage key goldenseed.prefs.v1.<username>), with a
 * device default for the login page and for anyone who has not chosen yet. The office shares devices, so one person's
 * size, theme or start page must not reach the next person. See prefsStore.js.
 *
 * fix181 (15.1d): the first paint already has the right theme and size because a tiny inline script in index.html
 * applies the saved choices before React starts; this provider takes over for changes after that.
 * fix181 (15.1k): a change in another open tab is followed (storage listener).
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
 *   contrast  strengthens table row lines (tables only).
 *   landing   the start page after sign-in (never for Employee; checked against the rank in App.jsx).
 */
import React, { useState, useLayoutEffect, useEffect, useCallback, useMemo } from 'react';
import { PreferencesContext, DEFAULT_PREFS } from './PreferencesContext';
import { currentUsername, keyFor, DEVICE_KEY, readPrefsFor, writePrefsFor, THEME_COLOR } from './prefsStore';

const STAT_SIZES = {
    small:    { label: 'clamp(8px, 0.8vw, 9.5px)',  value: 'clamp(12px, 1.3vw, 15px)',   valueSm: 'clamp(10px, 1.1vw, 12px)', note: 'clamp(7px, 0.75vw, 9px)' },
    standard: { label: 'clamp(8px, 0.85vw, 10px)',  value: 'clamp(13px, 1.45vw, 16.5px)', valueSm: 'clamp(11px, 1.2vw, 13px)', note: 'clamp(7px, 0.8vw, 9px)' },
    large:    { label: 'clamp(9px, 0.95vw, 11px)',  value: 'clamp(16px, 1.8vw, 21px)',    valueSm: 'clamp(13px, 1.4vw, 16px)', note: 'clamp(8px, 0.85vw, 10px)' },
};

export const PreferencesProvider = ({ children }) => {
    const [who, setWho] = useState(currentUsername);
    const [prefs, setPrefs] = useState(() => readPrefsFor(currentUsername()));

    // useLayoutEffect: applied before the browser paints the change
    useLayoutEffect(() => {
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
        document.querySelector('meta[name="theme-color"]')?.setAttribute('content', THEME_COLOR[prefs.theme] || THEME_COLOR.light);
    }, [prefs]);

    // another person signed in on this tab, or another tab changed the choices / the person
    useEffect(() => {
        const reload = () => { const u = currentUsername(); setWho(u); setPrefs(readPrefsFor(u)); };
        const onStorage = (e) => {
            if (e.key === null || e.key === 'gs_user' || e.key === keyFor(currentUsername()) || e.key === DEVICE_KEY) reload();
        };
        window.addEventListener('gs-user-changed', reload);
        window.addEventListener('storage', onStorage);
        return () => { window.removeEventListener('gs-user-changed', reload); window.removeEventListener('storage', onStorage); };
    }, []);

    const setPref = useCallback((key, value) => setPrefs(p => {
        const next = { ...p, [key]: value };
        writePrefsFor(who, next);
        return next;
    }), [who]);
    const resetPrefs = useCallback(() => { writePrefsFor(who, DEFAULT_PREFS); setPrefs(DEFAULT_PREFS); }, [who]);

    const value = useMemo(() => ({ prefs, setPref, resetPrefs }), [prefs, setPref, resetPrefs]);

    return (
        <PreferencesContext.Provider value={value}>
            {children}
        </PreferencesContext.Provider>
    );
};

export default PreferencesProvider;
