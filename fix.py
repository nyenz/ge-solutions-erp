# PATH: fix.py
# PHASE 4B - STAGE TEMPLATE UI (INTAKE + FOLDERPAGE) - ADDITIVE
# Run from project root: py fix.py
#
# SCOPE OF THIS PATCH:
#
# Adds the checkbox + "+" custom-stage picker to Intake, and a new
# "STAGE CHECKLIST" panel to FolderPage that reads/writes the flexible
# ProjectStage records added in Phase 4A. This is FRONTEND ONLY -- no
# backend changes needed, since Phase 4A already built every endpoint
# this UI calls (stage-templates CRUD, project stage attach/toggle/
# cost-edit/remove).
#
# IMPORTANT DESIGN DECISION (read this before testing):
#   FolderPage's OLD 5-stage pipeline (the dots at the top: COMMITMENT,
#   FIELD WORK, DOCUMENTATION, DEED PLAN, RELEASE -- driven by
#   currentStageIndex) is left completely UNTOUCHED. It still works
#   exactly as before.
#
#   The NEW "STAGE CHECKLIST" panel added by this patch is a SEPARATE,
#   ADDITIVE system living alongside it, driven by the ProjectStage
#   table from Phase 4A. The two systems do not talk to each other yet.
#
#   Why: Dashboard's pipeline widget, Ledger sorting, and the
#   reality-override endpoint all still key off currentStageIndex.
#   Fully replacing the old pipeline with the new checklist (as
#   originally sketched in the addendum) would mean also rewriting
#   those three things in the same patch, which is exactly the kind
#   of large blind multi-file JSX risk the addendum flagged. Keeping
#   both systems side by side for now is the safer move. Retiring the
#   old pipeline in favor of the new checklist can be a small, focused
#   Phase 4C once you've used the new checklist for a while and are
#   sure the shape is right.
#
# WHAT THIS PATCH ADDS:
#   - IntakePage.jsx: a new "STAGES" panel. Staff can check any of the
#     6 master template stages (cost/notes editable per plot), or add
#     a one-off custom stage. Optional -- submitting with nothing
#     checked behaves exactly as before (no stages attached).
#   - FolderPage.jsx: a new "STAGE CHECKLIST" panel (in the OVERVIEW
#     tab, above Financials). Shows attached stages with cost/notes,
#     a completion checkbox, edit/remove (in Edit Mode), and a
#     "+ ADD STAGE" button to attach more stages later (from the
#     master checklist or custom) on any existing plot.
#
# TEST PLAN (once deployed):
#   1. New Plot page -> STAGES panel should show your 6 default
#      stages as unchecked checkboxes. Check 2 of them, edit one
#      cost, add a custom stage called "Site Visit" at UGX 20,000.
#      Submit the plot.
#   2. Open that new plot's folder -> OVERVIEW tab -> STAGE CHECKLIST
#      panel should show the 3 stages you picked, with the costs you
#      set.
#   3. Click EDIT on the folder, tick the completion checkbox on one
#      stage -> should turn green with a strikethrough.
#   4. Still in Edit Mode, click "+ ADD STAGE" -> pick one more
#      template stage -> ADD SELECTED -> should appear in the list.
#   5. Confirm the OLD pipeline dots at the top of the folder page
#      still work exactly as before (click a dot in Edit Mode,
#      confirm stage still changes) -- this proves the old system is
#      untouched.

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

print("Starting Phase 4B Patch - Stage Template UI (Intake + FolderPage)...")
print("-" * 60)

# ============================================================
# INTAKE PAGE
# ============================================================
path = "erp-frontend/src/pages/Intake/IntakePage.jsx"

patch_file(path,
    "import predictionService from '../../services/predictionService';",
    "import predictionService from '../../services/predictionService';\nimport stageTemplateService from '../../services/stageTemplateService';",
    "IntakePage.jsx import stageTemplateService")

