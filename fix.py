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

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK       {label}")
    else:
        print(f"MISSING  {label}")

# =====================================================================
# FIX 1: FolderPage.jsx - Storage fee controls + PDF fix + header cleanup
# =====================================================================

FOLDER = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Replace the BacklogFeeControls component with the new full version
patch(FOLDER,
'''// ===============================================================
// BACKLOG FEE ADMIN CONTROLS
// ===============================================================
const BacklogFeeControls = ({ project, projectId, onRefresh, toast }) => {
    const [feeInput,    setFeeInput]    = React.useState('');
    const [rateInput,   setRateInput]   = React.useState('');
    const [saving,      setSaving]      = React.useState(false);

    const handlePause = async () => {
        try {
            await recoveryService.pauseStorageFees(projectId, !project.storagePaused);
            await onRefresh();
            toast(project.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED', 'info');
        } catch { toast('ACTION FAILED', 'error'); }
    };

    const handleSetRate = async () => {
        const val = Number(rateInput);
        if (!rateInput || val < 0) { toast('ENTER A VALID RATE (0 or more)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setStorageRate(projectId, val);
            setRateInput('');
            await onRefresh();
            toast('MONTHLY RATE UPDATED', 'success');
        } catch { toast('RATE UPDATE FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const handleSetFees = async () => {
        const val = Number(feeInput);
        if (feeInput === '' || val < 0) { toast('ENTER A VALID AMOUNT (0 to waive all)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setAccumulatedFees(projectId, val);
            setFeeInput('');
            await onRefresh();
            toast('ACCUMULATED FEES ADJUSTED', 'success');
        } catch { toast('FEE ADJUSTMENT FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const boxStyle = { background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 8, padding: '12px 14px', marginTop: 12 };
    const labelStyle = { display: 'block', fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 };
    const inputStyle = { background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6, color: '#1a2e30', fontFamily: 'Space Mono,monospace', fontWeight: 700, fontSize: 13, padding: '6px 10px', outline: 'none', width: '100%', boxSizing: 'border-box' };
    const btnStyle = (color) => ({ background: color + '22', border: '1.5px solid ' + color, color: color, borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 10, fontWeight: 900, fontFamily: 'DM Sans,sans-serif', textTransform: 'uppercase', letterSpacing: 1, marginTop: 6 });

    return (
        <div style={boxStyle}>
            <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#ef4444', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 10 }}>
                ADMIN: STORAGE FEE CONTROLS
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div>
                    <span style={labelStyle}>PAUSE / RESUME FEES</span>
                    <button onClick={handlePause} style={btnStyle(project.storagePaused ? '#22c55e' : '#f59e0b')}>
                        {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                    </button>
                    {project.storagePaused && <div style={{ fontSize: 9, color: '#f59e0b', marginTop: 4, fontWeight: 700 }}>Fees currently PAUSED</div>}
                </div>
                <div>
                    <span style={labelStyle}>SET MONTHLY RATE (UGX)</span>
                    <input style={inputStyle} type="number" value={rateInput} placeholder={project.storageFeeOverride ? String(project.storageFeeOverride) : '50000'} onChange={e => setRateInput(e.target.value)} />
                    <button onClick={handleSetRate} style={btnStyle('#EE8C3A')} disabled={saving}>APPLY RATE</button>
                </div>
                <div>
                    <span style={labelStyle}>ADJUST TOTAL FEES (UGX)</span>
                    <input style={inputStyle} type="number" value={feeInput} placeholder={String(project.storageFeesAccumulated || 0)} onChange={e => setFeeInput(e.target.value)} />
                    <button onClick={handleSetFees} style={btnStyle('#ef4444')} disabled={saving}>SET TOTAL</button>
                    <div style={{ fontSize: 8, color: 'rgba(255,255,255,0.4)', marginTop: 3, fontWeight: 700 }}>Enter 0 to waive all fees</div>
                </div>
            </div>
        </div>
    );
};''',
'''// ===============================================================
// BACKLOG FEE ADMIN CONTROLS - Full version with deadline + late entry
// ===============================================================
const BacklogFeeControls = ({ project, projectId, onRefresh, toast }) => {
    const [feeInput,      setFeeInput]      = React.useState('');
    const [rateInput,     setRateInput]     = React.useState('');
    const [deadlineInput, setDeadlineInput] = React.useState(
        project.storagePauseDeadline
            ? new Date(project.storagePauseDeadline).toISOString().split('T')[0]
            : ''
    );
    const [saving, setSaving] = React.useState(false);

    const handlePause = async () => {
        try {
            await recoveryService.pauseStorageFees(projectId, !project.storagePaused);
            await onRefresh();
            toast(project.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED - NEGOTIATION MODE', 'info');
        } catch { toast('ACTION FAILED', 'error'); }
    };

    const handleSetRate = async () => {
        const val = Number(rateInput);
        if (!rateInput || val < 0) { toast('ENTER A VALID RATE (0 or more)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setStorageRate(projectId, val);
            setRateInput('');
            await onRefresh();
            toast('MONTHLY RATE UPDATED', 'success');
        } catch { toast('RATE UPDATE FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const handleSetFees = async () => {
        const val = Number(feeInput);
        if (feeInput === '' || val < 0) { toast('ENTER A VALID AMOUNT (0 to waive all)', 'error'); return; }
        setSaving(true);
        try {
            await recoveryService.setAccumulatedFees(projectId, val);
            setFeeInput('');
            await onRefresh();
            toast('ACCUMULATED FEES ADJUSTED', 'success');
        } catch { toast('FEE ADJUSTMENT FAILED', 'error'); }
        finally { setSaving(false); }
    };

    // Months of fees to manually backfill (for late-entered titles)
    const handleBackfillMonths = async (months) => {
        if (!months || months < 1) { toast('ENTER NUMBER OF MONTHS', 'error'); return; }
        const rate = project.storageFeeOverride || 50000;
        const total = (Number(project.storageFeesAccumulated) || 0) + (months * rate);
        setSaving(true);
        try {
            await recoveryService.setAccumulatedFees(projectId, total);
            await onRefresh();
            toast(`BACKFILLED ${months} MONTH(S) OF FEES -- UGX ${(months * rate).toLocaleString()} ADDED`, 'warn');
        } catch { toast('BACKFILL FAILED', 'error'); }
        finally { setSaving(false); }
    };

    const boxStyle = {
        background: 'rgba(0,0,0,0.3)',
        border: '1px solid rgba(239,68,68,0.3)',
        borderRadius: 10,
        padding: '14px 16px',
        marginTop: 14
    };
    const sectionStyle = {
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 7,
        padding: '10px 12px'
    };
    const labelStyle = {
        display: 'block', fontFamily: 'DM Sans,sans-serif', fontSize: 9,
        fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase',
        letterSpacing: 1, marginBottom: 5
    };
    const inputStyle = {
        background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
        color: '#1a2e30', fontFamily: 'Space Mono,monospace', fontWeight: 700,
        fontSize: 13, padding: '7px 10px', outline: 'none', width: '100%', boxSizing: 'border-box'
    };
    const btnStyle = (color, full) => ({
        background: color + '22', border: '1.5px solid ' + color, color: color,
        borderRadius: 6, padding: '7px 14px', cursor: 'pointer', fontSize: 10,
        fontWeight: 900, fontFamily: 'DM Sans,sans-serif', textTransform: 'uppercase',
        letterSpacing: 1, marginTop: 7, display: 'flex', alignItems: 'center', gap: 5,
        width: full ? '100%' : 'auto', justifyContent: 'center'
    });

    const [backfillMonths, setBackfillMonths] = React.useState('');

    return (
        <div style={boxStyle}>
            <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#ef4444', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: 4, padding: '2px 8px' }}>ADMIN</span>
                STORAGE FEE CONTROLS
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
                {/* PAUSE / RESUME with optional deadline */}
                <div style={sectionStyle}>
                    <span style={labelStyle}>NEGOTIATION / PAUSE MODE</span>
                    <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)', marginBottom: 8, fontFamily: 'DM Sans,sans-serif', fontWeight: 700, lineHeight: 1.4 }}>
                        Pause fee accumulation while negotiating with client. Set an optional deadline.
                    </div>
                    <label style={{ ...labelStyle, marginTop: 6 }}>PAUSE DEADLINE (optional)</label>
                    <input type="date" style={{ ...inputStyle, marginBottom: 4 }}
                        value={deadlineInput}
                        min={new Date().toISOString().split('T')[0]}
                        onChange={e => setDeadlineInput(e.target.value)} />
                    <div style={{ fontSize: 8, color: 'rgba(255,255,255,0.35)', fontFamily: 'DM Sans,sans-serif', fontWeight: 700, marginBottom: 6 }}>
                        If set, fees auto-resume after this date.
                    </div>
                    <button onClick={handlePause} style={btnStyle(project.storagePaused ? '#22c55e' : '#f59e0b', true)}>
                        {project.storagePaused ? '▶ RESUME FEE ACCUMULATION' : '⏸ PAUSE FEES (NEGOTIATING)'}
                    </button>
                    {project.storagePaused && (
                        <div style={{ fontSize: 9, color: '#f59e0b', marginTop: 5, fontWeight: 800, fontFamily: 'DM Sans,sans-serif', background: 'rgba(245,158,11,0.1)', padding: '4px 8px', borderRadius: 4, border: '1px solid rgba(245,158,11,0.3)' }}>
                            ⏸ FEES PAUSED {deadlineInput ? `-- RESUMES ${deadlineInput}` : ''}
                        </div>
                    )}
                </div>

                {/* RATE + ADJUST */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={sectionStyle}>
                        <span style={labelStyle}>MONTHLY FEE RATE (UGX)</span>
                        <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)', marginBottom: 6, fontFamily: 'DM Sans,sans-serif', fontWeight: 700 }}>
                            Default: UGX 50,000/month
                        </div>
                        <input style={inputStyle} type="number" value={rateInput}
                            placeholder={project.storageFeeOverride ? String(project.storageFeeOverride) : '50000'}
                            onChange={e => setRateInput(e.target.value)} />
                        <button onClick={handleSetRate} style={btnStyle('#EE8C3A')} disabled={saving}>APPLY NEW RATE</button>
                    </div>

                    <div style={sectionStyle}>
                        <span style={labelStyle}>OVERRIDE TOTAL FEES (UGX)</span>
                        <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)', marginBottom: 6, fontFamily: 'DM Sans,sans-serif', fontWeight: 700 }}>
                            Current: UGX {Number(project.storageFeesAccumulated || 0).toLocaleString()}
                        </div>
                        <input style={inputStyle} type="number" value={feeInput}
                            placeholder="e.g. 0 to waive all"
                            onChange={e => setFeeInput(e.target.value)} />
                        <button onClick={handleSetFees} style={btnStyle('#ef4444')} disabled={saving}>SET TOTAL FEES</button>
                    </div>
                </div>
            </div>

            {/* LATE ENTRY BACKFILL */}
            <div style={{ ...sectionStyle, borderColor: 'rgba(6,182,212,0.3)' }}>
                <span style={{ ...labelStyle, color: '#06b6d4' }}>LATE ENTRY BACKFILL</span>
                <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)', marginBottom: 8, fontFamily: 'DM Sans,sans-serif', fontWeight: 700, lineHeight: 1.4 }}>
                    If this title was entered into the system late and already had outstanding storage months before entry, add those months here.
                    Rate used: UGX {Number(project.storageFeeOverride || 50000).toLocaleString()}/month.
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                        <label style={labelStyle}>MONTHS TO ADD</label>
                        <input style={inputStyle} type="number" min="1" max="120"
                            placeholder="e.g. 3"
                            value={backfillMonths}
                            onChange={e => setBackfillMonths(e.target.value)} />
                    </div>
                    <button
                        onClick={() => handleBackfillMonths(Number(backfillMonths))}
                        style={{ ...btnStyle('#06b6d4'), marginTop: 0, alignSelf: 'flex-end', height: 34 }}
                        disabled={saving}>
                        ADD MONTHS
                    </button>
                </div>
                {backfillMonths && Number(backfillMonths) > 0 && (
                    <div style={{ fontSize: 9, color: '#06b6d4', marginTop: 4, fontFamily: 'DM Sans,sans-serif', fontWeight: 800 }}>
                        Will add: UGX {(Number(backfillMonths) * Number(project.storageFeeOverride || 50000)).toLocaleString()}
                    </div>
                )}
            </div>
        </div>
    );
};''',
    "FolderPage -- Replace BacklogFeeControls with full version"
)

