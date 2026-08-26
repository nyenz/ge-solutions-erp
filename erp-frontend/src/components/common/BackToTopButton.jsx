// PATH: erp-frontend/src/components/common/BackToTopButton.jsx
import React from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';

/**
 * GOLDEN SEED -- STANDARD BACK-TO-TOP
 * A reactive up-arrow: no background, no border -- just the orange arrow
 * with a soft glow so it stays visible on any surface. Hover lifts it.
 */
export default function BackToTopButton({ label = 'Back to top' }) {
    const scrollToTop = () => {
        const scrollArea = document.querySelector('[class*="scrollArea"]');
        if (scrollArea) scrollArea.scrollTo({ top: 0, behavior: 'smooth' });
        else window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    return (
        <button type="button" className={styles.topBtn} onClick={scrollToTop} aria-label={label}>
            <FiArrowUp aria-hidden="true" />
        </button>
    );
}