patch_file(path,
    "    const [titleIssueDate,    setTitleIssueDate]    = useState('');",
    """    const [titleIssueDate,    setTitleIssueDate]    = useState('');

    // Stages (Phase 4B)
    const [stageTemplates, setStageTemplates] = useState([]);
    const [checkedStages,  setCheckedStages]  = useState({});
    const [stageCosts,     setStageCosts]     = useState({});
    const [stageNotes,     setStageNotes]     = useState({});
    const [customStages,   setCustomStages]   = useState([]);
    const [newCustomName,  setNewCustomName]  = useState('');
    const [newCustomCost,  setNewCustomCost]  = useState('');""",
    "IntakePage.jsx stage state variables")

patch_file(path,
    "    const sg = key => predictionService.getSuggestions(key) || [];",
    """    const sg = key => predictionService.getSuggestions(key) || [];

    // Load the master stage checklist once on mount (Phase 4B)
    useEffect(() => {
        stageTemplateService.getTemplate()
            .then(data => setStageTemplates(data || []))
            .catch(() => {});
    }, []);""",
    "IntakePage.jsx load stage templates")

patch_file(path,
    "    const [drawers, setDrawers] = useState({ plot: true, owners: true, finance: true, docs: false, notes: false });",
    "    const [drawers, setDrawers] = useState({ plot: true, owners: true, finance: true, stages: true, docs: false, notes: false });",
    "IntakePage.jsx drawers.stages key")

patch_file(path,
    "    const arrears = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));",
    "    const arrears = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));\n    const selectedStageCount = Object.values(checkedStages).filter(Boolean).length + customStages.length;",
    "IntakePage.jsx selectedStageCount")

# selectedStages in handleDuplicatePlot payload
patch_file(path,
    """                isStartAsBacklog: isBacklog,
                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
                isLegacy: false,
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
            };""",
    """                isStartAsBacklog: isBacklog,
                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
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
            };""",
    "IntakePage.jsx selectedStages in duplicate payload")

# selectedStages in handleSubmit payload
patch_file(path,
    """                isStartAsBacklog: isBacklog,
                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,
                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,
                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
                isLegacy: false, // Always false for new plots - legacy is a historical flag only
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
            };""",
    """                isStartAsBacklog: isBacklog,
                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,
                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,
                surveyDate: surveyDate || undefined,
                projectStartDate: projectStartDate || undefined,
                titleIssueDate: titleIssueDate || undefined,
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
            };""",
    "IntakePage.jsx selectedStages in submit payload")

intake_stages_panel = """                {/* STAGES (Phase 4B) */}
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

                {/* -- DOCUMENTS -- */}
                <div className={styles.splitGrid}>"""

patch_file(path,
    """                        </div>
                    </div>
                </div>

                {/* -- DOCUMENTS -- */}
                <div className={styles.splitGrid}>""",
    intake_stages_panel,
    "IntakePage.jsx STAGES panel insertion")

# ============================================================
# FOLDER PAGE
# ============================================================
path = "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"

patch_file(path,
    "import landService from '../../services/landService';",
    "import landService from '../../services/landService';\nimport stageTemplateService from '../../services/stageTemplateService';",
    "FolderPage.jsx import stageTemplateService")

patch_file(path,
    "    const [drawers, setDrawers] = useState({ overview: true, balance: true, backlog: true, history: true, notes: true, owners: true, docs: true });",
    "    const [drawers, setDrawers] = useState({ overview: true, balance: true, backlog: true, history: true, notes: true, owners: true, docs: true, stagesPanel: true });",
    "FolderPage.jsx drawers.stagesPanel key")