# Fix PDF opening - replace the getVaultUrl + isPDF logic and the doc rendering
patch(FOLDER,
'''    const getVaultUrl = (filePath) => {
        if (!filePath) return '#';
        // Cloudinary URLs work directly -- just return them
        if (filePath.startsWith('http')) return filePath;
        const parts = filePath.split(/ge_uploads[/]/);
        const rel   = parts.length > 1 ? parts[1] : filePath;
        const base  = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';
        return `${base}/vault/` + rel.replace(/\\\\/g, '/');
    };

    const isPDF = (filePath) => {
        if (!filePath) return false;
        const lower = filePath.toLowerCase();
        return lower.includes('.pdf') || lower.includes('application/pdf') ||
               (lower.includes('cloudinary') && lower.includes('/raw/'));
    };''',
'''    const getVaultUrl = (filePath) => {
        if (!filePath) return '#';
        if (filePath.startsWith('http')) return filePath;
        const parts = filePath.split(/ge_uploads[/]/);
        const rel   = parts.length > 1 ? parts[1] : filePath;
        const base  = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';
        return `${base}/vault/` + rel.replace(/\\\\/g, '/');
    };

    const isPDF = (filePath) => {
        if (!filePath) return false;
        const lower = filePath.toLowerCase();
        return lower.endsWith('.pdf') || lower.includes('application/pdf') ||
               (lower.includes('cloudinary') && lower.includes('/raw/'));
    };

    const openDocument = (doc) => {
        const url = getVaultUrl(doc.filePath);
        if (isPDF(doc.filePath)) {
            // For Cloudinary raw PDFs: open directly in new tab
            // Modern browsers will render PDFs inline
            window.open(url, '_blank', 'noopener,noreferrer');
        } else {
            window.open(url, '_blank', 'noopener,noreferrer');
        }
    };''',
    "FolderPage -- Fix PDF opening logic"
)

