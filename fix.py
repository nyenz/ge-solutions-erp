#!/usr/bin/env python3
# PATH: fix173.py
# GOLDEN SEED -- fix173: the default monthly storage fee (50,000) lives in ONE place.
#
# THE PROBLEM:
#   The default fee was written out by hand in the nightly fee job, the intake save, the Intake page and the Folder page
#   (plus several sentences on the Folder page and the glossary). Changing it in one place missed the others. On top of that,
#   the Intake page saved a copy of 50,000 as the project's OWN rate on every Legacy Title, so even a changed default would
#   never have reached those projects.
#
# WHAT CHANGES:
#   1. BACKEND: new constant LandProject.DEFAULT_MONTHLY_STORAGE_FEE. ReceivableSchedulerService (nightly job) and
#      LandService (intake save) use it.
#   2. BACKEND: new read-only GET /api/v1/land/storage-fee-default (same roles as next-index).
#   3. INTAKE + FOLDER pages: no hard-coded number any more. They read the default from that endpoint (landService.getStorageFeeDefault,
#      fetched once). Every sentence that quoted 50,000 now shows the value from the server. The glossary line no longer quotes it.
#   4. INTAKE: the Monthly Storage Fee box starts blank (the default shows as the placeholder and in the hint). A rate is sent
#      only when staff typed one that differs from the default. A project entered at the default stores NO rate, so it follows
#      the default from now on.
#   5. LLM_CONTEXT_GUIDE.md: records where the default lives.
#
# NOT in this fix: an editable default (needs a settings table), the seed data's own 50000 in ScenarioData (demo rows only),
# changing existing projects that already carry a stored 50,000 rate (those keep it as their own rate), and the other two
# findings of the review (Recovery list membership, set-aside fees) -- both wait for the owner's decision.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
# Names, and one variable per file this fix touches.
FIX_NO = "fix173"
COMMIT_MSG = "fix173: default monthly storage fee lives in one place (LandProject constant + /land/storage-fee-default); intake no longer saves a copy of it"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

F_LAND_PROJECT = os.path.join(JAVA, "modules", "land", "model", "LandProject.java")
F_SCHEDULER = os.path.join(JAVA, "modules", "land", "service", "ReceivableSchedulerService.java")
F_LAND_SERVICE = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
F_LAND_CONTROLLER = os.path.join(JAVA, "modules", "land", "controller", "LandController.java")
F_LAND_SERVICE_JS = os.path.join(SRC, "services", "landService.js")
F_INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
F_FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
F_GLOSSARY = os.path.join(SRC, "components", "common", "glossary.js")
F_GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
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
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (F_LAND_PROJECT, F_SCHEDULER, F_LAND_SERVICE, F_LAND_CONTROLLER, F_LAND_SERVICE_JS, F_INTAKE_JSX, F_FOLDER_JSX, F_GLOSSARY, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_LAND_PROJECT,
      "\n".join([
          "    /**",
          "     * STORAGE FEE OVERRIDE: Custom monthly rate (null = use system default 50,000).",
          "     */",
          "    @Column(name = \"storage_fee_override\", precision = 15, scale = 2)"
      ]),
      "\n".join([
          "    /**",
          "     * fix173: THE system default monthly storage fee. The only place the number lives. The nightly fee job, the intake",
          "     * save and (through GET /api/v1/land/storage-fee-default) the Intake and Folder pages all read this constant.",
          "     */",
          "    public static final BigDecimal DEFAULT_MONTHLY_STORAGE_FEE = new BigDecimal(\"50000\");",
          "",
          "    /**",
          "     * STORAGE FEE OVERRIDE: Custom monthly rate (null = follow DEFAULT_MONTHLY_STORAGE_FEE).",
          "     */",
          "    @Column(name = \"storage_fee_override\", precision = 15, scale = 2)"
      ]),
      "LandProject: one DEFAULT_MONTHLY_STORAGE_FEE constant")

