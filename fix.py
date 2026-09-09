# fix.py -- fix114: line-based repair of FolderPage.jsx (close the open OWNERS div by flattening tabs) + finish the folder batch
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules" / "land"
JSX = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
EM = "\u2014"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)
def lines_of(p): return read(p).split("\n")
def save(p, lines, label): write(p, "\n".join(lines)); print("OK", label)

def find(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]: return i
    return -1

def delete_line(lines, needle, label):
    i = find(lines, needle)
    if i < 0: print("SKIP", label); return lines
    del lines[i]; print("OK", label); return lines

def replace_line(lines, needle, new, label):
    i = find(lines, needle)
    if i < 0: print("SKIP", label); return lines
    lines[i] = new; print("OK", label); return lines

def sub_in_line(lines, needle, old, new, label):
    i = find(lines, needle)
    if i < 0 or old not in lines[i]: print("SKIP", label); return lines
    lines[i] = lines[i].replace(old, new, 1); print("OK", label); return lines

def insert_after(lines, needle, new, label):
    i = find(lines, needle)
    if i < 0: print("SKIP", label); return lines
    lines.insert(i + 1, new); print("OK", label); return lines

def insert_before(lines, needle, new, label):
    i = find(lines, needle)
    if i < 0: print("SKIP", label); return lines
    lines.insert(i, new); print("OK", label); return lines

s = read(JSX)

# ---------- BUILD FIX: flatten the OWNERS tab (remove the unclosed wrapper div) ----------
L = lines_of(JSX)
L = delete_line(L, '<div className={styles.tabWrap} style={activeTab !== \'OWNERS\'', "remove unclosed OWNERS tabWrap div")
L = sub_in_line(L, '<section className={styles.hwPanel} aria-label="Owners">', 'aria-label="Owners">', 'aria-label="Owners" style={activeTab !== \'OWNERS\' ? { display: \'none\' } : {}}>', "owners section self-hides")

# ---------- make sure prerequisites exist (idempotent) ----------
if 'FiFolderPlus' not in "\n".join(L):
    L = sub_in_line(L, 'FiDollarSign, FiActivity, FiHome, FiArchive', 'FiHome, FiArchive', 'FiHome, FiArchive,', "comma before new icons")
    L = insert_after(L, 'FiDollarSign, FiActivity, FiHome, FiArchive,', 'FiPlus, FiFolderPlus', "add FiPlus FiFolderPlus imports")
if 'insertAfterId' not in "\n".join(L):
    L = insert_after(L, "const [saving, setSaving] = useState(false);", "const [insertAfterId, setInsertAfterId] = useState(null); const [insertAfterName, setInsertAfterName] = useState('');", "insert state")
if 'const openAddModal = async (afterId, afterName)' not in "\n".join(L):
    L = replace_line(L, 'const openAddModal = async () =>', "const openAddModal = async (afterId, afterName) => { try { setTemplates(await stageTemplateService.getTemplate() || []); } catch { setTemplates([]); } setCheckedTemplates({}); setCustomName(''); setCustomCost(''); setInsertAfterId(afterId || null); setInsertAfterName(afterName || ''); setAddModalOpen(true); };", "openAddModal args")
if 'related: true' not in "\n".join(L):
    L = sub_in_line(L, 'const [drawers, setDrawers] = useState(', 'owners: true,', 'owners: true, related: true,', "drawers related key")
if 'canUploadDocs' not in "\n".join(L):
    L = insert_after(L, 'const canLog = true;', "const canUploadDocs = isManager || role === 'ROLE_SECRETARY'; // add scans without edit mode; delete still needs edit", "canUploadDocs gate")

# ---------- stage middle-insert ----------
if 'reorderProjectStages(projectId, ordered)' not in "\n".join(L):
    L = replace_line(L, 'try { await stageTemplateService.attachStages(projectId, requests); await loadStages(); setAddModalOpen(false);',
        "\n".join([
        "try {",
        "const created = await stageTemplateService.attachStages(projectId, requests);",
        "const createdIds = (created || []).map(c => c.id).filter(Boolean);",
        "if (createdIds.length) {",
        "const currentIds = stages.map(s => s.id);",
        "let ordered = [...currentIds, ...createdIds];",
        "if (insertAfterId) {",
        "const idx = currentIds.indexOf(insertAfterId);",
        "if (idx >= 0) ordered = [...currentIds.slice(0, idx + 1), ...createdIds, ...currentIds.slice(idx + 1)];",
        "}",
        "await stageTemplateService.reorderProjectStages(projectId, ordered);",
        "}",
        "await loadStages(); setAddModalOpen(false); toast && toast(insertAfterId ? 'Stage(s) inserted under ' + insertAfterName : 'Stage(s) added at end', 'success');",
        "}"]), "handleAttach middle insert")
