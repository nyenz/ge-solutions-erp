# PATH: fix.py
# PHASE 6 - LEGACY RECEIVABLES ENTRY MODE
# Run from project root: py fix.py
#
# WHAT THIS PHASE DOES (per Section 17.6 of LLM_CONTEXT_GUIDE.md):
# Adds a simplified intake path for old titles already sitting in storage.
# Staff flip one toggle ("LEGACY RECEIVABLE") on the New Plot form; this
# hides the Stage Checklist panel (legacy titles don't need a stage
# breakdown -- Section 17.6 explicitly says this is NOT an estimation
# system, just the real lump-sum total from the ledger) and marks the
# submitted project with isLegacy = true.
#
# IMPORTANT FINDING: The backend ALREADY fully supports this. LandProject,
# LandEntryRequest, and LandService.atomicIntake() already have an
# isLegacy field/column and already persist it correctly
# (.isLegacy(request.isLegacy())). The ONLY gap was that IntakePage.jsx
# hardcoded isLegacy: false on every submission with no way for staff to
# set it true. This phase is therefore FRONTEND-ONLY -- no backend files
# touched, no migration needed.
#
# Once submitted, a Legacy Receivable behaves exactly like any other
# project for payment tracking (Section 17.6) -- no special-casing needed
# anywhere else in the app. Same duplicate-NIN check applies (unchanged,
# already runs regardless of isLegacy).
#
# PATCHED FRONTEND FILE:
#   erp-frontend/src/pages/Intake/IntakePage.jsx

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

print("Starting Phase 6 - Legacy Receivables Entry Mode...")
print("-" * 60)

intake_path = "erp-frontend/src/pages/Intake/IntakePage.jsx"

# ============================================================
# PATCH 1: Add isLegacyMode state
# ============================================================

anchor_1 = """    const [errors, setErrors] = useState({});


    // Plot fields"""

replacement_1 = """    const [errors, setErrors] = useState({});

    // PHASE 6: Legacy Receivables Entry Mode -- simplified path for old
    // titles already in storage. Single lump total cost, no stage checklist.
    const [isLegacyMode, setIsLegacyMode] = useState(false);

    // Plot fields"""

patch_file(intake_path, anchor_1, replacement_1, "IntakePage.jsx - add isLegacyMode state")

# ============================================================
# PATCH 2: Insert ENTRY MODE toggle panel above the form
# ============================================================

anchor_2 = """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Plot Registration</h1>
                    <p className={styles.subtitle}>Register a new land title into the system</p>
                </div>
            </header>

            <div className={styles.formFlow}>"""

replacement_2 = """            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Plot Registration</h1>
                    <p className={styles.subtitle}>
                        {isLegacyMode
                            ? 'Legacy Receivable -- lump-sum entry for a title already in storage'
                            : 'Register a new land title into the system'}
                    </p>
                </div>
            </header>

            <div className={styles.hwPanel} style={{ marginBottom: 16 }}>
                <div className={styles.panelInner}>
                    <div className={styles.modeRow} style={{ marginTop: 0 }}>
                        <label>ENTRY MODE</label>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button type="button"
                                className={!isLegacyMode ? styles.toggleLegacy : styles.toggleStandard}
                                onClick={() => setIsLegacyMode(false)}>
                                ✓ STANDARD PROJECT
                            </button>
                            <button type="button"
                                className={isLegacyMode ? styles.toggleLegacy : styles.toggleStandard}
                                style={isLegacyMode ? { borderColor: '#06b6d4', color: '#06b6d4', background: 'rgba(6,182,212,0.12)' } : {}}
                                onClick={() => setIsLegacyMode(true)}>
                                ⚠ LEGACY RECEIVABLE
                            </button>
                        </div>
                        {isLegacyMode && (
                            <div className={styles.backlogFeeNote} style={{ borderColor: 'rgba(6,182,212,0.25)', background: 'rgba(6,182,212,0.08)', color: 'rgba(255,255,255,0.55)' }}>
                                Enter the real total cost from the ledger in the Financials section below.
                                No stage checklist needed for legacy titles -- this behaves like a normal
                                project for payment tracking once saved.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className={styles.formFlow}>"""

patch_file(intake_path, anchor_2, replacement_2, "IntakePage.jsx - ENTRY MODE toggle panel")

# ============================================================
# PATCH 3a: Hide the STAGES panel when in Legacy mode (open)
# ============================================================

anchor_3a = """                {/* ── STAGES (Phase 4B) ── */}
                <div className={styles.hwPanel}>
                    <DrawerHeader label="STAGES" isOpen={drawers.stages} onClick={() => toggleDrawer('stages')}"""

replacement_3a = """                {/* ── STAGES (Phase 4B) -- hidden for Legacy Receivables (Section 17.6) ── */}
                {!isLegacyMode && (
                <div className={styles.hwPanel}>
                    <DrawerHeader label="STAGES" isOpen={drawers.stages} onClick={() => toggleDrawer('stages')}"""

patch_file(intake_path, anchor_3a, replacement_3a, "IntakePage.jsx - STAGES panel open guard")

# ============================================================
# PATCH 3b: Hide the STAGES panel when in Legacy mode (close)
# ============================================================

anchor_3b = """                                <button type="button" onClick={() => {
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

                {/* ── DOCUMENTS ── */}"""

