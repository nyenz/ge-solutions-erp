#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix179: ONE shared document section design for the Folder page and the Intake page.
#
# WHAT CHANGES:
#   1. New shared component components/common/DocParts.jsx (+ DocParts.module.css): DocList, DocGroup, DocRow, DocDropzone.
#   2. Folder > Documents: rows lose the white name bar (the name is plain text on the row plane), get the Intake View button
#      (opens the existing preview window) and the outlined delete button; grouped by type as before. The "+ ADD SCANS" button
#      becomes the Intake upload zone: tall when empty, slim "Add more documents" bar once files exist.
#      Read-only folders (no upload right / deleted) keep the plain "NO DOCUMENTS ATTACHED" panel.
#   3. Intake > Documents: queued files use the same rows and are grouped by type; same upload zone (required mark kept).
#   4. Print: Folder keeps its light print look for the document rows; buttons and the upload zone are hidden on print.
#
# NOT in this fix: backend, LLM_CONTEXT_GUIDE.md, the old dropzone CSS in IntakePage.module.css (now unused). Needs fix178 applied first.
#
# Atomic: every patch for every file is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix179"
COMMIT_MSG = "fix179: Shared document design on Folder and Intake (View button, plain name, type groups, Intake upload zone)"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

F_FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
F_FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")
F_INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
F_DOCPARTS_JSX = os.path.join(SRC, "components", "common", "DocParts.jsx")
F_DOCPARTS_CSS = os.path.join(SRC, "components", "common", "DocParts.module.css")
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
LOAD_FILES = (F_FOLDER_JSX, F_FOLDER_CSS, F_INTAKE_JSX,)
for _p in LOAD_FILES:
    load(_p)

newfile(F_DOCPARTS_JSX, r'''// PATH: erp-frontend/src/components/common/DocParts.jsx
// fix179: ONE shared document section design for the Folder page and the Intake page.
//   DocList     the dark inset plane that holds the groups (Folder look)
//   DocGroup    orange uppercase type heading + count (Folder look)
//   DocRow      icon, plain name (no white bar), meta, View (Intake look), delete / LOCKED
//   DocDropzone big upload zone when empty, slim "Add more documents" bar once files exist (Intake look)
// Pages pass their own copy-in props only; the look lives here so the two pages can never drift apart again.
import React from 'react';
import { FiFileText, FiEye, FiTrash2, FiUploadCloud } from 'react-icons/fi';
import s from './DocParts.module.css';

export function DocList({ capped = false, className = '', children }) {
    return <div className={`${s.list} ${capped ? s.listCapped : ''} ${className}`.trim()}>{children}</div>;
}

export function DocGroup({ label, count, children }) {
    return (
        <>
            <div className={s.groupLabel}>{label}{count != null && <span className={s.groupCount}>{count}</span>}</div>
            {children}
        </>
    );
}

export function DocRow({ name, meta, metaTitle, onView, onDelete, deleteTitle, locked = false, lockTitle, className = '' }) {
    return (
        <div className={`${s.row} ${className}`.trim()}>
            <FiFileText className={s.icon} aria-hidden="true" />
            <span className={s.name} title={name}>{name}</span>
            {meta ? <span className={s.meta} title={metaTitle}>{meta}</span> : null}
            <span className={s.actions}>
                <button type="button" className={s.btn} onClick={onView} aria-label={'View ' + name} title={'View ' + name}>
                    <FiEye size={12} aria-hidden="true" /> View
                </button>
                {onDelete && (
                    <button type="button" className={`${s.btn} ${s.btnDel}`} onClick={onDelete} aria-label={'Delete ' + name} title={deleteTitle || 'Delete this document'}>
                        <FiTrash2 size={12} aria-hidden="true" />
                    </button>
                )}
                {locked && <span className={s.lock} title={lockTitle}>LOCKED</span>}
            </span>
        </div>
    );
}

export function DocDropzone({ compact = false, required = false, onClick, className = '', title }) {
    const act = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick && onClick(); } };
    return (
        <div className={`${s.zone} ${compact ? s.zoneCompact : ''} ${className}`.trim()} onClick={onClick} onKeyDown={act} role="button" tabIndex={0} title={title}>
            <span className={s.zoneIcon}><FiUploadCloud size={compact ? 13 : 18} aria-hidden="true" /></span>
            {compact ? (
                <span className={s.zoneTitle}>Add more documents</span>
            ) : (
                <>
                    <span className={s.zoneTitle}>Click to upload{required && <span className={s.req}>*</span>}</span>
                    <span className={s.zoneSub}>{required ? 'Required - ' : ''}PDF, JPG, PNG or WEBP, up to 50 MB each</span>
                </>
            )}
        </div>
    );
}
''', 'components/common/DocParts.jsx', 'fix179')

