# fix.py -- fix112: folder stage middle-insert, related projects own panel, docs add without edit
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules" / "land"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)

EM = "@EM@"  # token replaced with em dash so this file stays pure ASCII
def em(s): return s.replace(EM, "\u2014")

jsx = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"

# 1. icons: add FiPlus (insert button) + FiFolderPlus (related projects panel)
patch(jsx,
"""FiDollarSign, FiActivity, FiHome, FiArchive
} from 'react-icons/fi';""",
"""FiDollarSign, FiActivity, FiHome, FiArchive,
FiPlus, FiFolderPlus
} from 'react-icons/fi';""",
"imports FiPlus FiFolderPlus")

# 2. stage panel: insert-position state
patch(jsx,
"""const [editCost, setEditCost] = useState(''); const [editNotes, setEditNotes] = useState(''); const [saving, setSaving] = useState(false);""",
"""const [editCost, setEditCost] = useState(''); const [editNotes, setEditNotes] = useState(''); const [saving, setSaving] = useState(false);
const [insertAfterId, setInsertAfterId] = useState(null); const [insertAfterName, setInsertAfterName] = useState('');""",
"stage insert state")

# 3. openAddModal takes a position
patch(jsx,
"""const openAddModal = async () => { try { setTemplates(await stageTemplateService.getTemplate() || []); } catch { setTemplates([]); } setCheckedTemplates({}); setCustomName(''); setCustomCost(''); setAddModalOpen(true); };""",
"""const openAddModal = async (afterId, afterName) => { try { setTemplates(await stageTemplateService.getTemplate() || []); } catch { setTemplates([]); } setCheckedTemplates({}); setCustomName(''); setCustomCost(''); setInsertAfterId(afterId || null); setInsertAfterName(afterName || ''); setAddModalOpen(true); };""",
"openAddModal position args")

# 4. handleAttach inserts at position then renumbers
patch(jsx,
"""setSaving(true);
try { await stageTemplateService.attachStages(projectId, requests); await loadStages(); setAddModalOpen(false); toast && toast('Stage(s) added', 'success'); }
catch { toast && toast('Failed to add stage(s)', 'error'); } finally { setSaving(false); }
};""",
"""setSaving(true);
try {
const created = await stageTemplateService.attachStages(projectId, requests);
const createdIds = (created || []).map(c => c.id).filter(Boolean);
if (createdIds.length) {
const currentIds = stages.map(s => s.id);
let ordered = [...currentIds, ...createdIds];
if (insertAfterId) {
const idx = currentIds.indexOf(insertAfterId);
if (idx >= 0) ordered = [...currentIds.slice(0, idx + 1), ...createdIds, ...currentIds.slice(idx + 1)];
}
await stageTemplateService.reorderProjectStages(projectId, ordered);
}
await loadStages(); setAddModalOpen(false); toast && toast(insertAfterId ? 'Stage(s) inserted under ' + insertAfterName : 'Stage(s) added at end', 'success');
}
catch { toast && toast('Failed to add stage(s)', 'error'); } finally { setSaving(false); }
};""",
"handleAttach middle insert")

# 5. per-row plus button (insert below this stage)
patch(jsx,
"""{canEdit && editingId !== stage.id && (<div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
<button type="button" className={styles.iconBtn2} aria-label="Edit stage\"""",
"""PLACEHOLDER_NEVER_MATCHES""",
"noop guard")  # safety: real patch below uses full block

patch(jsx,
"""{canEdit && editingId !== stage.id && (<div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
<button type="button" className={styles.iconBtn2} aria-label="Edit stage" onClick={() => { setEditingId(stage.id); setEditCost(String(stage.cost || 0)); setEditNotes(stage.notes || ''); }}><FiEdit3 /></button>""",
"""{canEdit && editingId !== stage.id && (<div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
<button type="button" className={styles.plusBtn} title="Insert stage below" aria-label={`Insert stage below ${stage.stageName}`} onClick={() => openAddModal(stage.id, stage.stageName)}><FiPlus /></button>
<button type="button" className={styles.iconBtn2} aria-label="Edit stage" onClick={() => { setEditingId(stage.id); setEditCost(String(stage.cost || 0)); setEditNotes(stage.notes || ''); }}><FiEdit3 /></button>""",
"stage row plus button")

