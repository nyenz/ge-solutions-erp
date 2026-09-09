# fix.py -- fix116: replace FolderPage StageChecklistPanel with an exact mirror of the Intake stages panel
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
JSX = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
CSS = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)

NEW_COMPONENT = """/* STAGE CHECKLIST - mirrors the Intake page stages panel (fix116).
   Rows = the project's attached stages, done stages pre-ticked.
   No money, no notes, no modal: tick to complete, plus to insert below,
   trash to remove. Nothing can be added after the last stage. */
const StageChecklistPanel = ({ projectId, canEdit, canRemove, toast }) => {
    const [stages, setStages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [insertAfterId, setInsertAfterId] = useState(null);
    const [insertAfterName, setInsertAfterName] = useState('');
    const [saving, setSaving] = useState(false);
    const loadStages = useCallback(async () => { try { setStages(await stageTemplateService.getProjectStages(projectId) || []); } catch {} finally { setLoading(false); } }, [projectId]);
    useEffect(() => { loadStages(); }, [loadStages]);
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
        } catch { toast && toast('Failed to insert stage', 'error'); } finally { setSaving(false); }
    };
    const handleToggleComplete = async (stage) => { try { await stageTemplateService.toggleStageCompletion(projectId, stage.id, !stage.isCompleted); await loadStages(); } catch { toast && toast('Failed to update stage', 'error'); } };
    const handleRemove = async (stageId) => { try { await stageTemplateService.removeStage(projectId, stageId); await loadStages(); toast && toast('Stage removed.', 'warn'); } catch { toast && toast('Failed to remove stage', 'error'); } };
    if (loading) return null;
    return (<div className={styles.stageList}>
        {stages.length === 0 && <div className={styles.emptyState}><FiCheckCircle className={styles.emptyIcon} aria-hidden="true" /><span>NO STAGES ATTACHED YET</span></div>}
        {stages.map((stage, i) => {
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
                        {canRemove && (<button type="button" className={styles.iconBtnDanger} title="Remove stage"
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

lines = read(JSX).split("\n")
start = -1
for i, ln in enumerate(lines):
    if 'const StageChecklistPanel = ({ projectId, canEdit, canRemove, toast }) => {' in ln:
        start = i
        break
if start < 0:
    print("MISSING StageChecklistPanel start marker")
else:
    folder_idx = -1
    for i, ln in enumerate(lines):
        if ln.strip().startswith('const FolderPage = () => {'):
            folder_idx = i
            break
    if folder_idx < 0:
        print("MISSING FolderPage start marker")
    else:
        end = folder_idx - 1
        while end > start and lines[end].strip() == '':
            end -= 1
        if lines[end].strip() != '};':
            print("MISSING component end marker, found:", lines[end][:60])
        else:
            lines[start:end + 1] = NEW_COMPONENT.split("\n")
            write(JSX, "\n".join(lines))
            print("OK StageChecklistPanel replaced with Intake mirror")

s = read(CSS)
if 'fix116' not in s:
    s += """
/* fix116: Intake-mirrored stage checklist rows */
.stageList { display: flex; flex-direction: column; gap: 6px; }
.stageItem { display: flex; align-items: center; gap: 10px; padding: 9px 12px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 7px; cursor: pointer; transition: border-color 0.2s; }
.stageItem:hover { border-color: rgba(238,140,58,0.35); }
.stageItemChecked { background: rgba(238,140,58,0.06); border-color: rgba(238,140,58,0.3); }
.stageItemChecked .stageItemName { text-decoration: line-through; color: var(--fs-muted); }
.stageCheckbox { width: 15px; height: 15px; accent-color: #EE8C3A; cursor: pointer; flex-shrink: 0; }
.stageItemName { font-weight: 700; color: #fff; font-size: clamp(11px, 1.1vw, 13px); letter-spacing: 0.5px; flex: 1; min-width: 0; }
.stageActions { margin-left: auto; display: flex; gap: 8px; align-items: center; }
.insertRow { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px dashed rgba(238,140,58,0.45); border-radius: 7px; background: rgba(238,140,58,0.05); flex-wrap: wrap; }
.insertInput { flex: 1; min-width: 140px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.15); border-radius: 5px; color: #fff; padding: 7px 9px; font-family: 'DM Sans', sans-serif; font-size: 12px; }
.insertInput:focus { outline: none; border-color: #EE8C3A; }
"""
    write(CSS, s)
    print("OK fix116 css")
else:
    print("SKIP fix116 css already present")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix116: FolderPage stage checklist now mirrors the Intake stages panel (pre-ticked, inline insert, no money/no modal)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")