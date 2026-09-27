#!/usr/bin/env python3
# PATH: fix127.py
# GOLDEN SEED -- fix127: four Settings-page fixes, all against the
#   Intake/Reports design language that's already the app's baseline.
#   1. Appearance's seven settings were one flat dark list ("too many
#      things at once"). They now render as three lighter cream cards
#      (Report Catalogue's own #f2ede4 tone) -- Display / Interaction /
#      Notifications each get their own box, two-up on wide screens.
#      Same shade-play idea Owners' rgba(0,0,0,0.15) row already uses,
#      just lighter instead of darker, so the panel isn't uniformly
#      dark end to end.
#   2. Collapsed panelHeadRow was always using the "open" top-only
#      radius (11px 11px 0 0) -- the square bottom corners poked out
#      past the card's own 12px rounded corners whenever a tab was
#      collapsed. Report Studio's panelCollapsed already avoids this;
#      Settings now gets the same [aria-expanded="false"] -> full-radius
#      rule.
#   3. Staff's purple (--violet) is now a green; Archive's slate-grey
#      (--slate) is now a yellow. Both tokens are scoped to this one
#      CSS module and only ever drove Staff/Archive visuals (tab pill,
#      card accent, rank-menu, kill-switch focus rings), so recoloring
#      the two tokens (plus their hardcoded rgba() shadow fallbacks and
#      the one literal hex on .rankSecretary) recolors both sections
#      everywhere without touching anything else.
#   4. Not touched: the panelHeadRow title-on-hover-turns-white rule
#      already matches Intake's CollapsibleSection (.header:hover
#      .title { color: #fff }) line for line -- nothing to change there.
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

SETTINGS_JSX = os.path.join(SRC, "pages", "settings", "SettingsPage.jsx")
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


# ═══ SettingsPage.jsx ═══
apply_patches(SETTINGS_JSX, [
    (
        # 1. group PREF_GROUPS into named sections once, instead of
        # re-diffing against the previous row every render.
        "];\n\nconst SettingsPage = () => {",

        "];\n\n"
        "/* fix127: group PREF_GROUPS into named sections so Appearance\n"
        "   renders as three separated cards instead of one long flat\n"
        "   list -- same data, grouped once instead of re-diffed against\n"
        "   the previous row every render. */\n"
        "const PREF_SECTIONS = ['Display', 'Interaction', 'Notifications'].map(name => ({\n"
        "  name,\n"
        "  items: PREF_GROUPS.filter(g => g.group === name),\n"
        "}));\n\n"
        "const SettingsPage = () => {",

        "PREF_SECTIONS grouping helper added",
    ),
    (
        # 2. Appearance tab: flat list -> three cream cards.
        "            {tab === 'appearance' && (\n"
        "              <>\n"
        "                <div className={styles.securityAlert}><FiMonitor aria-hidden=\"true\" /><span>These are saved on this device, not on your account -- the office shares logins across a desktop and two phones, and \"this screen is too small to read\" is a fact about the screen.</span></div>\n"
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
        "                ))}\n"
        "                <div className={styles.submitRow}>\n"
        "                  <button type=\"button\" className={styles.commitBtn} onClick={resetPrefs}><FiRotateCcw aria-hidden=\"true\" /> RESET APPEARANCE</button>\n"
        "                </div>\n"
        "              </>\n"
        "            )}",

        "            {tab === 'appearance' && (\n"
        "              <>\n"
        "                <div className={styles.securityAlert}><FiMonitor aria-hidden=\"true\" /><span>These are saved on this device, not on your account -- the office shares logins across a desktop and two phones, and \"this screen is too small to read\" is a fact about the screen.</span></div>\n"
        "                {/* fix127: three lighter cream cards (Report Catalogue's own\n"
        "                    #f2ede4 tone) instead of one long dark list -- each\n"
        "                    section groups its own rows so Appearance reads as\n"
        "                    organised clusters, not seven settings in a row. */}\n"
        "                <div className={styles.prefSectionsGrid}>\n"
        "                  {PREF_SECTIONS.map(section => (\n"
        "                    <div key={section.name} className={styles.prefGroupBox}>\n"
        "                      <div className={styles.prefGroupLabel}>{section.name}</div>\n"
        "                      {section.items.map(group => (\n"
        "                        <div key={group.key} className={styles.prefRow}>\n"
        "                          <div className={styles.prefLabel}>\n"
        "                            <strong>{group.label}</strong>\n"
        "                            <span>{group.hint}</span>\n"
        "                          </div>\n"
        "                          <div className={styles.prefOptions} role=\"group\" aria-label={group.label}>\n"
        "                            {group.options.map(opt => (\n"
        "                              <button\n"
        "                                key={opt.value}\n"
        "                                type=\"button\"\n"
        "                                className={prefs[group.key] === opt.value ? styles.prefBtnActive : styles.prefBtn}\n"
        "                                aria-pressed={prefs[group.key] === opt.value}\n"
        "                                onClick={() => setPref(group.key, opt.value)}\n"
        "                              >\n"
        "                                {opt.label}\n"
        "                              </button>\n"
        "                            ))}\n"
        "                          </div>\n"
        "                        </div>\n"
        "                      ))}\n"
        "                    </div>\n"
        "                  ))}\n"
        "                </div>\n"
        "                <div className={styles.submitRow}>\n"
        "                  <button type=\"button\" className={styles.commitBtn} onClick={resetPrefs}><FiRotateCcw aria-hidden=\"true\" /> RESET APPEARANCE</button>\n"
        "                </div>\n"
        "              </>\n"
        "            )}",

        "Appearance tab rewired to render PREF_SECTIONS as prefGroupBox cards instead of a flat PREF_GROUPS list",
    ),
])

