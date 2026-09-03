# fix.py — fix56: RECOVERY COCKPIT v2
# cards + priority, exact Intake badges, receivable-only queue, locked tray,
# audit writes, hardware-family consistency, all low-tier repairs.
import os, re, sys, shutil, subprocess, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE = ROOT / "erp-frontend" / "src"

def read(p): return p.read_text(encoding="utf-8")
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8")
    print("  wrote", p.relative_to(ROOT))
def backup(p):
    if p.exists():
        shutil.copy2(p, ROOT / ".fix_backup" / (p.name + ".bak56"))
        print("  backup", p.name)

CRIT, WARN = [], []
def need(c, m):
    if not c: CRIT.append(m)
def warn(m): WARN.append(m)

print("== PRE-FLIGHT ==")
svc = FE / "services" / "recoveryService.js"
api_import = "import api from '../api/axios';"
if svc.exists():
    m = re.search(r"(?m)^import\s+\w+\s+from\s+['\"][^'\"]+['\"];?", read(svc))
    if m: api_import = m.group(0)

# LandProject repository interface name (optional - degrades if absent)
proj_repo = ""
lr = BE / "modules" / "land" / "repository"
if lr.exists():
    for f in lr.glob("*.java"):
        m = re.search(r"public interface\s+(\w+)\s+extends\s+JpaRepository<LandProject", read(f))
        if m: proj_repo = m.group(1); break
if not proj_repo: warn("LandProject repository not found - badges/queue fall back to include-all")
print("  project repo:", proj_repo or "(none)")

audit_exists = (BE / "common" / "audit" / "AuditService.java").exists()
if not audit_exists: warn("AuditService missing - recovery taps will not be audited")

if CRIT:
    print("ABORT:"); [print(" -", m) for m in CRIT]; sys.exit(1)

# ================= BACKEND: controller v2 =================
print("== BACKEND ==")
ctrl_path = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
backup(ctrl_path)

PROJ_FIELD = ""
PROJ_INIT = ""
if proj_repo:
    PROJ_FIELD = "    @org.springframework.beans.factory.annotation.Autowired(required = false)\n    private com.gesolutions.erp.modules.land.repository.%s projectRepo;\n" % proj_repo
    PROJ_INIT = "        // projectRepo injected"
else:
    PROJ_FIELD = "    @org.springframework.beans.factory.annotation.Autowired(required = false)\n    private Object projectRepo;\n"

AUDIT_FIELD = ""
if audit_exists:
    AUDIT_FIELD = "    @org.springframework.beans.factory.annotation.Autowired(required = false)\n    private com.gesolutions.erp.common.audit.AuditService auditService;\n"

