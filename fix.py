# PATH: fix.py
# PHASE 4B CORRECTION - INSERT MISSING STAGES PANEL INTO INTAKEPAGE.JSX
# Run from project root: py fix.py
#
# WHY THIS EXISTS:
# The original Phase 4B fix.py successfully patched everything in
# IntakePage.jsx EXCEPT the actual STAGES panel insertion -- that one
# anchor didn't match because the real file content differed from what
# was assumed. Everything else from that run (state variables, the
# useEffect that loads templates, selectedStageCount, and the
# selectedStages array in both submit payloads) is already live and
# correct. This patch does the one remaining piece: inserting the
# checkbox + "+" custom-stage panel between FINANCIALS and DOCUMENTS.
#
# Confirmed against the real file content this time -- exact anchor
# text verified before writing this patch.

import os

def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  -> Saved: {path}")

def patch_file(path, anchor, replacement, label):
    content = read_file(path)
    if content is None:
        print(f"FAIL: {label} ({path} not found)")
        return
    if anchor not in content:
        print(f"MISSING: {label} (anchor not found in {path} -- may already be patched, or file changed)")
        return
    if content.count(anchor) > 1:
        print(f"WARN: {label} (anchor appears more than once -- patching first occurrence only)")
    content = content.replace(anchor, replacement, 1)
    write_file(path, content)
    print(f"OK: {label}")

print("Starting Phase 4B Correction - STAGES panel insertion into IntakePage.jsx...")
print("-" * 60)

path = "erp-frontend/src/pages/Intake/IntakePage.jsx"

anchor = """                        </div>
                    </div>
                </div>

                {/* \u2500\u2500 DOCUMENTS \u2500\u2500 */}
                <div className={styles.splitGrid}>"""

stages_panel = """                        </div>
                    </div>
                </div>

                {/* \u2500\u2500 STAGES (Phase 4B) \u2500\u2500 */}
                <div className={styles.hwPanel}>
                    <DrawerHeader label="STAGES" isOpen={drawers.stages} onClick={() => toggleDrawer('stages')}
                        icon={FiCheckSquare} badge={selectedStageCount || undefined} />
                    <div className={`${styles.panelBody} ${drawers.stages ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            <div style={{ marginBottom: 10, fontFamily: "'DM Sans',sans-serif", fontSize: 11,
                                fontWeight: 700, color: 'rgba(255,255,255,0.4)' }}>
                                Optional -- pick which stages apply to this plot. Costs default from the master
                                checklist and can be edited per plot. You can also add stages later from the folder.
                            </div>
                            {stageTemplates.map(t => {
                                const checked = !!checkedStages[t.id];
                                return (
                                    <div key={t.id} style={{ marginBottom: 8 }}>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer',
                                            fontFamily: "'DM Sans',sans-serif", fontSize: 12, fontWeight: 800, color: '#fff' }}>
                                            <input type="checkbox" checked={checked}
                                                onChange={e => setCheckedStages(prev => ({ ...prev, [t.id]: e.target.checked }))}
                                                style={{ width: 17, height: 17 }} />
                                            <span style={{ flex: 1 }}>{t.stageName}</span>
                                        </label>
                                        {checked && (
                                            <div style={{ display: 'flex', gap: 8, marginTop: 6, marginLeft: 27, flexWrap: 'wrap' }}>
                                                <input type="number"
                                                    value={stageCosts[t.id] !== undefined ? stageCosts[t.id] : String(t.defaultCost || 0)}
                                                    onChange={e => setStageCosts(prev => ({ ...prev, [t.id]: e.target.value }))}
                                                    placeholder="Cost (UGX)"
                                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                                        padding: '7px 10px', fontFamily: "'Space Mono',monospace", fontWeight: 700,
                                                        fontSize: 12, color: '#1a2e30', width: 140 }} />
                                                <input type="text"
                                                    value={stageNotes[t.id] || ''}
                                                    onChange={e => setStageNotes(prev => ({ ...prev, [t.id]: e.target.value }))}
                                                    placeholder="Notes (optional)"
                                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                                        padding: '7px 10px', fontFamily: "'DM Sans',sans-serif", fontWeight: 700,
                                                        fontSize: 12, color: '#1a2e30', flex: 1, minWidth: 140 }} />
                                            </div>
                                        )}
                                    </div>
                                );
                            })}

                            {customStages.length > 0 && (
                                <div style={{ marginTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10 }}>
                                    {customStages.map((cs, i) => (
                                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                            <span style={{ flex: 1, fontFamily: "'DM Sans',sans-serif", fontSize: 12,
                                                fontWeight: 800, color: '#EE8C3A' }}>{cs.name}</span>
                                            <span style={{ fontFamily: "'Space Mono',monospace", fontSize: 11,
                                                color: 'rgba(255,255,255,0.5)' }}>UGX {Number(cs.cost || 0).toLocaleString()}</span>
                                            <button type="button" onClick={() => setCustomStages(prev => prev.filter((_, j) => j !== i))}
                                                style={{ background: 'transparent', border: 'none', color: '#ef4444',
                                                    cursor: 'pointer', fontSize: 14, padding: 4 }}>
                                                <FiX />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                                <input type="text" value={newCustomName} onChange={e => setNewCustomName(e.target.value)}
                                    placeholder="Custom stage name"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '8px 12px', fontFamily: "'DM Sans',sans-serif", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', flex: 1, minWidth: 160 }} />
                                <input type="number" value={newCustomCost} onChange={e => setNewCustomCost(e.target.value)}
                                    placeholder="Cost"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '8px 12px', fontFamily: "'Space Mono',monospace", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', width: 120 }} />
                                <button type="button" onClick={() => {
                                        if (!newCustomName.trim()) return;
                                        setCustomStages(prev => [...prev, { name: newCustomName.trim(), cost: Number(newCustomCost) || 0 }]);
                                        setNewCustomName('');
                                        setNewCustomCost('');
                                    }}
                                    style={{ background: 'rgba(238,140,58,0.15)', border: '1.5px solid rgba(238,140,58,0.4)',
                                        color: '#EE8C3A', borderRadius: 6, padding: '8px 16px', fontFamily: "'DM Sans',sans-serif",
                                        fontWeight: 900, fontSize: 11, textTransform: 'uppercase', cursor: 'pointer',
                                        whiteSpace: 'nowrap' }}>
                                    + ADD
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* \u2500\u2500 DOCUMENTS \u2500\u2500 */}
                <div className={styles.splitGrid}>"""

patch_file(path, anchor, stages_panel, "IntakePage.jsx STAGES panel insertion (corrected anchor)")

print("-" * 60)
print("DONE. Check for FAIL / MISSING messages above.")
print("")
print("If OK, run:")
print("git add -A && git commit -m 'fix: Phase 4B correction - insert STAGES panel into IntakePage' && git push")
print("")
print("TEST PLAN:")
print("  1. Go to New Plot page -> a STAGES panel should now appear between")
print("     FINANCIALS and DOCUMENTS, showing your 6 default stages as")
print("     unchecked checkboxes.")
print("  2. Check 2 stages, edit one cost, add a custom stage.")
print("  3. Submit the plot -> open its folder -> STAGE CHECKLIST panel")
print("     (already working from the prior run) should show what you picked.")
print("")
print("NOTE: per your new instruction, all future phases (5 onward) will be")
print("written as one complete fix.py per phase -- no more A/B/C splitting.")