import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING: {path}")
        print(f"  Could not find: {old[:60]}...")
        return
    content = content.replace(old, new, 1)
    write(path, content)

# ============================================================
# 1. FOLDERPAGE.MODULE.CSS - Unify all button/badge styles
# ============================================================
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'

# Replace the entire buttons section with unified design
patch(
    FOLDER_CSS,
    '''/* ═══════════════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════════════ */
.btn { display: inline-flex; align-items: center; gap: clamp(5px, 0.7vw, 8px); padding: clamp(9px, 1.2vw, 12px) clamp(12px, 1.8vw, 22px); border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif; font-weight: 900; font-size: var(--fs-btn); text-transform: uppercase; letter-spacing: 1px; border: 2px solid transparent; cursor: pointer; white-space: nowrap; transition: background 0.2s, color 0.2s, box-shadow 0.2s, border-color 0.2s; line-height: 1; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.btnPrimary { background: var(--orange); color: var(--navy); border-color: var(--orange); }
.btnPrimary:not(:disabled):hover { background: #f0a050; box-shadow: 0 0 18px rgba(238,140,58,0.4); }
.btnDanger { background: var(--navy); color: var(--red); border-color: var(--red); }
.btnDanger:hover { background: rgba(239,68,68,0.12); }
.unlockMasterBtn { display: inline-flex; align-items: center; gap: clamp(6px, 0.9vw, 9px); background: var(--navy); border: 2px solid var(--orange); color: var(--orange); padding: clamp(9px, 1.2vw, 12px) clamp(14px, 2vw, 26px); border-radius: var(--radius-sm); font-weight: 900; font-size: var(--fs-btn); letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; white-space: nowrap; transition: 0.25s; }
.unlockMasterBtn:hover, .unlockMasterBtn:focus-visible { background: var(--orange); color: var(--navy); box-shadow: 0 0 20px rgba(238,140,58,0.4); outline: none; }
.purgeBtn { display: inline-flex; align-items: center; gap: clamp(5px, 0.7vw, 7px); background: rgba(69,10,10,0.5); border: 1.5px solid var(--red); color: var(--red); padding: clamp(8px, 1.1vw, 10px) clamp(12px, 1.5vw, 16px); border-radius: var(--radius-sm); font-weight: 900; font-size: var(--fs-btn); text-transform: uppercase; cursor: pointer; transition: 0.2s; white-space: nowrap; flex-shrink: 0; }
.purgeBtn:hover { background: var(--red); color: #fff; }
.printBtn { display: inline-flex; align-items: center; justify-content: center; width: clamp(34px, 4.5vw, 42px); height: clamp(34px, 4.5vw, 42px); background: rgba(26,46,48,0.08); border: 1.5px solid rgba(26,46,48,0.25); color: var(--navy); border-radius: var(--radius-sm); font-size: clamp(15px, 1.8vw, 19px); cursor: pointer; transition: 0.2s; flex-shrink: 0; }
.printBtn:hover { background: var(--navy); color: var(--orange); border-color: var(--navy); }
.handshakeActions { display: flex; gap: clamp(7px, 1vw, 10px); flex-wrap: wrap; }

/* Unified control zone buttons - view mode */
.ctrlBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(10px, 1.3vw, 14px);
    background: rgba(26, 46, 48, 0.08);
    border: 1.5px solid rgba(26, 46, 48, 0.22);
    color: var(--navy);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
}
.ctrlBtn:hover { background: var(--navy); color: #fff; border-color: var(--navy); }
.ctrlBtn:focus-visible { outline: 2px solid var(--orange); }
.ctrlBtnDanger {
    border-color: rgba(239,68,68,0.4);
    color: #ef4444;
    background: rgba(239,68,68,0.08);
}
.ctrlBtnDanger:hover { background: #ef4444; color: #fff; border-color: #ef4444; }
.ctrlBtnSuccess {
    border-color: rgba(34,197,94,0.4);
    color: #22c55e;
    background: rgba(34,197,94,0.08);
}
.ctrlBtnSuccess:hover { background: #22c55e; color: #1a2e30; border-color: #22c55e; }''',
    '''/* ═══════════════════════════════════════════════════════════════════
   BUTTONS  -- unified "pill" system matching Ledger filter buttons
   All buttons share the same base shape. Color encodes meaning only.
   ═══════════════════════════════════════════════════════════════════ */

/* ── BASE PILL (used by all ctrl-zone buttons) ── */
.ctrlBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.08);
    border: 1.5px solid rgba(26, 46, 48, 0.22);
    color: var(--navy);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
    line-height: 1;
}
.ctrlBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── DARK BG PILL BASE (inside the terminal header dark panels) ── */
.darkCtrlBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
    line-height: 1;
}
.darkCtrlBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: var(--orange); }
.darkCtrlBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.darkCtrlBtn:disabled { opacity: 0.45; cursor: not-allowed; }

/* EDIT -- orange tint inactive, orange-filled active (same as Ledger activeFilter) */
.unlockMasterBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(238, 140, 58, 0.12);
    border: 1.5px solid rgba(238, 140, 58, 0.45);
    color: var(--orange);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, color 0.2s;
}
.unlockMasterBtn:hover, .unlockMasterBtn:focus-visible {
    background: #EE8C3A;
    color: #1a2e30;
    border-color: #EE8C3A;
    box-shadow: 0 0 14px rgba(238,140,58,0.35);
    outline: none;
}

/* SAVE -- orange filled (primary action) */
.btn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(12px, 1.6vw, 18px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    border: 1.5px solid transparent;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, color 0.2s;
    line-height: 1;
}
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

.btnPrimary {
    background: #EE8C3A;
    color: #1a2e30;
    border-color: #EE8C3A;
}
.btnPrimary:not(:disabled):hover {
    background: #f0a050;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}

/* ABORT -- muted transparent with red on hover */
.btnDanger {
    background: rgba(26, 46, 48, 0.75);
    border-color: rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.75);
}
.btnDanger:hover {
    background: rgba(239,68,68,0.15);
    border-color: rgba(239,68,68,0.5);
    color: #fca5a5;
}

/* DELETE (nuclear purge) -- red tint, stronger than abort */
.purgeBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(239, 68, 68, 0.10);
    border: 1.5px solid rgba(239, 68, 68, 0.35);
    color: #fca5a5;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}
.purgeBtn:hover { background: #ef4444; color: #fff; border-color: #ef4444; box-shadow: 0 0 12px rgba(239,68,68,0.35); }
.purgeBtn:focus-visible { outline: 2px solid #ef4444; outline-offset: 2px; }

/* PAYMENT -- green tint (money action) */
.ctrlBtnPay {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(16, 185, 129, 0.10);
    border: 1.5px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}
.ctrlBtnPay:hover { background: #10b981; color: #1a2e30; border-color: #10b981; box-shadow: 0 0 12px rgba(16,185,129,0.3); }
.ctrlBtnPay:focus-visible { outline: 2px solid #10b981; outline-offset: 2px; }

/* BACKLOG -- red tint (danger/warning action) */
.ctrlBtnBacklog {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(239, 68, 68, 0.10);
    border: 1.5px solid rgba(239, 68, 68, 0.30);
    color: #fca5a5;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
}
.ctrlBtnBacklog:hover { background: rgba(239,68,68,0.20); border-color: rgba(239,68,68,0.55); }
.ctrlBtnBacklog:focus-visible { outline: 2px solid #ef4444; outline-offset: 2px; }

/* PRINT icon-only */
.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    background: rgba(26, 46, 48, 0.08);
    border: 1.5px solid rgba(26, 46, 48, 0.20);
    color: var(--navy);
    border-radius: var(--radius-sm);
    font-size: clamp(14px, 1.6vw, 17px);
    cursor: pointer;
    transition: 0.2s;
    flex-shrink: 0;
}
.printBtn:hover { background: var(--navy); color: var(--orange); border-color: var(--navy); }

/* Ctrl group layout */
.ctrlGroup { display: flex; align-items: center; gap: clamp(6px, 0.9vw, 10px); flex-wrap: wrap; flex-shrink: 0; }
.handshakeActions { display: flex; gap: clamp(7px, 1vw, 10px); flex-wrap: wrap; }

/* icon buttons (trash, edit inside notes/docs) */'''
)

