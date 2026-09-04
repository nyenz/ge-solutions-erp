# fix.py -- fix61: collapse duplicate insertions left by double-run of fix59
import os, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def collapse(path, block, label):
    s = read(path)
    if block + block in s:
        path.write_text(s.replace(block + block, block, 1), encoding="utf-8", newline="\n")
        print("OK   collapsed:", label)
    else:
        print("skip (single or absent):", label)

P = """    @Builder.Default
    @Column(name = "is_problem", nullable = false)
    private boolean problem = false;
"""
M = """    @PostMapping("/{id}/toggle-problem")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> toggleProblem(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setProblem(!p.isProblem());
        projectRepository.save(p);
        auditService.logAction("PROBLEM_FLAG", "Operator [" + op() + "] " + (p.isProblem() ? "flagged" : "cleared") + " PROBLEM on #" + p.getProjectIndex() + ".");
        return receivable(id);
    }

"""
T = "  toggleProblem: (id) => api.post(`/land/portal/${id}/toggle-problem`).then(r => r.data),\n"
B = """    const lastPay = project?.lastPaymentDate ? new Date(project.lastPaymentDate) : null;
    const daysSincePay = lastPay ? Math.floor((Date.now() - lastPay.getTime()) / 86400000) : null;
    const statusBadge = isReceivable ? ['RECEIVABLE', 'badgeRecv']
        : project.landTitle?.isReleased ? ['RELEASED', 'badgeReleased']
        : (totalValue > 0 && amountPaid >= totalValue) ? ['PAID', 'badgePaid']
        : !project.landTitle ? ['PROCESSING', 'badgeProcessing']
        : (daysSincePay === null || daysSincePay > 30) ? ['CRITICAL', 'badgeCritical']
        : ['ACTIVE', 'badgeActive'];
"""
H = """    const handleRelease = async () => { const ok = await confirm('RELEASE TITLE', 'Mark this title as released to the client? This records the handover.', 'warn'); if (!ok) return; try { await landService.authorizeRelease(id, 'Released from folder page'); await loadFolderData(); toast('Title released.', 'success'); } catch (err) { toast(err.response?.data?.message || 'RELEASE FAILED', 'error', 8000); } };
    const handleToggleProblem = async () => { const was = project.problem; try { await folderPortalService.toggleProblem(id); await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };
"""
U = """                        {canMoney && project.landTitle && !project.landTitle.isReleased && <button className={styles.releaseBtn} onClick={handleRelease}><FiCheckCircle aria-hidden="true" /> RELEASE</button>}
                        {canEdit && <button className={`${styles.problemBtn} ${project.problem ? styles.problemBtnActive : ''}`} onClick={handleToggleProblem}><FiAlertTriangle aria-hidden="true" /> PROBLEM</button>}
"""

collapse(BE / "modules" / "land" / "model" / "LandProject.java", P, "LandProject.problem field")
collapse(BE / "modules" / "land" / "controller" / "FolderPortalController.java", M, "toggleProblem method")
collapse(FE / "services" / "folderPortalService.js", T, "service toggleProblem line")
fp = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
collapse(fp, B, "statusBadge consts")
collapse(fp, H, "release/problem handlers")
collapse(fp, U, "RELEASE/PROBLEM buttons")

# build gate
esb = ROOT / "erp-frontend" / "node_modules" / ".bin" / "esbuild"
if esb.exists():
    chk = subprocess.run([str(esb), str(fp), "--loader:.jsx=jsx", "--outfile=" + str(ROOT / ".jsx_check.js")], capture_output=True, text=True)
    print("esbuild:", "OK" if chk.returncode == 0 else chk.stderr[:1200])
    if chk.returncode != 0:
        print("ABORT push - JSX broken"); raise SystemExit(1)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix61: collapse duplicate insertions from double-run fix59"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE - after push, the test-file red squiggles should clear once the IDE rebuilds (they were cascades of the two duplicates).")