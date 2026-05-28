# PATH: fix.py
import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content.strip() + '\n')
    print(f"OK (OVERWRITTEN): {path}")

BASE = os.path.dirname(os.path.abspath(__file__))

print("=== EXECUTING MASTER UNIFORMITY OVERWRITE (FIXED) ===")

# ─── 1. OVERWRITE: RecoveryPortal.module.css (Robust & Bold) ──────────
rec_css_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.module.css')
write(rec_css_path, '''
.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238,140,58,0.18);
    --orange-border: rgba(238,140,58,0.3);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg,#1c3335 0%,#213E40 100%);
    --red:           #ef4444;
    --green:         #10b981;
    --cyan:          #06b6d4;

    /* Official Uniform Font Sizes */
    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(9px,  0.9vw, 11px);
    --fs-label:  clamp(8px,  0.85vw, 10px);
    --fs-value:  clamp(13px, 1.4vw, 16px);
    --fs-tag:    clamp(8px,  0.82vw, 10px);
    --fs-input:  clamp(12px, 1.2vw, 14px);
    --fs-th:     clamp(9px,  0.9vw, 11px);
    --fs-td:     clamp(12px, 1.2vw, 14px);
    --fs-meta:   clamp(10px, 1vw,   12px);
    --fs-btn:    clamp(10px, 1vw,   12px);

    --radius:    12px;
    --radius-sm: 8px;

    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

/* ── HUD CARDS ── */
.finHUD { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.finHUDCard {
    background: var(--panel-bg); border: 1.5px solid var(--orange-border);
    border-radius: var(--radius); padding: 18px 24px;
    display: flex; flex-direction: column; gap: 4px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.finHUDCard label { font-family:'DM Sans'; font-size:var(--fs-label); font-weight:900; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:1px; }
.finHUDCard strong { font-family:'Space Mono'; font-size:clamp(16px, 1.8vw, 22px); font-weight:700; color: #fff; }

/* ── HEADER & SEARCH ── */
.pageHeader {
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
    gap: 12px; margin-bottom: 24px; border-left: 5px solid var(--orange);
    padding: 16px 28px; background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0; backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0,0,0,0.07);
}
.pageTitle { font-family: 'Cinzel'; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; margin: 0; }
.pageSubtitle { font-family: 'DM Sans'; color: #64748b; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; margin: 0; }

.modeSwitch { display: flex; background: var(--navy); padding: 4px; border-radius: 8px; border: 1px solid var(--orange-border); gap: 4px; }
.modeActive { background: var(--orange); color: var(--navy); border: none; padding: 8px 16px; border-radius: 6px; font-weight: 900; font-size: var(--fs-btn); cursor: pointer; display: flex; align-items: center; gap: 6px; }
.modeInactive { background: transparent; color: rgba(255,255,255,0.7); border: none; padding: 8px 16px; border-radius: 6px; font-weight: 900; font-size: var(--fs-btn); cursor: pointer; display: flex; align-items: center; gap: 6px; }

.filterBar { position: sticky; top: 0; z-index: 200; padding: 12px 0; display: flex; flex-direction: column; gap: 12px; }
.searchInner {
    position: relative; display: flex; align-items: center; background: #fff;
    border: 1.5px solid #c8d6d7; border-radius: 8px; height: 44px; width: 100%; max-width: 500px;
}
.searchInput { width: 100%; border: none; outline: none; background: transparent; color: var(--navy); padding: 0 40px !important; font-size: var(--fs-input); font-weight: 800; }
.searchIcon { position: absolute; left: 12px; color: var(--orange); font-size: 18px; }

.filterPills { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; }
.filterPill { background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 8px 18px; border-radius: 6px; font-weight: 900; font-size: var(--fs-btn); text-transform: uppercase; cursor: pointer; }
.filterPillActive { background: var(--orange) !important; color: var(--navy) !important; border-color: var(--orange) !important; }

/* ── MISSION CARDS (THE ROBUST PANELS) ── */
.missionGrid { display: flex; flex-direction: column; gap: 16px; }
.sectionHeader {
    font-family:'DM Sans'; font-size:var(--fs-btn); font-weight:900; color: #fff;
    background: rgba(26,46,48,0.75); padding: 8px 16px; border-radius: 6px; border: 1px solid var(--orange-border); align-self: flex-start; margin-bottom: 8px;
}
.missionCard {
    background: var(--panel-bg); border: 1.5px solid var(--orange-border);
    border-radius: var(--radius); box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    transition: transform 0.2s, border-color 0.2s; overflow: hidden;
}
.missionCard:hover { transform: translateY(-2px); border-color: var(--orange); }

.cardHeader { display: flex; flex-direction: column; gap: 12px; padding: 20px 28px; cursor: pointer; }

/* LINE 1: ID and Debt */
.cardTopRow { display: flex; justify-content: space-between; align-items: center; }
.cardTopRowLeft { display: flex; align-items: center; gap: 10px; }
.plotId { font-family: 'Space Mono'; font-size: var(--fs-value); font-weight: 900; color: var(--orange); letter-spacing: 0.5px; }
.backlogPill { background: rgba(239,68,68,0.2); border: 1px solid #ef4444; color: #fca5a5; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 4px; }

.balanceLine { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.balanceLabel { font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.4); text-transform: uppercase; }
.balanceVal { font-family: 'Space Mono'; font-size: 18px; font-weight: 900; color: #fff; }

/* LINE 2: Owner and Actions */
.cardMain { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; }
.ownerLine { font-family: 'DM Sans'; font-size: var(--fs-td); font-weight: 900; color: rgba(255,255,255,0.9); flex: 1; }
.phoneLine { font-family: 'Space Mono'; font-size: var(--fs-meta); color: var(--orange); font-weight: 700; margin: 0 20px; }

.logCallBtnSmall {
    background: var(--orange); color: var(--navy); border: none; border-radius: 6px;
    font-weight: 900; font-size: var(--fs-btn); padding: 10px 20px; cursor: pointer;
    display: flex; align-items: center; gap: 8px; transition: 0.2s;
}
.logCallBtnSmall:hover { background: #f09a48; box-shadow: 0 0 15px rgba(238,140,58,0.4); }

.cardBody { padding: 0 28px 24px; border-top: 1px solid rgba(255,255,255,0.05); background: rgba(0,0,0,0.1); }
.timingRow { display: flex; gap: 12px; background: rgba(0,0,0,0.3); padding: 10px 16px; border-radius: 6px; margin: 12px 0; font-size: var(--fs-meta); font-weight: 800; color: rgba(255,255,255,0.6); }

/* MOBILE */
@media (max-width: 600px) {
    .cardTopRow, .cardMain { flex-direction: column; align-items: flex-start; gap: 8px; }
    .balanceLine { align-items: flex-start; }
    .phoneLine { margin: 0; }
    .logCallBtnSmall { width: 100%; justify-content: center; }
}

.legend { display: flex; gap: 16px; padding: 12px 0; }
.legendItem { display: flex; align-items: center; gap: 6px; font-size: var(--fs-meta); font-weight: 800; color: rgba(26,46,48,0.7); }
''')

