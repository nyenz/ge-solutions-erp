// PATH: erp-frontend/src/utils/motion.js
// fix226 (David): "make sure the settings page affects the app as required throughout". Settings > Animation = REDUCED
// stops CSS movement (index.css); this is the same switch for movement started from code (smooth scrolling, sliding tabs).
export const calmMotion = () => {
    if (typeof document === 'undefined') return false;
    if (document.documentElement.getAttribute('data-motion') === 'reduced') return true;
    try { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); } catch { return false; }
};

/** 'auto' when movement is turned off, else 'smooth' (for scrollTo / scrollIntoView). */
export const scrollBehavior = () => (calmMotion() ? 'auto' : 'smooth');
