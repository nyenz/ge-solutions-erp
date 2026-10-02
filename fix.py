#!/usr/bin/env python3
# PATH: fix175.py
# GOLDEN SEED -- fix175: INTAKE > Documents now classifies files with the Folder page's UPLOAD DOCUMENTS popup; View never downloads.
#
# WHAT CHANGES:
#   1. INTAKE: choosing files opens the same UPLOAD DOCUMENTS popup the Folder page uses (CATEGORY FOR ALL n FILE(S), a category
#      per file, + NEW CATEGORY). Pressing ADD puts the files in the Documents box, each showing its type as a tag. The old inline
#      per-file picker and the SET ALL TO row are gone. A file cannot join the list without a type.
#   2. INTAKE: same file rules as the Folder page (PDF, JPG, PNG, WEBP; not empty; max 50 MB). Rejected files are named in a toast.
#   3. VIEW (Intake): opens an in-page preview window (PDF in a frame, images as images) -- nothing is downloaded, no new tab.
#   4. VIEW (Folder page): opens the stored file as a typed blob (application/pdf, image/*) so the browser shows it instead of
#      downloading it; falls back to the plain link if the fetch fails.
#   5. LLM_CONTEXT_GUIDE.md: records the above.
#
# NOT in this fix: backend (it already takes `categories` per file from fix174), re-typing a queued file (remove it and add it again).
#
# Atomic: every patch for every file is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix175"
COMMIT_MSG = "fix175: Intake documents use the Folder upload popup for classification; View opens inline without downloading"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

F_INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
F_INTAKE_CSS = os.path.join(SRC, "pages", "Intake", "IntakePage.module.css")
F_FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
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
LOAD_FILES = (F_INTAKE_JSX, F_INTAKE_CSS, F_FOLDER_JSX, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_INTAKE_JSX, "import HardwareSelect from '../../components/common/HardwareSelect';\n", "import HardwareSelect from '../../components/common/HardwareSelect';\nimport HardwareModal from '../../components/common/HardwareModal';\nimport HardwareModalSelect from '../../components/common/HardwareModalSelect';\nimport modalStyles from '../../components/common/HardwareModal.module.css';\n", "IntakePage: imports (modal, modal select, modal styles)")

patch(F_INTAKE_JSX, "const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';", "const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';\n// fix175: same file rules as the Folder page\nconst SCAN_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'webp'];\nconst fileExt = (name) => { const m = String(name || '').toLowerCase().match(/[.]([a-z0-9]{1,6})$/); return m ? m[1] : ''; };", "IntakePage: file helpers (allowed types)")

patch(F_INTAKE_JSX, "    const catChoices = useMemo(() => docCats.filter(c => c.code !== 'PAYMENT_RECEIPT'), [docCats]);\n", "    const catChoices = useMemo(() => docCats.filter(c => c.code !== 'PAYMENT_RECEIPT'), [docCats]);\n    const catOptions = useMemo(() => catChoices.map(c => ({ value: c.code, label: c.label })), [catChoices]);\n    const [uploadDraft, setUploadDraft] = useState(null); // fix175: { batch, error, files: [{ file, category }] }\n    const [newCatOpen, setNewCatOpen] = useState(false);\n    const [newCatName, setNewCatName] = useState('');\n    const [catBusy, setCatBusy] = useState(false);\n    const [previewFile, setPreviewFile] = useState(null);\n", "IntakePage: popup + preview state")

patch(F_INTAKE_JSX, "    const handleFileUpload = (e) => {\n        const items = Array.from(e.target.files).map(f => ({ name: f.name, size: f.size, file: f, url: URL.createObjectURL(f), category: '' }));\n        if (items.length) { setFileQueue(p => [...p, ...items]); markDirty(); }\n        e.target.value = '';\n    };", "    // fix175: picking files opens the same UPLOAD DOCUMENTS popup the Folder page uses; files join the list only once each has a type\n    const handleFileUpload = (e) => {\n        const picked = Array.from(e.target.files || []);\n        e.target.value = '';\n        if (!picked.length) return;\n        const ok = []; const bad = [];\n        picked.forEach(f => {\n            if (!SCAN_EXT.includes(fileExt(f.name))) bad.push(f.name + ' (use PDF, JPG, PNG or WEBP)');\n            else if (!f.size) bad.push(f.name + ' (the file is empty)');\n            else if (f.size > 50 * 1024 * 1024) bad.push(f.name + ' (over 50 MB)');\n            else ok.push(f);\n        });\n        if (bad.length) toast('NOT ADDED: ' + bad.join('; '), 'error');\n        if (!ok.length) return;\n        setUploadDraft({ batch: '', error: '', files: ok.map(file => ({ file, category: '' })) });\n    };", "IntakePage: file pick opens the popup")

