// PATH: erp-frontend/src/pages/Dashboard/RootTerminal.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiShield, FiDatabase, FiPhoneCall, FiTrendingUp,
    FiLayers, FiActivity, FiFilePlus, FiPieChart,
    FiCreditCard, FiClock, FiGrid
} from 'react-icons/fi';
import styles from './Dashboard.module.css';

const RootTerminal = ({ stats }) => {
    const navigate = useNavigate();
    const liquidityPercent = stats?.collectionVelocity || 0;

    return (
        <div className={styles.terminalWrapper}>

            {/* ── STAT HUD ── */}
            <div className={styles.statGrid}>
                <div className={`${styles.statTile} ${styles.azure}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiDatabase /></div>
                    <div className={styles.statValue}>{stats?.totalPlots || 0}</div>
                    <div className={styles.statLabel}>GLOBAL ARCHIVE VOLUME</div>
                </div>
                <div className={`${styles.statTile} ${styles.gold}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiPhoneCall /></div>
                    <div className={styles.statValue}>{stats?.staleCallCount || 0}</div>
                    <div className={styles.statLabel}>STALE RECOVERY DEBTORS</div>
                </div>
                <div className={`${styles.statTile} ${styles.emerald}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiShield /></div>
                    <div className={styles.statValue}>{liquidityPercent.toFixed(1)}%</div>
                    <div className={styles.statLabel}>CASH COLLECTION VELOCITY</div>
                </div>
                <div className={`${styles.statTile} ${styles.ruby}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiActivity /></div>
                    <div className={styles.statValue}>{stats?.dailyAuditCount || 0}</div>
                    <div className={styles.statLabel}>SYSTEM OPS (24H)</div>
                </div>
            </div>

            {/* ── MAIN GRID ── */}
            <div className={styles.mainGrid}>

                {/* LEFT: Financials + Activity */}
                <div className={styles.leftCol}>
                    <div className={styles.hwPanel}>
                        <div className={styles.panelHeader}>
                            <FiCreditCard aria-hidden="true" /> FINANCIAL LIQUIDITY ASSESSMENT
                        </div>
                        <div className={styles.panelInner}>
                            <div className={styles.financeDisplay}>
                                <div className={styles.moneyRow}>
                                    <div className={styles.moneyBox}>
                                        <label>PORTFOLIO VALUE</label>
                                        <strong>UGX {(stats?.totalArchiveValue || 0).toLocaleString()}</strong>
                                    </div>
                                    <div className={styles.moneyBox}>
                                        <label>LIQUIDITY (PAID)</label>
                                        <strong className={styles.valueEmerald}>
                                            UGX {(stats?.totalCollected || 0).toLocaleString()}
                                        </strong>
                                    </div>
                                </div>
                                <div className={`${styles.moneyBox} ${styles.moneyBoxArrears}`}>
                                    <label>TOTAL OUTSTANDING ARREARS</label>
                                    <strong className={styles.valueRuby}>
                                        UGX {(stats?.outstandingArrears || 0).toLocaleString()}
                                    </strong>
                                </div>
                                <div className={styles.liquidityGauge}>
                                    <div className={styles.gaugeLabel}>
                                        <span>CAPITAL RECOVERY PROGRESS</span>
                                        <span>{liquidityPercent.toFixed(1)}%</span>
                                    </div>
                                    <div className={styles.gaugeTrack}>
                                        <div className={styles.gaugeFill} style={{ width: `${liquidityPercent}%` }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className={styles.hwPanel}>
                        <div className={styles.panelHeader}>
                            <FiActivity aria-hidden="true" /> RECENT ACTIVITY
                        </div>
                        <div className={styles.panelInner}>
                            <div className={styles.activityStream}>
                                {(stats?.recentActivity || []).length === 0 ? (
                                    <div className={styles.activityRow}>
                                        <FiActivity className={styles.activityIcon} aria-hidden="true" />
                                        <div className={styles.activityText}>
                                            <strong className={styles.activityAction}>NO RECENT ACTIVITY</strong>
                                            <span className={styles.activityDetail}>Actions will appear here</span>
                                        </div>
                                    </div>
                                ) : (stats?.recentActivity || []).map((act, i) => (
                                    <div key={i} className={styles.activityRow}>
                                        <FiActivity className={styles.activityIcon} aria-hidden="true" />
                                        <div className={styles.activityText}>
                                            <strong className={styles.activityAction}>
                                                {act.action} · {act.performedBy}
                                            </strong>
                                            <span className={styles.activityDetail}>
                                                {act.details?.substring(0, 50)} · {new Date(act.timestamp).toLocaleTimeString()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT: Pipeline + Launchpad */}
                <div className={styles.rightCol}>
                    <div className={styles.hwPanel}>
                        <div className={styles.panelHeader}>
                            <FiClock aria-hidden="true" /> PIPELINE BOTTLENECKS
                        </div>
                        <div className={styles.panelInner}>
                            {[
                                { n: 1, label: 'COMMITMENT' },
                                { n: 2, label: 'FIELD WORK' },
                                { n: 3, label: 'DOCUMENTATION' },
                                { n: 4, label: 'DEED PLAN' },
                                { n: 5, label: 'RELEASE READY' },
                            ].map(item => {
                                const val = stats?.stageDistribution?.[item.n] || 0;
                                const pct = ((val / (stats?.totalPlots || 1)) * 100).toFixed(0);
                                return (
                                    <div key={item.n} className={styles.gaugeRow}>
                                        <div className={styles.gaugeLabel}>
                                            <span>{item.label}</span>
                                            <span>{val} FILES</span>
                                        </div>
                                        <div className={styles.gaugeTrack}>
                                            <div
                                                className={styles.gaugeFill}
                                                style={{
                                                    width: `${pct}%`,
                                                    background: item.n === 5 ? 'var(--emerald)' : 'var(--orange)',
                                                }}
                                                role="progressbar"
                                                aria-valuenow={Number(pct)}
                                                aria-valuemin={0}
                                                aria-valuemax={100}
                                                aria-label={`${item.label}: ${val} files, ${pct}%`}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    <div className={styles.hwPanel}>
                        <div className={styles.panelHeader}>
                            <FiGrid aria-hidden="true" /> COMMAND LAUNCHPAD
                        </div>
                        <div className={styles.panelInner}>
                            <div className={styles.launchPad}>
                                <button className={styles.launchBtn} onClick={() => navigate('/land/new')}      aria-label="Go to asset intake"><FiFilePlus  aria-hidden="true" /> ASSET INTAKE</button>
                                <button className={styles.launchBtn} onClick={() => navigate('/land/projects')} aria-label="Go to master ledger"><FiLayers    aria-hidden="true" /> MASTER LEDGER</button>
                                <button className={styles.launchBtn} onClick={() => navigate('/reports')}       aria-label="Go to analytics"><FiPieChart  aria-hidden="true" /> ANALYTICS</button>
                                <button className={styles.launchBtn} onClick={() => navigate('/recovery')}      aria-label="Go to recovery"><FiPhoneCall aria-hidden="true" /> RECOVERY</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RootTerminal;