patch(F_SCHEDULER,
      "\n".join([
          "    private static final BigDecimal DEFAULT_MONTHLY_FEE = new BigDecimal(\"50000\");"
      ]),
      "\n".join([
          "    private static final BigDecimal DEFAULT_MONTHLY_FEE = LandProject.DEFAULT_MONTHLY_STORAGE_FEE;   // fix173: one shared default"
      ]),
      "Nightly job: use the shared default fee")

patch(F_SCHEDULER,
      "\n".join([
          "    // Adds 50,000 per 30-day period since receivable start date"
      ]),
      "\n".join([
          "    // Adds the monthly storage fee (the project's own rate, else the shared default) per 30-day period since receivable start date"
      ]),
      "Nightly job: comment no longer states the number")

patch(F_LAND_SERVICE,
      "\n".join([
          "                ? request.getMonthlyStorageFee() : new BigDecimal(\"50000\");"
      ]),
      "\n".join([
          "                ? request.getMonthlyStorageFee() : LandProject.DEFAULT_MONTHLY_STORAGE_FEE;   // fix173: one shared default"
      ]),
      "Intake save: use the shared default fee")

patch(F_LAND_CONTROLLER,
      "\n".join([
          "    public ResponseEntity<String> previewNextIndex() {",
          "        return ResponseEntity.ok(landService.previewNextIndex());",
          "    }",
          ""
      ]),
      "\n".join([
          "    public ResponseEntity<String> previewNextIndex() {",
          "        return ResponseEntity.ok(landService.previewNextIndex());",
          "    }",
          "",
          "    // fix173: the system default monthly storage fee, so the Intake and Folder pages never carry their own copy of the number",
          "    @PreAuthorize(\"hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')\")",
          "    @GetMapping(\"/storage-fee-default\")",
          "    public ResponseEntity<java.util.Map<String, java.math.BigDecimal>> storageFeeDefault() {",
          "        return ResponseEntity.ok(java.util.Map.of(\"defaultMonthlyFee\", LandProject.DEFAULT_MONTHLY_STORAGE_FEE));",
          "    }",
          ""
      ]),
      "LandController: GET /land/storage-fee-default")

patch(F_LAND_SERVICE_JS,
      "\n".join([
          "import api from '../api/axios';",
          "",
          "const landService = {"
      ]),
      "\n".join([
          "import api from '../api/axios';",
          "",
          "// fix173: the system default monthly storage fee is fetched once and shared by every page",
          "let storageFeeDefaultPromise = null;",
          "",
          "const landService = {"
      ]),
      "landService.js: cache slot for the default fee")

patch(F_LAND_SERVICE_JS,
      "\n".join([
          "    getNextIndex: async () => {",
          "        const response = await api.get('/land/next-index');",
          "        return response.data;",
          "    }",
          "};"
      ]),
      "\n".join([
          "    getNextIndex: async () => {",
          "        const response = await api.get('/land/next-index');",
          "        return response.data;",
          "    },",
          "",
          "    // fix173: the system default monthly storage fee (the server holds the only copy of the number)",
          "    getStorageFeeDefault: () => {",
          "        if (!storageFeeDefaultPromise) {",
          "            storageFeeDefaultPromise = api.get('/land/storage-fee-default')",
          "                .then(r => Number(r.data && r.data.defaultMonthlyFee) || 0)",
          "                .catch(e => { storageFeeDefaultPromise = null; throw e; });",
          "        }",
          "        return storageFeeDefaultPromise;",
          "    }",
          "};"
      ]),
      "landService.js: getStorageFeeDefault()")

