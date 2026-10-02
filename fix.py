#!/usr/bin/env python3
# PATH: fix174.py
# GOLDEN SEED -- fix174: DOCUMENTS sub-system -- Intake Documents box redesigned, every intake file gets a document type
# (the folder classifications), and INVOICES added as a document type.
#
# WHAT CHANGES:
#   1. INTAKE > Documents box: the uploaded files are listed at the TOP, the upload button sits BELOW them. Once at least one
#      file is in, the upload button shrinks to a slim "ADD MORE DOCUMENTS" bar (full-size "CLICK TO UPLOAD *" only while empty).
#   2. INTAKE: every file carries a DOCUMENT TYPE picked from the same classifications the Folder page uses (Application Forms,
#      Offer Letters, Forwarding Letters, Deed Plan, Copy of Title, Invoices, plus any custom ones). A "SET ALL TO" picker shows
#      when more than one file is queued. Saving is refused until every file has a type. PAYMENT_RECEIPT is not offered at intake
#      (receipts are filed by the payment window and can never be deleted).
#   3. BACKEND: POST /land/ingest accepts `categories` (one per file, same order as `scans`). LandService.atomicIntake has a new
#      3-argument form that refuses a file without a type and files each document under its type (bad type = whole intake rolls
#      back). The old 2-argument form stays (tests, seeders) and means "no types".
#   4. INVOICES: new built-in category INVOICE ("Invoices"). DocumentCategoryService seeds any missing built-in on first use,
#      so it appears on the Folder page upload window, the Folder vault headings and the Intake picker with no database edit.
#   5. LLM_CONTEXT_GUIDE.md: records the above.
#
# NOT in this fix: changing the Folder page (its upload window and vault grouping already use the categories and pick up Invoices
# by themselves), re-typing documents uploaded before, or adding a "new category" button on the Intake page (add one from the
# Folder page upload window).
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix174"
COMMIT_MSG = "fix174: Intake documents box (files on top, slim upload bar), document type per intake file, Invoices category"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

F_DOC_CAT_SERVICE = os.path.join(JAVA, "modules", "land", "service", "DocumentCategoryService.java")
F_LAND_SERVICE = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
F_LAND_CONTROLLER = os.path.join(JAVA, "modules", "land", "controller", "LandController.java")
F_LAND_SERVICE_JS = os.path.join(SRC, "services", "landService.js")
F_INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
F_INTAKE_CSS = os.path.join(SRC, "pages", "Intake", "IntakePage.module.css")
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
LOAD_FILES = (F_DOC_CAT_SERVICE, F_LAND_SERVICE, F_LAND_CONTROLLER, F_LAND_SERVICE_JS, F_INTAKE_JSX, F_INTAKE_CSS, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_DOC_CAT_SERVICE,
      "\n".join([
          "        {\"PAYMENT_RECEIPT\",    \"Payment Receipts\"},",
          "    };",
      ]),
      "\n".join([
          "        {\"PAYMENT_RECEIPT\",    \"Payment Receipts\"},",
          "        {\"INVOICE\",            \"Invoices\"},   // fix174",
          "    };",
      ]),
      "DocumentCategoryService: INVOICE built-in category")

patch(F_LAND_SERVICE,
      "\n".join([
          "    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {",
      ]),
      "\n".join([
          "    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {",
          "        return atomicIntake(request, scans, null);",
          "    }",
          "",
          "    // fix174: the Intake page sends a document type (category code) for every file, same order as the files.",
          "    // A file without a type is refused here because the server must not trust the page. A type that does not exist is refused",
          "    // inside addScansToProject, which rolls the whole intake back.",
          "    @Transactional(rollbackFor = Exception.class)",
          "    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans, List<String> categories) throws Exception {",
          "        if (categories != null && scans != null) {",
          "            for (int i = 0; i < scans.length; i++) {",
          "                String c = i < categories.size() ? categories.get(i) : null;",
          "                if (c == null || c.isBlank()) {",
          "                    throw new BusinessException(\"DOCUMENT_TYPE_MISSING: Pick a document type for every file (\" + scans[i].getOriginalFilename() + \").\");",
          "                }",
          "            }",
          "        }",
      ]),
      "LandService: atomicIntake with a document type per file")

