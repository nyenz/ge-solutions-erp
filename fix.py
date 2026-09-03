# fix.py — fix58: X-replaces-CANCEL rule, styled loader, related projects, badge colors, inactivity autosave
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
def find(name, base=FE):
    for r, d, fs in os.walk(base):
        if name in fs: return os.path.join(r, name)
    return None
jsx = find("FolderPage.jsx"); guide = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
if not jsx: print("ABORT: FolderPage.jsx missing."); sys.exit(1)
shutil.copy2(jsx, os.path.join(ROOT, ".fix_backup", "FolderPage.jsx.bak58"))

# ---------- 1) APP-WIDE: remove redundant CANCEL buttons (X remains as closer) ----------
removed = 0
for r, d, fs in os.walk(FE):
    for f in fs:
        if f.endswith(".jsx"):
            p = os.path.join(r, f); s = open(p, encoding="utf-8").read()
            s2 = re.sub(r"[ \t]*<button[^>]*modalBtnSecondary[^>]*>[^<]*<[^>]*>[^<]*CANCEL</button>\n", "", s)
            s2 = re.sub(r"[ \t]*<button[^>]*modalBtnSecondary[^>]*>.*?CANCEL</button>\n", "", s2)
            if s2 != s:
                open(p, "w", encoding="utf-8").write(s2); removed += 1
                print("CANCEL removed in:", os.path.relpath(p, ROOT))
print("Files patched for CANCEL rule:", removed)

src = open(jsx, encoding="utf-8").read(); changed = False

# ConfirmModal CANCEL (own class) -> X stays
cc = '<button type="button" className={styles.confirmCancelBtn} onClick={() => onAnswer(false)} autoFocus><FiX aria-hidden="true" /> CANCEL</button>'
if cc in src: src = src.replace(cc, "", 1); changed = True

# ---------- 2) Styled loading skeleton ----------
old_load = "if (loading) return <div className={styles.container}><p style={{ padding: 40, color: 'rgba(255,255,255,0.4)' }}>Loading record…</p></div>;"
new_load = ("if (loading) return (<div className={styles.container}><div className={styles.skeletonPage}>"
    "<div className={styles.skeletonTermHeader} /><div className={styles.skeletonHUD} />"
    "<div className={styles.skeletonPanel}><div className={styles.skeletonHeader} /><div className={styles.skeletonBody}><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /></div></div>"
    "<div className={styles.skeletonPanel}><div className={styles.skeletonHeader} /><div className={styles.skeletonBody}><div className={styles.skeletonLine} /><div className={styles.skeletonLine} /></div></div>"
    "</div></div>);")
if old_load in src: src = src.replace(old_load, new_load, 1); changed = True; print("Loader: skeleton applied.")

# ---------- 3) RELATED PROJECTS section under Owners ----------
OWN_END = "                        </div>\n                    </div></div>\n                </section>\n                <section className={styles.hwPanel} aria-label=\"Documents\""
if "RELATED PROJECTS" not in src and OWN_END in src:
    rel_sec = """                        </div>
                        <h3 className={styles.sectionTitle}>RELATED PROJECTS</h3>
                        {portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
                            <table className={styles.portfolioTable}>
                                <thead><tr><th>#</th><th>PLOT</th><th>OWNER</th><th>STATUS</th></tr></thead>
                                <tbody>{portfolio.map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                    onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                    <td>#{r.index}</td><td>{r.plot || '—'}</td><td>{r.sharedOwner}</td>
                                    <td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
                                </tr>))}</tbody>
                            </table>)}
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Documents\""""
    src = src.replace(OWN_END, rel_sec, 1); changed = True; print("Owners: RELATED PROJECTS section added.")

# ---------- 4) Inactivity auto-save (5 min) ----------
if "lastActiveRef" not in src:
    anchor = "const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(!committing && isEditing);"
    add = anchor + """
    const lastActiveRef = useRef(Date.now());
    useEffect(() => {
        const mark = () => { lastActiveRef.current = Date.now(); };
        window.addEventListener('click', mark); window.addEventListener('keydown', mark);
        return () => { window.removeEventListener('click', mark); window.removeEventListener('keydown', mark); };
    }, []);"""
    src = src.replace(anchor, add, 1)
    anchor2 = "const handleCommit = async () => {"
    # interval effect after handleCommit definition end is complex; place before return of component via useEffect near others
    anchor3 = "    useEffect(() => {\n        if (!isEditing || committing) return;\n        const handler = (e) => { e.preventDefault(); e.returnValue = ''; return ''; };"
    add3 = """    useEffect(() => {
        const t = setInterval(() => {
            if (!isEditing || committing) return;
            if (Date.now() - lastActiveRef.current > 5 * 60 * 1000) {
                lastActiveRef.current = Date.now();
                handleCommit();
            }
        }, 15000);
        return () => clearInterval(t);
    });
""" + anchor3
    src = src.replace(anchor3, add3, 1); changed = True; print("Inactivity auto-save added (5 min).")

