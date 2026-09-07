# fix.py -- fix78: final recovery engine (call/miss only, 30-day lock, auto site visit, payment auto-note)
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

# ---------- 1. RecoveryNoteController: full rewrite ----------
write(BE / "modules" / "client" / "controller" / "RecoveryNoteController.java",
"""package com.gesolutions.erp.modules.client.controller;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
@RestController
@RequestMapping("/api/v1/recovery")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_SECRETARY','ROLE_ADMIN','ROLE_DIRECTOR')")
public class RecoveryNoteController {
    private final ClientRepository clientRepo;
    private final RecoveryNoteRepository noteRepo;
    private final UserRepository userRepo;
    private final LandProjectRepository projectRepo;
    private final FollowUpRepository followUpRepo;
    private final AuditService auditService;
    private final NotificationService notificationService;
    private static final String[][] TAGS = {
        {"answered call",   "POSITIVE", "true"},
        {"not picking up",  "NEGATIVE", "true"},
        {"not going through","NEGATIVE", "true"},
        {"wrong number",    "NEGATIVE", "true"}
    };
    private static String[] tagDef(String tag) { for (String[] t : TAGS) if (t[0].equals(tag)) return t; return null; }
    private List<LandProject> projectsOf(Client c) {
        List<LandProject> out = new ArrayList<>();
        for (LandProject p : projectRepo.findAll()) {
            if (p.getProprietors() != null && p.getProprietors().stream().anyMatch(o -> o != null && o.getId() != null && o.getId().equals(c.getId()))) out.add(p);
        }
        return out;
    }
    private String entryTypeOf(List<LandProject> ps) {
        for (LandProject p : ps) { if (p.isLegacy()) return "Legacy Title"; if (p.getLandTitle() != null) return "New Title"; }
        return ps.isEmpty() ? null : "New Folder";
    }
    private boolean qualifies(List<LandProject> ps) {
        if (ps.isEmpty()) return false;
        for (LandProject p : ps) {
            if (p.isLegacy()) return true;
            if (Math.max(p.activeTotalOwed().doubleValue(), p.receivableTotalOwed().doubleValue()) > 0) return true;
            if (p.getStages() != null) { for (Object s : p.getStages()) { if (s instanceof com.gesolutions.erp.modules.land.model.ProjectStage) { if (!((com.gesolutions.erp.modules.land.model.ProjectStage) s).isCompleted()) return true; } } }
            return true;
        }
        return false;
    }
    private String payBadge(List<LandProject> ps) {
        LocalDateTime newest = null;
        for (LandProject p : ps) if (p.getLastPaymentDate() != null && (newest == null || p.getLastPaymentDate().isAfter(newest))) newest = p.getLastPaymentDate();
        if (newest == null) return "RED";
        long d = ChronoUnit.DAYS.between(newest, LocalDateTime.now());
        return d <= 14 ? "GREEN" : d <= 30 ? "YELLOW" : "RED";
    }
    private LocalDateTime lastPayment(List<LandProject> ps) {
        LocalDateTime newest = null;
        for (LandProject p : ps) if (p.getLastPaymentDate() != null && (newest == null || p.getLastPaymentDate().isAfter(newest))) newest = p.getLastPaymentDate();
        return newest;
    }
    private List<RecoveryNote> succ30(Client c, LocalDateTime now) {
        List<RecoveryNote> out = new ArrayList<>();
        for (RecoveryNote n : noteRepo.findByClientOrderByCreatedAtDesc(c)) if ("POSITIVE".equals(n.getTone()) && n.isCountsAsAttempt() && n.getCreatedAt().isAfter(now.minusDays(30))) out.add(n);
        return out;
    }
    private long miss30(Client c, LocalDateTime now) {
        long n = 0;
        for (RecoveryNote x : noteRepo.findByClientOrderByCreatedAtDesc(c)) if ("NEGATIVE".equals(x.getTone()) && x.isCountsAsAttempt() && x.getCreatedAt().isAfter(now.minusDays(30))) n++;
        return n;
    }
    private LocalDate lockedUntil(Client c, LocalDateTime now, List<LandProject> ps) {
        LocalDate unlock = null;
        LocalDateTime pay = lastPayment(ps);
        if (pay != null && pay.plusDays(30).isAfter(now)) unlock = pay.plusDays(30).toLocalDate();
        List<RecoveryNote> succ = succ30(c, now);
        if (succ.size() >= 2) {
            LocalDate u2 = succ.get(1).getCreatedAt().plusDays(30).toLocalDate();
            if (unlock == null || u2.isAfter(unlock)) unlock = u2;
        }
        return unlock;
    }
    private boolean siteVisit(Client c, LocalDateTime now) { return miss30(c, now) >= 2 && succ30(c, now).isEmpty(); }
    private String state(Client c, LocalDateTime now, List<LandProject> ps) {
        if (lockedUntil(c, now, ps) != null) return "LOCKED";
        if (siteVisit(c, now)) return "SITE";
        Optional<RecoveryNote> last = noteRepo.findFirstByClientOrderByCreatedAtDesc(c);
        if (!last.isPresent()) return "NEW";
        if ("POSITIVE".equals(last.get().getTone())) return "CONTACTED";
        if ("NEGATIVE".equals(last.get().getTone())) return "MISSED";
        return "NEW";
    }
    private long dayMiss(Client c, LocalDateTime now) {
        LocalDateTime oldest = null;
        for (RecoveryNote n : noteRepo.findByClientOrderByCreatedAtDesc(c)) if ("NEGATIVE".equals(n.getTone()) && n.isCountsAsAttempt() && n.getCreatedAt().isAfter(now.minusDays(30))) oldest = n.getCreatedAt();
        if (oldest == null) return 0;
        return Math.min(30, ChronoUnit.DAYS.between(oldest, now));
    }
    private Map<String, Object> clientDto(Client c, LocalDateTime now, List<LandProject> ps) {
        Map<String, Object> m = new LinkedHashMap<>();
        String st = state(c, now, ps);
        LocalDate unlock = lockedUntil(c, now, ps);
        LocalDateTime pay = lastPayment(ps);
        long days = c.getLastContactedAt() == null ? -1 : ChronoUnit.DAYS.between(c.getLastContactedAt(), now);
        m.put("id", c.getId()); m.put("name", c.getFullName()); m.put("nin", c.getNationalId()); m.put("phone", c.getPhoneNumber());
        m.put("entryType", entryTypeOf(ps));
        List<String> idx = new ArrayList<>(); List<String> pids = new ArrayList<>(); List<String> co = new ArrayList<>();
        for (LandProject p : ps) {
            if (p.getProjectIndex() != null) idx.add(p.getProjectIndex());
            pids.add(p.getId().toString());
            if (p.getProprietors() != null) for (Client o : p.getProprietors()) if (!o.getId().equals(c.getId()) && !co.contains(o.getFullName())) co.add(o.getFullName());
        }
        m.put("indexes", idx); m.put("projectIds", pids); m.put("coNames", co);
        m.put("district", ps.isEmpty() ? null : ps.get(0).getDistrict());
        m.put("village", ps.isEmpty() ? null : ps.get(0).getVillage());
        m.put("lastContactedAt", c.getLastContactedAt());
        m.put("payBadge", payBadge(ps));
        m.put("state", st); m.put("unlock", unlock == null ? null : unlock.toString());
        m.put("dayMiss", (st.equals("MISSED") || st.equals("SITE")) ? dayMiss(c, now) : 0);
        m.put("calls30", succ30(c, now).size()); m.put("miss30", miss30(c, now));
        noteRepo.findFirstByClientOrderByCreatedAtDesc(c).ifPresent(n -> { m.put("lastTag", n.getTag()); m.put("lastTone", n.getTone()); });
        String reason;
        if (st.equals("LOCKED")) reason = (pay != null && pay.plusDays(30).isAfter(now)) ? "paid " + pay.toLocalDate() + " - rest until " + unlock : "2 good calls - rest until " + unlock;
        else if (st.equals("SITE")) reason = "missed twice - plan a visit";
        else if (st.equals("MISSED")) reason = "missed " + days + " days ago";
        else if (st.equals("CONTACTED")) reason = "spoke " + days + " days ago";
        else reason = days < 0 ? "never called" : "waiting " + days + " days";
        m.put("reason", reason);
        return m;
    }
    @GetMapping("/tags")
    public List<Map<String, Object>> tags() {
        List<Map<String, Object>> out = new ArrayList<>();
        for (String[] t : TAGS) { Map<String, Object> m = new LinkedHashMap<>(); m.put("tag", t[0]); m.put("tone", t[1]); m.put("countsAsAttempt", Boolean.parseBoolean(t[2])); out.add(m); }
        return out;
    }
    @GetMapping("/queues")
    public Map<String, Object> queueCounts() {
        LocalDateTime now = LocalDateTime.now();
        long all = 0, con = 0, mis = 0, site = 0, lock = 0;
        for (Client c : clientRepo.findAll()) {
            List<LandProject> ps = projectsOf(c);
            if (!qualifies(ps)) continue;
            String st = state(c, now, ps);
            if (st.equals("LOCKED")) lock++;
            else if (st.equals("SITE")) site++;
            else { all++; if (st.equals("CONTACTED")) con++; if (st.equals("MISSED")) mis++; }
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("ALL", all); m.put("CONTACTED", con); m.put("MISSED", mis); m.put("SITE", site); m.put("LOCKED", lock);
        return m;
    }
    @GetMapping("/queue")
    public List<Map<String, Object>> queue(@RequestParam(defaultValue = "ALL") String queue) {
        LocalDateTime now = LocalDateTime.now();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Client c : clientRepo.findAll()) {
            List<LandProject> ps = projectsOf(c);
            if (!qualifies(ps)) continue;
            String st = state(c, now, ps);
            boolean inAll = st.equals("NEW") || st.equals("CONTACTED") || st.equals("MISSED");
            if (queue.equals("ALL") ? !inAll : !st.equals(queue)) continue;
            out.add(clientDto(c, now, ps));
        }
        out.sort((x, y) -> {
            LocalDateTime a = (LocalDateTime) x.get("lastContactedAt");
            LocalDateTime b = (LocalDateTime) y.get("lastContactedAt");
            if (a == null && b == null) return 0;
            if (a == null) return -1;
            if (b == null) return 1;
            return a.compareTo(b);
        });
        int total = out.size(), pos = 1;
        for (Map<String, Object> d : out) { d.put("position", pos++); d.put("queueTotal", total); }
        return out;
    }
    @GetMapping("/stats")
    public Map<String, Object> stats() {
        LocalDateTime now = LocalDateTime.now();
        long callsToday = noteRepo.countByCountsAsAttemptTrueAndCreatedAtAfter(now.toLocalDate().atStartOfDay());
        long succMonth = 0, missMonth = 0, longest = 0; String longestName = "-";
        for (Client c : clientRepo.findAll()) {
            List<LandProject> ps = projectsOf(c);
            if (!qualifies(ps)) continue;
            for (RecoveryNote n : noteRepo.findByClientOrderByCreatedAtDesc(c)) {
                if (!n.getCreatedAt().isAfter(now.minusDays(30))) break;
                if ("POSITIVE".equals(n.getTone())) succMonth++;
                if ("NEGATIVE".equals(n.getTone())) missMonth++;
            }
            String st = state(c, now, ps);
            if (st.equals("NEW") || st.equals("CONTACTED") || st.equals("MISSED")) {
                long d = c.getLastContactedAt() == null ? 999 : ChronoUnit.DAYS.between(c.getLastContactedAt(), now);
                if (d > longest) { longest = d; longestName = c.getFullName(); }
            }
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("dueNow", queueCounts().get("ALL"));
        m.put("callsToday", callsToday); m.put("callsMonth", succMonth);
        m.put("missMonth", missMonth); m.put("longestWait", longest == 999 ? "NEW" : longest + "d");
        m.put("longestName", longestName);
        return m;
    }
    @GetMapping("/locked")
    public List<Map<String, Object>> lockedList() { return queue("LOCKED"); }
    @GetMapping("/clients/{id}/notes")
    public List<Map<String, Object>> notes(@PathVariable UUID id) {
        return clientRepo.findById(id).map(c -> {
            List<Map<String, Object>> out = new ArrayList<>();
            for (RecoveryNote n : noteRepo.findByClientOrderByCreatedAtDesc(c)) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("id", n.getId()); m.put("tag", n.getTag()); m.put("tone", n.getTone());
                m.put("text", n.getText()); m.put("countsAsAttempt", n.isCountsAsAttempt());
                m.put("createdAt", n.getCreatedAt()); m.put("source", "RECOVERY");
                m.put("author", n.getAuthor() == null ? null : n.getAuthor().getUsername());
                out.add(m);
            }
            for (LandProject p : projectsOf(c)) for (FollowUpLog log : followUpRepo.findByProjectIdOrderByTimestampDesc(p.getId())) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("id", log.getId()); m.put("tag", "FOLDER NOTE"); m.put("tone", "INFO");
                m.put("text", log.getNotes()); m.put("countsAsAttempt", false);
                m.put("createdAt", log.getTimestamp()); m.put("source", "FOLDER"); m.put("author", log.getRecordedBy());
                out.add(m);
            }
            out.sort((a, b) -> ((LocalDateTime) b.get("createdAt")).compareTo((LocalDateTime) a.get("createdAt")));
            return out;
        }).orElse(List.of());
    }
    @PostMapping("/notes")
    public ResponseEntity<?> log(@RequestBody Map<String, String> body, Authentication auth) {
        String[] def = tagDef(body.get("tag"));
        if (def == null) return ResponseEntity.badRequest().body(Map.of("error", "Unknown tag"));
        Client c = clientRepo.findById(UUID.fromString(body.get("clientId"))).orElseThrow(() -> new RuntimeException("Client not found"));
        LocalDateTime now = LocalDateTime.now();
        List<LandProject> ps = projectsOf(c);
        LocalDate unlock = lockedUntil(c, now, ps);
        if (unlock != null) return ResponseEntity.status(409).body(Map.of("error", "Resting until " + unlock));
        boolean wasSite = siteVisit(c, now);
        User author = userRepo.findByUsername(auth.getName()).orElse(null);
        RecoveryNote n = RecoveryNote.builder().client(c).author(author).tag(def[0]).tone(def[1]).countsAsAttempt(true)
            .text(body.get("text") == null || body.get("text").isBlank() ? null : body.get("text").trim()).build();
        noteRepo.save(n);
        c.setLastContactedAt(now);
        double delta = "POSITIVE".equals(def[1]) ? 1.5 : -2;
        double cur = c.getReliabilityScore() == null ? 100.0 : c.getReliabilityScore();
        c.setReliabilityScore(Math.max(0.0, Math.min(100.0, cur + delta)));
        clientRepo.save(c);
        auditService.logAction("RECOVERY_NOTE", "RECOVERY_NOTE: " + def[0] + " (NIN " + c.getNationalId() + ")");
        if ("POSITIVE".equals(def[1]) && succ30(c, now).size() == 2) {
            LocalDate u = lockedUntil(c, now, ps);
            notificationService.emitRaw("LOCKED", "INFO", c.getFullName() + " had 2 good calls. Rest until " + u + ".", "CLIENT", c.getId(), author == null ? "ROLE_MANAGER" : author.getRole().name());
        }
        if (!wasSite && siteVisit(c, now)) {
            notificationService.emitRaw("SITE_VISIT_AUTO", "WARN", c.getFullName() + " missed twice with no answer in 30 days. Plan a site visit.", "CLIENT", c.getId(), "ROLE_MANAGER");
        }
        if ("NEGATIVE".equals(def[1]) && c.getReliabilityScore() < 40 && !notificationService.existsToday("RELIABILITY_LOW", c.getId())) {
            notificationService.emitRaw("RELIABILITY_LOW", "WARN", c.getFullName() + " reliability below 40 after missed calls.", "CLIENT", c.getId(), "ROLE_MANAGER");
        }
        String warning = null;
        LocalDateTime window = now.minusDays(3);
        for (LandProject p : ps) for (Client co : p.getProprietors()) {
            if (co.getId().equals(c.getId())) continue;
            for (RecoveryNote other : noteRepo.findByClientOrderByCreatedAtDesc(co)) {
                if (other.isCountsAsAttempt() && other.getCreatedAt().isAfter(window)) { warning = co.getFullName() + " was already contacted about this plot on " + other.getCreatedAt().toLocalDate() + "."; break; }
            }
            if (warning != null) break;
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("ok", true); resp.put("id", n.getId());
        if (warning != null) resp.put("coOwnerWarning", warning);
        return ResponseEntity.ok(resp);
    }
    @DeleteMapping("/notes/{id}")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    public ResponseEntity<?> deleteNote(@PathVariable UUID id, Authentication auth) {
        RecoveryNote n = noteRepo.findById(id).orElse(null);
        if (n == null) return ResponseEntity.ok(Map.of("ok", true));
        Client c = n.getClient();
        noteRepo.delete(n);
        if (c != null) {
            LocalDateTime newest = null;
            for (RecoveryNote r : noteRepo.findByClientOrderByCreatedAtDesc(c)) if (r.isCountsAsAttempt()) { newest = r.getCreatedAt(); break; }
            c.setLastContactedAt(newest);
            clientRepo.save(c);
        }
        auditService.logAction("RECOVERY_NOTE_DELETED", "Operator [" + auth.getName() + "] deleted tag: " + n.getTag());
        return ResponseEntity.ok(Map.of("ok", true));
    }
}
""")