replacement_3b = """                                <button type="button" onClick={() => {
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
                )}

                {/* ── DOCUMENTS ── */}"""

patch_file(intake_path, anchor_3b, replacement_3b, "IntakePage.jsx - STAGES panel close guard")

# ============================================================
# PATCH 4a: handleDuplicatePlot -- use isLegacyMode, skip stages
# ============================================================

anchor_4a = """                titleIssueDate: titleIssueDate || undefined,
                isLegacy: false,
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
                selectedStages: [
                    ...Object.entries(checkedStages).filter(([, v]) => v).map(([tid]) => ({
                        stageTemplateId: tid,
                        cost: stageCosts[tid] !== undefined ? Number(stageCosts[tid]) : undefined,
                        notes: stageNotes[tid] || undefined,
                        isCustom: false,
                    })),
                    ...customStages.map(cs => ({
                        stageName: cs.name,
                        cost: Number(cs.cost) || 0,
                        isCustom: true,
                    })),
                ],
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Saved! Now enter a new Plot ID for the duplicate', 'success', 4000);"""

replacement_4a = """                titleIssueDate: titleIssueDate || undefined,
                isLegacy: isLegacyMode,
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
                selectedStages: isLegacyMode ? [] : [
                    ...Object.entries(checkedStages).filter(([, v]) => v).map(([tid]) => ({
                        stageTemplateId: tid,
                        cost: stageCosts[tid] !== undefined ? Number(stageCosts[tid]) : undefined,
                        notes: stageNotes[tid] || undefined,
                        isCustom: false,
                    })),
                    ...customStages.map(cs => ({
                        stageName: cs.name,
                        cost: Number(cs.cost) || 0,
                        isCustom: true,
                    })),
                ],
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Saved! Now enter a new Plot ID for the duplicate', 'success', 4000);"""

patch_file(intake_path, anchor_4a, replacement_4a, "IntakePage.jsx - handleDuplicatePlot isLegacy wiring")

# ============================================================
# PATCH 4b: handleSubmit -- use isLegacyMode, skip stages
# ============================================================

anchor_4b = """                titleIssueDate: titleIssueDate || undefined,
                isLegacy: false, // Always false for new plots - legacy is a historical flag only
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
                selectedStages: [
                    ...Object.entries(checkedStages).filter(([, v]) => v).map(([tid]) => ({
                        stageTemplateId: tid,
                        cost: stageCosts[tid] !== undefined ? Number(stageCosts[tid]) : undefined,
                        notes: stageNotes[tid] || undefined,
                        isCustom: false,
                    })),
                    ...customStages.map(cs => ({
                        stageName: cs.name,
                        cost: Number(cs.cost) || 0,
                        isCustom: true,
                    })),
                ],
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Plot registered successfully!', 'success', 3000);"""

replacement_4b = """                titleIssueDate: titleIssueDate || undefined,
                isLegacy: isLegacyMode, // Section 17.6: staff flips ENTRY MODE toggle to mark a Legacy Receivable
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
                selectedStages: isLegacyMode ? [] : [
                    ...Object.entries(checkedStages).filter(([, v]) => v).map(([tid]) => ({
                        stageTemplateId: tid,
                        cost: stageCosts[tid] !== undefined ? Number(stageCosts[tid]) : undefined,
                        notes: stageNotes[tid] || undefined,
                        isCustom: false,
                    })),
                    ...customStages.map(cs => ({
                        stageName: cs.name,
                        cost: Number(cs.cost) || 0,
                        isCustom: true,
                    })),
                ],
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Plot registered successfully!', 'success', 3000);"""

patch_file(intake_path, anchor_4b, replacement_4b, "IntakePage.jsx - handleSubmit isLegacy wiring")

print("-" * 60)
print("DONE. Check for FAIL / MISSING messages above.")
print("")
print("If all OK, run:")
print("git add -A && git commit -m 'feat: Phase 6 - Legacy Receivables Entry Mode' && git push")
print("")
print("NOTE: No backend changes, no DB migration -- isLegacy already existed")
print("on LandProject/LandEntryRequest and was already being persisted by")
print("LandService.atomicIntake(). This phase only exposes it in the UI.")
print("")
print("TEST PLAN (per the permanent deferred-testing rule, run together")
print("with Phases 1-7 once Phase 7 is code-complete, not before):")
print("  1. Go to New Plot -> confirm 'ENTRY MODE' toggle appears above the form,")
print("     defaulting to STANDARD PROJECT.")
print("  2. Click LEGACY RECEIVABLE -> confirm the STAGES panel disappears and")
print("     a cyan hint box appears explaining the lump-sum entry.")
print("  3. Fill in a legacy plot (owners incl. NIN, total cost, at least one")
print("     document scan) and save -> confirm it lands in the Ledger.")
print("  4. Open the saved plot's folder -> confirm payments can be recorded")
print("     against it exactly like a normal project (Section 17.6).")
print("  5. Toggle back to STANDARD PROJECT on a fresh form -> confirm the")
print("     STAGES panel reappears and works as before (Phase 4 regression check).")
print("  6. Duplicate a Legacy Receivable via DUPLICATE PLOT -> confirm the")
print("     duplicate also saves with isLegacy true (mode toggle stays as set).")