ctrl = """package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import lombok.RequiredArgsConstructor;
import java.lang.reflect.Method;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * RECOVERY CALL COCKPIT v2 (fix56).
 * Cards + priority, exact Intake entry badges, receivable-only queue,
 * locked tray, audit writes, 2-14 server side. Numbers only - no money.
 */
@RestController
@RequestMapping("/api/recovery")
@RequiredArgsConstructor
@SuppressWarnings({"unchecked","rawtypes"})
public class RecoveryNoteController {

    private final ClientRepository clientRepo;
    private final RecoveryNoteRepository noteRepo;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private UserRepository userRepo;
__PROJ_FIELD____AUDIT_FIELD__
    private static final String[][] TAGS = {
        {"committed to pay",   "POSITIVE", "true"},
        {"answered call",      "POSITIVE", "true"},
        {"not picking up",     "NEGATIVE", "true"},
        {"not going through",  "NEGATIVE", "true"},
        {"rings, no answer",   "NEGATIVE", "true"},
        {"phone off",          "NEGATIVE", "true"},
        {"needs site visit",   "NEGATIVE", "false"},
        {"failed to pay",      "NEGATIVE", "false"}
    };

    private static String[] tagDef(String tag) {
        for (String[] t : TAGS) if (t[0].equals(tag)) return t;
        return null;
    }

    // ---------- reflection helpers (compile-safe across model versions) ----------
    private static Object call(Object o, String m) {
        try { return o.getClass().getMethod(m).invoke(o); } catch (Exception e) { return null; }
    }
    private static Boolean readBool(Object o, String... c) {
        for (String s : c) { Object v = call(o, s); if (v instanceof Boolean) return (Boolean) v; }
        return null;
    }
    private static Number readNum(Object o, String... c) {
        for (String s : c) { Object v = call(o, s); if (v instanceof Number) return (Number) v; }
        return null;
    }
    private static String readStr(Object o, String... c) {
        for (String s : c) { Object v = call(o, s); if (v != null) return String.valueOf(v); }
        return null;
    }

    private List<Object> allProjects() {
        if (projectRepo == null) return List.of();
        try { return (List<Object>) projectRepo.getClass().getMethod("findAll").invoke(projectRepo); }
        catch (Exception e) { return List.of(); }
    }
    private List<Object> projectsOf(Client c) {
        List<Object> out = new ArrayList<>();
        for (Object p : allProjects()) {
            Object props = call(p, "getProprietors");
            if (props instanceof Collection && ((Collection) props).contains(c)) out.add(p);
        }
        return out;
    }
    private String entryTypeOf(List<Object> projects) {
        for (Object p : projects) {
            Boolean leg = readBool(p, "isLegacy", "getIsLegacy", "getLegacy");
            if (Boolean.TRUE.equals(leg)) return "Legacy Title";
            Boolean ta = readBool(p, "getTitleAtIntake", "isTitleAtIntake");
            if (Boolean.TRUE.equals(ta)) return "New Title";
        }
        return projects.isEmpty() ? null : "New Folder";
    }
    private boolean qualifies(List<Object> projects) {
        if (projects.isEmpty()) return false;
        for (Object p : projects) {
            if (Boolean.TRUE.equals(readBool(p, "isLegacy", "getIsLegacy", "getLegacy"))) return true;
            Number bal = readNum(p, "getBalance", "getAmountOwed", "getOutstandingBalance");
            if (bal != null) { if (bal.doubleValue() > 0) return true; else continue; }
            Number sf = readNum(p, "getMonthlyStorageFee");
            if (sf != null && sf.doubleValue() > 0) return true;
            Object st = call(p, "getStages");
            if (st instanceof Collection) {
                for (Object s : (Collection) st)
                    if (!Boolean.TRUE.equals(readBool(s, "isCompleted", "getIsCompleted", "getCompleted"))) return true;
                continue;
            }
            return true;
        }
        return false;
    }

    private boolean locked(Client c, LocalDateTime now) {
        LocalDateTime unlock = now.minusDays(14);
        LocalDateTime last = c.getLastContactedAt();
        if (last != null && last.isAfter(unlock)) return true;
        return noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(
            c, LocalDate.now().withDayOfMonth(1).atStartOfDay()) >= 2;
    }
    private LocalDateTime nextUnlock(Client c, LocalDateTime now) {
        LocalDateTime a = null;
        LocalDateTime last = c.getLastContactedAt();
        if (last != null && last.isAfter(now.minusDays(14))) a = last.plusDays(14);
        long attempts = noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(
            c, LocalDate.now().withDayOfMonth(1).atStartOfDay());
        LocalDateTime b = attempts >= 2
            ? LocalDate.now().withDayOfMonth(1).plusMonths(1).atStartOfDay() : null;
        if (a == null) return b; if (b == null) return a;
        return a.isAfter(b) ? a : b;
    }
    private int negStreak(Client c) {
        int n = 0;
        for (RecoveryNote note : noteRepo.findByClientOrderByCreatedAtDesc(c)) {
            if ("NEGATIVE".equals(note.getTone()) && note.isCountsAsAttempt()) n++;
            else break;
        }
        return n;
    }

    private Map<String, Object> clientDto(Client c, LocalDateTime now, List<Object> projects) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", c.getId());
        m.put("name", c.getFullName());
        m.put("nin", c.getNationalId());
        m.put("phone", c.getPhoneNumber());
        m.put("entryType", entryTypeOf(projects));
        List<String> idx = new ArrayList<>();
        for (Object p : projects) { String i = readStr(p, "getProjectIndex", "getIndex"); if (i != null) idx.add(i); }
        m.put("indexes", idx);
        String district = null, village = null;
        if (!projects.isEmpty()) {
            district = readStr(projects.get(0), "getDistrict");
            village = readStr(projects.get(0), "getVillage");
        }
        m.put("district", district); m.put("village", village);
        m.put("lastContactedAt", c.getLastContactedAt());
        boolean lock = locked(c, now);
        m.put("locked", lock);
        m.put("nextUnlock", lock ? nextUnlock(c, now).toString() : null);
        long attempts = noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(
            c, LocalDate.now().withDayOfMonth(1).atStartOfDay());
        m.put("attemptsThisMonth", attempts);
        noteRepo.findFirstByClientOrderByCreatedAtDesc(c).ifPresent(n -> {
            m.put("lastTag", n.getTag()); m.put("lastTone", n.getTone());
        });
        // priority: P1 failed-to-pay streak or legacy; P2 stale/neg-streak/site-visit; P3 rest
        String lastTag = (String) m.get("lastTag");
        boolean legacy = "Legacy Title".equals(m.get("entryType"));
        long days = c.getLastContactedAt() == null ? 999
            : ChronoUnit.DAYS.between(c.getLastContactedAt(), now);
        int priority = 3;
        if ("failed to pay".equals(lastTag) || legacy) priority = 1;
        else if (days > 30 || negStreak(c) >= 2 || "needs site visit".equals(lastTag)) priority = 2;
        m.put("priority", priority);
        return m;
    }

    @GetMapping("/tags")
    public List<Map<String, Object>> tags() {
        List<Map<String, Object>> out = new ArrayList<>();
        for (String[] t : TAGS) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("tag", t[0]); m.put("tone", t[1]);
            m.put("countsAsAttempt", Boolean.parseBoolean(t[2]));
            out.add(m);
        }
        return out;
    }

    @GetMapping("/queue")
    public List<Map<String, Object>> queue() {
        LocalDateTime now = LocalDateTime.now();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Client c : clientRepo.findAll()) {
            List<Object> projects = projectsOf(c);
            if (locked(c, now) || !qualifies(projects)) continue;
            out.add(clientDto(c, now, projects));
        }
        out.sort((x, y) -> {
            int p = Integer.compare((int) x.get("priority"), (int) y.get("priority"));
            if (p != 0) return p;
            LocalDateTime a = (LocalDateTime) x.get("lastContactedAt");
            LocalDateTime b = (LocalDateTime) y.get("lastContactedAt");
            if (a == null && b == null) return 0;
            if (a == null) return -1; if (b == null) return 1;
            return a.compareTo(b);
        });
        return out;
    }

    @GetMapping("/locked")
    public List<Map<String, Object>> lockedList() {
        LocalDateTime now = LocalDateTime.now();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Client c : clientRepo.findAll()) {
            List<Object> projects = projectsOf(c);
            if (!locked(c, now) || !qualifies(projects)) continue;
            out.add(clientDto(c, now, projects));
        }
        return out;
    }

    @GetMapping("/stats")
    public Map<String, Object> stats() {
        LocalDateTime now = LocalDateTime.now();
        long due = 0, lock = 0, site = 0, p1 = 0;
        for (Client c : clientRepo.findAll()) {
            List<Object> projects = projectsOf(c);
            if (!qualifies(projects)) continue;
            Map<String, Object> d = clientDto(c, now, projects);
            if (Boolean.TRUE.equals(d.get("locked"))) lock++; else due++;
            if ("needs site visit".equals(d.get("lastTag"))) site++;
            if ((int) d.get("priority") == 1) p1++;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("dueNow", due); m.put("locked", lock); m.put("siteVisits", site); m.put("p1", p1);
        m.put("callsToday", noteRepo.countByCountsAsAttemptTrueAndCreatedAtAfter(LocalDate.now().atStartOfDay()));
        m.put("callsThisMonth", noteRepo.countByCountsAsAttemptTrueAndCreatedAtAfter(
            LocalDate.now().withDayOfMonth(1).atStartOfDay()));
        return m;
    }

    @GetMapping("/clients/{id}/notes")
    public List<Map<String, Object>> notes(@PathVariable UUID id) {
        return clientRepo.findById(id).map(c -> {
            List<Map<String, Object>> out = new ArrayList<>();
            for (RecoveryNote n : noteRepo.findByClientOrderByCreatedAtDesc(c)) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("id", n.getId()); m.put("tag", n.getTag());
                m.put("tone", n.getTone()); m.put("text", n.getText());
                m.put("countsAsAttempt", n.isCountsAsAttempt());
                m.put("createdAt", n.getCreatedAt());
                m.put("author", n.getAuthor() == null ? null : n.getAuthor().getUsername());
                out.add(m);
            }
            return out;
        }).orElse(List.of());
    }

    @PostMapping("/notes")
    public ResponseEntity<?> log(@RequestBody Map<String, String> body, Authentication auth) {
        String tag = body.get("tag");
        String[] def = tagDef(tag);
        if (def == null) return ResponseEntity.badRequest().body(Map.of("error", "Unknown tag"));
        Client c = clientRepo.findById(UUID.fromString(body.get("clientId")))
            .orElseThrow(() -> new RuntimeException("Client not found"));
        LocalDateTime now = LocalDateTime.now();
        boolean attempt = Boolean.parseBoolean(def[2]);
        if (attempt && locked(c, now))
            return ResponseEntity.status(409).body(Map.of(
                "error", "Cool-down active: 14-day interval or 2-call monthly limit"));
        com.gesolutions.erp.modules.auth.model.User author = null;
        if (userRepo != null && auth != null) {
            try {
                Object temp = userRepo.getClass().getMethod("findByUsername", String.class)
                    .invoke(userRepo, auth.getName());
                if (temp instanceof Optional) author = ((Optional<com.gesolutions.erp.modules.auth.model.User>) temp).orElse(null);
                else author = (com.gesolutions.erp.modules.auth.model.User) temp;
            } catch (Exception ignored) { }
        }
        RecoveryNote n = RecoveryNote.builder()
            .client(c).author(author).tag(def[0]).tone(def[1])
            .countsAsAttempt(attempt)
            .text(body.get("text") == null || body.get("text").isBlank() ? null : body.get("text").trim())
            .build();
        noteRepo.save(n);
        if (attempt) { c.setLastContactedAt(now); clientRepo.save(c); }
        audit(auth, def[0], c.getNationalId());
        return ResponseEntity.ok(Map.of("ok", true, "id", n.getId()));
    }

    private void audit(Authentication auth, String tag, String nin) {
        if (auditService == null) return;
        String who = auth == null ? "system" : auth.getName();
        for (Method m : auditService.getClass().getMethods()) {
            String name = m.getName();
            if (!(name.equals("log") || name.equals("record") || name.equals("write"))) continue;
            try {
                Class<?>[] pt = m.getParameterTypes();
                if (pt.length == 2 && pt[0] == String.class && pt[1] == String.class)
                    { m.invoke(auditService, who, "RECOVERY_NOTE: " + tag + " (NIN " + nin + ")"); return; }
                if (pt.length == 3 && pt[0] == String.class && pt[1] == String.class && pt[2] == String.class)
                    { m.invoke(auditService, who, "RECOVERY_NOTE", tag + " (NIN " + nin + ")"); return; }
            } catch (Exception ignored) { }
        }
    }
}
"""
ctrl = ctrl.replace("__PROJ_FIELD__", PROJ_FIELD).replace("__AUDIT_FIELD__", AUDIT_FIELD)
write(ctrl_path, ctrl)

