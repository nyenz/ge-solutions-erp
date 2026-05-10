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

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING in {path}: {repr(old[:80])}")
        return
    content = content.replace(old, new, 1)
    write(path, content)
    print(f"PATCHED: {path}")


FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
PAYMENTS_CSS = 'erp-frontend/src/pages/Payments/PaymentsPage.module.css'
LEDGER_CSS = 'erp-frontend/src/pages/Ledger/LedgerPage.module.css'
AUDIT_CSS = 'erp-frontend/src/pages/Audit/AuditPage.module.css'


# ================================================================
# CHANGE 1: FolderPage JSX -- PAUSE/RESUME button
# When fees are PAUSED: show orange-filled "RESUME FEES" (call to action)
# When fees are ACTIVE: show grey "PAUSE FEES" (less prominent)
# ================================================================
patch(
    FOLDER_JSX,
    '''                                                <button
                                                    type="button"
                                                    className={styles.btnPauseResume}
                                                    onClick={async () => {
                                                        try {
                                                            await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                            await loadFolderData();
                                                            toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                        } catch { toast('ACTION FAILED', 'error'); }
                                                    }}
                                                >
                                                    {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                                </button>''',
    '''                                                <button
                                                    type="button"
                                                    className={project.storagePaused ? styles.btnResumeActive : styles.btnPauseGrey}
                                                    onClick={async () => {
                                                        try {
                                                            await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                            await loadFolderData();
                                                            toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                        } catch { toast('ACTION FAILED', 'error'); }
                                                    }}
                                                >
                                                    {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                                </button>'''
)


# ================================================================
# CHANGE 2: FolderPage JSX -- Remove toast on blur for fee inputs
# The inputs call toast every time user leaves the field which is
# annoying. Remove the toast calls, keep the data save silently.
# ================================================================
patch(
    FOLDER_JSX,
    '''                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setStorageRate(project.id, val);
                                                                await loadFolderData();
                                                                toast(`MONTHLY RATE SET TO UGX ${Number(val).toLocaleString()}`, 'success', 2500);
                                                            } catch { toast('RATE UPDATE FAILED', 'error'); }
                                                        }
                                                    }}''',
    '''                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setStorageRate(project.id, val);
                                                                await loadFolderData();
                                                            } catch { /* silent */ }
                                                        }
                                                    }}'''
)

patch(
    FOLDER_JSX,
    '''                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setAccumulatedFees(project.id, val);
                                                                await loadFolderData();
                                                                toast(`TOTAL FEES ADJUSTED TO UGX ${Number(val).toLocaleString()}`, 'success', 2500);
                                                            } catch { toast('FEE ADJUSTMENT FAILED', 'error'); }
                                                        }
                                                    }}''',
    '''                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setAccumulatedFees(project.id, val);
                                                                await loadFolderData();
                                                            } catch { /* silent */ }
                                                        }
                                                    }}'''
)


# ================================================================
# CHANGE 3: FolderPage CSS -- Replace btnPauseResume with two variants
# btnResumeActive = orange fill (prominent -- "click to resume")
# btnPauseGrey    = dark grey (subtle -- "click to pause")
# Also redesign printBtn using dark navy theme
# ================================================================
patch(
    FOLDER_CSS,
    '''/* Pause/Resume fees button -- same design as Ledger "PAID TITLES" filter:
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
    '''/* RESUME FEES -- orange fill (prominent call to action when fees are paused) */
.btnResumeActive {
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
    box-shadow: 0 2px 8px rgba(238, 140, 58, 0.3);
}
.btnResumeActive:hover {
    background: #f0a050;
    border-color: #f0a050;
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.5);
}
.btnResumeActive:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* PAUSE FEES -- dark grey (subtle, less prominent when fees are running) */
.btnPauseGrey {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(5px, 0.6vw, 7px);
    width: 100%;
    height: var(--input-h, clamp(34px, 4.5vw, 40px));
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.75);
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
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.45);
    color: #fca5a5;
}
.btnPauseGrey:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }'''
)

# Redesign printBtn -- dark navy, no blue
patch(
    FOLDER_CSS,
    '''/* PRINT icon-only (no text label) */
