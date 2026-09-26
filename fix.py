#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix111: Intake page gets a new automatic ENTRY DATE field,
# and DATE STARTED goes back to being editable (defaults to today).
#
# What this fixes, and why:
#   1. Two different dates were being conflated into one read-only field.
#      "Date Started" was shown as a static today() value with no way to
#      change it, so there was no way to record that fieldwork on a plot
#      actually began a few days before the operator got round to keying
#      it into the system. It is now a real date input, defaulting to
#      today but editable.
#   2. To keep that honest, a second, separate field -- ENTRY DATE -- has
#      been added next to it. This one stays fully automatic: it is the
#      day the record was actually entered into Golden Seed, set once by
#      the server at save time and never editable on the client, so there
#      is always an untouched record of "when this was typed in" even
#      after Date Started has been backdated.
#   3. On the backend, LandProject never actually stored a start date at
#      all -- the intake builder chain had no .projectStartDate(...) call,
#      so every project's start date landed NULL regardless of what the
#      form showed. That is now wired up, alongside the new entry_date
#      column (server-set, updatable = false). The LandTitle side had
#      gone the other way (see the old "STEP 7" comment) and force-set
#      today() specifically to stop the client editing it -- that
#      decision is reversed here since editable is exactly what's wanted
#      now.
#
# Every edit below is a surgical find/replace against known-good source
# text rather than a full-file rewrite.
#
# Runs `npm run build` before committing if node_modules is installed
# (fix76's build-gate rule) and refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
BACKEND = os.path.join(ROOT, "erp-backend", "src", "main", "java", "com", "gesolutions", "erp")

INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
LAND_PROJECT_JAVA = os.path.join(BACKEND, "modules", "land", "model", "LandProject.java")
LAND_SERVICE_JAVA = os.path.join(BACKEND, "modules", "land", "service", "LandService.java")


