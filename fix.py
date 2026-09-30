#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix163: REVERT A SAVED TITLE BACK TO STAGES (step 2 of the Folder page backbone plan).
#
#  1. New director/admin-only action REVERT TO STAGES on the Folder page (needs a reason, audited as TITLE_REVERTED).
#     Backend: LandService.revertTitle + PATCH /land/projects/{id}/revert-title.
#  2. It deletes the saved title (frees the unique plot number), un-ticks the final stage, puts the project back to ACTIVE,
#     and keeps the old title values (plot, title ID, tenure, block, date) in the audit line.
#  3. It is REFUSED (on the server, not just hidden in the page) when: the title was handed over (undo that first),
#     the project is Receivable or Legacy, or the project was created as New Title / Legacy Title (no stages to go back to).
#  4. The stage checklist no longer disappears once a title exists. It stays visible, read-only, with a fresh reload
#     when the title appears or goes. Titled projects with no stages show no empty panel.
#  5. LLM_CONTEXT_GUIDE.md Section 15 records the 6-step plan status (1 done, 2 done, 3 partly, 4-6 to do).
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix163"
COMMIT_MSG = "fix163: revert a saved title back to stages (director/admin, reason, audited) + stage checklist stays visible after titling"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
LAND_SVC = os.path.join(SRC, "services", "landService.js")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp", "modules", "land")
LAND_SERVICE = os.path.join(JAVA, "service", "LandService.java")
LAND_CTRL = os.path.join(JAVA, "controller", "LandController.java")
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
# ============================= EDIT PART 1 END =============================


# ================== DO NOT EDIT: helpers (copy exactly) ====================
MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# sub = exact find/replace of the FIRST match. Prints OK / SKIP / MISSING.
def sub(text, old, new, desc):
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


# newfile = create (or replace) a whole file. SKIP if it already holds `marker`.
def newfile(path, text, label, marker):
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)



# ============================ EDIT PART 2 START ============================
LOAD_FILES = (FOLDER_JSX, LAND_SVC, LAND_SERVICE, LAND_CTRL, GUIDE)
for _p in LOAD_FILES:
    load(_p)


# =========================== PART A -- BACKEND: revert a saved title back to stages ===========================

# A1. LandService needs the title repository so the title row can really be deleted (frees the unique plot number).
patch(LAND_SERVICE,
"""    private final ProjectStageRepository projectStageRepository;
""",
"""    private final ProjectStageRepository projectStageRepository;
    private final LandTitleRepository landTitleRepository;
""",
"LandService: inject LandTitleRepository")

# A2. The revert itself: director/admin only, reason, refuses unsafe cases, audits the old title values.
patch(LAND_SERVICE,
"""            "Operator [" + getCurrentOperator() + "] undid the hand-over of " + plotLabel(project) + ". Reason: " + why);
    }
""",
"""            "Operator [" + getCurrentOperator() + "] undid the hand-over of " + plotLabel(project) + ". Reason: " + why);
    }

    // fix163: REVERT A SAVED TITLE BACK TO STAGES.
    // Director/admin only. Needs a reason. Refused when the title was handed over, when the project is
    // Receivable or Legacy, and when the project was created as New Title / Legacy Title (it has no stages).
    // The title row is deleted (this frees the plot number); the old values are kept in the audit line.
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void revertTitle(UUID id, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the title is being reverted (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(id)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        LandTitle title = project.getLandTitle();
        if (title == null) {
            throw new BusinessException("REVERT_DENIED: This project has no saved title to revert.");
        }
        if (title.isReleased()) {
            throw new BusinessException("REVERT_DENIED: The title was handed over. Undo the hand-over first.");
        }
        if (project.isReceivable() || project.isLegacy()) {
            throw new BusinessException("REVERT_DENIED: A Receivable or Legacy project cannot be reverted to stages.");
        }
        java.util.List<com.gesolutions.erp.modules.land.model.ProjectStage> stages =
                projectStageRepository.findByProjectIdOrderByDisplayOrderAsc(id);
        if (stages.isEmpty()) {
            throw new BusinessException("REVERT_DENIED: This project was created with its title (New Title / Legacy Title), so it has no stages to go back to.");
        }
        String oldValues = "plot " + title.getPlotNumber() + ", title ID " + title.getTitleId()
                + ", tenure " + title.getTenure() + ", block " + title.getBlockRoad()
                + ", title date " + title.getTitleIssueDate();
        project.setLandTitle(null);
        project.setStatus("ACTIVE");
        projectRepository.saveAndFlush(project);
        landTitleRepository.delete(title);
        com.gesolutions.erp.modules.land.model.ProjectStage last = stages.get(stages.size() - 1);
        if (last.isCompleted()) {
            last.setCompleted(false);
            last.setCompletedAt(null);
            projectStageRepository.save(last);
        }
        auditService.logAction("TITLE_REVERTED",
            "Operator [" + getCurrentOperator() + "] reverted the saved title of project " + project.getProjectIndex()
            + " back to stages. Old title: " + oldValues + ". Reason: " + why);
    }
""",
"LandService: revertTitle (director/admin, reason, audited, deletes the title row, un-ticks last stage)")