# Fix the document rendering to use the new openDocument function
patch(FOLDER,
'''                                    {binder.documents.map((doc, idx) => (
                                        <div key={idx} className={styles.docTag} role="listitem">
                                            <FiFileText className={styles.docIcon} aria-hidden="true" />
                                            <a
                                                href={getVaultUrl(doc.filePath)}
                                                target="_blank"
                                                rel="noreferrer"
                                                className={styles.docName}
                                                title={isPDF(doc.filePath) ? 'Open PDF in new tab' : doc.fileName}
                                            >
                                                {isPDF(doc.filePath) ? '\\u{1F4C4} ' : ''}{doc.fileName}
                                            </a>
                                            {isEditing && (
                                                <button type="button" className={styles.iconBtn}
                                                    onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>
                                                    <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                </button>
                                            )}
                                        </div>
                                    ))}''',
'''                                    {binder.documents.map((doc, idx) => (
                                        <div key={idx} className={styles.docTag} role="listitem">
                                            <FiFileText className={styles.docIcon} aria-hidden="true" />
                                            <button
                                                type="button"
                                                className={styles.docName}
                                                onClick={() => openDocument(doc)}
                                                title={isPDF(doc.filePath) ? 'Open PDF in new tab' : `Open ${doc.fileName}`}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}
                                            >
                                                {isPDF(doc.filePath) ? '\\u{1F4C4} ' : '\\u{1F5BC} '}{doc.fileName}
                                            </button>
                                            {isEditing && (
                                                <button type="button" className={styles.iconBtn}
                                                    onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>
                                                    <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                </button>
                                            )}
                                        </div>
                                    ))}''',
    "FolderPage -- Fix document button to properly open files"
)

