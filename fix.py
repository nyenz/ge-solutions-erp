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
# STAGE 1: FolderPage tab navigation
# Replace accordion drawers with a sticky 4-tab bar:
# OVERVIEW | FINANCIALS | OWNERS | DOCUMENTS
# ================================================================

# ── PATCH 1: Add tab state and remove drawer state in FolderPage.jsx ──
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    "    const [drawers, setDrawers] = useState({ tech:true, identity:true, finance:true, vault:true, intel:true, payments:false });",
    "    const [activeTab, setActiveTab] = useState('OVERVIEW');",
    'FolderPage drawers -> activeTab'
)

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    "    const toggleDrawer = (key) => setDrawers(p => ({ ...p, [key]: !p[key] }));",
    "    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS'];",
    'FolderPage toggleDrawer -> TABS'
)

# ── PATCH 2: Replace the workstationBody JSX with tabbed layout ──
# We replace from <main className={styles.workstationBody}> to closing </main>

OLD_MAIN = '''            <main className={styles.workstationBody}>

                {/* PLOT DETAILS */}
                <section id="drawer-tech" className={styles.hwPanel} aria-label="Plot Details">
                    <DrawerHeader label="PLOT DETAILS" isOpen={drawers.tech} onClick={() => toggleDrawer('tech')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.tech ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.tech}>
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                        <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />
                                        <SmartInput label="BOX LOCATION" value={buffer.physicalBoxNumber} showCaps onChange={e => touchedSetBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                        <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                        <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="INSTRUMENT NO." value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />
                                        <SmartInput label="VOLUME" value={buffer.volume} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\\D/g,'')})} />
                                        <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />
                                    </div>
                                </>
                            ) : (
                                <div className={styles.readOnlyGrid}>
                                    {[['PLOT ID',project.landTitle.plotNumber],['TENURE',project.landTitle.tenure],['BOX',project.landTitle.physicalBoxNumber],
                                      ['DISTRICT',project.landTitle.district],['COUNTY',project.landTitle.county],['BLOCK / ROAD',project.landTitle.blockRoad],
                                      ['VOLUME',project.landTitle.volume],['FOLIO',project.landTitle.folio],['INSTRUMENT',project.landTitle.instrumentNo]
                                    ].map(([l,v],i) => (
                                        <div key={i} className={styles.specItem}>
                                            <span className={styles.specLabel}>{l}</span>
                                            <span className={styles.specValue}>{v || '---'}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                {/* OWNERS */}
                <section id="drawer-identity" className={styles.hwPanel} aria-label="Owners">
                    <DrawerHeader label="OWNERS" count={project.proprietors.length} isOpen={drawers.identity} onClick={() => toggleDrawer('identity')} icon={FiUsers} />
                    <div className={`${styles.panelBody} ${drawers.identity ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.identity}>
                        <div className={styles.panelInner}>
                            <div className={styles.ownersScroll}>
                                <div className={styles.ownersGrid2} role="list">
                                    {isEditing ? buffer.owners.map((o, idx) => (
                                        <div key={idx} className={styles.ownerEditCard} role="listitem">
                                            <div className={styles.ownerCardLabel}>ENTITY #{idx+1} {idx===0&&'(PRIMARY)'}</div>
                                            <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                            <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} onBlur={v => handlePhoneBlurCheck(idx, v)} id={`owner_${idx}_phone`} />
                                            <NINInput value={o.nationalId} onChange={v => handleOwnerChange(idx,'nationalId',v)} id={`owner_${idx}_nin`} />
                                            <EmailInput value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} onCommit={val => handleEmailCommit(idx,val)} id={`owner_${idx}_email`} />
                                            <AddressInput label="HOME ADDRESS" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />
                                        </div>
                                    )) : project.proprietors.map((p, i) => (
                                        <div key={i} className={styles.ownerStaticCard} role="listitem">
                                            <h2 className={styles.ownerName}>{p.fullName}</h2>
                                            <div className={styles.infoColumns}>
                                                <div className={styles.infoRow}><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMail   aria-hidden="true" /><span>{p.email||'---'}</span></div>
                                                <div className={styles.infoRow}><FiShield aria-hidden="true" /><span>{p.nationalId||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMapPin aria-hidden="true" /><span>{p.homeAddress||'---'}</span></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* FINANCIALS */}
                <section id="drawer-finance" className={styles.hwPanel} aria-label="Financials">
                    <DrawerHeader label="FINANCIALS" isOpen={drawers.finance} onClick={() => toggleDrawer('finance')} icon={FiCreditCard} />
                    <div className={`${styles.panelBody} ${drawers.finance ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.finance}>
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <>
                                <div className={styles.inputGrid3}>
                                    <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />
                                    <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />
                                    <div className={styles.hwInputWrap}>
                                        <div className={styles.inputLabelRow}><label>ARREARS</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                        <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                    </div>
                                </div>
                                {project.isBacklog && (
                                    <div className={styles.editBacklogFeeSection}>
                                        <div className={styles.editBacklogFeeTitleRow}>
                                            <div className={styles.editBacklogFeeTitle}>BACKLOG FEE CONTROLS</div>
                                            {isAdmin && (
                                                <button onClick={handleExitBacklog} className={styles.btnExitBacklog}>
                                                    EXIT BACKLOG
                                                </button>
                                            )}
                                        </div>
                                        <div className={styles.inputGrid3}>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>MONTHLY STORAGE FEE (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeeOverride || 50000}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setStorageRate(project.id, val);
                                                                await loadFolderData();
                                                            } catch { /* silent */ }
                                                        }
                                                    }}
                                                    placeholder="50000"
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>ADJUST TOTAL FEES (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeesAccumulated || 0}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setAccumulatedFees(project.id, val);
                                                                await loadFolderData();
                                                            } catch { /* silent */ }
                                                        }
                                                    }}
                                                    placeholder={String(project.storageFeesAccumulated || 0)}
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>FEES STATUS</label>
                                                </div>
                                                <button
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
                                                </button>
                                            </div>
                                        </div>
                                        <div className={styles.editBacklogFeeHint}>
                                            Changes apply immediately. Current monthly fee: UGX {fmt(effectiveMonthlyFee)} (default 50,000 if not set).
                                        </div>
                                    </div>
                                )}
                                </>
                            ) : isBacklog ? (
                                /* BACKLOG FINANCIAL BREAKDOWN */
                                <div>
                                    <div className={styles.backlogNotice}>
                                        <FiAlertOctagon className={styles.backlogNoticeIcon} size={14} />
                                        <div className={styles.backlogNoticeText}>
                                            <strong>STORAGE FEES ACTIVE</strong>
                                            <span>UGX {fmt(effectiveMonthlyFee)} is added every month until the full balance is cleared</span>
                                        </div>
                                    </div>
                                    <div className={styles.moneyStatsRow}>
                                        <div className={styles.statBox}>
                                            <label>ORIGINAL DEBT</label>
                                            <strong>UGX {fmt(origDebt)}</strong>
                                        </div>
                                        <div className={styles.statBox}>
                                            <label style={{color:'#ef4444'}}>STORAGE FEES ADDED</label>
                                            <strong className={styles.redGlow}>UGX {fmt(storageFees)}</strong>
                                            <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                {project.backlogStartDate
                                                    ? `Since ${new Date(project.backlogStartDate).toLocaleDateString()} @ UGX ${fmt(effectiveMonthlyFee)}/mo`
                                                    : `UGX ${fmt(effectiveMonthlyFee)}/month`}
                                            </small>
                                        </div>
                                        <div className={styles.statBox}>
                                            <label>TOTAL PAID (ALL)</label>
                                            <strong>UGX {fmt(amountPaid)}</strong>
                                        </div>
                                    </div>
                                    <div style={{ borderTop: '1px solid rgba(239,68,68,0.3)', marginTop: 12, paddingTop: 12 }}>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox} style={{ gridColumn: '1/-1' }}>
                                                <label style={{color:'#ef4444'}}>TOTAL NOW OWED</label>
                                                <strong className={styles.redGlow} style={{fontSize:'1.4rem'}}>
                                                    UGX {fmt(Math.max(0, backlogOwed))}
                                                </strong>
                                                <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                    = Original debt + storage fees − payments made
                                                </small>
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            ) : (
                                /* ACTIVE FINANCIAL */
                                <>
                                    <div className={styles.moneyStatsRow}>
                                        <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalCost)}</strong></div>
                                        <div className={styles.statBox}><label>COLLECTED</label><strong>UGX {fmt(amountPaid)}</strong></div>
                                        <div className={styles.statBox}><label>ARREARS</label><strong className={styles.redGlow}>UGX {fmt(remaining)}</strong></div>
                                    </div>
                                    <div className={styles.velocityNote}>
                                        <FiClock aria-hidden="true" />
                                        <span>COLLECTION PERFORMANCE: <strong>{(binder.collectionPercentage||0).toFixed(1)}%</strong></span>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </section>

                {/* PAYMENT HISTORY */}
                <section id="drawer-payments" className={styles.hwPanel} aria-label="Payment History">
                    <DrawerHeader label="PAYMENT HISTORY" count={paymentCount} isOpen={drawers.payments} onClick={() => toggleDrawer('payments')} icon={FiActivity} />
                    <div className={`${styles.panelBody} ${drawers.payments ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.payments}>
                        <div className={styles.panelInner}>
                            {paymentCount === 0 ? (
                                <div className={styles.emptyState} role="status">
                                    <FiDollarSign className={styles.emptyIcon} aria-hidden="true" />
                                    <span>NO PAYMENTS RECORDED</span>
                                </div>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                    {payments.map((pay, i) => (
                                        <div key={pay.id || i} style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '10px 14px', background: 'rgba(255,255,255,0.04)',
                                            borderRadius: 6, borderLeft: `3px solid ${pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : '#22c55e'}`
                                        }}>
                                            <div>
                                                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                                                    UGX {fmt(pay.amountPaid)}
                                                </div>
                                                <div style={{ fontSize: '0.72rem', opacity: 0.6 }}>
                                                    {pay.paymentType} · by {pay.recordedBy}
                                                    {pay.notes ? ` · ${pay.notes}` : ''}
                                                </div>
                                            </div>
                                            <div style={{ textAlign: 'right' }}>
                                                <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                                                    {new Date(pay.timestamp).toLocaleDateString()}
                                                </div>
                                                {pay.balanceAfter != null && (
                                                    <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                                        Balance after: UGX {fmt(pay.balanceAfter)}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                {/* DOCUMENTS + NOTES */}
                <div className={styles.intelDoubleRow}>
                    <section className={styles.hwPanel} aria-label="Documents">
                        <DrawerHeader label="DOCUMENTS" count={docCount} isOpen={drawers.vault} onClick={() => toggleDrawer('vault')} icon={FiUploadCloud} />
                        <div className={`${styles.panelBody} ${drawers.vault ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.vault}>
                            <div className={styles.panelInner}>
                                <div className={styles.compactVault} role="list">
                                    {docCount === 0 && (
                                        <div className={styles.emptyState} role="status">
                                            <FiFileText className={styles.emptyIcon} aria-hidden="true" />
                                            <span>NO DOCUMENTS ATTACHED</span>
                                        </div>
                                    )}
                                    {binder.documents.map((doc, idx) => (
                                        <div key={idx} className={styles.docTag} role="listitem">
                                            <FiFileText className={styles.docIcon} aria-hidden="true" />
                                            <button
                                                type="button"
                                                className={styles.docName}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}
                                                onClick={() => handleOpenDoc(doc.filePath, doc.fileName)}
                                                title={isPDF(doc.filePath) ? 'Open PDF in new tab' : 'Open ' + doc.fileName}
                                            >
                                                {isPDF(doc.filePath) ? '📄 ' : '🖼 '}{doc.fileName}
                                            </button>
                                            {isEditing && (
                                                <button type="button" className={styles.iconBtn}
                                                    onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>
                                                    <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                                {isEditing && (
                                    <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>
                                        + INGEST NEW SCANS
                                    </button>
                                )}
                            </div>
                        </div>
                    </section>

                    <section className={styles.hwPanel} aria-label="Notes">
                        <DrawerHeader label="NOTES" count={noteCount} isOpen={drawers.intel} onClick={() => toggleDrawer('intel')} icon={FiInfo} />
                        <div className={`${styles.panelBody} ${drawers.intel ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.intel}>
                            <div className={styles.panelInner}>
                                <div className={styles.notebookTimeline} role="list">
                                    {noteCount === 0 && (
                                        <div className={styles.emptyState} role="status">
                                            <FiInfo className={styles.emptyIcon} aria-hidden="true" />
                                            <span>NO NOTES LOGGED</span>
                                        </div>
                                    )}
                                    {binder.notes.map((log, i) => (
                                        <article key={i} className={styles.ruledNote} role="listitem">
                                            <div className={styles.noteMeta}>
                                                <time className={styles.noteTime} dateTime={log.timestamp}>
                                                    {new Date(log.timestamp).toLocaleDateString()}
                                                </time>
                                                {isEditing && (
                                                    <div className={styles.actionBlock}>
                                                        <button type="button" className={styles.iconBtn}
                                                            onClick={() => setNoteModal({open:true,id:log.id,content:log.notes})}>
                                                            <FiEdit3 className={styles.editIcon} aria-hidden="true" />
                                                        </button>
                                                        <button type="button" className={styles.iconBtn}
                                                            onClick={() => handleDeleteNote(log.id)}>
                                                            <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                            <p className={styles.noteContent}>{log.notes}</p>
                                        </article>
                                    ))}
                                </div>
                                {isEditing && (
                                    <button type="button" className={styles.addNoteBtn}
                                        onClick={() => setNoteModal({open:true,id:null,content:''})}>
                                        + ADD NOTE
                                    </button>
                                )}
                            </div>
                        </div>
                    </section>
                </div>
            </main>'''

