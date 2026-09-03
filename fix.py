# fix.py — fix48: RECOVERY CALL COCKPIT + NOTES TAG SUBSYSTEM v1
# Self-discovering guarded batch. Reads live code, adapts, backs up, aborts safely.
import os, re, sys, shutil, subprocess, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE   = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE   = ROOT / "erp-frontend" / "src"

def read(p):  return p.read_text(encoding="utf-8")
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")
    print("  wrote", p.relative_to(ROOT))
def backup(p):
    if p.exists():
        shutil.copy2(p, ROOT / ".fix_backup" / p.name)
        print("  backup", p.name)

CRITICAL, WARN = [], []
def need(cond, msg):
    if not cond: CRITICAL.append(msg)
def warn(msg): WARN.append(msg)

print("== PRE-FLIGHT DISCOVERY ==")
# 1) axios api import line (copied verbatim from an existing service in same folder)
api_import = None
svc_dir = FE / "services"
for svc in ["folderPortalService.js", "landService.js"] + sorted(f.name for f in svc_dir.glob("*.js")):
    p = svc_dir / svc
    if p.exists():
        m = re.search(r"(?m)^import\s+\w+\s+from\s+['\"][^'\"]*(api|axios)[^'\"]*['\"];?", read(p))
        if m: api_import = m.group(0); break
need(api_import, "axios api import line not discoverable from services/")
print("  api_import:", api_import)

# 2) Client accessors
client_java = BE / "modules" / "client" / "model" / "Client.java"
need(client_java.exists(), "Client.java missing")
csrc = read(client_java) if client_java.exists() else ""
def cfield(pats):
    for pat in pats:
        m = re.search(r"private\s+[\w<>,\s]+?\s(" + pat + r")\s*;", csrc)
        if m: return m.group(1)
    return None
name_f  = cfield(["fullName", "clientName", "name"])
nin_f   = cfield(["nationalId", "nin"])
phone_f = cfield(["phoneNumber", "phone"])
last_f  = cfield(["lastContactedAt", "lastContacted"])
need(name_f and nin_f and last_f, "Client name/nin/lastContactedAt fields not found")
def getter(f): return "get" + f[0].upper() + f[1:]
print("  client fields:", name_f, nin_f, phone_f, last_f)

# 3) repositories
crepo = urepo = None
crdir = BE / "modules" / "client" / "repository"
if crdir.exists():
    for f in crdir.glob("*.java"):
        m = re.search(r"public interface\s+(\w+)\s+extends\s+JpaRepository<Client,", read(f))
        if m: crepo = m.group(1)
need(crepo, "Client repository interface not found")
urdir = BE / "modules" / "auth" / "repository"
if urdir.exists():
    for f in urdir.glob("*.java"):
        m = re.search(r"public interface\s+(\w+)\s+extends\s+JpaRepository<User,", read(f))
        if m: urepo = m.group(1)
if not urepo: warn("User repository not found - notes will store author as null")
print("  repos:", crepo, urepo)

# 4) Intake entry-type labels (for badge consistency)
labels = None
ip = FE / "pages" / "Intake" / "IntakePage.jsx"
if ip.exists():
    m = re.search(r"(?:ENTRY|INTAKE|CLIENT)[_A-Z]*TYPES?\s*=\s*\[([^\]]*)\]", read(ip))
    if m: labels = re.findall(r"['\"]([^'\"]+)['\"]", m.group(1))
if not labels:
    lp = BE / "modules" / "land" / "model" / "LandProject.java"
    if lp.exists():
        m = re.search(r"enum\s+\w+\s*\{([^}]*)\}", read(lp))
        if m: labels = [x.strip() for x in m.group(1).split(",") if x.strip()]
if not labels:
    labels = ["NEW", "LEGACY", "BACKLOG"]; warn("Intake labels not discovered - using defaults")
print("  intake labels:", labels)

if CRITICAL:
    print("\nABORT - critical discoveries missing:")
    for m in CRITICAL: print("  -", m)
    sys.exit(1)