patch(F_INTAKE_JSX, '    const setFileCategory = (i, label) => { setFileQueue(p => p.map((q, j) => (j === i ? { ...q, category: catCodeOf(label) } : q))); markDirty(); };\n    const setAllCategories = (label) => { const code = catCodeOf(label); setFileQueue(p => p.map(q => ({ ...q, category: code }))); markDirty(); };', '    const closeUploadDraft = () => { setUploadDraft(null); setNewCatOpen(false); setNewCatName(\'\'); };\n    const setBatchCategory = (code) => setUploadDraft(d => d && ({ ...d, error: \'\', batch: code, files: d.files.map(f => ({ ...f, category: code })) }));\n    const setDraftFileCategory = (i, code) => setUploadDraft(d => d && ({ ...d, error: \'\', files: d.files.map((f, j) => (j === i ? { ...f, category: code } : f)) }));\n    const handleAddCategory = async () => {\n        const name = newCatName.trim();\n        if (name.length < 2 || catBusy) return;\n        setCatBusy(true);\n        try {\n            const cat = await landService.addDocumentCategory(name);\n            setDocCats(await landService.getDocumentCategories());\n            setNewCatName(\'\'); setNewCatOpen(false);\n            setUploadDraft(d => d && ({ ...d, error: \'\', batch: d.batch || cat.code, files: d.files.map(f => (f.category ? f : { ...f, category: cat.code })) }));\n            toast(\'Category "\' + cat.label + \'" ready\', \'success\');\n        } catch (err) { setUploadDraft(d => d && ({ ...d, error: \'COULD NOT ADD CATEGORY: \' + ((err && err.response && err.response.data && (err.response.data.message || err.response.data.error)) || (err && err.message) || \'unknown error\') })); } finally { setCatBusy(false); }\n    };\n    const confirmUploadDraft = () => {\n        if (!uploadDraft) return;\n        if (uploadDraft.files.some(f => !f.category)) { setUploadDraft(d => d && ({ ...d, error: \'PICK A CATEGORY FOR EVERY FILE.\' })); return; }\n        const items = uploadDraft.files.map(({ file, category }) => ({ name: file.name, size: file.size, file, url: URL.createObjectURL(file), category }));\n        setFileQueue(p => [...p, ...items]); markDirty();\n        closeUploadDraft();\n    };', "IntakePage: popup handlers")

patch(F_INTAKE_JSX, '                        {fileQueue.length > 0 && (\n                            <div className={styles.fileList}>\n                                {fileQueue.map((f, i) => (\n                                    <div key={i} className={styles.fileItem}>\n                                        <span className={styles.fileMeta}>\n                                            <FiFile className={styles.fileIcon} size={14} />\n                                            <span className={styles.fileName}>{f.name}</span>\n                                            <span className={styles.fileSize}>{fmtSize(f.size)}</span>\n                                        </span>\n                                        <span className={styles.fileActions}>\n                                            <span className={styles.fileCat}>\n                                                <HardwareSelect compact options={catChoices.map(c => c.label)} value={catLabelOf(f.category)}\n                                                    placeholder="Document type" onChange={label => setFileCategory(i, label)} />\n                                            </span>\n                                            <a className={`${styles.btn} ${styles.small}`} href={f.url} target="_blank" rel="noreferrer" aria-label={`View ${f.name}`}>\n                                                <FiEye size={12} /> View\n                                            </a>\n                                            <button type="button" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`} onClick={() => removeFile(i)} aria-label={`Remove ${f.name}`}>\n                                                <FiTrash2 size={12} />\n                                            </button>\n                                        </span>\n                                    </div>\n                                ))}\n                            </div>\n                        )}\n                        {fileQueue.length > 1 && (\n                            <div className={styles.setAllRow}>\n                                <span className={styles.setAllLabel}>Set all to</span>\n                                <HardwareSelect compact options={catChoices.map(c => c.label)}\n                                    value={fileQueue.every(q => q.category === fileQueue[0].category) ? catLabelOf(fileQueue[0].category) : \'\'}\n                                    placeholder="Choose type" onChange={setAllCategories} />\n                            </div>\n                        )}\n                        <div className={`${styles.dropzone} ${fileQueue.length > 0 ? styles.dropzoneCompact : \'\'}`} onClick={triggerFileInput} role="button" tabIndex={0}\n                            onKeyDown={e => { if (e.key === \'Enter\' || e.key === \' \') { e.preventDefault(); triggerFileInput(); } }}>\n                            <span className={styles.dropzoneIcon}><FiUploadCloud size={fileQueue.length > 0 ? 13 : 18} /></span>\n                            {fileQueue.length > 0 ? (\n                                <span className={styles.dropzoneTitle}>Add more documents</span>\n                            ) : (\n                                <>\n                                    <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>\n                                    <span className={styles.dropzoneSub}>Required - PDF, images, any file</span>\n                                </>\n                            )}\n                        </div>\n                        <input ref={fileInputRef} type="file" multiple onChange={handleFileUpload} style={{ display: \'none\' }} />', '                        {fileQueue.length > 0 && (\n                            <div className={styles.fileList}>\n                                {fileQueue.map((f, i) => (\n                                    <div key={i} className={styles.fileItem}>\n                                        <span className={styles.fileMeta}>\n                                            <FiFile className={styles.fileIcon} size={14} />\n                                            <span className={styles.fileName}>{f.name}</span>\n                                            <span className={styles.fileSize}>{fmtSize(f.size)}</span>\n                                        </span>\n                                        <span className={styles.fileActions}>\n                                            <span className={styles.fileTypeChip}>{catLabelOf(f.category) || \'No type\'}</span>\n                                            <button type="button" className={`${styles.btn} ${styles.small}`} onClick={() => setPreviewFile(f)} aria-label={`View ${f.name}`}>\n                                                <FiEye size={12} /> View\n                                            </button>\n                                            <button type="button" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`} onClick={() => removeFile(i)} aria-label={`Remove ${f.name}`}>\n                                                <FiTrash2 size={12} />\n                                            </button>\n                                        </span>\n                                    </div>\n                                ))}\n                            </div>\n                        )}\n                        <div className={`${styles.dropzone} ${fileQueue.length > 0 ? styles.dropzoneCompact : \'\'}`} onClick={triggerFileInput} role="button" tabIndex={0}\n                            onKeyDown={e => { if (e.key === \'Enter\' || e.key === \' \') { e.preventDefault(); triggerFileInput(); } }}>\n                            <span className={styles.dropzoneIcon}><FiUploadCloud size={fileQueue.length > 0 ? 13 : 18} /></span>\n                            {fileQueue.length > 0 ? (\n                                <span className={styles.dropzoneTitle}>Add more documents</span>\n                            ) : (\n                                <>\n                                    <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>\n                                    <span className={styles.dropzoneSub}>Required - PDF, JPG, PNG or WEBP, up to 50 MB each</span>\n                                </>\n                            )}\n                        </div>\n                        <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={handleFileUpload} style={{ display: \'none\' }} />', "IntakePage: Documents box (type tag, inline View, no inline picker)")

