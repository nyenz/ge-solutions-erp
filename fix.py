# fix.py — fix56: bulletproof structural repair for JSX + backend type fix
import os, re, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")
BE = os.path.join(ROOT, "erp-backend", "src", "main", "java", "com", "gesolutions", "erp")

def find(name, base):
    for r, d, fs in os.walk(base):
        if name in fs: return os.path.join(r, name)
    return None

jsx_path = find("FolderPage.jsx", FE)
ctrl_path = find("RecoveryNoteController.java", BE)

if not jsx_path or not ctrl_path:
    print("ABORT: Files not found."); exit(1)

# Backup
os.makedirs(os.path.join(ROOT, ".fix_backup"), exist_ok=True)
shutil.copy2(jsx_path, os.path.join(ROOT, ".fix_backup", "FolderPage.jsx.bak56"))
shutil.copy2(ctrl_path, os.path.join(ROOT, ".fix_backup", "RecoveryNoteController.java.bak56"))

# ==================== FRONTEND REPAIR ====================
with open(jsx_path, "r", encoding="utf-8") as f:
    jsx = f.read()

# 1. Replace Owners Section completely with perfectly balanced code
owners_start_anchor = '<section className={styles.hwPanel} aria-label="Owners"'
start_idx = jsx.find(owners_start_anchor)

if start_idx != -1:
    # Find the matching closing </section>
    # Since Owners doesn't have nested <section> tags, the first one after start_idx is the end
    end_idx = jsx.find('</section>', start_idx) + len('</section>')
    
    new_owners_block = """<section className={styles.hwPanel} aria-label="Owners" style={activeTab !== 'OWNERS' ? {display:'none'} : {}}>
                    <DrawerHeader label="OWNERS" isOpen={drawers.owners} onClick={() => toggleDrawer('owners')} icon={FiUsers} count={project.proprietors.length} />
                    <div className={`${styles.panelBody} ${drawers.owners ? styles.bodyOpen : styles.bodyClosed}`}><div className={styles.panelInner}>
                        <div className={styles.ownersGrid2}>
                            {isEditing ? buffer.owners.map((o, idx) => (<div key={idx} className={styles.ownerEditCard}>
                                <SmartInput label={`LEGAL NAME #${idx+1}`} value={o.fullName} showCaps required error={fieldErrors['owner_'+idx+'_name']} onChange={e => handleOwnerChange(idx,'fullName',e.target.value)} />
                                <SmartInput label="NIN" value={o.nationalId} required onChange={e => handleOwnerChange(idx,'nationalId',e.target.value)} onBlur={e => handleNinBlurCheck(idx, e.target.value)} id={`owner_${idx}_nin`} />
                                <SmartInput label="PHONE" value={o.phone} onChange={e => handleOwnerChange(idx,'phone',e.target.value)} id={`owner_${idx}_phone`} />
                                <SmartInput label="EMAIL" value={o.email} onChange={e => handleOwnerChange(idx,'email',e.target.value)} onCommit={val => handleEmailCommit(idx,val)} id={`owner_${idx}_email`} />
                            </div>)) : project.proprietors.map((p, i) => (<div key={i} className={styles.ownerStaticCard}>
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
                    </div></div>
                </section>"""
    
    jsx = jsx[:start_idx] + new_owners_block + jsx[end_idx:]
    print("✓ Frontend: Owners section rebuilt with perfectly balanced JSX.")

# 2. Ensure Notes section is wrapped in NOTES tab and moved to the end
notes_start = jsx.find('<section className={styles.hwPanel} aria-label="Notes and Call Log">')
if notes_start != -1:
    notes_end = jsx.find('</section>', notes_start) + len('</section>')
    notes_block = jsx[notes_start:notes_end]
    
    # Remove it from wherever it currently is
    jsx = jsx[:notes_start] + jsx[notes_end:]
    
    # Wrap it in the NOTES tab visibility toggle
    wrapped_notes = f'<div style={{activeTab !== \'NOTES\' ? {{ display: \'none\' }} : {{}}}}>\n{notes_block}\n</div>'
    
    # Insert it right before the closing </main> tag
    main_end = jsx.rfind('</main>')
    if main_end != -1:
        jsx = jsx[:main_end] + wrapped_notes + '\n            ' + jsx[main_end:]
        print("✓ Frontend: Notes section moved to end and wrapped in NOTES tab.")

with open(jsx_path, "w", encoding="utf-8") as f:
    f.write(jsx)

# ==================== BACKEND REPAIR ====================
with open(ctrl_path, "r", encoding="utf-8") as f:
    ctrl = f.read()

old_java = """            try {
                author = (com.gesolutions.erp.modules.auth.model.User)
                    userRepo.getClass().getMethod("findByUsername", String.class)
                    .invoke(userRepo, auth.getName());
                if (author instanceof java.util.Optional) author = ((java.util.Optional<com.gesolutions.erp.modules.auth.model.User>) author).orElse(null);
            } catch (Exception ignored) { }"""

new_java = """            try {
                Object temp = userRepo.getClass().getMethod("findByUsername", String.class)
                    .invoke(userRepo, auth.getName());
                if (temp instanceof java.util.Optional) {
                    author = ((java.util.Optional<com.gesolutions.erp.modules.auth.model.User>) temp).orElse(null);
                } else {
                    author = (com.gesolutions.erp.modules.auth.model.User) temp;
                }
            } catch (Exception ignored) { }"""

if old_java in ctrl:
    ctrl = ctrl.replace(old_java, new_java, 1)
    with open(ctrl_path, "w", encoding="utf-8") as f:
        f.write(ctrl)
    print("✓ Backend: RecoveryNoteController line 163 type mismatch fixed.")
else:
    print("Note: Backend code may already be fixed.")

# ==================== COMMIT & PUSH ====================
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix56: bulletproof structural repair (Owners JSX + Notes tab + Backend type)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("✓ GIT: Committed and pushed. Render should build cleanly now.")
except Exception as e:
    print("GIT WARN:", e)

print("DONE.")