# fix.py -- fix117: stage insert root-cause (backend reorder), Intake button tones, heading glow, scroll-top button, stage rules
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules" / "land"
JSX = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
CSS = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"
CTRL = BE / "controller" / "StageTemplateController.java"
SVC = BE / "service" / "StageTemplateService.java"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)
def find(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]: return i
    return -1

NEW_COMPONENT = """/* STAGE CHECKLIST - Intake mirror (fix117): Intake/Recovery button tones,
   first stage auto-ticked, first & last stages locked from delete,
   RESTORE DEFAULTS like Intake, insert-below never after the last stage. */
const StageChecklistPanel = ({ projectId, canEdit, canRemove, toast }) => {
    const [stages, setStages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [insertAfterId, setInsertAfterId] = useState(null);
    const [insertAfterName, setInsertAfterName] = useState('');
    const [saving, setSaving] = useState(false);
    const autoTicked = useRef(false);
    const loadStages = useCallback(async () => { try { setStages(await stageTemplateService.getProjectStages(projectId) || []); } catch {} finally { setLoading(false); } }, [projectId]);
    useEffect(() => { loadStages(); }, [loadStages]);
    useEffect(() => {
        if (!canEdit || autoTicked.current || loading || !stages.length) return;
        autoTicked.current = true;
        if (!stages[0].isCompleted) {
            stageTemplateService.toggleStageCompletion(projectId, stages[0].id, true).then(loadStages).catch(() => {});
        }
    }, [stages, loading, canEdit, projectId, loadStages]);
    const openInsertBelow = (stage) => { setInsertAfterId(stage.id); setInsertAfterName(stage.stageName); setNewStageName(''); setAddingStage(true); };
    const cancelInsert = () => { setAddingStage(false); setNewStageName(''); setInsertAfterId(null); setInsertAfterName(''); };
    const handleAddStage = async () => {
        const name = newStageName.trim();
        if (!name) { toast && toast('Enter a stage name first.', 'error'); return; }
        if (stages.some(s => (s.stageName || '').toLowerCase() === name.toLowerCase())) { toast && toast('That stage is already on the list.', 'error'); return; }
        setSaving(true);
        try {
            const created = await stageTemplateService.attachStages(projectId, [{ stageName: name, cost: 0, isCustom: true }]);
            const createdIds = (created || []).map(c => c.id).filter(Boolean);
            if (createdIds.length && insertAfterId) {
                const currentIds = stages.map(s => s.id);
                const idx = currentIds.indexOf(insertAfterId);
                const ordered = idx >= 0 ? [...currentIds.slice(0, idx + 1), ...createdIds, ...currentIds.slice(idx + 1)] : [...currentIds, ...createdIds];
                await stageTemplateService.reorderProjectStages(projectId, ordered);
            }
            await loadStages(); cancelInsert(); toast && toast('Stage inserted.', 'success');
        } catch { await loadStages(); cancelInsert(); toast && toast('Stage saved but position update failed - refresh to view.', 'error'); } finally { setSaving(false); }
    };
    const handleToggleComplete = async (stage) => { try { await stageTemplateService.toggleStageCompletion(projectId, stage.id, !stage.isCompleted); await loadStages(); } catch { toast && toast('Failed to update stage', 'error'); } };
    const handleRemove = async (stageId) => { try { await stageTemplateService.removeStage(projectId, stageId); await loadStages(); toast && toast('Stage removed.', 'warn'); } catch { toast && toast('Failed to remove stage', 'error'); } };
    const handleRestoreDefaults = async () => {
        setSaving(true);
        try {
            const tpls = await stageTemplateService.getTemplate() || [];
            await Promise.all(stages.map(s => stageTemplateService.removeStage(projectId, s.id)));
            await stageTemplateService.attachStages(projectId, tpls.map((t, i) => ({ stageTemplateId: t.id, isCustom: false, cost: 0, isCompleted: i === 0 })));
            autoTicked.current = true;
            await loadStages(); cancelInsert(); toast && toast('Default stages restored.', 'success');
        } catch { await loadStages(); toast && toast('Failed to restore defaults', 'error'); } finally { setSaving(false); }
    };
    if (loading) return null;
    return (<div className={styles.stageList}>
        {canEdit && (<div className={styles.stageListTop}>
            <button type="button" className={styles.ghostBtn} onClick={handleRestoreDefaults} disabled={saving}><FiRefreshCw aria-hidden="true" /> RESTORE DEFAULTS</button>
        </div>)}
        {stages.length === 0 && <div className={styles.emptyState}><FiCheckCircle className={styles.emptyIcon} aria-hidden="true" /><span>NO STAGES ATTACHED YET</span></div>}
        {stages.map((stage, i) => {
            const isFirst = i === 0;
            const isLast = i === stages.length - 1;
            return (<React.Fragment key={stage.id}>
                <label className={`${styles.stageItem} ${stage.isCompleted ? styles.stageItemChecked : ''}`}>
                    <input type="checkbox" className={styles.stageCheckbox} checked={!!stage.isCompleted} disabled={!canEdit}
                        onChange={() => handleToggleComplete(stage)} aria-label={`Mark ${stage.stageName} complete`} />
                    <span className={styles.stageItemName}>{stage.stageName}</span>
                    <span className={styles.stageActions}>
                        {canEdit && !isLast && (<button type="button" className={styles.plusBtn} title="Insert a stage below this one"
                            aria-label={`Insert stage below ${stage.stageName}`}
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(stage); }}><FiPlus size={12} /></button>)}
                        {canRemove && !isFirst && !isLast && (<button type="button" className={styles.iconBtnDanger} title="Remove stage"
                            aria-label={`Remove ${stage.stageName}`}
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleRemove(stage.id); }}><FiTrash2 size={12} /></button>)}
                    </span>
                </label>
                {addingStage && insertAfterId === stage.id && (<div className={styles.insertRow}>
                    <span className={styles.insertCtx}>INSERT UNDER: {insertAfterName}</span>
                    <input type="text" className={styles.insertInput} value={newStageName} autoFocus
                        onChange={e => setNewStageName(e.target.value)} placeholder="New stage name"
                        aria-label="New stage name"
                        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddStage(); } if (e.key === 'Escape') cancelInsert(); }} />
                    <HardwareButton type="button" onClick={handleAddStage} loading={saving} icon={FiCheckCircle}>ADD</HardwareButton>
                    <button type="button" className={styles.ghostBtn} onClick={cancelInsert} aria-label="Cancel insert"><FiX aria-hidden="true" /></button>
                </div>)}
            </React.Fragment>);
        })}
    </div>);
};"""

