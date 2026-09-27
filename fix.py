#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix124: two follow-ups on the Report Catalogue.
#   1. The page used to load (and reload on every dataset switch) with
#      nothing applied -- appliedId started at null and stayed null
#      until you manually opened a report and hit "Use This Report",
#      so the viewer panel below the catalogue was just absent on
#      first load. That's also why the pinned "DEFAULT VIEW" row never
#      looked applied on the ALL scope: nothing had actually applied
#      it. The dataset-switch effect now looks up that same default
#      report (DEFAULTS[dataset].ALL) and applies it automatically --
#      same columns/sort/chart it would get from clicking "Use This
#      Report" by hand -- so the page always lands on a populated
#      view, and the pinned row shows APPLIED right away.
#   2. .catList had its own visible scrollbar sitting right next to
#      the page's own scrollbar in the screenshot -- two thin orange
#      tracks side by side. The scrolling itself (max-height,
#      overflow-y, the overscroll-behavior-y hand-off from fix123) is
#      unaffected and still works; only the track is hidden now, the
#      same hidden-but-functional pattern .ddScroll already uses a few
#      lines up in this same file. Wheel/trackpad/keyboard scrolling
#      inside the list still works with no visible scrollbar of its
#      own -- just the page's.
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

STUDIO_JSX = os.path.join(SRC, "pages", "Reports", "ReportStudio.jsx")
STUDIO_CSS = os.path.join(SRC, "pages", "Reports", "ReportStudio.module.css")


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


# ═══ ReportStudio.jsx ═══
apply_patches(STUDIO_JSX, [
    (
        # 1. auto-apply the dataset's default report on mount/dataset
        # switch instead of leaving appliedId null.
        "  useEffect(() => {\n"
        "    const ds = DATASETS[datasetKey];\n"
        "    if (!ds) return;\n"
        "    const allowed = fieldsFor(ds, canSeeMoney).map(f => f.key);\n"
        "    setColumns(ds.defaultColumns.filter(c => allowed.includes(c)));\n"
        "    setEntity(null); setAppliedId(null); setReadId(null);\n"
        "    setGroupTab('ALL'); setSearch('');\n"
        "    const sub = fieldsFor(ds, canSeeMoney).find(f => f.label === 'Sub-County');\n"
        "    setSort(sub ? { col: sub.label, dir: 'asc' } : { col: '', dir: 'asc' });\n"
        "    setChartMode('NONE');\n"
        "  }, [datasetKey, canSeeMoney]);",

        "  useEffect(() => {\n"
        "    const ds = DATASETS[datasetKey];\n"
        "    if (!ds) return;\n"
        "    const allowed = fieldsFor(ds, canSeeMoney).map(f => f.key);\n"
        "    const fieldMap = {};\n"
        "    fieldsFor(ds, canSeeMoney).forEach(f => { fieldMap[f.label] = f; });\n"
        "    setEntity(null); setReadId(null);\n"
        "    setGroupTab('ALL'); setSearch('');\n"
        "    const sub = fieldsFor(ds, canSeeMoney).find(f => f.label === 'Sub-County');\n"
        "    // fix124: land on the dataset's own default report (the\n"
        "    // catalogue's pinned DEFAULT VIEW row) instead of an empty\n"
        "    // viewer -- same as clicking \"Use This Report\" on it by hand.\n"
        "    const dName = (DEFAULTS[datasetKey] || {}).ALL || '';\n"
        "    const dDef = CATALOGUE.find(d => d.title === dName && d.ds === datasetKey && (!d.money || canSeeMoney)) || null;\n"
        "    if (dDef) {\n"
        "      setAppliedId(dDef.id);\n"
        "      const dCols = (dDef.cols || []).map(l => (fieldMap[l] || {}).key).filter(Boolean).filter(k => allowed.includes(k));\n"
        "      setColumns(dCols.length ? dCols : ds.defaultColumns.filter(c => allowed.includes(c)));\n"
        "      setSort(dDef.sort ? { col: dDef.sort.col, dir: dDef.sort.dir } : (sub ? { col: sub.label, dir: 'asc' } : { col: '', dir: 'asc' }));\n"
        "      setChartMode(dDef.chart || 'NONE');\n"
        "    } else {\n"
        "      setAppliedId(null);\n"
        "      setColumns(ds.defaultColumns.filter(c => allowed.includes(c)));\n"
        "      setSort(sub ? { col: sub.label, dir: 'asc' } : { col: '', dir: 'asc' });\n"
        "      setChartMode('NONE');\n"
        "    }\n"
        "  }, [datasetKey, canSeeMoney]);",

        "dataset-switch effect now auto-applies the DEFAULTS[dataset].ALL report instead of leaving appliedId null",
    ),
])

# ═══ ReportStudio.module.css ═══
apply_patches(STUDIO_CSS, [
    (
        # 2. hide catList's own scrollbar track (scroll itself untouched).
        "/* fix123: reverts fix122 -- the list keeps its own scroll like\n"
        "   every other internally-scrolled list in this app (Ledger,\n"
        "   Audit, Payments, Recovery all set a max-height the same way;\n"
        "   see the SCROLLABLE BODY comment in Shell.module.css). What was\n"
        "   actually broken is the hand-off at the boundary, not the\n"
        "   scroll itself -- overscroll-behavior-y: auto makes that\n"
        "   hand-off to the page's real scroll container explicit instead\n"
        "   of leaving it to browser default. */\n"
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; overscroll-behavior-y: auto; background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 7px;\n"
        "  scrollbar-width: thin; scrollbar-color: #EE8C3A transparent;\n"
        "}\n"
        ".catList::-webkit-scrollbar { width: 6px; }\n"
        ".catList::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.45); border-radius: 3px; }",

        "/* fix123: reverts fix122 -- the list keeps its own scroll like\n"
        "   every other internally-scrolled list in this app (Ledger,\n"
        "   Audit, Payments, Recovery all set a max-height the same way;\n"
        "   see the SCROLLABLE BODY comment in Shell.module.css). What was\n"
        "   actually broken is the hand-off at the boundary, not the\n"
        "   scroll itself -- overscroll-behavior-y: auto makes that\n"
        "   hand-off to the page's real scroll container explicit instead\n"
        "   of leaving it to browser default. */\n"
        "/* fix124: the scroll stays -- only its own visible track is\n"
        "   gone now, the same hidden-but-functional pattern .ddScroll\n"
        "   already uses a few lines up. Wheel/trackpad/keyboard scroll\n"
        "   inside the list still works exactly as before (and still\n"
        "   hands off to the page at the boundary); there's just no\n"
        "   second thin scrollbar sitting next to the page's own one. */\n"
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; overscroll-behavior-y: auto; background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 7px;\n"
        "  scrollbar-width: none; -ms-overflow-style: none;\n"
        "}\n"
        ".catList::-webkit-scrollbar { display: none; width: 0; height: 0; }",

        "catList's own scrollbar track hidden (scrollbar-width:none / webkit display:none), scroll+chaining behavior unchanged",
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
git("commit", "-m", "fix124: dataset's default report now auto-applies on load/switch instead of leaving the viewer empty; catList scrollbar track hidden (scroll + page hand-off unchanged)")
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