if 'styles.plusBtn' not in "\n".join(L):
    L = insert_before(L, '<button type="button" className={styles.iconBtn2} aria-label="Edit stage"',
        '<button type="button" className={styles.plusBtn} title="Insert stage below" aria-label={`Insert stage below ${stage.stageName}`} onClick={() => openAddModal(stage.id, stage.stageName)}><FiPlus /></button>', "plus button per stage row")
L = sub_in_line(L, 'className={styles.addStageBtn} onClick={openAddModal}', 'onClick={openAddModal}>+ ADD STAGE</button>', "onClick={() => openAddModal(null, '')}>+ ADD STAGE (AT END)</button>", "add-stage button appends")
L = sub_in_line(L, 'HardwareModal isOpen={addModalOpen}', 'title="ADD STAGE(S)">', "title={insertAfterId ? 'INSERT STAGE(S) UNDER: ' + insertAfterName : 'ADD STAGE(S)'}>", "modal title shows position")
if 'styles.insertCtx' not in "\n".join(L):
    L = insert_after(L, 'HardwareModal isOpen={addModalOpen}',
        '{insertAfterId && (<div style={{ marginBottom: 10 }}><span className={styles.insertCtx}>INSERT POSITION: DIRECTLY UNDER {insertAfterName} (MIDDLE INSERT, NOT AT END)</span></div>)}', "insert context line")

# ---------- owners: drop the per-card OTHER PROJECTS block ----------
if 'styles.ownerPortfolio' in "\n".join(L):
    i = find(L, 'styles.ownerPortfolio}>')
    j = find(L, '</tbody></table>', i)
    if i > 0 and j > i:
        del L[i - 1:j + 2]
        print("OK removed in-card OTHER PROJECTS block")
    else:
        print("MISSING ownerPortfolio range")

# ---------- RELATED PROJECTS becomes its own self-hiding panel ----------
if 'aria-label="Related Projects"' not in "\n".join(L):
    i = find(L, '<h3 className={styles.sectionTitle}>RELATED PROJECTS</h3>')
    j = find(L, '</div>)))}', i)
    j2 = find(L, '</div></div>', j)
    j3 = find(L, '</section>', j2)
    if i >= 0 and j3 > i:
        new_block = [
        "</div></div>",
        "</section>",
        '<section className={styles.hwPanel} aria-label="Related Projects" style={activeTab !== \'OWNERS\' ? { display: \'none\' } : {}}>',
        '<DrawerHeader label="RELATED PROJECTS" isOpen={drawers.related} onClick={() => toggleDrawer(\'related\')} icon={FiFolderPlus} count={portfolio.length || undefined} />',
        '<div className={`${styles.panelBody} ${drawers.related ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>',
        '<CornerDecor hideTop />',
        '{portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (',
        '[...new Set(portfolio.map(r => r.sharedOwner))].map(owner => (',
        '<div key={owner} className={styles.ownerRelGroup}>',
        '<h4 className={styles.ownerRelName}>{owner}</h4>',
        '<table className={styles.portfolioTable}>',
        '<thead><tr><th>#</th><th>PLOT</th><th>STATUS</th></tr></thead>',
        '<tbody>{portfolio.filter(r => r.sharedOwner === owner).map((r, i) => (<tr key={i} onClick={() => navigate(\'/land/projects/\' + r.projectId)} tabIndex={0}',
        "onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>",
        '<td>#{r.index}</td><td>{r.plot || ' + "'" + EM + "'" + '}</td>',
        '<td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>',
        '</tr>))}</tbody>',
        '</table>',
        '</div>)))}',
        '</div></div>',
        "</section>"]
        L[i:j3 + 1] = new_block
        print("OK related projects own panel")
    else:
        print("MISSING related projects range")