# ═══ SettingsPage.module.css ═══
apply_patches(SETTINGS_CSS, [
    (
        # 3. Staff: purple -> green. Archive: slate-grey -> yellow.
        "    --violet:        #a78bfa;\n"
        "    --slate:         #94a3b8;",

        "    --violet:        #34d399; /* fix127: Staff, was purple #a78bfa */\n"
        "    --slate:         #eab308; /* fix127: Archive, was grey #94a3b8 */",

        "Staff/Archive token recolor: violet->green, slate->yellow",
    ),
    (
        "rgba(167,139,250,0.32)", "rgba(52,211,153,0.32)",
        "Staff tab-on box-shadow recolor",
    ),
    (
        "rgba(167,139,250,0.14)", "rgba(52,211,153,0.14)",
        "Staff add-operator hover recolor",
    ),
    (
        "rgba(167,139,250,0.16)", "rgba(52,211,153,0.16)",
        "Staff rank-menu-item hover recolor",
    ),
    (
        "rgba(167,139,250,0.1)", "rgba(52,211,153,0.1)",
        "Staff rank-menu-item active recolor",
    ),
    (
        "rgba(148,163,184,0.32)", "rgba(234,179,8,0.32)",
        "Archive tab-on box-shadow recolor",
    ),
    (
        ".rankSecretary { font-family: 'Space Mono', monospace; color: #a78bfa; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; margin-top: clamp(2px,0.3vw,3px); display: block; }",
        ".rankSecretary { font-family: 'Space Mono', monospace; color: #4ade80; font-size: var(--fs-label); font-weight: 900; text-transform: uppercase; margin-top: clamp(2px,0.3vw,3px); display: block; }",
        "Secretary rank badge recolor off purple",
    ),
    (
        # 4. collapsed panelHeadRow was stuck on the open/top-only
        # radius -- square bottom corners poking past the card's own
        # rounded ones. Same fix Report Studio's panelCollapsed uses.
        ".panelHeadRowOpen { border-bottom-color: var(--accent); }",

        ".panelHeadRowOpen { border-bottom-color: var(--accent); }\n"
        "/* fix127: collapsed, the row was still using the open top-only\n"
        "   radius (11px 11px 0 0) -- its own square bottom corners then\n"
        "   poked out past the card's rounded ones whenever a tab was\n"
        "   collapsed. Same fix Report Studio's panelCollapsed already\n"
        "   applies: collapsed, the row goes back to being the whole\n"
        "   visible card, fully curved. */\n"
        ".panelHeadRow[aria-expanded=\"false\"] { border-radius: 11px; border-bottom-color: transparent; }",

        "panelHeadRow collapsed-state full-radius fix",
    ),
    (
        # 5. lighter cream cards for the three Appearance groups.
        "/* ── RESPONSIVE ─────────────────────────────────────────────────── */",

        "/* ── APPEARANCE GROUP CARDS (fix127) ───────────────────────────────\n"
        "   Report Catalogue's own #f2ede4 cream, not another dark box --\n"
        "   Display/Interaction/Notifications each get one, two-up on wide\n"
        "   screens, so the panel reads as three organised clusters instead\n"
        "   of one long dark list, and isn't uniformly dark end to end. */\n"
        ".prefSectionsGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--gap-lg); align-items: start; }\n"
        ".prefGroupBox {\n"
        "  background: #f2ede4; border: 1px solid rgba(26,46,48,0.14);\n"
        "  border-radius: var(--radius-sm); padding: clamp(10px,1.3vw,14px) clamp(12px,1.5vw,16px);\n"
        "  display: flex; flex-direction: column;\n"
        "}\n"
        ".prefGroupBox .prefGroupLabel { color: var(--accent, var(--orange)); opacity: 1; padding: 0 0 clamp(6px,0.8vw,9px); }\n"
        ".prefGroupBox .prefRow { border-bottom: 1px solid rgba(26,46,48,0.10); margin: 0; padding: clamp(8px,1.1vw,11px) 0; }\n"
        ".prefGroupBox .prefRow:hover { background: rgba(26,46,48,0.045); }\n"
        ".prefGroupBox .prefRow:last-child { border-bottom: none; }\n"
        ".prefGroupBox .prefLabel strong { color: #1a2e30; }\n"
        ".prefGroupBox .prefLabel span { color: rgba(26,46,48,0.65); }\n"
        ".prefGroupBox .prefBtn, .prefGroupBox .prefBtnActive { border: 1.5px solid rgba(26,46,48,0.2); background: rgba(255,255,255,0.65); color: rgba(26,46,48,0.85); }\n"
        ".prefGroupBox .prefBtn:hover { background: rgba(238,140,58,0.16); border-color: #EE8C3A; color: #EE8C3A; }\n"
        ".prefGroupBox .prefBtnActive { background: #EE8C3A; border-color: #EE8C3A; color: #1a2e30; }\n\n\n"
        "/* ── RESPONSIVE ─────────────────────────────────────────────────── */",

        "prefGroupBox/prefSectionsGrid cream-card styles added",
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
git("commit", "-m", "fix127: Settings Appearance regrouped into three cream cards (was one flat dark list); collapsed panelHeadRow corner-radius bug fixed; Staff purple -> green, Archive slate -> yellow")
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