patch(F_INTAKE_JSX, "            {blocker.state === 'blocked' && typeof document !== 'undefined' && createPortal(", '            <HardwareModal isOpen={!!uploadDraft} lockBackdrop onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">\n                {uploadDraft && (<>\n                    <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>CATEGORY FOR ALL {uploadDraft.files.length} FILE(S)</label>\n                        <HardwareModalSelect value={uploadDraft.batch} options={catOptions} onChange={setBatchCategory} placeholder="Choose category" emptyText="No categories available" ariaLabel="Category for all files" /></div>\n                    <div className={styles.upFileList}>{uploadDraft.files.map((f, i) => (<div key={i} className={styles.upFileRow}>\n                        <span className={styles.upFileName} title={f.file.name}>{f.file.name}</span>\n                        <HardwareModalSelect compact className={styles.upFileSelect} value={f.category} options={catOptions} onChange={code => setDraftFileCategory(i, code)} placeholder="Category" emptyText="No categories available" ariaLabel={\'Category for \' + f.file.name} /></div>))}</div>\n                    {newCatOpen ? (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NEW CATEGORY NAME</label>\n                        <input type="text" className={modalStyles.modalInput} value={newCatName} maxLength={120} placeholder="e.g. Survey Report" onChange={e => setNewCatName(e.target.value)} onKeyDown={e => { if (e.key === \'Enter\') handleAddCategory(); }} />\n                        <div className={styles.upCatActions}>\n                            <button type="button" className={styles.upBtn} onClick={handleAddCategory} disabled={catBusy || newCatName.trim().length < 2}>SAVE CATEGORY</button>\n                            <button type="button" className={styles.upBtn} onClick={() => { setNewCatOpen(false); setNewCatName(\'\'); }}>CLOSE</button>\n                        </div></div>)\n                        : (<button type="button" className={styles.upBtn} onClick={() => setNewCatOpen(true)} title="Add a category that is not in the list yet">+ NEW CATEGORY</button>)}\n                    {uploadDraft.error && <div className={styles.upErr} role="alert">{uploadDraft.error}</div>}\n                    <div className={modalStyles.modalFooter}>\n                        <button type="button" className={modalStyles.modalBtnPrimary} onClick={confirmUploadDraft}>ADD</button>\n                    </div>\n                </>)}\n            </HardwareModal>\n            <HardwareModal isOpen={!!previewFile} onClose={() => setPreviewFile(null)} title={previewFile ? previewFile.name : \'\'}>\n                {previewFile && (fileExt(previewFile.name) === \'pdf\'\n                    ? <iframe className={styles.previewFrame} src={previewFile.url} title={previewFile.name} />\n                    : <img className={styles.previewImg} src={previewFile.url} alt={previewFile.name} />)}\n            </HardwareModal>\n            {blocker.state === \'blocked\' && typeof document !== \'undefined\' && createPortal(', "IntakePage: upload popup + preview window")

