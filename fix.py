# fix.py -- fix119: corrected frontend diagnostics patches + backend reorder audit (field names, dupes, compile-safety)
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules" / "land"
JSX = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
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
def replace_line(lines, needle, new, label):
    i = find(lines, needle)
    if i < 0: print("SKIP", label); return lines
    lines[i] = new; print("OK", label); return lines
def sub_in_line(lines, needle, old, new, label):
    i = find(lines, needle)
    if i < 0 or old not in lines[i]: print("SKIP", label); return lines
    lines[i] = lines[i].replace(old, new, 1); print("OK", label); return lines
def method_region(text, sig):
    i = text.find(sig)
    if i < 0: return None
    k = text.find('{', i)
    if k < 0: return None
    depth = 0
    for n in range(k, len(text)):
        if text[n] == '{': depth += 1
        elif text[n] == '}':
            depth -= 1
            if depth == 0: return text[i:n + 1]
    return None
def insert_before_last_brace(path, marker, block, label):
    s = read(path)
    if marker in s:
        print("SKIP", label); return
    lines = s.split("\n")
    idx = len(lines) - 1
    while idx >= 0 and lines[idx].strip() != '}':
        idx -= 1
    if idx < 0:
        print("MISSING class close for", label); return
    lines[idx:idx] = block
    write(path, "\n".join(lines))
    print("OK", label)

# ---------- 1. frontend: retry + HTTP-status diagnostics (crash-free this time) ----------
L = read(JSX).split("\n")
L = replace_line(L, 'reorderProjectStages(projectId, ordered);',
    "            try { await stageTemplateService.reorderProjectStages(projectId, ordered); } catch { await stageTemplateService.reorderProjectStages(projectId, ordered); }",
    "reorder retry once")
L = replace_line(L, "Stage saved but position update failed",
    "} catch (err) { await loadStages(); cancelInsert(); toast && toast('POSITION UPDATE FAILED (HTTP ' + (err.response?.status || 'network') + ') - stage added at the end.', 'error', 9000); } finally { setSaving(false); }",
    "insert catch shows HTTP status")
L = sub_in_line(L, 'toggleStageCompletion(projectId, stages[0].id, true)', '.catch(() => {});',
    ".catch(err => toast && toast('AUTO-TICK FAILED (HTTP ' + (err.response?.status || 'network') + ')', 'error', 6000));",
    "auto-tick catch shows HTTP status")
OLD_CATCH = "catch { toast && toast('Failed to update stage', 'error'); }"
NEW_CATCH = "catch (err) { toast && toast('Failed to update stage (HTTP ' + (err.response?.status || 'network') + ')', 'error'); }"
L = sub_in_line(L, OLD_CATCH, OLD_CATCH, NEW_CATCH, "manual tick catch shows HTTP status")
write(JSX, "\n".join(L))

# ---------- 2. backend audit: presence, dupes, field-name compile-safety ----------
cs = read(CTRL)
ss = read(SVC)
print("AUDIT controller reorder mappings:", cs.count('@PutMapping("/land/projects/{projectId}/stages/reorder")'))
print("AUDIT service reorder methods:", ss.count('public List<ProjectStage> reorderProjectStages'))

m_svc = re.search(r'private final ProjectStageRepository\s+(\w+)\s*;', ss)
svc_field = m_svc.group(1) if m_svc else None
print("AUDIT service ProjectStageRepository field name:", svc_field)
if svc_field and svc_field != 'projectStageRepository':
    region = method_region(ss, 'public List<ProjectStage> reorderProjectStages')
    if region:
        fixed = region.replace('projectStageRepository', svc_field)
        ss = ss.replace(region, fixed, 1)
        write(SVC, ss)
        print("OK service reorder method field name corrected to", svc_field)
    else:
        print("MISSING reorder method region in service")
else:
    print("SKIP service field name already correct or not detected")

m_ctrl = re.search(r'private final StageTemplateService\s+(\w+)\s*;', cs)
ctrl_field = m_ctrl.group(1) if m_ctrl else None
print("AUDIT controller StageTemplateService field name:", ctrl_field)
if ctrl_field and ctrl_field != 'stageTemplateService':
    region = method_region(cs, 'public ResponseEntity<List<ProjectStage>> reorderProjectStages')
    if region:
        fixed = region.replace('stageTemplateService', ctrl_field)
        cs = cs.replace(region, fixed, 1)
        write(CTRL, cs)
        print("OK controller reorder method field name corrected to", ctrl_field)
    else:
        print("MISSING reorder method region in controller")
else:
    print("SKIP controller field name already correct or not detected")

# ---------- 3. safety net: insert endpoint if somehow absent ----------
insert_before_last_brace(CTRL, 'stages/reorder', [
'@PutMapping("/land/projects/{projectId}/stages/reorder")',
'public ResponseEntity<List<ProjectStage>> reorderProjectStages(',
'@PathVariable UUID projectId, @RequestBody List<String> orderedIds) {',
'List<UUID> ids = orderedIds.stream().map(UUID::fromString).toList();',
'return ResponseEntity.ok(stageTemplateService.reorderProjectStages(projectId, ids));',
'}'], "controller reorder endpoint (end of class)")
insert_before_last_brace(SVC, 'reorderProjectStages', [
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
'}'], "service reorder method (end of class)")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix119: crash-free frontend diagnostics + backend reorder audit (field names, dupes, compile-safety)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")