# Fix the duplicate ctrlBtn/ctrlBtnDanger/ctrlBtnSuccess block
patch(
    FOLDER_CSS,
    '''/* Unified control zone buttons - view mode */
.ctrlBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(10px, 1.3vw, 14px);
    background: rgba(26, 46, 48, 0.08);
    border: 1.5px solid rgba(26, 46, 48, 0.22);
    color: var(--navy);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
}
.ctrlBtn:hover { background: var(--navy); color: #fff; border-color: var(--navy); }
.ctrlBtn:focus-visible { outline: 2px solid var(--orange); }
.ctrlBtnDanger {
    border-color: rgba(239,68,68,0.4);
    color: #ef4444;
    background: rgba(239,68,68,0.08);
}
.ctrlBtnDanger:hover { background: #ef4444; color: #fff; border-color: #ef4444; }
.ctrlBtnSuccess {
    border-color: rgba(34,197,94,0.4);
    color: #22c55e;
    background: rgba(34,197,94,0.08);
}
.ctrlBtnSuccess:hover { background: #22c55e; color: #1a2e30; border-color: #22c55e; }
.iconBtn { display: inline-flex; align-items: center; justify-content: center; background: transparent; border: none; cursor: pointer; padding: clamp(4px, 0.6vw, 6px); border-radius: 4px; transition: background 0.15s; line-height: 1; }''',
    '''.iconBtn { display: inline-flex; align-items: center; justify-content: center; background: transparent; border: none; cursor: pointer; padding: clamp(4px, 0.6vw, 6px); border-radius: 4px; transition: background 0.15s; line-height: 1; }'''
)

