# fix.py — fix56: clean duplicate NOTES wrapper, dead onCommit, restore ADDRESS, verify css+backend
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
BE = os.path.join(ROOT, "erp-backend", "src", "main", "java", "com", "gesolutions", "erp")
def find(name, base):
    for r, d, fs in os.walk(base):
        if name in fs: return os.path.join(r, name)
    return None
jsx = find("FolderPage.jsx", FE); fcss = find("FolderPage.module.css", FE)
ctrl = find("FolderPortalController.java", BE)
if not (jsx and fcss and ctrl):
    print("ABORT: files missing."); sys.exit(1)
for p in (jsx, fcss, ctrl): shutil.copy2(p, os.path.join(ROOT, ".fix_backup", os.path.basename(p) + ".bak56"))

src = open(jsx, "r", encoding="utf-8").read(); changed = False

# 1) Remove the EMPTY duplicate NOTES wrapper
n1 = len(src)
src = re.sub(r"<div style=\{activeTab !== 'NOTES' \? \{ display: 'none' \} : \{\}\}>\s*</div>", "", src)
if len(src) != n1: changed = True; print("JSX: empty NOTES wrapper removed.")

# 2) Remove dead onCommit prop
if "handleEmailCommit" in src:
    src = src.replace(" onCommit={val => handleEmailCommit(idx,val)}", ""); changed = True
    print("JSX: dead onCommit removed.")

# 3) Restore ADDRESS input in owner edit card (after EMAIL input)
EMAIL_LINE = "id={`owner_${idx}_email`} />"
if EMAIL_LINE in src and "owner_' + idx + '_addr" not in src and "owner_${idx}_addr" not in src:
    src = src.replace(EMAIL_LINE, EMAIL_LINE + "\n                                <SmartInput label=\"ADDRESS\" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />", 1)
    changed = True; print("JSX: ADDRESS field restored.")

if changed: open(jsx, "w", encoding="utf-8").write(src); print("JSX written.")

# 4) Verify CSS v7 present
c = open(fcss, "r", encoding="utf-8").read()
if "FS-UNIFY v7" not in c or ".statRed" not in c:
    c += '''
/* FS-UNIFY v7 (re-verified by fix56) */
.container{--fs-green:#10b981;--fs-red:#ef4444;}
.hwPanel{border-radius:10px !important;}
.drawerHeader[aria-expanded="false"]{border-radius:9px;}
.statRed label,.statRed strong{color:var(--fs-red) !important;}
.textBadge{background:rgba(238,140,58,0.10);border:1px solid rgba(238,140,58,0.35);border-radius:999px;padding:3px 9px;font-family:'Inter',sans-serif;}
.badgeBacklog{color:#EE8C3A;background:rgba(238,140,58,0.10);border-color:rgba(238,140,58,0.35);}
.badgeTitled{color:#10b981;background:rgba(16,185,129,0.10);border-color:rgba(16,185,129,0.35);}
.badgeRecv{color:#ef4444;background:rgba(239,68,68,0.10);border-color:rgba(239,68,68,0.35);}
.badgeActive{color:#213E40;background:rgba(33,62,64,0.10);border-color:rgba(33,62,64,0.35);}
.badgeLegacy{color:#64748b;background:rgba(100,116,139,0.12);border-color:rgba(100,116,139,0.35);}
.badgePaused{color:#06b6d4;background:rgba(6,182,212,0.10);border-color:rgba(6,182,212,0.35);}
.ownerPortfolio{margin-top:10px;border-top:1px solid rgba(255,255,255,0.08);padding-top:8px;}
.confirmBox{position:relative;}
@keyframes xPop{from{transform:rotate(0)}to{transform:rotate(90deg)}}
.confirmClose{position:absolute;top:10px;right:10px;background:rgba(239,68,68,0.12);border:1.5px solid rgba(239,68,68,0.45);color:#ef4444;border-radius:8px;padding:6px;cursor:pointer;transition:all .2s;display:inline-flex;}
.confirmClose:hover{background:#ef4444;color:#fff;animation:xPop .2s ease forwards;}
'''
    open(fcss, "w", encoding="utf-8").write(c); print("CSS: v7 verified/re-applied.")
else:
    print("CSS: v7 already present.")

# 5) Verify backend billing fix
ct = open(ctrl, "r", encoding="utf-8").read()
if "setReceivableMonthsBilled(0)" not in ct:
    old_e = "        p.setReceivable(true);\n        if (p.getReceivableStartDate() == null) p.setReceivableStartDate(LocalDateTime.now());"
    new_e = "        p.setReceivable(true);\n        p.setReceivableStartDate(LocalDateTime.now());\n        p.setReceivableMonthsBilled(0);"
    if old_e in ct:
        open(ctrl, "w", encoding="utf-8").write(ct.replace(old_e, new_e, 1)); print("BACKEND: billing clock fix applied.")
    else:
        print("WARN: backend enter() pattern not found — check manually.")
else:
    print("BACKEND: billing fix already present.")

# 6) esbuild gate + push
fe_root = os.path.dirname(FE); esb = os.path.join(fe_root, "node_modules", ".bin", "esbuild")
if os.path.exists(esb):
    chk = subprocess.run([esb, jsx, "--loader:.jsx=jsx", "--outfile=" + os.path.join(ROOT, ".jsx_check.js")], capture_output=True, text=True)
    if chk.returncode != 0:
        print("ABORT: JSX broken — nothing pushed."); print(chk.stderr[:1500]); sys.exit(1)
    print("VERIFY: esbuild OK.")
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix56: clean notes wrapper, dead onCommit, restore address, verify css/backend"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")