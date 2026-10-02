#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix177: FOLDER > Documents > View uses the Intake preview window; popup a bit smaller; X rotates like the others.
#
# WHAT CHANGES:
#   1. FOLDER page View (documents list + payment RECEIPT button): no more new browser tab. It opens the same preview window as Intake,
#      shaped to the document (portrait / landscape tag), Esc / X / click outside closes it.
#   2. Preview window (Folder AND Intake) is a bit smaller with a bigger screen margin, so it is never cut off at the bottom or sides.
#   3. The X in the preview now rotates on hover (same as every other popup); the window also fades/slides in like the others.
#   4. LLM_CONTEXT_GUIDE.md: records the above.
#
# NOT in this fix: backend, the upload popup.
#
# Atomic: every patch for every file is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix177"
COMMIT_MSG = "fix177: Folder documents open in the Intake-style preview window; preview window a bit smaller; X rotates like other popups"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

F_FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
F_FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")
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
LOAD_FILES = (F_FOLDER_JSX, F_FOLDER_CSS, F_INTAKE_CSS, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_FOLDER_JSX, r'''const handleOpenDoc = (filePath) => { if (!filePath) return; const url = getDocUrl(filePath); const isHttp = filePath.startsWith('http'); const ext = fileExt(filePath.split('?')[0]); const mime = { pdf: 'application/pdf', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' }[ext]; const w = window.open('', '_blank'); const go = (href, revoke) => { if (w) w.location.href = href; else window.open(href, '_blank'); if (revoke) setTimeout(() => URL.revokeObjectURL(href), 60000); }; fetch(url, { headers: isHttp ? {} : { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } }).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.blob(); }).then(blob => go(URL.createObjectURL(mime ? new Blob([blob], { type: mime }) : blob), true)).catch(() => go(url, false)); };''', r'''// fix177: View opens the Intake-style preview window (sized to the document, always on screen) instead of a new tab
    const [docPreview, setDocPreview] = useState(null);
    const docUrlRef = useRef(null);
    const closeDocPreview = () => { if (docUrlRef.current) { URL.revokeObjectURL(docUrlRef.current); docUrlRef.current = null; } setDocPreview(null); };
    useEffect(() => {
        if (!docPreview) return undefined;
        const onKey = (e) => { if (e.key === 'Escape') closeDocPreview(); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [docPreview]);
    useEffect(() => () => { if (docUrlRef.current) URL.revokeObjectURL(docUrlRef.current); }, []);
    const handleOpenDoc = async (filePath, fileName) => {
        if (!filePath) return;
        const url = getDocUrl(filePath);
        const isHttp = filePath.startsWith('http');
        const clean = filePath.split('?')[0];
        const ext = fileExt(clean);
        const mime = { pdf: 'application/pdf', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' }[ext];
        let name = fileName;
        if (!name) { try { name = decodeURIComponent(clean.split(/[\\/]/).pop() || 'Document'); } catch (e) { name = 'Document'; } }
        try {
            const r = await fetch(url, { headers: isHttp ? {} : { Authorization: 'Bearer ' + localStorage.getItem('gs_token') } });
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const raw = await r.blob();
            const blob = mime ? new Blob([raw], { type: mime }) : raw;
            const isPdf = ext === 'pdf' || blob.type === 'application/pdf';
            const isImg = !isPdf && String(blob.type || '').startsWith('image/');
            if (!isPdf && !isImg) { const o = URL.createObjectURL(blob); window.open(o, '_blank'); setTimeout(() => URL.revokeObjectURL(o), 60000); return; }
            const href = URL.createObjectURL(blob);
            let ratio = 0.707; // A4 portrait fallback
            try {
                if (isPdf) {
                    const txt = new TextDecoder('latin1').decode(await blob.slice(0, 3000000).arrayBuffer());
                    const mb = txt.match(/\/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]/);
                    if (mb) {
                        let w = Math.abs(mb[3] - mb[1]); let h = Math.abs(mb[4] - mb[2]);
                        const rot = txt.match(/\/Rotate\s+(-?\d+)/);
                        if (rot && Math.abs(parseInt(rot[1], 10)) % 180 === 90) { const t = w; w = h; h = t; }
                        if (w > 0 && h > 0) ratio = w / h;
                    }
                } else {
                    ratio = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im.naturalWidth / im.naturalHeight); im.onerror = rej; im.src = href; });
                }
            } catch (err) { /* keep the portrait default */ }
            ratio = Math.min(4, Math.max(0.25, ratio || 0.707));
            if (docUrlRef.current) URL.revokeObjectURL(docUrlRef.current);
            docUrlRef.current = href;
            setDocPreview({ name, url: href, isPdf, ratio });
        } catch (err) { window.open(url, '_blank'); }
    };''', 'FolderPage: View opens the in-app preview window (reads orientation, Esc closes)')