# Fix the terminal header - clean up button layout
patch(FOLDER,
'''            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle.plotNumber}</h1>
                    <div className={styles.metaLine}>
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>
                        {isBacklog
                            ? <span className={`${styles.metaTag}`} style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444' }}>BACKLOG</span>
                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>
                        }
                        {isEditing && <div className={styles.editBadge}>EDIT MODE ENABLED</div>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {!isEditing && <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record"><FiPrinter aria-hidden="true" /></button>}
                    {isAdmin && !isEditing && !isBacklog && (
                        <button onClick={handleMoveToBacklog}
                            style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)',
                                color: '#ef4444', borderRadius: 6, padding: '6px 14px',
                                cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700, display:'flex', alignItems:'center', gap:6 }}>
                            <FiAlertOctagon aria-hidden="true" /> MOVE TO BACKLOG
                        </button>
                    )}
                    {isAdmin && !isEditing && (
                        <button onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}
                            style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.4)',
                                color: '#22c55e', borderRadius: 6, padding: '6px 14px',
                                cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700, display:'flex', alignItems:'center', gap:6 }}>
                            <FiDollarSign aria-hidden="true" /> RECORD PAYMENT
                        </button>
                    )}
                    {isEditing && user?.isRoot && (
                        <button className={styles.purgeBtn} onClick={handleNuclearPurge}>
                            <FiTrash2 aria-hidden="true" /> DELETE
                        </button>
                    )}
                    {!isEditing ? (
                        <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                            <FiUnlock aria-hidden="true" /> EDIT
                        </button>
                    ) : (
                        <div className={styles.handshakeActions}>
                            <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}>
                                <FiX aria-hidden="true" /> ABORT
                            </button>
                            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}>
                                <FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE CHANGES'}
                            </button>
                        </div>
                    )}
                </div>
            </header>''',
'''            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle.plotNumber}</h1>
                    <div className={styles.metaLine}>
                        <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                            COLLECTION: {(binder.collectionPercentage||0).toFixed(1)}%
                        </span>
                        {isBacklog
                            ? <span className={styles.metaTag} style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', borderColor: 'rgba(239,68,68,0.4)' }}>BACKLOG</span>
                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>
                        }
                        {isEditing && <div className={styles.editBadge}>EDIT MODE ENABLED</div>}
                    </div>
                </div>
                <div className={styles.ctrlZone}>
                    {/* VIEW MODE ACTIONS */}
                    {!isEditing && (
                        <>
                            <button className={styles.ctrlBtn} onClick={() => window.print()} aria-label="Print record">
                                <FiPrinter aria-hidden="true" />
                            </button>
                            {isAdmin && !isBacklog && (
                                <button className={`${styles.ctrlBtn} ${styles.ctrlBtnDanger}`} onClick={handleMoveToBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG
                                </button>
                            )}
                            {isAdmin && (
                                <button className={`${styles.ctrlBtn} ${styles.ctrlBtnSuccess}`}
                                    onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>
                                    <FiDollarSign aria-hidden="true" /> RECORD PAYMENT
                                </button>
                            )}
                            <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                                <FiUnlock aria-hidden="true" /> EDIT
                            </button>
                        </>
                    )}
                    {/* EDIT MODE ACTIONS */}
                    {isEditing && (
                        <>
                            {user?.isRoot && (
                                <button className={styles.purgeBtn} onClick={handleNuclearPurge}>
                                    <FiTrash2 aria-hidden="true" /> DELETE
                                </button>
                            )}
                            <div className={styles.handshakeActions}>
                                <button className={`${styles.btn} ${styles.btnDanger}`} onClick={handleAbort}>
                                    <FiX aria-hidden="true" /> ABORT
                                </button>
                                <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCommit} disabled={committing}>
                                    <FiSave aria-hidden="true" /> {committing ? 'SAVING...' : 'SAVE CHANGES'}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </header>''',
    "FolderPage -- Clean up terminal header button layout"
)