# Fix meta tags to be uniform, smaller pills matching ledger style
patch(
    FOLDER_CSS,
    '.metaTag { display: inline-flex; align-items: center; gap: clamp(4px, 0.6vw, 6px); font-size: var(--fs-meta); font-weight: 800; text-transform: uppercase; padding: clamp(3px, 0.4vw, 5px) clamp(8px, 1.1vw, 12px); border-radius: 5px; letter-spacing: 0.5px; white-space: nowrap; }\n.tagBlue   { background: rgba(6,182,212,0.1);  color: #0891b2; border: 1px solid rgba(6,182,212,0.25); }\n.tagOrange { background: rgba(238,140,58,0.1); color: #c2410c; border: 1px solid var(--orange-border); }\n.editBadge { background: var(--navy); color: var(--cyan); font-size: var(--fs-tag); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; padding: clamp(3px, 0.4vw, 5px) clamp(8px, 1vw, 12px); border-radius: 4px; border: 1px solid var(--cyan); white-space: nowrap; animation: pulse 2s ease-in-out infinite; }',
    '''.metaTag {
    display: inline-flex;
    align-items: center;
    gap: clamp(4px, 0.5vw, 6px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.82vw, 10px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: clamp(3px, 0.4vw, 5px) clamp(8px, 1.1vw, 12px);
    border-radius: var(--radius-sm);
    white-space: nowrap;
    border: 1.5px solid transparent;
}
/* COLLECTION % -- muted navy pill (matches ledger tagStandard) */
.tagBlue {
    background: rgba(26, 46, 48, 0.75);
    border-color: rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
}
/* ACTIVE status -- muted with orange tint (matches ledger tagStandard + hint) */
.tagOrange {
    background: rgba(238, 140, 58, 0.10);
    border-color: rgba(238, 140, 58, 0.35);
    color: var(--orange);
}
/* EDIT MODE badge -- cyan accent, pulsing */
.editBadge {
    background: rgba(6, 182, 212, 0.12);
    border: 1.5px solid rgba(6, 182, 212, 0.4);
    color: #67e8f9;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.82vw, 10px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: clamp(3px, 0.4vw, 5px) clamp(8px, 1.1vw, 12px);
    border-radius: var(--radius-sm);
    white-space: nowrap;
    animation: pulse 2s ease-in-out infinite;
}'''
)

print("FolderPage CSS patches applied")

# ============================================================
# 2. FOLDERPAGE.JSX - Update button class names in JSX
# ============================================================
FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Fix the view mode ctrlZone buttons to use new class names
patch(
    FOLDER_JSX,
    '''                    {/* VIEW MODE ACTIONS */}
                    {!isEditing && (
                        <div className={styles.ctrlGroup}>
                            <button className={styles.ctrlBtnIcon} onClick={() => window.print()} aria-label="Print record" title="Print">
                                <FiPrinter aria-hidden="true" />
                            </button>
                            {isAdmin && (
                                <button className={styles.ctrlBtnPay}
                                    onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>
                                    <FiDollarSign aria-hidden="true" /> PAYMENT
                                </button>
                            )}
                            {isAdmin && !isBacklog && (
                                <button className={styles.ctrlBtnBacklog} onClick={handleMoveToBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG
                                </button>
                            )}
                            <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                                <FiUnlock aria-hidden="true" /> EDIT
                            </button>
                        </div>
                    )}
                    {/* EDIT MODE ACTIONS */}
                    {isEditing && (
                        <div className={styles.ctrlGroup}>
                            {user?.isRoot && (
                                <button className={styles.purgeBtn} onClick={handleNuclearPurge} title="Permanently delete this record">
                                    <FiTrash2 aria-hidden="true" /> DELETE
                                </button>
                            )}
                            <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}>
                                <FiX aria-hidden="true" /> ABORT
                            </button>
                            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}>
                                <FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}
                            </button>
                        </div>
                    )}''',
    '''                    {/* VIEW MODE ACTIONS */}
                    {!isEditing && (
                        <div className={styles.ctrlGroup}>
                            <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record" title="Print">
                                <FiPrinter aria-hidden="true" />
                            </button>
                            {isAdmin && (
                                <button className={styles.ctrlBtnPay}
                                    onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>
                                    <FiDollarSign aria-hidden="true" /> PAYMENT
                                </button>
                            )}
                            {isAdmin && !isBacklog && (
                                <button className={styles.ctrlBtnBacklog} onClick={handleMoveToBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG
                                </button>
                            )}
                            <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                                <FiUnlock aria-hidden="true" /> EDIT
                            </button>
                        </div>
                    )}
                    {/* EDIT MODE ACTIONS */}
                    {isEditing && (
                        <div className={styles.ctrlGroup}>
                            {user?.isRoot && (
                                <button className={styles.purgeBtn} onClick={handleNuclearPurge} title="Permanently delete this record">
                                    <FiTrash2 aria-hidden="true" /> DELETE
                                </button>
                            )}
                            <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}>
                                <FiX aria-hidden="true" /> ABORT
                            </button>
                            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}>
                                <FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE'}
                            </button>
                        </div>
                    )}'''
)

