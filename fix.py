#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix121: report + group heading titles toned down to a
# shared grey at rest -- the near-black ink (.name #1a2e30) and dark
# navy (.groupLabel #162a2c) were too heavy side by side, overwhelming
# the list. Both now share the same muted grey (#5b6f70 -- the app's
# own original report-title grey, pre-fix112). Nothing else changes:
#   - .row.rowApplied .name already overrides .name's color with a
#     higher-specificity selector, so an applied report keeps reading
#     in dark ink exactly as it does now.
#   - the open/persistent-hover selectors (.row.rowOpen:not(.rowApplied)
#     .rowHead .name, .row:not(.rowApplied) .rowHead:hover .name) are
#     also higher-specificity than .name, so hovering still flips the
#     title white same as before -- greying the resting color doesn't
#     touch that.
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


# ═══ ReportStudio.module.css -- resting title/label color toned down ═══
apply_patches(STUDIO_CSS, [
    (
        ".groupLabel span { font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: #162a2c; transition: color 0.18s ease; }",
        ".groupLabel span { font-size: 9px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: #5b6f70; transition: color 0.18s ease; }",
        "group heading resting color toned down from dark navy (#162a2c) to a muted grey (#5b6f70), matching the report title grey below",
    ),
    (
        ".name { font-size: 13px; font-weight: 800; letter-spacing: 0.3px; text-transform: uppercase; color: #1a2e30; transition: color 0.15s ease; }",
        ".name { font-size: 13px; font-weight: 800; letter-spacing: 0.3px; text-transform: uppercase; color: #5b6f70; transition: color 0.15s ease; }",
        "report title resting color toned down from near-black ink (#1a2e30) to a muted grey (#5b6f70) -- applied and open/hover states override this with their own colors, so those are unaffected",
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
git("commit", "-m", "fix121: report title + group heading resting text color toned down to a shared grey (#5b6f70), applied/open/hover colors untouched")
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