# fix.py -- fix59: one-word badges, RELEASE/PROBLEM buttons, related projects,
# rounded bottoms, green/red money contrast, popup CANCEL cleanup.
import os, re, sys, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s): write_safe(p, s)
def write_safe(p, s):
    p.write_text(s, encoding="utf-8", newline="\n"); print("WROTE", p.name)
def patch(path, old, new, label):
    s = read(path)
    if old in s:
        write_safe(path, s.replace(old, new, 1)); print("OK  ", label)
    else:
        print("MISS", label)

fp   = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
cssp = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"
led  = FE / "pages" / "Ledger" / "LedgerPage.jsx"
ledcss = FE / "pages" / "Ledger" / "LedgerPage.module.css"
svc  = FE / "services" / "folderPortalService.js"
lp   = BE / "modules" / "land" / "model" / "LandProject.java"
fpc  = BE / "modules" / "land" / "controller" / "FolderPortalController.java"

# ================= BACKEND =================
patch(lp,
'    @Builder.Default\n    @Column(name = "is_legacy", nullable = false)\n    private boolean isLegacy = false;',
'    @Builder.Default\n    @Column(name = "is_legacy", nullable = false)\n    private boolean isLegacy = false;\n\n    @Builder.Default\n    @Column(name = "is_problem", nullable = false)\n    private boolean problem = false;',
"LandProject.problem field")

patch(fpc, 'm.put("backlog", p.getLandTitle() == null);',
'm.put("backlog", p.getLandTitle() == null);\n        m.put("problem", p.isProblem());',
"receivable map problem")

patch(fpc, '    @PostMapping("/{id}/receivable/settings")',
'''    @PostMapping("/{id}/toggle-problem")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> toggleProblem(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setProblem(!p.isProblem());
        projectRepository.save(p);
        auditService.logAction("PROBLEM_FLAG", "Operator [" + op() + "] " + (p.isProblem() ? "flagged" : "cleared") + " PROBLEM on #" + p.getProjectIndex() + ".");
        return receivable(id);
    }

    @PostMapping("/{id}/receivable/settings")''',
"toggle-problem endpoint")

patch(svc, "settings: (id, payload) => api.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),",
"settings: (id, payload) => api.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),\n  toggleProblem: (id) => api.post(`/land/portal/${id}/toggle-problem`).then(r => r.data),",
"service toggleProblem")

# ================= FOLDER =================
patch(fp, "const arrearsEdit = (Number(buffer?.totalCost) || 0) - (Number(buffer?.initialPayment) || 0);",
"""const arrearsEdit = (Number(buffer?.totalCost) || 0) - (Number(buffer?.initialPayment) || 0);
    const lastPay = project?.lastPaymentDate ? new Date(project.lastPaymentDate) : null;
    const daysSincePay = lastPay ? Math.floor((Date.now() - lastPay.getTime()) / 86400000) : null;
    const statusBadge = isReceivable ? ['RECEIVABLE', 'badgeRecv']
        : project.landTitle?.isReleased ? ['RELEASED', 'badgeReleased']
        : (totalValue > 0 && amountPaid >= totalValue) ? ['PAID', 'badgePaid']
        : !project.landTitle ? ['PROCESSING', 'badgeProcessing']
        : (daysSincePay === null || daysSincePay > 30) ? ['CRITICAL', 'badgeCritical']
        : ['ACTIVE', 'badgeActive'];""",
"statusBadge consts")

patch(fp,
"""{isBacklog ? <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>
                            : <span className={`${styles.textBadge} ${styles.badgeTitled}`}>TITLED</span>}
                        {isReceivable ? <span className={`${styles.textBadge} ${styles.badgeRecv}`}>IN RECEIVABLES</span>
                            : amountPaid >= totalValue ? <span className={`${styles.textBadge} ${styles.badgeTitled}`}>FULLY PAID</span>
                            : <span className={`${styles.textBadge} ${styles.badgeActive}`}>ACTIVE</span>}
                        {project.landTitle?.isReleased && <span className={`${styles.textBadge} ${styles.badgeTitled}`}>RELEASED</span>}
                        {project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}""",
"""<span className={`${styles.textBadge} ${styles[statusBadge[1]]}`}>{statusBadge[0]}</span>
                        {project.isLegacy && <span className={`${styles.textBadge} ${styles.badgeLegacy}`}>LEGACY</span>}
                        {project.problem && <span className={`${styles.textBadge} ${styles.badgeProblem}`}>PROBLEM</span>}""",
"metaLine one-word badges")