# 6. add-stage button + modal title + insert context line
patch(jsx,
"""{canEdit && <button type="button" className={styles.addStageBtn} onClick={openAddModal}>+ ADD STAGE</button>}
<HardwareModal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title="ADD STAGE(S)">
<div style={{ marginBottom: 14 }}>""",
"""{canEdit && <button type="button" className={styles.addStageBtn} onClick={() => openAddModal(null, '')}>+ ADD STAGE (AT END)</button>}
<HardwareModal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title={insertAfterId ? 'INSERT STAGE(S) UNDER: ' + insertAfterName : 'ADD STAGE(S)'}>
{insertAfterId && (<div style={{ marginBottom: 10 }}><span className={styles.insertCtx}>INSERT POSITION: DIRECTLY UNDER {insertAfterName} (MIDDLE INSERT, NOT AT END)</span></div>)}
<div style={{ marginBottom: 14 }}>""",
"add stage modal insert context")

# 7. new drawer key for related projects
patch(jsx,
"""const [drawers, setDrawers] = useState({ overview: true, balance: true, recv: true, history: true, notes: true, owners: true, docs: true, stagesPanel: true });""",
"""const [drawers, setDrawers] = useState({ overview: true, balance: true, recv: true, history: true, notes: true, owners: true, related: true, docs: true, stagesPanel: true });""",
"drawers related key")

# 8. docs upload permission without edit mode
patch(jsx,
"""const canLog = true;          // any operator may log notes/calls""",
"""const canLog = true;          // any operator may log notes/calls
const canUploadDocs = isManager || role === 'ROLE_SECRETARY'; // add scans without edit mode; delete still needs edit""",
"canUploadDocs role gate")

# 9. notes tab wrapper gets print-safe class
patch(jsx,
"""<div style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>""",
"""<div className={styles.tabWrap} style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>""",
"notes tabWrap class")

# 10. owners tab wrapper + plain owners panel
patch(jsx,
"""<section className={styles.hwPanel} aria-label="Owners" style={activeTab !== 'OWNERS' ? {display:'none'} : {}}>""",
"""<div className={styles.tabWrap} style={activeTab !== 'OWNERS' ? { display: 'none' } : {}}>
<section className={styles.hwPanel} aria-label="Owners">""",
"owners tab wrapper")

# 11. remove duplicate OTHER PROJECTS table inside owner cards
patch(jsx, em("""{(portfolio.filter(r => r.sharedOwner === p.fullName).length > 0) && (
<div className={styles.ownerPortfolio}>
<h3 className={styles.sectionTitle}>OTHER PROJECTS</h3>
<table className={styles.portfolioTable}><tbody>
{portfolio.filter(r => r.sharedOwner === p.fullName).map((r, k) => (
<tr key={k} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
onKeyDown={ev => { if (ev.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
<td>#{r.index}</td><td>{r.plot || 'EM'}</td>
<td>{r.receivable ? 'RECEIVABLE' : r.titled ? 'TITLED' : 'BACKLOG'}</td>
</tr>))}
</tbody></table>
</div>)}"""), "",
"remove in-card other projects")

# 12. related projects becomes its own panel, closes owners tab wrapper
patch(jsx, em("""<h3 className={styles.sectionTitle}>RELATED PROJECTS</h3>
{portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
[...new Set(portfolio.map(r => r.sharedOwner))].map(owner => (
<div key={owner} className={styles.ownerRelGroup}>
<h4 className={styles.ownerRelName}>{owner}</h4>
<table className={styles.portfolioTable}>
<thead><tr><th>#</th><th>PLOT</th><th>STATUS</th></tr></thead>
<tbody>{portfolio.filter(r => r.sharedOwner === owner).map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
<td>#{r.index}</td><td>{r.plot || 'EM'}</td>
<td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
</tr>))}</tbody>
</table>
</div>)))}
</div></div>
</section>"""),
em("""</div></div>
</section>
<section className={styles.hwPanel} aria-label="Related Projects">
<DrawerHeader label="RELATED PROJECTS" isOpen={drawers.related} onClick={() => toggleDrawer('related')} icon={FiFolderPlus} count={portfolio.length || undefined} />
<div className={`${styles.panelBody} ${drawers.related ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
<CornerDecor hideTop />
{portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
[...new Set(portfolio.map(r => r.sharedOwner))].map(owner => (
<div key={owner} className={styles.ownerRelGroup}>
<h4 className={styles.ownerRelName}>{owner}</h4>
<table className={styles.portfolioTable}>
<thead><tr><th>#</th><th>PLOT</th><th>STATUS</th></tr></thead>
<tbody>{portfolio.filter(r => r.sharedOwner === owner).map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
<td>#{r.index}</td><td>{r.plot || 'EM'}</td>
<td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
</tr>))}</tbody>
</table>
</div>)))}
</div></div>
</section>
</div>"""),
"related projects own panel")

