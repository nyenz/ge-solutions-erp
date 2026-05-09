// PATH: erp-frontend/src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import landService from '../../services/landService';
import RootTerminal from './RootTerminal';
import ManagerTerminal from './ManagerTerminal';
import styles from './Dashboard.module.css';
import { FiRefreshCcw } from 'react-icons/fi';
import ErrorMessage from '../../components/common/ErrorMessage';

const Dashboard = () => {
    const { user } = useAuth();
    const [stats,   setStats]   = useState(null);
    const [loading, setLoading] = useState(true);
    const [error,   setError]   = useState(null);

    const syncCockpitData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await landService.getDashboardSummary();
            setStats(data);
        } catch (err) {
            console.error('COCKPIT_SYNC_FAULT', err);
            setError('REGISTRY SIGNAL LOST — DATABASE UNREADABLE');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { syncCockpitData(); }, [syncCockpitData]);

    if (loading) return (
        <div className={styles.bootScreen} role="status" aria-label="Loading dashboard">
            <div className={styles.spinner} aria-hidden="true" />
            <span className={styles.bootLabel}>Loading dashboard...</span>
        </div>
    );

    if (error) return (
        <div className={styles.container}>
            <div style={{ maxWidth: 520, margin: '80px auto' }}>
                <ErrorMessage
                    type="network"
                    title="Can't load dashboard"
                    message="The server isn't responding right now. Check your connection, then try again."
                    onRetry={syncCockpitData}
                    retryLabel="Reload Dashboard"
                />
            </div>
        </div>
    );

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.titleBlock}>
                    <h1 className={styles.pageTitle}>System Dashboard</h1>
                    <p className={styles.pageSubtitle}>
                        {user?.isRoot ? 'ROOT OWNER ACCESS' : 'MANAGER ACCESS'}
                        {' · '}SYSTEM ACTIVE
                    </p>
                </div>
                <div className={styles.syncBadge} aria-live="polite">
                    LAST SYNC: {new Date().toLocaleTimeString()}
                </div>
            </header>

            {user?.isRoot
                ? <RootTerminal stats={stats} />
                : <ManagerTerminal stats={stats} />
            }
        </div>
    );
};

export default Dashboard;