patch(fp, '{canEdit && <button className={styles.unlockMasterBtn} onClick={handleUnlock}><FiUnlock aria-hidden="true" /> EDIT</button>}',
"""{canMoney && project.landTitle && !project.landTitle.isReleased && <button className={styles.releaseBtn} onClick={handleRelease}><FiCheckCircle aria-hidden="true" /> RELEASE</button>}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}><FiAlertTriangle aria-hidden="true" /> PROBLEM</button>}
                        {canEdit && <button className={styles.unlockMasterBtn} onClick={handleUnlock}><FiUnlock aria-hidden="true" /> EDIT</button>}""",
"RELEASE+PROBLEM buttons")

patch(fp, "const handleUnlock = async () => {",
"""const handleRelease = async () => { const ok = await confirm('RELEASE TITLE', 'Mark this title as released to the client? This records the handover.', 'warn'); if (!ok) return; try { await landService.authorizeRelease(id, 'Released from folder page'); await loadFolderData(); toast('Title released.', 'success'); } catch (err) { toast(err.response?.data?.message || 'RELEASE FAILED', 'error', 8000); } };
    const handleToggleProblem = async () => { const was = project.problem; try { await folderPortalService.toggleProblem(id); await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };
    const handleUnlock = async () => {""",
"release/problem handlers")

# popup CANCEL cleanup (X is the closer)
patch(fp, '<button type="button" className={modalStyles.modalBtnSecondary} onClick={() => { setPayModal({ open: false }); setPayType(\'TITLE\'); setPayAmount(\'\'); setPayNotes(\'\'); }}><FiX aria-hidden="true" /> CANCEL</button>\n', "", "payment CANCEL removed")
patch(fp, '<button type="button" className={modalStyles.modalBtnSecondary} onClick={() => setAddModalOpen(false)}><FiX aria-hidden="true" /> CANCEL</button>\n', "", "add-stage CANCEL removed")
patch(fp, '<button type="button" className={styles.confirmCancelBtn} onClick={() => onAnswer(false)} autoFocus><FiX aria-hidden="true" /> CANCEL</button>\n', "", "confirm CANCEL removed")

# RELATED PROJECTS under Owners
patch(fp,
"""</div>))}
                        </div>
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Documents\"""",
"""</div>))}
                        </div>
                        <h3 className={styles.sectionTitle}>RELATED PROJECTS</h3>
                        {portfolio.length === 0 ? (<div className={styles.emptyState}><FiUsers className={styles.emptyIcon} aria-hidden="true" /><span>NO RELATED PROJECTS FOR THESE OWNERS</span></div>) : (
                            <table className={styles.portfolioTable}>
                                <thead><tr><th>#</th><th>PLOT</th><th>OWNER</th><th>STATUS</th></tr></thead>
                                <tbody>{portfolio.map((r, i) => (<tr key={i} onClick={() => navigate('/land/projects/' + r.projectId)} tabIndex={0}
                                    onKeyDown={e => { if (e.key === 'Enter') navigate('/land/projects/' + r.projectId); }}>
                                    <td>#{r.index}</td><td>{r.plot || '—'}</td><td>{r.sharedOwner}</td>
                                    <td>{r.receivable ? 'RECEIVABLE' : r.titled ? 'TITLED' : 'PROCESSING'}</td>
                                </tr>))}</tbody>
                            </table>)}
                    </div></div>
                </section>
                <section className={styles.hwPanel} aria-label="Documents\"""",
"RELATED PROJECTS section")

