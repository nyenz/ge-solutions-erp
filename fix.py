#!/usr/bin/env python3
# PATH: fix141.py
# GOLDEN SEED -- fix141: GUIDE CLEANUP. LLM_CONTEXT_GUIDE.md is corrected to match
# the code (the code is the truth). DOCS ONLY -- no app code is touched.
#
#   1. SECTION 4: repo is really PUBLIC; backend address is ge-solutions-api;
#      Cloudinary details point to Section 12 (one place only).
#   2. SECTION 5: phone-number rule added (fix139); Cloudinary line points to
#      Section 12; the restore screen is Settings > ARCHIVE tab (not "Recently
#      Deleted Plots").
#   3. SECTION 7 (design):
#      - NEW "DESIGN REFERENCE PAGES" block: Intake first, Ledger second, Reports
#        third, Recovery fourth, Settings fifth -- with the exact files and the
#        specific styles that make each one good.
#      - The old "Ledger is THE reference" law is marked SUPERSEDED.
#      - Loading states: the app uses the ONE shared LoadingState component.
#      - Fonts: DM Sans added (it is used in the code).
#      - "DESIGN RULES (fix58)" moved into Section 7 (it had no number).
#   4. SECTION 10: old addendum file steps removed. SECTION 13 rewritten (all
#      addendum rules removed; "the code is the truth" added).
#   5. SECTION 12: now the ONE place Cloudinary is described.
#   6. SECTION 14 (empty) removed. SECTION 15 filled (hosting, security at the
#      end, dashboard unfinished). SECTION 16: note about old code comments.
#   7. Hosting plan renamed from Section 17 to SECTION 18 (the code still has
#      comments pointing at an old Section 17). Its password item now says
#      "leave for now, app uses fake data -- do it before real data".
#
# Atomic: every patch is matched in memory first; if any one is MISSING nothing
# is written and nothing is committed. Safe to run twice.
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


def swap_section(path, start, end, new, desc):
    """Replace everything from `start` up to (not including) `end` with `new`.
    new == "" removes the section. Skips when already done."""
    t = FILES[path]
    if new and new in t:
        print("SKIP: " + desc + " -- already applied")
        return
    s = t.find(start)
    if s < 0:
        if not new:
            print("SKIP: " + desc + " -- already removed")
        else:
            print("MISSING: " + desc)
            MISSING.append(desc)
        return
    e = t.find(end, s + len(start))
    if e < 0:
        print("MISSING: " + desc + " (end marker not found)")
        MISSING.append(desc)
        return
    FILES[path] = t[:s] + new + t[e:]
    print("OK: " + desc)


load(GUIDE)

# ======================================================================
# 0. Hosting plan: Section 17 -> Section 18 (only the first time)
# ======================================================================
_t = FILES[GUIDE]
if "## 17. HOSTING + BACKUP PLAN" in _t:
    for _o, _n in (("## 17. HOSTING + BACKUP PLAN", "## 18. HOSTING + BACKUP PLAN"),
                   ("### 17.", "### 18."),
                   ("SECTION 17", "SECTION 18"),
                   ("Section 17", "Section 18")):
        _t = _t.replace(_o, _n)
    FILES[GUIDE] = _t
    print("OK: Hosting plan renamed to Section 18")
elif "## 18. HOSTING + BACKUP PLAN" in _t:
    print("SKIP: Hosting plan renamed to Section 18 -- already applied")
else:
    print("MISSING: Hosting plan section not found")
    MISSING.append("hosting plan section not found")

patch(GUIDE,
      "# Last updated: September 2026 (fix140: hosting plan added)\n",
      "# Last updated: September 2026 (fix141: guide cleaned up to match the code)\n",
      "Guide: last-updated line")

patch(GUIDE,
      "> 1. In your FIRST reply of the session, add ONE short line reminding David that the\n"
      ">    hosting move (Section 18) is still pending and that its \"DO THIS FIRST\" items\n"
      ">    are still open. Then carry on with whatever he asked. Do not nag more than once\n"
      ">    per session.\n",
      "> 1. In your FIRST reply of the session, add ONE short line reminding David that the\n"
      ">    hosting move (Section 18) is still pending. Then carry on with whatever he\n"
      ">    asked. Do not nag more than once per session. (Do NOT nag about passwords or\n"
      ">    security -- David chose to leave those for the end.)\n",
      "Guide: standing reminder wording")