stage_checklist_component = '''const StageChecklistPanel = ({ projectId, isEditing, isAdmin, toast }) => {
    const [stages, setStages] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [addModalOpen, setAddModalOpen] = useState(false);
    const [checkedTemplates, setCheckedTemplates] = useState({});
    const [customName, setCustomName] = useState('');
    const [customCost, setCustomCost] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editCost, setEditCost] = useState('');
    const [editNotes, setEditNotes] = useState('');
    const [saving, setSaving] = useState(false);

    const loadStages = useCallback(async () => {
        try {
            const data = await stageTemplateService.getProjectStages(projectId);
            setStages(data || []);
        } catch { /* silent */ }
        finally { setLoading(false); }
    }, [projectId]);

    useEffect(() => { loadStages(); }, [loadStages]);

    const openAddModal = async () => {
        try {
            const t = await stageTemplateService.getTemplate();
            setTemplates(t || []);
        } catch { setTemplates([]); }
        setCheckedTemplates({});
        setCustomName('');
        setCustomCost('');
        setAddModalOpen(true);
    };

    const handleAttach = async () => {
        const requests = [];
        templates.forEach(t => {
            if (checkedTemplates[t.id]) {
                requests.push({ stageTemplateId: t.id, cost: t.defaultCost, isCustom: false });
            }
        });
        if (customName.trim()) {
            requests.push({
                stageName: customName.trim(),
                cost: Number(customCost) || 0,
                isCustom: true,
            });
        }
        if (requests.length === 0) {
            toast && toast('Select at least one stage', 'error');
            return;
        }
        setSaving(true);
        try {
            await stageTemplateService.attachStages(projectId, requests);
            await loadStages();
            setAddModalOpen(false);
            toast && toast('Stage(s) added', 'success');
        } catch {
            toast && toast('Failed to add stage(s)', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleToggleComplete = async (stage) => {
        try {
            await stageTemplateService.toggleStageCompletion(projectId, stage.id, !stage.isCompleted);
            await loadStages();
        } catch { toast && toast('Failed to update stage', 'error'); }
    };

    const startEdit = (stage) => {
        setEditingId(stage.id);
        setEditCost(String(stage.cost || 0));
        setEditNotes(stage.notes || '');
    };

    const saveEdit = async (stageId) => {
        try {
            await stageTemplateService.updateStageCost(projectId, stageId, Number(editCost) || 0, editNotes);
            setEditingId(null);
            await loadStages();
            toast && toast('Stage updated', 'success');
        } catch { toast && toast('Failed to save stage', 'error'); }
    };

    const handleRemove = async (stageId) => {
        try {
            await stageTemplateService.removeStage(projectId, stageId);
            await loadStages();
            toast && toast('Stage removed', 'warn');
        } catch { toast && toast('Failed to remove stage', 'error'); }
    };

    const rowStyle = (completed) => ({
        display: 'flex', alignItems: 'center', gap: 12,
        background: completed ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.04)',
        border: '1px solid ' + (completed ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'),
        borderRadius: 7, padding: '10px 14px', marginBottom: 8,
    });

    if (loading) return null;

    return (
        <div style={{ marginTop: 4 }}>
            {stages.length === 0 && (
                <div style={{ textAlign: 'center', padding: '24px 0', color: 'rgba(255,255,255,0.25)',
                    fontFamily: "'Space Mono',monospace", fontSize: 11, fontWeight: 900,
                    letterSpacing: 2, textTransform: 'uppercase' }}>
                    NO STAGES ATTACHED YET
                </div>
            )}
            {stages.map(stage => (
                <div key={stage.id} style={rowStyle(stage.isCompleted)}>
                    <input
                        type="checkbox"
                        checked={!!stage.isCompleted}
                        onChange={() => handleToggleComplete(stage)}
                        disabled={!isEditing}
                        style={{ width: 18, height: 18, flexShrink: 0, cursor: isEditing ? 'pointer' : 'default' }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            <strong style={{
                                fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 13,
                                color: stage.isCompleted ? '#6ee7b7' : '#fff', textTransform: 'uppercase',
                                textDecoration: stage.isCompleted ? 'line-through' : 'none',
                            }}>{stage.stageName}</strong>
                            {stage.isCustom && (
                                <span style={{ fontSize: 8, fontWeight: 900, color: '#EE8C3A',
                                    background: 'rgba(238,140,58,0.15)', padding: '2px 6px', borderRadius: 3,
                                    textTransform: 'uppercase', letterSpacing: 1 }}>CUSTOM</span>
                            )}
                        </div>
                        {editingId === stage.id ? (
                            <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                                <input type="number" value={editCost} onChange={e => setEditCost(e.target.value)}
                                    placeholder="Cost"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '6px 10px', fontFamily: "'Space Mono',monospace", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', width: 120 }} />
                                <input type="text" value={editNotes} onChange={e => setEditNotes(e.target.value)}
                                    placeholder="Notes"
                                    style={{ background: '#fff', border: '1.5px solid #c8d6d7', borderRadius: 6,
                                        padding: '6px 10px', fontFamily: "'DM Sans',sans-serif", fontWeight: 700,
                                        fontSize: 12, color: '#1a2e30', flex: 1, minWidth: 140 }} />
                                <button onClick={() => saveEdit(stage.id)}
                                    style={{ background: '#EE8C3A', border: 'none', borderRadius: 6, padding: '6px 12px',
                                        fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 10,
                                        textTransform: 'uppercase', color: '#1a2e30', cursor: 'pointer' }}>SAVE</button>
                                <button onClick={() => setEditingId(null)}
                                    style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: 6, padding: '6px 12px', fontFamily: "'DM Sans',sans-serif",
                                        fontWeight: 900, fontSize: 10, textTransform: 'uppercase', color: '#fff',
                                        cursor: 'pointer' }}>CANCEL</button>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', gap: 14, marginTop: 4, flexWrap: 'wrap' }}>
                                <span style={{ fontFamily: "'Space Mono',monospace", fontSize: 11, fontWeight: 700,
                                    color: 'rgba(255,255,255,0.6)' }}>UGX {Number(stage.cost || 0).toLocaleString()}</span>
                                {stage.notes && (
                                    <span style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 11, fontWeight: 600,
                                        color: 'rgba(255,255,255,0.4)', fontStyle: 'italic' }}>{stage.notes}</span>
                                )}
                            </div>
                        )}
                    </div>
                    {isEditing && editingId !== stage.id && (
                        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                            <button onClick={() => startEdit(stage)} title="Edit cost/notes"
                                style={{ background: 'transparent', border: 'none', color: '#EE8C3A', cursor: 'pointer',
                                    fontSize: 15, padding: 4 }}>
                                <FiEdit3 />
                            </button>
                            {isAdmin && (
                                <button onClick={() => handleRemove(stage.id)} title="Remove stage"
                                    style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer',
                                        fontSize: 15, padding: 4 }}>
                                    <FiTrash2 />
                                </button>
                            )}
                        </div>
                    )}
                </div>
            ))}

            {isEditing && (
                <button type="button" onClick={openAddModal}
                    style={{ width: '100%', marginTop: 8, padding: '10px 0', background: 'rgba(238,140,58,0.06)',
                        border: '2px dashed rgba(238,140,58,0.4)', borderRadius: 7, color: '#EE8C3A',
                        fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 11, textTransform: 'uppercase',
                        letterSpacing: 1, cursor: 'pointer' }}>
                    + ADD STAGE
                </button>
            )}

            <HardwareModal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title="ADD STAGE(S)">
                <div style={{ marginBottom: 14 }}>
                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900,
                        color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                        FROM MASTER CHECKLIST
                    </div>
                    {templates.length === 0 && (
                        <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: 11, fontFamily: "'DM Sans',sans-serif" }}>
                            No template stages available.
                        </div>
                    )}
                    {templates.map(t => (
                        <label key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0',
                            cursor: 'pointer', fontFamily: "'DM Sans',sans-serif", fontSize: 12, fontWeight: 700, color: '#fff' }}>
                            <input type="checkbox" checked={!!checkedTemplates[t.id]}
                                onChange={e => setCheckedTemplates(prev => ({ ...prev, [t.id]: e.target.checked }))}
                                style={{ width: 16, height: 16 }} />
                            <span style={{ flex: 1 }}>{t.stageName}</span>
                            <span style={{ fontFamily: "'Space Mono',monospace", fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>
                                UGX {Number(t.defaultCost || 0).toLocaleString()}
                            </span>
                        </label>
                    ))}
                </div>
                <div style={{ marginBottom: 14, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 12 }}>
                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900,
                        color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                        OR ADD A CUSTOM STAGE
                    </div>
                    <input type="text" value={customName} onChange={e => setCustomName(e.target.value)}
                        placeholder="Custom stage name"
                        style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(255,255,255,0.07)',
                            border: '1.5px solid rgba(255,255,255,0.18)', borderRadius: 8, padding: '10px 12px',
                            color: '#fff', fontFamily: "'DM Sans',sans-serif", fontWeight: 700, fontSize: 13,
                            marginBottom: 8 }} />
                    <input type="number" value={customCost} onChange={e => setCustomCost(e.target.value)}
                        placeholder="Cost (UGX)"
                        style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(255,255,255,0.07)',
                            border: '1.5px solid rgba(255,255,255,0.18)', borderRadius: 8, padding: '10px 12px',
                            color: '#fff', fontFamily: "'Space Mono',monospace", fontWeight: 700, fontSize: 13 }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                    <button onClick={() => setAddModalOpen(false)}
                        style={{ background: 'rgba(255,255,255,0.06)', border: '1.5px solid rgba(255,255,255,0.2)',
                            color: 'rgba(255,255,255,0.7)', borderRadius: 8, padding: '10px 18px',
                            fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 11, textTransform: 'uppercase',
                            cursor: 'pointer' }}>CANCEL</button>
                    <button onClick={handleAttach} disabled={saving}
                        style={{ background: '#EE8C3A', border: 'none', color: '#1a2e30', borderRadius: 8,
                            padding: '10px 20px', fontFamily: "'DM Sans',sans-serif", fontWeight: 900, fontSize: 11,
                            textTransform: 'uppercase', cursor: saving ? 'wait' : 'pointer', opacity: saving ? 0.6 : 1 }}>
                        {saving ? 'SAVING...' : 'ADD SELECTED'}
                    </button>
                </div>
            </HardwareModal>
        </div>
    );
};

// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════
const FolderPage = () => {'''

