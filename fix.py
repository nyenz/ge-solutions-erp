# fix.py -- fix75: review-findings batch + re-land lost seed fixes
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE = ROOT / "erp-frontend" / "src"
DI = BE / "config" / "DataInitializer.java"
SA = BE / "modules" / "admin" / "controller" / "SystemAdminController.java"
RN = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
DC = BE / "modules" / "land" / "controller" / "DashboardController.java"
LS = BE / "modules" / "land" / "service" / "LandService.java"
RS = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
FP = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"

def read(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("WROTE", p.name)

res = []

def lines_of(p):
    return read(p).split("\n")

def save_lines(p, ls):
    write(p, "\n".join(ls))

def swap_line(p, old_strip, new_strips):
    ls = lines_of(p)
    for i, ln in enumerate(ls):
        if ln.strip() == old_strip:
            base = ln[:len(ln) - len(ln.lstrip())]
            ls[i:i+1] = [base + t for t in new_strips]
            save_lines(p, ls)
            res.append("OK swap: " + old_strip[:60])
            return True
    res.append("MISS swap: " + old_strip[:60])
    return False

def delete_line(p, old_strip):
    ls = lines_of(p)
    for i, ln in enumerate(ls):
        if ln.strip() == old_strip:
            ls.pop(i)
            save_lines(p, ls)
            res.append("OK delete: " + old_strip[:60])
            return True
    res.append("MISS delete: " + old_strip[:60])
    return False

def insert_after(p, anchor_strip, new_strips):
    ls = lines_of(p)
    for i, ln in enumerate(ls):
        if ln.strip() == anchor_strip:
            base = ln[:len(ln) - len(ln.lstrip())]
            ls[i+1:i+1] = [base + t for t in new_strips]
            save_lines(p, ls)
            res.append("OK insert after: " + anchor_strip[:50])
            return True
    res.append("MISS insert after: " + anchor_strip[:50])
    return False

def delete_range(p, start_strip, end_strip):
    ls = lines_of(p)
    si = ei = -1
    for i, ln in enumerate(ls):
        if si < 0 and ln.strip() == start_strip:
            si = i
        elif si >= 0 and ln.strip() == end_strip:
            ei = i
            break
    if si >= 0 and ei >= si:
        del ls[si:ei+1]
        save_lines(p, ls)
        res.append("OK delete range: " + start_strip[:50])
        return True
    res.append("MISS delete range: " + start_strip[:50])
    return False

def replace_range(p, start_strip, end_strip, new_strips):
    ls = lines_of(p)
    si = ei = -1
    for i, ln in enumerate(ls):
        if si < 0 and ln.strip() == start_strip:
            si = i
        elif si >= 0 and ln.strip() == end_strip:
            ei = i
            break
    if si >= 0 and ei >= si:
        base = ls[si][:len(ls[si]) - len(ls[si].lstrip())]
        ls[si:ei+1] = [base + t for t in new_strips]
        save_lines(p, ls)
        res.append("OK replace range: " + start_strip[:50])
        return True
    res.append("MISS replace range: " + start_strip[:50])
    return False

# ---------- 1. DataInitializer: re-land lost seed fixes ----------
s = read(DI)
if "notificationService" not in s:
    insert_after(DI, "private final FollowUpRepository followUpRepository;",
        ["private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;"])
if "seedNotificationsIfEmpty();" not in s:
    insert_after(DI, "seedScenarioDataOnce();", ["seedNotificationsIfEmpty();"])
if "self-heal re-seed" not in s:
    swap_line(DI, 'if (seeded) { System.out.println(">>> [SCENARIO] Already seeded -- skipping."); return; }',
        ["if (seeded) {",
         "    int projectRows = 0;",
         '    try (java.sql.PreparedStatement ps2 = conn.prepareStatement("SELECT COUNT(*) FROM land_projects"); java.sql.ResultSet rs2 = ps2.executeQuery()) { rs2.next(); projectRows = rs2.getInt(1); }',
         '    if (projectRows > 0) { System.out.println(">>> [SCENARIO] Already seeded -- skipping."); return; }',
         '    System.out.println(">>> [SCENARIO] Flag set but ledger empty -- self-heal re-seed.");',
         "}"])
if "is_read" not in s:
    swap_line(DI, '"ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL"',
        ['"ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",',
         '"ALTER TABLE notifications DROP COLUMN IF EXISTS is_read"'])
if "seedNotificationsIfEmpty()" not in read(DI):
    insert_after(DI, "private final FollowUpRepository followUpRepository;", [])  # no-op guard
    METHOD = [
    "// fix75: seed demo notifications so the bell is never empty on a fresh seed.",
    "public void seedNotificationsIfEmpty() {",
    "    try (Connection conn = dataSource.getConnection()) {",
    "        int n = 0;",
    '        try (Statement st = conn.createStatement(); java.sql.ResultSet rs = st.executeQuery("SELECT COUNT(*) FROM notifications")) { if (rs.next()) n = rs.getInt(1); }',
    '        if (n > 0) { System.out.println(">>> [SCENARIO] Notifications already present -- skipping."); return; }',
    "        java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();",
    '        try (Statement st = conn.createStatement(); java.sql.ResultSet rs = st.executeQuery("SELECT id FROM land_projects WHERE deleted = false ORDER BY project_index NULLS LAST LIMIT 12")) { while (rs.next()) ids.add((java.util.UUID) rs.getObject(1)); }',
    '        if (ids.isEmpty()) { System.out.println(">>> [SCENARIO] No projects for notification seed -- skipping."); return; }',
    "        java.util.UUID i0 = ids.get(0), i1 = ids.get(1 % ids.size()), i2 = ids.get(2 % ids.size()), i3 = ids.get(3 % ids.size()), i4 = ids.get(4 % ids.size()), i5 = ids.get(5 % ids.size()), i6 = ids.get(6 % ids.size()), i7 = ids.get(7 % ids.size()), i8 = ids.get(8 % ids.size()), i9 = ids.get(9 % ids.size()), i10 = ids.get(10 % ids.size()), i11 = ids.get(11 % ids.size());",
    '        notificationService.emitRaw("NEW_INTAKE", "INFO", "New project registered by SYSTEM seed.", "PROJECT", i0, "ROLE_MANAGER");',
    '        notificationService.emitRaw("PAYMENT_ON_RECEIVABLE", "POSITIVE", "Payment received on a receivable project.", "PROJECT", i1, "ROLE_DIRECTOR");',
    '        notificationService.emitRaw("STORAGE_FEE_APPLIED", "INFO", "Monthly storage fee applied to a receivable project.", "PROJECT", i2, "ROLE_DIRECTOR");',
    '        notificationService.emitRaw("AUTO_RECEIVABLE_365", "WARN", "Project auto-flagged RECEIVABLE after 365 days silent.", "PROJECT", i3, "ROLE_DIRECTOR");',
    '        notificationService.emitRaw("NEGOTIATION_DEADLINE", "WARN", "Negotiation deadline within 3 days on a receivable project.", "PROJECT", i4, "ROLE_MANAGER");',
    '        notificationService.emitRaw("FAILED_AFTER_PROMISE", "CRITICAL", "Client failed to pay after committing to a promise date.", "PROJECT", i5, "ROLE_DIRECTOR");',
    '        notificationService.emitRaw("FAILED_AFTER_PROMISE_ROOT", "CRITICAL", "Client failed to pay after committing -- Root escalation.", "PROJECT", i5, "ROLE_ADMIN");',
    '        notificationService.emitRaw("RELIABILITY_LOW", "WARN", "Client reliability below 40 after negative contact.", "PROJECT", i6, "ROLE_ADMIN");',
    '        notificationService.emitRaw("SITE_VISIT_TAGGED", "INFO", "Client tagged as needing a site visit.", "PROJECT", i7, "ROLE_ADMIN");',
    '        notificationService.emitRaw("PROMISE_DUE", "CRITICAL", "Promised payment date passed with no payment received.", "PROJECT", i8, "ROLE_ADMIN");',
    '        notificationService.emitRaw("COOLDOWN_EXPIRED", "INFO", "Client callable again -- cooldown expired.", "PROJECT", i9, "ROLE_SECRETARY");',
    '        notificationService.emitRaw("MONTHLY_LIMIT", "INFO", "Client reached the 2-call monthly limit.", "PROJECT", i10, "ROLE_MANAGER");',
    '        notificationService.emitRaw("SYSTEM_NOTICE", "INFO", "Demo dataset active -- ledger, recovery and notifications seeded.", "PROJECT", i11, "ALL");',
    '        System.out.println(">>> [SCENARIO] Notification seed complete (13 demo notifications).");',
    "    } catch (Exception e) { System.err.println(\">>> [SCENARIO] notification seed fault: \" + e.getMessage()); }",
    "}",
    ]
    insert_after(DI, "private void runSchemaMigrations() throws Exception {", [])  # anchor probe
    ls = lines_of(DI)
    for i, ln in enumerate(ls):
        if ln.strip() == "private void runSchemaMigrations() throws Exception {":
            base = ln[:len(ln) - len(ln.lstrip())]
            ls[i:i] = [base + t for t in METHOD]
            save_lines(DI, ls)
            res.append("OK inserted seedNotificationsIfEmpty method")
            break
    else:
        res.append("MISS method anchor runSchemaMigrations")

# ---------- 2. SystemAdminController: wipe list + wipe reseed ----------
s2 = read(SA)
if "scenario_seed_flag" not in s2:
    ls = lines_of(SA)
    for i, ln in enumerate(ls):
        if ln.strip() == '"users"':
            base = ln[:len(ln) - len(ln.lstrip())]
            ls[i:i] = [base + t for t in ['"scenario_seed_flag",', '"notification_reads",', '"recovery_notes",', '"project_proprietors",']]
            save_lines(SA, ls)
            res.append("OK wipe list extended")
            break
    else:
        res.append("MISS wipe list anchor users")
if "seedScenarioDataOnce" not in read(SA):
    insert_after(SA, 'System.out.println(">>> [WIPE] OK: default expense presets reseeded");',
        ["try {",
         "    dataInitializer.seedScenarioDataOnce();",
         '    System.out.println(">>> [WIPE] OK: scenario dataset reseeded after wipe");',
         "} catch (Exception e) {",
         '    System.err.println(">>> [WIPE] scenario reseed warning: " + e.getMessage());',
         "}"])

# ---------- 3. RecoveryNoteController: contains-bug + qualifies bug + notif repeats ----------
swap_line(RN, "if (p.getProprietors() != null && p.getProprietors().contains(c)) out.add(p);",
    ["if (p.getProprietors() != null && p.getProprietors().stream().anyMatch(o -> o != null && o.getId() != null && o.getId().equals(c.getId()))) out.add(p);"])
delete_line(RN, "return true;")
swap_line(RN, 'notificationService.emit("NEG_STREAK_2", "WARN", c.getFullName() + ": 2 negative contacts in a row - suggest site visit.", "CLIENT", c.getId(), "ROLE_MANAGER");',
    ['if (!notificationService.existsToday("NEG_STREAK_2", c.getId())) notificationService.emitRaw("NEG_STREAK_2", "WARN", c.getFullName() + ": 2 negative contacts in a row - suggest site visit.", "CLIENT", c.getId(), "ROLE_MANAGER");'])
swap_line(RN, 'notificationService.emit("FAILED_AFTER_PROMISE", "CRITICAL", c.getFullName() + " failed to pay after committing. Escalate.", "CLIENT", c.getId(), "ROLE_DIRECTOR");',
    ['notificationService.emitRaw("FAILED_AFTER_PROMISE", "CRITICAL", c.getFullName() + " failed to pay after committing. Escalate.", "CLIENT", c.getId(), "ROLE_DIRECTOR");'])
swap_line(RN, 'notificationService.emit("FAILED_AFTER_PROMISE_M", "CRITICAL", c.getFullName() + " failed to pay after committing. Escalate.", "CLIENT", c.getId(), "ROLE_MANAGER");',
    ['notificationService.emitRaw("FAILED_AFTER_PROMISE_M", "CRITICAL", c.getFullName() + " failed to pay after committing. Escalate.", "CLIENT", c.getId(), "ROLE_MANAGER");'])
swap_line(RN, 'notificationService.emit("RELIABILITY_LOW", "WARN", c.getFullName() + " reliability below 40 after negative contact.", "CLIENT", c.getId(), "ROLE_MANAGER");',
    ['if (!notificationService.existsToday("RELIABILITY_LOW", c.getId())) notificationService.emitRaw("RELIABILITY_LOW", "WARN", c.getFullName() + " reliability below 40 after negative contact.", "CLIENT", c.getId(), "ROLE_MANAGER");'])
swap_line(RN, 'notificationService.emit("SITE_VISIT_TAGGED", "INFO", c.getFullName() + " needs a site visit.", "CLIENT", c.getId(), "ROLE_DIRECTOR");',
    ['if (!notificationService.existsToday("SITE_VISIT_TAGGED", c.getId())) notificationService.emitRaw("SITE_VISIT_TAGGED", "INFO", c.getFullName() + " needs a site visit.", "CLIENT", c.getId(), "ROLE_DIRECTOR");'])

# ---------- 4. DashboardController: parity with live recovery rule ----------
replace_range(DC,
    "java.util.Optional<com.gesolutions.erp.modules.client.model.RecoveryNote> last = recoveryNoteRepository.findFirstByClientOrderByCreatedAtDesc(owner);",
    "return !java.time.LocalDate.now().isBefore(eligible);",
    ["java.time.LocalDateTime lastContact = owner.getLastContactedAt();",
     "if (lastContact != null && lastContact.isAfter(java.time.LocalDateTime.now().minusDays(14))) return false;",
     "return true;"])
swap_line(DC, "// RecoveryController.buildOwnerTasks's eligibility rule exactly.",
    ["// RecoveryNoteController locked()/qualifies() rule exactly (live /recovery/stats)."])

# ---------- 5. LandService + Scheduler: recurring notifications ----------
swap_line(LS, 'notificationService.emit("NEGOTIATION_DEADLINE", "WARN", "Negotiation deadline for " + plotLabel(project) + " is within 3 days.", "PROJECT", projectId, "ROLE_MANAGER");',
    ['notificationService.emitRaw("NEGOTIATION_DEADLINE", "WARN", "Negotiation deadline for " + plotLabel(project) + " is within 3 days.", "PROJECT", projectId, "ROLE_MANAGER");'])
swap_line(RS, 'notificationService.emit("STORAGE_FEE_APPLIED", "INFO", "Storage fee UGX " + toAdd + " added to " + ownerLabel(plot) + ".", "PROJECT", plot.getId(), "ROLE_DIRECTOR");',
    ['if (!notificationService.existsToday("STORAGE_FEE_APPLIED", plot.getId())) notificationService.emitRaw("STORAGE_FEE_APPLIED", "INFO", "Storage fee UGX " + toAdd + " added to " + ownerLabel(plot) + ".", "PROJECT", plot.getId(), "ROLE_DIRECTOR");'])
replace_range(RS, 'notificationService.emit("PROMISE_DUE", "CRITICAL",', '"NOTE", n.getId(), "ROLE_MANAGER");',
    ['if (!notificationService.existsToday("PROMISE_DUE", n.getId())) notificationService.emitRaw("PROMISE_DUE", "CRITICAL",',
     'c.getFullName() + " promised to pay by " + n.getPromiseDate() + " but no payment arrived.",',
     '"NOTE", n.getId(), "ROLE_MANAGER");'])
swap_line(RS, "if (p.getProprietors() == null || !p.getProprietors().contains(c)) continue;",
    ["if (p.getProprietors() == null || !p.getProprietors().stream().anyMatch(o -> o != null && o.getId() != null && o.getId().equals(c.getId()))) continue;"])

# ---------- 6. FolderPage: dup effect, source filter, dead vars, prompt modal ----------
ls = lines_of(FP)
for i, ln in enumerate(ls):
    if (ln.strip().startswith("Promise.all(binder.project.proprietors") and ln.strip().endswith("slice(0, 20)));")
            and i >= 2 and ls[i-1].strip() == "if (!binder?.project?.proprietors) return;"
            and ls[i-2].strip() == "useEffect(() => {" and ls[i+1].strip() == "}, [binder]);"):
        del ls[i-2:i+2]
        save_lines(FP, ls)
        res.append("OK removed duplicate recovery-notes useEffect")
        break
else:
    res.append("MISS duplicate useEffect block")
swap_line(FP, "const all = lists.flat().sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 20);",
    ["const all = lists.flat().filter(n => n.source === 'RECOVERY').sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 20);"])
delete_line(FP, "const lastPay = project?.lastPaymentDate ? new Date(project.lastPaymentDate) : null;")
delete_line(FP, "const daysSincePay = lastPay ? Math.floor((Date.now() - lastPay.getTime()) / 86400000) : null;")
delete_range(FP, "const statusBadge = isReceivable ? ['RECEIVABLE', 'badgeRecv']", ": ['ACTIVE', 'badgeActive'];")
insert_after(FP, "const [freezeOpen, setFreezeOpen] = useState(false);",
    ["const [problemModal, setProblemModal] = useState({ open: false, note: '' });"])
swap_line(FP, "const handleToggleProblem = async () => { const was = project.problem; let note = ''; if (!was) { note = window.prompt('Describe the problem (optional):') || ''; } try { await folderPortalService.toggleProblem(id, note); if (!was && note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast(was ? 'Problem flag removed.' : 'Flagged as PROBLEM.', was ? 'info' : 'warn'); } catch { toast('FLAG FAILED', 'error'); } };",
    ["const handleToggleProblem = async () => { const was = project.problem; if (!was) { setProblemModal({ open: true, note: '' }); return; } try { await folderPortalService.toggleProblem(id, ''); await loadFolderData(); toast('Problem flag removed.', 'info'); } catch { toast('FLAG FAILED', 'error'); } };",
     "const confirmProblemFlag = async () => { const note = problemModal.note; setProblemModal({ open: false, note: '' }); try { await folderPortalService.toggleProblem(id, ''); if (note.trim()) { await landService.addStandaloneNote(id, '[PROBLEM] ' + note.trim()); } await loadFolderData(); toast('Flagged as PROBLEM.', 'warn'); } catch { toast('FLAG FAILED', 'error'); } };"])
insert_after(FP, "<BackToTopButton />", [])  # probe
ls = lines_of(FP)
for i, ln in enumerate(ls):
    if ln.strip() == "<BackToTopButton />":
        base = ln[:len(ln) - len(ln.lstrip())]
        block = [
        base + "<HardwareModal isOpen={problemModal.open} onClose={() => setProblemModal({ open: false, note: '' })} title=\"FLAG AS PROBLEM\">",
        base + "<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>DESCRIBE THE PROBLEM (OPTIONAL)</label><textarea className={modalStyles.modalTextarea} value={problemModal.note} onChange={e => setProblemModal(p => ({ ...p, note: e.target.value }))} placeholder=\"e.g. Boundary dispute reported by neighbour...\" aria-label=\"Problem description\" /></div>",
        base + "<div className={modalStyles.modalFooter}>",
        base + "<button type=\"button\" className={modalStyles.modalBtnPrimary} onClick={confirmProblemFlag}><FiAlertTriangle aria-hidden=\"true\" /> CONFIRM FLAG</button>",
        base + "</div>",
        base + "</HardwareModal>",
        ]
        ls[i:i] = block
        save_lines(FP, ls)
        res.append("OK inserted problem-note HardwareModal")
        break
else:
    res.append("MISS BackToTopButton anchor")

for r in res:
    print(r)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix75: review-findings batch - recovery contains/qualifies bugs, dashboard parity, folder dup notes, prompt modal, recurring notifications, re-land seed fixes"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")