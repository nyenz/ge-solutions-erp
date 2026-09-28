#!/usr/bin/env python3
# PATH: fix132.py
# GOLDEN SEED -- fix132: two changes, both on FolderPage.
#   1. REVERT fix131's PLOT DETAILS treatment. The cream prefGroupBox
#      cards didn't land well against the panel's dark gradient -- back
#      to the original flat, dark spec grid and the original copy-free
#      spec items. Organisation is kept, but the lightweight way: a
#      slim LOCATION / TITLE label (the .sectionSubHeader style that
#      already existed in this file, unused, for exactly this) sits
#      above each group instead of boxing it.
#   2. Settings' TAB DOCK, ported onto the Folder page's own section
#      tabs. OVERVIEW/FINANCIALS/OWNERS/DOCUMENTS/NOTES move from five
#      separately-bordered floating pills into the one shared grey tray
#      (#4d5c5a) holding borderless pills that solid-fill on selection
#      -- Settings' exact tabDock/tab/tabOn construction -- with each
#      tab keeping its own destination accent (orange/cyan/violet/
#      slate/red) the way Settings' own dock hints at where a tab leads
#      before you land there.
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
        # 1. fix131's FiCopy import reverted -- no longer used.
        "    FiDollarSign, FiActivity, FiHome, FiArchive,\n"
        "FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp, FiCopy\n"
        "} from 'react-icons/fi';",

        "    FiDollarSign, FiActivity, FiHome, FiArchive,\n"
        "FiPlus, FiFolderPlus, FiRefreshCw, FiArrowUp\n"
        "} from 'react-icons/fi';",

        "FiCopy import reverted",
    ),
    (
        # 2. fix131's copy handler removed.
        "    const handleToggleProblem = async () => { const was = project.problem; let note = ''; if (!was) { note = window.prompt('Describe the problem (optional):') || ''; } try { await folderPortalService.toggleProblem(id, note); if (!was && note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };\n"
        "    const handleCopySpec = (value, label) => { if (!value) return; navigator.clipboard?.writeText(String(value)).then(() => toast(label + ' copied', 'success', 1500)).catch(() => toast('Copy failed', 'error')); };",

        "    const handleToggleProblem = async () => { const was = project.problem; let note = ''; if (!was) { note = window.prompt('Describe the problem (optional):') || ''; } try { await folderPortalService.toggleProblem(id, note); if (!was && note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };",

        "handleCopySpec handler removed",
    ),
    (
        # 3. back to the flat, dark spec grid -- no boxes, no copy
        # buttons -- with a slim LOCATION / TITLE label above each
        # group using the file's own pre-existing sectionSubHeader
        # style instead of a bounded card.
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

        "PLOT DETAILS reverted to flat spec grid w/ LOCATION/TITLE sectionSubHeader labels",
    ),
    (
        # 4. per-tab accent map, sitting right next to TABS itself.
        "    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS', 'NOTES'];",

        "    const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS', 'NOTES'];\n"
        "    const TAB_ACCENTS = { OVERVIEW: 'orange', FINANCIALS: 'cyan', OWNERS: 'violet', DOCUMENTS: 'slate', NOTES: 'red' };",

        "TAB_ACCENTS map added",
    ),
    (
        # 5. tab bar markup -> Settings' tabDock/tabRow/tab-tabOn
        # construction. .tabBar itself is left as the outer wrapper
        # (it's the hook print/media rules already target), now just
        # holding the dock instead of five loose pills directly.
        "            <div className={styles.tabBar} role=\"tablist\" aria-label=\"Record sections\">\n"
        "                {TABS.map(tab => (<button key={tab} role=\"tab\" aria-selected={activeTab === tab}\n"
        "                    className={`${styles.tabBtn} ${activeTab === tab ? styles.tabBtnActive : ''}`} onClick={() => setActiveTab(tab)} title={tab}>\n"
        "                    <span className={styles.tabFull}>{tab}</span><span className={styles.tabShort}>{tab.substring(0, 2)}</span>\n"
        "                </button>))}\n"
        "            </div>",

        "            <div className={styles.tabBar} role=\"tablist\" aria-label=\"Record sections\">\n"
        "                <div className={styles.tabDock}>\n"
        "                    <div className={styles.tabRow}>\n"
        "                        {TABS.map(tab => (<button key={tab} role=\"tab\" aria-selected={activeTab === tab}\n"
        "                            data-accent={TAB_ACCENTS[tab]}\n"
        "                            className={activeTab === tab ? styles.tabOn : styles.tab} onClick={() => setActiveTab(tab)} title={tab}>\n"
        "                            <span className={styles.tabFull}>{tab}</span><span className={styles.tabShort}>{tab.substring(0, 2)}</span>\n"
        "                        </button>))}\n"
        "                    </div>\n"
        "                </div>\n"
        "            </div>",

        "tab bar markup switched to Settings' tabDock construction",
    ),
])

