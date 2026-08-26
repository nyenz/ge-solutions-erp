// PATH: erp-frontend/src/components/common/BackToTopButton.jsx
import React from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';

/**
 * GOLDEN SEED -- SHARED BACK-TO-TOP CONTROL
 *
 * Standardized "scroll to top" button for long-scrolling pages, so each
 * page doesn't reimplement its own low-visibility icon button.
 *
 * Scrolls the app shell's main scroll container (Shell.module.css's
 * .scrollArea) rather than the window, since that's what actually
 * scrolls in this layout. Found via a partial class-name match because
 * CSS-module class names are hashed at build time -- the same pattern
 * IntakePage.jsx already uses to find the sidebar toggle. Falls back to
 * window.scrollTo if, for some reason, that container isn't found.
 */
export default function BackToTopButton({ label = 'Back to top' }) {
    const scrollToTop = () => {
        const scrollArea = document.querySelector('[class*="scrollArea"]');
        if (scrollArea) {
            scrollArea.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    return (
        <button type="button" className={styles.topBtn} onClick={scrollToTop} aria-label={label}>
            <FiArrowUp />
        </button>
    );
}