# ================= LEDGER =================
patch(led,
"""{isReceivable && <span className={styles.tagReceivable}>RECEIVABLES</span>}
                            {!isReceivable && proj.landTitle?.isReleased && <span className={styles.tagPaid}>RELEASED</span>}
                            {!isReceivable && !proj.landTitle?.isReleased && (proj.amountPaid || 0) >= (proj.totalCost || 0) && <span className={styles.tagPaid}>FULLY PAID</span>}
                            {!isReceivable && (proj.amountPaid || 0) < (proj.totalCost || 0) && <span className={styles.tagStandard}>ACTIVE</span>}
                            {isCritical && <span className={styles.tagCritical}>CRITICAL</span>}""",
"""{isReceivable ? <span className={styles.tagReceivable}>RECEIVABLE</span>
                            : proj.landTitle?.isReleased ? <span className={styles.tagPaid}>RELEASED</span>
                            : (proj.totalCost || 0) > 0 && (proj.amountPaid || 0) >= (proj.totalCost || 0) ? <span className={styles.tagPaid}>PAID</span>
                            : !proj.landTitle ? <span className={styles.tagProcessing}>PROCESSING</span>
                            : isCritical ? <span className={styles.tagCritical}>CRITICAL</span>
                            : <span className={styles.tagActive}>ACTIVE</span>}""",
"ledger one-word status")

patch(led, "{ key: 'BACKLOG', label: 'BACKLOG' },", "{ key: 'BACKLOG', label: 'PROCESSING' },", "ledger filter label")

# ================= CSS =================
s = read(cssp)
if "FS-UNIFY v9" not in s:
    s += """
/* FS-UNIFY v9 -- one-word badges, rounded bottoms, money contrast */
.hwPanel{border-radius:10px !important;}
.panelBody{border-radius:0 0 10px 10px;}
.badgeProcessing{color:#EE8C3A;background:rgba(238,140,58,0.12);border-color:rgba(238,140,58,0.4);}
.badgeActive{color:#10b981;background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.4);}
.badgeCritical{color:#ef4444;background:rgba(239,68,68,0.12);border-color:rgba(239,68,68,0.4);}
.badgePaid{color:#10b981;background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.4);}
.badgeReleased{color:#06b6d4;background:rgba(6,182,212,0.12);border-color:rgba(6,182,212,0.4);}
.badgeProblem{color:#ef4444;background:rgba(239,68,68,0.12);border-color:rgba(239,68,68,0.4);}
.statGreen strong{color:#10b981 !important;}
.statRed strong{color:#ef4444 !important;}
.releaseBtn{display:inline-flex;align-items:center;gap:5px;height:clamp(32px,4vw,38px);padding:0 clamp(10px,1.3vw,15px);background:rgba(6,182,212,0.12);border:1.5px solid rgba(6,182,212,0.45);color:#06b6d4;border-radius:6px;font-family:'Inter',sans-serif;font-weight:900;font-size:var(--fs-btn);letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;}
.releaseBtn:hover{background:#06b6d4;color:#1a2e30;}
.problemBtn{display:inline-flex;align-items:center;gap:5px;height:clamp(32px,4vw,38px);padding:0 clamp(10px,1.3vw,15px);background:rgba(239,68,68,0.08);border:1.5px solid rgba(239,68,68,0.35);color:#fca5a5;border-radius:6px;font-family:'Inter',sans-serif;font-weight:900;font-size:var(--fs-btn);letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;}
.problemBtnActive{background:#ef4444;color:#fff;border-color:#ef4444;}
"""
    write_safe(cssp, s); print("OK   folder css v9")

s = read(ledcss)
if "tagProcessing" not in s:
    s += "\n.tagProcessing{color:#EE8C3A;}\n.tagActive{color:#34d399;}\n"
    write_safe(ledcss, s); print("OK   ledger css tags")

# ================= GIT =================
try:
    subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","fix59: one-word badges, RELEASE/PROBLEM, related projects, contrast fixes"],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")