# fix.py -- fix115: stage checklist cleanup (no per-stage money, direct ticking, no edit popup, no add after last stage)
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
JSX = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding="utf-8", newline="\n") as f: f.write(s)
    print("WROTE", p.name)
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

L = read(JSX).split("\n")

# 1. panel is directly usable by Manager+ without entering edit mode
L = sub_in_line(L, 'StageChecklistPanel projectId={id}', 'canEdit={isEditing && canEdit}', 'canEdit={canEdit}', "tick stages without edit mode")

# 2. drop edit-row state (cost/notes/editingId)
L = replace_line(L, "const [editCost, setEditCost] = useState(''); const [editNotes, setEditNotes] = useState('');", "const [saving, setSaving] = useState(false);", "drop editCost/editNotes state")
L = replace_line(L, "const [customCost, setCustomCost] = useState(''); const [editingId, setEditingId] = useState(null);", "const [customCost, setCustomCost] = useState('');", "drop editingId state")
L = delete_line(L, 'const saveEdit = async (stageId)', "drop saveEdit function")

# 3. map with index so we can hide insert-below on the last row
L = sub_in_line(L, '{stages.map(stage => (<div key={stage.id}', 'stages.map(stage =>', 'stages.map((stage, sIdx) =>', "stage map index")

# 4. remove the cost / edit popup row entirely (money + redundancy gone)
i = find(L, 'styles.stageEditRow')
j = find(L, 'UGX {fmt(stage.cost)}', i if i >= 0 else 0)
if i >= 0 and j >= i:
    del L[i:j + 1]
    print("OK removed cost/edit popup row")
else:
    print("SKIP cost/edit popup row already gone")

# 5. actions block no longer depends on editingId
L = sub_in_line(L, '{canEdit && editingId !== stage.id && (<div style={{ display:', '{canEdit && editingId !== stage.id && (', '{canEdit && (', "actions block condition")

# 6. insert-below plus hidden on the last stage (nothing after Title Issuance)
L = replace_line(L, 'className={styles.plusBtn} title="Insert stage below"',
    '{sIdx < stages.length - 1 && <button type="button" className={styles.plusBtn} title="Insert stage below" aria-label={`Insert stage below ${stage.stageName}`} onClick={() => openAddModal(stage.id, stage.stageName)}><FiPlus /></button>}',
    "plus hidden on last row")

# 7. remove pencil edit button (redundant popup entry point)
L = delete_line(L, 'className={styles.iconBtn2} aria-label="Edit stage"', "drop pencil edit button")

# 8. remove the add-at-end button (no stages after the last stage)
L = delete_line(L, 'className={styles.addStageBtn}', "drop add-at-end button")

# 9. toast wording now always insert
L = sub_in_line(L, "toast && toast(insertAfterId ? 'Stage(s) inserted under '", "'Stage(s) added at end'", "'Stage(s) inserted'", "toast wording")

write(JSX, "\n".join(L))
print("OK FolderPage.jsx stage checklist cleaned")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix115: stage checklist - no per-stage money, direct ticking, no edit popup, no add after last stage"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")