# ---------- 2. LandService: payment auto-note ----------
LS = BE / "modules" / "land" / "service" / "LandService.java"
patch(LS, "    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;",
"    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;\n    private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;", "LS noteRepo inject")
patch(LS, """        auditService.logAction("PAYMENT_RECORDED",""",
"""        if (project.getProprietors() != null) {
            for (com.gesolutions.erp.modules.client.model.Client owner : project.getProprietors()) {
                recoveryNoteRepository.save(com.gesolutions.erp.modules.client.model.RecoveryNote.builder()
                    .client(owner).author(null).tag("payment received").tone("INFO").countsAsAttempt(false)
                    .text("Paid UGX " + amount + " on " + java.time.LocalDate.now()).build());
            }
        }
        auditService.logAction("PAYMENT_RECORDED",""", "LS payment auto-note")

# ---------- 3. Scheduler: disable promise + old cooldown loops ----------
RS = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
patch(RS, "for (RecoveryNote n : recoveryNoteRepository.findOverduePromises(LocalDate.now())) {",
"for (RecoveryNote n : java.util.Collections.<RecoveryNote>emptyList()) {", "RS disable promise loop")
patch(RS, "if (last.get().getCreatedAt().isAfter(now.minusDays(14))) continue;",
"continue; // fix78: old 14-day cooldown alert removed (lock rule changed)", "RS disable cooldown loop")