patch(F_LAND_SERVICE,
      "\n".join([
          "        if (scans != null) addScansToProject(saved.getId(), scans);",
      ]),
      "\n".join([
          "        if (scans != null) addScansToProject(saved.getId(), scans, null, categories);   // fix174: file each document under its type",
      ]),
      "LandService: intake files each document under its type")

patch(F_LAND_CONTROLLER,
      "\n".join([
          "            @RequestPart(value = \"scans\", required = false) MultipartFile[] scans) throws Exception {",
          "        LandEntryRequest request = objectMapper.readValue(jsonData, LandEntryRequest.class);",
          "        return ResponseEntity.ok(landService.atomicIntake(request, scans));",
      ]),
      "\n".join([
          "            @RequestPart(value = \"scans\", required = false) MultipartFile[] scans,",
          "            @RequestParam(value = \"categories\", required = false) List<String> categories) throws Exception {   // fix174",
          "        LandEntryRequest request = objectMapper.readValue(jsonData, LandEntryRequest.class);",
          "        return ResponseEntity.ok(landService.atomicIntake(request, scans, categories));",
      ]),
      "LandController: /land/ingest takes the document types")

patch(F_LAND_SERVICE_JS,
      "\n".join([
          "    createAtomicEntry: async (data, scans) => {",
      ]),
      "\n".join([
          "    createAtomicEntry: async (data, scans, categories = []) => {",
      ]),
      "landService.js: createAtomicEntry takes categories")

patch(F_LAND_SERVICE_JS,
      "\n".join([
          "        if (scans) scans.forEach(file => formData.append('scans', file));",
          "        const response = await api.post('/land/ingest', formData, {",
      ]),
      "\n".join([
          "        if (scans) scans.forEach(file => formData.append('scans', file));",
          "        // fix174: one document type (category code) per file, same order as scans",
          "        if (scans && categories.length === scans.length) categories.forEach(c => formData.append('categories', c || ''));",
          "        const response = await api.post('/land/ingest', formData, {",
      ]),
      "landService.js: send one category per intake file")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const [fileQueue, setFileQueue] = useState([]);",
          "",
      ]),
      "\n".join([
          "    const [fileQueue, setFileQueue] = useState([]);",
          "    // fix174: document types = the Folder page classifications (PAYMENT_RECEIPT is filed by the payment window, never at intake)",
          "    const [docCats, setDocCats] = useState([]);",
          "    useEffect(() => { landService.getDocumentCategories().then(setDocCats).catch(() => {}); }, []);",
          "    const catChoices = useMemo(() => docCats.filter(c => c.code !== 'PAYMENT_RECEIPT'), [docCats]);",
          "    const catLabelOf = (code) => { const c = docCats.find(x => x.code === code); return c ? c.label : ''; };",
          "    const catCodeOf = (label) => { const c = catChoices.find(x => x.label === label); return c ? c.code : ''; };",
          "",
      ]),
      "IntakePage: load document types")

patch(F_INTAKE_JSX,
      "\n".join([
          "const items = Array.from(e.target.files).map(f => ({ name: f.name, size: f.size, file: f, url: URL.createObjectURL(f) }));",
      ]),
      "\n".join([
          "const items = Array.from(e.target.files).map(f => ({ name: f.name, size: f.size, file: f, url: URL.createObjectURL(f), category: '' }));",
      ]),
      "IntakePage: each queued file starts with no type")

