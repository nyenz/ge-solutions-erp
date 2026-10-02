#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix176: INTAKE > Documents > View now follows the document's orientation and is never cut off.
#
# WHAT CHANGES:
#   1. INTAKE View: the old preview sat inside the 520px popup but forced the file to 80vw wide, so it was clipped on the right
#      and bottom. It now opens its own preview window.
#   2. The window reads the file first: images by their pixel size, PDFs by their page size (and rotation). Portrait files open
#      as a tall window, landscape files as a wide one. The tag in the title bar says which.
#   3. The window is capped to the screen (width and height), so the whole document is always visible -- no cropping, no page scroll.
#   4. Esc, the X, or clicking outside closes it. Nothing is downloaded, no new tab.
#   5. LLM_CONTEXT_GUIDE.md: records the above.
#
# NOT in this fix: backend, the Folder page View, the upload popup.
#
# Atomic: every patch for every file is matched in memory first; if any one is MISSING nothing is written and nothing is committed.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
FIX_NO = "fix176"
COMMIT_MSG = "fix176: Intake document preview follows the document orientation and fits the screen"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

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
LOAD_FILES = (F_INTAKE_JSX, F_INTAKE_CSS, F_GUIDE,)
for _p in LOAD_FILES:
    load(_p)

patch(F_INTAKE_JSX, r'''    const [previewFile, setPreviewFile] = useState(null);
''', r'''    const [previewFile, setPreviewFile] = useState(null);
    // fix176: preview window is sized to the document (portrait / landscape) and always fits the screen
    const openPreview = async (f) => {
        const isPdf = fileExt(f.name) === 'pdf';
        let ratio = 0.707; // A4 portrait fallback
        try {
            if (isPdf) {
                const txt = new TextDecoder('latin1').decode(await f.file.arrayBuffer());
                const mb = txt.match(/\/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]/);
                if (mb) {
                    let w = Math.abs(mb[3] - mb[1]); let h = Math.abs(mb[4] - mb[2]);
                    const rot = txt.match(/\/Rotate\s+(-?\d+)/);
                    if (rot && Math.abs(parseInt(rot[1], 10)) % 180 === 90) { const t = w; w = h; h = t; }
                    if (w > 0 && h > 0) ratio = w / h;
                }
            } else {
                ratio = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im.naturalWidth / im.naturalHeight); im.onerror = rej; im.src = f.url; });
            }
        } catch (err) { /* keep the portrait default */ }
        ratio = Math.min(4, Math.max(0.25, ratio || 0.707));
        setPreviewFile({ ...f, isPdf, ratio });
    };
    useEffect(() => {
        if (!previewFile) return undefined;
        const onKey = (e) => { if (e.key === 'Escape') setPreviewFile(null); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [previewFile]);
''', 'IntakePage: openPreview (reads document orientation) + Esc to close')

patch(F_INTAKE_JSX, r'''onClick={() => setPreviewFile(f)} aria-label={`View ${f.name}`}''', r'''onClick={() => openPreview(f)} aria-label={`View ${f.name}`}''', 'IntakePage: View button uses openPreview')

patch(F_INTAKE_JSX, r'''            <HardwareModal isOpen={!!previewFile} onClose={() => setPreviewFile(null)} title={previewFile ? previewFile.name : ''}>
                {previewFile && (fileExt(previewFile.name) === 'pdf'
                    ? <iframe className={styles.previewFrame} src={previewFile.url} title={previewFile.name} />
                    : <img className={styles.previewImg} src={previewFile.url} alt={previewFile.name} />)}
            </HardwareModal>
''', r'''            {previewFile && typeof document !== 'undefined' && createPortal(
                <div className={styles.pvOverlay} onClick={() => setPreviewFile(null)} role="dialog" aria-modal="true" aria-label={previewFile.name}>
                    <div className={styles.pvPanel} onClick={e => e.stopPropagation()}>
                        <header className={styles.pvHead}>
                            <span className={styles.pvTitle} title={previewFile.name}>{previewFile.name}</span>
                            <span className={styles.pvTag}>{previewFile.ratio >= 1 ? 'Landscape' : 'Portrait'}</span>
                            <button type="button" className={styles.pvClose} onClick={() => setPreviewFile(null)} aria-label="Close preview" title="Close"><FiX size={16} /></button>
                        </header>
                        <div className={styles.pvStage} style={{ '--pv-ratio': previewFile.ratio }}>
                            {previewFile.isPdf
                                ? <iframe className={styles.pvMedia} src={previewFile.url} title={previewFile.name} />
                                : <img className={`${styles.pvMedia} ${styles.pvImg}`} src={previewFile.url} alt={previewFile.name} />}
                        </div>
                    </div>
                </div>, document.body)}
''', 'IntakePage: preview window (own overlay, fits the screen, follows orientation)')

patch(F_INTAKE_CSS, r'''.previewFrame { width: min(80vw, 860px); height: 70vh; border: 0; background: #fff; border-radius: 4px; }
.previewImg { display: block; max-width: min(80vw, 860px); max-height: 70vh; margin: 0 auto; object-fit: contain; }
''', r'''/* fix176: preview window -- the stage takes the document's own shape (--pv-ratio = width / height) and is capped to the screen, so nothing is cut off */
.pvOverlay { position: fixed; inset: 0; z-index: 99999; display: flex; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; background: rgba(10, 20, 25, 0.85); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.pvPanel { display: flex; flex-direction: column; gap: 10px; max-width: 100%; max-height: 100%; padding: 12px; box-sizing: border-box; overflow: auto; background: linear-gradient(160deg, #1c3335 0%, #213e40 100%); border: 2px solid rgba(238, 140, 58, 0.4); border-radius: 14px; box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7); }
.pvHead { display: flex; align-items: center; gap: 10px; min-width: 0; padding-bottom: 8px; border-bottom: 1px solid rgba(238, 140, 58, 0.25); }
.pvTitle { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: 'Cinzel', serif; color: var(--orange, #EE8C3A); font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }
.pvTag { flex-shrink: 0; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.15); border-radius: 4px; padding: 2px 7px; }
.pvClose { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; cursor: pointer; color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; }
.pvClose:hover { color: #ef4444; border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.15); }
.pvStage { position: relative; flex-shrink: 0; width: max(260px, min(calc(100vw - 72px), calc((100vh - 150px) * var(--pv-ratio, 0.707)))); aspect-ratio: var(--pv-ratio, 0.707); background: #fff; border-radius: 4px; overflow: hidden; }
.pvMedia { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; display: block; }
.pvImg { object-fit: contain; background: #0f1f21; }
''', 'IntakePage.module.css: preview window styles (replace fixed 80vw/70vh box)')

patch(F_GUIDE, r'''- FOLDER PAGE LOOPHOLES CLOSED (fix166):''', r'''- INTAKE PREVIEW SIZING (fix176): the Intake Documents View no longer uses HardwareModal (its 520px cap clipped the file). `openPreview` in IntakePage.jsx reads the document shape first (image: naturalWidth/naturalHeight; PDF: /MediaBox + /Rotate from the file bytes, portrait A4 if unreadable) and opens its own overlay (`pvOverlay/pvPanel/pvStage` in IntakePage.module.css). The stage uses `aspect-ratio: var(--pv-ratio)` and is capped to the viewport (width = min(100vw-72px, (100vh-150px)*ratio)), so portrait and landscape files both fit fully on screen. Esc, the X, or a click outside closes it.
- FOLDER PAGE LOOPHOLES CLOSED (fix166):''', 'Guide: intake preview sizing (fix176)')

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