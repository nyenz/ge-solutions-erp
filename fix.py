# fix.py -- fix_build_and_warnings: FolderPage.jsx JSX tag mismatch + Java warnings
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FE = ROOT / "erp-frontend" / "src"
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)

def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)

# 1. FolderPage.jsx: close the OWNERS tabWrap <div> before the NOTES tabWrap
folder_jsx = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
patch(folder_jsx,
"""                </section>

            <div className={styles.tabWrap} style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>""",
"""                </section>
                </div>

            <div className={styles.tabWrap} style={activeTab !== 'NOTES' ? { display: 'none' } : {}}>""",
"FolderPage OWNERS tabWrap closing tag")

# 2. ReceivableSchedulerService.java: remove unused imports
scheduler_java = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
patch(scheduler_java,
"""import java.time.LocalDate;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.model.Client;""",
"""import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.model.Client;""",
"ReceivableSchedulerService unused imports")

# 3. FolderPortalController.java: merge /{id} into class-level @RequestMapping
portal_java = BE / "modules" / "land" / "controller" / "FolderPortalController.java"
patch(portal_java,
"""@RequestMapping("/api/v1/land/portal")
@RequiredArgsConstructor""",
"""@RequestMapping("/api/v1/land/portal/{id}")
@RequiredArgsConstructor""",
"FolderPortalController class-level mapping")

patch(portal_java,
"""    @GetMapping("/{id}/receivable")""",
"""    @GetMapping("/receivable")""",
"FolderPortalController receivable mapping")

patch(portal_java,
"""    @GetMapping("/{id}/portfolio")""",
"""    @GetMapping("/portfolio")""",
"FolderPortalController portfolio mapping")

patch(portal_java,
"""    @PostMapping("/{id}/receivable/enter")""",
"""    @PostMapping("/receivable/enter")""",
"FolderPortalController enter mapping")

patch(portal_java,
"""    @PostMapping("/{id}/receivable/exit")""",
"""    @PostMapping("/receivable/exit")""",
"FolderPortalController exit mapping")

patch(portal_java,
"""    @PostMapping("/{id}/toggle-problem")""",
"""    @PostMapping("/toggle-problem")""",
"FolderPortalController toggle-problem mapping")

patch(portal_java,
"""    @PostMapping("/{id}/receivable/settings")""",
"""    @PostMapping("/receivable/settings")""",
"FolderPortalController settings mapping")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix_build_and_warnings: close OWNERS tabWrap in FolderPage, fix Java warnings"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")