patch(F_INTAKE_JSX,
      "\n".join([
          "    const triggerFileInput = () => fileInputRef.current && fileInputRef.current.click();",
          "",
      ]),
      "\n".join([
          "    const triggerFileInput = () => fileInputRef.current && fileInputRef.current.click();",
          "    const setFileCategory = (i, label) => { setFileQueue(p => p.map((q, j) => (j === i ? { ...q, category: catCodeOf(label) } : q))); markDirty(); };",
          "    const setAllCategories = (label) => { const code = catCodeOf(label); setFileQueue(p => p.map(q => ({ ...q, category: code }))); markDirty(); };",
          "",
      ]),
      "IntakePage: set document type (one file / all files)")

patch(F_INTAKE_JSX,
      "\n".join([
          "        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }",
          "",
      ]),
      "\n".join([
          "        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }",
          "        if (fileQueue.some(q => !q.category)) { toast('Pick a document type for every file.', 'error'); return false; }   // fix174",
          "",
      ]),
      "IntakePage: every file needs a document type")

patch(F_INTAKE_JSX,
      "\n".join([
          "await landService.createAtomicEntry(payload, fileQueue.map(q => q.file));",
      ]),
      "\n".join([
          "await landService.createAtomicEntry(payload, fileQueue.map(q => q.file), fileQueue.map(q => q.category));",
      ]),
      "IntakePage: send the document types with the files")

patch(F_INTAKE_JSX,
      "\n".join([
          "                        <div className={styles.dropzone} onClick={triggerFileInput} role=\"button\" tabIndex={0}",
          "                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); } }}>",
          "                            <span className={styles.dropzoneIcon}><FiUploadCloud size={18} /></span>",
          "                            <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>",
          "                            <span className={styles.dropzoneSub}>Required - PDF, images, any file</span>",
          "                        </div>",
          "                        <input ref={fileInputRef} type=\"file\" multiple onChange={handleFileUpload} style={{ display: 'none' }} />",
          "                        <div className={styles.fileList}>",
          "                            {fileQueue.map((f, i) => (",
          "                                <div key={i} className={styles.fileItem}>",
          "                                    <span className={styles.fileMeta}>",
          "                                        <FiFile className={styles.fileIcon} size={14} />",
          "                                        <span className={styles.fileName}>{f.name}</span>",
          "                                        <span className={styles.fileSize}>{fmtSize(f.size)}</span>",
          "                                    </span>",
          "                                    <span className={styles.fileActions}>",
          "                                        <a className={`${styles.btn} ${styles.small}`} href={f.url} target=\"_blank\" rel=\"noreferrer\" aria-label={`View ${f.name}`}>",
          "                                            <FiEye size={12} /> View",
          "                                        </a>",
          "                                        <button type=\"button\" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`} onClick={() => removeFile(i)} aria-label={`Remove ${f.name}`}>",
          "                                            <FiTrash2 size={12} />",
          "                                        </button>",
          "                                    </span>",
          "                                </div>",
          "                            ))}",
          "                        </div>",
      ]),
      "\n".join([
          "                        {fileQueue.length > 0 && (",
          "                            <div className={styles.fileList}>",
          "                                {fileQueue.map((f, i) => (",
          "                                    <div key={i} className={styles.fileItem}>",
          "                                        <span className={styles.fileMeta}>",
          "                                            <FiFile className={styles.fileIcon} size={14} />",
          "                                            <span className={styles.fileName}>{f.name}</span>",
          "                                            <span className={styles.fileSize}>{fmtSize(f.size)}</span>",
          "                                        </span>",
          "                                        <span className={styles.fileActions}>",
          "                                            <span className={styles.fileCat}>",
          "                                                <HardwareSelect compact options={catChoices.map(c => c.label)} value={catLabelOf(f.category)}",
          "                                                    placeholder=\"Document type\" onChange={label => setFileCategory(i, label)} />",
          "                                            </span>",
          "                                            <a className={`${styles.btn} ${styles.small}`} href={f.url} target=\"_blank\" rel=\"noreferrer\" aria-label={`View ${f.name}`}>",
          "                                                <FiEye size={12} /> View",
          "                                            </a>",
          "                                            <button type=\"button\" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`} onClick={() => removeFile(i)} aria-label={`Remove ${f.name}`}>",
          "                                                <FiTrash2 size={12} />",
          "                                            </button>",
          "                                        </span>",
          "                                    </div>",
          "                                ))}",
          "                            </div>",
          "                        )}",
          "                        {fileQueue.length > 1 && (",
          "                            <div className={styles.setAllRow}>",
          "                                <span className={styles.setAllLabel}>Set all to</span>",
          "                                <HardwareSelect compact options={catChoices.map(c => c.label)}",
          "                                    value={fileQueue.every(q => q.category === fileQueue[0].category) ? catLabelOf(fileQueue[0].category) : ''}",
          "                                    placeholder=\"Choose type\" onChange={setAllCategories} />",
          "                            </div>",
          "                        )}",
          "                        <div className={`${styles.dropzone} ${fileQueue.length > 0 ? styles.dropzoneCompact : ''}`} onClick={triggerFileInput} role=\"button\" tabIndex={0}",
          "                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); } }}>",
          "                            <span className={styles.dropzoneIcon}><FiUploadCloud size={fileQueue.length > 0 ? 13 : 18} /></span>",
          "                            {fileQueue.length > 0 ? (",
          "                                <span className={styles.dropzoneTitle}>Add more documents</span>",
          "                            ) : (",
          "                                <>",
          "                                    <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>",
          "                                    <span className={styles.dropzoneSub}>Required - PDF, images, any file</span>",
          "                                </>",
          "                            )}",
          "                        </div>",
          "                        <input ref={fileInputRef} type=\"file\" multiple onChange={handleFileUpload} style={{ display: 'none' }} />",
      ]),
      "IntakePage: Documents box -- files on top, slim upload bar below, type picker per file")

