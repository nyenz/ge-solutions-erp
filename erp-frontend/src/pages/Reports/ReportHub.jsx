import React from 'react';
import ReportStudio from './ReportStudio';
import styles from './ReportHub.module.css';

export default function ReportHub() {
  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.pageTitle}>Report Studio</h1>
          <p className={styles.pageSubtitle}>Build, view and export company intelligence</p>
        </div>
      </header>
      <ReportStudio />
    </div>
  );
}