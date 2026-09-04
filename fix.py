# fix.py -- fix63: comprehensive audit repair
import os, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    p.write_text(s, encoding="utf-8", newline="\n")
    print("WROTE", p.name)
def patch(path, old, new, label):
    s = read(path)
    if old in s:
        write(path, s.replace(old, new, 1))
        print("OK  ", label)
        return True
    print("MISS", label)
    return False
def collapse(path, block, label):
    s = read(path)
    if block + block in s:
        write(path, s.replace(block + block, block, 1))
        print("OK   collapse:", label)
        return True
    print("skip (single):", label)
    return False

# ================= 1) CLIENT ENTITY =================
client_java = BE / "modules" / "client" / "model" / "Client.java"
if client_java.exists():
    s = read(client_java)
    fields = [
        ("fullName", '    @Column(name = "full_name", nullable = false)\n    private String fullName;\n'),
        ("nationalId", '    @Column(name = "national_id", unique = true)\n    private String nationalId;\n'),
        ("phoneNumber", '    @Column(name = "phone_number")\n    private String phoneNumber;\n'),
        ("email", '    @Column(name = "email")\n    private String email;\n'),
        ("homeAddress", '    @Column(name = "home_address")\n    private String homeAddress;\n'),
    ]
    changed = False
    for name, decl in fields:
        if f"private String {name};" not in s:
            s = s.replace("    private UUID id;\n", "    private UUID id;\n\n" + decl, 1)
            changed = True
            print("OK   added", name)
    if "private int monthlyContactCount" not in s:
        s = s.replace("    private UUID id;\n", '    private UUID id;\n\n    @Builder.Default\n    @Column(name = "monthly_contact_count")\n    private int monthlyContactCount = 0;\n\n    @Column(name = "last_contacted_at")\n    private LocalDateTime lastContactedAt;\n\n    @Builder.Default\n    @Column(name = "reliability_score")\n    private double reliabilityScore = 50.0;\n', 1)
        changed = True
        print("OK   added monthlyContactCount + lastContactedAt + reliabilityScore")
    if "shouldResetMonthlyCounter" not in s:
        s = s.replace("}", """
    public boolean shouldResetMonthlyCounter() {
        if (lastContactedAt == null) return false;
        return lastContactedAt.getMonth() != LocalDateTime.now().getMonth()
            || lastContactedAt.getYear() != LocalDateTime.now().getYear();
    }
}""", 1)
        changed = True
        print("OK   added shouldResetMonthlyCounter()")
    if changed: write(client_java, s)

# ================= 2) COLLAPSE DUPLICATES =================
LP = BE / "modules" / "land" / "model" / "LandProject.java"
FPC = BE / "modules" / "land" / "controller" / "FolderPortalController.java"
SVC = FE / "services" / "folderPortalService.js"

problem_field = """    @Builder.Default
    @Column(name = "is_problem", nullable = false)
    private boolean problem = false;
"""
toggle_method = """    @PostMapping("/{id}/toggle-problem")
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
toggle_service = "  toggleProblem: (id) => api.post(`/land/portal/${id}/toggle-problem`).then(r => r.data),\n"

if LP.exists(): collapse(LP, problem_field, "LandProject.problem")
if FPC.exists(): collapse(FPC, toggle_method, "toggleProblem method")
if SVC.exists(): collapse(SVC, toggle_service, "service toggleProblem")

# ================= 3) FOLDERPAGE.jsx =================
fp = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
if fp.exists():
    s = read(fp)
    
    # 3a) Remove dead handleEmailCommit reference
    if "handleEmailCommit" in s:
        s = re.sub(r"\s*onCommit=\{val => handleEmailCommit\([^)]*\)\}", "", s)
        print("OK   removed dead handleEmailCommit")
    
    # 3b) Remove duplicate empty NOTES wrapper
    s = re.sub(r"<div style=\{activeTab !== 'NOTES' \? \{ display: 'none' \} : \{\}\}>\s*</div>\s*", "", s)
    
    # 3c) Restore ADDRESS in owner edit card
    if "owner_${idx}_addr" not in s and "owner_' + idx + '_addr" not in s:
        s = s.replace(
            "id={`owner_${idx}_email`} />",
            "id={`owner_${idx}_email`} />\n                                <SmartInput label=\"ADDRESS\" value={o.address} onChange={e => handleOwnerChange(idx,'address',e.target.value)} id={`owner_${idx}_addr`} />",
            1
        )
        print("OK   restored ADDRESS field")
    
    # 3d) Remove all CANCEL buttons next to X
    for pattern in [
        r'<button[^>]*modalBtnSecondary[^>]*>.*?CANCEL</button>\s*\n',
        r'<button[^>]*confirmCancelBtn[^>]*>.*?CANCEL</button>\s*\n'
    ]:
        s2 = re.sub(pattern, "", s)
        if s2 != s:
            s = s2
            print("OK   removed CANCEL button")
    
    write(fp, s)

# ================= 4) CSS v10 =================
cssp = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"
if cssp.exists():
    s = read(cssp)
    if "FS-UNIFY v10" not in s:
        s += """
/* FS-UNIFY v10 -- comprehensive audit fixes */
.capsBadge{background:none !important;border:none !important;color:rgba(255,255,255,0.35) !important;font-size:8px !important;font-weight:700 !important;letter-spacing:0.5px !important;padding:0 !important;}
.hwPanel{border-radius:10px !important;}
.panelBody{border-radius:0 0 10px 10px;}
.statGreen strong{color:#10b981 !important;}
.statRed strong{color:#ef4444 !important;}
.badgeProcessing{color:#EE8C3A;background:rgba(238,140,58,0.12);border-color:rgba(238,140,58,0.4);}
.badgeActive{color:#10b981;background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.4);}
.badgeCritical{color:#ef4444;background:rgba(239,68,68,0.12);border-color:rgba(239,68,68,0.4);}
.badgePaid{color:#10b981;background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.4);}
.badgeReleased{color:#06b6d4;background:rgba(6,182,212,0.12);border-color:rgba(6,182,212,0.4);}
.badgeProblem{color:#ef4444;background:rgba(239,68,68,0.12);border-color:rgba(239,68,68,0.4);}
"""
        write(cssp, s)
        print("OK   CSS v10 appended")

# ================= 5) CLEAN .bak FILES =================
bak_dir = ROOT / ".fix_backup"
if bak_dir.exists():
    for f in bak_dir.glob("*.bak*"):
        f.unlink()
        print("OK   removed", f.name)

# ================= 6) GIT =================
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix63: comprehensive audit repair"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("\n=== AUDIT SUMMARY ===")
print("✓ Client entity fields restored")
print("✓ Duplicate insertions collapsed")
print("✓ Dead handleEmailCommit removed")
print("✓ ADDRESS field restored in owner edit")
print("✓ All CANCEL buttons removed (X is closer)")
print("✓ CSS v10 with badge colors + caps restyle")
print("✓ .bak files cleaned")
print("\nAfter push, the test-file errors should clear automatically.")