# A3. Endpoint
patch(LAND_CTRL,
"""        landService.undoRelease(id, reason);
        return ResponseEntity.ok().build();
    }
""",
"""        landService.undoRelease(id, reason);
        return ResponseEntity.ok().build();
    }

    // fix163: revert a saved title back to the stage checklist
    @PatchMapping("/projects/{id}/revert-title")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> revertTitle(@PathVariable UUID id, @RequestParam String reason) {
        landService.revertTitle(id, reason);
        return ResponseEntity.ok().build();
    }
""",
"LandController: PATCH /projects/{id}/revert-title")

# =========================== PART B -- FRONTEND ===========================

# B1. service call
patch(LAND_SVC,
"""    undoRelease: async (projectId, reason) => {
        await api.patch(`/land/projects/${projectId}/undo-release`, null, { params: { reason } });
    },
""",
"""    undoRelease: async (projectId, reason) => {
        await api.patch(`/land/projects/${projectId}/undo-release`, null, { params: { reason } });
    },

    // fix163: revert a saved title back to stages
    revertTitle: async (projectId, reason) => {
        await api.patch(`/land/projects/${projectId}/revert-title`, null, { params: { reason } });
    },
""",
"landService.js: revertTitle")

# B2. the stage panel tells the page how many stages the project has (so titled New Title projects show no empty panel)
patch(FOLDER_JSX,
"({ projectId, canEdit, canRemove, toast, confirm, onLastStageToggle }, ref) => {",
"({ projectId, canEdit, canRemove, toast, confirm, onLastStageToggle, onLoaded }, ref) => {",
"Folder: stage panel takes onLoaded")
patch(FOLDER_JSX,
"const loadStages = useCallback(async () => { try { setStages(await stageTemplateService.getProjectStages(projectId) || []); } catch {} finally { setLoading(false); } }, [projectId]);",
"const loadStages = useCallback(async () => { try { const list = await stageTemplateService.getProjectStages(projectId) || []; setStages(list); if (onLoaded) onLoaded(list.length); } catch {} finally { setLoading(false); } }, [projectId, onLoaded]);",
"Folder: stage panel reports its stage count")

# B3. page state
patch(FOLDER_JSX,
"const [payAmount, setPayAmount] = useState(''); const [payNotes, setPayNotes] = useState('');",
"const [stageCount, setStageCount] = useState(0);\n    const [payAmount, setPayAmount] = useState(''); const [payNotes, setPayNotes] = useState('');",
"Folder: stageCount state")

# B4. the stage list stays visible (read-only) after a title exists; hidden only if the project has no stages
patch(FOLDER_JSX,
"""{!project.landTitle && (
<section className={styles.hwPanel} aria-label="Stage Checklist\"""",
"""{(
<section className={styles.hwPanel} aria-label="Stage Checklist\"""",
"Folder: stage panel no longer disappears once a title exists")
patch(FOLDER_JSX,
"style={(activeTab !== 'OVERVIEW' || buffer.convertToTitle) ? { display: 'none' } : {}}>",
"style={(activeTab !== 'OVERVIEW' || buffer.convertToTitle || (project.landTitle && stageCount < 1)) ? { display: 'none' } : {}}>",
"Folder: hide the stage panel only for titled projects that have no stages")
patch(FOLDER_JSX,
"<StageChecklistPanel ref={stageChecklistRef} projectId={id} canEdit={canEdit && isEditing} canRemove={isDirector && isEditing} toast={toast} confirm={confirm}",
"<StageChecklistPanel key={project.landTitle ? 'titled' : 'folder'} ref={stageChecklistRef} projectId={id} canEdit={canEdit && isEditing && !project.landTitle} canRemove={isDirector && isEditing && !project.landTitle} toast={toast} confirm={confirm} onLoaded={setStageCount}",
"Folder: stage panel read-only when titled, reloads when the title appears or goes")

