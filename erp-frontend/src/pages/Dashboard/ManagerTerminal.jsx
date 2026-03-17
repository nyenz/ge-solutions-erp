// PATH: erp-frontend/src/pages/Dashboard/ManagerTerminal.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDatabase, FiPhoneCall, FiTrendingUp,
    FiFilePlus, FiClock, FiCheckSquare,
    FiMapPin, FiActivity, FiGrid
} from 'react-icons/fi';
import styles from './Dashboard.module.css';

const ManagerTerminal = ({ stats }) => {
    const navigate = useNavigate();

    return (
        <div className={styles.terminalWrapper}>

            {/* ── STAT HUD ── */}
            <div className={styles.statGrid}>
                <div className={`${styles.statTile} ${styles.azure}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiDatabase /></div>
                    <div className={styles.statValue}>{stats?.totalPlots || 0}</div>
                    <div className={styles.statLabel}>PLOTS UNDER MANAGEMENT</div>
                </div>
                <div className={`${styles.statTile} ${styles.gold}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiPhoneCall /></div>
                    <div className={styles.statValue}>{stats?.staleCallCount || 0}</div>
                    <div className={styles.statLabel}>PENDING RECOVERY CALLS</div>
                </div>
                <div className={`${styles.statTile} ${styles.emerald}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiTrendingUp /></div>
                    <div className={styles.statValue}>+{stats?.plotsGrowth || 0}</div>
                    <div className={styles.statLabel}>NEW INTAKES (7D)</div>
                </div>
                <div className={`${styles.statTile} ${styles.ruby}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiCheckSquare /></div>
                    <div className={styles.statValue}>{stats?.readyForReleaseCount || 0}</div>
                    <div className={styles.statLabel}>AWAITING FINAL HANDOVER</div>
                </div>
            </div>

            {/* ── MAIN GRID ── */}
            <div className={styles.mainGrid}>

                <div className={styles.leftCol}>
                    <div className={styles.hwPanel}>
                        <div className={styles.panelHeader}>
                            <FiClock aria-hidden="true" /> ARCHIVE PROCESSING STATUS
                        </div>
                        <div className={styles.panelInner}>
                            {[
                                { n: 1, label: 'COMMITMENT' },
                                { n: 2, label: 'FIELD WORK' },
                                { n: 3, label: 'DOCUMENTATION' },
                                { n: 4, label: 'DEED PLAN' },
                                { n: 5, label: 'HANDOVER READY' },
                            ].map(item => {
                                const val = stats?.stageDistribution?.[item.n] || 0;
                                const pct = ((val / (stats?.totalPlots || 1)) * 100).toFixed(0);
                                return (
                                    <div key={item.n} className={styles.gaugeRow}>
                                        <div className={styles.gaugeLabel}>
                                            <span>PHASE 0{item.n}: {item.label}</span>
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
                </div>

                <div className={styles.rightCol}>
                    <div className={styles.hwPanel}>
                        <div className={styles.panelHeader}>
                            <FiGrid aria-hidden="true" /> OPERATIONAL LAUNCHPAD
                        </div>
                        <div className={styles.panelInner}>
                            <div className={styles.launchPad}>
                                <button className={styles.launchBtn} onClick={() => navigate('/land/new')}      aria-label="New intake"><FiFilePlus  aria-hidden="true" /> NEW INTAKE</button>
                                <button className={styles.launchBtn} onClick={() => navigate('/recovery')}      aria-label="Recovery hub"><FiPhoneCall aria-hidden="true" /> RECOVERY HUB</button>
                                <button className={styles.launchBtn} onClick={() => navigate('/land/projects')} aria-label="View ledger"><FiMapPin    aria-hidden="true" /> VIEW LEDGER</button>
                                <button className={styles.launchBtn} onClick={() => navigate('/settings')}      aria-label="My profile"><FiActivity   aria-hidden="true" /> MY PROFILE</button>
                            </div>
                            <div className={styles.auditNote}>
                                <FiActivity aria-hidden="true" className={styles.auditNoteIcon} />
                                All actions are logged to the forensic audit ledger for Root oversight.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ManagerTerminal;