# ═══ FolderPage.module.css ═══
apply_patches(FOLDER_CSS, [
    (
        # 1. fix131's cream-card block removed outright.
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

        "\n"
        "\n"
        "/* ═══════════════════════════════════════════════════════════════════\n"
        "   EDIT INPUT GRID — strict repeat(3,1fr), no auto-fit\n"
        "   auto-fit collapses columns unpredictably on narrow panels\n"
        "   ═══════════════════════════════════════════════════════════════════ */",

        "fix131 plotGroupBox/copyBtn block removed",
    ),
    (
        # 2. Settings' tabDock/tabRow/tab-tabOn construction, dropped
        # right after the old tabBtn rules so both live together for
        # anyone diffing the history (tabBtn rules elsewhere in the
        # file are now unused but left in place, same as every other
        # superseded-in-place block this file already carries).
        ".tabBtn:focus-visible {\n"
        "    outline: 2px solid var(--orange);\n"
        "    outline-offset: 2px;\n"
        "}",

        ".tabBtn:focus-visible {\n"
        "    outline: 2px solid var(--orange);\n"
        "    outline-offset: 2px;\n"
        "}\n"
        "\n"
        "/* ── TAB DOCK (fix132) — ported from Settings' .tabDock ───────────\n"
        "   One shared grey tray holding borderless pills that solid-fill on\n"
        "   selection, each carrying its own destination accent, instead of\n"
        "   five separately-bordered floating buttons. */\n"
        ".tabDock {\n"
        "    flex: 1 1 auto; display: flex; align-items: center; min-width: 0;\n"
        "    background: #4d5c5a; border: none; border-radius: 8px;\n"
        "    padding: 6px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.14);\n"
        "    overflow-x: auto; scrollbar-width: none;\n"
        "}\n"
        ".tabDock::-webkit-scrollbar { display: none; }\n"
        ".tabRow { display: flex; flex-wrap: nowrap; gap: 6px; align-items: center; }\n"
        ".tab, .tabOn {\n"
        "    display: inline-flex; align-items: center; gap: 8px; cursor: pointer;\n"
        "    font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.95vw, 11px); font-weight: 900;\n"
        "    letter-spacing: 1.5px; text-transform: uppercase;\n"
        "    padding: clamp(7px,0.9vw,9px) clamp(12px,1.6vw,18px); border-radius: 6px; outline: none;\n"
        "    border: 1.5px solid transparent; background: transparent;\n"
        "    color: rgba(255,255,255,0.85); white-space: nowrap; flex-shrink: 0; line-height: 1;\n"
        "    transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;\n"
        "}\n"
        ".tab[data-accent=\"orange\"]:hover { color: var(--orange); }\n"
        ".tab[data-accent=\"cyan\"]:hover   { color: var(--cyan); }\n"
        ".tab[data-accent=\"violet\"]:hover { color: #34d399; }\n"
        ".tab[data-accent=\"slate\"]:hover  { color: #eab308; }\n"
        ".tab[data-accent=\"red\"]:hover    { color: var(--red); }\n"
        ".tabOn { color: #1a2e30; }\n"
        ".tabOn[data-accent=\"orange\"] { background: var(--orange); border-color: var(--orange); box-shadow: 0 4px 16px rgba(238,140,58,0.32); }\n"
        ".tabOn[data-accent=\"cyan\"]   { background: var(--cyan);   border-color: var(--cyan);   box-shadow: 0 4px 16px rgba(6,182,212,0.32); }\n"
        ".tabOn[data-accent=\"violet\"] { background: #34d399; border-color: #34d399; box-shadow: 0 4px 16px rgba(52,211,153,0.32); }\n"
        ".tabOn[data-accent=\"slate\"]  { background: #eab308; border-color: #eab308; box-shadow: 0 4px 16px rgba(234,179,8,0.32); }\n"
        ".tabOn[data-accent=\"red\"]    { background: var(--red); border-color: var(--red); color: #fff; box-shadow: 0 4px 16px rgba(239,68,68,0.32); }\n"
        ".tabOn:focus-visible, .tab:focus-visible { outline: 2px solid rgba(255,255,255,0.4); outline-offset: -2px; }\n"
        "@media (max-width: 480px) {\n"
        "    .tab, .tabOn { padding: clamp(6px,2vw,8px) clamp(9px,2.6vw,12px); font-size: 9px; }\n"
        "    .tabDock { padding: 5px; }\n"
        "}",

        "tabDock/tabRow/tab/tabOn rules added",
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
git("commit", "-m", "fix132: revert fix131 PLOT DETAILS cards to flat spec grid w/ LOCATION/TITLE labels; port Settings' tab dock onto Folder page section tabs")
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