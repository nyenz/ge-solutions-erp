# fix.py — fix54: receivable billing fix + structure repair + badge/button/popup polish
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
for p in (jsx, fcss, ctrl): shutil.copy2(p, os.path.join(ROOT, ".fix_backup", os.path.basename(p) + ".bak"))

def scan_block(src, open_tag_start, tag):
    """return (start, end) of the block starting at open_tag_start, matching </tag> by depth"""
    i = src.find(">", open_tag_start) + 1
    depth = 1; j = i
    while j < len(src) and depth:
        no = src.find("<" + tag, j); nc = src.find("</" + tag + ">", j)
        if nc == -1: break
        if no != -1 and no < nc:
            depth += 1; j = no + len(tag) + 1
        else:
            depth -= 1; j = nc + len(tag) + 3
    return (open_tag_start, j)

src = open(jsx, "r", encoding="utf-8").read(); changed = False

# ---- 1) NOTES block: lift out of wherever it is, place as sibling before </main> ----
NM = "<div style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>"
ni = src.find(NM)
if ni != -1:
    s, e = scan_block(src, ni, "div")
    block = src[s:e]
    rest = src[:s] + src[e:]
    anchor = "            </main>"
    if anchor in rest:
        src = rest.replace(anchor, block + "\n" + anchor, 1); changed = True
        print("JSX: Notes block re-positioned as own tab section.")
else:
    print("WARN: notes wrapper not found.")

# ---- 2) Hide Stage Checklist once titled / converting ----
SM = '<section className={styles.hwPanel} aria-label="Stage Checklist"'
si = src.find(SM)
if si != -1 and "{!project.landTitle && !buffer.convertToTitle && (" not in src[max(0,si-80):si]:
    s, e = scan_block(src, si, "section")
    wrapped = "{!project.landTitle && !buffer.convertToTitle && (\n" + src[s:e] + "\n                )}"
    src = src[:s] + wrapped + src[e:]; changed = True
    print("JSX: Stage checklist hidden for titled projects.")

# ---- 3) Shorter button wording ----
for a, b in [("+ INGEST NEW SCANS", "+ ADD SCANS"), ("+ INGEST MORE SCANS", "+ ADD SCANS"),
             (">ADD TO RECEIVABLES<", ">+ RECEIVABLES<"), ("> ADD TO RECEIVABLES <", "> + RECEIVABLES <")]:
    if a in src: src = src.replace(a, b); changed = True

# ---- 4) AMOUNT OWED red state (both branches) ----
old_owed = '<div className={styles.statBox}><label>AMOUNT OWED</label>'
new_owed = '<div className={`${styles.statBox} ${styles.statRed}`}><label>AMOUNT OWED</label>'
if old_owed in src: src = src.replace(old_owed, new_owed); changed = True

# ---- 5) Owners: per-owner other projects ----
OA = "                                    <div className={styles.infoRow}><FiMapPin aria-hidden=\"true\" /><span>{p.homeAddress || '---'}</span></div>\n                                </div>\n                            </div>))}"
if OA in src and "ownerPortfolio" not in src:
    add = OA.replace("                            </div>))}",
"""                                {(portfolio.filter(r => r.sharedOwner === p.fullName).length > 0) && (
                                    <div className={styles.ownerPortfolio}>
                                        <h3 className={styles.sectionTitle}>OTHER PROJECTS</h3>
                                        <table className={styles.portfolioTable}><tbody>
                                            {portfolio.filter(r => r.sharedOwner === p.fullName).map((r, k) => (
                                                <tr key={k} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                                    onKeyDown={ev => { if (ev.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                                    <td>#{r.index}</td><td>{r.plot || '—'}</td>
                                                    <td>{r.receivable ? 'RECEIVABLE' : r.titled ? 'TITLED' : 'BACKLOG'}</td>
                                                </tr>))}
                                        </tbody></table>
                                    </div>)}
                                </div>
                            </div>))}""")
    src = src.replace(OA, add, 1); changed = True
    print("JSX: per-owner other-projects added.")

# ---- 6) Extra badges (paused / negotiation) ----
LA = "{project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}"
if LA in src and "badgePaused" not in src:
    src = src.replace(LA, LA + "\n                        {project.storagePaused && <span className={`${styles.textBadge} ${styles.badgePaused}`}>STORAGE PAUSED</span>}\n                        {project.negotiationDeadline && <span className={`${styles.textBadge} ${styles.badgePaused}`}>NEGOTIATION</span>}", 1)
    changed = True

# ---- 7) ConfirmModal: single animated X ----
CB = '<div className={styles.confirmBox}>'
if CB in src and "confirmClose" not in src:
    src = src.replace(CB, CB + '\n        <button type="button" className={styles.confirmClose} onClick={() => onAnswer(false)} aria-label="Close"><FiX aria-hidden="true" /></button>', 1)
    changed = True
    print("JSX: animated X on confirm popups.")

if changed: open(jsx, "w", encoding="utf-8").write(src); print("JSX written.")

# ---- 8) CSS v7 ----
c = open(fcss, "r", encoding="utf-8").read()
if "FS-UNIFY v7" not in c:
    c += '''
/* FS-UNIFY v7 — tokens fix, curved bottoms, badge chips, red owed, X anim */
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
    open(fcss, "w", encoding="utf-8").write(c); print("CSS v7 appended.")

# ---- 9) Backend: restart billing clock on every entry ----
ct = open(ctrl, "r", encoding="utf-8").read()
old_e = "        p.setReceivable(true);\n        if (p.getReceivableStartDate() == null) p.setReceivableStartDate(LocalDateTime.now());"
new_e = "        p.setReceivable(true);\n        p.setReceivableStartDate(LocalDateTime.now());\n        p.setReceivableMonthsBilled(0);"
if old_e in ct:
    open(ctrl, "w", encoding="utf-8").write(ct.replace(old_e, new_e, 1))
    print("BACKEND: enter() now restarts fee clock + resets counter (accrued fees kept).")
else:
    print("WARN: enter() pattern not found — check controller manually.")

# ---- gate + push ----
fe_root = os.path.dirname(FE); esb = os.path.join(fe_root, "node_modules", ".bin", "esbuild")
if os.path.exists(esb):
    chk = subprocess.run([esb, jsx, "--loader:.jsx=jsx", "--outfile=" + os.path.join(ROOT, ".jsx_check.js")], capture_output=True, text=True)
    if chk.returncode != 0:
        print("ABORT: JSX broken — nothing pushed."); print(chk.stderr[:1500]); sys.exit(1)
    print("VERIFY: esbuild OK.")
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix54: receivable billing fix, notes structure repair, stages hide on title, badge chips, X anim, wording"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")