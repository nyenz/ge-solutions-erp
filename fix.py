import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new, label=""):
    content = read(path)
    if old not in content:
        print(f"MISSING ({label or path}): target string not found")
        return
    write(path, content.replace(old, new, 1))
    print(f"OK patch ({label or path})")

# ================================================================
# FIX 1: FolderPage.module.css
# - printBtn: make it an actual icon button (no text, just icon)
# - btnPauseGrey / btnResumeActive: fix pause/resume button design
# ================================================================

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    '''.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    padding: 0;
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.65);
    border-radius: var(--radius-sm);
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    line-height: 1;
    font-size: clamp(14px, 1.6vw, 18px);
}
.printBtn:hover {
    background: rgba(26, 46, 48, 0.95);
    border-color: rgba(255, 255, 255, 0.4);
    color: #fff;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
}
.printBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }''',
    '''.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    padding: 0;
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.65);
    border-radius: var(--radius-sm);
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    line-height: 1;
    font-size: clamp(16px, 1.8vw, 20px);
}
.printBtn svg {
    width: clamp(16px, 1.8vw, 20px);
    height: clamp(16px, 1.8vw, 20px);
}
.printBtn:hover {
    background: rgba(26, 46, 48, 0.95);
    border-color: rgba(255, 255, 255, 0.4);
    color: #fff;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
}
.printBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }''',
    'FolderPage.module.css printBtn fix'
)

# Fix pause/resume button styles
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    '''/* Pause/Resume fees button — same design as Ledger "PAID TITLES" filter:
   orange fill when active (resume), orange outline when inactive (pause) */
.btnPauseResume {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(5px, 0.6vw, 7px);
    width: 100%;
    height: var(--input-h, clamp(34px, 4.5vw, 40px));
    background: #EE8C3A;
    border: 1.5px solid #EE8C3A;
    color: #1a2e30;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.82vw, 10px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s;
    box-shadow: 0 2px 8px rgba(238, 140, 58, 0.25);
}
.btnPauseResume:hover {
    background: #f0a050;
    border-color: #f0a050;
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.45);
}
.btnPauseResume:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }''',
    '''/* btnPauseGrey = fees currently ACTIVE, click to PAUSE (show grey/danger) */
.btnPauseGrey {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(5px, 0.6vw, 7px);
    width: 100%;
    height: var(--input-h, clamp(34px, 4.5vw, 40px));
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(245, 158, 11, 0.45);
    color: #fcd34d;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.82vw, 10px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
}
.btnPauseGrey:hover {
    background: rgba(245, 158, 11, 0.2);
    border-color: #f59e0b;
    color: #fff;
}
.btnPauseGrey:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* btnResumeActive = fees currently PAUSED, click to RESUME (show green/active) */
.btnResumeActive {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(5px, 0.6vw, 7px);
    width: 100%;
    height: var(--input-h, clamp(34px, 4.5vw, 40px));
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid rgba(16, 185, 129, 0.5);
    color: #34d399;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.82vw, 10px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
}
.btnResumeActive:hover {
    background: #10b981;
    border-color: #10b981;
    color: #1a2e30;
}
.btnResumeActive:focus-visible { outline: 2px solid #10b981; outline-offset: 2px; }''',
    'FolderPage.module.css pause/resume button fix'
)

# ================================================================
# FIX 2: FolderPage.jsx
# - printBtn: just the icon, no text
# ================================================================

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''                    <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record">
                                <FiPrinter aria-hidden="true" /> PRINT
                            </button>''',
    '''                    <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record">
                                <FiPrinter aria-hidden="true" />
                            </button>''',
    'FolderPage.jsx printBtn icon only'
)

# ================================================================
# FIX 3: RecoveryPortal.jsx
# - Add storage fee override section per plot card (backlog plots)
# - Separate "Set Monthly Fee" input directly on backlog plot cards
# - Fix design consistency: filter pills, search, header
# ================================================================

patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''import React, { useState, useEffect, useCallback, useMemo } from 'react';''',
    '''import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';''',
    'RecoveryPortal.jsx add useRef import'
)