patch(F_INTAKE_JSX,
      "\n".join([
          "const DEFAULT_MONTHLY_STORAGE_FEE = 50000;"
      ]),
      "\n".join([
          "// fix173: the default monthly storage fee is read from the server (landService.getStorageFeeDefault); no copy of it lives here."
      ]),
      "Intake: remove the hard-coded 50,000")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const [monthlyStorageFee, setMonthlyStorageFee] = useState(DEFAULT_MONTHLY_STORAGE_FEE);"
      ]),
      "\n".join([
          "    // fix173: blank = follow the system default (nothing is stored on the project); a typed rate is that project's own rate",
          "    const [monthlyStorageFee, setMonthlyStorageFee] = useState('');",
          "    const [systemFee, setSystemFee] = useState(0);",
          "    useEffect(() => { landService.getStorageFeeDefault().then(setSystemFee).catch(() => {}); }, []);"
      ]),
      "Intake: monthly fee starts blank, default comes from the server")

patch(F_INTAKE_JSX,
      "\n".join([
          "const backlogNow = receivablesSince ? monthsSince(receivablesSince) * (Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE) : 0;"
      ]),
      "\n".join([
          "const backlogNow = receivablesSince ? monthsSince(receivablesSince) * (Number(monthlyStorageFee) || systemFee) : 0;"
      ]),
      "Intake: backlog check uses the server default")

patch(F_INTAKE_JSX,
      "\n".join([
          "                payload.monthlyStorageFee = Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE;"
      ]),
      "\n".join([
          "                // fix173: send a rate only when one was typed that differs from the system default, so a project entered at the",
          "                // default keeps FOLLOWING the default (before, every Legacy project was saved with its own copy of 50,000)",
          "                const typedFee = Number(monthlyStorageFee) || 0;",
          "                if (typedFee > 0 && typedFee !== systemFee) payload.monthlyStorageFee = typedFee;"
      ]),
      "Intake: do not save a copy of the default as the project's own rate")

patch(F_INTAKE_JSX,
      "\n".join([
          "setInitialStorageFeePaid(0); setMonthlyStorageFee(DEFAULT_MONTHLY_STORAGE_FEE);"
      ]),
      "\n".join([
          "setInitialStorageFeePaid(0); setMonthlyStorageFee('');"
      ]),
      "Intake: duplicate form resets the fee to blank")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const backlogRate = Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE;"
      ]),
      "\n".join([
          "    const backlogRate = Number(monthlyStorageFee) || systemFee;"
      ]),
      "Intake: summary backlog rate uses the server default")

patch(F_INTAKE_JSX,
      "\n".join([
          "value={monthlyStorageFee} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} />"
      ]),
      "\n".join([
          "value={monthlyStorageFee} placeholder={systemFee ? String(systemFee) : ''} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} />"
      ]),
      "Intake: monthly fee box shows the default as its placeholder")

patch(F_INTAKE_JSX,
      "\n".join([
          "<p className={styles.hint}>System default: {DEFAULT_MONTHLY_STORAGE_FEE.toLocaleString()}</p>"
      ]),
      "\n".join([
          "<p className={styles.hint}>System default: {systemFee ? systemFee.toLocaleString() : '...'}. Leave blank to use it.</p>"
      ]),
      "Intake: hint shows the server default")

patch(F_FOLDER_JSX,
      "\n".join([
          "const DEFAULT_RATE = 50000;"
      ]),
      "\n".join([
          "// fix173: the default monthly storage fee is read from the server (landService.getStorageFeeDefault); no copy of it lives here."
      ]),
      "Folder: remove the hard-coded 50,000")

patch(F_FOLDER_JSX,
      "\n".join([
          "    const [rateFee, setRateFee] = useState(''); const [pauseUntil, setPauseUntil] = useState('');"
      ]),
      "\n".join([
          "    const [rateFee, setRateFee] = useState(''); const [pauseUntil, setPauseUntil] = useState('');",
          "    const [defaultRate, setDefaultRate] = useState(0);   // fix173: system default monthly fee, from the server",
          "    useEffect(() => { landService.getStorageFeeDefault().then(setDefaultRate).catch(() => {}); }, []);"
      ]),
      "Folder: load the default fee from the server")