NEW_MAIN = '''            {/* TAB BAR */}
            <div className={styles.tabBar} role="tablist" aria-label="Record sections">
                {TABS.map(tab => (
                    <button
                        key={tab}
                        role="tab"
                        aria-selected={activeTab === tab}
                        className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            <main className={styles.workstationBody} role="tabpanel">

                {/* ── OVERVIEW TAB ── */}
                {activeTab === 'OVERVIEW' && (
                    <section className={styles.hwPanel} aria-label="Plot Details">
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                        <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />
                                        <SmartInput label="BOX LOCATION" value={buffer.physicalBoxNumber} showCaps onChange={e => touchedSetBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                        <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                        <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="INSTRUMENT NO." value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />
                                        <SmartInput label="VOLUME" value={buffer.volume} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\\D/g,'')})} />
                                        <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />
                                    </div>
                                </>
                            ) : (
                                <div className={styles.readOnlyGrid}>
                                    {[['PLOT ID',project.landTitle.plotNumber],['TENURE',project.landTitle.tenure],['BOX',project.landTitle.physicalBoxNumber],
                                      ['DISTRICT',project.landTitle.district],['COUNTY',project.landTitle.county],['BLOCK / ROAD',project.landTitle.blockRoad],
                                      ['VOLUME',project.landTitle.volume],['FOLIO',project.landTitle.folio],['INSTRUMENT',project.landTitle.instrumentNo]
                                    ].map(([l,v],i) => (
                                        <div key={i} className={styles.specItem}>
                                            <span className={styles.specLabel}>{l}</span>
                                            <span className={styles.specValue}>{v || '---'}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </section>
                )}

                {/* ── FINANCIALS TAB ── */}
                {activeTab === 'FINANCIALS' && (
                    <section className={styles.hwPanel} aria-label="Financials">
                        <div className={styles.panelInner}>
                            {isEditing ? (
                                <>
                                <div className={styles.inputGrid3}>
                                    <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />
                                    <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />
                                    <div className={styles.hwInputWrap}>
                                        <div className={styles.inputLabelRow}><label>ARREARS</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                        <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                    </div>
                                </div>
                                {project.isBacklog && (
                                    <div className={styles.editBacklogFeeSection}>
                                        <div className={styles.editBacklogFeeTitleRow}>
                                            <div className={styles.editBacklogFeeTitle}>BACKLOG FEE CONTROLS</div>
                                            {isAdmin && (
                                                <button onClick={handleExitBacklog} className={styles.btnExitBacklog}>
                                                    EXIT BACKLOG
                                                </button>
                                            )}
                                        </div>
                                        <div className={styles.inputGrid3}>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>MONTHLY STORAGE FEE (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeeOverride || 50000}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setStorageRate(project.id, val);
                                                                await loadFolderData();
                                                            } catch { /* silent */ }
                                                        }
                                                    }}
                                                    placeholder="50000"
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>ADJUST TOTAL FEES (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeesAccumulated || 0}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setAccumulatedFees(project.id, val);
                                                                await loadFolderData();
                                                            } catch { /* silent */ }
                                                        }
                                                    }}
                                                    placeholder={String(project.storageFeesAccumulated || 0)}
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>FEES STATUS</label>
                                                </div>
                                                <button
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
                                                </button>
                                            </div>
                                        </div>
                                        <div className={styles.editBacklogFeeHint}>
                                            Changes apply immediately. Current monthly fee: UGX {fmt(effectiveMonthlyFee)} (default 50,000 if not set).
                                        </div>
                                    </div>
                                )}
                                </>
                            ) : isBacklog ? (
                                <div>
                                    <div className={styles.backlogNotice}>
                                        <FiAlertOctagon className={styles.backlogNoticeIcon} size={14} />
                                        <div className={styles.backlogNoticeText}>
                                            <strong>STORAGE FEES ACTIVE</strong>
                                            <span>UGX {fmt(effectiveMonthlyFee)} is added every month until the full balance is cleared</span>
                                        </div>
                                    </div>
                                    <div className={styles.moneyStatsRow}>
                                        <div className={styles.statBox}>
                                            <label>ORIGINAL DEBT</label>
                                            <strong>UGX {fmt(origDebt)}</strong>
                                        </div>
                                        <div className={styles.statBox}>
                                            <label style={{color:'#ef4444'}}>STORAGE FEES ADDED</label>
                                            <strong className={styles.redGlow}>UGX {fmt(storageFees)}</strong>
                                            <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                {project.backlogStartDate
                                                    ? `Since ${new Date(project.backlogStartDate).toLocaleDateString()} @ UGX ${fmt(effectiveMonthlyFee)}/mo`
                                                    : `UGX ${fmt(effectiveMonthlyFee)}/month`}
                                            </small>
                                        </div>
                                        <div className={styles.statBox}>
                                            <label>TOTAL PAID (ALL)</label>
                                            <strong>UGX {fmt(amountPaid)}</strong>
                                        </div>
                                    </div>
                                    <div style={{ borderTop: '1px solid rgba(239,68,68,0.3)', marginTop: 12, paddingTop: 12 }}>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox} style={{ gridColumn: '1/-1' }}>
                                                <label style={{color:'#ef4444'}}>TOTAL NOW OWED</label>
                                                <strong className={styles.redGlow} style={{fontSize:'1.4rem'}}>
                                                    UGX {fmt(Math.max(0, backlogOwed))}
                                                </strong>
                                                <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                    = Original debt + storage fees -- payments made
                                                </small>
                                            </div>
                                        </div>
                                    </div>

                                    {/* PAYMENT HISTORY inside financials tab */}
                                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: 16, paddingTop: 16 }}>
                                        <div className={styles.sectionSubHeader}>PAYMENT HISTORY</div>
                                        {paymentCount === 0 ? (
                                            <div className={styles.emptyState} role="status">
                                                <FiDollarSign className={styles.emptyIcon} aria-hidden="true" />
                                                <span>NO PAYMENTS RECORDED</span>
                                            </div>
                                        ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                {payments.map((pay, i) => (
                                                    <div key={pay.id || i} style={{
                                                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                                        padding: '10px 14px', background: 'rgba(255,255,255,0.04)',
                                                        borderRadius: 6, borderLeft: `3px solid ${pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : '#22c55e'}`
                                                    }}>
                                                        <div>
                                                            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>UGX {fmt(pay.amountPaid)}</div>
                                                            <div style={{ fontSize: '0.72rem', opacity: 0.6 }}>
                                                                {pay.paymentType} · by {pay.recordedBy}{pay.notes ? ` · ${pay.notes}` : ''}
                                                            </div>
                                                        </div>
                                                        <div style={{ textAlign: 'right' }}>
                                                            <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>{new Date(pay.timestamp).toLocaleDateString()}</div>
                                                            {pay.balanceAfter != null && (
                                                                <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>Balance after: UGX {fmt(pay.balanceAfter)}</div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className={styles.moneyStatsRow}>
                                        <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalCost)}</strong></div>
                                        <div className={styles.statBox}><label>COLLECTED</label><strong>UGX {fmt(amountPaid)}</strong></div>
                                        <div className={styles.statBox}><label>ARREARS</label><strong className={styles.redGlow}>UGX {fmt(remaining)}</strong></div>
                                    </div>
                                    <div className={styles.velocityNote}>
                                        <FiClock aria-hidden="true" />
                                        <span>COLLECTION PERFORMANCE: <strong>{(binder.collectionPercentage||0).toFixed(1)}%</strong></span>
                                    </div>

                                    {/* PAYMENT HISTORY inside financials tab */}
                                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: 16, paddingTop: 16 }}>
                                        <div className={styles.sectionSubHeader}>PAYMENT HISTORY</div>
                                        {paymentCount === 0 ? (
                                            <div className={styles.emptyState} role="status">
                                                <FiDollarSign className={styles.emptyIcon} aria-hidden="true" />
                                                <span>NO PAYMENTS RECORDED</span>
                                            </div>
                                        ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                {payments.map((pay, i) => (
                                                    <div key={pay.id || i} style={{
                                                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                                        padding: '10px 14px', background: 'rgba(255,255,255,0.04)',
                                                        borderRadius: 6, borderLeft: `3px solid ${pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : '#22c55e'}`
                                                    }}>
                                                        <div>
                                                            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>UGX {fmt(pay.amountPaid)}</div>
                                                            <div style={{ fontSize: '0.72rem', opacity: 0.6 }}>
                                                                {pay.paymentType} · by {pay.recordedBy}{pay.notes ? ` · ${pay.notes}` : ''}
                                                            </div>
                                                        </div>
                                                        <div style={{ textAlign: 'right' }}>
                                                            <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>{new Date(pay.timestamp).toLocaleDateString()}</div>
                                                            {pay.balanceAfter != null && (
                                                                <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>Balance after: UGX {fmt(pay.balanceAfter)}</div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    </section>
                )}

                {/* ── OWNERS TAB ── */}
                {activeTab === 'OWNERS' && (
                    <section className={styles.hwPanel} aria-label="Owners">
                        <div className={styles.panelInner}>
                            <div className={styles.ownersScroll}>
                                <div className={styles.ownersGrid2} role="list">
                                    {isEditing ? buffer.owners.map((o, idx) => (
                                        <div key={idx} className={styles.ownerEditCard} role="listitem">
                                            <div className={styles.ownerCardLabel}>ENTITY #{idx+1} {idx===0&&'(PRIMARY)'}</div>
                                            <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                            <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} onBlur={v => handlePhoneBlurCheck(idx, v)} id={`owner_${idx}_phone`} />
                                            <NINInput value={o.nationalId} onChange={v => handleOwnerChange(idx,'nationalId',v)} id={`owner_${idx}_nin`} />
                                            <EmailInput value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} onCommit={val => handleEmailCommit(idx,val)} id={`owner_${idx}_email`} />
                                            <AddressInput label="HOME ADDRESS" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />
                                        </div>
                                    )) : project.proprietors.map((p, i) => (
                                        <div key={i} className={styles.ownerStaticCard} role="listitem">
                                            <h2 className={styles.ownerName}>{p.fullName}</h2>
                                            <div className={styles.infoColumns}>
                                                <div className={styles.infoRow}><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMail   aria-hidden="true" /><span>{p.email||'---'}</span></div>
                                                <div className={styles.infoRow}><FiShield aria-hidden="true" /><span>{p.nationalId||'---'}</span></div>
                                                <div className={styles.infoRow}><FiMapPin aria-hidden="true" /><span>{p.homeAddress||'---'}</span></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>
                )}

                {/* ── DOCUMENTS TAB ── */}
                {activeTab === 'DOCUMENTS' && (
                    <section className={styles.hwPanel} aria-label="Documents and Notes">
                        <div className={styles.panelInner}>
                            <div className={styles.sectionSubHeader}>DOCUMENTS ({docCount})</div>
                            <div className={styles.compactVault} role="list" style={{ maxHeight: 'none' }}>
                                {docCount === 0 && (
                                    <div className={styles.emptyState} role="status">
                                        <FiFileText className={styles.emptyIcon} aria-hidden="true" />
                                        <span>NO DOCUMENTS ATTACHED</span>
                                    </div>
                                )}
                                {binder.documents.map((doc, idx) => (
                                    <div key={idx} className={styles.docTag} role="listitem">
                                        <FiFileText className={styles.docIcon} aria-hidden="true" />
                                        <button
                                            type="button"
                                            className={styles.docName}
                                            style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}
                                            onClick={() => handleOpenDoc(doc.filePath, doc.fileName)}
                                            title={isPDF(doc.filePath) ? 'Open PDF in new tab' : 'Open ' + doc.fileName}
                                        >
                                            {isPDF(doc.filePath) ? '📄 ' : '🖼 '}{doc.fileName}
                                        </button>
                                        {isEditing && (
                                            <button type="button" className={styles.iconBtn}
                                                onClick={() => handleDeleteDoc(doc.id, doc.fileName)}>
                                                <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                            {isEditing && (
                                <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>
                                    + INGEST NEW SCANS
                                </button>
                            )}

                            <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: 20, paddingTop: 16 }}>
                                <div className={styles.sectionSubHeader}>NOTES ({noteCount})</div>
                                <div className={styles.notebookTimeline} role="list" style={{ maxHeight: 'none' }}>
                                    {noteCount === 0 && (
                                        <div className={styles.emptyState} role="status">
                                            <FiInfo className={styles.emptyIcon} aria-hidden="true" />
                                            <span>NO NOTES LOGGED</span>
                                        </div>
                                    )}
                                    {binder.notes.map((log, i) => (
                                        <article key={i} className={styles.ruledNote} role="listitem">
                                            <div className={styles.noteMeta}>
                                                <time className={styles.noteTime} dateTime={log.timestamp}>
                                                    {new Date(log.timestamp).toLocaleDateString()}
                                                </time>
                                                {isEditing && (
                                                    <div className={styles.actionBlock}>
                                                        <button type="button" className={styles.iconBtn}
                                                            onClick={() => setNoteModal({open:true,id:log.id,content:log.notes})}>
                                                            <FiEdit3 className={styles.editIcon} aria-hidden="true" />
                                                        </button>
                                                        <button type="button" className={styles.iconBtn}
                                                            onClick={() => handleDeleteNote(log.id)}>
                                                            <FiTrash2 className={styles.redIcon} aria-hidden="true" />
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                            <p className={styles.noteContent}>{log.notes}</p>
                                        </article>
                                    ))}
                                </div>
                                {isEditing && (
                                    <button type="button" className={styles.addNoteBtn}
                                        onClick={() => setNoteModal({open:true,id:null,content:''})}>
                                        + ADD NOTE
                                    </button>
                                )}
                            </div>
                        </div>
                    </section>
                )}

            </main>'''

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    OLD_MAIN,
    NEW_MAIN,
    'FolderPage main content -> tabbed layout'
)

