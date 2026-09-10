// PATH: erp-frontend/src/components/common/RouteErrorScreen.jsx
import React from 'react';
import { useRouteError, useNavigate } from 'react-router-dom';
import { FiAlertOctagon, FiRefreshCw, FiHome } from 'react-icons/fi';
import styles from './RouteErrorScreen.module.css';

const RouteErrorScreen = () => {
  const error = useRouteError();
  const navigate = useNavigate();
  const msg = error?.message || String(error || 'UNKNOWN FAULT');
  return (
    <div className={styles.wrap}>
      <div className={styles.hud} role="alert">
        <div className={styles.iconBox}><FiAlertOctagon aria-hidden="true" /></div>
        <div className={styles.body}>
          <h1 className={styles.title}>SYSTEM FAULT</h1>
          <p className={styles.msg}>{msg}</p>
          <p className={styles.hint}>The fault is contained to this screen. Your data is safe.</p>
          <div className={styles.actions}>
            <button type="button" className={styles.btn} onClick={() => window.location.reload()}><FiRefreshCw aria-hidden="true" /> RELOAD TERMINAL</button>
            <button type="button" className={styles.btnGhost} onClick={() => navigate('/dashboard')}><FiHome aria-hidden="true" /> BACK TO DASHBOARD</button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default RouteErrorScreen;