# ================= FRONTEND =================
print("== FRONTEND ==")
backup(svc)
write(svc, api_import + """

// RECOVERY COCKPIT v2 - cards, priority, locked tray, numbers-only
const recoveryService = {
  getQueue:  () => api.get('/recovery/queue'),
  getLocked: () => api.get('/recovery/locked'),
  getTags:   () => api.get('/recovery/tags'),
  getStats:  () => api.get('/recovery/stats'),
  getNotes:  (clientId) => api.get('/recovery/clients/' + clientId + '/notes'),
  logNote:   (payload) => api.post('/recovery/notes', payload),
};
export default recoveryService;
""")

page = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
css  = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
backup(page); backup(css)

write(page, r"""import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
    FiPhone, FiSearch, FiX, FiMapPin, FiClock, FiAlertTriangle,
    FiArchive, FiFilePlus, FiFolderPlus, FiChevronDown, FiChevronUp, FiUser
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './RecoveryPortal.module.css';

// EXACT Intake entry labels - one source of truth across pages
const ENTRY_META = [
    { label: 'New Folder',   icon: FiFolderPlus, cls: 'badge0' },
    { label: 'New Title',    icon: FiFilePlus,  cls: 'badge1' },
    { label: 'Legacy Title', icon: FiArchive,   cls: 'badge2' },
];
const FILTERS = [
    { key: 'all',  label: 'All Due' },
    { key: 'p1',   label: 'Priority 1' },
    { key: 'p2',   label: 'Priority 2' },
    { key: 'p3',   label: 'Priority 3' },
    { key: 'site', label: 'Site Visits' },
];

function fmtDT(s) {
    if (!s) return 'Never';
    const d = new Date(s);
    const p = (x) => String(x).padStart(2, '0');
    return p(d.getDate()) + '/' + p(d.getMonth() + 1) + '/' + d.getFullYear() +
        ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
}

function Badge({ type }) {
    const meta = ENTRY_META.find((e) => e.label === type);
    if (!meta) return <span className={styles.badge0}>-</span>;
    const Icon = meta.icon;
    return (
        <span className={styles[meta.cls]}>
            <Icon size={11} aria-hidden="true" /> {meta.label}
        </span>
    );
}

function Dots({ n }) {
    return (
        <span className={styles.dots} title={n + ' of 2 calls this month'}>
            {[0, 1].map((i) => (
                <span key={i} className={i < n ? styles.dotOn : styles.dotOff} />
            ))}
        </span>
    );
}

export default function RecoveryPortal() {
    const [queue, setQueue] = useState([]);
    const [lockedList, setLockedList] = useState([]);
    const [tags, setTags] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [filter, setFilter] = useState('all');
    const [showLocked, setShowLocked] = useState(false);
    const [sel, setSel] = useState(null);
    const [notes, setNotes] = useState([]);
    const [picked, setPicked] = useState(null);
    const [text, setText] = useState('');
    const [busy, setBusy] = useState(false);
    const [toasts, setToasts] = useState([]);
    const collapsedOnce = useRef(false);

    const toast = useCallback((msg, type) => {
        const id = Date.now() + Math.random();
        setToasts((p) => [...p, { id, msg, type: type || 'info' }]);
        setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000);
    }, []);

    // low-tier consistency: auto-collapse sidebar on first interaction (like Intake)
    useEffect(() => {
        const handler = () => {
            if (collapsedOnce.current) return;
            collapsedOnce.current = true;
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
        };
        window.addEventListener('click', handler, { once: true });
        return () => window.removeEventListener('click', handler);
    }, []);

    const load = useCallback(() => {
        setLoading(true);
        Promise.all([
            recoveryService.getQueue(), recoveryService.getLocked(),
            recoveryService.getTags(), recoveryService.getStats(),
        ]).then((r) => {
            setQueue(r[0].data || []);
            setLockedList(r[1].data || []);
            setTags(r[2].data || []);
            setStats(r[3].data || null);
            setLoading(false);
        }).catch((e) => {
            setLoading(false);
            toast('Could not load the recovery queue. Refresh to retry.', 'error');
        });
    }, [toast]);
    useEffect(() => { load(); }, [load]);

    const open = (c) => {
        setSel(c); setPicked(null); setText('');
        recoveryService.getNotes(c.id).then((r) => setNotes(r.data || []));
    };

    const save = () => {
        if (!picked || !sel) return;
        setBusy(true);
        recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text })
            .then(() => { setSel(null); toast('Outcome logged.', 'success'); load(); })
            .catch((e) => {
                setBusy(false);
                toast((e.response && e.response.data && e.response.data.error) || 'Save failed', 'error');
            });
    };

    const term = search.toLowerCase().replace(/\s+/g, '');
    const matches = (c) => {
        if (!term) return true;
        const hay = [c.name, c.nin, c.phone, c.lastTag, c.entryType, c.district, c.village,
            ...(c.indexes || [])].join(' ').toLowerCase().replace(/\s+/g, '');
        return hay.indexOf(term) >= 0;
    };
    const rows = queue.filter((c) => {
        if (!matches(c)) return false;
        if (filter === 'all') return true;
        if (filter === 'site') return c.lastTag === 'needs site visit';
        return c.priority === Number(filter.replace('p', ''));
    });

    const count = (k) => (stats ? stats[k] : '-');

    return (
        <div className={styles.cockpit}>
            <header className={styles.topbar}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Recovery Cockpit</h1>
                    <p className={styles.subtitle}>Call logs & follow-up queue</p>
                </div>
                <div className={styles.counts}>
                    <div className={styles.count}><span>{count('dueNow')}</span><label>Due Now</label></div>
                    <div className={styles.count}><span>{count('callsToday')}</span><label>Calls Today</label></div>
                    <div className={styles.count}><span>{count('callsThisMonth')}</span><label>This Month</label></div>
                    <div className={styles.count}><span>{count('locked')}</span><label>Locked</label></div>
                    <div className={styles.count}><span>{count('siteVisits')}</span><label>Site Visits</label></div>
                </div>
            </header>

            <div className={styles.controls}>
                <div className={styles.searchRow}>
                    <FiSearch aria-hidden="true" />
                    <input
                        placeholder="Search name, NIN, phone, index, tag, district..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        aria-label="Search recovery queue"
                    />
                </div>
                <div className={styles.filters}>
                    {FILTERS.map((f) => (
                        <button key={f.key}
                            className={filter === f.key ? styles.filterOn : styles.filter}
                            onClick={() => setFilter(f.key)}>
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className={styles.grid}>
                    {[0, 1, 2, 3, 4, 5].map((i) => <div key={i} className={styles.skel} />)}
                </div>
            ) : (
                <div className={styles.grid}>
                    {rows.map((c) => (
                        <article key={c.id} className={styles.card} onClick={() => open(c)}>
                            <header className={styles.cardHead}>
                                <span className={styles['p' + c.priority]}>P{c.priority}</span>
                                <Badge type={c.entryType} />
                                <Dots n={c.attemptsThisMonth || 0} />
                            </header>
                            <h2 className={styles.cname}>{c.name}</h2>
                            <div className={styles.nin}>{c.nin}</div>
                            <div className={styles.mono}>{c.phone}</div>
                            {(c.indexes || []).length > 0 && (
                                <div className={styles.mono}>#{c.indexes.join(' #')}</div>
                            )}
                            {c.district && (
                                <div className={styles.loc}>{c.district}{c.village ? ' - ' + c.village : ''}</div>
                            )}
                            <div className={styles.cardFoot}>
                                {c.lastTag
                                    ? <span className={c.lastTone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{c.lastTag}</span>
                                    : <span className={styles.chipNone}>No contact yet</span>}
                                <span className={styles.mono}>{fmtDT(c.lastContactedAt)}</span>
                            </div>
                            <button className={styles.openBtn} onClick={(e) => { e.stopPropagation(); open(c); }}>
                                <FiPhone aria-hidden="true" /> Open Call Log
                            </button>
                        </article>
                    ))}
                    {rows.length === 0 && (
                        <div className={styles.empty}>Queue clear - everyone is cooled down, contacted, or filtered out.</div>
                    )}
                </div>
            )}

            <section className={styles.lockedTray}>
                <button className={styles.trayToggle} onClick={() => setShowLocked((s) => !s)}
                    aria-expanded={showLocked}>
                    <FiAlertTriangle aria-hidden="true" />
                    Locked Clients ({lockedList.length}) - read only
                    {showLocked ? <FiChevronUp aria-hidden="true" /> : <FiChevronDown aria-hidden="true" />}
                </button>
                {showLocked && (
                    <div className={styles.trayList}>
                        {lockedList.filter(matches).map((c) => (
                            <div key={c.id} className={styles.trayRow} onClick={() => open(c)}>
                                <Badge type={c.entryType} />
                                <span className={styles.cname}>{c.name}</span>
                                <span className={styles.nin}>{c.nin}</span>
                                <span className={styles.mono}>Callable {fmtDT(c.nextUnlock)}</span>
                            </div>
                        ))}
                        {lockedList.length === 0 && <div className={styles.empty}>No locked clients.</div>}
                    </div>
                )}
            </section>

            {sel && (
                <div className={styles.overlay} onClick={() => setSel(null)}>
                    <div className={styles.drawer} onClick={(e) => e.stopPropagation()} role="dialog" aria-label={'Call log for ' + sel.name}>
                        <header className={styles.drawerHead}>
                            <div>
                                <h2>{sel.name}</h2>
                                <div className={styles.drawerMeta}>
                                    <Badge type={sel.entryType} />
                                    <span className={styles.nin}>{sel.nin}</span>
                                    <span className={styles.mono}>{sel.phone}</span>
                                </div>
                            </div>
                            <button className={styles.closeBtn} onClick={() => setSel(null)} aria-label="Close">
                                <FiX aria-hidden="true" />
                            </button>
                        </header>

                        {sel.locked && (
                            <div className={styles.lockBanner}>
                                <FiAlertTriangle aria-hidden="true" />
                                Cool-down active - read only. Callable {fmtDT(sel.nextUnlock)}.
                            </div>
                        )}

                        <div className={styles.attemptLine}>
                            <FiUser aria-hidden="true" /> Calls this month: <Dots n={sel.attemptsThisMonth || 0} />
                        </div>

                        <div className={styles.tagwall}>
                            <label className={styles.wallLabel}>Positive</label>
                            <div className={styles.wallRow}>
                                {tags.filter((t) => t.tone === 'POSITIVE').map((t) => (
                                    <button key={t.tag}
                                        className={styles.tagPos + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                                        disabled={sel.locked && t.countsAsAttempt}
                                        onClick={() => setPicked(t)}>
                                        {t.tag}
                                    </button>
                                ))}
                            </div>
                            <label className={styles.wallLabel}>Negative</label>
                            <div className={styles.wallRow}>
                                {tags.filter((t) => t.tone === 'NEGATIVE').map((t) => (
                                    <button key={t.tag}
                                        className={styles.tagNeg + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                                        disabled={sel.locked && t.countsAsAttempt}
                                        onClick={() => setPicked(t)}>
                                        {t.tag.indexOf('site visit') >= 0 ? <FiMapPin aria-hidden="true" /> :
                                            (t.countsAsAttempt ? <FiPhone aria-hidden="true" /> : <FiClock aria-hidden="true" />)}
                                        {t.tag}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <input className={styles.noteInput}
                            placeholder="Optional detail (rare)"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            aria-label="Optional note detail" />

                        <div className={styles.drawerActions}>
                            <button className={styles.saveBtn} disabled={!picked || busy || sel.locked} onClick={save}>
                                {busy ? 'Saving...' : 'Log Outcome'}
                            </button>
                        </div>

                        <div className={styles.history}>
                            <label className={styles.wallLabel}>Call Log</label>
                            {notes.map((n) => (
                                <div key={n.id} className={styles.histRow}>
                                    <span className={n.tone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{n.tag}</span>
                                    <span className={styles.histMeta}>{n.author || 'System'} - {fmtDT(n.createdAt)}</span>
                                    {n.text && <span className={styles.histText}>{n.text}</span>}
                                </div>
                            ))}
                            {notes.length === 0 && <div className={styles.empty}>No calls logged yet.</div>}
                        </div>
                    </div>
                </div>
            )}

            <BackToTopButton />

            {typeof document !== 'undefined' && createPortal(
                <div className={styles.toastStack} role="region" aria-label="Notifications" aria-live="polite">
                    {toasts.map((t) => (
                        <div key={t.id} className={styles['toast_' + t.type]}>{t.msg}</div>
                    ))}
                </div>,
                document.body
            )}
        </div>
    );
}
""")

