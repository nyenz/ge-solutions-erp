import React, { useEffect, useState } from 'react';
import { FiArrowUp } from 'react-icons/fi';
import styles from './BackToTopButton.module.css';

function scrollers() {
  const list = [];
  const a = document.querySelector('[class*="scrollArea"]');
  const b = document.querySelector('[class*="mainContent"]');
  if (a) list.push(a);
  if (b && b !== a) list.push(b);
  return list;
}
function currentY() {
  let y = window.scrollY || 0;
  for (const el of scrollers()) y = Math.max(y, el.scrollTop || 0);
  return y;
}

export default function BackToTopButton() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const onScroll = () => setShow(currentY() > 300);
    document.addEventListener('scroll', onScroll, true);
    window.addEventListener('resize', onScroll);
    onScroll();
    return () => {
      document.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', onScroll);
    };
  }, []);
  const toTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    for (const el of scrollers()) el.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return (
    <button type="button" className={`${styles.backToTop} ${show ? styles.show : ''}`} onClick={toTop} aria-label="Back to top" tabIndex={show ? 0 : -1}>
      <FiArrowUp aria-hidden="true" />
    </button>
  );
}
