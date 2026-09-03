# fix.py — fix53: feedback pass (dropdown, caps, convert toggle, badges, notes-last, popup parity, X default)
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
def find(name):
    for r, d, fs in os.walk(FE):
        if name in fs: return os.path.join(r, name)
    return None
jsx = find("FolderPage.jsx"); fcss = find("FolderPage.module.css")
hmodal = find("HardwareModal.module.css"); icss = find("IntakePage.module.css")
if not (jsx and fcss and hmodal and icss):
    print("ABORT: missing files.", jsx, fcss, hmodal, icss); sys.exit(1)
for p in (jsx, fcss, hmodal, icss): shutil.copy2(p, os.path.join(ROOT, ".fix_backup", os.path.basename(p) + ".bak"))

# ================= JSX =================
src = open(jsx, "r", encoding="utf-8").read(); changed = False

# 1) TABS: Notes last
old_t = "const TABS = ['OVERVIEW', 'FINANCIALS', 'NOTES', 'OWNERS', 'DOCUMENTS'];"
new_t = "const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS', 'NOTES'];"
if old_t in src: src = src.replace(old_t, new_t, 1); changed = True

# 2) Move Notes block to after Documents (before </main>)
m = re.search(r"(?P<notes>                <div style=\{activeTab !== 'NOTES' \? \{ display: 'none' \} : \{\}\}>[\s\S]*?                </div>)\n(?P<owners>                <section className=\{styles\.hwPanel\} aria-label=\"Owners\")", src)
if m:
    notes = m.group('notes')
    src = src[:m.start('notes')] + m.group('owners') + src[m.end('owners'):]
    src = re.sub(r"(                </section>\n            </main>)", notes + "\n\\1", src, count=1)
    changed = True; print("JSX: Notes moved after Documents.")
else:
    print("NOTE: notes-move anchor not found (check order).")

# 3) Convert button: own class + toggle wording
old_cb = re.search(r"<button type=\"button\" className=\{`\$\{styles\.payTypeBtn\} \$\{buffer\.convertToTitle \? styles\.payTypeBtnActive : ''\}`\}\n(\s+)onClick=\{\(\) => touchedSetBuffer\(p => \(\{ \.\.\.p, convertToTitle: !p\.convertToTitle \}\)\)\}><FiCheckCircle aria-hidden=\"true\" /> CONVERT TO TITLE</button>", src)
if old_cb:
    src = src[:old_cb.start()] + ("<button type=\"button\" className={`${styles.convertBtn} ${buffer.convertToTitle ? styles.convertBtnActive : ''}`}\n" + old_cb.group(1) + "onClick={() => touchedSetBuffer(p => ({ ...p, convertToTitle: !p.convertToTitle }))}><FiCheckCircle aria-hidden=\"true\" /> {buffer.convertToTitle ? 'CONVERT TO FOLDER' : 'CONVERT TO TITLE'}</button>") + src[old_cb.end():]
    changed = True; print("JSX: convert button wording toggles.")
else:
    print("NOTE: convert button anchor not found.")

# 4) Remove redundant PROJECT # pill; add LEGACY badge
pill = "{project.projectIndex && <span className={`${styles.metaTag} ${styles.tagBlue}`}>PROJECT #{project.projectIndex}</span>}"
if pill in src: src = src.replace(pill, "", 1); changed = True
rel_line = "{project.landTitle?.isReleased && <span className={`${styles.textBadge} ${styles.badgeTitled}`}>RELEASED</span>}"
if rel_line in src and "badgeLegacy" not in src:
    src = src.replace(rel_line, rel_line + "\n                        {project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}", 1); changed = True
if changed: open(jsx, "w", encoding="utf-8").write(src); print("JSX: written.")

