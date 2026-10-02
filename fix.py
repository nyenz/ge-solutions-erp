#!/usr/bin/env python3
# PATH: fix173.py
# GOLDEN SEED -- fix173: default storage fee in ONE place, Recovery list only for clients who owe, 0/negative intake fee -> default,
# and a COLLECT SET-ASIDE FEES button (take payments for fees kept after a SET ASIDE).
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
#   5. LLM_CONTEXT_GUIDE.md: records where the default lives and the two rules below.
#   6. RECOVERY (owner decision): a client is on the Recovery list (queue, counts, stats, ALL DUE) only while they OWE money on a
#      project. Before, the check ended in an unconditional `return true`, so every client with any project was listed, even
#      fully paid ones. The queues and counts will get smaller. Owed = receivable project: cost + fees - paid; other project: cost - paid.
#   8. FOLDER + PAYMENTS (owner decision): new button COLLECT SET-ASIDE FEES in the Storage Fees panel of a set-aside project that still has
#      kept fees. It opens the normal payment window on STORAGE FEE (receipt, payer and whole-shilling rules unchanged; manager, admin or
#      director). Amount cannot be more than the kept fees. The project stays set aside and no new fees start. The paid amount goes into
#      amount paid and total cost and comes off the kept fees, so what the client owes on the title work does not change. When the kept
#      fees reach 0 the hand-over block is gone. A reversal of such a payment makes the fee owed again as part of the cost.
#   7. INTAKE (owner decision): a Monthly Storage Fee of 0 or less is not allowed. The box changes to the system default and a
#      message says so (when the user leaves the box, and again at save). The server already treats 0 or less as the default.
#
# NOT in this fix: an editable default (needs a settings table), the seed data's own 50000 in ScenarioData (demo rows only),
# changing existing projects that already carry a stored 50,000 rate (those keep it as their own rate), or any change to WAIVE /
# ADD FEES TO COST. The Folder page rate box is unchanged: there 0 still means no more fees.
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
COMMIT_MSG = "fix173: default storage fee in one place; Recovery list only for clients who owe money; intake fee 0/negative becomes the default; collect set-aside fees button"
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
F_RECOVERY = os.path.join(JAVA, "modules", "client", "controller", "RecoveryNoteController.java")
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
LOAD_FILES = (F_RECOVERY, F_LAND_PROJECT, F_SCHEDULER, F_LAND_SERVICE, F_LAND_CONTROLLER, F_LAND_SERVICE_JS, F_INTAKE_JSX, F_FOLDER_JSX, F_GLOSSARY, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

# patch_either: like patch(), but the text may be in more than one known state (never touched, or an earlier run of this fix).
def patch_either(path, olds, new, desc):
    text = FILES[path]
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return
    for old in olds:
        if old in text:
            print("OK: " + desc)
            FILES[path] = text.replace(old, new, 1)
            return
    print("MISSING: " + desc)
    MISSING.append(desc)


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

patch_either(F_INTAKE_JSX,
      ["\n".join([
          "const backlogNow = receivablesSince ? monthsSince(receivablesSince) * (Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE) : 0;"
      ]),
       "\n".join([
          "const backlogNow = receivablesSince ? monthsSince(receivablesSince) * (Number(monthlyStorageFee) || systemFee) : 0;"
      ])],
      "\n".join([
          "const backlogNow = receivablesSince ? monthsSince(receivablesSince) * feeOrDefault(monthlyStorageFee) : 0;"
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

patch_either(F_INTAKE_JSX,
      ["\n".join([
          "    const backlogRate = Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE;"
      ]),
       "\n".join([
          "    const backlogRate = Number(monthlyStorageFee) || systemFee;"
      ])],
      "\n".join([
          "    const backlogRate = feeOrDefault(monthlyStorageFee);"
      ]),
      "Intake: summary backlog rate uses the server default")

patch_either(F_INTAKE_JSX,
      ["\n".join([
          "value={monthlyStorageFee} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} />"
      ]),
       "\n".join([
          "value={monthlyStorageFee} placeholder={systemFee ? String(systemFee) : ''} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} />"
      ])],
      "\n".join([
          "value={monthlyStorageFee} placeholder={systemFee ? String(systemFee) : ''} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} onBlur={fixFeeBox} />"
      ]),
      "Intake: monthly fee box shows the default as a placeholder and is fixed when the user leaves it")

patch_either(F_INTAKE_JSX,
      ["\n".join([
          "<p className={styles.hint}>System default: {DEFAULT_MONTHLY_STORAGE_FEE.toLocaleString()}</p>"
      ]),
       "\n".join([
          "<p className={styles.hint}>System default: {systemFee ? systemFee.toLocaleString() : '...'}. Leave blank to use it.</p>"
      ])],
      "\n".join([
          "<p className={styles.hint}>System default: {systemFee ? systemFee.toLocaleString() : '...'}. Leave blank to use it. 0 or less is not allowed and turns into the default.</p>"
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

patch(F_RECOVERY,
      "\n".join([
          "    private boolean qualifies(List<LandProject> ps) {",
          "        if (ps.isEmpty()) return false;",
          "        for (LandProject p : ps) {",
          "            if (p.isLegacy()) return true;",
          "            if (Math.max(p.activeTotalOwed().doubleValue(), p.receivableTotalOwed().doubleValue()) > 0) return true;",
          "            if (p.getStages() != null) { for (Object s : p.getStages()) { if (s instanceof com.gesolutions.erp.modules.land.model.ProjectStage) { if (!((com.gesolutions.erp.modules.land.model.ProjectStage) s).isCompleted()) return true; } } }",
          "            return true;",
          "        }",
          "        return false;",
          "    }"
      ]),
      "\n".join([
          "    // fix173: a client is on the Recovery list only while they OWE money on at least one project. Fully paid clients, finished",
          "    // legacy projects and projects with only unfinished stages are no longer listed. \"Owes\" is counted the same way the",
          "    // rest of the app counts it: a receivable project owes cost + fees - paid; any other project owes cost - paid.",
          "    // (Fees kept by SET ASIDE are not owed while the project is set aside, so they do not count here.)",
          "    private boolean qualifies(List<LandProject> ps) {",
          "        for (LandProject p : ps) {",
          "            java.math.BigDecimal owed = p.isReceivable() ? p.receivableTotalOwed() : p.activeTotalOwed();",
          "            if (owed.signum() > 0) return true;",
          "        }",
          "        return false;",
          "    }"
      ]),
      "Recovery: a client is listed only while they owe money")

patch(F_INTAKE_JSX,
      "\n".join([
          "        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);",
          "    }, []);",
          ""
      ]),
      "\n".join([
          "        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);",
          "    }, []);",
          "    // fix173: a monthly fee of 0 or less is not allowed at intake. It becomes the system default and the user is told.",
          "    const feeOrDefault = (v) => { const n = Number(v); return n > 0 ? n : systemFee; };",
          "    const fixFeeBox = () => {",
          "        if (monthlyStorageFee === '' || monthlyStorageFee === null || Number(monthlyStorageFee) > 0) return;",
          "        setMonthlyStorageFee(systemFee > 0 ? String(systemFee) : '');",
          "        toast('Monthly Storage Fee must be more than 0, so the system default' + (systemFee > 0 ? ' (UGX ' + systemFee.toLocaleString() + ')' : '') + ' is used instead.', 'info');",
          "    };",
          ""
      ]),
      "Intake: helper that turns a 0 or negative monthly fee into the default and shows a message")

patch(F_INTAKE_JSX,
      "\n".join([
          "        if (isLegacy) {",
          "            const feeCharged = Number(initialStorageFee) || 0;"
      ]),
      "\n".join([
          "        if (isLegacy) {",
          "            fixFeeBox();   // fix173: 0 or negative monthly fee -> default, with a message",
          "            const feeCharged = Number(initialStorageFee) || 0;"
      ]),
      "Intake: same fix at save time")

patch(F_GUIDE,
      "\n".join([
          "## 19. SEED DATA (DATASET v4, fix167)"
      ]),
      "\n".join([
          "**Recovery list rule (fix173).** `RecoveryNoteController.qualifies()`: a client is listed (queue, queue counts, stats `dueNow`, ALL DUE) only while at least one of their projects is owed money: receivable project = cost + fees - paid, other project = cost - paid. Fully paid clients, finished legacy projects and unfinished stages alone no longer list a client. **Intake monthly fee (fix173):** 0 or negative is turned into the system default on the page (box changes, message shown); the server already did the same.",
          "",
          "**Collecting set-aside fees (fix173).** A project that was SET ASIDE and still carries kept fees (`storage_fees_accumulated` > 0, not receivable) accepts a STORAGE payment through the same payment window (button COLLECT SET-ASIDE FEES on the Folder page; manager, admin, director; receipt and payer rules unchanged). Rules in `LandService.recordPayment`: amount <= kept fees; billing stays stopped; the paid amount is added to `amount_paid` AND to `total_cost`, and taken off `storage_fees_accumulated` (`storage_fees_paid` stays 0), so \"owed = total_cost - amount_paid\" is unchanged and only the kept fees go down. When they reach 0 the hand-over block clears. Reversing such a payment lowers `amount_paid` only: the fee stays inside `total_cost`, so the client owes it again as part of the cost (same as reversing a fee payment made before the project left receivables).",
          "",
          "## 19. SEED DATA (DATASET v4, fix167)"
      ]),
      "Guide: Recovery list rule and intake fee rule")

patch(F_LAND_SERVICE,
      "\n".join([
          "        if (\"STORAGE\".equals(kind)) {",
          "            if (!project.isReceivable()) {",
          "                throw new BusinessException(\"PAYMENT_FAULT: Storage fees can only be paid while the project is in receivables.\");",
          "            }",
          "            BigDecimal feesLeft = project.storageUnpaid();"
      ]),
      "\n".join([
          "        // fix173: a STORAGE payment is allowed in two cases: the project is in receivables, OR it was SET ASIDE and still carries",
          "        // kept (unpaid) fees. The second case is \"collecting set-aside fees\": billing stays stopped, no new fees are added.",
          "        boolean keptFeesPayment = \"STORAGE\".equals(kind) && !project.isReceivable();",
          "        if (\"STORAGE\".equals(kind)) {",
          "            if (keptFeesPayment && project.storageUnpaid().signum() <= 0) {",
          "                throw new BusinessException(\"PAYMENT_FAULT: There are no storage fees to pay on this project. Storage fees can be paid while the project is in receivables, or while set-aside fees are still kept on it.\");",
          "            }",
          "            BigDecimal feesLeft = project.storageUnpaid();"
      ]),
      "Payments: allow STORAGE payments on a set-aside project that still has kept fees")

patch(F_LAND_SERVICE,
      "\n".join([
          "        project.setAmountPaid(paidNow.add(amount));",
          "        if (\"STORAGE\".equals(kind)) project.setStorageFeesPaid(project.storagePaidSafe().add(amount));"
      ]),
      "\n".join([
          "        project.setAmountPaid(paidNow.add(amount));",
          "        if (keptFeesPayment) {",
          "            // fix173: paid set-aside fees move into the total cost at once (the same rule SET ASIDE and WAIVE use for paid fees),",
          "            // so \"owed = total cost - amount paid\" stays true and only the kept (unpaid) fees go down.",
          "            project.setTotalCost(cost.add(amount));",
          "            project.setStorageFeesAccumulated(project.getStorageFeesAccumulated().subtract(amount));",
          "        } else if (\"STORAGE\".equals(kind)) {",
          "            project.setStorageFeesPaid(project.storagePaidSafe().add(amount));",
          "        }"
      ]),
      "Payments: a paid set-aside fee moves into the total cost and lowers the kept fees")

patch(F_LAND_SERVICE,
      "\n".join([
          "            + \" | For: \" + kind",
          "            + (payer != null"
      ]),
      "\n".join([
          "            + \" | For: \" + kind + (keptFeesPayment ? \" (set-aside fees)\" : \"\")",
          "            + (payer != null"
      ]),
      "Payments: audit line says when the money was for set-aside fees")

patch(F_LAND_SERVICE,
      "\n".join([
          "of set-aside storage fees is still on this project. A director must WAIVE them or ADD them to the cost first.\");"
      ]),
      "\n".join([
          "of set-aside storage fees is still on this project. Collect them as a STORAGE FEE payment, or a director must WAIVE them or ADD them to the cost first.\");"
      ]),
      "Hand-over message mentions collecting the kept fees")

patch(F_FOLDER_JSX,
      "\n".join([
          "    const openPayModal = () => {",
          "        setPayAmount(''); setPayNotes(''); setPayErr(''); setPayReceipt(null);",
          "        setPayType('TITLE');"
      ]),
      "\n".join([
          "    // fix173: openPayModal('STORAGE') opens it on the STORAGE FEE choice (used by COLLECT SET-ASIDE FEES)",
          "    const openPayModal = (startType) => {",
          "        setPayAmount(''); setPayNotes(''); setPayErr(''); setPayReceipt(null);",
          "        setPayType(startType === 'STORAGE' ? 'STORAGE' : 'TITLE');"
      ]),
      "Folder: payment window can open on STORAGE FEE")

patch(F_FOLDER_JSX,
      "\n".join([
          "                                <div className={styles.recvActionRow}>",
          "                                    {canMoney && !isDeleted && !isReleased && amountOwed + keptFees > 0"
      ]),
      "\n".join([
          "                                <div className={styles.recvActionRow}>",
          "                                    {canEdit && !isReleased && keptFees > 0 && <button type=\"button\" className={styles.ctrlBtnPay}",
          "                                        title={'Take a payment for the kept fees (receipt required). The project stays set aside and no new fees start. Unpaid: UGX ' + fmt(keptFees)}",
          "                                        onClick={() => openPayModal('STORAGE')}><FiDollarSign aria-hidden=\"true\" /> COLLECT SET-ASIDE FEES</button>}",
          "                                    {canMoney && !isDeleted && !isReleased && amountOwed + keptFees > 0"
      ]),
      "Folder: COLLECT SET-ASIDE FEES button")

patch(F_FOLDER_JSX,
      "\n".join([
          "                {isReceivable && (<div className={styles.payTypeRow}>"
      ]),
      "\n".join([
          "                {(isReceivable || keptFees > 0) && (<div className={styles.payTypeRow}>"
      ]),
      "Folder: payment window offers TITLE / STORAGE FEE also for set-aside fees")

patch(F_FOLDER_JSX,
      "\n".join([
          "They are not owed now, but block the hand-over until a director waives them or adds them to the cost.\">SET-ASIDE FEES"
      ]),
      "\n".join([
          "They are not owed now, but block the hand-over until they are paid, or a director waives them or adds them to the cost.\">SET-ASIDE FEES"
      ]),
      "Folder: badge text mentions paying the kept fees")

patch(F_FOLDER_JSX,
      "\n".join([
          "title=\"Kept when the project was set aside. Not owed now; they block the hand-over until cleared.\""
      ]),
      "\n".join([
          "title=\"Kept when the project was set aside. Not owed now; they block the hand-over until they are paid, waived or added to the cost.\""
      ]),
      "Folder: kept fees box text mentions paying them")

patch(F_FOLDER_JSX,
      "\n".join([
          "and blocks the hand-over until it is waived or added to the cost.'"
      ]),
      "\n".join([
          "and blocks the hand-over until it is paid, waived or added to the cost.'"
      ]),
      "Folder: SET ASIDE window text mentions paying the kept fees")

patch(F_FOLDER_JSX,
      "\n".join([
          "must be waived or added to the cost first.'"
      ]),
      "\n".join([
          "must be paid, waived or added to the cost first.'"
      ]),
      "Folder: hand-over button text mentions paying the kept fees")

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