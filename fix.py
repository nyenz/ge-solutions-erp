# fix.py — fix55a: repair broken JSX in FolderPage (owners section structure)
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
jsx = None
for r, d, fs in os.walk(os.path.join(ROOT, "erp-frontend", "src")):
    if "FolderPage.jsx" in fs: jsx = os.path.join(r, "FolderPage.jsx"); break
if not jsx:
    print("ABORT: FolderPage.jsx not found."); sys.exit(1)
shutil.copy2(jsx, os.path.join(ROOT, ".fix_backup", "FolderPage.jsx.bak55"))

src = open(jsx, "r", encoding="utf-8").read()

# The ownerPortfolio insertion likely left unclosed tags or broken nesting.
# Safest repair: find the Owners section and rebuild the map cleanly.

# Find the owners map start
OWNERS_MAP_START = "project.proprietors.map((p, i) =>"
OWNERS_SECTION_END = "</section>"

si = src.find(OWNERS_MAP_START)
if si == -1:
    print("ABORT: cannot locate owners map."); sys.exit(1)

# Find the matching closing </section> for the Owners section
section_start = src.rfind("<section", 0, si)
section_end = src.find("</section>", si)
if section_start == -1 or section_end == -1:
    print("ABORT: cannot find section boundaries."); sys.exit(1)

# Extract everything before the owners map, and everything after the section
before = src[:si]
after = src[section_end:]

# Rebuild the owners map cleanly
new_owners_map = """project.proprietors.map((p, i) => (<div key={i} className={styles.ownerStaticCard}>
                                <h2 className={styles.ownerName}>{p.fullName}</h2>
                                <div className={styles.infoColumns}>
                                    <div className={styles.infoRow}><FiPhoneCall aria-hidden="true" /><span className={styles.phoneHighlight}>{p.phoneNumber||'---'}</span></div>
                                    <div className={styles.infoRow}><FiMail aria-hidden="true" /><span>{p.email||'---'}</span></div>
                                    <div className={styles.infoRow}><FiShield aria-hidden="true" /><span>{p.nationalId||'---'}</span></div>
                                    <div className={styles.infoRow}><FiMapPin aria-hidden="true" /><span>{p.homeAddress||'---'}</span></div>
                                </div>
                                {(portfolio.filter(r => r.sharedOwner === p.fullName).length > 0) && (
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
                            </div>))}
                        </div>
                    </div>
                </section>"""

src = before + new_owners_map + after[len("</section>"):]
open(jsx, "w", encoding="utf-8").write(src)
print("JSX: owners section rebuilt cleanly.")

# esbuild gate
fe_root = os.path.dirname(os.path.dirname(jsx))
esb = os.path.join(fe_root, "node_modules", ".bin", "esbuild")
if os.path.exists(esb):
    chk = subprocess.run([esb, jsx, "--loader:.jsx=jsx", "--outfile=" + os.path.join(ROOT, ".jsx_check.js")], capture_output=True, text=True)
    if chk.returncode != 0:
        print("ABORT: JSX still broken."); print(chk.stderr[:1500]); sys.exit(1)
    print("VERIFY: esbuild OK.")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix55a: repair broken owners section JSX"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")