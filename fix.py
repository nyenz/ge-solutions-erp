#!/usr/bin/env python3
# PATH: fix133.py
# GOLDEN SEED -- fix133: two follow-up fixes on top of fix132, both from
#   direct feedback against a live screenshot.
#     1. TAB DOCK WIDTH -- fix132 gave the dock `flex: 1 1 auto`, which
#        stretches the grey tray across the whole header width even
#        though five short pills fill barely a third of it -- a long
#        bar of dark-grey nothing to the right of NOTES. Settings' own
#        .tabDock is `flex: 0 0 auto` -- sized to its own content, sitting
#        left inside a dockRow -- and that's the value that was supposed
#        to carry over. Fixed to match: the tray now hugs the five tabs.
#     2. PLOT DETAILS SPLIT -- LOCATION and TITLE read as one undivided
#        run with a stray line trailing under the TITLE label and
#        nothing marking where LOCATION ends. Each group is now wrapped
#        in its own .specGroup; every group after the first
#        (.specGroupDivided) gets one real divider -- a border-TOP rule
#        sitting between the two groups, not a border-bottom hanging off
#        a single label with no visual reason to be there. sectionSubHeader
#        drops its own border-bottom accordingly, so there's exactly one
#        line in the panel and it's doing an obvious job: splitting
#        LOCATION from TITLE.
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
        # LOCATION and TITLE each wrapped in .specGroup; TITLE also
        # gets .specGroupDivided so the CSS can hang exactly one
        # divider between the two, instead of one dangling off the
        # TITLE label alone.
        "                        </>) : (<>\n"
        "                            <div className={styles.sectionSubHeader}>LOCATION</div>\n"
        "                            <div className={styles.readOnlyGrid}>\n"
        "                                {[['DISTRICT', project.district], ['COUNTY', project.county], ['SUB-COUNTY', project.subCounty], ['PARISH', project.parish], ['VILLAGE', project.village], ['AREA', project.area]].map(([l, v], i) => (\n"
        "                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}\n"
        "                            </div>\n"
        "                            {project.landTitle && (<>\n"
        "                            <div className={styles.sectionSubHeader}>TITLE</div>\n"
        "                            <div className={styles.readOnlyGrid}>\n"
        "                                {[['PLOT ID', project.landTitle.plotNumber], ['TENURE', project.landTitle.tenure], ['TITLE ID', project.landTitle.titleId], ['BLOCK / ROAD', project.landTitle.blockRoad]].map(([l, v], i) => (\n"
        "                                    <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}\n"
        "                            </div>\n"
        "                            </>)}\n"
        "                        </>)}",

        "                        </>) : (<>\n"
        "                            <div className={styles.specGroup}>\n"
        "                                <div className={styles.sectionSubHeader}>LOCATION</div>\n"
        "                                <div className={styles.readOnlyGrid}>\n"
        "                                    {[['DISTRICT', project.district], ['COUNTY', project.county], ['SUB-COUNTY', project.subCounty], ['PARISH', project.parish], ['VILLAGE', project.village], ['AREA', project.area]].map(([l, v], i) => (\n"
        "                                        <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}\n"
        "                                </div>\n"
        "                            </div>\n"
        "                            {project.landTitle && (<div className={`${styles.specGroup} ${styles.specGroupDivided}`}>\n"
        "                                <div className={styles.sectionSubHeader}>TITLE</div>\n"
        "                                <div className={styles.readOnlyGrid}>\n"
        "                                    {[['PLOT ID', project.landTitle.plotNumber], ['TENURE', project.landTitle.tenure], ['TITLE ID', project.landTitle.titleId], ['BLOCK / ROAD', project.landTitle.blockRoad]].map(([l, v], i) => (\n"
        "                                        <div key={i} className={styles.specItem}><span className={styles.specLabel}>{l}</span><span className={styles.specValue}>{v || '---'}</span></div>))}\n"
        "                                </div>\n"
        "                            </div>)}\n"
        "                        </>)}",

        "PLOT DETAILS wrapped in specGroup/specGroupDivided",
    ),
])

# ═══ FolderPage.module.css ═══
apply_patches(FOLDER_CSS, [
    (
        # 1. dock sized to its own content, not stretched across the
        # header -- matches Settings' `flex: 0 0 auto` exactly.
        ".tabDock {\n"
        "    flex: 1 1 auto; display: flex; align-items: center; min-width: 0;\n"
        "    background: #4d5c5a; border: none; border-radius: 8px;\n"
        "    padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
        "    overflow-x: auto; scrollbar-width: none;\n"
        "}",

        ".tabDock {\n"
        "    flex: 0 0 auto; display: flex; align-items: center; max-width: 100%;\n"
        "    background: #4d5c5a; border: none; border-radius: 8px;\n"
        "    padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
        "    overflow-x: auto; scrollbar-width: none;\n"
        "}",

        "tabDock sized to content instead of stretching full width",
    ),
    (
        # 2. sectionSubHeader loses its own border-bottom -- a label
        # alone shouldn't carry a divider; the divider's job moves to
        # specGroupDivided below, where it's actually splitting two
        # groups apart instead of trailing off one.
        ".sectionSubHeader {\n"
        "    font-family: 'DM Sans', sans-serif;\n"
        "    font-size: clamp(9px, 0.9vw, 11px);\n"
        "    font-weight: 900;\n"
        "    color: var(--orange);\n"
        "    text-transform: uppercase;\n"
        "    letter-spacing: 2px;\n"
        "    margin-bottom: clamp(10px, 1.3vw, 14px);\n"
        "    padding-bottom: clamp(6px, 0.8vw, 9px);\n"
        "    border-bottom: 1px solid rgba(238, 140, 58, 0.2);\n"
        "}",

        ".sectionSubHeader {\n"
        "    font-family: 'DM Sans', sans-serif;\n"
        "    font-size: clamp(9px, 0.9vw, 11px);\n"
        "    font-weight: 900;\n"
        "    color: var(--orange);\n"
        "    text-transform: uppercase;\n"
        "    letter-spacing: 2px;\n"
        "    margin-bottom: clamp(9px, 1.2vw, 13px);\n"
        "}\n"
        "\n"
        "/* fix133: LOCATION/LOCATION-style groups get their own wrapper so a\n"
        "   divider can sit BETWEEN two groups (specGroupDivided) instead of\n"
        "   hanging off a single label with nothing on either side of it. */\n"
        ".specGroup { display: flex; flex-direction: column; gap: clamp(9px, 1.2vw, 13px); }\n"
        ".specGroupDivided {\n"
        "    border-top: 1px solid rgba(255, 255, 255, 0.1);\n"
        "    padding-top: clamp(12px, 1.6vw, 18px);\n"
        "}",

        "sectionSubHeader border-bottom removed; specGroup/specGroupDivided added",
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
git("commit", "-m", "fix133: tab dock sized to content (not stretched full-width); PLOT DETAILS LOCATION/TITLE split with one real divider between groups")
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