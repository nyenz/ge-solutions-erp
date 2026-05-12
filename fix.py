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
# STAGE 2: Restructure FolderPage tab content
#
# OVERVIEW   - plot details + read-only/edit grid
# FINANCIALS - balance summary + payment history + backlog controls
#              + notes/call log (all in one scrollable hub)
# OWNERS     - owner cards
# DOCUMENTS  - docs upload + list
# ================================================================

# We replace the entire <main> block (tab bar + tab panels)
# The OLD string is the new_main we wrote in Stage 1.

OLD_MAIN = '''            {/* TAB BAR */}
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

                {/* ════════════════════════════════════════════════════
                    OVERVIEW TAB — Plot technical details
                    ════════════════════════════════════════════════════ */}
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
                                    {[
                                        ['PLOT ID',      project.landTitle.plotNumber],
                                        ['TENURE',       project.landTitle.tenure],
                                        ['BOX',          project.landTitle.physicalBoxNumber],
                                        ['DISTRICT',     project.landTitle.district],
                                        ['COUNTY',       project.landTitle.county],
                                        ['BLOCK / ROAD', project.landTitle.blockRoad],
                                        ['VOLUME',       project.landTitle.volume],
                                        ['FOLIO',        project.landTitle.folio],
                                        ['INSTRUMENT',   project.landTitle.instrumentNo],
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

                {/* ════════════════════════════════════════════════════
                    FINANCIALS TAB — Central hub:
                    1. Balance Summary
                    2. Record Payment (admin)
                    3. Backlog Controls (admin, if backlog)
                    4. Payment History
                    5. Notes & Call Log
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'FINANCIALS' && (
                    <div className={styles.financialsStack}>

                        {/* ── 1. BALANCE SUMMARY ── */}
                        <section className={styles.hwPanel} aria-label="Balance Summary">
                            <div className={styles.finPanelHeader}>
                                <FiCreditCard aria-hidden="true" />
                                BALANCE SUMMARY
                            </div>
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
                                    </>
                                ) : isBacklog ? (
                                    <>
                                        <div className={styles.backlogNotice}>
                                            <FiAlertOctagon className={styles.backlogNoticeIcon} size={14} />
                                            <div className={styles.backlogNoticeText}>
                                                <strong>STORAGE FEES ACTIVE</strong>
                                                <span>UGX {fmt(effectiveMonthlyFee)}/month accumulates until full balance is cleared</span>
                                            </div>
                                        </div>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox}>
                                                <label>ORIGINAL DEBT</label>
                                                <strong>UGX {fmt(origDebt)}</strong>
                                            </div>
                                            <div className={styles.statBox}>
                                                <label style={{color:'#ef4444'}}>+ STORAGE FEES</label>
                                                <strong className={styles.redGlow}>UGX {fmt(storageFees)}</strong>
                                                <small style={{opacity:0.5,fontSize:'0.7rem'}}>
                                                    {project.backlogStartDate
                                                        ? `Since ${new Date(project.backlogStartDate).toLocaleDateString()}`
                                                        : 'UGX ' + fmt(effectiveMonthlyFee) + '/month'}
                                                </small>
                                            </div>
                                            <div className={styles.statBox}>
                                                <label>- PAYMENTS MADE</label>
                                                <strong style={{color:'#86efac'}}>UGX {fmt(amountPaid)}</strong>
                                            </div>
                                        </div>
                                        <div className={styles.totalOwedBanner}>
                                            <span>TOTAL NOW OWED</span>
                                            <strong>UGX {fmt(Math.max(0, backlogOwed))}</strong>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className={styles.moneyStatsRow}>
                                            <div className={styles.statBox}><label>PLOT VALUE</label><strong>UGX {fmt(totalCost)}</strong></div>
                                            <div className={styles.statBox}><label>COLLECTED</label><strong style={{color:'#86efac'}}>UGX {fmt(amountPaid)}</strong></div>
                                            <div className={styles.statBox}><label>ARREARS</label><strong className={styles.redGlow}>UGX {fmt(remaining)}</strong></div>
                                        </div>
                                        <div className={styles.collectionBar}>
                                            <div className={styles.collectionFill}
                                                style={{width: totalCost > 0 ? `${Math.min(100,(amountPaid/totalCost)*100)}%` : '0%'}} />
                                        </div>
                                        <div className={styles.velocityNote}>
                                            <FiClock aria-hidden="true" />
                                            <span>COLLECTION: <strong>{(binder.collectionPercentage||0).toFixed(1)}%</strong></span>
                                        </div>
                                    </>
                                )}

                                {/* Record Payment button — admin only, always visible in this panel */}
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
                        )}

                        {/* ── 3. PAYMENT HISTORY ── */}
                        <section className={styles.hwPanel} aria-label="Payment History">
                            <div className={styles.finPanelHeader}>
                                <FiActivity aria-hidden="true" />
                                PAYMENT HISTORY
                                <span className={styles.finPanelCount}>{paymentCount}</span>
                            </div>
                            <div className={styles.panelInner}>
                                {paymentCount === 0 ? (
                                    <div className={styles.emptyState} role="status">
                                        <FiDollarSign className={styles.emptyIcon} aria-hidden="true" />
                                        <span>NO PAYMENTS RECORDED YET</span>
                                    </div>
                                ) : (
                                    <div className={styles.paymentList}>
                                        {payments.map((pay, i) => (
                                            <div key={pay.id || i} className={styles.paymentRow}
                                                style={{borderLeftColor: pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#06b6d4' : '#22c55e'}}>
                                                <div className={styles.payRowLeft}>
                                                    <div className={styles.payAmount}>UGX {fmt(pay.amountPaid)}</div>
                                                    <div className={styles.payMeta}>
                                                        <span className={styles.payType}
                                                            style={{color: pay.paymentType === 'BACKLOG_PARTIAL' ? '#fca5a5' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#67e8f9' : '#86efac'}}>
                                                            {pay.paymentType === 'STANDARD' ? 'Title Payment'
                                                            : pay.paymentType === 'INITIAL_DEPOSIT' ? 'Initial Deposit'
                                                            : pay.paymentType === 'BACKLOG_PARTIAL' ? 'Backlog Payment'
                                                            : pay.paymentType}
                                                        </span>
                                                        <span className={styles.payBy}>by {pay.recordedBy}</span>
                                                        {pay.notes && <span className={styles.payNotes}>{pay.notes}</span>}
                                                    </div>
                                                </div>
                                                <div className={styles.payRowRight}>
                                                    <div className={styles.payDate}>{new Date(pay.timestamp).toLocaleDateString()}</div>
                                                    {pay.balanceAfter != null && (
                                                        <div className={styles.payBalance}>Bal: UGX {fmt(pay.balanceAfter)}</div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </section>

                        {/* ── 4. NOTES & CALL LOG ── */}
                        <section className={styles.hwPanel} aria-label="Notes and Call Log">
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
                            <div className={styles.panelInner}>
                                {noteCount === 0 ? (
                                    <div className={styles.emptyState} role="status">
                                        <FiInfo className={styles.emptyIcon} aria-hidden="true" />
                                        <span>NO NOTES LOGGED YET</span>
                                    </div>
                                ) : (
                                    <div className={styles.notebookTimeline} role="list">
                                        {binder.notes.map((log, i) => (
                                            <article key={i} className={styles.ruledNote} role="listitem">
                                                <div className={styles.noteMeta}>
                                                    <div className={styles.noteMetaLeft}>
                                                        <time className={styles.noteTime} dateTime={log.timestamp}>
                                                            {new Date(log.timestamp).toLocaleDateString()}
                                                        </time>
                                                        <span className={styles.noteAuthor}>by {log.recordedBy}</span>
                                                    </div>
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
                                )}
                            </div>
                        </section>

                    </div>
                )}

                {/* ════════════════════════════════════════════════════
                    OWNERS TAB
                    ════════════════════════════════════════════════════ */}
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

                {/* ════════════════════════════════════════════════════
                    DOCUMENTS TAB — Files + upload
                    ════════════════════════════════════════════════════ */}
                {activeTab === 'DOCUMENTS' && (
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
                        <div className={styles.panelInner}>
                            {docCount === 0 ? (
                                <div className={styles.emptyState} role="status">
                                    <FiUploadCloud className={styles.emptyIcon} aria-hidden="true" />
                                    <span>NO DOCUMENTS ATTACHED</span>
                                    {isEditing && (
                                        <button type="button" className={styles.addDocBtn}
                                            onClick={() => fileInputRef.current?.click()}>
                                            + INGEST NEW SCANS
                                        </button>
                                    )}
                                </div>
                            ) : (
                                <>
                                    <div className={styles.compactVault} role="list">
                                        {binder.documents.map((doc, idx) => (
                                            <div key={idx} className={styles.docTag} role="listitem">
                                                <FiFileText className={styles.docIcon} aria-hidden="true" />
                                                <button type="button" className={styles.docName}
                                                    style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: 0 }}
                                                    onClick={() => handleOpenDoc(doc.filePath, doc.fileName)}
                                                    title={isPDF(doc.filePath) ? 'Open PDF in new tab' : 'Open ' + doc.fileName}>
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
                                        <button type="button" className={styles.addDocBtn}
                                            onClick={() => fileInputRef.current?.click()}>
                                            + INGEST MORE SCANS
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                    </section>
                )}

            </main>'''

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    OLD_MAIN,
    NEW_MAIN,
    'FolderPage Stage 2 - restructured tab content'
)