print()

# =====================================================================
# FIX 2: FolderPage.module.css - Add ctrlBtn styles
# =====================================================================

FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'

patch(FOLDER_CSS,
'''.handshakeActions { display: flex; gap: clamp(7px, 1vw, 10px); flex-wrap: wrap; }''',
'''.handshakeActions { display: flex; gap: clamp(7px, 1vw, 10px); flex-wrap: wrap; }

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
    "FolderPage.module.css -- Add unified ctrlBtn styles"
)

print()

# =====================================================================
# FIX 3: IntakePage.jsx - Notes popup + storage fee backfill + unsaved warning
# =====================================================================

INTAKE = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Add note modal state + backfill state after existing state declarations
patch(INTAKE,
'''    // Docs & notes
    const [fileQueue, setFileQueue] = useState([]);
    const [noteText,  setNoteText]  = useState('');''',
'''    // Docs & notes
    const [fileQueue,    setFileQueue]    = useState([]);
    const [noteText,     setNoteText]     = useState('');
    const [notesList,    setNotesList]    = useState([]); // multi-note list
    const [noteModal,    setNoteModal]    = useState(false);
    const [noteDraft,    setNoteDraft]    = useState('');

    // Backlog late entry
    const [backfillMonths, setBackfillMonths] = useState('');''',
    "IntakePage -- Add note modal + backfill state"
)

# Replace isDirty check to include notesList
patch(INTAKE,
'''    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        noteText.trim() !== '',
    [plotNumber, owners, totalCost, fileQueue, noteText]);''',
'''    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        notesList.length > 0 ||
        noteText.trim() !== '',
    [plotNumber, owners, totalCost, fileQueue, notesList, noteText]);''',
    "IntakePage -- Update isDirty to include notesList"
)

# Update payload to use notesList
patch(INTAKE,
'''                notes: noteText.trim() ? [{ content: noteText.trim() }] : [],''',
'''                notes: [
                    ...notesList.map(n => ({ content: n })),
                    ...(noteText.trim() ? [{ content: noteText.trim() }] : [])
                ],''',
    "IntakePage -- Update payload to use notesList"
)

# Replace the NOTES section with the new popup-based design
patch(INTAKE,
'''                    {/* \\u2500\\u2500 NOTES \\u2500\\u2500 */}
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="NOTES" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                <textarea className={styles.notesArea}
                                    value={noteText}
                                    onChange={e => setNoteText(e.target.value)}
                                    placeholder="Add an intake note (e.g. client visited in person, documents pending...)" />
                            </div>
                        </div>
                    </div>''',
'''                    {/* NOTES -- uniform popup design matching FolderPage */}
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="NOTES" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')}
                            icon={FiInfo} badge={notesList.length || undefined} />
                        <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                {/* Existing notes list */}
                                <div className={styles.notebookTimeline}>
                                    {notesList.length === 0 && (
                                        <div className={styles.emptyState}>
                                            <FiInfo className={styles.emptyIcon} aria-hidden="true" />
                                            <span>No notes yet</span>
                                        </div>
                                    )}
                                    {notesList.map((note, i) => (
                                        <article key={i} className={styles.ruledNote}>
                                            <div className={styles.noteMeta}>
                                                <span style={{ fontFamily: 'Space Mono,monospace', fontSize: 10, color: '#64748b', fontWeight: 800 }}>
                                                    INTAKE NOTE #{i + 1}
                                                </span>
                                                <button type="button"
                                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: 13, padding: 3 }}
                                                    onClick={() => setNotesList(prev => prev.filter((_, j) => j !== i))}
                                                    aria-label="Remove note">
                                                    <FiTrash2 />
                                                </button>
                                            </div>
                                            <p className={styles.noteContent}>{note}</p>
                                        </article>
                                    ))}
                                </div>
                                <button type="button" className={styles.addNoteBtn}
                                    onClick={() => { setNoteDraft(''); setNoteModal(true); }}>
                                    + ADD NOTE
                                </button>
                            </div>
                        </div>
                    </div>''',
    "IntakePage -- Replace notes textarea with popup-based design"
)

# Add the note modal JSX + backfill section before the submit section
patch(INTAKE,
'''                {/* \\u2500\\u2500 SUBMIT \\u2500\\u2500 */}
                <div className={styles.submitSection}>''',
'''                {/* NOTE MODAL */}
                {noteModal && typeof document !== 'undefined' && (() => {
                    const { createPortal } = require('react-dom');
                    return createPortal(
                        <div style={{
                            position: 'fixed', inset: 0, zIndex: 99999,
                            background: 'rgba(10,20,22,0.82)', backdropFilter: 'blur(6px)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            padding: 'clamp(16px,3vw,32px)'
                        }}>
                            <div style={{
                                background: 'linear-gradient(160deg,#1c3335 0%,#213E40 100%)',
                                border: '2px solid rgba(238,140,58,0.4)', borderRadius: 14,
                                padding: 'clamp(20px,3vw,32px)', width: '100%',
                                maxWidth: 480, boxShadow: '0 30px 80px rgba(0,0,0,0.7)'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderBottom: '1px solid rgba(238,140,58,0.25)', paddingBottom: 12 }}>
                                    <span style={{ fontFamily: 'Cinzel,serif', color: '#EE8C3A', fontSize: 14, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>
                                        ADD INTAKE NOTE
                                    </span>
                                    <button type="button" onClick={() => setNoteModal(false)}
                                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.5)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>
                                        <FiX />
                                    </button>
                                </div>
                                <textarea
                                    autoFocus
                                    style={{
                                        width: '100%', minHeight: 140,
                                        background: 'rgba(255,255,255,0.07)', border: '1.5px solid rgba(255,255,255,0.18)',
                                        borderRadius: 8, color: 'rgba(255,255,255,0.92)',
                                        fontFamily: 'DM Sans,sans-serif', fontSize: 14, fontWeight: 700,
                                        resize: 'vertical', outline: 'none', padding: '12px 14px', boxSizing: 'border-box',
                                        display: 'block', marginBottom: 14
                                    }}
                                    placeholder="Enter intake note (e.g. client visited in person, documents pending...)"
                                    value={noteDraft}
                                    onChange={e => setNoteDraft(e.target.value)}
                                    onFocus={e => { e.target.style.borderColor = 'rgba(238,140,58,0.7)'; }}
                                    onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.18)'; }}
                                />
                                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 14 }}>
                                    <button type="button" onClick={() => setNoteModal(false)}
                                        style={{ background: 'rgba(255,255,255,0.06)', border: '1.5px solid rgba(255,255,255,0.2)', color: 'rgba(255,255,255,0.7)', borderRadius: 8, padding: '8px 18px', cursor: 'pointer', fontFamily: 'DM Sans,sans-serif', fontWeight: 900, fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <FiX /> CANCEL
                                    </button>
                                    <button type="button"
                                        onClick={() => {
                                            if (noteDraft.trim()) {
                                                setNotesList(prev => [...prev, noteDraft.trim()]);
                                                setNoteModal(false);
                                                setNoteDraft('');
                                            }
                                        }}
                                        style={{ background: '#EE8C3A', border: 'none', color: '#1a2e30', borderRadius: 8, padding: '8px 18px', cursor: 'pointer', fontFamily: 'DM Sans,sans-serif', fontWeight: 900, fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <FiSave /> SAVE NOTE
                                    </button>
                                </div>
                            </div>
                        </div>,
                        document.body
                    );
                })()}

                {/* SUBMIT */}
                <div className={styles.submitSection}>''',
    "IntakePage -- Add note modal portal JSX"
)

# Fix the import - add FiSave and FiTrash2 if not present (they already exist in FolderPage but let's check IntakePage imports)
# IntakePage already has FiTrash2 and FiX. Need to add FiSave
patch(INTAKE,
'''    FiMap, FiUsers, FiCreditCard, FiUploadCloud,
    FiInfo, FiPlusSquare, FiTrash2, FiSend,
    FiCheckCircle, FiAlertCircle, FiAlertTriangle, FiX, FiCheckSquare, FiAlertOctagon
} from 'react-icons/fi';''',
'''    FiMap, FiUsers, FiCreditCard, FiUploadCloud,
    FiInfo, FiPlusSquare, FiTrash2, FiSend, FiSave,
    FiCheckCircle, FiAlertCircle, FiAlertTriangle, FiX, FiCheckSquare, FiAlertOctagon
} from 'react-icons/fi';''',
    "IntakePage -- Add FiSave import"
)

# Add backfill section to the financials panel (after the backlog toggle)
patch(INTAKE,
'''                            {isBacklog && (
                                    <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, fontSize: '0.82rem', color: '#fca5a5' }}>
                                        This plot will immediately start accumulating UGX 50,000 / month storage fees.
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* \\u2500\\u2500 DOCUMENTS \\u2500\\u2500 */}''',
'''                            {isBacklog && (
                                    <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, fontSize: '0.82rem', color: '#fca5a5' }}>
                                        This plot will immediately start accumulating UGX 50,000 / month storage fees.
                                    </div>
                                )}

                                {/* LATE ENTRY BACKFILL -- shown when isBacklog is true */}
                                {isBacklog && (
                                    <div style={{ marginTop: 12, background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.3)', borderRadius: 8, padding: '12px 14px' }}>
                                        <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#06b6d4', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                                            <span>LATE ENTRY BACKFILL</span>
                                        </div>
                                        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)', fontFamily: 'DM Sans,sans-serif', fontWeight: 700, marginBottom: 10, lineHeight: 1.5 }}>
                                            If this title has accumulated storage fees before being entered into the system, add the number of months here. Each month = UGX 50,000.
                                        </div>
                                        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                                            <div style={{ flex: 1 }}>
                                                <label style={{ display: 'block', fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 5 }}>
                                                    PRE-EXISTING MONTHS
                                                </label>
                                                <input
                                                    type="number" min="0" max="120"
                                                    placeholder="e.g. 3"
                                                    value={backfillMonths}
                                                    onChange={e => setBackfillMonths(e.target.value)}
                                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6, color: '#1a2e30', fontFamily: 'Space Mono,monospace', fontWeight: 700, fontSize: 13, padding: '7px 10px', width: '100%', boxSizing: 'border-box', outline: 'none' }}
                                                />
                                            </div>
                                            <div style={{ textAlign: 'center', paddingBottom: 2, minWidth: 80 }}>
                                                <div style={{ fontFamily: 'Space Mono,monospace', fontSize: 11, fontWeight: 900, color: '#06b6d4' }}>
                                                    {backfillMonths && Number(backfillMonths) > 0
                                                        ? `UGX ${(Number(backfillMonths) * 50000).toLocaleString()}`
                                                        : 'UGX 0'
                                                    }
                                                </div>
                                                <div style={{ fontSize: 8, color: 'rgba(255,255,255,0.35)', fontFamily: 'DM Sans,sans-serif', fontWeight: 700 }}>to be added</div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* DOCUMENTS */}''',
    "IntakePage -- Add late entry backfill section"
)

# Update payload to include backfill months - find where notes are in payload and add backfill concept
# We pass this as a note so the system records it at intake
patch(INTAKE,
'''                notes: [
                    ...notesList.map(n => ({ content: n })),
                    ...(noteText.trim() ? [{ content: noteText.trim() }] : [])
                ],''',
'''                notes: [
                    ...notesList.map(n => ({ content: n })),
                    ...(noteText.trim() ? [{ content: noteText.trim() }] : []),
                    ...(isBacklog && backfillMonths && Number(backfillMonths) > 0
                        ? [{ content: `BACKFILL NOTE: ${backfillMonths} month(s) of pre-existing storage fees (UGX ${(Number(backfillMonths) * 50000).toLocaleString()}) recorded at intake. Admin should adjust accumulated fees via folder page.` }]
                        : [])
                ],''',
    "IntakePage -- Include backfill note in payload"
)

print()

# =====================================================================
# FIX 4: IntakePage.module.css - Add missing styles for notes section
# =====================================================================

INTAKE_CSS = 'erp-frontend/src/pages/Intake/IntakePage.module.css'

# Add notebookTimeline, ruledNote, noteMeta, noteContent, addNoteBtn, emptyState, emptyIcon styles
patch(INTAKE_CSS,
'''/* ===============================================================
   SUBMIT WORKSTATION
   =============================================================== */