patch(GUIDE,
      "- A. **Reset the Neon database password.** render.yaml in the public GitHub repo contains it in plain text. Resetting is the only real fix (the old one stays in git history). Then put the new password only in the host's environment settings, never in a file in the repo.",
      "- A. **Reset the Neon database password and make the GitHub repo private -- BEFORE real client data goes in.** David chose to leave this for now because the app only holds fake data. render.yaml in the repo contains the password in plain text and the repo is public; the old password stays in git history, so resetting is the only real fix. Then put the new password only in the host's environment settings, never in a file in the repo.",
      "Guide: hosting plan password item (left for later, fake data)")

# ======================================================================
# 1. SECTION 4
# ======================================================================
patch(GUIDE,
      "| Repo | GitHub (PRIVATE): github.com/nyenz/ge-solutions-erp |",
      "| Repo | GitHub (currently PUBLIC -- David will switch it to private before real data goes in): github.com/nyenz/ge-solutions-erp |",
      "Section 4: repo is public")
patch(GUIDE,
      "- Backend: https://ge-solutions.onrender.com",
      "- Backend: https://ge-solutions-api.onrender.com (the app calls it at /api/v1)",
      "Section 4: backend address")
patch(GUIDE,
      "| File Storage | Cloudinary (cloud name: dfd115bnz) |",
      "| File Storage | Cloudinary (details: Section 12) |",
      "Section 4: Cloudinary points to Section 12")

# ======================================================================
# 2. SECTION 5
# ======================================================================
patch(GUIDE,
      "- **Cloudinary:** All files stored on Cloudinary.",
      "- **Files:** all uploads are stored on Cloudinary today (details: Section 12; changes when hosting moves, Section 18).",
      "Section 5: Cloudinary points to Section 12")
patch(GUIDE,
      "- **Identity uniqueness:** NIN is the real uniqueness check per owner. Phone number is no longer used to prevent duplicates.",
      "- **Identity uniqueness:** NIN is the real uniqueness check per owner. Phone number is no longer used to prevent duplicates.\n"
      "- **Phone numbers (fix139):** staff can type a number any normal way (0772 123 456, +256772123456, 772123456). It is checked and saved as +256772123456. Several numbers are separated with \"/\" (max 3 per person). Wrong length, letters, or made-up numbers (6+ of the same digit in a row, or 7+ counting digits) are refused. A foreign number is allowed only when typed with its + country code. Checked in the browser (`utils/phone.js`) and again on the server (`PhoneUtil.java`) -- keep the two in step. Old numbers already saved are not changed.",
      "Section 5: phone-number rule")
patch(GUIDE,
      "Root can restore it from Settings > Recently Deleted Plots.",
      "Root can restore it from the Settings > ARCHIVE tab.",
      "Section 5: restore screen is the Settings ARCHIVE tab")