# ---------- 4. recoveryService: queue params ----------
patch(FE / "services" / "recoveryService.js", "getQueue:  () => api.get('/recovery/queue'),",
"getQueue:  (q) => api.get('/recovery/queue', { params: { queue: q || 'ALL' } }),\ngetQueues: () => api.get('/recovery/queues'),", "recoveryService queues")

# ---------- 5. RecoveryPortal: full rewrite ----------
write(FE / "pages" / "Recovery" / "RecoveryPortal.jsx",
"""import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { FiSearch, FiX, FiPhone, FiMapPin, FiClock, FiChevronDown, FiChevronUp, FiUser, FiFolderPlus, FiFilePlus, FiArchive } from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';
const TABS = [
  { key: 'ALL', label: 'ALL DUE' },
  { key: 'CONTACTED', label: 'CONTACTED' },
  { key: 'MISSED', label: 'MISSED' },
  { key: 'SITE', label: 'SITE VISIT' },
  { key: 'LOCKED', label: 'LOCKED' },
];
function fmtD(s) { if (!s) return 'NEVER'; const d = new Date(s); const p = (x) => String(x).padStart(2, '0'); return p(d.getDate()) + '/' + p(d.getMonth() + 1) + '/' + d.getFullYear(); }
function Badge({ type }) {
  const cls = type === 'Legacy Title' ? styles.badgeLegacy : type === 'New Title' ? styles.badgeTitle : styles.badgeFolder;
  const Icon = type === 'Legacy Title' ? FiArchive : type === 'New Title' ? FiFilePlus : FiFolderPlus;
  return <span className={cls}><Icon size={11} aria-hidden="true" /> {type}</span>;
}
export default function RecoveryPortal() {
  const [tab, setTab] = useState('ALL');
  const [counts, setCounts] = useState(null);
  const [stats, setStats] = useState(null);
  const [rows, setRows] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [openId, setOpenId] = useState(null);
  const [sel, setSel] = useState(null);
  const [notes, setNotes] = useState([]);
  const [picked, setPicked] = useState(null);
  const [text, setText] = useState('');
  const [coWarn, setCoWarn] = useState(null);
  const [busy, setBusy] = useState(false);
  const [toasts, setToasts] = useState([]);
  const toast = useCallback((msg, type) => { const id = Date.now() + Math.random(); setToasts((p) => [...p, { id, msg, type: type || 'info' }]); setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000); }, []);
  const load = useCallback(() => {
    setLoading(true);
    Promise.all([recoveryService.getQueues(), recoveryService.getQueue(tab), recoveryService.getTags(), recoveryService.getStats()])
      .then((r) => {
        setCounts(r[0].data || r[0]); setTags(r[2].data || r[2]); setStats(r[3].data || r[3]);
        const list = r[1].data || r[1];
        setRows(list);
        setOpenId(list.length ? list[0].id : null);
        setLoading(false);
      }).catch(() => { setLoading(false); toast('Could not load recovery queue.', 'error'); });
  }, [tab, toast]);
  useEffect(() => { load(); }, [load]);
  const open = (c) => { setSel(c); setPicked(null); setText(''); recoveryService.getNotes(c.id).then((r) => setNotes(r.data || [])); };
  const save = () => {
    if (!picked || !sel) return;
    setBusy(true);
    recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text: text })
      .then((r) => { setSel(null); toast('Logged.', 'success'); if (r && r.data && r.data.coOwnerWarning) setCoWarn(r.data.coOwnerWarning); load(); })
      .catch((e) => { setBusy(false); toast((e.response && e.response.data && e.response.data.error) || 'Save failed', 'error'); });
  };
  const term = search.toLowerCase().replace(/\\s+/g, '');
  const rowsF = rows.filter((c) => !term || [c.name, c.nin, c.phone, c.lastTag, c.entryType, c.district, c.village, ...(c.indexes || [])].join(' ').toLowerCase().replace(/\\s+/g, '').indexOf(term) >= 0);
  return (
    <div className={styles.container}>
      <header className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>Recovery Cockpit</h1>
          <p className={styles.subtitle}>Call logs only - numbers only</p>
        </div>
      </header>
      <div className={styles.countsHUD}>
        <div className={styles.countCard}><label>TODAY'S CALLS</label><strong>{stats ? stats.callsToday : '-'}</strong></div>
        <div className={styles.countCard}><label>MONTH'S CALLS</label><strong>{stats ? stats.callsMonth : '-'}</strong></div>
        <div className={styles.countCard}><label>LONGEST WAIT</label><strong>{stats ? stats.longestWait : '-'}</strong></div>
        <div className={styles.countCard}><label>MONTH'S MISS</label><strong>{stats ? stats.missMonth : '-'}</strong></div>
      </div>
      <div className={styles.controls}>
        <div className={styles.searchInner}>
          <FiSearch className={styles.searchIcon} aria-hidden="true" />
          <input type="search" className={styles.searchInput} placeholder="Search name, NIN, phone, index..." value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search recovery queue" autoComplete="off" />
          {search && (<button type="button" className={styles.searchClearBtn} onClick={() => setSearch('')} aria-label="Clear search"><FiX aria-hidden="true" /></button>)}
        </div>
      </div>
      <div className={styles.stickyTabs} role="tablist" aria-label="Recovery queues">
        {TABS.map((t) => (
          <button key={t.key} role="tab" aria-selected={tab === t.key} className={`${styles.qTab} ${tab === t.key ? styles.qTabActive : ''}`} onClick={() => setTab(t.key)}>
            {t.label} ({counts ? counts[t.key] : '-'})
          </button>
        ))}
      </div>
      {loading ? (
        <div className={styles.emptyState} role="status"><div className={styles.loadingSpinner} aria-hidden="true" /><span>SYNCING RECOVERY QUEUE...</span></div>
      ) : (
        <div className={styles.list}>
          {rowsF.map((c) => {
            const isOpen = openId === c.id;
            return (
              <article key={c.id} className={`${styles.rowCard} ${isOpen ? styles.rowOpen : ''}`}>
                <button type="button" className={styles.rowHead} onClick={() => setOpenId(isOpen ? null : c.id)} aria-expanded={isOpen}>
                  <span className={styles.callPos}>{tab} #{c.position}/{c.queueTotal}</span>
                  <span className={styles.cname}>{c.name}</span>
                  <span title={'Payment health: ' + c.payBadge} style={{ width: 8, height: 8, borderRadius: '50%', background: c.payBadge === 'GREEN' ? '#22c55e' : c.payBadge === 'YELLOW' ? '#f59e0b' : '#ef4444', boxShadow: '0 0 4px ' + (c.payBadge === 'GREEN' ? '#22c55e' : c.payBadge === 'YELLOW' ? '#f59e0b' : '#ef4444') }} />
                  <span className={c.lastTone === 'POSITIVE' ? styles.chipPos : c.lastTone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{c.lastTag || 'no contact yet'}</span>
                  {c.dayMiss > 0 && <span className={styles.dayChip}>day {c.dayMiss}/30</span>}
                  <span className={styles.reason}>{c.reason}</span>
                  {isOpen ? <FiChevronUp aria-hidden="true" /> : <FiChevronDown aria-hidden="true" />}
                </button>
                {isOpen && (
                  <div className={styles.rowBody}>
                    <Badge type={c.entryType} />
                    <span className={styles.nin}>{c.nin}</span>
                    <span className={styles.mono}>{c.phone}</span>
                    <div className={styles.projLine}>
                      {(c.projectIds || []).map((pid, i) => (<a key={pid} className={styles.projLink} href={'/folder/' + pid} onClick={(e) => e.stopPropagation()}>#{c.indexes[i] || pid}</a>))}
                    </div>
                    {c.coNames && c.coNames.length > 0 && (<div className={styles.coLine}><FiUser aria-hidden="true" /> Joint with: {c.coNames.join(', ')}</div>)}
                    {c.district && (<div className={styles.loc}><FiMapPin aria-hidden="true" /> {c.district}{c.village ? ' - ' + c.village : ''}</div>)}
                    <div className={styles.attemptLine}><FiClock aria-hidden="true" /> Good calls this 30 days: {c.calls30}/2 - Misses: {c.miss30}</div>
                    {c.unlock && (<div className={styles.lockBanner}><FiClock aria-hidden="true" /> Resting until {fmtD(c.unlock)}.</div>)}
                    <div className={styles.rowActions}>
                      <HardwareButton type="button" icon={FiPhone} onClick={() => open(c)} disabled={c.state === 'LOCKED'}>OPEN CALL LOG</HardwareButton>
                      {(c.projectIds || []).length > 0 && (<a className={styles.projLink} href={'/folder/' + c.projectIds[0]}><FiFolderPlus aria-hidden="true" /> OPEN FOLDER</a>)}
                    </div>
                  </div>
                )}
              </article>
            );
          })}
          {rowsF.length === 0 && (<div className={styles.emptyState}><span>{term ? 'NO RECORDS MATCH "' + term.toUpperCase() + '"' : 'QUEUE CLEAR'}</span></div>)}
        </div>
      )}
      <HardwareModal isOpen={!!sel} onClose={() => setSel(null)} title={sel ? 'CALL LOG - ' + sel.name : 'CALL LOG'}>
        {sel && (<>
          <div className={styles.metaRow}><Badge type={sel.entryType} /><span className={styles.nin}>{sel.nin}</span><span className={styles.mono}>{sel.phone}</span></div>
          {sel.unlock && (<div className={styles.lockBanner}><FiClock aria-hidden="true" /> Resting until {fmtD(sel.unlock)} - read only.</div>)}
          <div className={styles.tagwall}>
            <label className={styles.wallLabel}>CALL (WE SPOKE)</label>
            <div className={styles.wallRow}>
              {tags.filter((t) => t.tone === 'POSITIVE').map((t) => (
                <button type="button" key={t.tag} className={styles.tagPos + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')} disabled={!!sel.unlock} onClick={() => setPicked(t)}>{t.tag}</button>
              ))}
            </div>
            <label className={styles.wallLabel}>MISSED (NO CONTACT)</label>
            <div className={styles.wallRow}>
              {tags.filter((t) => t.tone === 'NEGATIVE').map((t) => (
                <button type="button" key={t.tag} className={styles.tagNeg + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')} disabled={!!sel.unlock} onClick={() => setPicked(t)}>{t.tag}</button>
              ))}
            </div>
          </div>
          <div className={modalStyles.modalField}>
            <label className={modalStyles.modalLabel}>NOTE (OPTIONAL)</label>
            <input type="text" className={modalStyles.modalInput} value={text} onChange={(e) => setText(e.target.value)} aria-label="Optional note" />
          </div>
          <div className={styles.histSection}>
            <label className={styles.wallLabel}>HISTORY</label>
            {notes.map((n) => (
              <div key={n.id} className={styles.histRow}>
                <span className={n.tone === 'POSITIVE' ? styles.chipPos : n.tone === 'NEGATIVE' ? styles.chipNeg : styles.chipNone}>{n.tag}</span>
                <span className={styles.histMeta}>{n.author || 'SYSTEM'} - {fmtD(n.createdAt)}</span>
                {n.text && <span className={styles.histText}>{n.text}</span>}
              </div>
            ))}
            {notes.length === 0 && (<div className={styles.trayEmpty}>NO CALLS LOGGED YET.</div>)}
          </div>
          <div className={modalStyles.modalFooter}>
            <HardwareButton type="button" onClick={save} loading={busy} icon={FiPhone} disabled={!picked || !!sel.unlock}>LOG OUTCOME</HardwareButton>
          </div>
        </>)}
      </HardwareModal>
      {coWarn && (
        <div className={styles.coWarnBanner} role="status">
          <span>{coWarn}</span>
          <button type="button" className={styles.coWarnDismiss} onClick={() => setCoWarn(null)} aria-label="Dismiss notice">&times;</button>
        </div>
      )}
      <BackToTopButton />
      {typeof document !== 'undefined' && ReactDOM.createPortal(
        <div className={styles.toastStack} role="region" aria-label="Notifications" aria-live="polite">
          {toasts.map((t) => (<div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`}>{t.msg}</div>))}
        </div>,
        document.body
      )}
    </div>
  );
}
""")

