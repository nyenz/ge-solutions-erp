#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix125: Settings page redesign, Report Studio dimension
# parity + real sub-sections.
#
# The root cause of "inputs too stretched / buttons too big": SettingsPage
# rebuilt itself in fix121 to match Report Studio's chrome (gradient card,
# panel head, tab dock, button language) but never set the --input-height /
# --input-px / --btn-height / --btn-px custom properties the shared
# Hardware* components and this page's own buttons all read through
# var(..., fallback). With nothing set, every control on the page was
# silently falling back to HardwareInput's own default (44px) and
# HardwareButton's own default (48px) instead of Report Studio's 36-38px
# scale -- both bigger than anything else in the app, and inconsistent
# with each other.
#
#   1. One set of sizing tokens on .container brings every Hardware*
#      control and native button on the page down to Report Studio's own
#      scale in one place, instead of guessing at each control one by one.
#   2. The two fields that had no width cap at all -- the wipe-confirmation
#      input (spanning the full ~1350px card for a six-word phrase) and
#      the security dual-row (each password field able to stretch to half
#      the card on a wide desktop) -- now cap at a sane reading width.
#   3. The Provision Operator modal's CREATE button was the one control
#      NOT reachable by page-level tokens (HardwareModal portals to
#      document.body, outside .container in the DOM, so CSS vars set on
#      the page never cascade into it) -- it's swapped for the app's own
#      modalBtnPrimary convention (already used by every other modal
#      footer in this codebase) instead of the oversized HardwareButton.
#   4. Appearance's seven settings are split into three labelled
#      sub-groups (Display / Interaction / Notifications) instead of one
#      flat list, with a hover state added so rows read as individually
#      interactive, and the panel head icon gets a soft badge instead of
#      sitting bare on the dark bar -- matching Report Studio's iconFrame
#      treatment while staying keyed to each tab's own accent colour.
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
SETTINGS_JSX = os.path.join(SRC, "pages", "settings", "SettingsPage.jsx")


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
        # 1. sizing tokens -- brings every Hardware* control + native
        # button on the page down to Report Studio's 36-38px scale.
        "    --fs-op:     clamp(11px, 1.2vw, 14px);\n"
        "\n"
        "    max-width: 1400px;",

        "    --fs-op:     clamp(11px, 1.2vw, 14px);\n"
        "\n"
        "    /* fix125: control dims pulled in line with Report Studio's own\n"
        "       entInput/pickBtn scale (36-38px) instead of HardwareInput's\n"
        "       bare default (44px) and HardwareButton's bare default (48px)\n"
        "       -- both were rendering unopposed here because nothing on this\n"
        "       page set these vars before now. Every Hardware* control and\n"
        "       every native button below reads these through var(...)\n"
        "       fallbacks, so one set of numbers brings the whole page to\n"
        "       one consistent scale. */\n"
        "    --input-height: clamp(34px, 4vw, 38px);\n"
        "    --input-px:     clamp(10px, 1.3vw, 14px);\n"
        "    --input-radius: 6px;\n"
        "    --input-font:   clamp(11px, 1.05vw, 13px);\n"
        "    --label-font:   clamp(8px, 0.85vw, 10px);\n"
        "    --btn-height:   clamp(36px, 4.6vw, 42px);\n"
        "    --btn-px:       clamp(14px, 1.8vw, 20px);\n"
        "    --btn-font:     clamp(9px, 0.9vw, 11px);\n"
        "\n"
        "    max-width: 1400px;",

        "sizing tokens added to .container (--input-*/--btn-* now set, were previously unset)",
    ),
    (
        # 2a. wipe-confirmation field -- was full card width for a
        # six-word phrase.
        "/* ── DANGER ZONE ────────────────────────────────────────────────── */\n"
        ".wipeField { margin: var(--gap-md) 0; }",

        "/* ── DANGER ZONE ────────────────────────────────────────────────── */\n"
        "/* fix125: a six-word confirmation phrase doesn't need the full\n"
        "   card's width -- capped so it reads as a deliberate, compact\n"
        "   arm-switch instead of a text box stretched the width of the\n"
        "   whole panel. */\n"
        ".wipeField { margin: var(--gap-md) 0; max-width: clamp(260px, 40vw, 420px); }",

        ".wipeField width capped",
    ),
    (
        # 2b. security dual-row -- each field could stretch to half the
        # 1400px card on a wide desktop.
        ".dualRow { display: grid; grid-template-columns: 1fr 1fr; gap: var(--gap-md); }",

        "/* fix125: capped so the two key fields stay a sane reading width\n"
        "   instead of each stretching to half of a 1400px card. */\n"
        ".dualRow { display: grid; grid-template-columns: 1fr 1fr; gap: var(--gap-md); max-width: 640px; }",

        ".dualRow width capped",
    ),
    (
        # 3. panel head icon -- bare glyph on the dark bar before, now a
        # soft badge (Report Studio's iconFrame treatment).
        ".panelHeadIcon { font-size: clamp(12px,1.3vw,15px); }",

        "/* fix125: icon sits in a soft badge instead of bare on the dark\n"
        "   head bar, echoing Report Studio's iconFrame treatment. */\n"
        ".panelHeadIcon {\n"
        "  font-size: clamp(11px,1.15vw,14px);\n"
        "  width: clamp(22px, 2.4vw, 27px); height: clamp(22px, 2.4vw, 27px);\n"
        "  display: inline-flex; align-items: center; justify-content: center;\n"
        "  background: rgba(255, 255, 255, 0.08);\n"
        "  border: 1px solid rgba(255, 255, 255, 0.14);\n"
        "  border-radius: 6px; flex-shrink: 0;\n"
        "}",

        ".panelHeadIcon badge treatment added",
    ),
    (
        # 4. Appearance rows -- group label style + hover state, so the
        # seven settings can read as three organised clusters.
        ".prefRow {\n"
        "  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;\n"
        "  gap: 12px; padding: clamp(10px, 1.3vw, 14px) 0;\n"
        "  border-bottom: 1px solid rgba(255, 255, 255, 0.08);\n"
        "}\n"
        ".prefRow:last-of-type { border-bottom: none; }",

        "/* fix125: sub-groups inside Appearance so seven settings read as\n"
        "   three organised clusters (Display / Interaction / Notifications)\n"
        "   instead of one undifferentiated list. */\n"
        ".prefGroupLabel {\n"
        "  font-family: 'Inter', sans-serif; font-size: clamp(8px, 0.85vw, 10px);\n"
        "  font-weight: 900; letter-spacing: 2px; text-transform: uppercase;\n"
        "  color: var(--accent, var(--orange)); opacity: 0.85;\n"
        "  padding: clamp(12px, 1.6vw, 18px) 0 clamp(4px, 0.6vw, 6px);\n"
        "}\n"
        ".prefGroupLabel:first-child { padding-top: 0; }\n"
        "\n"
        ".prefRow {\n"
        "  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;\n"
        "  gap: 12px; padding: clamp(10px, 1.3vw, 14px) 10px;\n"
        "  margin: 0 -10px;\n"
        "  border-radius: 6px;\n"
        "  border-bottom: 1px solid rgba(255, 255, 255, 0.08);\n"
        "  transition: background 0.18s ease;\n"
        "}\n"
        ".prefRow:hover { background: rgba(255, 255, 255, 0.03); }\n"
        ".prefRow:last-of-type { border-bottom: none; }",

        ".prefGroupLabel added, .prefRow gets hover state",
    ),
])

