#!/usr/bin/env python3
# PATH: fix131.py
# GOLDEN SEED -- fix131: FOLDER PAGE / PLOT DETAILS re-organised onto the
#   Settings page's dataset-card language (fix121/fix127), plus one real
#   functionality gain: click-to-copy on every read-only value.
#     1. ORGANISATION -- PLOT DETAILS used to be one flat run of six
#        location fields followed by (sometimes) four title fields, with
#        no label separating the two groups. It's now two named, bounded
#        cream mini-cards -- LOCATION and TITLE -- the exact
#        prefGroupBox/prefGroupLabel construction Settings' Appearance
#        panel uses to split Display/Interaction/Notifications, right
#        down to the 2px accent-colour heading rule. LOCATION keeps the
#        panel's own orange; TITLE gets cyan, so the two clusters are
#        distinguishable at a glance the way Settings' own tabs are.
#     2. DESIGN -- specItem's left-edge accent, dropped to `none` by an
#        earlier unify pass, comes back at low opacity (rgba(26,46,48,.18))
#        against the cream card specifically, echoing the per-group
#        left-edge tinting the SIGNALS dropdown (fix130) and Settings'
#        own bounded rows already use. Values sit in navy-on-cream, not
#        white-on-cream, for correct contrast on the new light card.
#     3. FUNCTIONALITY -- every value in the new LOCATION/TITLE cards
#        (district, plot ID, title ID, etc.) gets a small copy icon that
#        appears on row hover; clicking copies the raw value to the
#        clipboard and fires the existing toast system. Small thing, but
#        Title ID and Plot ID are exactly the strings staff re-type into
#        other systems all day.
#
# Surgical find/replace against known-good source text, not a full
# rewrite. Runs `npm run build` before committing if node_modules is
# installed and refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")


def apply_patches(path, patches):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    rel = os.path.relpath(path, ROOT)
    applied = 0
    for old, new, desc in patches:
        if old not in text:
            if new and new in text:
                print("skip: " + rel + " -- '" + desc + "' already applied")
            else:
                print("WARN: " + rel + " -- '" + desc + "' did not match expected text, check manually")
            continue
        text = text.replace(old, new, 1)
        applied += 1

    if applied:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("written: " + rel + " (" + str(applied) + "/" + str(len(patches)) + " patch(es) applied)")
    else:
        print("skip: " + rel + " -- no patches applied")
    return applied


# ═══ FolderPage.jsx ═══
apply_patches(FOLDER_JSX, [
    (
        # 1. FiCopy for the new copy-to-clipboard affordance.
        "    FiDollarSign, FiActivity, FiHome, FiArchive,\n"
        "FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp\n"
        "} from 'react-icons/fi';",

        "    FiDollarSign, FiActivity, FiHome, FiArchive,\n"
        "FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp, FiCopy\n"
        "} from 'react-icons/fi';",

        "FiCopy import added",
    ),
    (
        # 2. one shared copy handler, dropped next to the other
        # single-purpose handlers so it's easy to find.
        "    const handleToggleProblem = async () => { const was = project.problem; let note = ''; if (!was) { note = window.prompt('Describe the problem (optional):') || ''; } try { await folderPortalService.toggleProblem(id, note); if (!was && note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };",

        "    const handleToggleProblem = async () => { const was = project.problem; let note = ''; if (!was) { note = window.prompt('Describe the problem (optional):') || ''; } try { await folderPortalService.toggleProblem(id, note); if (!was && note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };\n"
        "    const handleCopySpec = (value, label) => { if (!value) return; navigator.clipboard?.writeText(String(value)).then(() => toast(label + ' copied', 'success', 1500)).catch(() => toast('Copy failed', 'error')); };",

        "handleCopySpec handler added",
    ),
    (
        # 3. the flat two-grid layout becomes two named, bounded
        # LOCATION / TITLE cards, each row gaining a copy button.
        "                        </>) : (<>\n"
        "                            <div className={styles.readOnlyGrid}>\n"
        "                                {[['DISTRICT', project.district], ['COUNTY', project.county], ['SUB-COUNTY', project.subCounty], ['PARISH', project.parish], ['VILLAGE', project.village], ['AREA', project.area]].map(([l, v], i) => (\n"
        "                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}\n"
        "                            </div>\n"
        "                            {project.landTitle && (<div className={styles.readOnlyGrid}>\n"
        "                                {[['PLOT ID', project.landTitle.plotNumber], ['TENURE', project.landTitle.tenure], ['TITLE ID', project.landTitle.titleId], ['BLOCK / ROAD', project.landTitle.blockRoad]].map(([l, v], i) => (\n"
        "                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}\n"
        "                            </div>)}\n"
        "                        </>)}",

        "                        </>) : (<>\n"
        "                            <div className={styles.plotGroupsGrid}>\n"
        "                                <div className={styles.plotGroupBox} data-accent=\"orange\">\n"
        "                                    <div className={styles.plotGroupLabel}>LOCATION</div>\n"
        "                                    <div className={styles.readOnlyGrid}>\n"
        "                                        {[['DISTRICT', project.district], ['COUNTY', project.county], ['SUB-COUNTY', project.subCounty], ['PARISH', project.parish], ['VILLAGE', project.village], ['AREA', project.area]].map(([l, v], i) => (\n"
        "                                            <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValueRow}><span className={styles.specValue}>{v || '---'}</span>{v && <button type=\"button\" className={styles.copyBtn} onClick={() => handleCopySpec(v, l)} aria-label={`Copy ${l}`}><FiCopy aria-hidden=\"true\" /></button>}</span></div>))}\n"
        "                                    </div>\n"
        "                                </div>\n"
        "                                {project.landTitle && (<div className={styles.plotGroupBox} data-accent=\"cyan\">\n"
        "                                    <div className={styles.plotGroupLabel}>TITLE</div>\n"
        "                                    <div className={styles.readOnlyGrid}>\n"
        "                                        {[['PLOT ID', project.landTitle.plotNumber], ['TENURE', project.landTitle.tenure], ['TITLE ID', project.landTitle.titleId], ['BLOCK / ROAD', project.landTitle.blockRoad]].map(([l, v], i) => (\n"
        "                                            <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValueRow}><span className={styles.specValue}>{v || '---'}</span>{v && <button type=\"button\" className={styles.copyBtn} onClick={() => handleCopySpec(v, l)} aria-label={`Copy ${l}`}><FiCopy aria-hidden=\"true\" /></button>}</span></div>))}\n"
        "                                    </div>\n"
        "                                </div>)}\n"
        "                            </div>\n"
        "                        </>)}",

        "PLOT DETAILS view-mode grid split into LOCATION/TITLE group cards w/ copy buttons",
    ),
])