patch(F_INTAKE_CSS, '.notesWrap { display: flex; flex-direction: column; gap: 4px; }', '/* fix175: UPLOAD DOCUMENTS popup + in-page preview */\n.fileTypeChip { display: inline-flex; align-items: center; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; background: var(--orange-dim); border: 1px solid var(--orange-border); color: var(--orange); font-size: var(--fs-meta); font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; }\n.upFileList { display: flex; flex-direction: column; gap: 6px; max-height: clamp(140px, 30vh, 260px); overflow-y: auto; margin-bottom: 8px; }\n.upFileRow { display: flex; align-items: center; gap: 8px; min-width: 0; }\n.upFileName { flex: 1 1 50%; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: rgba(255,255,255,0.8); font-size: 12px; }\n.upFileSelect { flex: 1 1 50%; min-width: 0; }\n.upCatActions { display: flex; gap: 8px; }\n.upCatActions .upBtn { flex: 1; }\n.upBtn { display: flex; align-items: center; justify-content: center; width: 100%; padding: 8px; margin-top: 6px; border: 2px dashed var(--orange); color: var(--orange); font-size: var(--fs-meta); font-weight: 900; cursor: pointer; background: rgba(238,140,58,0.04); text-transform: uppercase; letter-spacing: 1px; border-radius: 4px; box-sizing: border-box; }\n.upBtn:hover:not(:disabled) { background: var(--orange-dim); border-style: solid; }\n.upBtn:disabled { opacity: 0.5; cursor: not-allowed; }\n.upErr { margin-top: 8px; padding: 8px 10px; border: 1px solid var(--red); border-radius: 4px; color: var(--red); font-size: var(--fs-meta); font-weight: 800; letter-spacing: 0.5px; }\n.previewFrame { width: min(80vw, 860px); height: 70vh; border: 0; background: #fff; border-radius: 4px; }\n.previewImg { display: block; max-width: min(80vw, 860px); max-height: 70vh; margin: 0 auto; object-fit: contain; }\n.notesWrap { display: flex; flex-direction: column; gap: 4px; }', "IntakePage.module.css: popup + preview styles")

patch(F_FOLDER_JSX, "    const handleOpenDoc = (filePath) => { if (!filePath) return; const url = getDocUrl(filePath); if (filePath.startsWith('http')) window.open(url, '_blank', 'noopener,noreferrer'); else fetch(url, { headers: { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } }).then(r => r.blob()).then(blob => { const b = URL.createObjectURL(blob); window.open(b, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(b), 30000); }).catch(() => window.open(url, '_blank', 'noopener,noreferrer')); };", "    // fix175: View opens the file in a tab as a typed blob so PDFs/images show in the browser instead of downloading\n    const handleOpenDoc = (filePath) => { if (!filePath) return; const url = getDocUrl(filePath); const isHttp = filePath.startsWith('http'); const ext = fileExt(filePath.split('?')[0]); const mime = { pdf: 'application/pdf', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' }[ext]; const w = window.open('', '_blank'); const go = (href, revoke) => { if (w) w.location.href = href; else window.open(href, '_blank'); if (revoke) setTimeout(() => URL.revokeObjectURL(href), 60000); }; fetch(url, { headers: isHttp ? {} : { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } }).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.blob(); }).then(blob => go(URL.createObjectURL(mime ? new Blob([blob], { type: mime }) : blob), true)).catch(() => go(url, false)); };", "FolderPage: View opens inline as typed blob")

patch(F_GUIDE, '- FOLDER PAGE LOOPHOLES CLOSED (fix166):', '- DOCUMENTS POPUP + VIEW (fix175): Intake file picking opens the SAME UPLOAD DOCUMENTS popup as the Folder page (category for all + per file + NEW CATEGORY); ADD puts the files in the Intake Documents box with their type shown as a tag (no inline picker). Files follow the Folder rules: PDF/JPG/PNG/WEBP, not empty, max 50 MB. Intake View opens an in-page preview (PDF in an iframe, images as <img>) from the local blob -- nothing downloads. Folder View (`handleOpenDoc`) fetches the file and opens it as a typed blob (application/pdf, image/*) so Cloudinary / vault files display instead of downloading; plain-link fallback if the fetch fails.\n- FOLDER PAGE LOOPHOLES CLOSED (fix166):', "Guide: documents popup + inline view (fix175)")

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