# ---------- 1. swap the stage panel component ----------
lines = read(JSX).split("\n")
start = find(lines, 'const StageChecklistPanel = ({ projectId, canEdit, canRemove, toast }) => {')
if start < 0:
    print("MISSING StageChecklistPanel start marker")
else:
    folder_idx = find(lines, 'const FolderPage = () => {')
    end = folder_idx - 1
    while end > start and lines[end].strip() == '':
        end -= 1
    if lines[end].strip() != '};':
        print("MISSING component end marker")
    else:
        lines[start:end + 1] = NEW_COMPONENT.split("\n")
        print("OK stage panel swapped (fix117 version)")

# ---------- 2. imports: FiRefreshCw + FiArrowUp ----------
i = find(lines, 'FiPlus, FiFolderPlus')
if i >= 0 and 'FiRefreshCw' not in lines[i]:
    lines[i] = lines[i].replace('FiPlus, FiFolderPlus', 'FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp', 1)
    print("OK imports FiRefreshCw FiArrowUp")
else:
    print("SKIP imports already present or marker missing")

# ---------- 3. scroll-top state + effect (appears when header/edit scrolls away) ----------
if 'showTopBtn' not in "\n".join(lines):
    i = find(lines, 'const lastActiveRef = useRef(Date.now());')
    if i >= 0:
        block = [
        "const [showTopBtn, setShowTopBtn] = useState(false);",
        "useEffect(() => {",
        "    const onScroll = () => { const h = document.querySelector('[class*=\"terminalHeader\"]'); setShowTopBtn(!!h && h.getBoundingClientRect().bottom < 0); };",
        "    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();",
        "    return () => window.removeEventListener('scroll', onScroll);",
        "}, []);"]
        lines[i + 1:i + 1] = block
        print("OK scroll-top state + effect")
    else:
        print("MISSING lastActiveRef anchor")
else:
    print("SKIP scroll-top already present")

# ---------- 4. replace BackToTopButton with header-aware scroll-top button ----------
i = find(lines, '<BackToTopButton />')
if i >= 0:
    lines[i] = "{showTopBtn && (<button type=\"button\" className={styles.scrollTopBtn} onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label=\"Back to top to edit or save\"><FiArrowUp aria-hidden=\"true\" /></button>)}"
    print("OK scroll-top button replaces BackToTopButton")
else:
    print("SKIP BackToTopButton line not found")

write(JSX, "\n".join(lines))

