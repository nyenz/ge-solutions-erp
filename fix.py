import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK: {label}")
    else:
        print(f"MISSING: {label}")

BASE = os.path.dirname(os.path.abspath(__file__))

print("=== STARTING FOLDER PAGE & BACKLOG STAGE FIXES ===")

# ─── FIX 1: Backend - Amount Paid Save & Backlog Stage 5 ──────────────────
svc_path = os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'land', 'service', 'LandService.java')

patch(
    svc_path,
    '''        LandProject.LandProjectBuilder builder = LandProject.builder()
                .landTitle(title)
                .totalCost(totalCost)
                .amountPaid(initialPayment)
                .isLegacy(request.isLegacy())
                .status(startAsBacklog ? "BACKLOG" : "ACTIVE");''',
    '''        LandProject.LandProjectBuilder builder = LandProject.builder()
                .landTitle(title)
                .totalCost(totalCost)
                .amountPaid(initialPayment)
                .isLegacy(request.isLegacy())
                .currentStageIndex(startAsBacklog ? 5 : 1)
                .status(startAsBacklog ? "BACKLOG" : "ACTIVE");''',
    'Backend: Set Backlog default stage to 5'
)

patch(
    svc_path,
    '''        project.setTotalCost(request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());''',
    '''        project.setTotalCost(request.getTotalCost() != null ? request.getTotalCost() : BigDecimal.ZERO);
        project.setAmountPaid(request.getInitialPayment() != null ? request.getInitialPayment() : BigDecimal.ZERO);
        project.setLegacy(request.isLegacy());''',
    'Backend: Allow Amount Paid to be updated in full edit'
)

# ─── FIX 2: FolderPage - Native Popup Purge ───────────────────────────────
folder_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'DigitalFolder', 'FolderPage.jsx')
intake_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Intake', 'IntakePage.jsx')

# Replace native confirm in FolderPage
f_content = read(folder_path)
f_content = f_content.replace(
    "if (!window.confirm('Discard unsaved note?')) return;", 
    "const ok = await confirm('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');\n                    if (!ok) return;"
)
write(folder_path, f_content)
print("OK: FolderPage Native Popup Purged")

# Replace native confirm in IntakePage
i_content = read(intake_path)
i_content = i_content.replace(
    "if (!window.confirm('Discard unsaved note?')) return;", 
    "const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?');\n                        if (!ok) return;"
)
write(intake_path, i_content)
print("OK: IntakePage Native Popup Purged")


# ─── FIX 3: FolderPage - Drawer Expand/Collapse ───────────────────────────
patch(
    folder_path,
    '''    const [paying,     setPaying]     = useState(false);

    const { confirmState, confirm, handleAnswer } = useConfirm();''',
    '''    const [paying,     setPaying]     = useState(false);

    const [drawers, setDrawers] = useState({ overview: true, balance: true, backlog: true, history: true, notes: true, owners: true, docs: true });
    const toggleDrawer = key => setDrawers(p => ({ ...p, [key]: !p[key] }));

    const { confirmState, confirm, handleAnswer } = useConfirm();''',
    'FolderPage: Add drawers state'
)

patch(
    folder_path,
    '''                {activeTab === 'OVERVIEW' && (
                    <section className={styles.hwPanel} aria-label="Plot Details">
                        <div className={styles.panelInner}>''',
    '''                {activeTab === 'OVERVIEW' && (
                    <section className={styles.hwPanel} aria-label="Plot Details">
                        <DrawerHeader label="PLOT DETAILS" isOpen={drawers.overview} onClick={() => toggleDrawer('overview')} icon={FiMap} />
                        <div className={`${styles.panelBody} ${drawers.overview ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>''',
    'FolderPage: Overview Drawer Open'
)
patch(
    folder_path,
    '''                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </section>
                )}''',
    '''                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        </div>
                    </section>
                )}''',
    'FolderPage: Overview Drawer Close'
)

patch(
    folder_path,
    '''                        <section className={styles.hwPanel} aria-label="Balance Summary">
                            <div className={styles.finPanelHeader}>
                                <FiCreditCard aria-hidden="true" />
                                BALANCE SUMMARY
                            </div>
                            <div className={styles.panelInner}>''',
    '''                        <section className={styles.hwPanel} aria-label="Balance Summary">
                            <DrawerHeader label="BALANCE SUMMARY" isOpen={drawers.balance} onClick={() => toggleDrawer('balance')} icon={FiCreditCard} />
                            <div className={`${styles.panelBody} ${drawers.balance ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>''',
    'FolderPage: Balance Drawer Open'
)
patch(
    folder_path,
    '''                                        </div>
                                    </>
                                )}

                            </div>
                        </section>

                        {/* ── 2. BACKLOG MANAGEMENT (admin only, shown when backlog) ── */}''',
    '''                                        </div>
                                    </>
                                )}

                            </div>
                            </div>
                        </section>

                        {/* ── 2. BACKLOG MANAGEMENT (admin only, shown when backlog) ── */}''',
    'FolderPage: Balance Drawer Close'
)

patch(
    folder_path,
    '''                            <section className={styles.hwPanel} aria-label="Backlog Controls" id="backlog-controls">
                                <div className={styles.finPanelHeader} style={{color:'#fca5a5', borderBottomColor:'rgba(239,68,68,0.3)'}}>
                                    <FiAlertOctagon aria-hidden="true" />
                                    BACKLOG MANAGEMENT
                                </div>
                                <div className={styles.panelInner}>''',
    '''                            <section className={styles.hwPanel} aria-label="Backlog Controls" id="backlog-controls">
                                <DrawerHeader label="BACKLOG MANAGEMENT" isOpen={drawers.backlog} onClick={() => toggleDrawer('backlog')} icon={FiAlertOctagon} />
                                <div className={`${styles.panelBody} ${drawers.backlog ? styles.bodyOpen : styles.bodyClosed}`}>
                                <div className={styles.panelInner}>''',
    'FolderPage: Backlog Drawer Open'
)
patch(
    folder_path,
    '''                                        </div>
                                    )}
                                </div>
                            </section>
                        )}

                        {/* ── 3. PAYMENT HISTORY ── */}''',
    '''                                        </div>
                                    )}
                                </div>
                                </div>
                            </section>
                        )}

                        {/* ── 3. PAYMENT HISTORY ── */}''',
    'FolderPage: Backlog Drawer Close'
)

