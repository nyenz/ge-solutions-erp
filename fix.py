#!/usr/bin/env python3
# PATH: fix140.py
# GOLDEN SEED -- fix140: writes the HOSTING + BACKUP PLAN into LLM_CONTEXT_GUIDE.md
# and adds a STANDING REMINDER at the very top, so every LLM that reads the guide
# tells David the move is still pending (until it is marked DONE).
#
#   1. TOP OF THE GUIDE: a short STANDING REMINDER block. Any LLM reading the
#      guide must mention, once per session, that the hosting move is pending.
#   2. NEW SECTION 17 "HOSTING + BACKUP PLAN": what was decided (Hetzner, office
#      backups, free domain), why, the estimated cost, the setup steps, the
#      things to fix first, and the routine after going live.
#   3. SECTION 15 (WHAT STILL NEEDS TO BE DONE) now points to Section 17.
#
# DOCS ONLY. No app code is touched, nothing is bought, installed or moved.
# The backend compile and frontend build are skipped because no code changes.
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing
# is written and nothing is committed. Safe to run twice (second run says
# "already applied").
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")

MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sub(text, old, new, desc):
    """Exact find/replace, first occurrence. Prints OK / SKIP / MISSING."""
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


FILES = {}
ORIGINAL = {}


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


load(GUIDE)

# ======================================================================
# 1. STANDING REMINDER (top of the guide)
# ======================================================================
REMINDER = r'''# Last updated: September 2026 (fix140: hosting plan added)

> ##############################################################
> ## STANDING REMINDER -- HOSTING MOVE IS PENDING (READ FIRST) ##
> ##############################################################
> David has DECIDED to move the app onto ONE Hetzner server, but it is NOT DONE yet.
> Nothing has been bought or moved. The full plan is in SECTION 17 at the bottom.
>
> RULES FOR EVERY LLM THAT READS THIS GUIDE:
> 1. In your FIRST reply of the session, add ONE short line reminding David that the
>    hosting move (Section 17) is still pending and that its "DO THIS FIRST" items
>    are still open. Then carry on with whatever he asked. Do not nag more than once
>    per session.
> 2. Do NOT start the move unless David says so.
> 3. Keep this reminder until Section 17 says "STATUS: DONE". Only a fix script that
>    marks Section 17 as done may remove this block.
> 4. When he does start: ONE step at a time, exact copy-paste commands, plain
>    English. He is a beginner.
'''

patch(GUIDE,
      "# Last updated: August 2026\n",
      REMINDER,
      "Guide: standing hosting reminder at the top")

# ======================================================================
# 2. SECTION 15 pointer
# ======================================================================
patch(GUIDE,
      "*(Nothing listed yet -- starts fresh from this reset point forward.)*",
      "- HOSTING + BACKUP MOVE (pending) -- see Section 17. Remind David once per session.",
      "Guide: Section 15 points to the hosting plan")

