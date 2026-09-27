#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix115: Scope panel header height, matched to Intake's
# CollapsibleSection header for real this time.
#
# The user's read was right, but the cause wasn't the padding: fix113
# already set .scopePanel .panelHeadRow's padding/gap to Intake's exact
# clamp() tokens, and fix112 already matched .scopeTitle's font-size. Both
# of those are byte-for-byte identical to Intake today.
#
# The actual culprit was .headToggle -- the chevron wrapper. Its own comment
# says "a plain rotating glyph, not a boxed button", but the rule underneath
# it was still exactly that: a fixed 28x28px circle with a fixed 16px icon
# inside. Intake's CollapsibleSection chevron has no box at all -- it's a
# ~14px glyph sized straight off font-size. A 28px-tall element sitting
# inside a flex row with align-items: center forces the whole row to be at
# least 28px tall regardless of what the padding says, so the header read
# taller than Intake's even though every padding/gap/font-size token
# matched. Shrinking the toggle to a plain glyph (no hit-box needed -- the
# entire row already has role="button" and its own onClick) removes that
# floor and lets the two headers land on the same height.
#
# Surgical find/replace against known-good source text, not a full rewrite.
# Runs `npm run build` before committing if node_modules is installed and
# refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")

REPORT_STUDIO_CSS = os.path.join(SRC, "pages", "Reports", "ReportStudio.module.css")


def apply_patches(path, patches):
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


# ═══ ReportStudio.module.css -- chevron goes from boxed button to plain glyph ═══
apply_patches(REPORT_STUDIO_CSS, [
    (
        "/* Matches the Intake page's CollapsibleSection chevron: a plain rotating\n"
        "   glyph, not a boxed button -- was the odd one out, styled as a separate\n"
        "   orange square unlike every other collapse control in the app. No hover\n"
        "   state of its own either, same as Intake's chevron -- the head row's\n"
        "   hover (below) is the only feedback hovering this corner gives. */\n"
        ".headToggle {\n"
        "  margin-left: auto; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; flex-shrink: 0; border: none; background: transparent; color: rgba(255, 255, 255, 0.45); transition: color 0.2s ease;\n"
        "}\n"
        ".headToggle svg {\n"
        "  width: 16px; height: 16px; transition: transform 0.2s ease;\n"
        "}",
        "/* fix115: this comment always said \"a plain rotating glyph, not a boxed\n"
        "   button\" but the rule below it still was one -- a fixed 28x28 circle\n"
        "   with a fixed 16px icon, taller than Intake's ~14px chevron glyph with\n"
        "   no box at all. That circle, not the padding (already matched to\n"
        "   Intake since fix113), is what was making the whole header row read\n"
        "   taller/bigger than an Intake CollapsibleSection header. Now it really\n"
        "   is just a glyph: sized in em off the row's own font-size, no hit-box\n"
        "   of its own, because the entire row is already the click target\n"
        "   (role=\"button\" on .panelHeadRow itself). */\n"
        ".headToggle {\n"
        "  margin-left: auto; display: inline-flex; align-items: center; flex-shrink: 0; color: rgba(255, 255, 255, 0.4); font-size: 14px; transition: color 0.2s ease;\n"
        "}\n"
        ".headToggle svg {\n"
        "  transition: transform 0.2s ease;\n"
        "}",
        "headToggle chevron shrunk from a fixed 28x28 circular hit-box to a plain ~14px glyph, matching Intake's CollapsibleSection chevron exactly",
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
git("commit", "-m", "fix115: Scope/Catalogue chevron shrunk from a fixed 28x28 circular hit-box to a plain ~14px glyph -- that box, not the padding, was making the Scope header read taller than Intake's CollapsibleSection header")
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