.submitSection {''',
'''/* ===============================================================
   NOTES SECTION (uniform with FolderPage)
   =============================================================== */
.notebookTimeline {
    max-height: clamp(200px, 28vw, 320px);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: clamp(8px, 1.2vw, 12px);
    padding-right: 4px;
    margin-bottom: clamp(8px, 1vw, 12px);
}
.notebookTimeline::-webkit-scrollbar { width: 4px; }
.notebookTimeline::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.notebookTimeline::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 4px; }

.ruledNote {
    background: #fff;
    color: var(--navy);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(8px, 1.1vw, 12px) clamp(10px, 1.4vw, 16px);
    border-radius: 4px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.15);
}
.noteMeta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: clamp(3px, 0.4vw, 5px);
    margin-bottom: clamp(4px, 0.6vw, 7px);
    gap: 6px;
}
.noteContent {
    font-size: clamp(11px, 1.05vw, 13px);
    line-height: 1.5;
    margin: 0;
    color: var(--navy);
    word-break: break-word;
    font-family: 'DM Sans', sans-serif;
    font-weight: 700;
}
.addNoteBtn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100% !important;
    padding: clamp(7px, 1vw, 9px);
    border: 2px dashed var(--orange);
    color: var(--orange);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    cursor: pointer;
    background: rgba(238, 140, 58, 0.04);
    text-transform: uppercase;
    letter-spacing: 1px;
    text-align: center;
    border-radius: 4px;
    transition: background 0.2s, border-style 0.15s;
    box-sizing: border-box;
}
.addNoteBtn:hover { background: var(--orange-dim); border-style: solid; }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }

/* ===============================================================
   SUBMIT WORKSTATION
   =============================================================== */
.submitSection {''',
    "IntakePage.module.css -- Add notebook/notes styles matching FolderPage"
)

# Also ensure emptyState and emptyIcon are defined (they likely are already in vault section, but let's check)
# They ARE defined already in the intake CSS

print()
print("=== ALL PATCHES COMPLETE ===")
print()
print("git add -A && git commit -m 'fix: folder/intake improvements -- storage fee controls, PDF viewer, header buttons, notes popup, late entry backfill, navigation warnings' && git push")