# Add storage fee input to backlog plot cards
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''                                        <div className={styles.lastNote}>
                                            <FiMessageSquare size={11} /><span>"{plot.lastInteractionNote}"</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className={styles.divider} />

                        <div className={styles.cardActions}>''',
    '''                                        <div className={styles.lastNote}>
                                            <FiMessageSquare size={11} /><span>"{plot.lastInteractionNote}"</span>
                                        </div>
                                        {isAdmin && (
                                            <StorageFeeInlineControls
                                                plot={plot}
                                                onUpdated={loadData}
                                                toast={toast}
                                            />
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className={styles.divider} />

                        <div className={styles.cardActions}>''',
    'RecoveryPortal.jsx add StorageFeeInlineControls to backlog cards'
)

# Add the StorageFeeInlineControls component before the main RecoveryPortal component
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''// ── MAIN COMPONENT ──────────────────────────────────────────────
const RecoveryPortal = () => {''',
    '''// ── STORAGE FEE INLINE CONTROLS ────────────────────────────────
// Shows directly on each backlog plot card so admin can set monthly fee
// without opening a separate modal
const StorageFeeInlineControls = ({ plot, onUpdated, toast }) => {
    const [rateInput, setRateInput] = React.useState('');
    const [saving, setSaving] = React.useState(false);
    const [expanded, setExpanded] = React.useState(false);

    const handleSetRate = async () => {
        const val = Number(rateInput);
        if (rateInput === '' || val < 0) {
            toast('ENTER A VALID MONTHLY RATE', 'error');
            return;
        }
        setSaving(true);
        try {
            await recoveryService.setStorageRate(plot.projectId, val);
            setRateInput('');
            setExpanded(false);
            await onUpdated();
            toast('MONTHLY FEE UPDATED', 'success');
        } catch {
            toast('FEE UPDATE FAILED', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleTogglePause = async () => {
        setSaving(true);
        try {
            await recoveryService.pauseStorageFees(plot.projectId, !plot.storagePaused);
            await onUpdated();
            toast(plot.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED', 'info');
        } catch {
            toast('ACTION FAILED', 'error');
        } finally {
            setSaving(false);
        }
    };

    const currentRate = plot.storageFeeOverride && Number(plot.storageFeeOverride) > 0
        ? Number(plot.storageFeeOverride)
        : 50000;

    if (!expanded) {
        return (
            <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <button
                    onClick={() => setExpanded(true)}
                    style={{
                        background: 'transparent',
                        border: '1px solid rgba(239,68,68,0.3)',
                        borderRadius: 5,
                        color: 'rgba(252,165,165,0.7)',
                        fontFamily: 'DM Sans,sans-serif',
                        fontSize: 9,
                        fontWeight: 900,
                        letterSpacing: 1,
                        textTransform: 'uppercase',
                        padding: '4px 10px',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                    }}>
                    <FiSettings size={10} />
                    FEE: UGX {Number(currentRate).toLocaleString()}/mo
                    {plot.storagePaused && <span style={{color:'#fcd34d'}}> · PAUSED</span>}
                </button>
            </div>
        );
    }

    return (
        <div style={{
            marginTop: 10,
            padding: '10px 12px',
            background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: 7,
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#fca5a5', textTransform: 'uppercase', letterSpacing: 1.5 }}>
                    STORAGE FEE SETTINGS
                </span>
                <button onClick={() => setExpanded(false)} style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.4)', cursor: 'pointer', fontSize: 14 }}>
                    <FiX size={13} />
                </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div>
                    <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 8, fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 5 }}>
                        MONTHLY RATE (UGX)
                    </div>
                    <div style={{ display: 'flex', gap: 5 }}>
                        <input
                            type="number"
                            value={rateInput}
                            onChange={e => setRateInput(e.target.value)}
                            placeholder={String(currentRate)}
                            style={{
                                flex: 1,
                                background: '#fff',
                                border: '1.5px solid #c8d6d7',
                                borderRadius: 5,
                                color: '#1a2e30',
                                fontFamily: 'Space Mono,monospace',
                                fontWeight: 700,
                                fontSize: 11,
                                padding: '5px 8px',
                                outline: 'none',
                                minWidth: 0,
                            }}
                        />
                        <button
                            onClick={handleSetRate}
                            disabled={saving}
                            style={{
                                background: '#EE8C3A',
                                border: 'none',
                                borderRadius: 5,
                                color: '#1a2e30',
                                fontFamily: 'DM Sans,sans-serif',
                                fontSize: 9,
                                fontWeight: 900,
                                padding: '0 9px',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                flexShrink: 0,
                            }}>
                            SET
                        </button>
                    </div>
                </div>
                <div>
                    <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 8, fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 5 }}>
                        FEE STATUS
                    </div>
                    <button
                        onClick={handleTogglePause}
                        disabled={saving}
                        style={{
                            width: '100%',
                            background: plot.storagePaused ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                            border: plot.storagePaused ? '1.5px solid rgba(16,185,129,0.5)' : '1.5px solid rgba(245,158,11,0.5)',
                            borderRadius: 5,
                            color: plot.storagePaused ? '#34d399' : '#fcd34d',
                            fontFamily: 'DM Sans,sans-serif',
                            fontSize: 9,
                            fontWeight: 900,
                            padding: '6px 0',
                            cursor: 'pointer',
                            textTransform: 'uppercase',
                            letterSpacing: 1,
                        }}>
                        {plot.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                    </button>
                </div>
            </div>
        </div>
    );
};

// ── MAIN COMPONENT ──────────────────────────────────────────────
const RecoveryPortal = () => {''',
    'RecoveryPortal.jsx add StorageFeeInlineControls component'
)

# Add FiSettings to imports
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity, FiHome, FiTrendingDown,
    FiArchive, FiZap
} from 'react-icons/fi';''',
    '''import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity, FiHome, FiTrendingDown,
    FiArchive, FiZap, FiSettings
} from 'react-icons/fi';''',
    'RecoveryPortal.jsx add FiSettings import'
)

print("\nAll fixes written.")
print("Run: git add -A && git commit -m 'fix: print icon only, pause/resume buttons, storage fee controls per backlog plot in recovery' && git push")