newfile(F_DOCPARTS_CSS, r'''/* PATH: erp-frontend/src/components/common/DocParts.module.css */
/* fix179: shared document section look (Folder + Intake). Literal sizes (not page variables) so both pages render it identically.
   Accent follows the page: var(--orange) with an orange fallback. */
.list { display: flex; flex-direction: column; gap: clamp(5px, 0.8vw, 8px); background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.10); border-radius: 8px; padding: clamp(10px, 1.4vw, 14px); margin-bottom: clamp(6px, 0.9vw, 10px); box-sizing: border-box; }
.listCapped { max-height: clamp(140px, 22vw, 200px); overflow-y: auto; }
.listCapped::-webkit-scrollbar { width: 4px; }
.listCapped::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.listCapped::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 4px; }

.groupLabel { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: clamp(4px, 0.6vw, 8px); padding: 0 2px; font-family: 'Space Mono', monospace; font-weight: 900; font-size: clamp(8px, 0.85vw, 10px); letter-spacing: 1.5px; text-transform: uppercase; color: var(--orange, #EE8C3A); }
.groupLabel:first-child { margin-top: 0; }
.groupCount { color: rgba(255,255,255,0.35); }

.row { display: flex; align-items: center; gap: clamp(7px, 1vw, 10px); width: 100%; min-width: 0; box-sizing: border-box; background: rgba(255,255,255,0.07); border: 1px solid var(--orange-border, rgba(238,140,58,0.28)); border-radius: 6px; padding: clamp(7px, 1vw, 10px) clamp(10px, 1.3vw, 13px); transition: border-color 0.2s, background 0.2s; }
.row:hover { border-color: var(--orange, #EE8C3A); background: var(--orange-dim, rgba(238,140,58,0.18)); }
.icon { color: var(--orange, #EE8C3A); font-size: clamp(13px, 1.5vw, 16px); flex-shrink: 0; }
/* plain text on the row plane: no button chrome, no white bar */
.name { flex: 1; min-width: 0; color: #fff; font-family: 'Inter', sans-serif; font-size: clamp(10px, 1.05vw, 12px); font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: transparent; border: none; padding: 0; }
.meta { flex-shrink: 0; color: rgba(255,255,255,0.4); font-size: clamp(8px, 0.85vw, 10px); font-weight: 700; white-space: nowrap; }
.actions { display: flex; align-items: center; gap: clamp(5px, 0.9vw, 10px); flex-shrink: 0; }

.btn { font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px); font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; padding: clamp(4px, 0.7vw, 7px) clamp(8px, 1.1vw, 12px); border-radius: 6px; border: 1.5px solid rgba(255,255,255,0.1); background: transparent; color: rgba(255,255,255,0.7); cursor: pointer; transition: background 0.2s, border-color 0.2s, color 0.2s; display: inline-flex; align-items: center; gap: 5px; text-decoration: none; }
.btn:hover { background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.22); color: #fff; }
.btn:focus-visible { outline: 2px solid var(--orange, #EE8C3A); outline-offset: 2px; }
.btnDel { border-color: rgba(239,68,68,0.3); color: rgba(239,68,68,0.7); }
.btnDel:hover { background: rgba(239,68,68,0.15); border-color: #ef4444; color: #ef4444; }
.lock { font-size: clamp(7px, 0.75vw, 9px); font-weight: 900; letter-spacing: 1px; color: rgba(255,255,255,0.45); border: 1px dashed rgba(255,255,255,0.25); border-radius: 4px; padding: 1px 6px; cursor: help; }

/* upload zone (moved here from the Intake page so both pages share it) */
.zone { border: 2px dashed rgba(238,140,58,0.4); border-radius: 10px; padding: clamp(12px, 1.6vw, 18px); text-align: center; color: rgba(255,255,255,0.55); cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; align-items: center; gap: 4px; box-sizing: border-box; width: 100%; }
.zone:hover { background: var(--orange-dim, rgba(238,140,58,0.18)); border-color: var(--orange, #EE8C3A); color: var(--orange, #EE8C3A); }
.zone:focus-visible { outline: 2px solid var(--orange, #EE8C3A); outline-offset: 2px; }
.zoneIcon { width: clamp(34px, 4vw, 44px); height: clamp(34px, 4vw, 44px); border-radius: 50%; background: rgba(238,140,58,0.12); border: 1px solid var(--orange-border, rgba(238,140,58,0.28)); display: flex; align-items: center; justify-content: center; color: var(--orange, #EE8C3A); margin-bottom: 2px; }
.zoneTitle { font-family: 'Inter', sans-serif; font-weight: 800; font-size: clamp(10px, 1.05vw, 12px); letter-spacing: 1px; text-transform: uppercase; }
.req { color: #ef4444; margin-left: 3px; }
.zoneSub { font-size: clamp(8px, 0.85vw, 10px); color: rgba(255,255,255,0.35); font-weight: 700; letter-spacing: 0.5px; }
.zoneCompact { flex-direction: row; justify-content: center; gap: 8px; padding: 6px 12px; }
.zoneCompact .zoneIcon { width: 24px; height: 24px; margin-bottom: 0; }
.zoneCompact .zoneTitle { font-size: clamp(8px, 0.85vw, 10px); }

@media (max-width: 560px) {
  .row { flex-wrap: wrap; }
  .name { flex-basis: calc(100% - 40px); }
  .actions { margin-left: auto; }
}
''', 'components/common/DocParts.module.css', 'fix179')