patch(
    folder_path,
    '''                        <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                            <div className={styles.finPanelHeader}>
                                <FiActivity aria-hidden="true" />
                                PAYMENT HISTORY
                                <span className={styles.finPanelCount}>{paymentCount}</span>
                            </div>
                            <div className={styles.panelInner}>''',
    '''                        <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">
                            <DrawerHeader label="PAYMENT HISTORY" isOpen={drawers.history} onClick={() => toggleDrawer('history')} icon={FiActivity} count={paymentCount} />
                            <div className={`${styles.panelBody} ${drawers.history ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>''',
    'FolderPage: History Drawer Open'
)
patch(
    folder_path,
    '''                                    </div>
                                )}
                            </div>
                        </section>

                        {/* ── 4. NOTES & CALL LOG ── */}''',
    '''                                    </div>
                                )}
                            </div>
                            </div>
                        </section>

                        {/* ── 4. NOTES & CALL LOG ── */}''',
    'FolderPage: History Drawer Close'
)

patch(
    folder_path,
    '''                        <section className={styles.hwPanel} aria-label="Notes and Call Log">
                            <div className={styles.finPanelHeader}>
                                <FiInfo aria-hidden="true" />
                                NOTES & CALL LOG
                                <span className={styles.finPanelCount}>{noteCount}</span>
                                {isEditing && (
                                    <button type="button" className={styles.addNoteInlineBtn}
                                        onClick={() => setNoteModal({open:true,id:null,content:''})}>
                                        + ADD NOTE
                                    </button>
                                )}
                            </div>
                            <div className={styles.panelInner}>''',
    '''                        <section className={styles.hwPanel} aria-label="Notes and Call Log">
                            <DrawerHeader label="NOTES & CALL LOG" isOpen={drawers.notes} onClick={() => toggleDrawer('notes')} icon={FiInfo} count={noteCount} />
                            <div className={`${styles.panelBody} ${drawers.notes ? styles.bodyOpen : styles.bodyClosed}`}>
                            <div className={styles.panelInner}>
                                {isEditing && (
                                    <button type="button" className={styles.addNoteBtn} style={{marginBottom: '10px', marginTop: '0'}}
                                        onClick={() => setNoteModal({open:true,id:null,content:''})}>
                                        + ADD NOTE
                                    </button>
                                )}''',
    'FolderPage: Notes Drawer Open'
)
patch(
    folder_path,
    '''                                    </div>
                                )}
                            </div>
                        </section>

                    </div>
                )}

                {/* ════════════════════════════════════════════════════
                    OWNERS TAB''',
    '''                                    </div>
                                )}
                            </div>
                            </div>
                        </section>

                    </div>
                )}

                {/* ════════════════════════════════════════════════════
                    OWNERS TAB''',
    'FolderPage: Notes Drawer Close'
)

patch(
    folder_path,
    '''                {activeTab === 'OWNERS' && (
                    <section className={styles.hwPanel} aria-label="Owners">
                        <div className={styles.panelInner}>''',
    '''                {activeTab === 'OWNERS' && (
                    <section className={styles.hwPanel} aria-label="Owners">
                        <DrawerHeader label="OWNERS" isOpen={drawers.owners} onClick={() => toggleDrawer('owners')} icon={FiUsers} count={project.proprietors.length} />
                        <div className={`${styles.panelBody} ${drawers.owners ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>''',
    'FolderPage: Owners Drawer Open'
)
patch(
    folder_path,
    '''                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>
                )}

                {/* ════════════════════════════════════════════════════
                    DOCUMENTS TAB''',
    '''                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        </div>
                    </section>
                )}

                {/* ════════════════════════════════════════════════════
                    DOCUMENTS TAB''',
    'FolderPage: Owners Drawer Close'
)

patch(
    folder_path,
    '''                {activeTab === 'DOCUMENTS' && (
                    <section className={styles.hwPanel} aria-label="Documents">
                        <div className={styles.finPanelHeader}>
                            <FiUploadCloud aria-hidden="true" />
                            DOCUMENTS
                            <span className={styles.finPanelCount}>{docCount}</span>
                            {isEditing && (
                                <button type="button" className={styles.addNoteInlineBtn}
                                    onClick={() => fileInputRef.current?.click()}>
                                    + UPLOAD SCANS
                                </button>
                            )}
                        </div>
                        <div className={styles.panelInner}>''',
    '''                {activeTab === 'DOCUMENTS' && (
                    <section className={styles.hwPanel} aria-label="Documents">
                        <DrawerHeader label="DOCUMENTS" isOpen={drawers.docs} onClick={() => toggleDrawer('docs')} icon={FiUploadCloud} count={docCount} />
                        <div className={`${styles.panelBody} ${drawers.docs ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>''',
    'FolderPage: Docs Drawer Open'
)
patch(
    folder_path,
    '''                                    )}
                                </>
                            )}
                        </div>
                    </section>
                )}

            </main>''',
    '''                                    )}
                                </>
                            )}
                        </div>
                        </div>
                    </section>
                )}

            </main>''',
    'FolderPage: Docs Drawer Close'
)

print("\n=== COMPLETE ===")