# ================= BACKEND =================
print("== BACKEND ==")
note_java = BE / "modules" / "client" / "model" / "RecoveryNote.java"
write(note_java, """package com.gesolutions.erp.modules.client.model;

import com.gesolutions.erp.modules.auth.model.User;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * NOTES TAG SUBSYSTEM v1 - one row per operator tap on the Recovery cockpit.
 * tone: POSITIVE | NEGATIVE. countsAsAttempt tags feed the 2-14 handbrake.
 */
@Entity
@Table(name = "recovery_notes", indexes = {
    @Index(name = "idx_rnote_client",  columnList = "client_id"),
    @Index(name = "idx_rnote_attempt", columnList = "counts_as_attempt"),
    @Index(name = "idx_rnote_created", columnList = "created_at")
})
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class RecoveryNote {

    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "client_id")
    private Client client;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "author_id")
    private User author;

    @Column(nullable = false, length = 60)
    private String tag;

    @Column(nullable = false, length = 10)
    private String tone;

    @Column(name = "counts_as_attempt", nullable = false)
    private boolean countsAsAttempt;

    @Column(length = 500)
    private String text;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    void onCreate() { if (createdAt == null) createdAt = LocalDateTime.now(); }
}
""")

repo_java = BE / "modules" / "client" / "repository" / "RecoveryNoteRepository.java"
write(repo_java, """package com.gesolutions.erp.modules.client.repository;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface RecoveryNoteRepository extends JpaRepository<RecoveryNote, UUID> {
    List<RecoveryNote> findByClientOrderByCreatedAtDesc(Client client);
    Optional<RecoveryNote> findFirstByClientOrderByCreatedAtDesc(Client client);
    long countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(Client client, LocalDateTime after);
    long countByCountsAsAttemptTrueAndCreatedAtAfter(LocalDateTime after);
    long countByCountsAsAttemptTrueAndCreatedAtBetween(LocalDateTime a, LocalDateTime b);
}
""")

# ---- controller (reflection for entryType so it compiles on any model version) ----
user_import = ""
user_field  = ""
author_resolve = "        com.gesolutions.erp.modules.auth.model.User author = null;"
if urepo:
    user_import = "import com.gesolutions.erp.modules.auth.repository.%s;\n" % urepo
    user_field  = "    @org.springframework.beans.factory.annotation.Autowired(required = false)\n    private %s userRepo;\n" % urepo
    author_resolve = """        com.gesolutions.erp.modules.auth.model.User author = null;
        if (auth != null && userRepo != null) {
            author = userRepo.findByUsername(auth.getName()).orElse(null);
        }"""
    # findByUsername may not exist; guard with reflection-free fallback
    author_resolve = """        com.gesolutions.erp.modules.auth.model.User author = null;
        if (userRepo != null && auth != null) {
            try {
                author = (com.gesolutions.erp.modules.auth.model.User)
                    userRepo.getClass().getMethod("findByUsername", String.class)
                    .invoke(userRepo, auth.getName());
                if (author instanceof java.util.Optional) author = ((java.util.Optional<com.gesolutions.erp.modules.auth.model.User>) author).orElse(null);
            } catch (Exception ignored) { }
        }"""