patch(F_FOLDER_JSX, r'''import CornerDecor from '../../components/ui/CornerDecor';''', r'''import CornerDecor from '../../components/ui/CornerDecor';
import { DocList, DocGroup, DocRow, DocDropzone } from '../../components/common/DocParts';''', 'FolderPage: import shared document parts')

patch(F_FOLDER_JSX, r'''{docCount === 0 ? (<div className={styles.emptyState}><FiUploadCloud className={styles.emptyIcon} aria-hidden="true" /><span>NO DOCUMENTS ATTACHED</span></div>) : (
                            <div className={styles.compactVault}>{docGroups.map(([cat, docs]) => (<React.Fragment key={cat}><div className={styles.docGroupLabel}>{cat === UNCATEGORISED ? 'UNCATEGORISED' : catLabel(cat)}<span className={styles.docGroupCount}>{docs.length}</span></div>{docs.map((doc) => (<div key={doc.id} className={styles.docTag}>
                                <FiFileText className={styles.docIcon} aria-hidden="true" />
                                <button type="button" className={styles.docName} onClick={() => handleOpenDoc(doc.filePath, doc.fileName)} title={'Open ' + doc.fileName}>{doc.fileName}</button>
                                <span className={styles.docMeta} title="Uploaded by / on">{doc.uploadedBy || '---'}{doc.uploadedAt ? ' - ' + fmtDate(doc.uploadedAt) : ''}</span>
                                {canEdit && !isReleased && doc.category !== 'PAYMENT_RECEIPT' && <button type="button" className={styles.iconBtn} onClick={() => handleDeleteDoc(doc.id, doc.fileName)} title="Delete this document" aria-label={'Delete ' + doc.fileName}><FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>}
                                {doc.category === 'PAYMENT_RECEIPT' && <span className={styles.lockTag} title="A payment receipt is proof of money received and can never be deleted. Reverse the payment instead.">LOCKED</span>}
                            </div>))}</React.Fragment>))}</div>)}
                        {canUploadDocs && !isDeleted && <button type="button" className={styles.addDocBtn} onClick={() => fileInputRef.current?.click()} title="Add scans (PDF, JPG, PNG or WEBP, up to 50 MB each). You pick a category for each file.">+ ADD SCANS</button>}''', r'''{docCount === 0 ? ((canUploadDocs && !isDeleted)
                            ? <DocDropzone className={styles.docPrintHide} onClick={() => fileInputRef.current?.click()} title="Add scans (PDF, JPG, PNG or WEBP, up to 50 MB each). You pick a category for each file." />
                            : <div className={styles.emptyState}><FiUploadCloud className={styles.emptyIcon} aria-hidden="true" /><span>NO DOCUMENTS ATTACHED</span></div>) : (
                            <>
                                <DocList className={styles.compactVault}>{docGroups.map(([cat, docs]) => (
                                    <DocGroup key={cat} label={cat === UNCATEGORISED ? 'UNCATEGORISED' : catLabel(cat)} count={docs.length}>
                                        {docs.map((doc) => (
                                            <DocRow key={doc.id} className={styles.docPrintRow} name={doc.fileName}
                                                meta={(doc.uploadedBy || '---') + (doc.uploadedAt ? ' - ' + fmtDate(doc.uploadedAt) : '')} metaTitle="Uploaded by / on"
                                                onView={() => handleOpenDoc(doc.filePath, doc.fileName)}
                                                onDelete={(canEdit && !isReleased && doc.category !== 'PAYMENT_RECEIPT') ? () => handleDeleteDoc(doc.id, doc.fileName) : undefined}
                                                locked={doc.category === 'PAYMENT_RECEIPT'} lockTitle="A payment receipt is proof of money received and can never be deleted. Reverse the payment instead." />
                                        ))}
                                    </DocGroup>))}
                                </DocList>
                                {canUploadDocs && !isDeleted && <DocDropzone compact className={styles.docPrintHide} onClick={() => fileInputRef.current?.click()} title="Add scans (PDF, JPG, PNG or WEBP, up to 50 MB each). You pick a category for each file." />}
                            </>)}''', 'FolderPage: Documents drawer uses the shared rows, groups and upload zone')