patch(F_FOLDER_JSX,
      "\n".join([
          "Number(project.storageFeeOverride) : DEFAULT_RATE;"
      ]),
      "\n".join([
          "Number(project.storageFeeOverride) : defaultRate;"
      ]),
      "Folder: effective rate falls back to the server default")

patch(F_FOLDER_JSX,
      "\n".join([
          "starts a monthly storage fee of UGX 50,000 unless a different rate is set, added every 30 days. Write why.'"
      ]),
      "\n".join([
          "starts a monthly storage fee of UGX ' + fmt(defaultRate) + ' unless a different rate is set, added every 30 days. Write why.'"
      ]),
      "Folder: MOVE TO RECEIVABLES text shows the server default")

patch(F_FOLDER_JSX,
      "\n".join([
          "adds a monthly storage fee (UGX 50,000 unless another rate is set) every 30 days."
      ]),
      "\n".join([
          "adds a monthly storage fee (UGX {fmt(defaultRate)} unless another rate is set) every 30 days."
      ]),
      "Folder: receivables hint shows the server default")

patch(F_FOLDER_JSX,
      "\n".join([
          "placeholder=\"50,000 (default)\" hint=\"Blank = the default 50,000. 0 = no more fees. Applies to the coming months only.\" />"
      ]),
      "\n".join([
          "placeholder={fmt(defaultRate) + ' (default)'} hint={'Blank = the default ' + fmt(defaultRate) + '. 0 = no more fees. Applies to the coming months only.'} />"
      ]),
      "Folder: rate box placeholder and hint show the server default")

patch(F_FOLDER_JSX,
      "\n".join([
          "rateFee === '' ? 'the default (UGX 50,000)' :"
      ]),
      "\n".join([
          "rateFee === '' ? 'the default (UGX ' + fmt(defaultRate) + ')' :"
      ]),
      "Folder: SAVE RATE confirmation shows the server default")

patch(F_GLOSSARY,
      "\n".join([
          "STORAGE_FEE: 'UGX 50,000 every 30 days. The 30-day clock only starts once the work becomes Legacy.',"
      ]),
      "\n".join([
          "STORAGE_FEE: 'The monthly storage fee (the system default unless the project has its own rate), added every 30 days. The 30-day clock only starts once the work becomes Legacy.',"
      ]),
      "Glossary: storage fee text no longer states the number")

patch(F_GUIDE,
      "\n".join([
          "- **Storage fee:** UGX 50,000 every 30 days. The 30-day timer only starts once the work becomes Legacy -- not before. This amount can be changed/overridden."
      ]),
      "\n".join([
          "- **Storage fee:** UGX 50,000 every 30 days. The 30-day timer only starts once the work becomes Legacy -- not before. This amount can be changed/overridden. (fix173) The 50,000 lives in ONE place, `LandProject.DEFAULT_MONTHLY_STORAGE_FEE`; the nightly job and the intake save use it, and the Intake and Folder pages read it from `GET /api/v1/land/storage-fee-default`. Intake sends a monthly rate only when staff typed one that differs from the default, so a project entered at the default has no stored rate (`storage_fee_override` null) and follows the default. The seed data (`ScenarioData`) still has its own 50000 for demo rows."
      ]),
      "Guide: where the default fee lives")

patch(F_GUIDE,
      "\n".join([
          "The 50,000 default is still a constant in ReceivableSchedulerService (a global editable default needs a settings table -- David to decide)."
      ]),
      "\n".join([
          "The 50,000 default is now ONE constant, `LandProject.DEFAULT_MONTHLY_STORAGE_FEE` (fix173); an editable global default still needs a settings table -- David to decide."
      ]),
      "Guide: backbone plan note about the default")

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

if not changed:
    print("note: nothing changed -- " + FIX_NO + " already applied")


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
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed and RUN_GATES:
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
if changed and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif changed:
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

if not changed:
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