print("FolderPage JSX patches applied")

# ============================================================
# 3. INTAKEPAGE.MODULE.CSS - Match drawer/panel sizing to FolderPage
# ============================================================
INTAKE_CSS = 'erp-frontend/src/pages/Intake/IntakePage.module.css'

# Match drawer header padding to FolderPage exactly
patch(
    INTAKE_CSS,
    '''.drawerHeader {
    display: flex; justify-content: space-between; align-items: center;
    width: 100% !important; cursor: pointer; user-select: none;
    padding: clamp(12px, 1.5vw, 16px) var(--pad-panel);
    border-bottom: 1px solid rgba(238, 140, 58, 0.12);
    transition: background 0.2s; box-sizing: border-box;
}''',
    '''.drawerHeader {
    display: flex; justify-content: space-between; align-items: center;
    width: 100% !important; cursor: pointer; user-select: none;
    padding: clamp(8px, 1.1vw, 11px) clamp(12px, 1.5vw, 17px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.12);
    transition: background 0.2s; box-sizing: border-box;
}'''
)

# Match drawerTitle font size to FolderPage
patch(
    INTAKE_CSS,
    '''.drawerTitle {
    display: flex; align-items: center; gap: clamp(6px, 0.8vw, 10px);
    color: var(--orange); font-weight: 900; font-size: var(--fs-meta);
    letter-spacing: 0.6px; text-transform: uppercase;
}
.drawerIcon  { font-size: clamp(14px, 1.5vw, 17px); color: var(--orange); }''',
    '''.drawerTitle {
    display: flex; align-items: center; gap: clamp(7px, 0.9vw, 11px);
    color: var(--orange); font-weight: 900; font-size: clamp(9px, 0.9vw, 11px);
    letter-spacing: 2px; text-transform: uppercase;
}
.drawerIcon  { font-size: clamp(13px, 1.4vw, 16px); color: var(--orange); }'''
)

# Match panelInner padding to FolderPage
patch(
    INTAKE_CSS,
    '.panelInner { padding: clamp(12px, 1.6vw, 18px); }',
    '.panelInner { padding: clamp(10px, 1.5vw, 16px) clamp(12px, 1.5vw, 17px); }'
)

# Unify the submit button with FolderPage's save button design
patch(
    INTAKE_CSS,
    '''.primaryCommitBtn {
    height: var(--btn-height, var(--input-h)); padding: 0 var(--btn-px, clamp(20px, 2.5vw, 32px));
    background: var(--navy); border: 2px solid var(--orange); color: var(--orange);
    border-radius: var(--radius-sm); font-family: 'DM Sans', sans-serif;
    font-weight: 900; font-size: var(--fs-btn); letter-spacing: 0.8px;
    text-transform: uppercase; display: flex; align-items: center;
    gap: clamp(6px, 0.8vw, 10px); cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s, color 0.2s;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2); white-space: nowrap;
}
.primaryCommitBtn:hover:not(:disabled) { background: var(--orange); color: #fff; box-shadow: 0 0 20px rgba(238,140,58,0.4); }
.primaryCommitBtn:disabled             { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.primaryCommitBtn:focus-visible        { outline: 2px solid var(--orange); }''',
    '''.primaryCommitBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 9px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(16px, 2vw, 24px);
    background: #EE8C3A;
    border: 1.5px solid #EE8C3A;
    color: #1a2e30;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s;
    white-space: nowrap;
}
.primaryCommitBtn:hover:not(:disabled) {
    background: #f0a050;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}
.primaryCommitBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.primaryCommitBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }'''
)

# Match the drawer chevron to FolderPage (using same unicode char)
patch(
    INTAKE_CSS,
    '''.chevron {
    color: var(--orange); font-size: clamp(18px, 2vw, 22px);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); flex-shrink: 0;
}''',
    '''.chevron {
    color: var(--orange); font-size: clamp(15px, 1.7vw, 19px);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); flex-shrink: 0;
}'''
)

print("IntakePage CSS patches applied")
print("\nAll patches complete. Run: git add -A && git commit -m 'unify button/badge/drawer design across FolderPage and IntakePage' && git push")