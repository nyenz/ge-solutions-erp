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

// fix287: the app page scrolls inside its own area (Shell), not the window. Go to the top of both.
export const scrollPageTop = () => {
    try {
        window.scrollTo({ top: 0, behavior: scrollBehavior() });
        const seen = new Set();
        for (const sel of ['[class*="scrollArea"]', '[class*="mainContent"]']) {
            const el = document.querySelector(sel);
            if (el && !seen.has(el)) { seen.add(el); el.scrollTo({ top: 0, behavior: scrollBehavior() }); }
        }
    } catch { /* never block the page */ }
};