patch(F_FOLDER_JSX, r'''onClick={() => handleOpenDoc(receipt.filePath)}''', r'''onClick={() => handleOpenDoc(receipt.filePath, receipt.fileName)}''', 'FolderPage: receipt View passes the file name')

patch(F_FOLDER_JSX, r'''onClick={() => handleOpenDoc(doc.filePath)}''', r'''onClick={() => handleOpenDoc(doc.filePath, doc.fileName)}''', 'FolderPage: document View passes the file name')

patch(F_FOLDER_JSX, r'''            <HardwareModal isOpen={!!uploadDraft} lockBackdrop onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">
''', r'''            {docPreview && typeof document !== 'undefined' && createPortal(
                <div className={styles.pvOverlay} onClick={closeDocPreview} role="dialog" aria-modal="true" aria-label={docPreview.name}>
                    <div className={styles.pvPanel} onClick={e => e.stopPropagation()}>
                        <header className={styles.pvHead}>
                            <span className={styles.pvTitle} title={docPreview.name}>{docPreview.name}</span>
                            <span className={styles.pvTag}>{docPreview.ratio >= 1 ? 'Landscape' : 'Portrait'}</span>
                            <button type="button" className={styles.pvClose} onClick={closeDocPreview} aria-label="Close preview" title="Close"><FiX size={16} /></button>
                        </header>
                        <div className={styles.pvStage} style={{ '--pv-ratio': docPreview.ratio }}>
                            {docPreview.isPdf
                                ? <iframe className={styles.pvMedia} src={docPreview.url} title={docPreview.name} />
                                : <img className={`${styles.pvMedia} ${styles.pvImg}`} src={docPreview.url} alt={docPreview.name} />}
                        </div>
                    </div>
                </div>, document.body)}
            <HardwareModal isOpen={!!uploadDraft} lockBackdrop onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">
''', 'FolderPage: preview window markup (same as Intake)')

patch(F_FOLDER_CSS, r'''.callWhen { grid-area: when; color: rgba(255, 255, 255, 0.45); font-size: clamp(9px, 0.9vw, 11px); white-space: nowrap; }
''', r'''.callWhen { grid-area: when; color: rgba(255, 255, 255, 0.45); font-size: clamp(9px, 0.9vw, 11px); white-space: nowrap; }

/* fix177: preview window (same look as Intake) -- a bit smaller so it never touches the screen edge; X rotates like every other popup */
.pvOverlay { animation: pvFade 0.2s ease-out; position: fixed; inset: 0; z-index: 99999; display: flex; align-items: center; justify-content: center; padding: 24px; box-sizing: border-box; background: rgba(10, 20, 25, 0.85); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.pvPanel { animation: pvSlide 0.25s cubic-bezier(0.2, 1, 0.3, 1); display: flex; flex-direction: column; gap: 10px; max-width: 100%; max-height: 100%; padding: 12px; box-sizing: border-box; overflow: auto; scrollbar-width: none; background: linear-gradient(160deg, #1c3335 0%, #213e40 100%); border: 2px solid rgba(238, 140, 58, 0.4); border-radius: 14px; box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7); }
.pvPanel::-webkit-scrollbar { display: none; }
.pvHead { display: flex; align-items: center; gap: 10px; min-width: 0; padding-bottom: 8px; border-bottom: 1px solid rgba(238, 140, 58, 0.25); }
.pvTitle { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: 'Cinzel', serif; color: var(--orange, #EE8C3A); font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }
.pvTag { flex-shrink: 0; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.15); border-radius: 4px; padding: 2px 7px; }
.pvClose { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; cursor: pointer; color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; transition: all 0.2s; }
.pvClose:hover { color: #ef4444; border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.15); transform: rotate(90deg); }
.pvStage { position: relative; flex-shrink: 0; width: max(240px, min(calc(100vw - 96px), calc((100vh - 220px) * var(--pv-ratio, 0.707)))); aspect-ratio: var(--pv-ratio, 0.707); background: #fff; border-radius: 4px; overflow: hidden; }
.pvMedia { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; display: block; }
.pvImg { object-fit: contain; background: #0f1f21; }
@keyframes pvFade { from { opacity: 0; } to { opacity: 1; } }
@keyframes pvSlide { from { opacity: 0; transform: translateY(20px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }
''', 'FolderPage.module.css: preview window styles')

