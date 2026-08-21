# PATH: fix.py
# STAGE 7 -- the 3 items from the "still open" list, actually resolved
# Run from project root: py fix.py
# Assumes Stage 5 and Stage 6 have already been run, committed, and pushed.
#
# David pushed back on the last "still open, needs a decision" list -- fair
# question, so each of the 3 got checked properly instead of left deferred.
# Result: 2 were genuinely doable safely, 1 turned out to already be done
# (Stage 6's addendum was wrong to list it as open). No decision needed from
# David on any of these -- write-up below is just showing the reasoning.
#
# ITEM 1 -- "HardwareSelect only used on 5 pages, others might have raw
# <select>": checked every page. Only ONE raw <select> exists anywhere
# (ExpensesPage.jsx's category filter) and only 2 pages use HardwareSelect
# (Audit, Settings) -- the earlier "5 pages" estimate was wrong, the real
# gap was smaller than thought.
#
# Did NOT swap it to HardwareSelect. Checked HardwareSelect.module.css: it
# renders a solid WHITE selectBox (#ffffff) with a stacked all-caps label
# above it (extra ~30px of height + margin-bottom:15px). ExpensesPage's
# filter row is a flat, unlabeled, single-line row of dark inputs
# (background: rgba(0,0,0,0.2), no labels, 36px tall, align-items:center).
# Dropping HardwareSelect in as-is would put a bright white pill with an
# orphan label sitting in a row of dark unlabeled inputs -- a visible
# mismatch, not a fix. The actual complaint ("browser default select
# styling") doesn't need the heavier component at all -- it needs the
# native chrome hidden and a custom arrow drawn, in the SAME dark style as
# its neighbors. That's what this patch does: pure CSS (appearance: none +
# an inline SVG arrow), scoped to `select.filterInput` so the sibling
# text/date/number inputs sharing that class are untouched. Zero JS/logic
# change, so nothing to break.
#
# ITEM 2 -- "Notification model exists but is never called, needs a
# feature decision": checked every .java file in the backend for any
# reference to Notification / NotificationService / NotificationRepository
# outside their own module folder. Zero. No controller exposes it, no
# @Scheduled job touches it, nothing autowires NotificationService. It is
# not a half-built feature waiting on a decision -- it is 3 files (30-ish
# lines total) that do nothing and are called from nowhere. That's a
# cleanup case, not a feature case, so this stage deletes them. If a real
# in-app notification feature is wanted later, that's new work to scope
# properly, not a resurrection of this dead stub.
#
# ITEM 3 -- "no dedicated Legacy Receivables intake flow found, only the
# isLegacy flag": this was a mistake in the last addendum. Re-checked
# IntakePage.jsx directly -- the isLegacyMode toggle (STANDARD PROJECT vs
# LEGACY RECEIVABLES) IS the Phase 6 flow; there's even a code comment on
# it that says so explicitly: "Section 17.6: staff flips ENTRY MODE toggle
# to mark a Legacy Receivable". Nothing to build here. No patch for this
# one -- just correcting the record so it stops showing up as open.
#
# Safe to re-run: every patch is checked before writing; if a patch target
# is not found it prints MISSING and leaves that file alone (most likely
# meaning this stage is already applied). File deletions are checked for
# existence first and are safe to re-run too (prints MISSING if already gone).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def patch(label, rel_path, old, new):
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path):
        print("[STAGE 7] " + label + " ... MISSING (file not found: " + rel_path + ")")
        return False
    content = read_file(full_path)
    if old not in content:
        if new in content:
            print("[STAGE 7] " + label + " ... OK (already applied)")
            return True
        print("[STAGE 7] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        return False
    content = content.replace(old, new, 1)
    write_file(full_path, content)
    print("[STAGE 7] " + label + " ... OK")
    return True


def delete_file(label, rel_path):
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path):
        print("[STAGE 7] " + label + " ... MISSING (already gone: " + rel_path + ")")
        return False
    os.remove(full_path)
    print("[STAGE 7] " + label + " ... OK (deleted)")
    return True


def main():
    print("=" * 70)
    print("STAGE 7 -- resolving the 3 deferred items")
    print("=" * 70)

    ok = 0
    total = 0

    # =========================================================================
    # ITEM 1 -- style the one remaining raw <select> to match the dark
    # HardwareSelect look, without swapping in the mismatched component.
    # =========================================================================
    total += 1
    ok += patch(
        "ExpensesPage: style the category <select> (hide native chrome)",
        "erp-frontend/src/pages/Financials/ExpensesPage.module.css",
        ".filterInput {\n"
        "    height: 36px;\n"
        "    padding: 0 10px;\n"
        "    border-radius: var(--radius-sm);\n"
        "    border: 1.5px solid rgba(255,255,255,0.15);\n"
        "    background: rgba(0,0,0,0.2);\n"
        "    color: #fff;\n"
        "    font-family: 'DM Sans', sans-serif;\n"
        "    font-size: 12px;\n"
        "    min-width: 120px;\n"
        "}\n"
        ".filterInput:focus { outline: none; border-color: var(--orange); }",

        ".filterInput {\n"
        "    height: 36px;\n"
        "    padding: 0 10px;\n"
        "    border-radius: var(--radius-sm);\n"
        "    border: 1.5px solid rgba(255,255,255,0.15);\n"
        "    background: rgba(0,0,0,0.2);\n"
        "    color: #fff;\n"
        "    font-family: 'DM Sans', sans-serif;\n"
        "    font-size: 12px;\n"
        "    min-width: 120px;\n"
        "}\n"
        ".filterInput:focus { outline: none; border-color: var(--orange); }\n"
        "select.filterInput {\n"
        "    appearance: none;\n"
        "    -webkit-appearance: none;\n"
        "    -moz-appearance: none;\n"
        "    padding-right: 28px;\n"
        "    cursor: pointer;\n"
        "    background-image: url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%23ffffff' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\");\n"
        "    background-repeat: no-repeat;\n"
        "    background-position: right 10px center;\n"
        "}\n"
        "select.filterInput option {\n"
        "    background: #1a2e30;\n"
        "    color: #fff;\n"
        "}",
    )

    # =========================================================================
    # ITEM 2 -- delete the confirmed-dead Notification module (3 files, zero
    # callers anywhere in the backend).
    # =========================================================================
    total += 1
    ok += delete_file(
        "Delete dead Notification.java (model)",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/notify/model/Notification.java",
    )
    total += 1
    ok += delete_file(
        "Delete dead NotificationRepository.java",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/notify/repository/NotificationRepository.java",
    )
    total += 1
    ok += delete_file(
        "Delete dead NotificationService.java",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/notify/service/NotificationService.java",
    )

    print("-" * 70)
    print("Applied/confirmed: " + str(ok) + " / " + str(total))
    print("-" * 70)
    print("ITEM 3 (Legacy Receivables intake flow): no patch needed -- it")
    print("already exists (IntakePage.jsx isLegacyMode toggle, Section 17.6).")
    print("This was a mistake in the last addendum, corrected there now.")
    print("=" * 70)
    print("Next: git add -A && git commit -m 'Stage 7: styled select + removed dead Notification module' && git push")
    print("")
    print("Note: after this deploys, the erp-backend/.../modules/notify/ folder")
    print("will be empty (all 3 files inside it deleted). That's expected --")
    print("delete the empty folder too, or leave it, either is harmless.")


if __name__ == "__main__":
    main()