ctrl = """package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.__CREPO__;
import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;
__USER_IMPORT__import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import lombok.RequiredArgsConstructor;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.*;

/**
 * RECOVERY CALL COCKPIT - numbers-only (no money), queue-first, tag-driven.
 * 2-14 rule enforced SERVER SIDE on attempt tags.
 */
@RestController
@RequestMapping("/api/recovery")
@RequiredArgsConstructor
public class RecoveryNoteController {

    private final __CREPO__ clientRepo;
    private final RecoveryNoteRepository noteRepo;
__USER_FIELD__
    // THE 8 LOCKED TAGS: label | tone | countsAsAttempt
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

    private boolean locked(Client c, LocalDateTime now) {
        LocalDateTime unlock = now.minusDays(14);
        LocalDateTime last = c.__GET_LAST__();
        if (last != null && last.isAfter(unlock)) return true;
        long attempts = noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(
            c, LocalDate.now().withDayOfMonth(1).atStartOfDay());
        return attempts >= 2;
    }

    // reflection: entryType badge without compile-time coupling to model version
    private String entryType(Client c) {
        for (String g : new String[]{"getEntryType","getIntakeType","getClientType","getPreset"}) {
            try {
                Object v = c.getClass().getMethod(g).invoke(c);
                if (v != null) return String.valueOf(v);
            } catch (Exception ignored) { }
        }
        return null;
    }

    private Map<String, Object> clientDto(Client c, LocalDateTime now) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", c.getId());
        m.put("name", c.__GET_NAME__());
        m.put("nin", c.__GET_NIN__());
        m.put("phone", c.__GET_PHONE__());
        m.put("entryType", entryType(c));
        m.put("lastContactedAt", c.__GET_LAST__());
        m.put("locked", locked(c, now));
        noteRepo.findFirstByClientOrderByCreatedAtDesc(c).ifPresent(n -> {
            m.put("lastTag", n.getTag());
            m.put("lastTone", n.getTone());
        });
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
        List<Client> due = new ArrayList<>();
        for (Client c : clientRepo.findAll()) if (!locked(c, now)) due.add(c);
        due.sort(Comparator.comparing(Client::__GET_LAST__,
            Comparator.nullsFirst(Comparator.naturalOrder())));
        List<Map<String, Object>> out = new ArrayList<>();
        for (Client c : due) out.add(clientDto(c, now));
        return out;
    }

    @GetMapping("/stats")
    public Map<String, Object> stats() {
        LocalDateTime now = LocalDateTime.now();
        long due = 0, lockedCount = 0, siteVisits = 0;
        for (Client c : clientRepo.findAll()) {
            if (locked(c, now)) lockedCount++; else due++;
            var last = noteRepo.findFirstByClientOrderByCreatedAtDesc(c);
            if (last.isPresent() && "needs site visit".equals(last.get().getTag())) siteVisits++;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("dueNow", due);
        m.put("callsToday", noteRepo.countByCountsAsAttemptTrueAndCreatedAtAfter(
            LocalDate.now().atStartOfDay()));
        m.put("callsThisMonth", noteRepo.countByCountsAsAttemptTrueAndCreatedAtAfter(
            LocalDate.now().withDayOfMonth(1).atStartOfDay()));
        m.put("locked", lockedCount);
        m.put("siteVisits", siteVisits);
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
        if (def == null) return ResponseEntity.badRequest().body(Map.of("error", "unknown tag"));
        UUID clientId = UUID.fromString(body.get("clientId"));
        Client c = clientRepo.findById(clientId)
            .orElseThrow(() -> new RuntimeException("client not found"));
        LocalDateTime now = LocalDateTime.now();
        boolean attempt = Boolean.parseBoolean(def[2]);
        if (attempt && locked(c, now))
            return ResponseEntity.status(409).body(Map.of(
                "error", "cool-down active: 14-day interval or 2-call monthly limit"));
__AUTHOR_RESOLVE__
        RecoveryNote n = RecoveryNote.builder()
            .client(c).author(author).tag(def[0]).tone(def[1])
            .countsAsAttempt(attempt)
            .text(body.get("text") == null || body.get("text").isBlank() ? null : body.get("text").trim())
            .build();
        noteRepo.save(n);
        if (attempt) { c.__SET_LAST__(now); clientRepo.save(c); }
        return ResponseEntity.ok(Map.of("ok", true, "id", n.getId()));
    }
}
"""
ctrl = (ctrl
    .replace("__CREPO__", crepo)
    .replace("__USER_IMPORT__", user_import)
    .replace("__USER_FIELD__", user_field)
    .replace("__AUTHOR_RESOLVE__", author_resolve)
    .replace("__GET_NAME__", getter(name_f))
    .replace("__GET_NIN__", getter(nin_f))
    .replace("__GET_PHONE__", getter(phone_f) if phone_f else "getPhoneNumber")
    .replace("__GET_LAST__", getter(last_f))
    .replace("__SET_LAST__", "set" + last_f[0].upper() + last_f[1:]))
ctrl_path = BE / "modules" / "client" / "controller" / "RecoveryNoteController.java"
write(ctrl_path, ctrl)

# ================= FRONTEND =================
print("== FRONTEND ==")
svc = FE / "services" / "recoveryService.js"
write(svc, (api_import or "import api from './api';") + """

// RECOVERY COCKPIT service - numbers-only, tag-driven
const recoveryService = {
  getQueue: () => api.get('/recovery/queue'),
  getTags:  () => api.get('/recovery/tags'),
  getStats: () => api.get('/recovery/stats'),
  getNotes: (clientId) => api.get('/recovery/clients/' + clientId + '/notes'),
  logNote:  (payload) => api.post('/recovery/notes', payload),
};
export default recoveryService;
""")

page = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
css  = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
backup(page); backup(css)