patch(F_FOLDER_CSS, r'''/* related projects + documents + notes */''', r'''/* related projects + documents + notes */
/* fix179: print hooks for the shared document rows (DocParts) */
@media print {
  .docPrintRow { background: #f0f0f0 !important; border: 1px solid #ccc !important; border-radius: 0 !important; padding: 4px 8px !important; page-break-inside: avoid !important; }
  .docPrintRow span, .docPrintRow svg { color: #000 !important; }
  .docPrintRow button { display: none !important; }
  .docPrintHide { display: none !important; }
}''', 'FolderPage.module.css: print hooks for the shared document rows')

patch(F_INTAKE_JSX, r'''FiEdit3, FiBookmark, FiX, FiCopy, FiFile, FiEye, FiRefreshCw, FiCalendar''', r'''FiEdit3, FiBookmark, FiX, FiCopy, FiRefreshCw, FiCalendar''', 'IntakePage: drop the icons the shared rows replace')

patch(F_INTAKE_JSX, r'''import styles from './IntakePage.module.css';''', r'''import { DocList, DocGroup, DocRow, DocDropzone } from '../../components/common/DocParts';
import styles from './IntakePage.module.css';''', 'IntakePage: import shared document parts')

patch(F_INTAKE_JSX, r'''    const catLabelOf = (code) => { const c = docCats.find(x => x.code === code); return c ? c.label : ''; };''', r'''    const catLabelOf = (code) => { const c = docCats.find(x => x.code === code); return c ? c.label : ''; };
    // fix179: queued files grouped by document type (same grouping as the Folder page), keeping each file's queue index
    const queueGroups = (() => {
        const g = new Map();
        fileQueue.forEach((f, i) => { const k = f.category || '__NONE__'; if (!g.has(k)) g.set(k, []); g.get(k).push({ f, i }); });
        const rank = (k) => { if (k === '__NONE__') return 9999; const x = docCats.findIndex(c => c.code === k); return x < 0 ? 9000 : x; };
        return [...g.entries()].sort((p, q) => rank(p[0]) - rank(q[0]));
    })();''', 'IntakePage: group queued files by document type')

patch(F_INTAKE_JSX, r'''{fileQueue.length > 0 && (
                            <div className={styles.fileList}>
                                {fileQueue.map((f, i) => (
                                    <div key={i} className={styles.fileItem}>
                                        <span className={styles.fileMeta}>
                                            <FiFile className={styles.fileIcon} size={14} />
                                            <span className={styles.fileName}>{f.name}</span>
                                            <span className={styles.fileSize}>{fmtSize(f.size)}</span>
                                        </span>
                                        <span className={styles.fileActions}>
                                            <span className={styles.fileTypeChip}>{catLabelOf(f.category) || 'No type'}</span>
                                            <button type="button" className={`${styles.btn} ${styles.small}`} onClick={() => openPreview(f)} aria-label={`View ${f.name}`}>
                                                <FiEye size={12} /> View
                                            </button>
                                            <button type="button" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`} onClick={() => removeFile(i)} aria-label={`Remove ${f.name}`}>
                                                <FiTrash2 size={12} />
                                            </button>
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                        <div className={`${styles.dropzone} ${fileQueue.length > 0 ? styles.dropzoneCompact : ''}`} onClick={triggerFileInput} role="button" tabIndex={0}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); } }}>
                            <span className={styles.dropzoneIcon}><FiUploadCloud size={fileQueue.length > 0 ? 13 : 18} /></span>
                            {fileQueue.length > 0 ? (
                                <span className={styles.dropzoneTitle}>Add more documents</span>
                            ) : (
                                <>
                                    <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>
                                    <span className={styles.dropzoneSub}>Required - PDF, JPG, PNG or WEBP, up to 50 MB each</span>
                                </>
                            )}
                        </div>''', r'''{fileQueue.length > 0 && (
                            <DocList>
                                {queueGroups.map(([cat, items]) => (
                                    <DocGroup key={cat} label={cat === '__NONE__' ? 'NO TYPE' : (catLabelOf(cat) || cat)} count={items.length}>
                                        {items.map(({ f, i }) => (
                                            <DocRow key={i} name={f.name} meta={fmtSize(f.size)} onView={() => openPreview(f)} onDelete={() => removeFile(i)} deleteTitle={'Remove ' + f.name} />
                                        ))}
                                    </DocGroup>
                                ))}
                            </DocList>
                        )}
                        <DocDropzone compact={fileQueue.length > 0} required onClick={triggerFileInput} />''', 'IntakePage: Documents section uses the shared rows, groups and upload zone')

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