# 13 + 14. documents: add without edit, delete unchanged (edit only)
patch(jsx,
"""{isEditing && canEdit && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}</div>) : (<>""",
"""{canUploadDocs && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}</div>) : (<>""",
"docs empty-state add gate")
patch(jsx,
"""{isEditing && canEdit && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}
</>)}""",
"""{canUploadDocs && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()}>+ ADD SCANS</button>}
</>)}""",
"docs add gate")

# 15. frontend service: reorder project stages
patch(FE / "services" / "stageTemplateService.js",
"""removeStage: async (projectId, stageId) => {
await api.delete(`/land/projects/${projectId}/stages/${stageId}`);
},""",
"""removeStage: async (projectId, stageId) => {
await api.delete(`/land/projects/${projectId}/stages/${stageId}`);
},
reorderProjectStages: async (projectId, orderedIds) => {
const response = await api.put(`/land/projects/${projectId}/stages/reorder`, orderedIds);
return response.data;
},""",
"service reorderProjectStages")

# 16. backend controller: reorder endpoint
patch(BE / "controller" / "StageTemplateController.java",
"""@PostMapping("/land/projects/{projectId}/stages")
public ResponseEntity<List<ProjectStage>> attachStages(
@PathVariable UUID projectId, @RequestBody List<ProjectStageRequest> requests) {
return ResponseEntity.ok(stageTemplateService.attachStagesToProject(projectId, requests));
}""",
"""@PostMapping("/land/projects/{projectId}/stages")
public ResponseEntity<List<ProjectStage>> attachStages(
@PathVariable UUID projectId, @RequestBody List<ProjectStageRequest> requests) {
return ResponseEntity.ok(stageTemplateService.attachStagesToProject(projectId, requests));
}
@PutMapping("/land/projects/{projectId}/stages/reorder")
public ResponseEntity<List<ProjectStage>> reorderProjectStages(
@PathVariable UUID projectId, @RequestBody List<String> orderedIds) {
List<UUID> ids = orderedIds.stream().map(UUID::fromString).toList();
return ResponseEntity.ok(stageTemplateService.reorderProjectStages(projectId, ids));
}""",
"controller reorder endpoint")

# 17. backend service: renumber displayOrder
patch(BE / "service" / "StageTemplateService.java",
"""auditService.logAction("PROJECT_STAGES_ATTACHED", "Operator [" + getCurrentOperator() + "] attached " + created.size()
+ " stage(s) to project: " + projectId);
return created;
}""",
"""auditService.logAction("PROJECT_STAGES_ATTACHED", "Operator [" + getCurrentOperator() + "] attached " + created.size()
+ " stage(s) to project: " + projectId);
return created;
}
@Transactional
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public List<ProjectStage> reorderProjectStages(UUID projectId, List<UUID> orderedIds) {
List<ProjectStage> stages = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
if (orderedIds == null || orderedIds.isEmpty()) return stages;
java.util.Map<UUID, ProjectStage> byId = new java.util.LinkedHashMap<>();
for (ProjectStage s : stages) byId.put(s.getId(), s);
List<ProjectStage> toSave = new java.util.ArrayList<>();
int order = 0;
for (UUID id : orderedIds) {
ProjectStage s = byId.remove(id);
if (s != null) { s.setDisplayOrder(order++); toSave.add(s); }
}
for (ProjectStage s : byId.values()) { s.setDisplayOrder(order++); toSave.add(s); }
projectStageRepository.saveAll(toSave);
auditService.logAction("PROJECT_STAGES_REORDERED",
"Operator [" + getCurrentOperator() + "] reordered stages on project: " + projectId);
return projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
}""",
"service reorderProjectStages")

# 18. CSS: plus button, insert context line, print-safe tab wrapper
cssp = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"
s = read(cssp)
if "fix112" not in s:
    s += """
/* fix112: middle-insert plus button + insert position line + print-safe tab wrapper */
.plusBtn { background: transparent; border: 1px solid rgba(238,140,58,0.3); color: #EE8C3A; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 4px 6px; border-radius: 4px; transition: all 0.2s; font-size: 12px; flex-shrink: 0; }
.plusBtn:hover { background: rgba(238,140,58,0.12); border-color: #EE8C3A; }
.plusBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 1px; }
.insertCtx { font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.95vw, 11px); color: #EE8C3A; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
.tabWrap { display: block; }
@media print { .tabWrap { display: block !important; } }
"""
    write(cssp, s); print("OK fix112 css")
else:
    print("SKIP fix112 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix112: folder stage middle-insert, related projects own panel, docs add without edit"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")