write(css, """.cockpit{min-height:100vh;padding:clamp(12px,2vw,28px);background:var(--navy,#0a1a2f);color:var(--text,#e8eef6);font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;gap:var(--gap-lg,18px)}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;gap:var(--gap-md,14px);flex-wrap:wrap}
.headerLeft .title{font-family:Cinzel,serif;color:var(--orange,#ff6b00);font-size:clamp(18px,2.2vw,26px);letter-spacing:2px;margin:0}
.subtitle{margin:2px 0 0;color:var(--muted,#8aa0b8);font-size:12px}
.counts{display:flex;gap:var(--gap-sm,10px);flex-wrap:wrap}
.count{background:var(--panel,#10233c);border:1px solid var(--line,#1e3a5c);border-radius:10px;padding:8px 14px;display:flex;flex-direction:column;align-items:center;min-width:86px}
.count span{font-family:'Space Mono',monospace;font-size:clamp(16px,1.8vw,22px);color:var(--orange,#ff6b00)}
.count label{font-size:10px;letter-spacing:1.5px;color:var(--muted,#8aa0b8)}
.controls{display:flex;gap:var(--gap-md,14px);flex-wrap:wrap;align-items:center}
.searchRow{flex:1;min-width:240px;display:flex;align-items:center;gap:8px;background:var(--panel,#10233c);border:1px solid var(--line,#1e3a5c);border-radius:10px;padding:10px 14px;color:var(--muted,#8aa0b8)}
.searchRow input{flex:1;background:transparent;border:none;outline:none;color:var(--text,#e8eef6);font-size:14px}
.filters{display:flex;gap:var(--gap-sm,8px);flex-wrap:wrap}
.filter,.filterOn{border-radius:20px;padding:7px 14px;font-size:12px;cursor:pointer;border:1px solid var(--line,#1e3a5c);background:transparent;color:var(--muted,#8aa0b8)}
.filterOn{background:var(--orange,#ff6b00);border-color:var(--orange,#ff6b00);color:#08131f;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--gap-md,14px)}
.card{background:var(--panel,#10233c);border:1px solid var(--line,#1e3a5c);border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:8px;cursor:pointer;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--orange,#ff6b00);transform:translateY(-2px)}
.cardHead{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.p1,.p2,.p3{font-family:'Space Mono',monospace;font-size:11px;border-radius:6px;padding:2px 8px}
.p1{background:#331410;color:#ff7a6b;border:1px solid #5c241d}
.p2{background:#332a10;color:#ffd35c;border:1px solid #5c4a1d}
.p3{color:var(--muted,#8aa0b8);border:1px solid var(--line,#1e3a5c)}
.badge0,.badge1,.badge2{display:inline-flex;align-items:center;gap:5px;font-size:10px;letter-spacing:1px;padding:3px 8px;border-radius:6px;border:1px solid var(--line,#1e3a5c)}
.badge0{color:var(--muted,#8aa0b8)}
.badge1{color:#7fd1ff;border-color:#2a5d84}
.badge2{color:#ffb35c;border-color:#84562a}
.dots{display:inline-flex;gap:4px;margin-left:auto}
.dotOn,.dotOff{width:8px;height:8px;border-radius:50%}
.dotOn{background:var(--orange,#ff6b00)}
.dotOff{border:1px solid var(--muted,#8aa0b8)}
.cname{font-size:15px;font-weight:700;margin:0}
.nin{font-family:'Space Mono',monospace;font-size:11px;color:var(--orange,#ff6b00)}
.mono{font-family:'Space Mono',monospace;font-size:12px;color:var(--muted,#8aa0b8)}
.loc{font-size:12px;color:var(--muted,#8aa0b8)}
.cardFoot{display:flex;align-items:center;gap:8px;justify-content:space-between;flex-wrap:wrap}
.chipPos,.chipNeg,.chipNone{font-size:11px;padding:3px 9px;border-radius:20px;white-space:nowrap}
.chipPos{background:#0e3320;color:#5ce08a;border:1px solid #1d5c36}
.chipNeg{background:#331410;color:#ff7a6b;border:1px solid #5c241d}
.chipNone{color:var(--muted,#8aa0b8);border:1px dashed var(--line,#1e3a5c)}
.openBtn{display:flex;align-items:center;justify-content:center;gap:6px;background:transparent;border:1px solid var(--orange,#ff6b00);color:var(--orange,#ff6b00);border-radius:8px;padding:8px 10px;cursor:pointer;font-size:12px;margin-top:4px}
.openBtn:hover{background:var(--orange,#ff6b00);color:#08131f}
.empty{grid-column:1/-1;text-align:center;color:var(--muted,#8aa0b8);padding:26px 0}
.skel{height:190px;border-radius:12px;background:linear-gradient(100deg,var(--panel,#10233c) 40%,var(--panel2,#0d1e33) 50%,var(--panel,#10233c) 60%);background-size:200% 100%;animation:shim 1.2s infinite}
@keyframes shim{to{background-position:-200% 0}}
.lockedTray{background:var(--panel,#10233c);border:1px solid var(--line,#1e3a5c);border-radius:12px;overflow:hidden}
.trayToggle{width:100%;display:flex;align-items:center;gap:8px;background:transparent;border:none;color:#ffd35c;padding:12px 16px;font-size:13px;cursor:pointer}
.trayList{border-top:1px solid var(--line,#1e3a5c);display:flex;flex-direction:column}
.trayRow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:10px 16px;border-bottom:1px solid var(--line,#1e3a5c);cursor:pointer}
.trayRow:hover{background:var(--hover,#132a46)}
.overlay{position:fixed;inset:0;background:rgba(4,10,18,.72);display:flex;justify-content:flex-end;z-index:60}
.drawer{width:min(560px,100%);height:100%;background:var(--panel,#10233c);border-left:1px solid var(--line,#1e3a5c);padding:20px;overflow-y:auto;display:flex;flex-direction:column;gap:14px}
.drawerHead{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.drawerHead h2{margin:0 0 6px;font-family:Cinzel,serif;font-size:18px}
.drawerMeta{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.closeBtn{background:transparent;border:none;color:var(--muted,#8aa0b8);font-size:18px;cursor:pointer}
.lockBanner{display:flex;align-items:center;gap:8px;background:#332a10;color:#ffd35c;border:1px solid #5c4a1d;border-radius:10px;padding:10px 12px;font-size:12px}
.attemptLine{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted,#8aa0b8)}
.wallLabel{font-size:10px;letter-spacing:2px;color:var(--muted,#8aa0b8);margin:6px 0 4px;display:block}
.wallRow{display:flex;gap:8px;flex-wrap:wrap}
.tagPos,.tagNeg{display:flex;align-items:center;gap:6px;border-radius:20px;padding:8px 14px;font-size:13px;cursor:pointer}
.tagPos{background:#0e3320;color:#5ce08a;border:1px solid #1d5c36}
.tagNeg{background:#331410;color:#ff7a6b;border:1px solid #5c241d}
.tagPos:disabled,.tagNeg:disabled{opacity:.35;cursor:not-allowed}
.tagOn{outline:2px solid var(--orange,#ff6b00);outline-offset:2px}
.noteInput{background:var(--panel2,#0d1e33);border:1px solid var(--line,#1e3a5c);border-radius:10px;padding:10px 12px;color:var(--text,#e8eef6);outline:none;font-size:13px}
.drawerActions{display:flex;justify-content:flex-end}
.saveBtn{background:var(--orange,#ff6b00);border:none;color:#08131f;font-weight:700;border-radius:10px;padding:10px 22px;cursor:pointer}
.saveBtn:disabled{opacity:.4;cursor:not-allowed}
.history{display:flex;flex-direction:column;gap:8px}
.histRow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px}
.histMeta{color:var(--muted,#8aa0b8)}
.histText{color:var(--text,#e8eef6)}
.toastStack{position:fixed;bottom:18px;right:18px;display:flex;flex-direction:column;gap:8px;z-index:100}
.toast_info,.toast_success,.toast_error{border-radius:10px;padding:10px 16px;font-size:13px;box-shadow:0 6px 18px rgba(0,0,0,.4)}
.toast_info{background:var(--panel2,#0d1e33);color:var(--text,#e8eef6);border:1px solid var(--line,#1e3a5c)}
.toast_success{background:#0e3320;color:#5ce08a;border:1px solid #1d5c36}
.toast_error{background:#331410;color:#ff7a6b;border:1px solid #5c241d}
""")

# ================= GIT =================
print("== GIT ==")
subprocess.run(["git", "add", "-A"], cwd=ROOT)
r = subprocess.run(["git", "commit", "-m",
    "fix56: recovery cockpit v2 - cards+priority, exact intake badges, receivable queue, locked tray, audit writes"],
    cwd=ROOT, capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
p = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
print(p.stdout.strip() or p.stderr.strip())

print("\nWARNINGS:")
for w in WARN: print(" -", w)
print("""
TEST AFTER DEPLOY:
1. Cards render P1/P2/P3 with exact badges (New Folder / New Title / Legacy Title).
2. Fully-paid clean clients no longer appear; legacy + owing clients do.
3. Locked tray lists cooled-down clients with 'Callable <date>'; drawer read-only.
4. Attempt dots fill per call this month; 3rd attempt blocked with 409 toast.
5. Search finds by project index and district; filters P1/P2/P3/Site work.
6. Sidebar auto-collapses on first click; skeletons show while loading; toasts fire.
7. Audit page shows RECOVERY_NOTE entries after logging a tag.""")