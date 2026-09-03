# fix.py — fix52: element-by-element Intake parity (CollapsibleSection/CornerDecor/HardwareButton)
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
def find(name):
    for r, d, fs in os.walk(FE):
        if name in fs: return os.path.join(r, name)
    return None
jsx = find("FolderPage.jsx"); hb = None
for r, d, fs in os.walk(FE):
    if "HardwareButton.module.css" in fs: hb = os.path.join(r, "HardwareButton.module.css"); break
css = find("FolderPage.module.css")
if not (jsx and css and hb):
    print("ABORT: files missing.", jsx, css, hb); sys.exit(1)
for p in (jsx, css, hb): shutil.copy2(p, os.path.join(ROOT, ".fix_backup", os.path.basename(p) + ".bak"))

# ---- 1) JSX: import + mount real CornerDecor in every panel ----
src = open(jsx, "r", encoding="utf-8").read()
if "CornerDecor" not in src:
    anchor = "import BackToTopButton from '../../components/common/BackToTopButton';"
    if anchor not in src: print("ABORT: import anchor missing."); sys.exit(1)
    src = src.replace(anchor, anchor + "\nimport CornerDecor from '../../components/ui/CornerDecor';", 1)
    n = src.count("<div className={styles.panelInner}>")
    src = src.replace("<div className={styles.panelInner}>",
                      "<div className={styles.panelInner}>\n<CornerDecor hideTop />")
    print("JSX: CornerDecor mounted in %d panels." % n)
    open(jsx, "w", encoding="utf-8").write(src)
else:
    print("JSX: CornerDecor already present.")

# ---- 2) HardwareButton: Intake behaviour (white text, no scale-hover, d97a2b hover) ----
h = open(hb, "r", encoding="utf-8").read()
h2 = re.sub(r"\.btn:hover:not\(:disabled\)\s*\{\s*transform:\s*translateY\(-3px\) scale\(1\.03\);\s*\}",
            ".btn:hover:not(:disabled) { transform: none; }", h)
h2 = re.sub(r"\.primary\s*\{\s*background:\s*var\(--orange\);\s*color:\s*var\(--navy\);\s*box-shadow:[^;]+;\s*\}",
            ".primary { background: var(--orange, #EE8C3A); color: #fff; box-shadow: 0 4px 12px rgba(238,140,58,0.3); }", h2)
h2 = re.sub(r"\.primary:hover\s*\{\s*background:\s*#f59a4a;\s*box-shadow:[^;]+;\s*\}",
            ".primary:hover { background: #d97a2b; box-shadow: 0 4px 12px rgba(238,140,58,0.3); }", h2)
if h2 != h:
    open(hb, "w", encoding="utf-8").write(h2); print("HB: HardwareButton aligned to Intake.")
else:
    print("HB: already aligned or patterns not found (check manually).")

# ---- 3) Folder CSS v5: exact CollapsibleSection port ----
c = open(css, "r", encoding="utf-8").read()
if "FS-UNIFY v5" not in c:
    c += '''
/* FS-UNIFY v5 — exact CollapsibleSection/Intake parity */
.container{--btn-height:clamp(32px,4vw,38px);--btn-px:clamp(10px,1.4vw,16px);--btn-font:clamp(8px,0.85vw,10px);--input-radius:6px;}
.hwPanel{
  background:linear-gradient(135deg,#3a5a5c 0%,#2a4a4c 50%,#213E40 100%);
  border:1px solid rgba(238,140,58,0.2);border-radius:10px;
  box-shadow:0 6px 24px rgba(0,0,0,0.25);
  transition:border-color .3s ease,box-shadow .3s ease;
}
.hwPanel:hover{border-color:#EE8C3A;box-shadow:0 8px 32px rgba(0,0,0,0.3);}
.hwPanel::before,.hwPanel::after{content:none;}
.drawerHeader{background:#162a2c;border-bottom:1.5px solid transparent;border-radius:9px 9px 0 0;padding:clamp(8px,1.1vw,12px) clamp(10px,1.4vw,16px);}
.drawerHeader[aria-expanded="true"]{border-bottom-color:#EE8C3A;}
.drawerTitle{font-family:'Cinzel',serif;font-size:clamp(10px,1.3vw,13px);font-weight:700;color:#EE8C3A;letter-spacing:2px;text-transform:uppercase;}
.drawerHeader:hover .drawerTitle{color:#fff;}
.drawerIcon{color:#EE8C3A;filter:drop-shadow(0 0 4px rgba(238,140,58,0.4));font-size:clamp(12px,1.4vw,16px);}
.chevron{color:rgba(255,255,255,0.4);font-size:14px;}
.chevron.rotated{color:#EE8C3A;}
.panelInner{position:relative;background:transparent;padding:clamp(10px,1.4vw,16px);display:flex;flex-direction:column;gap:clamp(7px,1.1vw,14px);}
.specItem{border-left:none;padding:0;}
.currencyTag,.autoCalcBadge{background:none;border:none;box-shadow:none;color:rgba(255,255,255,0.35);font-size:var(--fs-meta);font-weight:700;letter-spacing:0.5px;padding:0;text-transform:uppercase;}
.drawerCount{background:none;border:none;color:rgba(255,255,255,0.4);font-size:var(--fs-meta);padding:0;}
.idPlate h1{font-size:var(--fs-h1);letter-spacing:2px;}
.tabBtn{padding:clamp(6px,0.9vw,9px) clamp(10px,1.4vw,16px);}
.unlockMasterBtn,.btnPrimary{box-shadow:0 4px 12px rgba(238,140,58,0.3);}
.unlockMasterBtn:hover,.btnPrimary:hover{background:#d97a2b;border-color:#d97a2b;color:#fff;box-shadow:0 4px 12px rgba(238,140,58,0.3);}
'''
    open(css, "w", encoding="utf-8").write(c); print("CSS: v5 appended.")

# ---- 4) esbuild gate + commit ----
fe_root = os.path.dirname(FE); esb = os.path.join(fe_root, "node_modules", ".bin", "esbuild")
if os.path.exists(esb):
    chk = subprocess.run([esb, jsx, "--loader:.jsx=jsx", "--outfile=" + os.path.join(ROOT, ".jsx_check.js")], capture_output=True, text=True)
    if chk.returncode != 0:
        print("ABORT: JSX broken — nothing pushed."); print(chk.stderr[:1500]); sys.exit(1)
    print("VERIFY: esbuild OK.")
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix52: exact Intake parity — CornerDecor, CollapsibleSection values, HardwareButton norms"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")