patch_file(path,
    """// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════
const FolderPage = () => {""",
    stage_checklist_component,
    "FolderPage.jsx StageChecklistPanel component")

folder_stages_section = """                                        ['SURVEY DATE',  project.landTitle.surveyDate || '---'],
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

                {/* STAGE CHECKLIST (Phase 4B, additive -- flexible stage list from ProjectStage)
                    NOTE: separate from the pipeline dots above (COMMITMENT/FIELD WORK/etc),
                    which are the older fixed 5-stage system used by Dashboard and Ledger
                    sorting. Both systems coexist for now -- see fix.py header comment. */}
                <section
                    className={styles.hwPanel}
                    aria-label="Stage Checklist"
                    style={activeTab !== 'OVERVIEW' ? {display:'none'} : {}}
                    data-print-section="STAGES"
                >
                        <DrawerHeader label="STAGE CHECKLIST" isOpen={drawers.stagesPanel} onClick={() => toggleDrawer('stagesPanel')} icon={FiCheckCircle} />
                        <div className={`${styles.panelBody} ${drawers.stagesPanel ? styles.bodyOpen : styles.bodyClosed}`}>
                        <div className={styles.panelInner}>
                            <StageChecklistPanel projectId={id} isEditing={isEditing} isAdmin={isAdmin} toast={toast} />
                        </div>
                        </div>
                </section>"""

patch_file(path,
    """                                        ['SURVEY DATE',  project.landTitle.surveyDate || '---'],
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
                </section>""",
    folder_stages_section,
    "FolderPage.jsx STAGE CHECKLIST section insertion")

print("-" * 60)
print("DONE. Check for FAIL / MISSING / SKIPPED messages above.")
print("")
print("If everything shows OK, run:")
print("git add -A && git commit -m 'feat: Phase 4B - Stage Template UI (Intake + FolderPage)' && git push")
print("")
print("REMINDER:")
print("  - Frontend only. Backend already supports all of this from Phase 4A.")
print("  - The OLD 5-stage pipeline dots on FolderPage are UNTOUCHED and still")
print("    work exactly as before. The new checklist is a separate, additive")
print("    system living alongside it -- see the big comment at the top of")
print("    this file for why.")
print("  - Per your testing plan, this stays unconfirmed until your")
print("    end-of-all-phases test pass.")