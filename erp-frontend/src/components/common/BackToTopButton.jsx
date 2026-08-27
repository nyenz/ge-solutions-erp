// PATH: erp-frontend/src/components/common/BackToTopButton.jsx
import React from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';
export default function BackToTopButton({ label = 'Back to top' }) {
    const scrollToTop = () => {
        const el = document.querySelector('[class*="scrollArea"]');
        if (el) el.scrollTo({ top: 0, behavior: 'smooth' });
        else window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    return (
        <button type="button" className={styles.topBtn} onClick={scrollToTop} aria-label={label}>
            <FiArrowUp aria-hidden="true" />
        </button>
    );
}