# ======================================================================
# 3. SECTION 7 (design)
# ======================================================================
REFBLOCK = r'''### DESIGN REFERENCE PAGES (READ FIRST -- David's baseline, in priority order)
**THE CODE IS THE TRUTH.** When you change or create any element, first find the closest match in the pages below (in this order), OPEN that CSS file, and copy its pattern. If this summary and the CSS file disagree, the CSS file wins. Only if nothing matches, ask David.

**1. INTAKE PAGE -- the main baseline for most things.** Files: `pages/Intake/IntakePage.module.css`, `components/ui/CollapsibleSection.module.css`, `components/ui/CornerDecor.module.css`, `components/common/HardwareSelect.module.css`.
- Panels (`CollapsibleSection`): diagonal navy-teal gradient (`135deg, #3a5a5c -> #2a4a4c -> #213E40`), thin orange border at 20% that goes full orange on hover, 10px radius, soft deep shadow. The header bar is darker (`#162a2c`); a thin 1.5px orange line shows under it ONLY while the panel is open (no glow). Title: Cinzel 700, orange, 2px letter-spacing, uppercase, turns white on hover. The chevron turns orange when open. The body opens with a 0.2s fade-slide. `.accent` = 2px full-orange border for the focused panel. Corner brackets, the tiny glowing dot and the pins come from `CornerDecor`.
- Dropdown (`HardwareSelect`): white box, 1.5px orange-at-30% border, 6px radius, height `clamp(34px,4.3vw,40px)`, orange chevron that flips. Hover or open = full orange border plus a soft 2px orange ring. The list: white, 1.5px orange border, 6px radius, deep shadow, bold navy options with hairline separators, hover or selected = solid orange with white text, opens with a 0.2s slide, max height 220px, hidden scrollbar. Inside popups use `HardwareModalSelect`.
- Also copy from Intake: inputs (`.input`, `.textarea`: white, orange border on hover and focus), type buttons (`.typeBtn`, `.typeBtnActive`: dark, active = solid orange with navy text), `.grid2` / `.grid3`, `.dropzone` (dashed orange), `.financialsSummary`, `.noteDateChip`, `.btn` / `.btn.primary`, `.toast`.

**2. LEDGER PAGE -- second priority, especially the table.** File: `pages/Ledger/LedgerPage.module.css`.
- Table card (`.tablePanel`): gradient `160deg, #1c3335 -> #213E40`, 1.5px orange-at-28% border, 10px radius, bottom corner brackets and pins only.
- Header row (`.ledgerTable thead th`): sticky INSIDE the table's own scroll box, opaque `#162a2c`, orange text, weight 900, uppercase, 2px letter-spacing, 3px orange bottom border. Sortable headers get an orange wash and white text on hover.
- Rows: `12px 14px` padding, faint 1px white-6% lines. Hover = white 4% wash plus a 3px orange left edge, no glow. Numbers, phones and indexes are Space Mono. Status words are plain coloured text (no pills). Problem and receivable rows get a faint red tint.
- Also copy: `.searchInner` (white search box, orange focus ring), `.filterBtn` / `.activeFilter`, `.pagination` / `.pageBtn`, the stage dots (`.stageDot*`), `.legendRow`.

**3. REPORTS PAGE -- lists inside panels, and the light/dark tone play.** Files: `pages/Reports/ReportHub.module.css` (and `ReportStudio.module.css`).
- List row (`.reportRow`): a 3-column grid = icon frame, title, chevron. Hover = white 3.5% wash and the chevron turns orange. Open row = orange 6% wash plus a 3px orange left edge.
- Icon frame (`.iconFrame`): small rounded square, orange-tinted fill, thin orange border, orange icon.
- Light rows on a dark panel (`.libList`): each row is a WHITE card (6px radius) with dark navy text and an orange-tinted hover (7-9%). Small group labels (`.libLabel`): DM Sans 900, 2px letter-spacing, white 60%. The detail drawer (`.detailBox`) is near-black with a 4px orange left edge. Chips: `.libChip`.

**4. RECOVERY PAGE -- popups and the font/colour emphasis.** Files: `components/common/HardwareModal.module.css` (the popup) and `pages/Recovery/RecoveryPortal.module.css`.
- Popup (`HardwareModal`, used for the CALL LOG window): dark blurred backdrop (`rgba(10,20,25,0.8)` + 6px blur). The card has gradient `160deg, #1c3335 -> #213e40`, 2px orange-at-40% border, 14px radius, deep shadow, 0.25s slide-up. The title is Cinzel orange with a thin orange line under it. Popup inputs are white with an orange border. Use the `modalStyles.*` classes (see Modal Popup Standard below).
- Emphasis by colour and font: the client name is bold uppercase (Cinzel orange in the card head); the NIN and section labels are orange (`#ffb46b` in the final rules), in Space Mono or tiny DM Sans caps; good = `#34d399`, bad = `#fca5a5`, none = white 50%, written as plain text with a thin underline (no pills); call position = cyan `#67e8f9`; in history, dim details (white 45%) sit next to bright text (white 80%).
- WARNING: `RecoveryPortal.module.css` has many layered overrides. The LAST rule for a class wins. Read to the end before copying.

**5. SETTINGS PAGE -- section colours tied to the tabs.** File: `pages/settings/SettingsPage.module.css`.
- The tabs sit in a grey dock (`.tabDock`, `#4d5c5a`, 8px radius). Each tab has its own accent (`data-accent`): orange, cyan, violet, red, slate (variables at the top of the file) -- Appearance, Security, Staff, Danger, Archive. The active tab fills with its accent plus a soft matching glow; hover only tints the text.
- The card under the tabs recolours its head bar, focus ring and hover glow from ONE variable, `--accent`, so section and tab always match. The card chrome is shared with `ReportStudio.module.css`.
- Light groups (`.prefGroupBox`): a cream-white surface with dark navy text (65% for secondary text), orange on hover, solid orange when selected. Rank text colours: admin amber `#fbbf24`, manager cyan `#06b6d4`, secretary green `#4ade80`.

'''