# B5. REVERT TO STAGES button (director/admin), next to the hand-over buttons
patch(FOLDER_JSX,
"{canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}",
"""{canMoney && project.landTitle && !project.landTitle.isReleased && !project.isLegacy && !isReceivable && stageCount > 0 && (
                            <button type="button" className={styles.ghostBtn} title="Take the saved title off and go back to the stage checklist (reason required)."
                                onClick={() => openReasonModal({ kind: 'REVERT_TITLE', title: 'REVERT TO STAGES', confirmLabel: 'REVERT TO STAGES',
                                    info: 'This removes the saved title (plot ' + (project.landTitle.plotNumber || '---') + ') and un-ticks the final stage, so the project goes back to the stage checklist. The old title values stay in the audit log. Use it only if the title was entered by mistake. To fix a typo in the title, use EDIT instead.' })}><FiRefreshCw aria-hidden="true" /> REVERT TO STAGES</button>)}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}""",
"Folder: REVERT TO STAGES button")

# B6. the reason popup runs it
patch(FOLDER_JSX,
"else if (m.kind === 'UNDO_RELEASE') { await landService.undoRelease(id, why); toast('Hand-over undone.', 'warn'); }",
"else if (m.kind === 'UNDO_RELEASE') { await landService.undoRelease(id, why); toast('Hand-over undone.', 'warn'); }\n            else if (m.kind === 'REVERT_TITLE') { await landService.revertTitle(id, why); setStageCount(0); toast('Title reverted. The project is back to stages.', 'warn'); }",
"Folder: reason popup runs REVERT_TITLE")

# =========================== PART C -- GUIDE ===========================
patch(GUIDE,
"- DIRECTOR'S DASHBOARD -- David is still working on it and its code will change. Section 8.12 is only the plan.",
"""- DIRECTOR'S DASHBOARD -- David is still working on it and its code will change. Section 8.12 is only the plan.
- FOLDER PAGE BACKBONE PLAN (David's 6 steps): 1 money loopholes = DONE (fix162). 2 revert a saved title to stages = DONE (fix163: director/admin, reason, audited; `LandService.revertTitle`, `PATCH /land/projects/{id}/revert-title`; refused after hand-over, on Receivable/Legacy projects and on New Title/Legacy Title projects that have no stages; the title row is deleted and its old values go into the TITLE_REVERTED audit line; the stage checklist now stays visible read-only after titling). 3 fee negotiation = PARTLY (REDUCE FEES done; still to do: changeable 50,000 default, a reason on every rate change). 4 real call logs = TO DO (must reuse the Recovery notes / 2-14 lock; add promise date, promised amount, next follow-up date). 5 RELEASE + PROBLEM improvements (show reason and who flagged it) = TO DO. 6 per-plot history tab = TO DO.""",
"Guide: Section 15 backbone plan status")

# ============================= EDIT PART 2 END =============================


# ================= DO NOT EDIT: gates, rollback, git (copy exactly) ========
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since the last fix).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True


def working_tree_dirty():
    r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return bool((r.stdout or "").strip())


# active = this script wrote something, OR files were already changed by hand (commit-only mode)
active = changed or working_tree_dirty()
if not changed and active:
    print("note: commit-only mode -- no patches defined, committing the changes already in the working tree")
if not active:
    print("note: nothing changed and the working tree is clean -- nothing to do")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file this script touched was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if active and RUN_GATES:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate ----
if active and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif active and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif active:
    print("note: RUN_GATES is False (docs-only fix) -- compile and build skipped")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

if not active:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", COMMIT_MSG)
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip())
print("")
print("DONE: " + FIX_NO + " applied.")