#!/usr/bin/env python3
# PATH: fix128.py
# GOLDEN SEED -- fix128: fix127's three cream cards read better, but two
#   things were still flagged from a live screenshot of /settings:
#     1. No clear line between a group's heading and its own rows --
#      "DISPLAY" just sat directly above "PAGE THEME" with no divider.
#      Each prefGroupLabel now gets a 2px accent rule under it (same
#      idea as every other section title in the app separating from its
#      body, just inside the card instead of at the card's own head).
#     2. Rows inside a card were only ever separated by a 10%-opacity
#      border-bottom -- reads as almost nothing on a cream background,
#      so the three settings in a card still blur into one paragraph
#      ("too many things at once"). Each row is now its own bounded
#      mini-card -- Owners' row-shading idea (a bounded box per item)
#      applied here as a slightly darker tint instead of Owners' black
#      overlay, with its own border and rounded corners and a visible
#      gap to the next one, so every setting reads as one distinct,
#      countable unit instead of a paragraph broken by faint lines.
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

SETTINGS_CSS = os.path.join(SRC, "pages", "settings", "SettingsPage.module.css")


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


# ═══ SettingsPage.module.css ═══
apply_patches(SETTINGS_CSS, [
    (
        # 1. accent rule under the group heading, separating it from
        # its own rows.
        ".prefGroupBox .prefGroupLabel { color: var(--accent, var(--orange)); opacity: 1; padding: 0 0 clamp(6px,0.8vw,9px); }",

        ".prefGroupBox .prefGroupLabel {\n"
        "  color: var(--accent, var(--orange)); opacity: 1;\n"
        "  padding: 0 0 clamp(7px,0.9vw,10px); margin-bottom: clamp(7px,0.9vw,10px);\n"
        "  border-bottom: 2px solid var(--accent, var(--orange));\n"
        "}",

        "prefGroupLabel gets its own accent divider under the heading",
    ),
    (
        # 2. rows -> bounded mini-cards instead of a faint border-bottom
        # list, with a real gap between them.
        ".prefGroupBox .prefRow { border-bottom: 1px solid rgba(26,46,48,0.10); margin: 0; padding: clamp(8px,1.1vw,11px) 0; }\n"
        ".prefGroupBox .prefRow:hover { background: rgba(26,46,48,0.045); }\n"
        ".prefGroupBox .prefRow:last-child { border-bottom: none; }",

        ".prefGroupBox .prefRow {\n"
        "  border: 1px solid rgba(26,46,48,0.14); border-radius: 6px;\n"
        "  background: rgba(26,46,48,0.05);\n"
        "  margin: 0 0 clamp(7px,0.9vw,10px); padding: clamp(9px,1.2vw,12px);\n"
        "  transition: background 0.18s ease, border-color 0.18s ease;\n"
        "}\n"
        ".prefGroupBox .prefRow:hover { background: rgba(26,46,48,0.09); border-color: rgba(26,46,48,0.22); }\n"
        ".prefGroupBox .prefRow:last-child { margin-bottom: 0; }",

        "prefGroupBox rows turned into bounded mini-cards with real gaps",
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
git("commit", "-m", "fix128: Appearance group headings get an accent divider under them; rows turned into bounded mini-cards (border+tint+radius+gap) instead of a faint border-bottom list")
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