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
# RecoveryPortal.jsx -- improve plot-level distinction so
# owner cards clearly show WHICH plots are backlog vs active,
# with separate cost breakdowns and visual separation.
# ================================================================
PORTAL = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'

patch(
    PORTAL,
    '''                        <div className={styles.plotsList}>
                            <div className={styles.plotsHeader}>PLOTS FOR THIS OWNER</div>
                            {(mission.plots || []).map(plot => (
                                <div key={plot.projectId}
                                    className={`${styles.plotRow} ${plot.isBacklog ? styles.plotRowBacklog : ''}`}>
                                    <div className={styles.plotRowLeft}>
                                        <PaymentBadge badge={plot.paymentHealthBadge} />
                                        <div className={styles.plotInfo}>
                                            <span className={styles.plotNumber}>{plot.plotNumber}</span>
                                            <span className={styles.plotBox}>BOX: {plot.physicalBoxNumber}</span>
                                            {plot.isBacklog ? (
                                                <div className={styles.backlogBreakdown}>
                                                    <span className={styles.backlogPlotTag}>BACKLOG ({plot.storageMonthsCount} months)</span>
                                                    <div className={styles.debtLine}><span>Original debt: <strong>UGX {fmt(plot.originalDebt)}</strong></span></div>
                                                    <div className={styles.debtLine}><span>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(plot.storageFeesAccumulated)}</strong></span></div>
                                                    <div className={styles.debtLine}><span>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(plot.totalBacklogOwed)}</strong></span></div>
                                                    <div className={styles.debtLine}><span>Total paid: <strong>UGX {fmt(plot.amountPaid)}</strong></span></div>
                                                </div>
                                            ) : (
                                                <div className={styles.activePlotFinance}>
                                                    <span>Balance: <strong>UGX {fmt(plot.currentBalance)}</strong></span>
                                                    <span style={{opacity:0.6, fontSize:'0.75rem'}}> of UGX {fmt(plot.totalCost)}</span>
                                                </div>
                                            )}
                                            <div className={styles.lastNote}>
                                                <FiMessageSquare aria-hidden="true" size={11} />
                                                <span>"{plot.lastInteractionNote}"</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className={styles.plotRowActions}>
                                        <button className={styles.folderBtn}
                                            onClick={() => navigate(`/folder/${plot.projectId}`)}>
                                            <FiChevronRight aria-hidden="true" /> BINDER
                                        </button>
                                        {isAdmin && (
                                            <button className={styles.payBtn}
                                                onClick={() => { setPayModal({ open: true, plot }); setPayAmount(''); setPayNotes(''); }}>
                                                <FiDollarSign aria-hidden="true" /> PAY
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>''',
    '''                        <div className={styles.plotsList}>
                            {/* Split plots into backlog and active groups */}
                            {(() => {
                                const backlogPlots = (mission.plots || []).filter(p => p.isBacklog);
                                const activePlots  = (mission.plots || []).filter(p => !p.isBacklog);
                                const renderPlot = (plot) => (
                                    <div key={plot.projectId}
                                        className={`${styles.plotRow} ${plot.isBacklog ? styles.plotRowBacklog : styles.plotRowActive}`}>
                                        <div className={styles.plotRowLeft}>
                                            <PaymentBadge badge={plot.paymentHealthBadge} />
                                            <div className={styles.plotInfo}>
                                                <div className={styles.plotTopLine}>
                                                    <span className={styles.plotNumber}>{plot.plotNumber}</span>
                                                    <span className={styles.plotBox}>BOX: {plot.physicalBoxNumber}</span>
                                                </div>
                                                {plot.isBacklog ? (
                                                    <div className={styles.backlogBreakdown}>
                                                        <span className={styles.backlogPlotTag}>
                                                            <FiAlertOctagon size={9} /> BACKLOG · {plot.storageMonthsCount} month{plot.storageMonthsCount !== 1 ? 's' : ''}
                                                        </span>
                                                        <div className={styles.debtGrid}>
                                                            <div className={styles.debtGridItem}>
                                                                <span className={styles.debtGridLabel}>ORIGINAL DEBT</span>
                                                                <span className={styles.debtGridVal}>UGX {fmt(plot.originalDebt)}</span>
                                                            </div>
                                                            <div className={styles.debtGridItem}>
                                                                <span className={styles.debtGridLabel} style={{color:'#fca5a5'}}>STORAGE FEES</span>
                                                                <span className={styles.debtGridVal} style={{color:'#ef4444'}}>UGX {fmt(plot.storageFeesAccumulated)}</span>
                                                            </div>
                                                            <div className={styles.debtGridItem}>
                                                                <span className={styles.debtGridLabel}>AMOUNT PAID</span>
                                                                <span className={styles.debtGridVal}>UGX {fmt(plot.amountPaid)}</span>
                                                            </div>
                                                            <div className={`${styles.debtGridItem} ${styles.debtGridTotal}`}>
                                                                <span className={styles.debtGridLabel} style={{color:'#fca5a5'}}>TOTAL OWED</span>
                                                                <span className={styles.debtGridVal} style={{color:'#ef4444', fontWeight:900}}>UGX {fmt(plot.totalBacklogOwed)}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className={styles.activePlotFinance}>
                                                        <div className={styles.activeFinanceRow}>
                                                            <span className={styles.activeFinanceLabel}>BALANCE</span>
                                                            <span className={styles.activeFinanceVal}>UGX {fmt(plot.currentBalance)}</span>
                                                        </div>
                                                        <div className={styles.progressTrack}>
                                                            <div className={styles.progressFill}
                                                                style={{width: plot.totalCost > 0 ? `${Math.min(100, (1 - plot.currentBalance / plot.totalCost) * 100)}%` : '0%'}} />
                                                        </div>
                                                        <span className={styles.progressPct}>
                                                            {plot.totalCost > 0 ? Math.round((1 - plot.currentBalance / plot.totalCost) * 100) : 0}% paid of UGX {fmt(plot.totalCost)}
                                                        </span>
                                                    </div>
                                                )}
                                                <div className={styles.lastNote}>
                                                    <FiMessageSquare aria-hidden="true" size={11} />
                                                    <span>"{plot.lastInteractionNote}"</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className={styles.plotRowActions}>
                                            <button className={styles.folderBtn}
                                                onClick={() => navigate(`/folder/${plot.projectId}`)}>
                                                <FiChevronRight aria-hidden="true" /> BINDER
                                            </button>
                                            {isAdmin && (
                                                <button className={styles.payBtn}
                                                    onClick={() => { setPayModal({ open: true, plot }); setPayAmount(''); setPayNotes(''); }}>
                                                    <FiDollarSign aria-hidden="true" /> PAY
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                );
                                return (
                                    <>
                                        {activePlots.length > 0 && (
                                            <>
                                                <div className={styles.plotsGroupHeader}>
                                                    <span className={styles.plotsGroupLabelActive}>ACTIVE TITLES ({activePlots.length})</span>
                                                </div>
                                                {activePlots.map(renderPlot)}
                                            </>
                                        )}
                                        {backlogPlots.length > 0 && (
                                            <>
                                                <div className={styles.plotsGroupHeader}>
                                                    <FiAlertOctagon size={10} style={{color:'#ef4444', flexShrink:0}} />
                                                    <span className={styles.plotsGroupLabelBacklog}>BACKLOG TITLES ({backlogPlots.length}) — STORAGE FEES ACTIVE</span>
                                                </div>
                                                {backlogPlots.map(renderPlot)}
                                            </>
                                        )}
                                    </>
                                );
                            })()}
                        </div>''',
    'RecoveryPortal plot grouping'
)