def apply_patches(path, patches):
    """Apply an ordered list of (old, new, description) surgical patches to
    a file. Each `old` must appear exactly once -- if it doesn't (because
    the file has already been patched, or has drifted from what this
    script expects), that one patch is skipped with a warning instead of
    corrupting the file or aborting the whole run."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    rel = os.path.relpath(path, ROOT)
    applied = 0
    for old, new, desc in patches:
        if old not in text:
            if new in text:
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


# ═══ 1. IntakePage.jsx -- editable Date Started + new automatic Entry Date ═══
apply_patches(INTAKE_JSX, [
    (
        "    const [projectStartDate] = useState(todayISO);",
        "    const [projectStartDate, setProjectStartDate] = useState(todayISO);\n"
        "    // ENTRY DATE: automatic, never editable -- the day this intake was\n"
        "    // actually keyed into the system. Kept separate from Date Started\n"
        "    // above, which is when fieldwork began and can be backdated by the\n"
        "    // operator (e.g. entering a project two days after it started).\n"
        "    const [entryDate] = useState(todayDMY);",
        "projectStartDate becomes editable state, add entryDate (auto, no setter)",
    ),
    (
        "                    <div className={styles.grid2}>\n"
        "                        <div className={styles.field}>\n"
        "                            <label className={styles.label}>Index</label>\n"
        "                            <div className={styles.indexDisplay}>{nextIndex || 'Loading...'}</div>\n"
        "                            <p className={styles.hint}>Next available index, assigned on save</p>\n"
        "                        </div>\n"
        "                        <div className={styles.field}>\n"
        "                            <label className={styles.label}>Date Started</label>\n"
        "                            <div className={styles.indexDisplay}>{todayDMY()}</div>\n"
        "                            <p className={styles.hint}>Auto-generated with today's date</p>\n"
        "                        </div>\n"
        "                    </div>",
        "                    <div className={styles.grid3}>\n"
        "                        <div className={styles.field}>\n"
        "                            <label className={styles.label}>Index</label>\n"
        "                            <div className={styles.indexDisplay}>{nextIndex || 'Loading...'}</div>\n"
        "                            <p className={styles.hint}>Next available index, assigned on save</p>\n"
        "                        </div>\n"
        "                        <div className={styles.field}>\n"
        "                            <label className={styles.label}>Entry Date</label>\n"
        "                            <div className={styles.indexDisplay}>{entryDate}</div>\n"
        "                            <p className={styles.hint}>Automatically recorded when this is saved</p>\n"
        "                        </div>\n"
        "                        <div className={styles.field}>\n"
        "                            <label className={styles.label}>Date Started</label>\n"
        "                            <input type=\"date\" className={styles.input} value={projectStartDate}\n"
        "                                onChange={e => { setProjectStartDate(e.target.value); markDirty(); }} />\n"
        "                            <p className={styles.hint}>Defaults to today, edit if work started earlier</p>\n"
        "                        </div>\n"
        "                    </div>",
        "Entry Mode row: grid2 -> grid3, add Entry Date, Date Started becomes a date input",
    ),
    (
        "                isLegacy, titleAtIntake, projectStartDate: todayISO(),",
        "                isLegacy, titleAtIntake, projectStartDate: projectStartDate || todayISO(),",
        "save payload sends the (possibly edited) Date Started instead of a fresh today()",
    ),
    (
        "        setProjectType('NEW_FOLDER');\n"
        "        setTitleId(''); setTenure('FREEHOLD'); setPlotNumber(''); setBlockRoad(''); setTitleIssueDate('');",
        "        setProjectType('NEW_FOLDER'); setProjectStartDate(todayISO());\n"
        "        setTitleId(''); setTenure('FREEHOLD'); setPlotNumber(''); setBlockRoad(''); setTitleIssueDate('');",
        "duplicate-for-next-plot also resets Date Started back to today",
    ),
])

# ═══ 2. LandProject.java -- new entry_date column ═══
apply_patches(LAND_PROJECT_JAVA, [
    (
        "    @Column(name = \"project_start_date\")\n"
        "    private LocalDate projectStartDate;\n",
        "    @Column(name = \"project_start_date\")\n"
        "    private LocalDate projectStartDate;\n"
        "\n"
        "    /**\n"
        "     * ENTRY DATE -- automatic, never client-editable. The actual calendar\n"
        "     * day this record was keyed into Golden Seed, set once by the server\n"
        "     * at intake (atomicIntake()) and never touched again. Distinct from\n"
        "     * PROJECT START DATE above, which is when fieldwork began on the\n"
        "     * ground and CAN be backdated by the operator (e.g. entering a\n"
        "     * project two days after it actually started).\n"
        "     */\n"
        "    @Column(name = \"entry_date\", updatable = false)\n"
        "    private LocalDate entryDate;\n",
        "add entry_date column (automatic, updatable = false)",
    ),
])

# ═══ 3. LandService.java -- wire projectStartDate + entryDate into intake ═══
apply_patches(LAND_SERVICE_JAVA, [
    (
        "                    .blockRoad(request.getBlockRoad())\n"
        "                    // STEP 7: Date Started is no longer client-editable on the intake\n"
        "                    // form, so creation no longer trusts a client-supplied value here\n"
        "                    // -- always today. (updateProjectFull(), the Folder page's edit\n"
        "                    // flow, is a different form and is untouched.)\n"
        "                    .projectStartDate(LocalDate.now())\n"
        "                    .titleIssueDate(request.getTitleIssueDate())\n"
        "                    .build();",
        "                    .blockRoad(request.getBlockRoad())\n"
        "                    // Date Started is editable again on the intake form (staff can\n"
        "                    // backdate a project entered a few days after fieldwork began),\n"
        "                    // so this trusts the client value when present and only falls\n"
        "                    // back to today when it's missing. Entry Date (LandProject,\n"
        "                    // below) is the one that stays server-set and non-editable.\n"
        "                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())\n"
        "                    .titleIssueDate(request.getTitleIssueDate())\n"
        "                    .build();",
        "LandTitle.projectStartDate trusts the client value again instead of forcing today()",
    ),
    (
        "        LandProject.LandProjectBuilder builder = LandProject.builder()\n"
        "                .landTitle(title)\n"
        "                .projectIndex(projectIndex)\n"
        "                .district(request.getDistrict())",
        "        LandProject.LandProjectBuilder builder = LandProject.builder()\n"
        "                .landTitle(title)\n"
        "                .projectIndex(projectIndex)\n"
        "                // ENTRY DATE: automatic, server-set, never from the request.\n"
        "                .entryDate(LocalDate.now())\n"
        "                // DATE STARTED: editable on the intake form, defaults to today\n"
        "                // on the client -- this was previously never wired up here at\n"
        "                // all, so every project's start date landed NULL regardless of\n"
        "                // what the form showed.\n"
        "                .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : LocalDate.now())\n"
        "                .district(request.getDistrict())",
        "wire entryDate + projectStartDate into the LandProject builder (was missing entirely)",
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
git("commit", "-m", "fix111: Intake gets automatic Entry Date field, Date Started is editable again (defaults to today), backend wires both into LandProject")
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