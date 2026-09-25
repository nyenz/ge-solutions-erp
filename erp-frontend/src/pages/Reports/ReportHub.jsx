// PATH: erp-frontend/src/pages/Reports/ReportHub.jsx
// GOLDEN SEED -- REPORTS PAGE SHELL (fix84).
// Passes the two props the studio needs (money gate + refresh signal) and
// uses the header classes ReportHub.module.css actually defines.
import React, { useState } from 'react';
import { FiRefreshCw } from 'react-icons/fi';
import { HeaderActions, HeaderButton } from '../../components/common/HeaderButton';
import { useAuth } from '../../hooks/useAuth';
import ReportStudio from './ReportStudio';
import styles from './ReportHub.module.css';

const ReportHub = () => {
  const { user } = useAuth();
  const canSeeMoney = !!(user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR');
  const [reloadToken, setReloadToken] = useState(0);
  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Report Studio</h1>
          <p className={styles.subtitle}>Scope it, pick it, preview it, take it home</p>
        </div>
        <HeaderActions>
          <HeaderButton icon={FiRefreshCw} label="REFRESH" tip="Pull the current dataset again from the server"
            onClick={() => setReloadToken(t => t + 1)} />
        </HeaderActions>
      </header>
      <ReportStudio canSeeMoney={canSeeMoney} reloadToken={reloadToken} />
    </div>
  );
};
export default ReportHub;