LAW_OLD = ("### LAW: LEDGER PAGE IS THE REFERENCE DESIGN -- **This is the master rule everything else follows.**\n"
           "Ledger is the closest existing page to the target design language for the whole app. **Every** other list, table, filter bar, search box, dropdown, or empty state **must** default to Ledger's existing pattern unless a subsection below says otherwise.")
patch(GUIDE,
      LAW_OLD,
      REFBLOCK + LAW_OLD + "\n\n**SUPERSEDED by \"DESIGN REFERENCE PAGES\" above:** Intake is now the first baseline and Ledger is second.",
      "Section 7: design reference pages + old Ledger law superseded")

patch(GUIDE,
      "**Space Mono** for plot numbers and project index values.",
      "**Space Mono** for plot numbers, project index values, phone numbers and other IDs and figures. **DM Sans** (sans-serif, weight 900, small uppercase) for page-header subtitles, small labels and legends on the Reports, Recovery and Settings pages.",
      "Section 7: DM Sans added to the font list")

patch(GUIDE,
      "### Loading State Style -- CONFIRMED FROM CODE\n"
      "- Simple inline text \"Loading...\" where a value isn't ready yet (e.g. project index before it's assigned). No spinner graphic, no skeleton block.",
      "### Loading State Style -- CONFIRMED FROM CODE\n"
      "- Every \"loading...\", \"syncing...\" and \"no records\" message uses the ONE shared component `components/common/LoadingState.jsx` (`tone=\"panel\"` draws its own dark card; `tone=\"bare\"` when already inside a dark panel; `size=\"page\"` for a whole-page screen). Never write a custom loading message.\n"
      "- Only a single small value that is not ready yet (e.g. the project index on the Intake page) shows the inline text \"Loading...\". No spinner graphic.\n"
      "- Skeleton blocks exist only on the Folder page.",
      "Section 7: loading state matches the code")

FIX58 = r'''### DESIGN RULES (fix58)
1. X IS THE CLOSER: any popup/modal that shows the animated X must NOT also show a CANCEL button. X = dismiss.
2. LOADING STATES: use the shared `LoadingState` component (see Loading State Style above), never a custom message.
3. ATTENTION COLORS: green = healthy/active/paid, orange = pending/backlog, red = debt/danger, amber = paused/negotiation, cyan = released/info. Use consistently app-wide.
4. INACTIVITY: edit mode auto-saves and deactivates after 5 minutes of no interaction.
5. RELATED PROJECTS: Owners tab always lists every other project of each owner/joint owner, clickable to navigate.

'''
FH_OLD = "### FolderPage Header\n- Uses `.terminalHeader` -- its own unique design, do NOT change to pageHeader"
patch(GUIDE,
      FH_OLD,
      FIX58 + FH_OLD,
      "Section 7: design rules (fix58) moved in")

# remove the old unnumbered block at the very end of the file
_t = FILES[GUIDE]
_marker = "\n---\n\n## DESIGN RULES (fix58)\n"
if _marker in _t:
    FILES[GUIDE] = _t[:_t.find(_marker)] + "\n"
    print("OK: old unnumbered DESIGN RULES block removed from the end")
else:
    print("SKIP: old unnumbered DESIGN RULES block -- already gone")

