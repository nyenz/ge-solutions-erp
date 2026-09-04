# fix.py -- fix67: financials restructure, grouped related projects, release/problem naming+note, note color
import re, subprocess, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
fp = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
cssp = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)
results = []

s = read(fp)

# ---- 1) AMOUNT OWED color: green when 0, red when >0 (both branches) ----
old_owed = '<div className={`${styles.statBox} ${styles.statRed}`}><label>AMOUNT OWED</label>'
new_owed = '<div className={`${styles.statBox} ${amountOwed > 0 ? styles.statRed : styles.statGreen}`}><label>AMOUNT OWED</label>'
if old_owed in s:
    s = s.replace(old_owed, new_owed); results.append("OK amountOwed color logic")

# ---- 2) Move storage/settings INTO balance summary, gated on isReceivable ----
# Wrap the existing canMoney settings grid so it only shows when receivable.
old_set = "{canMoney && (<div className={styles.inputGrid3}>"
new_set = "{isReceivable && canMoney && (<div className={styles.storageBlock}><h3 className={styles.sectionTitle}>STORAGE & FEES</h3><div className={styles.inputGrid3}>"
if old_set in s:
    s = s.replace(old_set, new_set, 1)
    # close the extra wrapper div after the settings inputGrid3 closes
    s = s.replace(new_set + "\n                                <CurrencyInput label=\"MONTHLY STORAGE RATE\"", new_set + "\n                                <CurrencyInput label=\"MONTHLY STORAGE RATE\"", 1)
    results.append("OK storage block gated (open)")
# find the closing of that inputGrid3 (the </div> right before recvActionRow) and add one more </div>
s = s.replace("</div>)}\n                            <div className={styles.recvActionRow}>", "</div></div>)}\n                            <div className={styles.recvActionRow}>", 1)

# ---- 3) Related projects grouped by owner ----
old_rel = """<h3 className={styles.sectionTitle}>RELATED PROJECTS</h3>
                        {portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
                            <table className={styles.portfolioTable}>
                                <thead><tr><th>#</th><th>PLOT</th><th>OWNER</th><th>STATUS</th></tr></thead>
                                <tbody>{portfolio.map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                    onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                    <td>#{r.index}</td><td>{r.plot || '—'}</td><td>{r.sharedOwner}</td>
                                    <td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
                                </tr>))}</tbody>
                            </table>)}"""
new_rel = """<h3 className={styles.sectionTitle}>RELATED PROJECTS</h3>
                        {portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
                            [...new Set(portfolio.map(r => r.sharedOwner))].map(owner => (
                                <div key={owner} className={styles.ownerRelGroup}>
                                    <h4 className={styles.ownerRelName}>{owner}</h4>
                                    <table className={styles.portfolioTable}>
                                        <thead><tr><th>#</th><th>PLOT</th><th>STATUS</th></tr></thead>
                                        <tbody>{portfolio.filter(r => r.sharedOwner === owner).map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                            onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                            <td>#{r.index}</td><td>{r.plot || '—'}</td>
                                            <td>{r.receivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>RECEIVABLE</span> : r.titled ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span> : <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>}</td>
                                        </tr>))}</tbody>
                                    </table>
                                </div>)))}"""
if old_rel in s:
    s = s.replace(old_rel, new_rel, 1); results.append("OK related projects grouped by owner")

# ---- 4) RELEASE + PROBLEM button naming/state ----
old_btns = """{canMoney && project.landTitle && !project.landTitle.isReleased && <button className={styles.releaseBtn} onClick={handleRelease}><FiCheckCircle aria-hidden="true" /> RELEASE</button>}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}><FiAlertTriangle aria-hidden="true" /> PROBLEM</button>}"""
new_btns = """{canMoney && project.landTitle && (project.landTitle.isReleased
                            ? <button className={`${styles.releaseBtn} ${styles.releaseBtnDone}`} disabled><FiCheckCircle aria-hidden="true" /> RELEASED</button>
                            : <button className={styles.releaseBtn} onClick={handleRelease}><FiCheckCircle aria-hidden="true" /> RELEASE</button>)}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}><FiAlertTriangle aria-hidden="true" /> {project.problem ? 'PROBLEM ✓' : 'PROBLEM'}</button>}"""
if old_btns in s:
    s = s.replace(old_btns, new_btns, 1); results.append("OK release/problem naming+state")

# ---- 5) PROBLEM toggle takes a note ----
old_toggle = "const handleToggleProblem = async () => { const was = project.problem; try { await folderPortalService.toggleProblem(id); await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };"
new_toggle = "const handleToggleProblem = async () => { const was = project.problem; let note = ''; if (!was) { note = window.prompt('Describe the problem (optional):') || ''; } try { await folderPortalService.toggleProblem(id, note); if (!was && note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };"
if old_toggle in s:
    s = s.replace(old_toggle, new_toggle, 1); results.append("OK problem takes note")

write(fp, s)

# ---- service: toggleProblem accepts note param ----
svc = FE / "services" / "folderPortalService.js"
sv = read(svc)
old_svc = "toggleProblem: (id) => api.post(`/land/portal/${id}/toggle-problem`).then(r => r.data),"
new_svc = "toggleProblem: (id, note) => api.post(`/land/portal/${id}/toggle-problem`, null, { params: note ? { note } : {} }).then(r => r.data),"
if old_svc in sv:
    write(svc, sv.replace(old_svc, new_svc, 1)); results.append("OK service note param")

# ---- CSS: note textarea light + grouped related + released done ----
c = read(cssp)
if "FS-UNIFY v11" not in c:
    c += """
/* FS-UNIFY v11 -- note contrast, grouped related projects, released state */
.modalTextarea,.modalInput{background:#ffffff !important;color:#1a2e30 !important;border:1.5px solid rgba(238,140,58,0.3) !important;}
.modalTextarea::placeholder,.modalInput::placeholder{color:#9aa8a6 !important;}
.ownerRelGroup{margin-bottom:clamp(10px,1.3vw,14px);}
.ownerRelName{font-family:'Cinzel',serif;color:#fff;font-size:clamp(11px,1.2vw,14px);letter-spacing:1px;margin:0 0 6px;border-bottom:1px solid rgba(255,255,255,0.12);padding-bottom:4px;}
.releaseBtnDone{background:#10b981;border-color:#10b981;color:#fff;opacity:0.9;cursor:default;}
.storageBlock{margin-bottom:clamp(8px,1vw,12px);padding:clamp(8px,1vw,12px);background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.25);border-radius:8px;}
"""
    write(cssp, c); results.append("OK css v11")

for r in results: print(r)

try:
    subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","fix67: financials restructure, grouped related, release/problem naming+note, note contrast"],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")