write(page, """import React, { useState, useEffect, useCallback } from 'react';
import { FiPhone, FiSearch, FiX, FiMapPin, FiClock, FiAlertTriangle } from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import { useAuth } from '../../hooks/useAuth';
import styles from './RecoveryPortal.module.css';

// entry-type labels kept identical to Intake (discovered at fix time)
const ENTRY_TYPES = __LABELS__;

const ENTRY_TONE = {};
ENTRY_TYPES.forEach(function (t, i) { ENTRY_TONE[String(t).toUpperCase()] = i; });

function fmtWhen(s) {
  if (!s) return 'never';
  var d = new Date(s);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function RecoveryPortal() {
  const { user } = useAuth();
  const [queue, setQueue] = useState([]);
  const [tags, setTags] = useState([]);
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState('');
  const [sel, setSel] = useState(null);      // selected client row
  const [notes, setNotes] = useState([]);
  const [picked, setPicked] = useState(null); // picked tag def
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = useCallback(function () {
    Promise.all([
      recoveryService.getQueue(), recoveryService.getTags(), recoveryService.getStats()
    ]).then(function (r) {
      setQueue(r[0].data || []);
      setTags(r[1].data || []);
      setStats(r[2].data || null);
    }).catch(function (e) { setMsg('load failed: ' + (e.message || e)); });
  }, []);
  useEffect(function () { load(); }, [load]);

  const open = function (c) {
    setSel(c); setPicked(null); setText(''); setMsg(null);
    recoveryService.getNotes(c.id).then(function (r) { setNotes(r.data || []); });
  };

  const save = function () {
    if (!picked || !sel) return;
    setBusy(true); setMsg(null);
    recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text: text })
      .then(function () { setSel(null); load(); })
      .catch(function (e) {
        setBusy(false);
        setMsg((e.response && e.response.data && e.response.data.error) || 'save failed');
      });
  };

  const term = search.toLowerCase().replace(/\\s+/g, '');
  const rows = queue.filter(function (c) {
    if (!term) return true;
    var hay = [c.name, c.nin, c.phone, c.lastTag, c.entryType].join(' ').toLowerCase().replace(/\\s+/g, '');
    return hay.indexOf(term) >= 0;
  });

  return (
    <div className={styles.cockpit}>
      <header className={styles.topbar}>
        <h1 className={styles.title}>RECOVERY COCKPIT</h1>
        <div className={styles.counts}>
          <div className={styles.count}><span>{stats ? stats.dueNow : '-'}</span><label>DUE NOW</label></div>
          <div className={styles.count}><span>{stats ? stats.callsToday : '-'}</span><label>CALLS TODAY</label></div>
          <div className={styles.count}><span>{stats ? stats.callsThisMonth : '-'}</span><label>THIS MONTH</label></div>
          <div className={styles.count}><span>{stats ? stats.locked : '-'}</span><label>LOCKED</label></div>
          <div className={styles.count}><span>{stats ? stats.siteVisits : '-'}</span><label>SITE VISITS</label></div>
        </div>
      </header>

      <div className={styles.searchRow}>
        <FiSearch />
        <input
          placeholder="search name / NIN / phone / tag (e.g. needs site visit)"
          value={search}
          onChange={function (e) { setSearch(e.target.value); }}
        />
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr><th>#</th><th>CLIENT</th><th>PHONE</th><th>TYPE</th><th>LAST OUTCOME</th><th>LAST CONTACT</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map(function (c, i) {
              return (
                <tr key={c.id} className={styles.row} onClick={function () { open(c); }}>
                  <td className={styles.num}>{i + 1}</td>
                  <td>
                    <span className={styles.cname}>{c.name}</span>
                    <span className={styles.nin}>{c.nin}</span>
                  </td>
                  <td className={styles.mono}>{c.phone}</td>
                  <td>
                    {c.entryType
                      ? <span className={styles['badge' + (ENTRY_TONE[String(c.entryType).toUpperCase()] || 0)]}>{c.entryType}</span>
                      : <span className={styles.badge0}>-</span>}
                  </td>
                  <td>
                    {c.lastTag
                      ? <span className={c.lastTone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{c.lastTag}</span>
                      : <span className={styles.chipNone}>no contact</span>}
                  </td>
                  <td className={styles.mono}>{fmtWhen(c.lastContactedAt)}</td>
                  <td><button className={styles.openBtn}><FiPhone /> open</button></td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr><td colSpan="7" className={styles.empty}>queue clear - everyone cooled down or contacted</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {sel && (
        <div className={styles.overlay} onClick={function () { setSel(null); }}>
          <div className={styles.drawer} onClick={function (e) { e.stopPropagation(); }}>
            <header className={styles.drawerHead}>
              <div>
                <h2>{sel.name}</h2>
                <span className={styles.nin}>{sel.nin}</span>
                <span className={styles.mono}>{sel.phone}</span>
              </div>
              <button className={styles.closeBtn} onClick={function () { setSel(null); }}><FiX /></button>
            </header>

            {sel.locked && (
              <div className={styles.lockBanner}>
                <FiAlertTriangle /> cool-down active - read only (14-day / 2-call rule)
              </div>
            )}

            <div className={styles.tagwall}>
              <label className={styles.wallLabel}>POSITIVE</label>
              <div className={styles.wallRow}>
                {tags.filter(function (t) { return t.tone === 'POSITIVE'; }).map(function (t) {
                  return (
                    <button key={t.tag}
                      className={(styles.tagPos) + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                      disabled={sel.locked && t.countsAsAttempt}
                      onClick={function () { setPicked(t); }}>
                      {t.tag}
                    </button>
                  );
                })}
              </div>
              <label className={styles.wallLabel}>NEGATIVE</label>
              <div className={styles.wallRow}>
                {tags.filter(function (t) { return t.tone === 'NEGATIVE'; }).map(function (t) {
                  return (
                    <button key={t.tag}
                      className={(styles.tagNeg) + (picked && picked.tag === t.tag ? ' ' + styles.tagOn : '')}
                      disabled={sel.locked && t.countsAsAttempt}
                      onClick={function () { setPicked(t); }}>
                      {t.tag.indexOf('site visit') >= 0 ? <FiMapPin /> : (t.countsAsAttempt ? <FiPhone /> : <FiClock />)} {t.tag}
                    </button>
                  );
                })}
              </div>
            </div>

            <input className={styles.noteInput}
              placeholder="optional detail (rare)"
              value={text}
              onChange={function (e) { setText(e.target.value); }} />

            {msg && <div className={styles.err}>{msg}</div>}

            <div className={styles.drawerActions}>
              <button className={styles.saveBtn} disabled={!picked || busy} onClick={save}>
                {busy ? 'saving...' : 'log outcome'}
              </button>
            </div>

            <div className={styles.history}>
              {notes.map(function (n) {
                return (
                  <div key={n.id} className={styles.histRow}>
                    <span className={n.tone === 'POSITIVE' ? styles.chipPos : styles.chipNeg}>{n.tag}</span>
                    <span className={styles.histMeta}>{n.author || 'system'} - {fmtWhen(n.createdAt)}</span>
                    {n.text && <span className={styles.histText}>{n.text}</span>}
                  </div>
                );
              })}
              {notes.length === 0 && <div className={styles.empty}>no notes yet</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
""".replace("__LABELS__", json.dumps(labels)))