# ── PATCH 3: Remove unused DrawerHeader component (no longer needed) ──
# Keep it in file to avoid breaking anything — just leave it, it won't render

# ── PATCH 4: Add tab bar CSS to FolderPage.module.css ──
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    '/* ═══════════════════════════════════════════════════════════════════\n   WORKSTATION BODY\n   ═══════════════════════════════════════════════════════════════════ */\n.workstationBody { display: flex; flex-direction: column; gap: var(--gap-md); width: 100%; min-width: 0; }',
    '''/* ═══════════════════════════════════════════════════════════════════
   TAB BAR
   ═══════════════════════════════════════════════════════════════════ */
.tabBar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 0.8vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 2px;
    margin-bottom: clamp(10px, 1.3vw, 14px);
}
.tabBar::-webkit-scrollbar { display: none; }

.tabBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(14px, 1.8vw, 22px);
    border-radius: var(--radius-sm);
    font-family: \'DM Sans\', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.95vw, 11px);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    flex-shrink: 0;
    line-height: 1;
}
.tabBtn:hover {
    background: rgba(238, 140, 58, 0.12);
    color: #EE8C3A;
    border-color: #EE8C3A;
}
.tabBtnActive {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.35);
}
.tabBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── SECTION SUB HEADER ── */
.sectionSubHeader {
    font-family: \'DM Sans\', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: clamp(10px, 1.3vw, 14px);
    padding-bottom: clamp(6px, 0.8vw, 9px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.2);
}

/* ═══════════════════════════════════════════════════════════════════
   WORKSTATION BODY
   ═══════════════════════════════════════════════════════════════════ */
.workstationBody { display: flex; flex-direction: column; gap: var(--gap-md); width: 100%; min-width: 0; }''',
    'FolderPage.module.css add tab bar styles'
)

print()
print("Stage 1 complete: FolderPage now uses 4-tab navigation.")
print("Tabs: OVERVIEW | FINANCIALS | OWNERS | DOCUMENTS")
print()
print("Run: git add -A && git commit -m 'feat: FolderPage tab navigation (Stage 1)' && git push")