# ═══ FolderPage.module.css ═══
apply_patches(FOLDER_CSS, [
    (
        # group-card + copy-button styling, dropped right after the
        # existing spec grid rules so the two live side by side.
        ".specValue { color: #fff; font-size: var(--fs-value); font-weight: 700; font-family: 'Space Mono', monospace; line-height: 1.3; word-break: break-all; }\n"
        "\n"
        "\n"
        "/* ═══════════════════════════════════════════════════════════════════\n"
        "   EDIT INPUT GRID — strict repeat(3,1fr), no auto-fit\n"
        "   auto-fit collapses columns unpredictably on narrow panels\n"
        "   ═══════════════════════════════════════════════════════════════════ */",

        ".specValue { color: #fff; font-size: var(--fs-value); font-weight: 700; font-family: 'Space Mono', monospace; line-height: 1.3; word-break: break-all; }\n"
        "\n"
        "\n"
        "/* ═══════════════════════════════════════════════════════════════════\n"
        "   PLOT DETAILS GROUPING (fix131) — Settings-page parity\n"
        "   The flat spec list becomes two bounded, cream mini-cards -- the\n"
        "   exact prefGroupBox/prefGroupLabel language Settings' Appearance\n"
        "   panel uses for Display/Interaction/Notifications -- instead of one\n"
        "   undivided run of fields on the dark panel body.\n"
        "   ═══════════════════════════════════════════════════════════════════ */\n"
        ".plotGroupsGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--gap-lg); align-items: start; }\n"
        ".plotGroupBox {\n"
        "    --accent: var(--orange);\n"
        "    background: #f2ede4; border: 1px solid rgba(26,46,48,0.14);\n"
        "    border-radius: var(--radius-sm); padding: clamp(10px,1.3vw,14px) clamp(12px,1.5vw,16px);\n"
        "}\n"
        ".plotGroupBox[data-accent=\"cyan\"] { --accent: var(--cyan); }\n"
        ".plotGroupLabel {\n"
        "    font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);\n"
        "    font-weight: 900; letter-spacing: 2px; text-transform: uppercase;\n"
        "    color: var(--accent); border-bottom: 2px solid var(--accent);\n"
        "    padding: 0 0 clamp(7px,0.9vw,10px); margin-bottom: clamp(9px,1.2vw,14px);\n"
        "}\n"
        ".plotGroupBox .readOnlyGrid { row-gap: clamp(9px, 1.2vw, 14px); }\n"
        ".plotGroupBox .specItem { border-left: 2px solid rgba(26,46,48,0.18); padding: 2px 0 2px clamp(8px,1.1vw,12px); }\n"
        ".plotGroupBox .specLabel { color: rgba(26,46,48,0.55); }\n"
        ".plotGroupBox .specValue { color: #1a2e30; }\n"
        "\n"
        "/* Click-to-copy: quiet until the row is hovered/focused, then the\n"
        "   icon steps up to the group's own accent -- orange in LOCATION,\n"
        "   cyan in TITLE -- same recolor-per-group trick Settings uses. */\n"
        ".specValueRow { display: flex; align-items: center; gap: 6px; min-width: 0; }\n"
        ".copyBtn {\n"
        "    background: transparent; border: none; color: inherit; opacity: 0;\n"
        "    cursor: pointer; padding: 2px; font-size: 11px; flex-shrink: 0;\n"
        "    display: inline-flex; align-items: center;\n"
        "    transition: opacity 0.15s ease, color 0.15s ease;\n"
        "}\n"
        ".specItem:hover .copyBtn, .copyBtn:focus-visible { opacity: 0.55; }\n"
        ".copyBtn:hover, .copyBtn:focus-visible { opacity: 1 !important; color: var(--orange); outline: none; }\n"
        ".plotGroupBox .copyBtn:hover, .plotGroupBox .copyBtn:focus-visible { color: var(--accent, var(--orange)); }\n"
        "\n"
        "\n"
        "/* ═══════════════════════════════════════════════════════════════════\n"
        "   EDIT INPUT GRID — strict repeat(3,1fr), no auto-fit\n"
        "   auto-fit collapses columns unpredictably on narrow panels\n"
        "   ═══════════════════════════════════════════════════════════════════ */",

        "plotGroupsGrid/plotGroupBox/plotGroupLabel + copyBtn rules added",
    ),
])

# ═══ build gate (fix76) ═══
if os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True)
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        print("FAIL: build is red -- aborting, nothing committed")
        sys.exit(1)
    print("build OK")
else:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")


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

git("add", "-A")
git("commit", "-m", "fix131: PLOT DETAILS reorganised into Settings-style LOCATION/TITLE cards + click-to-copy on values")
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