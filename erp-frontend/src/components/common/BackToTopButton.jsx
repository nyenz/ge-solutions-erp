import React, { useEffect, useState } from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';

function findScroller() {
  const cands = [
    document.querySelector('[class*="scrollArea"]'),
    document.querySelector('[class*="mainContent"]'),
  ];
  for (const el of cands) if (el && el.scrollHeight > el.clientHeight + 40) return el;
  return document.scrollingElement || document.documentElement;
}

export default function BackToTopButton() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const scroller = findScroller();
    const onScroll = () => setShow((scroller.scrollTop || window.scrollY || 0) > 320);
    scroller.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
    return () => { scroller.removeEventListener('scroll', onScroll); window.removeEventListener('resize', onScroll); };
  }, []);
  const toTop = () => { const s = findScroller(); s.scrollTo({ top: 0, behavior: 'smooth' }); };
  return (
    <button type="button" className={`${styles.backToTop} ${show ? styles.show : ''}`} onClick={toTop} aria-label="Back to top" tabIndex={show ? 0 : -1}>
      <FiArrowUp aria-hidden="true" />
    </button>
  );
}
