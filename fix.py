# fix.py -- fix86: consolidated - fix85 backend items + recovery card grid, ledger-style pay dots, notes colour fixes
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8", errors="replace")
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
    print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: write(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)

# ---------- A. RecoveryPortal.jsx: auth, delete button, dead code, ledger-style dots ----------
jsxp = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
patch(jsxp, "import recoveryService from '../../services/recoveryService';",
"import recoveryService from '../../services/recoveryService';\nimport { useAuth } from '../../hooks/useAuth';", "useAuth import")
patch(jsxp, "import { FiSearch, FiX, FiPhone, FiMapPin, FiClock, FiChevronDown, FiChevronUp, FiUser, FiFolderPlus, FiFilePlus, FiArchive } from 'react-icons/fi';",
"import { FiSearch, FiX, FiPhone, FiMapPin, FiClock, FiChevronDown, FiChevronUp, FiUser, FiFolderPlus } from 'react-icons/fi';", "trim unused icons")
patch(jsxp, """function Badge({ type }) {
  const cls = type === 'Legacy Title' ? styles.badgeLegacy : type === 'New Title' ? styles.badgeTitle : styles.badgeFolder;
  const Icon = type === 'Legacy Title' ? FiArchive : type === 'New Title' ? FiFilePlus : FiFolderPlus;
  return <span className={cls}><Icon size={11} aria-hidden="true" /> {type}</span>;
}
""", "", "remove dead Badge helper")
patch(jsxp, "  const load = useCallback(() => {",
"""  const { user } = useAuth();
  const canManage = user?.isRoot || ['ROLE_ADMIN', 'ROLE_DIRECTOR', 'ROLE_MANAGER'].includes(user?.role);
  const load = useCallback(() => {""", "canManage flag")
patch(jsxp, """                <span className={styles.histMeta}>{n.author || 'SYSTEM'} - {fmtD(n.createdAt)}</span>
                {n.text && <span className={styles.histText}>{n.text}</span>}
              </div>""",
"""                <span className={styles.histMeta}>{n.author || 'SYSTEM'} - {fmtD(n.createdAt)}</span>
                {n.text && <span className={styles.histText}>{n.text}</span>}
                {canManage && n.source === 'RECOVERY' && n.tag !== 'payment received' && (
                  <button type="button" className={styles.histDelete} aria-label="Delete note"
                    onClick={() => recoveryService.deleteNote(n.id).then(() => { toast('Note deleted.', 'warn'); recoveryService.getNotes(sel.id).then((r) => setNotes(r.data || [])); load(); })}>
                    <FiX aria-hidden="true" />
                  </button>
                )}
              </div>""", "delete-note button in history")
patch(jsxp, "<span title={'Payment health: ' + c.payBadge} style={{ width: 8, height: 8, borderRadius: '50%', display: 'inline-block', background: c.payBadge === 'GREEN' ? '#22c55e' : c.payBadge === 'YELLOW' ? '#f59e0b' : '#ef4444', boxShadow: '0 0 4px ' + (c.payBadge === 'GREEN' ? '#22c55e' : c.payBadge === 'YELLOW' ? '#f59e0b' : '#ef4444') }} />",
"<span className={c.payBadge === 'GREEN' ? styles.payDotGreen : c.payBadge === 'YELLOW' ? styles.payDotYellow : styles.payDotRed} title={c.payBadge === 'GREEN' ? 'Recent payment' : c.payBadge === 'YELLOW' ? 'Payment 2-4 weeks ago' : 'No recent payment'} />", "ledger-style pay dot on card")
patch(jsxp, """      <div className={styles.dotLegend} aria-label="Payment dot legend">
        <span><i style={{ background: '#22c55e' }} /> paid in last 14 days</span>
        <span><i style={{ background: '#f59e0b' }} /> paid 15-30 days ago</span>
        <span><i style={{ background: '#ef4444' }} /> over 30 days or never</span>
      </div>""",
"""      <div className={styles.dotLegend} aria-label="Payment dot legend">
        <span><i className={styles.payDotGreen} /> Recent payment</span>
        <span><i className={styles.payDotYellow} /> Payment 2-4 weeks ago</span>
        <span><i className={styles.payDotRed} /> No recent payment</span>
      </div>""", "ledger-style legend wording")

# ---------- B. Recovery CSS: card body grid (spacing glitch) + dot classes ----------
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
s = read(cssp)
if "payDotGreen" not in s:
    s += """
/* fix86: ledger-format pay dots + compact card body grid */
.payDotGreen, .payDotYellow, .payDotRed { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.payDotGreen { background: #22c55e; box-shadow: 0 0 4px #22c55e; }
.payDotYellow { background: #f59e0b; box-shadow: 0 0 4px #f59e0b; }
.payDotRed { background: #ef4444; box-shadow: 0 0 4px #ef4444; }
.dotLegend i { width: 8px; height: 8px; }
.rowBody { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 6px 20px; align-items: center; }
.rowActions { grid-column: 1 / -1; }
.lockBanner { grid-column: 1 / -1; }
"""
    write(cssp, s)
    print("OK recovery css grid + dots")
else:
    print("SKIP recovery css already present")

# ---------- C. Folder page: recovery chip meta colour (was grey-on-dark collision) ----------
fpx = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
patch(fpx, "<span className={styles.noteAuthor}>{n.author || 'SYSTEM'} - {new Date(n.createdAt).toLocaleDateString()}</span>",
"<span className={styles.recvChipMeta}>{n.author || 'SYSTEM'} - {new Date(n.createdAt).toLocaleDateString()}</span>", "folder chip meta class")
fcss = FE / "pages" / "DigitalFolder" / "FolderPage.module.css"
c2 = read(fcss)
if "recvChipMeta" not in c2:
    c2 += """
/* fix86: light-on-dark meta for recovery chips inside NOTES panel */
.recvChipMeta { font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.55); letter-spacing: 0.4px; }
"""
    write(fcss, c2)
    print("OK folder recvChipMeta css")
