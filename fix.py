#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix119: Report Catalogue list -- three follow-ups to
# fix118's rebuild, reported straight off the live Render screenshots.
#
#   1. CUT-OFF DEFAULT ROW (real bug, not cosmetic). .ungrouped/.groupBody
#      had `overflow: hidden` so their rounded corners would clip
#      anything inside them -- including a row's own description text
#      if it ever laid out even a pixel taller than the card expected
#      (a font-swap reflow, a tab switch changing catList's scroll
#      height and nudging layout, etc). That's exactly the "sometimes
#      shows it, sometimes doesn't" symptom: nothing about the data
#      changes between tabs, only the layout timing does. Fix: drop
#      overflow:hidden entirely so nothing can ever be clipped, and get
#      the rounded corners back by rounding the first/last row's own
#      rowHead (or, if the last row is open, its readout) instead.
#   2. FONT TONE. Open (not-applied, not-hovered-applied) rows flipped
#      name/desc/meta text to white on the solid-orange fill. Nowhere
#      else in the app pairs orange with white text -- the tabs, the
#      pills, the applied wash all pair orange with the app's own dark
#      ink (#1a2e30). Open rows now match that.
#   3. SPACING. catList padding/gap, the gap between grouped cards,
#      rowHead's own padding, the desc's top margin and the readout's
#      padding are all trimmed down -- the list read as too airy.
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


# ═══ ReportStudio.module.css ═══
apply_patches(STUDIO_CSS, [
    (
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; background: #f2ede4;\n"
        "  padding: 14px; display: flex; flex-direction: column; gap: 10px;\n"
        "  scrollbar-width: thin; scrollbar-color: #EE8C3A transparent;\n"
        "}\n",
        ".catList {\n"
        "  max-height: 340px; overflow-y: auto; background: #f2ede4;\n"
        "  padding: 10px; display: flex; flex-direction: column; gap: 7px;\n"
        "  scrollbar-width: thin; scrollbar-color: #EE8C3A transparent;\n"
        "}\n",
        "catList padding/gap tightened (14px/10px -> 10px/7px) -- list read as too spaced out",
    ),
    (
        ".group { display: flex; flex-direction: column; gap: 6px; }\n"
        ".ungrouped, .groupBody { border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(26,46,48,0.14); background: #fff; }\n",
        ".group { display: flex; flex-direction: column; gap: 4px; }\n"
        "/* fix119: overflow:hidden removed -- it could clip a row's own\n"
        "   content (its description line) the moment layout shifted even a\n"
        "   pixel, which is what \"default row description sometimes missing\"\n"
        "   actually was. Rounded corners now live on the first/last row\n"
        "   instead, so nothing inside the card can ever be clipped. */\n"
        ".ungrouped, .groupBody { border-radius: 10px; box-shadow: 0 2px 8px rgba(26,46,48,0.14); background: #fff; }\n"
        ".groupBody .row:first-child .rowHead, .ungrouped .row:first-child .rowHead { border-top-left-radius: 10px; border-top-right-radius: 10px; }\n"
        ".groupBody .row:last-child:not(.rowOpen) .rowHead, .ungrouped .row:last-child:not(.rowOpen) .rowHead { border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }\n"
        ".groupBody .row:last-child.rowOpen .readout, .ungrouped .row:last-child.rowOpen .readout { border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }\n",
        "overflow:hidden removed from .ungrouped/.groupBody (was clipping row content) -- corners now rounded via first/last row instead; group gap tightened 6px -> 4px",
    ),
    (
        ".rowHead { display: flex; align-items: center; gap: 14px; width: 100%; text-align: left; border: none; background: transparent; padding: 14px 15px; cursor: pointer; transition: background 0.15s ease; }\n",
        ".rowHead { display: flex; align-items: center; gap: 14px; width: 100%; text-align: left; border: none; background: transparent; padding: 10px 14px; cursor: pointer; transition: background 0.15s ease; }\n",
        "rowHead padding tightened 14px/15px -> 10px/14px",
    ),
    (
        ".row.rowOpen:not(.rowApplied) .rowHead .name,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .rows,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .tag,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .chev,\n"
        ".row:not(.rowApplied) .rowHead:hover .name,\n"
        ".row:not(.rowApplied) .rowHead:hover .rows,\n"
        ".row:not(.rowApplied) .rowHead:hover .tag,\n"
        ".row:not(.rowApplied) .rowHead:hover .chev { color: #fff; }\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .desc,\n"
        ".row:not(.rowApplied) .rowHead:hover .desc { color: rgba(255,255,255,0.85); }\n",
        ".row.rowOpen:not(.rowApplied) .rowHead .name,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .rows,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .tag,\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .chev,\n"
        ".row:not(.rowApplied) .rowHead:hover .name,\n"
        ".row:not(.rowApplied) .rowHead:hover .rows,\n"
        ".row:not(.rowApplied) .rowHead:hover .tag,\n"
        ".row:not(.rowApplied) .rowHead:hover .chev { color: #1a2e30; }\n"
        ".row.rowOpen:not(.rowApplied) .rowHead .desc,\n"
        ".row:not(.rowApplied) .rowHead:hover .desc { color: rgba(26,46,48,0.7); }\n",
        "open/hover row text dropped from white to the app's own dark ink (#1a2e30) -- matches how orange fill pairs with text everywhere else (tabs, pills, applied wash)",
    ),
    (
        ".desc { font-size: 11px; font-weight: 600; color: rgba(26,46,48,0.55); margin-top: 3px; transition: color 0.15s ease; }\n",
        ".desc { font-size: 11px; font-weight: 600; color: rgba(26,46,48,0.55); margin-top: 2px; transition: color 0.15s ease; }\n",
        "desc top margin tightened 3px -> 2px",
    ),
    (
        ".readout { display: flex; align-items: center; gap: 12px; padding: 12px 15px; margin: 0; background: #28383a; }\n",
        ".readout { display: flex; align-items: center; gap: 10px; padding: 10px 14px; margin: 0; background: #28383a; }\n",
        "readout padding tightened 12px/15px -> 10px/14px",
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
git("commit", "-m", "fix119: Report Catalogue list -- default-row clipping bug fixed (overflow:hidden removed), open-row text tone matched to app's dark ink instead of white, overall list spacing tightened")
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