write(css, """.cockpit{min-height:100vh;padding:clamp(12px,2vw,28px);background:var(--navy,#0a1a2f);color:var(--text,#e8eef6);font-family:Inter,system-ui,sans-serif}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:14px}
.title{font-family:Cinzel,serif;color:var(--orange,#ff6b00);font-size:clamp(18px,2.2vw,26px);letter-spacing:2px;margin:0}
.counts{display:flex;gap:10px;flex-wrap:wrap}
.count{background:var(--panel,#10233c);border:1px solid var(--line,#1e3a5c);border-radius:10px;padding:8px 14px;display:flex;flex-direction:column;align-items:center;min-width:86px}
.count span{font-family:'Space Mono',monospace;font-size:clamp(16px,1.8vw,22px);color:var(--orange,#ff6b00)}
.count label{font-size:10px;letter-spacing:1.5px;color:var(--muted,#8aa0b8)}
.searchRow{display:flex;align-items:center;gap:8px;background:var(--panel,#10233c);border:1px solid var(--line,#1e3a5c);border-radius:10px;padding:10px 14px;margin-bottom:14px;color:var(--muted,#8aa0b8)}
.searchRow input{flex:1;background:transparent;border:none;outline:none;color:var(--text,#e8eef6);font-size:14px}
.tableWrap{background:var(--panel,#10233c);border:1px solid var(--line,#1e3a5c);border-radius:12px;overflow:auto;max-height:62vh}
.table{width:100%;border-collapse:collapse;font-size:13px}
.table thead th{position:sticky;top:0;background:var(--panel2,#0d1e33);color:var(--muted,#8aa0b8);font-size:10px;letter-spacing:1.5px;text-align:left;padding:10px 12px;border-bottom:1px solid var(--line,#1e3a5c)}
.table td{padding:10px 12px;border-bottom:1px solid var(--line,#1e3a5c);vertical-align:middle}
.row{cursor:pointer}
.row:hover{background:var(--hover,#132a46)}
.num{font-family:'Space Mono',monospace;color:var(--muted,#8aa0b8)}
.cname{display:block;font-weight:600}
.nin{display:block;font-family:'Space Mono',monospace;font-size:11px;color:var(--orange,#ff6b00)}
.mono{font-family:'Space Mono',monospace;font-size:12px;color:var(--muted,#8aa0b8)}
.badge0,.badge1,.badge2{font-size:10px;letter-spacing:1px;padding:3px 8px;border-radius:6px;border:1px solid var(--line,#1e3a5c)}
.badge0{color:var(--muted,#8aa0b8)}
.badge1{color:#7fd1ff;border-color:#2a5d84}
.badge2{color:#ffb35c;border-color:#84562a}
.chipPos,.chipNeg,.chipNone{font-size:11px;padding:3px 9px;border-radius:20px;white-space:nowrap}
.chipPos{background:#0e3320;color:#5ce08a;border:1px solid #1d5c36}
.chipNeg{background:#331410;color:#ff7a6b;border:1px solid #5c241d}
.chipNone{color:var(--muted,#8aa0b8);border:1px dashed var(--line,#1e3a5c)}
.openBtn{display:flex;align-items:center;gap:6px;background:transparent;border:1px solid var(--orange,#ff6b00);color:var(--orange,#ff6b00);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:12px}
.openBtn:hover{background:var(--orange,#ff6b00);color:#08131f}
.empty{text-align:center;color:var(--muted,#8aa0b8);padding:26px 0 !important}
.overlay{position:fixed;inset:0;background:rgba(4,10,18,.72);display:flex;justify-content:flex-end;z-index:60}
.drawer{width:min(560px,100%);height:100%;background:var(--panel,#10233c);border-left:1px solid var(--line,#1e3a5c);padding:20px;overflow-y:auto;display:flex;flex-direction:column;gap:14px}
.drawerHead{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.drawerHead h2{margin:0 0 4px;font-family:Cinzel,serif;font-size:18px}
.closeBtn{background:transparent;border:none;color:var(--muted,#8aa0b8);font-size:18px;cursor:pointer}
.lockBanner{display:flex;align-items:center;gap:8px;background:#332a10;color:#ffd35c;border:1px solid #5c4a1d;border-radius:10px;padding:10px 12px;font-size:12px}
.wallLabel{font-size:10px;letter-spacing:2px;color:var(--muted,#8aa0b8);margin:6px 0 4px}
.wallRow{display:flex;gap:8px;flex-wrap:wrap}
.tagPos,.tagNeg{display:flex;align-items:center;gap:6px;border-radius:20px;padding:8px 14px;font-size:13px;cursor:pointer}
.tagPos{background:#0e3320;color:#5ce08a;border:1px solid #1d5c36}
.tagNeg{background:#331410;color:#ff7a6b;border:1px solid #5c241d}
.tagPos:disabled,.tagNeg:disabled{opacity:.35;cursor:not-allowed}
.tagOn{outline:2px solid var(--orange,#ff6b00);outline-offset:2px}
.noteInput{background:var(--panel2,#0d1e33);border:1px solid var(--line,#1e3a5c);border-radius:10px;padding:10px 12px;color:var(--text,#e8eef6);outline:none;font-size:13px}
.err{color:#ff7a6b;font-size:12px}
.drawerActions{display:flex;justify-content:flex-end}
.saveBtn{background:var(--orange,#ff6b00);border:none;color:#08131f;font-weight:700;border-radius:10px;padding:10px 22px;cursor:pointer}
.saveBtn:disabled{opacity:.4;cursor:not-allowed}
.history{display:flex;flex-direction:column;gap:8px}
.histRow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px}
.histMeta{color:var(--muted,#8aa0b8)}
.histText{color:var(--text,#e8eef6)}
""")

# ================= COMMIT + PUSH =================
print("== GIT ==")
subprocess.run(["git", "add", "-A"], cwd=ROOT)
r = subprocess.run(["git", "commit", "-m",
    "fix48: recovery call cockpit + notes tags v1 (queue-first, numbers-only, 2-14 server-side)"],
    cwd=ROOT, capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
p = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
print(p.stdout.strip() or p.stderr.strip())

print("\nWARNINGS (non-blocking):")
for w in WARN: print("  -", w)
print("\nfix48 applied. Test AFTER deploy: queue order, tag tap -> note + cooldown, 409 on locked, tag search, badges.")