# ================================================================
# RecoveryPortal.module.css -- add new classes for the
# improved plot distinction layout
# ================================================================
CSS = 'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css'

patch(
    CSS,
    '.plotRowBacklog { border-left-color:rgba(239,68,68,0.7); background:rgba(239,68,68,0.08); }',
    '''.plotRowActive  { border-left-color:rgba(34,197,94,0.5); background:rgba(34,197,94,0.04); }
.plotRowBacklog { border-left-color:rgba(239,68,68,0.7); background:rgba(239,68,68,0.08); }''',
    'RecoveryPortal plotRowActive'
)

patch(
    CSS,
    '.plotRowLeft { display:flex; align-items:flex-start; gap:8px; flex:1; min-width:0; }',
    '''.plotRowLeft { display:flex; align-items:flex-start; gap:8px; flex:1; min-width:0; }
.plotTopLine { display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; margin-bottom:5px; }''',
    'RecoveryPortal plotTopLine'
)

patch(
    CSS,
    '.backlogBreakdown { display:flex; flex-direction:column; gap:3px; margin-top:4px; }',
    '''.backlogBreakdown { display:flex; flex-direction:column; gap:5px; margin-top:4px; }

.debtGrid { display:grid; grid-template-columns:1fr 1fr; gap:4px 10px; margin-top:4px; background:rgba(0,0,0,0.3); border-radius:5px; padding:6px 8px; }
.debtGridItem { display:flex; flex-direction:column; gap:1px; }
.debtGridLabel { font-family:'DM Sans',sans-serif; font-size:7px; font-weight:900; color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.8px; }
.debtGridVal { font-family:'Space Mono',monospace; font-size:10px; font-weight:700; color:#fff; }
.debtGridTotal { grid-column:1/-1; border-top:1px solid rgba(239,68,68,0.3); padding-top:4px; margin-top:2px; }

.plotsGroupHeader { display:flex; align-items:center; gap:5px; margin:8px 0 4px; padding:3px 6px; border-radius:4px; }
.plotsGroupLabelActive  { font-family:'DM Sans',sans-serif; font-size:8px; font-weight:900; color:rgba(34,197,94,0.8); text-transform:uppercase; letter-spacing:1.5px; }
.plotsGroupLabelBacklog { font-family:'DM Sans',sans-serif; font-size:8px; font-weight:900; color:rgba(239,68,68,0.85); text-transform:uppercase; letter-spacing:1.5px; }

.activeFinanceRow { display:flex; align-items:baseline; gap:8px; margin-bottom:4px; }
.activeFinanceLabel { font-family:'DM Sans',sans-serif; font-size:8px; font-weight:900; color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.8px; }
.activeFinanceVal { font-family:'Space Mono',monospace; font-size:11px; font-weight:700; color:#fff; }
.progressTrack { width:100%; height:3px; background:rgba(255,255,255,0.1); border-radius:3px; overflow:hidden; margin-bottom:3px; }
.progressFill  { height:100%; background:#22c55e; border-radius:3px; transition:width 0.4s ease; }
.progressPct   { font-family:'DM Sans',sans-serif; font-size:8px; font-weight:700; color:rgba(255,255,255,0.4); }''',
    'RecoveryPortal new plot CSS'
)

print("\nAll patches applied.")
print("Run: git add -A && git commit -m 'fix: recovery portal - clear backlog vs active plot distinction with grouped headers and debt breakdown grid' && git push")