# ─── 2. OVERWRITE: RecoveryPortal.jsx (Spacious Layout) ──────────────
rec_jsx_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.jsx')
write(rec_jsx_path, """
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch, FiCheckCircle, FiChevronRight, 
    FiMessageSquare, FiSave, FiList, FiCalendar, FiLock, FiUser, 
    FiChevronDown, FiChevronUp, FiX, FiCheckSquare, FiAlertCircle, 
    FiAlertTriangle, FiInfo, FiDollarSign, FiAlertOctagon, FiActivity, FiSettings
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Paid within 14 days', YELLOW: 'Paid within 30 days', RED: 'No recent payment' };

const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [viewMode, setViewMode] = useState('ACTION');
    const [missions, setMissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');
    const [callModal, setCallModal] = useState({ open: false, mission: null });
    const [logContent, setLogContent] = useState('');
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION' ? await recoveryService.getMissionQueue() : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch { console.error("SIGNAL_LOST"); }
        finally { setLoading(false); }
    }, [viewMode]);

    useEffect(() => { loadData(); }, [loadData]);

    const filteredMissions = useMemo(() => {
        let list = missions;
        if (searchTerm.trim()) {
            const t = searchTerm.toLowerCase();
            list = list.filter(m => m.ownerName.toLowerCase().includes(t) || m.phoneNumber.includes(t) || m.plots.some(p => p.plotNumber.toLowerCase().includes(t)));
        }
        if (statusFilter === 'BACKLOG') list = list.filter(m => m.hasBacklogPlots);
        if (statusFilter === 'ACTIVE')  list = list.filter(m => !m.hasBacklogPlots);
        return list;
    }, [missions, searchTerm, statusFilter]);

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Call Recovery</h1>
                    <p className={styles.pageSubtitle}>Log client calls and record payments</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.modeSwitch}>
                        <button className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive} onClick={() => setViewMode('ACTION')}><FiList /> DUE FOR CALL</button>
                        <button className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive} onClick={() => setViewMode('FORECAST')}><FiCalendar /> ALL TARGETS</button>
                    </div>
                </div>
            </header>

            <div className={styles.finHUD}>
                <div className={styles.finHUDCard}><label>ACTIVE TITLES OWED</label><strong>UGX {fmt(missions.filter(m => !m.hasBacklogPlots).reduce((s, m) => s + m.totalDemand, 0))}</strong></div>
                <div className={styles.finHUDCard}><label>BACKLOG TOTAL OWED</label><strong>UGX {fmt(missions.filter(m => m.hasBacklogPlots).reduce((s, m) => s + m.totalDemand, 0))}</strong></div>
                <div className={styles.finHUDCard}><label>STORAGE FEES</label><strong>UGX {fmt(missions.reduce((s, m) => s + m.totalStorageFees, 0))}</strong></div>
            </div>

            <div className={styles.filterBar}>
                <div className={styles.searchInner}><FiSearch className={styles.searchIcon} /><input className={styles.searchInput} placeholder="Search names, plots, phones..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} /></div>
                <div className={styles.filterPills}>
                    {['ALL', 'ACTIVE', 'BACKLOG'].map(f => (
                        <button key={f} className={`${styles.filterPill} ${statusFilter === f ? styles.filterPillActive : ''}`} onClick={() => setStatusFilter(f)}>{f}</button>
                    ))}
                </div>
            </div>

            <div className={styles.legend}>
                {Object.entries(BADGE_COLORS).map(([k, c]) => (
                    <span key={k} className={styles.legendItem}><span style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />{BADGE_LABELS[k]}</span>
                ))}
            </div>

            <div className={styles.missionGrid}>
                {filteredMissions.map(m => (
                    <div key={m.clientId} className={`${styles.missionCard} ${m.hasBacklogPlots ? styles.cardBacklog : ''}`}>
                        <div className={styles.cardHeader} onClick={() => setExpandedId(expandedId === m.clientId ? null : m.clientId)}>
                            <div className={styles.cardTopRow}>
                                <div className={styles.cardTopRowLeft}>
                                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: BADGE_COLORS[m.plots[0].paymentHealthBadge] }} />
                                    <span className={styles.plotId}>{m.plots.map(p => p.plotNumber).join(' & ')}</span>
                                    {m.hasBacklogPlots && <span className={styles.backlogPill}>BACKLOG</span>}
                                </div>
                                <div className={styles.balanceLine}>
                                    <span className={styles.balanceLabel}>TOTAL OWED</span>
                                    <span className={`${styles.balanceVal} ${m.hasBacklogPlots ? styles.balanceRed : ''}`}>UGX {fmt(m.totalDemand)}</span>
                                </div>
                            </div>
                            <div className={styles.cardMain}>
                                <span className={styles.ownerLine}>{m.ownerName}</span>
                                <span className={styles.phoneLine}>{m.phoneNumber}</span>
                                <div className={styles.cardSideActions}>
                                    <button className={styles.logCallBtnSmall} disabled={m.isLocked} onClick={(e) => { e.stopPropagation(); setCallModal({ open: true, mission: m.plots[0] }); }}>
                                        <FiPhoneCall /> {m.isLocked ? 'LOCKED' : 'LOG CALL'}
                                    </button>
                                    {expandedId === m.clientId ? <FiChevronUp className={styles.expandIcon} /> : <FiChevronDown className={styles.expandIcon} />}
                                </div>
                            </div>
                        </div>
                        {expandedId === m.clientId && (
                            <div className={styles.cardBody}>
                                <div className={styles.timingRow}><FiClock /> Last: {m.lastContactDate} | Next: {m.nextCallDue} | Monthly: {m.monthlyCallCount}/2</div>
                                {m.plots.map(p => (
                                    <div key={p.projectId} className={styles.plotSubCard}>
                                        <div style={{display:'flex', justifyContent:'space-between', marginBottom:8}}>
                                            <strong style={{color:'var(--orange)'}}>{p.plotNumber}</strong>
                                            <span style={{fontSize:10, opacity:0.5}}>Box: {p.physicalBoxNumber}</span>
                                        </div>
                                        <div className={styles.finDetail}>
                                            <div className={styles.finDetailRow}><span>Arrears</span><strong>UGX {fmt(p.isBacklog ? p.totalBacklogOwed : p.currentBalance)}</strong></div>
                                            <div className={styles.finDetailRow}><span>Last Note</span><i>"{p.lastInteractionNote}"</i></div>
                                        </div>
                                        <div className={styles.expandedActions}>
                                            <button className={styles.folderBtn} onClick={() => navigate(`/folder/${p.projectId}`)}>OPEN FOLDER</button>
                                            {isAdmin && <button className={styles.payBtn} onClick={() => navigate(`/folder/${p.projectId}?action=pay`)}>RECORD PAYMENT</button>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <HardwareModal isOpen={callModal.open} onClose={() => setCallModal({ open: false, mission: null })} title="LOG CALL">
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>INTERACTION NOTES</label>
                    <textarea className={modalStyles.modalTextarea} value={logContent} onChange={e => setLogContent(e.target.value)} placeholder="Type result of call..." />
                </div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton onClick={async () => {
                        await recoveryService.logRecoveryCall(callModal.mission.projectId, logContent);
                        setCallModal({ open: false, mission: null });
                        setLogContent('');
                        loadData();
                    }} icon={FiSave}>SAVE LOG</HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};
export default RecoveryPortal;
""")

# ─── 3. PATCH: SettingsPage.jsx (Legend Added) ──────────────────────
set_jsx_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'settings', 'SettingsPage.jsx')
try:
    jsx_content = read(set_jsx_path)
    old_header = '<div className={styles.ledgerActions}>'
    new_header = '''
                    <div className={styles.statusLegend}>
                        <span className={`${styles.legendDot} ${styles.dotGreen}`}></span>
                        <span className={styles.legendText}>Active Operator</span>
                        <span className={styles.legendSep}></span>
                        <span className={`${styles.legendDot} ${styles.dotRed}`}></span>
                        <span className={styles.legendText}>Suspended / Inactive</span>
                    </div>
                    <div className={styles.ledgerActions}>'''
    if old_header in jsx_content and 'statusLegend' not in jsx_content:
        jsx_content = jsx_content.replace(old_header, new_header)
        with open(set_jsx_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(jsx_content)
        print("OK (PATCHED): SettingsPage Legend Added")
except Exception as e:
    print(f"ERROR: SettingsPage patch failed: {e}")

print("\n=== COMPLETE: UNIFORMITY RESTORED ===")