# ---------- 6. CSS: sticky tabs + row cards ----------
cssp = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
c = read(cssp)
if ".stickyTabs" not in c:
    c += """
.stickyTabs { position: sticky; top: 64px; z-index: 40; display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding: 8px 0; background: var(--bg, #f4efe8); }
.stickyTabs::-webkit-scrollbar { display: none; }
.qTab { background: rgba(26,46,48,0.75); border: 1.5px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.85); padding: 8px 14px; border-radius: 6px; font-weight: 900; font-size: 10px; letter-spacing: 1.5px; cursor: pointer; white-space: nowrap; font-family: 'Inter',sans-serif; }
.qTabActive { background: var(--orange) !important; color: #1a2e30 !important; border-color: var(--orange) !important; }
.qTab:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
.list { display: flex; flex-direction: column; gap: 8px; }
.rowCard { background: linear-gradient(160deg, #1c3335, #213E40); border: 1.5px solid rgba(255,255,255,0.12); border-radius: 10px; overflow: hidden; }
.rowOpen { border-color: var(--orange); }
.rowHead { display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; background: transparent; border: none; padding: 12px 14px; cursor: pointer; color: #fff; flex-wrap: wrap; }
.rowHead:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }
.rowBody { padding: 0 14px 14px; display: flex; flex-direction: column; gap: 8px; border-top: 1px solid rgba(255,255,255,0.08); }
.callPos { font-family: 'Space Mono',monospace; font-size: 10px; font-weight: 900; border-radius: 999px; padding: 3px 9px; border: 1px solid rgba(6,182,212,0.4); color: #67e8f9; background: rgba(6,182,212,0.12); white-space: nowrap; }
.reason { font-family: 'Space Mono',monospace; font-size: 10px; color: rgba(255,255,255,0.6); margin-left: auto; }
.dayChip { font-family: 'Space Mono',monospace; font-size: 9px; font-weight: 900; padding: 2px 8px; border-radius: 999px; border: 1px solid rgba(245,158,11,0.4); color: #fcd34d; background: rgba(245,158,11,0.12); white-space: nowrap; }
.coLine { font-size: 11px; color: rgba(255,255,255,0.7); display: flex; gap: 6px; align-items: center; }
.rowActions { display: flex; gap: 10px; align-items: center; }
.projLine { display: flex; gap: 6px; flex-wrap: wrap; }
.projLink { font-family: 'Space Mono',monospace; font-size: 11px; font-weight: 700; color: var(--orange); text-decoration: underline; display: inline-flex; gap: 4px; align-items: center; }
"""
    write(cssp, c)

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix78: final recovery engine - call/miss only, 30-day lock, auto site visit, payment auto-note, sticky tabs"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")