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
# STAGE 1: UNSAVED CHANGES GUARD ENFORCEMENT
# Ensures the warning modal triggers properly whenever in edit mode
# ================================================================

OLD_HOOK = """    // Wrap setBuffer so any change marks the form as touched
    const touchedSetBuffer = React.useCallback((updater) => {
        touchedRef.current = true;
        setBuffer(updater);
    }, []);

    // Unsaved changes guard -- active only while in edit mode and not mid-save
    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =
        useRouterBlock(!committing && isEditing && touchedRef.current);

    useEffect(() => {"""

NEW_HOOK = """    // Wrap setBuffer so any change marks the form as touched
    const touchedSetBuffer = React.useCallback((updater) => {
        touchedRef.current = true;
        setBuffer(updater);
    }, []);

    // Unsaved changes guard -- active only while in edit mode and not mid-save
    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =
        useRouterBlock(!committing && isEditing);

    useEffect(() => {"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_HOOK, NEW_HOOK, "FolderPage Guard Hook")


OLD_UNLOAD = """    // beforeunload -- catches tab close, hard refresh, browser back to external site
    useEffect(() => {
        if (!isEditing || committing || !touchedRef.current) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);"""

NEW_UNLOAD = """    // beforeunload -- catches tab close, hard refresh, browser back to external site
    useEffect(() => {
        if (!isEditing || committing) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_UNLOAD, NEW_UNLOAD, "FolderPage BeforeUnload")


# ================================================================
# STAGE 2: BACKLOG STATUS & EDIT MODE CONSISTENCY
# 1. Moves "EXIT BACKLOG" button up to the master terminal header.
# 2. Makes backlog details READ-ONLY unless edit mode is active.
# 3. Removes duplicate Payment button to consolidate UI.
# ================================================================

OLD_EXIT_HDR = """                            {isAdmin && !isBacklog && (
                                <button className={styles.ctrlBtnBacklog} onClick={handleMoveToBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG
                                </button>
                            )}
                            <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                                <FiUnlock aria-hidden="true" /> EDIT
                            </button>"""

NEW_EXIT_HDR = """                            {isAdmin && !isBacklog && (
                                <button className={styles.ctrlBtnBacklog} onClick={handleMoveToBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG
                                </button>
                            )}
                            {isAdmin && isBacklog && (
                                <button className={styles.ctrlBtnBacklog} onClick={handleExitBacklog}>
                                    <FiAlertOctagon aria-hidden="true" /> EXIT BACKLOG
                                </button>
                            )}
                            <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                                <FiUnlock aria-hidden="true" /> EDIT
                            </button>"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_EXIT_HDR, NEW_EXIT_HDR, "FolderPage Header Controls")


OLD_BACKLOG = """                                {/* Record Payment button — admin only, always visible in this panel */}
                                {isAdmin && !isEditing && (
                                    <div className={styles.recordPayBtnRow}>
                                        <button className={styles.recordPayBtn}
                                            onClick={() => { setPayModal({ open: true }); setPayAmount(''); setPayNotes(''); }}>
                                            <FiDollarSign aria-hidden="true" /> RECORD PAYMENT
                                        </button>
                                    </div>
                                )}
                            </div>
                        </section>

                        {/* ── 2. BACKLOG CONTROLS (admin only, shown when backlog) ── */}
                        {isAdmin && isBacklog && (
                            <section className={styles.hwPanel} aria-label="Backlog Controls">
                                <div className={styles.finPanelHeader} style={{color:'#fca5a5', borderBottomColor:'rgba(239,68,68,0.3)'}}>
                                    <FiAlertOctagon aria-hidden="true" />
                                    BACKLOG CONTROLS
                                    <button onClick={handleExitBacklog} className={styles.btnExitBacklog} style={{marginLeft:'auto'}}>
                                        EXIT BACKLOG
                                    </button>
                                </div>
                                <div className={styles.panelInner}>
                                    <div className={styles.inputGrid3}>
                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>MONTHLY STORAGE FEE (UGX)</label></div>
                                            <input type="number" className={styles.hwInput}
                                                defaultValue={project.storageFeeOverride || 50000}
                                                onBlur={async e => {
                                                    const val = Number(e.target.value);
                                                    if (val >= 0) {
                                                        try { await recoveryService.setStorageRate(project.id, val); await loadFolderData(); }
                                                        catch { /* silent */ }
                                                    }
                                                }}
                                                placeholder="50000" />
                                        </div>
                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>ADJUST ACCUMULATED FEES (UGX)</label></div>
                                            <input type="number" className={styles.hwInput}
                                                defaultValue={project.storageFeesAccumulated || 0}
                                                onBlur={async e => {
                                                    const val = Number(e.target.value);
                                                    if (val >= 0) {
                                                        try { await recoveryService.setAccumulatedFees(project.id, val); await loadFolderData(); }
                                                        catch { /* silent */ }
                                                    }
                                                }}
                                                placeholder={String(project.storageFeesAccumulated || 0)} />
                                        </div>
                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>FEES STATUS</label></div>
                                            <button type="button"
                                                className={project.storagePaused ? styles.btnResumeActive : styles.btnPauseGrey}
                                                onClick={async () => {
                                                    try {
                                                        await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                        await loadFolderData();
                                                        toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                    } catch { toast('ACTION FAILED', 'error'); }
                                                }}>
                                                {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                            </button>
                                        </div>
                                    </div>
                                    <div className={styles.inputGrid3} style={{marginTop:8}}>
                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>NEGOTIATION DEADLINE</label></div>
                                            <input type="date" className={styles.hwInput}
                                                defaultValue={project.negotiationDeadline ? project.negotiationDeadline.substring(0,10) : ''}
                                                onBlur={async e => {
                                                    try { await recoveryService.setNegotiationDeadline(project.id, e.target.value || null); await loadFolderData(); toast('DEADLINE UPDATED', 'info', 2000); }
                                                    catch { /* silent */ }
                                                }} />
                                        </div>
                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>BACKLOG START DATE OVERRIDE</label></div>
                                            <input type="date" className={styles.hwInput}
                                                defaultValue={project.backlogStartDate ? project.backlogStartDate.substring(0,10) : ''}
                                                onBlur={async e => {
                                                    if (!e.target.value) return;
                                                    try { await recoveryService.setBacklogStartOverride(project.id, e.target.value); await loadFolderData(); toast('START DATE OVERRIDDEN', 'info', 2000); }
                                                    catch { /* silent */ }
                                                }} />
                                        </div>
                                    </div>
                                    <div className={styles.editBacklogFeeHint}>
                                        Current monthly fee: UGX {fmt(effectiveMonthlyFee)}. Negotiation deadline pauses fees automatically until that date.
                                    </div>
                                </div>
                            </section>
                        )}"""

NEW_BACKLOG = """                            </div>
                        </section>

                        {/* ── 2. BACKLOG CONTROLS (admin only, shown when backlog) ── */}
                        {isAdmin && isBacklog && (
                            <section className={styles.hwPanel} aria-label="Backlog Controls">
                                <div className={styles.finPanelHeader} style={{color:'#fca5a5', borderBottomColor:'rgba(239,68,68,0.3)'}}>
                                    <FiAlertOctagon aria-hidden="true" />
                                    BACKLOG CONTROLS
                                </div>
                                <div className={styles.panelInner}>
                                    {isEditing ? (
                                        <>
                                            <div className={styles.inputGrid3}>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>MONTHLY STORAGE FEE (UGX)</label></div>
                                                    <input type="number" className={styles.hwInput}
                                                        defaultValue={project.storageFeeOverride || 50000}
                                                        onBlur={async e => {
                                                            const val = Number(e.target.value);
                                                            if (val >= 0) {
                                                                try { await recoveryService.setStorageRate(project.id, val); await loadFolderData(); toast('RATE UPDATED', 'success'); }
                                                                catch { /* silent */ }
                                                            }
                                                        }}
                                                        placeholder="50000" />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>ADJUST ACCUMULATED FEES (UGX)</label></div>
                                                    <input type="number" className={styles.hwInput}
                                                        defaultValue={project.storageFeesAccumulated || 0}
                                                        onBlur={async e => {
                                                            const val = Number(e.target.value);
                                                            if (val >= 0) {
                                                                try { await recoveryService.setAccumulatedFees(project.id, val); await loadFolderData(); toast('FEES ADJUSTED', 'success'); }
                                                                catch { /* silent */ }
                                                            }
                                                        }}
                                                        placeholder={String(project.storageFeesAccumulated || 0)} />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>FEES STATUS</label></div>
                                                    <button type="button"
                                                        className={project.storagePaused ? styles.btnResumeActive : styles.btnPauseGrey}
                                                        onClick={async () => {
                                                            try {
                                                                await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                                await loadFolderData();
                                                                toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                            } catch { toast('ACTION FAILED', 'error'); }
                                                        }}>
                                                        {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                                    </button>
                                                </div>
                                            </div>
                                            <div className={styles.inputGrid3} style={{marginTop:8}}>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>NEGOTIATION DEADLINE</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        defaultValue={project.negotiationDeadline ? project.negotiationDeadline.substring(0,10) : ''}
                                                        onBlur={async e => {
                                                            try { await recoveryService.setNegotiationDeadline(project.id, e.target.value || null); await loadFolderData(); toast('DEADLINE UPDATED', 'info', 2000); }
                                                            catch { /* silent */ }
                                                        }} />
                                                </div>
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>BACKLOG START DATE OVERRIDE</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        defaultValue={project.backlogStartDate ? project.backlogStartDate.substring(0,10) : ''}
                                                        onBlur={async e => {
                                                            if (!e.target.value) return;
                                                            try { await recoveryService.setBacklogStartOverride(project.id, e.target.value); await loadFolderData(); toast('START DATE OVERRIDDEN', 'info', 2000); }
                                                            catch { /* silent */ }
                                                        }} />
                                                </div>
                                            </div>
                                            <div className={styles.editBacklogFeeHint}>
                                                Current monthly fee: UGX {fmt(effectiveMonthlyFee)}. Negotiation deadline pauses fees automatically until that date.
                                            </div>
                                        </>
                                    ) : (
                                        <div className={styles.readOnlyGrid}>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>MONTHLY STORAGE FEE</span>
                                                <span className={styles.specValue}>UGX {fmt(effectiveMonthlyFee)}</span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>FEES STATUS</span>
                                                <span className={styles.specValue} style={{ color: project.storagePaused ? '#fcd34d' : '#86efac' }}>
                                                    {project.storagePaused ? 'PAUSED' : 'ACTIVE'}
                                                </span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>ACCUMULATED FEES</span>
                                                <span className={styles.specValue}>UGX {fmt(project.storageFeesAccumulated)}</span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>NEGOTIATION DEADLINE</span>
                                                <span className={styles.specValue}>
                                                    {project.negotiationDeadline ? new Date(project.negotiationDeadline).toLocaleDateString() : 'NONE'}
                                                </span>
                                            </div>
                                            <div className={styles.specItem}>
                                                <span className={styles.specLabel}>BACKLOG START DATE</span>
                                                <span className={styles.specValue}>
                                                    {project.backlogStartDate ? new Date(project.backlogStartDate).toLocaleDateString() : 'UNKNOWN'}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </section>
                        )}"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_BACKLOG, NEW_BACKLOG, "FolderPage Backlog Controls & Buttons")

print()
print("UI Consistency & Unsaved Changes Guard fixes applied.")
print("Run: py fix.py")