# ---------- 5) RELEASED badge differentiate ----------
if "badgeReleased" not in src:
    src = src.replace("{project.landTitle?.isReleased && <span className={`${styles.textBadge} ${styles.badgeTitled}`}>RELEASED</span>}",
                      "{project.landTitle?.isReleased && <span className={`${styles.textBadge} ${styles.badgeReleased}`}>RELEASED</span>}", 1)
    changed = True

if changed: open(jsx, "w", encoding="utf-8").write(src); print("JSX written.")

# ---------- 6) CSS v8: attention colors ----------
fcss = find("FolderPage.module.css")
c = open(fcss, encoding="utf-8").read()
if "FS-UNIFY v8" not in c:
    c += """
/* FS-UNIFY v8 — attention-color semantics */
.badgeActive{color:#10b981;background:rgba(16,185,129,0.10);border-color:rgba(16,185,129,0.35);}
.badgeTitled{color:#10b981;background:rgba(16,185,129,0.10);border-color:rgba(16,185,129,0.35);}
.badgeReleased{color:#06b6d4;background:rgba(6,182,212,0.10);border-color:rgba(6,182,212,0.35);}
.badgeRecv{color:#ef4444;background:rgba(239,68,68,0.12);border-color:rgba(239,68,68,0.4);}
.badgeBacklog{color:#EE8C3A;background:rgba(238,140,58,0.10);border-color:rgba(238,140,58,0.35);}
.badgeLegacy{color:#64748b;background:rgba(100,116,139,0.12);border-color:rgba(100,116,139,0.35);}
.badgePaused{color:#f59e0b;background:rgba(245,158,11,0.12);border-color:rgba(245,158,11,0.4);}
"""
    open(fcss, "w", encoding="utf-8").write(c); print("CSS v8 appended.")

# ---------- 7) DESIGN RULES into guide ----------
if os.path.exists(guide):
    g = open(guide, encoding="utf-8").read()
    if "DESIGN RULES (fix58)" not in g:
        g += """
## DESIGN RULES (fix58)
1. X IS THE CLOSER: any popup/modal that shows the animated X must NOT also show a CANCEL button. X = dismiss.
2. LOADING STATES: every page renders the skeleton loader (skeletonPage/skeletonPanel), never plain text.
3. ATTENTION COLORS: green = healthy/active/paid, orange = pending/backlog, red = debt/danger, amber = paused/negotiation, cyan = released/info. Use consistently app-wide.
4. INACTIVITY: edit mode auto-saves and deactivates after 5 minutes of no interaction.
5. RELATED PROJECTS: Owners tab always lists every other project of each owner/joint owner, clickable to navigate.
"""
        open(guide, "w", encoding="utf-8").write(g); print("Guide: design rules appended.")

# ---------- 8) Report plain loaders elsewhere ----------
print("\n=== Pages still using plain loading text (patch next) ===")
for r, d, fs in os.walk(FE):
    for f in fs:
        if f.endswith(".jsx"):
            s = open(os.path.join(r, f), encoding="utf-8").read()
            if re.search(r">Loading|Loading\.\.\.|Loading…", s):
                print(" -", os.path.relpath(os.path.join(r, f), ROOT))

# ---------- gate + push ----------
fe_root = os.path.dirname(FE); esb = os.path.join(fe_root, "node_modules", ".bin", "esbuild")
if os.path.exists(esb):
    chk = subprocess.run([esb, jsx, "--loader:.jsx=jsx", "--outfile=" + os.path.join(ROOT, ".jsx_check.js")], capture_output=True, text=True)
    if chk.returncode != 0:
        print("ABORT: JSX broken — nothing pushed."); print(chk.stderr[:1500]); sys.exit(1)
    print("VERIFY: esbuild OK.")
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix58: X-closer rule, skeleton loader, related projects, attention colors, inactivity autosave"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE. Paste the 'plain loading text' report so I can skeleton-patch the remaining pages.")