# ======================================================================
# 4. SECTIONS 10, 12
# ======================================================================
patch(GUIDE,
      "1. Create fix.py AND updated LLM_CONTEXT_ADDENDUM.md -> present both -> David downloads both\n"
      "2. David replaces local fix.py AND local LLM_CONTEXT_ADDENDUM.md",
      "1. Create fix.py -> present it -> David downloads it\n"
      "2. David replaces local fix.py",
      "Section 10: old extra-file steps removed")
patch(GUIDE,
      "## 12. CLOUDINARY DETAILS\n\n- Cloud name: dfd115bnz",
      "## 12. CLOUDINARY DETAILS\n\nThis is the ONE place Cloudinary is described (Sections 4 and 5 point here). It changes when hosting moves (Section 18).\n\n- Cloud name: dfd115bnz",
      "Section 12: the one place for Cloudinary")

# ======================================================================
# 5. SECTIONS 13, 14, 15, 16
# ======================================================================
SEC13 = r'''## 13. GUIDE RULES (HOW THIS GUIDE STAYS TRUE)

**RULE (PERMANENT):** THE CODE IS THE SOURCE OF TRUTH. If this guide and the code disagree, the code wins. Fix the guide to match the code (inside a fix.py), never the other way round.

**RULE (PERMANENT):** No fact, design standard, or process step should exist in more than one place in this guide. If something needs to be referenced elsewhere, point to it by section number instead of restating it. Found duplication is a documentation bug -- fix it immediately, the same way a code bug would be fixed.

**RULE (PERMANENT):** When a later section changes a decision made in an earlier one, never delete or silently rewrite the earlier text. Leave it in place and add a short "SUPERSEDED by Section X.Y" note directly under it, pointing to the new authority. (Plain factual errors -- a wrong address, a wrong font -- are simply corrected.)

**RULE (PERMANENT):** Guide changes ship inside a fix.py, like any other file change. Section 8 only updates its own Phase Tracker (8.10) as work progresses; Section 9's process rules change only when David explicitly approves a new permanent rule.

*(There is no Section 14: the empty "what has been completed" list was removed. Section numbers were kept so other references stay valid.)*

---

'''
swap_section(GUIDE, "## 13. SESSION MANAGEMENT RULES", "## 14. WHAT HAS BEEN COMPLETED", SEC13,
             "Section 13: rewritten (old extra-file rules removed)")

swap_section(GUIDE, "## 14. WHAT HAS BEEN COMPLETED", "## 15. WHAT STILL NEEDS TO BE DONE", "",
             "Section 14: empty section removed")

SEC15 = r'''## 15. WHAT STILL NEEDS TO BE DONE
- HOSTING + BACKUP MOVE (pending) -- see Section 18. Remind David once per session.
- SECURITY / JWT changes -- done at the END of the build. Until then ignore security work (the app only holds fake data). Before real client data goes in: reset the Neon password and make the GitHub repo private.
- DIRECTOR'S DASHBOARD -- David is still working on it and its code will change. Section 8.12 is only the plan.

---

'''
swap_section(GUIDE, "## 15. WHAT STILL NEEDS TO BE DONE", "## 16. KNOWN ISSUES", SEC15,
             "Section 15: filled in")

patch(GUIDE,
      "Do not rename these columns without a manual, out-of-band migration run directly against the live DB first.\n",
      "Do not rename these columns without a manual, out-of-band migration run directly against the live DB first.\n"
      "- Some code comments (for example in `Role.java`) point to guide sections \"17.7\" and \"17.10\". Those sections no longer exist in this guide. Ignore those pointers -- the code is the truth. (Section 18 is the hosting plan.)\n"
      "\n---\n",
      "Section 16: note about old code comments")

# ======================================================================
# ATOMIC GATE -- nothing is written unless every patch matched
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The guide differs from what this script expects (fix140 must already be applied).")
    sys.exit(1)

changed = False
for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True

if not changed:
    print("note: nothing changed -- fix141 already applied")
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
git("commit", "-m", "fix141: guide cleaned up to match the code -- design reference pages (Intake, Ledger, Reports, Recovery, Settings) added, wrong facts fixed (public repo, backend address, loading state, fonts, restore screen), phone rule added, old extra-file rules removed, hosting plan is now Section 18")
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
print("DONE: fix141 applied. Open LLM_CONTEXT_GUIDE.md to check the cleaned-up guide.")