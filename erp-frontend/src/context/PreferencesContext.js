// PATH: erp-frontend/src/context/PreferencesContext.js
import { createContext } from 'react';

export const DEFAULT_PREFS = {
    theme: 'light',      // light | dark   -- page background and chrome
    uiScale: '100',      // 90 | 100 | 110 | 125
    statSize: 'standard',// small | standard | large
    motion: 'full',      // full | reduced
    tips: 'normal',      // normal | slow | off
    contrast: 'normal',  // normal | high
    notifPoll: '300',    // 300 | 900 | 0 (seconds) -- bell auto-refresh, 0 = manual only
};

export const PreferencesContext = createContext({
    prefs: DEFAULT_PREFS,
    setPref: () => {},
    resetPrefs: () => {},
});