# ================= FOLDER CSS v6 =================
c = open(fcss, "r", encoding="utf-8").read()
if "FS-UNIFY v6" not in c:
    c += '''
/* FS-UNIFY v6 — feedback pass */
.bodyOpen{overflow:visible;}
.capsBadge{background:none;border:none;box-shadow:none;border-radius:0;color:rgba(255,255,255,0.35);font-size:8px;font-weight:700;letter-spacing:0.5px;padding:0;}
.convertBtn{display:flex;align-items:center;gap:5px;background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px);border-radius:6px;font-family:'Inter',sans-serif;font-weight:900;font-size:var(--fs-btn);letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;transition:all .2s ease;white-space:nowrap;}
.convertBtn:hover{background:rgba(238,140,58,0.12);color:#EE8C3A;border-color:#EE8C3A;}
.convertBtnActive,.convertBtnActive:hover{background:#EE8C3A;color:#1a2e30;border-color:#EE8C3A;box-shadow:0 0 14px rgba(238,140,58,0.4);}
.badgeActive{color:#213E40;}
.badgeLegacy{color:#64748b;}
.selectValue{font-size:var(--input-font);font-weight:600;}
.selectDropdown{position:absolute;z-index:600;margin-top:4px;max-height:240px;overflow:auto;background:#ffffff;border:1.5px solid rgba(238,140,58,0.3);border-radius:6px;box-shadow:0 8px 24px rgba(0,0,0,0.25);list-style:none;padding:0;}
.selectOption{color:#213E40;font-family:'Inter',sans-serif;font-weight:600;font-size:var(--input-font);padding:8px var(--input-px);cursor:pointer;}
.selectOption:hover{background:rgba(238,140,58,0.12);}
.selectOptionActive,.selectOptionActive:hover{background:#EE8C3A;color:#1a2e30;}
'''
    open(fcss, "w", encoding="utf-8").write(c); print("CSS: v6 appended.")

# ================= HardwareModal: Intake-white inputs + proportioned footer buttons =================
h = open(hmodal, "r", encoding="utf-8").read()
if "INTAKE-PORT v1" not in h:
    h += '''
/* INTAKE-PORT v1 — white Intake inputs + proportional buttons in all modals */
.modalInput,.modalTextarea{font-family:'Inter',sans-serif;font-weight:600;border:1.5px solid rgba(238,140,58,0.3);background:#ffffff;color:#213E40;border-radius:6px;font-size:clamp(11px,1.05vw,13px);padding:clamp(9px,1.2vw,13px);}
.modalInput::placeholder,.modalTextarea::placeholder{color:#9aa8a6;}
.modalBtnPrimary,.modalBtnSecondary{height:var(--btn-height,clamp(32px,4vw,38px));padding:0 clamp(10px,1.4vw,16px);font-family:'Inter',sans-serif;font-weight:900;font-size:var(--btn-font,clamp(8px,0.85vw,10px));letter-spacing:1.5px;text-transform:uppercase;border-radius:6px;}
'''
    open(hmodal, "w", encoding="utf-8").write(h); print("MODAL: inputs/buttons ported.")

# ================= Intake: app-default X (copied verbatim from HardwareModal at runtime) =================
i = open(icss, "r", encoding="utf-8").read()
if "INTAKE-PORT v1" not in i:
    close_rule = re.search(r"(\.[A-Za-z0-9_-]*close[A-Za-z0-9_-]*\s*\{[^}]*\})", h, re.I)
    anim = None
    if close_rule:
        am = re.search(r"animation:\s*([A-Za-z0-9_-]+)", close_rule.group(1))
        if am:
            kb = re.search(r"(@keyframes\s+" + am.group(1) + r"\s*\{[\s\S]*?\n\})", h)
            anim = kb.group(1) if kb else None
    block = "\n/* INTAKE-PORT v1 — app-default close X (verbatim from HardwareModal) */\n"
    if close_rule:
        decls = close_rule.group(1)
        block += ".xBtn" + decls[decls.index('{'):] + "\n"
        if anim: block += anim + "\n"
        block += ".xBtn:hover{transform:rotate(90deg);}\n"
    else:
        block += ".xBtn{background:rgba(239,68,68,0.12);border:1.5px solid rgba(239,68,68,0.45);color:#ef4444;border-radius:8px;padding:6px;transition:all .2s;}\n.xBtn:hover{background:#ef4444;color:#fff;transform:rotate(90deg);}\n"
    open(icss, "w", encoding="utf-8").write(i + block)
    print("INTAKE: X default ported.")

# ================= gate + push =================
fe_root = os.path.dirname(FE); esb = os.path.join(fe_root, "node_modules", ".bin", "esbuild")
if os.path.exists(esb):
    chk = subprocess.run([esb, jsx, "--loader:.jsx=jsx", "--outfile=" + os.path.join(ROOT, ".jsx_check.js")], capture_output=True, text=True)
    if chk.returncode != 0:
        print("ABORT: JSX broken — nothing pushed."); print(chk.stderr[:1500]); sys.exit(1)
    print("VERIFY: esbuild OK.")
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix53: feedback pass — dropdown fix, caps restyle, convert toggle, badges, notes last, popup parity, X default"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")