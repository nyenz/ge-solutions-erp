# fix.py — fix48: Intake tone alignment (Overview) + Notes own section
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
BACKUP = os.path.join(ROOT, ".fix_backup")
os.makedirs(BACKUP, exist_ok=True)

def find(name, base):
    for r, d, fs in os.walk(base):
        if name in fs: return os.path.join(r, name)
    return None
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)

jsx_path = find("FolderPage.jsx", FE)
css_path = find("FolderPage.module.css", FE)
if not jsx_path or not css_path:
    print("ABORT: FolderPage files not found."); sys.exit(1)
shutil.copy2(jsx_path, BACKUP); shutil.copy2(css_path, BACKUP)
src = read(jsx_path)
changed = False

# ---- 1) TABS: add NOTES ----
old_tabs = "const TABS = ['OVERVIEW', 'FINANCIALS', 'OWNERS', 'DOCUMENTS'];"
new_tabs = "const TABS = ['OVERVIEW', 'FINANCIALS', 'NOTES', 'OWNERS', 'DOCUMENTS'];"
if old_tabs in src:
    src = src.replace(old_tabs, new_tabs, 1); changed = True
elif new_tabs in src:
    print("NOTE: NOTES tab already present.")
else:
    print("ABORT: TABS anchor not found."); sys.exit(1)

# ---- 2) hash deep-link for notes ----
old_hash = "} else if (hash === 'identity' || hash === 'owners') setActiveTab('OWNERS');"
new_hash = "} else if (hash === 'notes' || hash === 'calls') setActiveTab('NOTES');\n        " + old_hash
if old_hash in src and "hash === 'notes'" not in src:
    src = src.replace(old_hash, new_hash, 1); changed = True

# ---- 3) Move Notes section out of FINANCIALS into its own tab ----
if "aria-label=\"Notes and Call Log\"" in src and "<div style={activeTab !== 'NOTES'" not in src:
    m = re.search(
        r'(?P<pre>[\s\S]*?)(?P<notes>[ \t]*<section className=\{styles\.hwPanel\} aria-label="Notes and Call Log">[\s\S]*?</section>)\n(?P<close>[ \t]*</div>)\n(?P<owners>[ \t]*<section className=\{styles\.hwPanel\} aria-label="Owners")',
        src)
    if not m:
        print("ABORT: could not isolate Notes section safely."); sys.exit(1)
    wrapped = (m.group('close').rstrip() and "") or ""
    notes_block = m.group('notes')
    src = (m.group('pre') + m.group('close') + "\n"
           + "                <div style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>\n"
           + notes_block + "\n                </div>\n"
           + m.group('owners') + src[m.end():])
    changed = True
    print("MOVED: Notes & Call Log now its own NOTES tab.")
else:
    print("NOTE: Notes section already moved or not found — skipping.")

if changed:
    write(jsx_path, src)
    print("WROTE: FolderPage.jsx")

# ---- 4) CSS: Intake tone alignment for Overview + fields ----
css = read(css_path)
if "FS-UNIFY v2" not in css:
    css += '''
/* FS-UNIFY v2 — Intake tone alignment (section headers, fields, tabs) */
.drawerHeader{border-bottom:1px solid rgba(238,140,58,.55);}
.drawerTitle{font-family:'Cinzel',serif;color:var(--fs-orange);letter-spacing:.08em;text-transform:uppercase;font-weight:700;}
.drawerIcon{color:var(--fs-orange);}
.chevron{color:var(--fs-orange);}
.specLabel{color:var(--fs-muted);letter-spacing:1.5px;text-transform:uppercase;}
.specValue{color:var(--fs-orange);font-family:'Space Mono',monospace;}
.hwInput{background:#fff;color:#122a28;border:1.5px solid #c8d6d7;border-radius:8px;}
.hwInput::placeholder{color:#9aa8a6;}
.selectTrigger{background:#fff;color:#122a28;border:1.5px solid #c8d6d7;border-radius:8px;}
.selectValue{color:#122a28;}
.inputLabelRow label{color:rgba(255,255,255,.85);letter-spacing:1.2px;text-transform:uppercase;font-size:10px;font-weight:700;}
.reqStar{color:var(--fs-orange);}
.currencyTag{color:var(--fs-orange);}
.tabBtn{background:#20403c;color:#fff;border:1px solid rgba(255,255,255,.12);}
.tabBtnActive{background:var(--fs-orange);color:#1a2e30;border-color:var(--fs-orange);}
.ctrlBtnPay{background:#20403c;color:#fff;border:1px solid rgba(255,255,255,.18);}
.unlockMasterBtn{background:var(--fs-orange);color:#1a2e30;}
.panelInner{background:transparent;}
.stageName{color:#fff;}
.stageCost{color:var(--fs-muted);}
'''
    write(css_path, css)
    print("APPENDED: FS-UNIFY v2 CSS.")
else:
    print("SKIPPED CSS: v2 already present.")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix48: intake tone alignment (overview) + notes own tab"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: committed and pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")