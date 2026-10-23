// PATH: erp-frontend/src/context/PreferencesContext.js
import { createContext } from 'react';

export const DEFAULT_PREFS = {
    theme: 'ges',        // fix233: ges (B GES DAYLIGHT, default) | gesnavy (C GES NAVY) | classic (A, the old CREAM) | dark (SLATE) | bright (LIGHT)
                         // the old value 'light' (CREAM) is no longer allowed, so it falls back to the new default once
    uiScale: '100',      // 90 | 100 | 110 | 125
    statSize: 'standard',// small | standard | large
    motion: 'full',      // full | reduced
    tips: 'normal',      // normal | fast | off (fix226: FAST replaced SLOW)
    contrast: 'normal',  // normal | high
    notifPoll: '300',    // 300 | 900 | 0 (seconds) -- bell auto-refresh, 0 = manual only
    landing: 'dashboard',// dashboard | ledger | recovery | clients -- start page (fix181, 14.0a); Employee has none
};

// fix181 (15.1j): the only values each setting may hold; a damaged or hand-edited value falls back to the default.
export const PREF_ALLOWED = {
    theme: ['ges', 'gesnavy', 'classic', 'dark', 'bright'],
    uiScale: ['90', '100', '110', '125'],
    statSize: ['small', 'standard', 'large'],
    motion: ['full', 'reduced'],
    tips: ['normal', 'fast', 'off'],
    contrast: ['normal', 'high'],
    notifPoll: ['300', '900', '0'],
    landing: ['dashboard', 'ledger', 'recovery', 'clients'],
};

export const PreferencesContext = createContext({
    prefs: DEFAULT_PREFS,
    setPref: () => {},
    resetPrefs: () => {},
});