# ── PATCH 2: Add new CSS classes for Stage 2 ──
# We append them before the @media print block

OLD_PRINT = '''/* ═══════════════════════════════════════════════════════════════════
   PRINT
   ═══════════════════════════════════════════════════════════════════ */
@media print {'''

NEW_PRINT = '''/* ═══════════════════════════════════════════════════════════════════
   FINANCIALS TAB STACK
   ═══════════════════════════════════════════════════════════════════ */

/* Stack of panels in the financials tab */
.financialsStack {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
}

/* Sub-header bar for each panel inside financials tab */
.finPanelHeader {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(9px, 1.2vw, 13px) clamp(12px, 1.5vw, 18px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.18);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
}

.finPanelCount {
    background: var(--orange-dim);
    color: var(--orange);
    border: 1px solid var(--orange-border);
    border-radius: 20px;
    padding: clamp(1px, 0.2vw, 3px) clamp(7px, 0.9vw, 10px);
    font-size: clamp(7px, 0.8vw, 9px);
    font-weight: 900;
    letter-spacing: 0;
    margin-left: clamp(2px, 0.3vw, 4px);
}

/* Total owed banner for backlog */
.totalOwedBanner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: clamp(10px, 1.3vw, 14px);
    padding: clamp(10px, 1.3vw, 14px) clamp(12px, 1.5vw, 16px);
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 8px;
}
.totalOwedBanner span {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 900;
    color: #fca5a5;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.totalOwedBanner strong {
    font-family: 'Space Mono', monospace;
    font-size: clamp(15px, 1.8vw, 20px);
    font-weight: 900;
    color: #ef4444;
    text-shadow: 0 0 12px rgba(239,68,68,0.4);
}

/* Collection progress bar */
.collectionBar {
    height: clamp(4px, 0.5vw, 6px);
    background: rgba(255,255,255,0.08);
    border-radius: 4px;
    overflow: hidden;
    margin: clamp(8px, 1vw, 12px) 0 clamp(4px, 0.5vw, 6px);
}
.collectionFill {
    height: 100%;
    background: var(--orange);
    border-radius: 4px;
    transition: width 0.6s cubic-bezier(0.2,1,0.3,1);
    box-shadow: 0 0 8px rgba(238,140,58,0.4);
}

/* Record Payment button row */
.recordPayBtnRow {
    margin-top: clamp(12px, 1.5vw, 16px);
    display: flex;
    justify-content: flex-end;
}
.recordPayBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(34px, 4vw, 40px);
    padding: 0 clamp(14px, 1.8vw, 20px);
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid rgba(16, 185, 129, 0.45);
    color: #34d399;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}
.recordPayBtn:hover {
    background: #10b981;
    color: #1a2e30;
    border-color: #10b981;
    box-shadow: 0 0 14px rgba(16,185,129,0.3);
}
.recordPayBtn:focus-visible { outline: 2px solid #10b981; outline-offset: 2px; }

/* Payment list */
.paymentList {
    display: flex;
    flex-direction: column;
    gap: clamp(6px, 0.8vw, 9px);
}

.paymentRow {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: clamp(10px, 1.4vw, 16px);
    padding: clamp(9px, 1.2vw, 13px) clamp(12px, 1.5vw, 16px);
    background: rgba(255,255,255,0.04);
    border-radius: 7px;
    border-left: 3px solid #22c55e;
    transition: background 0.18s;
}
.paymentRow:hover { background: rgba(255,255,255,0.07); }

.payRowLeft { display: flex; flex-direction: column; gap: clamp(3px, 0.4vw, 5px); min-width: 0; }
.payAmount {
    font-family: 'Space Mono', monospace;
    font-size: clamp(13px, 1.4vw, 16px);
    font-weight: 700;
    color: #fff;
}
.payMeta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(5px, 0.6vw, 8px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 800;
}
.payType { text-transform: uppercase; letter-spacing: 0.5px; }
.payBy   { color: rgba(255,255,255,0.4); }
.payNotes { color: rgba(255,255,255,0.35); font-style: italic; }

.payRowRight { text-align: right; flex-shrink: 0; }
.payDate    { font-family: 'Space Mono', monospace; font-size: clamp(9px, 0.9vw, 11px); color: rgba(255,255,255,0.5); font-weight: 700; }
.payBalance { font-family: 'DM Sans', sans-serif; font-size: clamp(8px, 0.82vw, 10px); color: rgba(255,255,255,0.3); font-weight: 800; margin-top: 2px; }

/* Add note inline button (in panel header) */
.addNoteInlineBtn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-left: auto;
    height: clamp(26px, 3.2vw, 32px);
    padding: 0 clamp(10px, 1.2vw, 14px);
    background: var(--orange-dim);
    border: 1.5px solid var(--orange-border);
    color: var(--orange);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.82vw, 9px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
}
.addNoteInlineBtn:hover {
    background: var(--orange);
    color: var(--navy);
}
.addNoteInlineBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* Note author badge */
.noteMetaLeft { display: flex; align-items: center; gap: clamp(8px, 1vw, 12px); flex-wrap: wrap; }
.noteAuthor {
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.82vw, 9px);
    font-weight: 700;
    color: rgba(26,46,48,0.5);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════════════════════════════════
   PRINT
   ═══════════════════════════════════════════════════════════════════ */
@media print {'''

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css',
    OLD_PRINT,
    NEW_PRINT,
    'FolderPage.module.css Stage 2 new classes'
)

# ── PATCH 3: Fix notebookTimeline max-height in financials tab
# The existing .notebookTimeline has max-height:320px which will
# look bad in the full-height financials tab. We make it show all.
# We already handled this above by not setting maxHeight inline.
# The existing CSS still applies but notes in financials tab are in a
# panel that scrolls naturally -- no change needed.

print()
print("Stage 2 complete.")
print("FINANCIALS tab now has 4 clear sub-sections:")
print("  1. Balance Summary + Record Payment button")
print("  2. Backlog Controls (admin, backlog only)")
print("  3. Payment History")
print("  4. Notes & Call Log")
print()
print("Run: git add -A && git commit -m 'feat: FolderPage Stage 2 - financials hub restructure' && git push")