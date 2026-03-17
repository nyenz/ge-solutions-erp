// PATH: erp-frontend/src/pages/Dashboard/SharedWidgets.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    FiArrowUpRight, FiActivity, FiDatabase, 
    FiChevronRight, FiAlertCircle, FiPackage, FiCpu
} from 'react-icons/fi';
import styles from './SharedWidgets.module.css';

/**
 * NYENZ HARDWARE TILE: MULTI-VARIANT GAUGE
 * 
 * Variants:
 * - azure (Archive): Technical Data
 * - gold (Recovery): Active Missions
 * - emerald (Release): Success Output
 * - purple (Storage): Physical Inventory
 */
export const StatTile = ({ label, value, trend, icon: Icon, link, variant = "azure", alert = false }) => {
    const navigate = useNavigate();
    
    return (
        <div 
            className={`${styles.statTile} ${styles[variant]} ${alert ? styles.alertPulse : ''} ${link ? styles.clickable : ''}`}
            onClick={() => link && navigate(link)}
        >
            <div className={styles.tileHeader}>
                <div className={styles.iconChassis}>
                    {Icon && <Icon />}
                </div>
                {trend && (
                    <div className={styles.trendIndicator}>
                        <FiArrowUpRight /> <span>{trend}</span>
                    </div>
                )}
            </div>
            
            <div className={styles.tileBody}>
                <div className={styles.labelGroup}>
                    <label>{label}</label>
                    <span className={styles.subDetail}>REGISTRY STATUS: OK</span>
                </div>
                <strong className={styles.massiveValue}>{value}</strong>
            </div>
            
            <div className={styles.footerAccent}></div>
        </div>
    );
};

/**
 * NYENZ BOTTLENECK AUDIT (STATIONARY GRID)
 */
export const BottleneckGauge = ({ stages, total }) => {
    const labels = ["Commitment", "Field Work", "Docs", "Deed Plan", "Release"];
    
    return (
        <div className={styles.bottleneckDeck}>
            {[1, 2, 3, 4, 5].map((n, i) => {
                const count = stages?.[n] || 0;
                const percent = total > 0 ? (count / total) * 100 : 0;
                
                return (
                    <div key={n} className={styles.gaugeChannel}>
                        <div className={styles.channelLabel}>
                            <span className={styles.chNum}>0{n}</span>
                            <span className={styles.chName}>{labels[i]}</span>
                        </div>
                        <div className={styles.chMeter}>
                            <div className={styles.chFill} style={{ width: `${percent}%` }} />
                            <span className={styles.chVal}>{count}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

/**
 * SYSTEMS PULSE (CYAN/ORANGE DUALITY)
 */
export const SystemsPulse = ({ online, actions }) => (
    <div className={styles.pulseControl}>
        <div className={styles.pulseTile}>
            <FiCpu className={styles.cpuIcon} />
            <div className={styles.pulseData}>
                <label>OPERATORS AUTHORIZED</label>
                <strong>{online} SESSIONS</strong>
            </div>
        </div>
        <div className={styles.pulseTile}>
            <FiActivity className={styles.activityIcon} />
            <div className={styles.pulseData}>
                <label>IO ACTIVITY (24H)</label>
                <strong>{actions} OPERATIONS</strong>
            </div>
        </div>
    </div>
);

/**
 * QUICK LAUNCHPAD
 */
export const LaunchBtn = ({ label, icon: Icon, path }) => {
    const navigate = useNavigate();
    return (
        <button className={styles.launchModule} onClick={() => navigate(path)}>
            {Icon && <Icon className={styles.launchIcon} />}
            <span className={styles.launchText}>{label}</span>
            <FiChevronRight className={styles.launchChevron} />
        </button>
    );
};