# ═══ SettingsPage.jsx ═══
apply_patches(SETTINGS_JSX, [
    (
        # drop the now-unused HardwareButton import, add modalStyles so
        # the modal footer can use the app's own modalBtnPrimary class.
        "import HardwareModal from '../../components/common/HardwareModal';\n"
        "import HardwareButton from '../../components/common/HardwareButton';\n"
        "import BackToTopButton from '../../components/common/BackToTopButton';\n"
        "import CornerDecor from '../../components/ui/CornerDecor';\n"
        "import styles from './SettingsPage.module.css';",

        "import HardwareModal from '../../components/common/HardwareModal';\n"
        "import BackToTopButton from '../../components/common/BackToTopButton';\n"
        "import CornerDecor from '../../components/ui/CornerDecor';\n"
        "import styles from './SettingsPage.module.css';\n"
        "import modalStyles from '../../components/common/HardwareModal.module.css';",

        "unused HardwareButton import dropped, modalStyles import added",
    ),
    (
        # tag each PREF_GROUPS entry with the sub-group it belongs to
        # (contiguous already -- no reordering needed).
        "const PREF_GROUPS = [\n"
        "  { key: 'theme', label: 'Page theme', hint: 'Background and chrome. Panels stay navy in both.',\n"
        "    options: [{ value: 'light', label: 'CREAM' }, { value: 'dark', label: 'SLATE' }] },\n"
        "  { key: 'uiScale', label: 'Interface size', hint: 'Scales the whole app, not just text.',\n"
        "    options: [{ value: '90', label: '90%' }, { value: '100', label: '100%' }, { value: '110', label: '110%' }, { value: '125', label: '125%' }] },\n"
        "  { key: 'statSize', label: 'Summary box size', hint: 'The figures at the top of Payments, Expenses and the dossier.',\n"
        "    options: [{ value: 'small', label: 'SMALL' }, { value: 'standard', label: 'STANDARD' }, { value: 'large', label: 'LARGE' }] },\n"
        "  { key: 'tips', label: 'Hover explainers', hint: 'How long before they appear, or turn them off.',\n"
        "    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'slow', label: 'SLOW' }, { value: 'off', label: 'OFF' }] },\n"
        "  { key: 'motion', label: 'Animation', hint: 'Turn off movement and fades across the app.',\n"
        "    options: [{ value: 'full', label: 'ON' }, { value: 'reduced', label: 'REDUCED' }] },\n"
        "  { key: 'contrast', label: 'Table contrast', hint: 'Stronger row lines for low-quality monitors.',\n"
        "    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'high', label: 'HIGH' }] },\n"
        "  { key: 'notifPoll', label: 'Notification refresh', hint: 'How often the bell checks for new signals in the background.',\n"
        "    options: [{ value: '300', label: '5 MIN' }, { value: '900', label: '15 MIN' }, { value: '0', label: 'MANUAL' }] },\n"
        "];",

        "const PREF_GROUPS = [\n"
        "  { key: 'theme', group: 'Display', label: 'Page theme', hint: 'Background and chrome. Panels stay navy in both.',\n"
        "    options: [{ value: 'light', label: 'CREAM' }, { value: 'dark', label: 'SLATE' }] },\n"
        "  { key: 'uiScale', group: 'Display', label: 'Interface size', hint: 'Scales the whole app, not just text.',\n"
        "    options: [{ value: '90', label: '90%' }, { value: '100', label: '100%' }, { value: '110', label: '110%' }, { value: '125', label: '125%' }] },\n"
        "  { key: 'statSize', group: 'Display', label: 'Summary box size', hint: 'The figures at the top of Payments, Expenses and the dossier.',\n"
        "    options: [{ value: 'small', label: 'SMALL' }, { value: 'standard', label: 'STANDARD' }, { value: 'large', label: 'LARGE' }] },\n"
        "  { key: 'tips', group: 'Interaction', label: 'Hover explainers', hint: 'How long before they appear, or turn them off.',\n"
        "    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'slow', label: 'SLOW' }, { value: 'off', label: 'OFF' }] },\n"
        "  { key: 'motion', group: 'Interaction', label: 'Animation', hint: 'Turn off movement and fades across the app.',\n"
        "    options: [{ value: 'full', label: 'ON' }, { value: 'reduced', label: 'REDUCED' }] },\n"
        "  { key: 'contrast', group: 'Interaction', label: 'Table contrast', hint: 'Stronger row lines for low-quality monitors.',\n"
        "    options: [{ value: 'normal', label: 'NORMAL' }, { value: 'high', label: 'HIGH' }] },\n"
        "  { key: 'notifPoll', group: 'Notifications', label: 'Notification refresh', hint: 'How often the bell checks for new signals in the background.',\n"
        "    options: [{ value: '300', label: '5 MIN' }, { value: '900', label: '15 MIN' }, { value: '0', label: 'MANUAL' }] },\n"
        "];",

        "PREF_GROUPS entries tagged with group (Display/Interaction/Notifications)",
    ),
    (
        # render a .prefGroupLabel whenever the group changes.
        "                {PREF_GROUPS.map(group => (\n"
        "                  <div key={group.key} className={styles.prefRow}>\n"
        "                    <div className={styles.prefLabel}>\n"
        "                      <strong>{group.label}</strong>\n"
        "                      <span>{group.hint}</span>\n"
        "                    </div>\n"
        "                    <div className={styles.prefOptions} role=\"group\" aria-label={group.label}>\n"
        "                      {group.options.map(opt => (\n"
        "                        <button\n"
        "                          key={opt.value}\n"
        "                          type=\"button\"\n"
        "                          className={prefs[group.key] === opt.value ? styles.prefBtnActive : styles.prefBtn}\n"
        "                          aria-pressed={prefs[group.key] === opt.value}\n"
        "                          onClick={() => setPref(group.key, opt.value)}\n"
        "                        >\n"
        "                          {opt.label}\n"
        "                        </button>\n"
        "                      ))}\n"
        "                    </div>\n"
        "                  </div>\n"
        "                ))}",

        "                {PREF_GROUPS.map((group, i) => (\n"
        "                  <React.Fragment key={group.key}>\n"
        "                    {group.group !== PREF_GROUPS[i - 1]?.group && (\n"
        "                      <div className={styles.prefGroupLabel}>{group.group}</div>\n"
        "                    )}\n"
        "                    <div className={styles.prefRow}>\n"
        "                      <div className={styles.prefLabel}>\n"
        "                        <strong>{group.label}</strong>\n"
        "                        <span>{group.hint}</span>\n"
        "                      </div>\n"
        "                      <div className={styles.prefOptions} role=\"group\" aria-label={group.label}>\n"
        "                        {group.options.map(opt => (\n"
        "                          <button\n"
        "                            key={opt.value}\n"
        "                            type=\"button\"\n"
        "                            className={prefs[group.key] === opt.value ? styles.prefBtnActive : styles.prefBtn}\n"
        "                            aria-pressed={prefs[group.key] === opt.value}\n"
        "                            onClick={() => setPref(group.key, opt.value)}\n"
        "                          >\n"
        "                            {opt.label}\n"
        "                          </button>\n"
        "                        ))}\n"
        "                      </div>\n"
        "                    </div>\n"
        "                  </React.Fragment>\n"
        "                ))}",

        "Appearance list now renders a .prefGroupLabel before each new group",
    ),
    (
        # Provision Operator CREATE button -- HardwareModal portals to
        # document.body, outside .container in the DOM, so the page's
        # --btn-height token never reaches it. Swap the oversized
        # HardwareButton (48px default) for the app's own modalBtnPrimary
        # convention, already used by every other modal footer.
        "        <div className={styles.modalCenter}>\n"
        "          <HardwareButton onClick={createOp} icon={FiUserPlus} disabled={!newOp.username || !newOp.email}>CREATE</HardwareButton>\n"
        "        </div>",

        "        <div className={styles.modalCenter}>\n"
        "          <button type=\"button\" className={modalStyles.modalBtnPrimary} onClick={createOp} disabled={!newOp.username || !newOp.email}>\n"
        "            <FiUserPlus aria-hidden=\"true\" /> CREATE\n"
        "          </button>\n"
        "        </div>",

        "CREATE button swapped from oversized HardwareButton to modalBtnPrimary",
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
git("commit", "-m", "fix125: Settings page redesign -- Report Studio dimension parity (--input-height/--btn-height tokens were unset, controls were silently falling back to Hardware*'s own bigger defaults), wipeField/dualRow width caps, Appearance split into Display/Interaction/Notifications sub-groups, Provision Operator CREATE button swapped from oversized HardwareButton to the app's own modalBtnPrimary")
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