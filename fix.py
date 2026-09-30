#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix164: FEE NEGOTIATION SAFETY (step 3 of the Folder page backbone plan). Apply AFTER fix163.
#
#  1. SAVE RATE and PAUSE FEES on the Folder page now open the reason popup. A rate change or a new pause date needs a
#     reason of 5+ characters; the audit line shows OLD -> NEW and the reason. RESUME FEES needs no reason.
#  2. They send only what changed, so saving a rate can no longer silently clear a pause (and vice versa).
#  3. A negative monthly rate is refused on the server.
#  4. The older endpoints storage-pause / storage-rate / storage-fees on LandController (no page uses them, but the server
#     accepted them with no reason -- storage-fees could set the accumulated fees to any figure) now require `reason`.
#     The rate audit also shows the real previous rate (it used to print the new one).
#  5. LLM_CONTEXT_GUIDE.md Section 15 records the step 3 status.
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
# Runs the backend compile and `npm run build` before committing when available, and rolls back if either goes red.

import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix164"
COMMIT_MSG = "fix164: every storage-rate / pause / fee adjustment needs a reason (page + server), old -> new audit"
RUN_GATES = True  # compile + build must be green before commit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp", "modules", "land")
LAND_SERVICE = os.path.join(JAVA, "service", "LandService.java")
LAND_CTRL = os.path.join(JAVA, "controller", "LandController.java")
PORTAL_CTRL = os.path.join(JAVA, "controller", "FolderPortalController.java")
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
LOAD_FILES = (FOLDER_JSX, LAND_SERVICE, LAND_CTRL, PORTAL_CTRL, GUIDE)
for _p in LOAD_FILES:
    load(_p)


# =========================== PART A -- BACKEND: every fee change needs a reason ===========================

# A1. Folder settings endpoint (the one the page uses): rate change or new pause date needs a reason; negative rate refused;
#     audit shows OLD -> NEW and the reason.
patch(PORTAL_CTRL,
"""        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        if (body.containsKey("rate")) {
            p.setStorageFeeOverride(body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate")));
        }
        if (body.containsKey("deadline")) {
            p.setNegotiationDeadline(body.get("deadline") == null || body.get("deadline").isBlank() ? null : LocalDateTime.parse(body.get("deadline")));
        }
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex()
                + " (monthly rate: " + (p.getStorageFeeOverride() != null ? "UGX " + p.getStorageFeeOverride().toPlainString() : "default")
                + ", fees paused until: " + (p.getNegotiationDeadline() != null ? p.getNegotiationDeadline().toString() : "not paused") + ").");""",
"""        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        // fix164: a rate change or a NEW pause date needs a written reason and is audited as OLD -> NEW.
        // Clearing a pause (RESUME FEES) needs no reason.
        BigDecimal oldRate = p.getStorageFeeOverride();
        LocalDateTime oldDeadline = p.getNegotiationDeadline();
        BigDecimal newRate = oldRate;
        LocalDateTime newDeadline = oldDeadline;
        if (body.containsKey("rate")) {
            newRate = body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate"));
            if (newRate != null && newRate.signum() < 0) {
                throw new BusinessException("RATE_INVALID: The monthly storage rate cannot be negative.");
            }
        }
        if (body.containsKey("deadline")) {
            newDeadline = body.get("deadline") == null || body.get("deadline").isBlank() ? null : LocalDateTime.parse(body.get("deadline"));
        }
        boolean rateChanged = (oldRate == null) != (newRate == null)
                || (oldRate != null && newRate != null && oldRate.compareTo(newRate) != 0);
        boolean pauseSet = newDeadline != null && !newDeadline.equals(oldDeadline);
        String why = body.get("reason") == null ? "" : body.get("reason").trim();
        if ((rateChanged || pauseSet) && why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the rate or pause is changing (at least 5 characters).");
        }
        p.setStorageFeeOverride(newRate);
        p.setNegotiationDeadline(newDeadline);
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex()
                + " (monthly rate: " + (oldRate != null ? "UGX " + oldRate.toPlainString() : "default")
                + " -> " + (newRate != null ? "UGX " + newRate.toPlainString() : "default")
                + ", fees paused until: " + (oldDeadline != null ? oldDeadline.toString() : "not paused")
                + " -> " + (newDeadline != null ? newDeadline.toString() : "not paused") + ")"
                + (why.isEmpty() ? "" : ". Reason: " + why));""",
"FolderPortalController.settings: reason required for a rate change or new pause; old -> new audit")

# A2. The three older fee endpoints (no page uses them, but the server allowed them with no reason -- e.g. set the
#     accumulated fees to any figure). They now need a reason too.
patch(LAND_CTRL,
"""    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,
                                                   @RequestParam boolean paused) {
        landService.setStoragePaused(id, paused);""",
"""    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,
                                                   @RequestParam boolean paused,
                                                   @RequestParam String reason) {
        landService.setStoragePaused(id, paused, reason);""",
"LandController: storage-pause needs a reason")
patch(LAND_CTRL,
"""    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal rate) {
        landService.setStorageFeeOverride(id, rate);""",
"""    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal rate,
                                               @RequestParam String reason) {
        landService.setStorageFeeOverride(id, rate, reason);""",
"LandController: storage-rate needs a reason")
patch(LAND_CTRL,
"""    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount) {
        landService.setAccumulatedFees(id, amount);""",
"""    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam String reason) {
        landService.setAccumulatedFees(id, amount, reason);""",
"LandController: storage-fees needs a reason")