else:
    print("SKIP folder css already present")

# ---------- D. Payments page: notes readability ----------
patch(FE / "pages" / "Payments" / "PaymentsPage.module.css",
".payNotes { color: rgba(255,255,255,0.35); font-style: italic; }",
".payNotes { color: rgba(255,255,255,0.5); font-style: italic; }", "payments notes readability")

# ---------- E. Backend (from pending fix85): calls-today counts all attempts, single-pass stats, notes perf ----------
rc = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
patch(rc, "                if (n.getCreatedAt().toLocalDate().equals(now.toLocalDate()) && \"POSITIVE\".equals(n.getTone())) callsToday++;",
"                if (n.getCreatedAt().toLocalDate().equals(now.toLocalDate()) && n.isCountsAsAttempt()) callsToday++;", "callsToday = all attempts")
patch(rc, "        long callsToday = 0, succMonth = 0, missMonth = 0, longest = 0; String longestName = \"-\";",
"        long callsToday = 0, succMonth = 0, missMonth = 0, longest = 0, allDue = 0; String longestName = \"-\";", "allDue counter")
patch(rc, """            if (st.equals("NEW") || st.equals("CONTACTED") || st.equals("MISSED")) {
                long d = c.getLastContactedAt() == null ? 999 : ChronoUnit.DAYS.between(c.getLastContactedAt(), now);""",
"""            if (st.equals("NEW") || st.equals("CONTACTED") || st.equals("MISSED")) {
                allDue++;
                long d = c.getLastContactedAt() == null ? 999 : ChronoUnit.DAYS.between(c.getLastContactedAt(), now);""", "count dueNow in same pass")
patch(rc, "        m.put(\"dueNow\", queueCounts().get(\"ALL\"));",
"        m.put(\"dueNow\", allDue);", "dueNow without second pass")
patch(rc, """    public List<Map<String, Object>> notes(@PathVariable UUID id) {
        return clientRepo.findById(id).map(c -> {""",
"""    public List<Map<String, Object>> notes(@PathVariable UUID id) {
        Map<UUID, List<LandProject>> pm = projMap();
        return clientRepo.findById(id).map(c -> {""", "notes: build projMap once")
patch(rc, "            for (LandProject p : projMap().getOrDefault(c.getId(), List.of())) for (FollowUpLog log : followUpRepo.findByProjectIdOrderByTimestampDesc(p.getId())) {",
"            for (LandProject p : pm.getOrDefault(c.getId(), List.of())) for (FollowUpLog log : followUpRepo.findByProjectIdOrderByTimestampDesc(p.getId())) {", "notes: use cached map")

# ---------- F. Scheduler: callable-again alert ----------
rs = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
patch(rs, "    private final NotificationService notificationService;",
"""    private final NotificationService notificationService;
    private final com.gesolutions.erp.modules.client.repository.ClientRepository clientRepo;
    private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;""", "scheduler repos back")
patch(rs, """    public void dailyNotificationSweep() {
        return; // fix79: old cooldown/promise loop disabled by new 30-day recovery engine
    }""",
"""    public void dailyNotificationSweep() {
        return; // old promise/cooldown loops stay disabled
    }
    @Scheduled(cron = "0 0 7 * * *")
    @Transactional
    public void unlockSweep() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        java.time.LocalDateTime yesterday = now.minusDays(1);
        for (com.gesolutions.erp.modules.client.model.Client c : clientRepo.findAll()) {
            boolean lockedYesterday = lockedAt(c, yesterday) != null;
            boolean lockedToday = lockedAt(c, now) != null;
            if (lockedYesterday && !lockedToday) {
                notificationService.emitRaw("UNLOCK", "INFO", c.getFullName() + " is callable again.", "CLIENT", c.getId(), "ROLE_SECRETARY");
                notificationService.emitRaw("UNLOCK_M", "INFO", c.getFullName() + " is callable again.", "CLIENT", c.getId(), "ROLE_MANAGER");
            }
        }
    }
    private java.time.LocalDate lockedAt(com.gesolutions.erp.modules.client.model.Client c, java.time.LocalDateTime now) {
        java.time.LocalDate unlock = null;
        java.time.LocalDateTime pay = null;
        for (LandProject p : projectRepository.findAll()) {
            if (p.getProprietors() == null) continue;
            boolean mine = p.getProprietors().stream().anyMatch(o -> o != null && o.getId() != null && o.getId().equals(c.getId()));
            if (!mine) continue;
            if (p.getLastPaymentDate() != null && (pay == null || p.getLastPaymentDate().isAfter(pay))) pay = p.getLastPaymentDate();
        }
        if (pay != null && pay.plusDays(30).isAfter(now)) unlock = pay.plusDays(30).toLocalDate();
        java.time.LocalDateTime second = null; int count = 0;
        for (com.gesolutions.erp.modules.client.model.RecoveryNote n : recoveryNoteRepository.findByClientOrderByCreatedAtDesc(c)) {
            if ("POSITIVE".equals(n.getTone()) && n.isCountsAsAttempt() && n.getCreatedAt().isAfter(now.minusDays(30))) { count++; if (count == 2) second = n.getCreatedAt(); }
        }
        if (second != null) { java.time.LocalDate u2 = second.plusDays(30).toLocalDate(); if (unlock == null || u2.isAfter(unlock)) unlock = u2; }
        return unlock;
    }""", "unlock sweep added")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix86: consolidated fix85 backend + recovery card grid, ledger-style pay dots, notes colour fixes"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")