# ======================================================================
# 3. SECTION 17 (full plan)
# ======================================================================
SECTION17 = r'''## 17. HOSTING + BACKUP PLAN

**STATUS: PENDING -- decided September 2026, NOT started.** (Change to "STATUS: DONE" only when the move is finished and tested.)

### 17.1 What David decided
- Host the WHOLE app on ONE rented server (a "VPS") at **Hetzner**. Location: **Germany or Finland** (US locations have a tiny traffic allowance).
- **Backups: kept at the office for now.** The server makes a backup file every night. David copies it down to the office computer and to an external hard drive. Later, add the Hetzner backup add-on so a copy also exists off-site.
- **Domain: a FREE subdomain for now** (for example a DuckDNS address), NOT a bare IP address like http://95.216.x.x. The padlock (HTTPS) is set up for free. A paid domain (about $10-15 a year) comes later; staff will then switch to the new address.
- JWT / security changes stay at the END of the build, as before.
- David still wants to check other things before the move starts.

### 17.2 Why
- One bill instead of paying Render + Neon + Cloudinary separately. The free tiers sleep or have small limits.
- Expected size: about 4000 projects, each with several uploads. The database is small (a few GB). The UPLOADS are the big part.
- Rewriting the app in another language is NOT recommended. Java + Spring Boot is a good fit for an ERP that handles money. Use an agent/Opus only to speed up the same fix.py work.
- An office server is NOT recommended (Uganda power cuts, no fixed IP). True offline mode is NOT planned.

### 17.3 Estimated cost (check the Hetzner site before paying -- prices rose in April 2026)
- Server, 4 CPU / 8 GB (about CX33): roughly EUR 6.50 a month, plus about EUR 0.50 for the IP address.
- Upload disk: roughly EUR 0.05 per GB a month. 200 GB is about EUR 10.
- Backups: about EUR 4-10 a month.
- **Total: about $20-30 a month.**
- Disk size is a GUESS (80-400 GB, assuming 20-100 MB of uploads per project). Ask David for the real average upload size per project before choosing the disk.

### 17.4 DO THIS FIRST (open items)
- A. **Reset the Neon database password.** render.yaml in the public GitHub repo contains it in plain text. Resetting is the only real fix (the old one stays in git history). Then put the new password only in the host's environment settings, never in a file in the repo.
- B. **docker-compose.yml**: on the real server, remove the public database port (5432) and use a strong password from a private .env file, not the one written in the file.
- C. Ask David: is the average upload size per project known?
- D. Ask David: does he have a Visa/Mastercard (or virtual card) that works for international online payments? Hetzner needs one, and new accounts can get extra ID checks.

### 17.5 Setup steps (one time -- do ONE step at a time)
1. Rent the Hetzner server (Germany or Finland).
2. Set up the free subdomain and point it at the server.
3. Install Docker on the server.
4. Copy the project onto it and start it with `docker compose up`. (docker-compose.yml already runs the database, backend and frontend, and already keeps uploads in ./infra/ge_uploads.)
5. Move the data from Neon, and the old uploads from Cloudinary, onto the new server. (Upload code: CloudinaryStorageServiceImpl.java and FileStorageService.java in the land module.) Set VITE_API_BASE_URL to the new address.
6. Turn on HTTPS (free), nightly backups, and an uptime alert (a free monitor such as UptimeRobot).

### 17.6 Routine after going live
- Staff: open the web address in Chrome and work as now.
- Weekly (about 10 min): copy the backup file to the office computer and the external hard drive. Glance at free disk space.
- Monthly (about 20 min): run security updates, pay the bill, check the backup file exists and looks the right size.
- Every few months: TEST a restore, because a backup that was never restored may not work.
- Shipping a fix: run fix.py on his computer as now (it commits and pushes), then run ONE update command on the server (the LLM gives the exact command).
- If the site is down: run the restart command the LLM gave him.

### 17.7 Rules for the LLM when helping with this
- Simple English, outline format, short. Exact copy-paste commands. One step, then wait for him to confirm.
- Do not ask "A or B" unless it is a real decision.
- Never write real passwords into any file in the repo or into this guide.
'''

patch(GUIDE,
      "## DESIGN RULES (fix58)",
      SECTION17 + "\n---\n\n## DESIGN RULES (fix58)",
      "Guide: new Section 17 (hosting + backup plan)")

# ======================================================================
# ATOMIC GATE -- nothing is written unless every patch matched
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The guide differs from what this script expects (or was edited since fix139).")
    sys.exit(1)

changed = False
for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True

if not changed:
    print("note: nothing changed -- fix140 already applied")
    print("nothing to commit -- done")
    sys.exit(0)

print("note: docs only -- backend compile and frontend build skipped")


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
git("commit", "-m", "fix140: hosting + backup plan (Hetzner VPS, office backups, free domain) written into the LLM guide as Section 17, with a standing reminder at the top so every session reminds David it is still pending")
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
print("DONE: fix140 applied. Open LLM_CONTEXT_GUIDE.md to see the reminder at the top and Section 17 at the bottom.")