.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    padding: 0;
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(6, 182, 212, 0.45);
    color: #67e8f9;
    border-radius: var(--radius-sm);
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s, transform 0.15s;
    line-height: 1;
    font-size: clamp(14px, 1.6vw, 18px);
    position: relative;
}
.printBtn::before {
    content: '';
    position: absolute;
    inset: -3px;
    border-radius: calc(var(--radius-sm) + 2px);
    background: rgba(6, 182, 212, 0);
    transition: background 0.2s;
}
.printBtn:hover {
    background: rgba(6, 182, 212, 0.18);
    color: #06b6d4;
    border-color: #06b6d4;
    box-shadow: 0 0 14px rgba(6,182,212,0.35), 0 0 0 3px rgba(6,182,212,0.12);
    transform: translateY(-1px);
}
.printBtn:active { transform: translateY(0); }
.printBtn:focus-visible { outline: 2px solid #06b6d4; outline-offset: 2px; }''',
    '''/* PRINT icon-only -- dark navy theme */
.printBtn {
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
.printBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }'''
)


# ================================================================
# CHANGE 4: PaymentsPage CSS -- typeBadge: plain colored text only
# Remove colored background from type badges, just color the text
# ================================================================
patch(
    PAYMENTS_CSS,
    '''.typeBadge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: clamp(2px, 0.3vw, 4px) clamp(6px, 0.8vw, 9px);
    border-radius: 4px;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-transform: uppercase;
    white-space: nowrap;
    letter-spacing: 0.5px;
}''',
    '''.typeBadge {
    display: inline-flex; align-items: center; gap: 4px;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-transform: uppercase;
    white-space: nowrap;
    letter-spacing: 0.5px;
    background: transparent !important;
    border: none !important;
    padding: 0;
}'''
)

# Also fix the inline style on the typeBadge in PaymentsPage.jsx
patch(
    'erp-frontend/src/pages/Payments/PaymentsPage.jsx',
    '''                                    <td>
                                        <span className={styles.typeBadge} style={{
                                            background: `${TYPE_COLORS[pay.paymentType] || '#888'}22`,
                                            color: TYPE_COLORS[pay.paymentType] || '#888',
                                            border: `1px solid ${TYPE_COLORS[pay.paymentType] || '#888'}55`
                                        }}>
                                            {pay.paymentType === 'BACKLOG_PARTIAL' && <FiAlertOctagon size={9} />}
                                            {TYPE_LABELS[pay.paymentType] || pay.paymentType}
                                        </span>
                                    </td>''',
    '''                                    <td>
                                        <span className={styles.typeBadge} style={{
                                            color: TYPE_COLORS[pay.paymentType] || '#888'
                                        }}>
                                            {pay.paymentType === 'BACKLOG_PARTIAL' && <FiAlertOctagon size={9} />}
                                            {TYPE_LABELS[pay.paymentType] || pay.paymentType}
                                        </span>
                                    </td>'''
)


# ================================================================
# CHANGE 5: LedgerPage CSS -- status tags: plain colored text
# tagBacklog, tagCritical, tagPaid, tagLegacy, tagStandard
# Remove colored backgrounds, just show colored text
# ================================================================
patch(
    LEDGER_CSS,
    '''.tagLegacy {
    font-family: 'DM Sans', sans-serif;
    background: #7c2d12;
    color: #fb923c;
    padding: clamp(2px, 0.3vw, 4px) clamp(5px, 0.7vw, 8px);
    border-radius: 4px;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
}
.tagStandard {
    font-family: 'DM Sans', sans-serif;
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.4);
    padding: clamp(2px, 0.3vw, 4px) clamp(5px, 0.7vw, 8px);
    border-radius: 4px;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
}
.tagPaid {
    font-family: 'DM Sans', sans-serif;
    background: rgba(16, 185, 129, 0.18);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.4);
    padding: clamp(2px, 0.3vw, 4px) clamp(5px, 0.7vw, 8px);
    border-radius: 4px;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
}

.tagCritical {
    font-family: 'DM Sans', sans-serif;
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.3);
    padding: clamp(2px, 0.3vw, 4px) clamp(5px, 0.7vw, 8px);
    border-radius: 4px;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    animation: criticalPulse 1.8s ease-in-out infinite;
}
@keyframes criticalPulse { 0%,100%{opacity:1} 50%{opacity:0.55} }''',
    '''.tagLegacy {
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    color: #fb923c;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.tagStandard {
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    color: rgba(255, 255, 255, 0.4);
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.tagPaid {
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    color: #6ee7b7;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.tagCritical {
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    color: #fca5a5;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    animation: criticalPulse 1.8s ease-in-out infinite;
}
@keyframes criticalPulse { 0%,100%{opacity:1} 50%{opacity:0.55} }'''
)

