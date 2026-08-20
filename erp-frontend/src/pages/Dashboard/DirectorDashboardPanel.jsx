// PATH: erp-frontend/src/pages/Dashboard/DirectorDashboardPanel.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { FiTrendingUp, FiUsers, FiClock, FiPlus, FiX } from 'react-icons/fi';
import landService from '../../services/landService';
import styles from './Dashboard.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const PeriodCard = ({ data, loading }) => {
    if (loading) {
        return (
            <div className={styles.hwPanel}>
                <div className={styles.panelInner}>
                    <div className={styles.periodLoading}>SYNCING...</div>
                </div>
            </div>
        );
    }
    if (!data) return null;

    return (
        <div className={styles.hwPanel}>
            <div className={styles.panelHeader}>
                <FiTrendingUp aria-hidden="true" /> {data.periodLabel}
            </div>
            <div className={styles.panelInner}>
                <div className={styles.periodStatRow}>
                    <div className={styles.periodStatBox}>
                        <label>REVENUE COLLECTED</label>
                        <strong>UGX {fmt(data.revenueCollected)}</strong>
                    </div>
                    <div className={styles.periodStatBox}>
                        <label>TRANSACTIONS</label>
                        <strong>{data.transactionCount}</strong>
                    </div>
                </div>

                <div className={styles.staffActivityHeader}>
                    <FiUsers aria-hidden="true" /> STAFF ACTIVITY
                </div>
                {(!data.staffActivity || data.staffActivity.length === 0) ? (
                    <div className={styles.periodEmpty}>NO ACTIVITY IN THIS WINDOW</div>
                ) : (
                    <div className={styles.staffActivityList}>
                        {data.staffActivity.slice(0, 6).map((s, i) => (
                            <div key={i} className={styles.staffActivityRow}>
                                <span className={styles.staffActivityName}>{s.username}</span>
                                <span className={styles.staffActivityCount}>{s.actionCount} actions</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

const DirectorDashboardPanel = () => {
    const [weekData,  setWeekData]  = useState(null);
    const [monthData, setMonthData] = useState(null);
    const [loading,   setLoading]   = useState(true);

    const [extraPeriod, setExtraPeriod] = useState(null); // null | 'DAY' | 'YEAR'
    const [extraData,   setExtraData]   = useState(null);
    const [extraLoading, setExtraLoading] = useState(false);

    const loadDefault = useCallback(async () => {
        setLoading(true);
        try {
            const [week, month] = await Promise.all([
                landService.getDirectorDashboard('WEEK'),
                landService.getDirectorDashboard('MONTH'),
            ]);
            setWeekData(week);
            setMonthData(month);
        } catch {
            // Non-fatal -- panel stays empty, rest of dashboard still works
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadDefault(); }, [loadDefault]);

    const toggleExtra = async (period) => {
        if (extraPeriod === period) {
            setExtraPeriod(null);
            setExtraData(null);
            return;
        }
        setExtraPeriod(period);
        setExtraLoading(true);
        try {
            const data = await landService.getDirectorDashboard(period);
            setExtraData(data);
        } catch {
            setExtraData(null);
        } finally {
            setExtraLoading(false);
        }
    };

    // Pipeline + company financials are live snapshots -- same on week/month, so read from whichever loaded first
    const snapshot = weekData || monthData || extraData;

    return (
        <div className={styles.directorSection}>
            <div className={styles.directorSectionHeader}>
                <span>DIRECTOR'S DASHBOARD</span>
                <div className={styles.directorToggleRow}>
                    <button
                        className={extraPeriod === 'DAY' ? styles.directorToggleBtnActive : styles.directorToggleBtn}
                        onClick={() => toggleExtra('DAY')}
                    >
                        {extraPeriod === 'DAY' ? <FiX aria-hidden="true" /> : <FiPlus aria-hidden="true" />} TODAY
                    </button>
                    <button
                        className={extraPeriod === 'YEAR' ? styles.directorToggleBtnActive : styles.directorToggleBtn}
                        onClick={() => toggleExtra('YEAR')}
                    >
                        {extraPeriod === 'YEAR' ? <FiX aria-hidden="true" /> : <FiPlus aria-hidden="true" />} THIS YEAR
                    </button>
                </div>
            </div>

            {snapshot && (
                <div className={styles.hwPanel} style={{ marginBottom: 12 }}>
                    <div className={styles.panelHeader}>
                        <FiClock aria-hidden="true" /> COMPANY EXPENSES SNAPSHOT
                    </div>
                    <div className={styles.panelInner}>
                        <div className={`${styles.moneyBox} ${styles.moneyBoxArrears}`}>
                            <label>TOTAL SPENT (ALL TIME)</label>
                            <strong className={styles.valueRuby}>UGX {fmt(snapshot.companyExpensesTotal)}</strong>
                        </div>
                        {snapshot.companyExpensesByCategory && Object.keys(snapshot.companyExpensesByCategory).length > 0 && (
                            <div className={styles.moneyRow} style={{ flexWrap: 'wrap', marginTop: 10 }}>
                                {Object.entries(snapshot.companyExpensesByCategory).map(([cat, amt]) => (
                                    <div className={styles.moneyBox} key={cat}>
                                        <label>{cat.toUpperCase()}</label>
                                        <strong>UGX {fmt(amt)}</strong>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className={styles.directorPeriodGrid}>
                <PeriodCard data={weekData}  loading={loading} />
                <PeriodCard data={monthData} loading={loading} />
                {extraPeriod && <PeriodCard data={extraData} loading={extraLoading} />}
            </div>
        </div>
    );
};

export default DirectorDashboardPanel;