# ---------- 5. backend: guarantee the reorder endpoint (root cause of Failed to insert stage) ----------
cs = read(CTRL)
if 'stages/reorder' not in cs:
    cl = cs.split("\n")
    i = find(cl, 'stageTemplateService.attachStagesToProject(projectId, requests));')
    if i >= 0:
        j = i + 1
        while j < len(cl) and cl[j].strip() != '}':
            j += 1
        block = [
        '@PutMapping("/land/projects/{projectId}/stages/reorder")',
        'public ResponseEntity<List<ProjectStage>> reorderProjectStages(',
        '@PathVariable UUID projectId, @RequestBody List<String> orderedIds) {',
        'List<UUID> ids = orderedIds.stream().map(UUID::fromString).toList();',
        'return ResponseEntity.ok(stageTemplateService.reorderProjectStages(projectId, ids));',
        '}']
        cl[j + 1:j + 1] = block
        write(CTRL, "\n".join(cl))
        print("OK controller reorder endpoint inserted")
    else:
        print("MISSING controller attach anchor")
else:
    print("SKIP controller reorder already present")

ss = read(SVC)
if 'reorderProjectStages' not in ss:
    sl = ss.split("\n")
    i = find(sl, 'return created;')
    if i >= 0:
        j = i + 1
        while j < len(sl) and sl[j].strip() != '}':
            j += 1
        block = [
        '@Transactional',
        '@PreAuthorize("hasAnyRole(\'ROLE_MANAGER\', \'ROLE_ADMIN\', \'ROLE_DIRECTOR\')")',
        'public List<ProjectStage> reorderProjectStages(UUID projectId, List<UUID> orderedIds) {',
        'List<ProjectStage> stages = projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);',
        'if (orderedIds == null || orderedIds.isEmpty()) return stages;',
        'java.util.Map<UUID, ProjectStage> byId = new java.util.LinkedHashMap<>();',
        'for (ProjectStage st : stages) byId.put(st.getId(), st);',
        'List<ProjectStage> toSave = new java.util.ArrayList<>();',
        'int order = 0;',
        'for (UUID id : orderedIds) {',
        'ProjectStage st = byId.remove(id);',
        'if (st != null) { st.setDisplayOrder(order++); toSave.add(st); }',
        '}',
        'for (ProjectStage st : byId.values()) { st.setDisplayOrder(order++); toSave.add(st); }',
        'projectStageRepository.saveAll(toSave);',
        'auditService.logAction("PROJECT_STAGES_REORDERED",',
        '"Operator [" + getCurrentOperator() + "] reordered stages on project: " + projectId);',
        'return projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(projectId);',
        '}']
        sl[j + 1:j + 1] = block
        write(SVC, "\n".join(sl))
        print("OK service reorder method inserted")
    else:
        print("MISSING service return created anchor")
else:
    print("SKIP service reorder already present")

# ---------- 6. CSS: Intake tones, heading glow, scroll-top ----------
s = read(CSS)
if 'fix117' not in s:
    s += """
/* fix117: Intake/Recovery button tones + panel heading glow + header-aware scroll-top */
.drawerTitle { text-shadow: 0 0 12px rgba(238,140,58,0.45); }
.sectionTitle { text-shadow: 0 0 10px rgba(238,140,58,0.4); }
.plusBtn { background: transparent; border: 1px solid var(--orange-border, rgba(238,140,58,0.28)); color: var(--fs-orange, #EE8C3A); width: clamp(24px,2.8vw,30px); height: clamp(24px,2.8vw,30px); border-radius: var(--radius-sm,6px); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: background .2s, color .2s, border-color .2s; font-size: 12px; flex-shrink: 0; }
.plusBtn:hover { background: var(--fs-orange, #EE8C3A); color: #1a2e30; border-color: var(--fs-orange, #EE8C3A); }
.iconBtnDanger { background: transparent; border: none; color: var(--fs-red, #ef4444); width: clamp(24px,2.8vw,30px); height: clamp(24px,2.8vw,30px); border-radius: var(--radius-sm,6px); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: background .2s; font-size: 13px; flex-shrink: 0; }
.iconBtnDanger:hover { background: rgba(239,68,68,0.14); }
.stageListTop { display: flex; justify-content: flex-end; margin-bottom: 2px; }
.scrollTopBtn { position: fixed; right: clamp(14px,2vw,24px); bottom: clamp(14px,2vw,24px); z-index: 400; width: clamp(38px,4.5vw,46px); height: clamp(38px,4.5vw,46px); border-radius: 50%; background: #EE8C3A; color: #1a2e30; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 3px 14px rgba(238,140,58,0.45); transition: background .2s, transform .2s; }
.scrollTopBtn:hover { background: #f0a050; transform: translateY(-2px); }
.scrollTopBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 2px; }
"""
    write(CSS, s)
    print("OK fix117 css")
else:
    print("SKIP fix117 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix117: backend reorder endpoint (insert root cause), Intake button tones, heading glow, header-aware scroll-top, stage first/last rules + restore defaults"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")