# Fix the three duplicate tagBacklog definitions -- replace the last one (the definitive one)
# First remove all three duplicates, then add one clean version
content = read(LEDGER_CSS)
# Remove all tagBacklog blocks (there are 3)
import re
# Replace all occurrences of the tagBacklog block
old_backlog = '''.tagBacklog {
    font-family: 'DM Sans', sans-serif;
    background: rgba(239, 68, 68, 0.18);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.4);
    padding: clamp(2px, 0.3vw, 4px) clamp(5px, 0.7vw, 8px);
    border-radius: 4px;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    animation: criticalPulse 1.8s ease-in-out infinite;
}'''
new_backlog = '''.tagBacklog {
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    color: #fca5a5;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    animation: criticalPulse 1.8s ease-in-out infinite;
}'''
# Replace all occurrences
content = content.replace(old_backlog, new_backlog)
write(LEDGER_CSS, content)


# ================================================================
# CHANGE 6: AuditPage -- action badge styling
# The severity left-border color already handles the color signal.
# The actionMeta strong color (already colored by severity class)
# -- no badge backgrounds to remove here, looks clean already.
# But the logRow severityHigh/Med/Intel/Low left borders are fine.
# ================================================================
# AuditPage is already clean (left border only, no badge bg) -- skip


# ================================================================
# CHANGE 7: RecoveryPortal -- backlogPlotTag: plain text, no bg pill
# ================================================================
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css',
    '''.backlogPlotTag { display:inline-flex; align-items:center; gap:4px; background:rgba(239,68,68,0.25); color:#fecaca; border:1px solid rgba(239,68,68,0.4); border-radius:3px; padding:2px 7px; font-size:9px; font-weight:800; text-transform:uppercase; margin-bottom:4px; width:fit-content; }''',
    '''.backlogPlotTag { display:inline-flex; align-items:center; gap:4px; background:transparent; color:#fca5a5; font-size:9px; font-weight:900; text-transform:uppercase; margin-bottom:4px; letter-spacing:0.5px; }'''
)

# ================================================================
# CHANGE 8: RecoveryPortal -- statusBadge: remove colored bg pill,
# use plain colored text instead (the card border already signals status)
# ================================================================
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css',
    '''.statusBadge { float:right; display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-bottom-left-radius:6px; font-family:'DM Sans',sans-serif; font-size:var(--fs-badge); font-weight:900; letter-spacing:0.8px; text-transform:uppercase; }
.statusRed     { background:#7f1d1d; color:#fecaca; }
.statusBlue    { background:#0c4a6e; color:#bae6fd; }
.statusGrey    { background:#3f3f46; color:#e4e4e7; }
.statusDefault { background:rgba(0,0,0,0.55); color:rgba(255,255,255,0.7); }''',
    '''.statusBadge { float:right; display:inline-flex; align-items:center; gap:5px; padding:4px 8px; font-family:'DM Sans',sans-serif; font-size:var(--fs-badge); font-weight:900; letter-spacing:0.8px; text-transform:uppercase; background:transparent; }
.statusRed     { color:#fca5a5; }
.statusBlue    { color:#93c5fd; }
.statusGrey    { color:rgba(255,255,255,0.4); }
.statusDefault { color:rgba(255,255,255,0.5); }'''
)

print()
print("All changes applied!")
print()
print("Changes made:")
print("1. Pause/Resume fees button: RESUME = orange (prominent), PAUSE = grey (subtle)")
print("2. Fee input fields: removed annoying toast on blur -- saves silently")
print("3. Print button: dark navy theme, clean and minimal")
print("4. Payments typeBadge: plain colored text only, no bg/border")
print("5. Ledger status tags: plain colored text (tagPaid, tagCritical, tagBacklog, etc.)")
print("6. Recovery backlogPlotTag: plain colored text")
print("7. Recovery statusBadge: plain colored text (card border already signals status)")
print()
print("Run: git add -A && git commit -m 'ui: plain text tags, alternating pause/resume btn, clean print btn, silent fee input saves' && git push")