patch(F_INTAKE_CSS, r'''.pvOverlay { position: fixed; inset: 0; z-index: 99999; display: flex; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; background: rgba(10, 20, 25, 0.85); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.pvPanel { display: flex; flex-direction: column; gap: 10px; max-width: 100%; max-height: 100%; padding: 12px; box-sizing: border-box; overflow: auto; background: linear-gradient(160deg, #1c3335 0%, #213e40 100%); border: 2px solid rgba(238, 140, 58, 0.4); border-radius: 14px; box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7); }''', r'''.pvOverlay { animation: pvFade 0.2s ease-out; position: fixed; inset: 0; z-index: 99999; display: flex; align-items: center; justify-content: center; padding: 24px; box-sizing: border-box; background: rgba(10, 20, 25, 0.85); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.pvPanel { animation: pvSlide 0.25s cubic-bezier(0.2, 1, 0.3, 1); display: flex; flex-direction: column; gap: 10px; max-width: 100%; max-height: 100%; padding: 12px; box-sizing: border-box; overflow: auto; background: linear-gradient(160deg, #1c3335 0%, #213e40 100%); border: 2px solid rgba(238, 140, 58, 0.4); border-radius: 14px; box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7); }''', 'IntakePage.module.css: preview window fade/slide-in + more screen margin')

patch(F_INTAKE_CSS, r'''.pvClose { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; cursor: pointer; color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; }
.pvClose:hover { color: #ef4444; border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.15); }
.pvStage { position: relative; flex-shrink: 0; width: max(260px, min(calc(100vw - 72px), calc((100vh - 150px) * var(--pv-ratio, 0.707)))); aspect-ratio: var(--pv-ratio, 0.707); background: #fff; border-radius: 4px; overflow: hidden; }''', r'''.pvClose { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; cursor: pointer; color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; transition: all 0.2s; }
.pvClose:hover { color: #ef4444; border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.15); transform: rotate(90deg); }
.pvStage { position: relative; flex-shrink: 0; width: max(240px, min(calc(100vw - 96px), calc((100vh - 220px) * var(--pv-ratio, 0.707)))); aspect-ratio: var(--pv-ratio, 0.707); background: #fff; border-radius: 4px; overflow: hidden; }''', 'IntakePage.module.css: X rotates on hover like other popups; preview a bit smaller')

patch(F_INTAKE_CSS, r'''.pvImg { object-fit: contain; background: #0f1f21; }''', r'''.pvImg { object-fit: contain; background: #0f1f21; }
@keyframes pvFade { from { opacity: 0; } to { opacity: 1; } }
@keyframes pvSlide { from { opacity: 0; transform: translateY(20px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }''', 'IntakePage.module.css: preview keyframes')

patch(F_GUIDE, r'''- FOLDER PAGE LOOPHOLES CLOSED (fix166):''', r'''- FOLDER DOCUMENT PREVIEW (fix177): Folder page View (documents list + payment RECEIPT button) no longer opens a browser tab. `handleOpenDoc(filePath, fileName)` in FolderPage.jsx fetches the file with the auth token as a typed blob, reads its shape (image size / PDF /MediaBox + /Rotate) and shows the SAME preview window as Intake (`pvOverlay/pvPanel/pvStage`, now duplicated in FolderPage.module.css). Esc, the X or a click outside closes it and frees the blob URL. Non-PDF/non-image files still open in a new tab; a failed fetch falls back to opening the URL directly. Both previews (Folder + Intake) are now a bit smaller (stage width = min(100vw-96px, (100vh-220px)*ratio), 24px screen margin), fade/slide in like HardwareModal, and the X rotates 90 degrees on hover like every other popup X.
- FOLDER PAGE LOOPHOLES CLOSED (fix166):''', 'Guide: folder document preview (fix177)')

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