# ---------- documents: second ADD SCANS button without edit mode ----------
L = sub_in_line(L, '{isEditing && canEdit && <button type="button" className={styles.addDocBtn}', '{isEditing && canEdit && ', '{canUploadDocs && ', "docs add gate")

save(JSX, L, "FolderPage.jsx rebuilt line-by-line")

# ---------- sanity: div balance inside the file ----------
s2 = read(JSX)
print("DIV OPEN/CLOSE COUNT:", s2.count('<div'), s2.count('</div>'))

# ---------- backend reorder endpoint (idempotent) ----------
ctrl = BE / "controller" / "StageTemplateController.java"
cs = read(ctrl)
if '/stages/reorder' not in cs:
    cs = cs.replace("""return ResponseEntity.ok(stageTemplateService.attachStagesToProject(projectId, requests));
}""", """return ResponseEntity.ok(stageTemplateService.attachStagesToProject(projectId, requests));
}
@PutMapping("/land/projects/{projectId}/stages/reorder")
public ResponseEntity<List<ProjectStage>> reorderProjectStages(
@PathVariable UUID projectId, @RequestBody List<String> orderedIds) {
List<UUID> ids = orderedIds.stream().map(UUID::fromString).toList();
return ResponseEntity.ok(stageTemplateService.reorderProjectStages(projectId, ids));
}""", 1)
    write(ctrl, cs); print("OK controller reorder endpoint")
else:
    print("SKIP controller reorder already present")

svc = BE / "service" / "StageTemplateService.java"
ss = read(svc)
if 'reorderProjectStages' not in ss:
    ss = ss.replace("""return created;
}""", """return created;
}
@Transactional
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public List<ProjectStage> reorderProjectStages(UUID projectId, List<UUID> orderedIds) {
List<ProjectStage> stages = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
if (orderedIds == null || orderedIds.isEmpty()) return stages;
java.util.Map<UUID, ProjectStage> byId = new java.util.LinkedHashMap<>();
for (ProjectStage st : stages) byId.put(st.getId(), st);
List<ProjectStage> toSave = new java.util.ArrayList<>();
int order = 0;
for (UUID id : orderedIds) {
ProjectStage st = byId.remove(id);
if (st != null) { st.setDisplayOrder(order++); toSave.add(st); }
}
for (ProjectStage st : byId.values()) { st.setDisplayOrder(order++); toSave.add(st); }
projectStageRepository.saveAll(toSave);
auditService.logAction("PROJECT_STAGES_REORDERED",
"Operator [" + getCurrentOperator() + "] reordered stages on project: " + projectId);
return projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);
}""", 1)
    write(svc, ss); print("OK service reorder method")
else:
    print("SKIP service reorder already present")

fe_svc = FE / "services" / "stageTemplateService.js"
fs = read(fe_svc)
if 'reorderProjectStages' not in fs:
    fs = fs.replace("""removeStage: async (projectId, stageId) => {""", """reorderProjectStages: async (projectId, orderedIds) => {
const response = await api.put(`/land/projects/${projectId}/stages/reorder`, orderedIds);
return response.data;
},
removeStage: async (projectId, stageId) => {""", 1)
    write(fe_svc, fs); print("OK frontend reorder service")
else:
    print("SKIP frontend reorder already present")

# ---------- CSS (idempotent) ----------
cssp = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"
cs2 = read(cssp)
if 'fix114' not in cs2:
    cs2 += """
/* fix114: middle-insert plus button + insert position line */
.plusBtn { background: transparent; border: 1px solid rgba(238,140,58,0.3); color: #EE8C3A; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 4px 6px; border-radius: 4px; transition: all 0.2s; font-size: 12px; flex-shrink: 0; }
.plusBtn:hover { background: rgba(238,140,58,0.12); border-color: #EE8C3A; }
.plusBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 1px; }
.insertCtx { font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.95vw, 11px); color: #EE8C3A; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
"""
    write(cssp, cs2); print("OK fix114 css")
else:
    print("SKIP fix114 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix114: line-based repair of FolderPage JSX (flatten OWNERS tab, no wrapper div), finish stage middle-insert + related panel + docs add gate"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")