patch(F_INTAKE_CSS,
      "\n".join([
          ".fileActions { display: flex; gap: var(--gap-md); flex-shrink: 0; }",
      ]),
      "\n".join([
          ".fileActions { display: flex; gap: var(--gap-md); flex-shrink: 0; align-items: center; }",
          "/* fix174: files on top, slim upload bar below */",
          ".fileList { margin-bottom: var(--gap-md); }",
          ".fileItem { flex-wrap: wrap; }",
          ".fileCat { display: inline-flex; min-width: 0; }",
          ".setAllRow { display: flex; align-items: center; justify-content: flex-end; gap: 8px; margin-bottom: var(--gap-md); }",
          ".setAllLabel { font-size: var(--fs-meta); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.45); }",
          ".dropzoneCompact { flex-direction: row; justify-content: center; gap: 8px; padding: 6px 12px; }",
          ".dropzoneCompact .dropzoneIcon { width: 24px; height: 24px; margin-bottom: 0; }",
          ".dropzoneCompact .dropzoneTitle { font-size: var(--fs-meta); }",
      ]),
      "IntakePage.module.css: slim upload bar + type picker styles")

patch(F_GUIDE,
      "\n".join([
          "- FOLDER PAGE LOOPHOLES CLOSED (fix166):",
      ]),
      "\n".join([
          "- DOCUMENTS (fix174): (1) the Intake Documents box lists the files at the TOP and the upload button BELOW; once a file is queued the button shrinks to a slim ADD MORE DOCUMENTS bar. (2) Every intake file must carry a document type = a `document_categories` code (the Folder page classifications; PAYMENT_RECEIPT is not offered at intake). `POST /land/ingest` takes `categories` (one per file, same order as `scans`); `LandService.atomicIntake(request, scans, categories)` refuses a missing type and rolls the whole intake back on an unknown one; the 2-argument form still exists and means no types. (3) INVOICE (\"Invoices\") is a built-in category, seeded by `DocumentCategoryService.ensureDefaults()` like the other built-ins -- add future built-ins to `DEFAULTS` there, nowhere else.",
          "- FOLDER PAGE LOOPHOLES CLOSED (fix166):",
      ]),
      "Guide: documents rules (fix174)")

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