patch(LAND_SERVICE,
"""    public void setStoragePaused(UUID projectId, boolean paused) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));""",
"""    public void setStoragePaused(UUID projectId, boolean paused, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the storage fees are being paused or resumed (at least 5 characters).");
        }
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));""",
"LandService.setStoragePaused: reason required")
patch(LAND_SERVICE,
"""action.toLowerCase() + " monthly storage fees for plot: \"""",
"""action.toLowerCase() + " monthly storage fees (reason: " + why + ") for plot: \"""",
"LandService.setStoragePaused: reason in audit")

patch(LAND_SERVICE,
"""    public void setStorageFeeOverride(UUID projectId, java.math.BigDecimal rate) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        project.setStorageFeeOverride(rate);
        projectRepository.save(project);
        auditService.logAction("STORAGE_RATE_CHANGED",
            "Operator [" + getCurrentOperator() + "] changed monthly storage fee to UGX " + rate
            + " for plot: " + plotLabel(project)
            + " (previously UGX " + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : "50000 (default)") + ")");""",
"""    public void setStorageFeeOverride(UUID projectId, java.math.BigDecimal rate, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the monthly storage rate is changing (at least 5 characters).");
        }
        if (rate != null && rate.signum() < 0) {
            throw new BusinessException("RATE_INVALID: The monthly storage rate cannot be negative.");
        }
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));
        java.math.BigDecimal previous = project.getStorageFeeOverride();
        project.setStorageFeeOverride(rate);
        projectRepository.save(project);
        auditService.logAction("STORAGE_RATE_CHANGED",
            "Operator [" + getCurrentOperator() + "] changed monthly storage fee to UGX " + rate
            + " for plot: " + plotLabel(project)
            + " (previously UGX " + (previous != null ? previous : "50000 (default)") + "). Reason: " + why);""",
"LandService.setStorageFeeOverride: reason required, audit shows the real previous rate")

patch(LAND_SERVICE,
"""    public void setAccumulatedFees(UUID projectId, java.math.BigDecimal amount) {
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));""",
"""    public void setAccumulatedFees(UUID projectId, java.math.BigDecimal amount, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) {
            throw new BusinessException("REASON_REQUIRED: Write why the accumulated fees are being adjusted (at least 5 characters).");
        }
        if (amount == null || amount.signum() < 0) {
            throw new BusinessException("FEES_INVALID: The accumulated fees cannot be negative.");
        }
        LandProject project = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND"));""",
"LandService.setAccumulatedFees: reason required, no negative figure")
patch(LAND_SERVICE,
"""+ " to UGX " + amount + " for plot: " + plotLabel(project));""",
"""+ " to UGX " + amount + " for plot: " + plotLabel(project) + ". Reason: " + why);""",
"LandService.setAccumulatedFees: reason in audit")

# =========================== PART B -- FRONTEND: SAVE RATE and PAUSE FEES ask for a reason ===========================
patch(FOLDER_JSX,
"""<HardwareButton type="button" icon={FiSave} loading={recvBusy} onClick={() => askReceivable('SETTINGS')}>SAVE RATE</HardwareButton>""",
"""<HardwareButton type="button" icon={FiSave} loading={recvBusy} onClick={() => openReasonModal({ kind: 'RATE', title: 'CHANGE MONTHLY STORAGE RATE', confirmLabel: 'SAVE RATE',
                                            info: 'New monthly rate: ' + (rateFee ? 'UGX ' + fmt(Number(rateFee)) : 'the default (UGX 50,000)') + '. It applies to future months only; fees already added stay as they are. Write why it is changing (for example the agreed figure after negotiation).' })}>SAVE RATE</HardwareButton>""",
"Folder: SAVE RATE opens the reason popup")
patch(FOLDER_JSX,
"""<HardwareButton type="button" icon={FiCheckCircle} loading={recvBusy} onClick={() => askReceivable('SETTINGS')}>PAUSE FEES</HardwareButton>""",
"""<HardwareButton type="button" icon={FiCheckCircle} loading={recvBusy} onClick={() => { if (!rateDeadline) { toast('PICK THE DATE THE PAUSE ENDS FIRST', 'error'); return; } openReasonModal({ kind: 'PAUSE', title: 'PAUSE STORAGE FEES', confirmLabel: 'PAUSE FEES',
                                            info: 'No new storage fees will be added until ' + String(rateDeadline).slice(0, 10) + '. Write why (for example the client is negotiating).' }); }}>PAUSE FEES</HardwareButton>""",
"Folder: PAUSE FEES opens the reason popup")
patch(FOLDER_JSX,
"else if (m.kind === 'REDUCE') { await folderPortalService.reduceFees(id, m.amount, why); toast('Storage fees reduced.', 'success'); }",
"""else if (m.kind === 'REDUCE') { await folderPortalService.reduceFees(id, m.amount, why); toast('Storage fees reduced.', 'success'); }
            else if (m.kind === 'RATE') { await folderPortalService.settings(id, { rate: rateFee, reason: why }); toast('Monthly storage rate saved.', 'success'); }
            else if (m.kind === 'PAUSE') { await folderPortalService.settings(id, { deadline: rateDeadline, reason: why }); setFreezeOpen(false); toast('Storage fees paused.', 'info'); }""",
"Folder: reason popup runs RATE and PAUSE")

# =========================== PART C -- GUIDE ===========================
patch(GUIDE,
"3 fee negotiation = PARTLY (REDUCE FEES done; still to do: changeable 50,000 default, a reason on every rate change).",
"3 fee negotiation = DONE except an editable global default (fix164: REDUCE/WAIVE/rate change/pause all need a reason of 5+ characters and audit old -> new; the older `storage-pause`, `storage-rate` and `storage-fees` endpoints on LandController now also need `reason`; SAVE RATE and PAUSE FEES send only what changed, so saving a rate can no longer silently clear a pause). The 50,000 default is still a constant in ReceivableSchedulerService (a global editable default needs a settings table -- David to decide).",
"Guide: Section 15 step 3 status")

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