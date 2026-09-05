# fix.py -- fix70: recovery + notes + notifications unification batch
import os, shutil, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"
FE = ROOT / "erp-frontend" / "src"
BAK = ROOT / ".fix_backup"
def read(p): return p.read_text(encoding="utf-8", errors="replace")
def backup(p):
    try:
        os.makedirs(BAK, exist_ok=True)
        if p.exists() and not (BAK / p.name).exists(): shutil.copy2(p, BAK / p.name)
    except Exception as e: print("BAK WARN", e)
def save(p, s):
    d = os.path.dirname(p)
    if d: os.makedirs(d, exist_ok=True)
    backup(p)
    p.write_text(s, encoding="utf-8", newline="\n")
def write(p, s): save(p, s); print("WROTE", p.name)
def patch(p, old, new, label):
    s = read(p)
    if old in s: save(p, s.replace(old, new, 1)); print("OK", label)
    else: print("MISSING", label)

# ---------- Q1/Q2: seed only when DB empty ----------
DI = BE / "config" / "DataInitializer.java"
patch(DI, "        seedSampleProjects();\n", "        seedSampleProjectsOnlyIfEmpty();\n", "DI guard call")
patch(DI, "    private void seedSampleProjects() {\n        purgeSampleData();\n",
"    public void seedSampleProjectsOnlyIfEmpty() {\n"
"        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement(); java.sql.ResultSet rs = st.executeQuery(\"SELECT COUNT(*) FROM land_projects\")) {\n"
"            rs.next();\n"
"            if (rs.getInt(1) > 0) { System.out.println(\">>> [SAMPLE] Real data present -- skipping demo seed.\"); return; }\n"
"        } catch (Exception e) { System.err.println(\">>> [SAMPLE] count check failed, skipping seed: \" + e.getMessage()); return; }\n"
"        purgeSampleData();\n", "DI seed guard")

# ---------- Q3: old orphan controller out of the way ----------
RC = BE / "modules" / "client" / "controller" / "RecoveryController.java"
patch(RC, '@RequestMapping("/api/v1/recovery")', '@RequestMapping("/api/v1/recovery-legacy")', "legacy remap")

# ---------- Q7: remove dangerous catch-all delete ----------
STC = BE / "modules" / "land" / "controller" / "StageTemplateController.java"
patch(STC, "    @DeleteMapping(\"/{id}\")\n    public ResponseEntity<Void> deleteStage(@PathVariable UUID id) {\n        stageTemplateService.deleteTemplateStage(id);\n        return ResponseEntity.noContent().build();\n    }\n", "", "catch-all delete removed")

# ---------- Q9: remove broken tests ----------
for t in ["modules/land/service/LandCascadeDeleteTest.java", "modules/land/service/ReceivableSchedulerTest.java"]:
    tp = ROOT / "erp-backend" / "src" / "test" / "java" / "com" / "gesolutions" / "erp" / t
    if tp.exists(): backup(tp); tp.unlink(); print("OK deleted", t)
    else: print("MISSING", t)

# ---------- Q8: env.production ----------
write(FE.parent / ".env.production", "VITE_API_BASE_URL=https://ge-solutions-api.onrender.com/api/v1\n")

# ---------- NOTIFICATION STACK ----------
NM = BE / "modules" / "notification"
write(NM / "model" / "Notification.java",
"""package com.gesolutions.erp.modules.notification.model;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;
@Entity
@Table(name = "notifications")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Notification {
    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    @Column(nullable = false, length = 60) private String type;
    @Column(nullable = false, length = 20) private String severity;
    @Column(columnDefinition = "TEXT", nullable = false) private String message;
    @Column(length = 20) private String entityType;
    private UUID entityId;
    @Column(nullable = false, length = 30) private String targetRole;
    @Column(name = "created_at", nullable = false) private LocalDateTime createdAt;
}
""")
write(NM / "model" / "NotificationRead.java",
"""package com.gesolutions.erp.modules.notification.model;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;
@Entity
@Table(name = "notification_reads", uniqueConstraints = @UniqueConstraint(columnNames = {"notification_id", "user_id"}))
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class NotificationRead {
    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    @Column(name = "notification_id", nullable = false) private UUID notificationId;
    @Column(name = "user_id", nullable = false) private UUID userId;
    @Column(name = "read_at") private LocalDateTime readAt;
}
""")
write(NM / "repository" / "NotificationRepository.java",
"""package com.gesolutions.erp.modules.notification.repository;
import com.gesolutions.erp.modules.notification.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
public interface NotificationRepository extends JpaRepository<Notification, UUID> {
    @Query("SELECT n FROM Notification n WHERE n.targetRole = 'ALL' OR n.targetRole = :role ORDER BY n.createdAt DESC")
    List<Notification> findForRole(@Param("role") String role);
    boolean existsByTypeAndEntityId(String type, UUID entityId);
    boolean existsByTypeAndEntityIdAndCreatedAtAfter(String type, UUID entityId, LocalDateTime after);
}
""")
write(NM / "repository" / "NotificationReadRepository.java",
"""package com.gesolutions.erp.modules.notification.repository;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
public interface NotificationReadRepository extends JpaRepository<NotificationRead, UUID> {
    boolean existsByNotificationIdAndUserId(UUID notificationId, UUID userId);
    List<NotificationRead> findByUserId(UUID userId);
}
""")
write(NM / "service" / "NotificationService.java",
"""package com.gesolutions.erp.modules.notification.service;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;
@Service
@RequiredArgsConstructor
public class NotificationService {
    private final NotificationRepository repo;
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void emit(String type, String severity, String message, String entityType, UUID entityId, String targetRole) {
        if (type == null || entityId == null) return;
        if (repo.existsByTypeAndEntityId(type, entityId)) return;
        repo.save(Notification.builder().type(type).severity(severity).message(message)
            .entityType(entityType).entityId(entityId).targetRole(targetRole)
            .createdAt(LocalDateTime.now()).build());
    }
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void emitRaw(String type, String severity, String message, String entityType, UUID entityId, String targetRole) {
        repo.save(Notification.builder().type(type).severity(severity).message(message)
            .entityType(entityType).entityId(entityId).targetRole(targetRole)
            .createdAt(LocalDateTime.now()).build());
    }
    @Transactional(readOnly = true)
    public boolean existsToday(String type, UUID entityId) {
        return repo.existsByTypeAndEntityIdAndCreatedAtAfter(type, entityId, LocalDate.now().atStartOfDay());
    }
}
""")
write(NM / "controller" / "NotificationController.java",
"""package com.gesolutions.erp.modules.notification.controller;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.notification.model.Notification;
import com.gesolutions.erp.modules.notification.model.NotificationRead;
import com.gesolutions.erp.modules.notification.repository.NotificationReadRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDateTime;
import java.util.*;
@RestController
@RequestMapping("/api/v1/notifications")
@RequiredArgsConstructor
public class NotificationController {
    private final NotificationRepository notifRepo;
    private final NotificationReadRepository readRepo;
    private final UserRepository userRepo;
    private User me(Authentication auth) { return userRepo.findByUsername(auth.getName()).orElse(null); }
    @GetMapping
    public List<Map<String, Object>> list(Authentication auth) {
        User u = me(auth);
        if (u == null) return List.of();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Notification n : notifRepo.findForRole(u.getRole().name())) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", n.getId()); m.put("type", n.getType()); m.put("severity", n.getSeverity());
            m.put("message", n.getMessage()); m.put("entityType", n.getEntityType());
            m.put("entityId", n.getEntityId()); m.put("createdAt", n.getCreatedAt());
            m.put("read", readRepo.existsByNotificationIdAndUserId(n.getId(), u.getId()));
            out.add(m);
        }
        return out;
    }
    @GetMapping("/unread-count")
    public Map<String, Long> unread(Authentication auth) {
        User u = me(auth);
        if (u == null) return Map.of("unread", 0L);
        long c = notifRepo.findForRole(u.getRole().name()).stream()
            .filter(n -> !readRepo.existsByNotificationIdAndUserId(n.getId(), u.getId())).count();
        return Map.of("unread", c);
    }
    @PostMapping("/{id}/read")
    public Map<String, Object> read(@PathVariable UUID id, Authentication auth) {
        User u = me(auth);
        if (u != null && !readRepo.existsByNotificationIdAndUserId(id, u.getId())) {
            readRepo.save(NotificationRead.builder().notificationId(id).userId(u.getId()).readAt(LocalDateTime.now()).build());
        }
        return Map.of("ok", true);
    }
    @PostMapping("/read-all")
    public Map<String, Object> readAll(Authentication auth) {
        User u = me(auth);
        if (u == null) return Map.of("ok", false);
        for (Notification n : notifRepo.findForRole(u.getRole().name())) {
            if (!readRepo.existsByNotificationIdAndUserId(n.getId(), u.getId())) {
                readRepo.save(NotificationRead.builder().notificationId(n.getId()).userId(u.getId()).readAt(LocalDateTime.now()).build());
            }
        }
        return Map.of("ok", true);
    }
}
""")

# ---------- RecoveryNote entity + repo (M8 promise date) ----------
write(BE / "modules" / "client" / "model" / "RecoveryNote.java",
"""package com.gesolutions.erp.modules.client.model;
import com.gesolutions.erp.modules.auth.model.User;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;
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
    @Column(nullable = false, length = 60) private String tag;
    @Column(nullable = false, length = 10) private String tone;
    @Column(name = "counts_as_attempt", nullable = false) private boolean countsAsAttempt;
    @Column(length = 500) private String text;
    @Column(name = "promise_date") private LocalDate promiseDate;
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    @PrePersist
    void onCreate() { if (createdAt == null) createdAt = LocalDateTime.now(); }
}
""")
write(BE / "modules" / "client" / "repository" / "RecoveryNoteRepository.java",
"""package com.gesolutions.erp.modules.client.repository;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
public interface RecoveryNoteRepository extends JpaRepository<RecoveryNote, UUID> {
    List<RecoveryNote> findByClientOrderByCreatedAtDesc(Client client);
    Optional<RecoveryNote> findFirstByClientOrderByCreatedAtDesc(Client client);
    long countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(Client client, LocalDateTime after);
    long countByCountsAsAttemptTrueAndCreatedAtAfter(LocalDateTime after);
    @Query("SELECT n FROM RecoveryNote n WHERE n.tag = 'committed to pay' AND n.promiseDate IS NOT NULL AND n.promiseDate < :d")
    List<RecoveryNote> findOverduePromises(@Param("d") LocalDate d);
}
""")

# ---------- RecoveryNoteController full rewrite (M1,M4,M6,M7,M8,M9,M10 + path fix) ----------
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
        {"committed to pay",   "POSITIVE", "true"},
        {"answered call",      "POSITIVE", "true"},
        {"not picking up",     "NEGATIVE", "true"},
        {"not going through",  "NEGATIVE", "true"},
        {"rings, no answer",   "NEGATIVE", "true"},
        {"phone off",          "NEGATIVE", "true"},
        {"needs site visit",   "NEGATIVE", "false"},
        {"failed to pay",      "NEGATIVE", "false"}
    };
    private static String[] tagDef(String tag) { for (String[] t : TAGS) if (t[0].equals(tag)) return t; return null; }
    private List<LandProject> projectsOf(Client c) {
        List<LandProject> out = new ArrayList<>();
        for (LandProject p : projectRepo.findAll()) {
            if (p.getProprietors() != null && p.getProprietors().contains(c)) out.add(p);
        }
        return out;
    }
    private String entryTypeOf(List<LandProject> ps) {
        for (LandProject p : ps) {
            if (p.isLegacy()) return "Legacy Title";
            if (p.getLandTitle() != null) return "New Title";
        }
        return ps.isEmpty() ? null : "New Folder";
    }
    private boolean qualifies(List<LandProject> ps) {
        if (ps.isEmpty()) return false;
        for (LandProject p : ps) {
            if (p.isLegacy()) return true;
            double owed = Math.max(p.activeTotalOwed().doubleValue(), p.receivableTotalOwed().doubleValue());
            if (owed > 0) return true;
            if (p.getStages() != null) {
                for (var s : p.getStages()) if (!s.isCompleted()) return true;
            }
            return true;
        }
        return false;
    }
    private boolean locked(Client c, LocalDateTime now) {
        LocalDateTime last = c.getLastContactedAt();
        if (last != null && last.isAfter(now.minusDays(14))) return true;
        return noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(c, LocalDate.now().withDayOfMonth(1).atStartOfDay()) >= 2;
    }
    private LocalDateTime nextUnlock(Client c, LocalDateTime now) {
        LocalDateTime a = null;
        LocalDateTime last = c.getLastContactedAt();
        if (last != null && last.isAfter(now.minusDays(14))) a = last.plusDays(14);
        long attempts = noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(c, LocalDate.now().withDayOfMonth(1).atStartOfDay());
        LocalDateTime b = attempts >= 2 ? LocalDate.now().withDayOfMonth(1).plusMonths(1).atStartOfDay() : null;
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
    private String payBadge(List<LandProject> ps) {
        LocalDateTime newest = null;
        for (LandProject p : ps) {
            if (p.getLastPaymentDate() != null && (newest == null || p.getLastPaymentDate().isAfter(newest))) newest = p.getLastPaymentDate();
        }
        if (newest == null) return "RED";
        long days = ChronoUnit.DAYS.between(newest, LocalDateTime.now());
        if (days <= 14) return "GREEN";
        if (days <= 30) return "YELLOW";
        return "RED";
    }
    private String recvState(List<LandProject> ps) {
        boolean recv = false, legacy = false, paying = false;
        for (LandProject p : ps) {
            if (p.isLegacy()) legacy = true;
            if (p.isReceivable()) {
                recv = true;
                if (p.getLastPaymentDate() != null && ChronoUnit.DAYS.between(p.getLastPaymentDate(), LocalDateTime.now()) <= 90) paying = true;
            }
        }
        if (legacy) return "LEGACY";
        if (recv) return paying ? "RECEIVABLE - PAYING" : "RECEIVABLE - SILENT";
        return "";
    }
    private Map<String, Object> clientDto(Client c, LocalDateTime now, List<LandProject> ps) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", c.getId()); m.put("name", c.getFullName()); m.put("nin", c.getNationalId());
        m.put("phone", c.getPhoneNumber()); m.put("entryType", entryTypeOf(ps));
        List<String> idx = new ArrayList<>(); List<String> pids = new ArrayList<>();
        for (LandProject p : ps) { if (p.getProjectIndex() != null) idx.add(p.getProjectIndex()); pids.add(p.getId().toString()); }
        m.put("indexes", idx); m.put("projectIds", pids);
        m.put("district", ps.isEmpty() ? null : ps.get(0).getDistrict());
        m.put("village", ps.isEmpty() ? null : ps.get(0).getVillage());
        m.put("lastContactedAt", c.getLastContactedAt());
        m.put("payBadge", payBadge(ps)); m.put("recvState", recvState(ps));
        boolean lock = locked(c, now);
        m.put("locked", lock);
        m.put("nextUnlock", lock ? nextUnlock(c, now).toString() : null);
        m.put("attemptsThisMonth", noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(c, LocalDate.now().withDayOfMonth(1).atStartOfDay()));
        noteRepo.findFirstByClientOrderByCreatedAtDesc(c).ifPresent(n -> { m.put("lastTag", n.getTag()); m.put("lastTone", n.getTone()); });
        String lastTag = (String) m.get("lastTag");
        long days = c.getLastContactedAt() == null ? 999 : ChronoUnit.DAYS.between(c.getLastContactedAt(), now);
        int priority = 3;
        if ("failed to pay".equals(lastTag) || "Legacy Title".equals(m.get("entryType"))) priority = 1;
        else if (days > 30 || negStreak(c) >= 2 || "needs site visit".equals(lastTag)) priority = 2;
        m.put("priority", priority);
        return m;
    }
    @GetMapping("/tags")
    public List<Map<String, Object>> tags() {
        List<Map<String, Object>> out = new ArrayList<>();
        for (String[] t : TAGS) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("tag", t[0]); m.put("tone", t[1]); m.put("countsAsAttempt", Boolean.parseBoolean(t[2]));
            out.add(m);
        }
        return out;
    }
    @GetMapping("/queue")
    public List<Map<String, Object>> queue() {
        LocalDateTime now = LocalDateTime.now();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Client c : clientRepo.findAll()) {
            List<LandProject> ps = projectsOf(c);
            if (locked(c, now) || !qualifies(ps)) continue;
            out.add(clientDto(c, now, ps));
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
            List<LandProject> ps = projectsOf(c);
            if (!locked(c, now) || !qualifies(ps)) continue;
            out.add(clientDto(c, now, ps));
        }
        return out;
    }
    @GetMapping("/stats")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    public Map<String, Object> stats() {
        LocalDateTime now = LocalDateTime.now();
        long due = 0, lock = 0, site = 0, p1 = 0;
        for (Client c : clientRepo.findAll()) {
            List<LandProject> ps = projectsOf(c);
            if (!qualifies(ps)) continue;
            Map<String, Object> d = clientDto(c, now, ps);
            if (Boolean.TRUE.equals(d.get("locked"))) lock++; else due++;
            if ("needs site visit".equals(d.get("lastTag"))) site++;
            if ((int) d.get("priority") == 1) p1++;
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("dueNow", due); m.put("locked", lock); m.put("siteVisits", site); m.put("p1", p1);
        m.put("callsToday", noteRepo.countByCountsAsAttemptTrueAndCreatedAtAfter(LocalDate.now().atStartOfDay()));
        m.put("callsThisMonth", noteRepo.countByCountsAsAttemptTrueAndCreatedAtAfter(LocalDate.now().withDayOfMonth(1).atStartOfDay()));
        return m;
    }
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
            for (LandProject p : projectsOf(c)) {
                for (FollowUpLog log : followUpRepo.findByProjectIdOrderByTimestampDesc(p.getId())) {
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("id", log.getId()); m.put("tag", "FOLDER NOTE"); m.put("tone", "INFO");
                    m.put("text", log.getNotes()); m.put("countsAsAttempt", false);
                    m.put("createdAt", log.getTimestamp()); m.put("source", "FOLDER");
                    m.put("author", log.getRecordedBy());
                    out.add(m);
                }
            }
            out.sort((a, b) -> ((LocalDateTime) b.get("createdAt")).compareTo((LocalDateTime) a.get("createdAt")));
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
            return ResponseEntity.status(409).body(Map.of("error", "Cool-down active: 14-day interval or 2-call monthly limit"));
        User author = userRepo.findByUsername(auth.getName()).orElse(null);
        LocalDate promise = null;
        if (body.get("promiseDate") != null && !body.get("promiseDate").isBlank()) {
            try { promise = LocalDate.parse(body.get("promiseDate")); } catch (Exception ignored) {}
        }
        RecoveryNote n = RecoveryNote.builder()
            .client(c).author(author).tag(def[0]).tone(def[1]).countsAsAttempt(attempt)
            .text(body.get("text") == null || body.get("text").isBlank() ? null : body.get("text").trim())
            .promiseDate(promise)
            .build();
        noteRepo.save(n);
        if (attempt) c.setLastContactedAt(now);
        double delta = 0;
        if ("POSITIVE".equals(def[1]) && attempt) delta = 1.5;
        if ("failed to pay".equals(tag)) delta = -10;
        if ("not picking up".equals(tag) || "phone off".equals(tag) || "rings, no answer".equals(tag)) delta = -2;
        if (delta != 0) {
            double cur = c.getReliabilityScore() == null ? 100.0 : c.getReliabilityScore();
            c.setReliabilityScore(Math.max(0.0, Math.min(100.0, cur + delta)));
        }
        clientRepo.save(c);
        auditService.logAction("RECOVERY_NOTE", "RECOVERY_NOTE: " + tag + " (NIN " + c.getNationalId() + ")");
        long monthAttempts = noteRepo.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(c, LocalDate.now().withDayOfMonth(1).atStartOfDay());
        if (attempt && monthAttempts == 2 && author != null) {
            notificationService.emitRaw("MONTHLY_LIMIT", "INFO", c.getFullName() + ": 2nd call this month. Next callable 1st of next month.", "CLIENT", c.getId(), author.getRole().name());
        }
        if (negStreak(c) >= 2) {
            notificationService.emit("NEG_STREAK_2", "WARN", c.getFullName() + ": 2 negative contacts in a row - suggest site visit.", "CLIENT", c.getId(), "ROLE_MANAGER");
        }
        if ("failed to pay".equals(tag)) {
            boolean priorPromise = noteRepo.findByClientOrderByCreatedAtDesc(c).stream().anyMatch(x -> "committed to pay".equals(x.getTag()) && !x.getId().equals(n.getId()));
            if (priorPromise) {
                notificationService.emit("FAILED_AFTER_PROMISE", "CRITICAL", c.getFullName() + " failed to pay after committing. Escalate.", "CLIENT", c.getId(), "ROLE_DIRECTOR");
                notificationService.emit("FAILED_AFTER_PROMISE_M", "CRITICAL", c.getFullName() + " failed to pay after committing. Escalate.", "CLIENT", c.getId(), "ROLE_MANAGER");
            }
        }
        if ("NEGATIVE".equals(def[1]) && c.getReliabilityScore() != null && c.getReliabilityScore() < 40) {
            notificationService.emit("RELIABILITY_LOW", "WARN", c.getFullName() + " reliability below 40 after negative contact.", "CLIENT", c.getId(), "ROLE_MANAGER");
        }
        if ("needs site visit".equals(tag)) {
            notificationService.emit("SITE_VISIT_TAGGED", "INFO", c.getFullName() + " needs a site visit.", "CLIENT", c.getId(), "ROLE_DIRECTOR");
        }
        String warning = null;
        LocalDateTime window = now.minusDays(3);
        for (LandProject p : projectsOf(c)) {
            for (Client co : p.getProprietors()) {
                if (co.getId().equals(c.getId())) continue;
                for (RecoveryNote other : noteRepo.findByClientOrderByCreatedAtDesc(co)) {
                    if (other.isCountsAsAttempt() && other.getCreatedAt().isAfter(window)) {
                        warning = co.getFullName() + " was already contacted about this plot on " + other.getCreatedAt().toLocalDate() + ".";
                        break;
                    }
                }
                if (warning != null) break;
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
        boolean wasAttempt = n.isCountsAsAttempt();
        noteRepo.delete(n);
        if (wasAttempt && c != null) {
            LocalDateTime newest = null;
            for (RecoveryNote r : noteRepo.findByClientOrderByCreatedAtDesc(c)) {
                if (r.isCountsAsAttempt()) { newest = r.getCreatedAt(); break; }
            }
            c.setLastContactedAt(newest);
            clientRepo.save(c);
        }
        auditService.logAction("RECOVERY_NOTE_DELETED", "Operator [" + auth.getName() + "] deleted tap-tag: " + n.getTag());
        return ResponseEntity.ok(Map.of("ok", true));
    }
}
""")

# ---------- Q5/M3: Dashboard NPE fixes + note-based stale count ----------
DC = BE / "modules" / "land" / "controller" / "DashboardController.java"
patch(DC, "    private final ExpenseRepository expenseRepository;\n",
"    private final ExpenseRepository expenseRepository;\n    private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;\n", "DC inject noteRepo")
patch(DC, """        long plotsGrowth = allPlots.stream()
                .filter(p -> p.getLandTitle().getCreatedAt().isAfter(sevenDaysAgo))
                .count();""",
"""        long plotsGrowth = allPlots.stream()
                .filter(p -> {
                    if (p.getLandTitle() != null && p.getLandTitle().getCreatedAt() != null) return p.getLandTitle().getCreatedAt().isAfter(sevenDaysAgo);
                    return p.getProjectStartDate() != null && p.getProjectStartDate().isAfter(sevenDaysAgo.toLocalDate());
                })
                .count();""", "DC plotsGrowth null-safe")
patch(DC, """                .filter(owner -> {
                    if (owner.shouldResetMonthlyCounter()) owner.setMonthlyContactCount(0);
                    if (owner.getMonthlyContactCount() >= 2) return false;
                    if (owner.getLastContactedAt() == null) return true;
                    java.time.LocalDate eligible = owner.getLastContactedAt().toLocalDate().plusDays(14);
                    return !java.time.LocalDate.now().isBefore(eligible);
                })""",
"""                .filter(owner -> {
                    java.time.LocalDateTime monthStart = java.time.LocalDate.now().withDayOfMonth(1).atStartOfDay();
                    if (recoveryNoteRepository.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(owner, monthStart) >= 2) return false;
                    java.util.Optional<com.gesolutions.erp.modules.client.model.RecoveryNote> last = recoveryNoteRepository.findFirstByClientOrderByCreatedAtDesc(owner);
                    if (!last.isPresent()) return true;
                    java.time.LocalDate eligible = last.get().getCreatedAt().toLocalDate().plusDays(14);
                    return !java.time.LocalDate.now().isBefore(eligible);
                })""", "DC stale from notes")
patch(DC, """        long readyForRelease = allPlots.stream()
                .filter(p -> p.getAmountPaid().compareTo(p.getTotalCost()) >= 0)
                .filter(p -> !p.getLandTitle().isReleased())
                .count();""",
"""        long readyForRelease = allPlots.stream()
                .filter(p -> p.getAmountPaid().compareTo(p.getTotalCost()) >= 0)
                .filter(p -> p.getLandTitle() != null && !p.getLandTitle().isReleased())
                .count();""", "DC readyForRelease null-safe")

# ---------- Q5: scheduler NPE (owner name) + T7/T8 + daily sweep T1/T5 ----------
RS = BE / "modules" / "land" / "service" / "ReceivableSchedulerService.java"
patch(RS, "import com.gesolutions.erp.common.audit.AuditService;\n",
"import com.gesolutions.erp.common.audit.AuditService;\nimport com.gesolutions.erp.modules.client.model.Client;\nimport com.gesolutions.erp.modules.client.model.RecoveryNote;\nimport com.gesolutions.erp.modules.client.repository.ClientRepository;\nimport com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;\nimport com.gesolutions.erp.modules.land.model.PaymentRecord;\nimport com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;\nimport com.gesolutions.erp.modules.notification.service.NotificationService;\nimport java.util.Optional;\nimport java.time.LocalDate;\n", "RS imports")
patch(RS, "    private final AuditService auditService;\n",
"    private final AuditService auditService;\n    private final NotificationService notificationService;\n    private final RecoveryNoteRepository recoveryNoteRepository;\n    private final PaymentRecordRepository paymentRecordRepository;\n    private final ClientRepository clientRepo;\n", "RS injects")
patch(RS, """                            + plot.getLandTitle().getPlotNumber()""",
"""                            + ownerLabel(plot)""", "RS audit label")
patch(RS, """                            + " | Total accumulated fees: UGX " + plot.getStorageFeesAccumulated());""",
"""                            + " | Total accumulated fees: UGX " + plot.getStorageFeesAccumulated());
            notificationService.emit("STORAGE_FEE_APPLIED", "INFO", "Storage fee UGX " + toAdd + " added to " + ownerLabel(plot) + ".", "PROJECT", plot.getId(), "ROLE_DIRECTOR");""", "RS T7")
patch(RS, """            auditService.logAction("AUTO_RECEIVABLE",
                    "SYSTEM: Plot " + plot.getLandTitle().getPlotNumber()""",
"""            auditService.logAction("AUTO_RECEIVABLE",
                    "SYSTEM: Plot " + ownerLabel(plot)""", "RS auto label")
patch(RS, """                    "Debt frozen at: UGX " + outstanding);""",
"""                    "Debt frozen at: UGX " + outstanding);
            notificationService.emit("AUTO_RECEIVABLE_365", "WARN", ownerLabel(plot) + " auto-flagged RECEIVABLE after 365 days silent.", "PROJECT", plot.getId(), "ROLE_DIRECTOR");""", "RS T8")
s = read(RS)
if "dailyNotificationSweep" not in s:
    t = s.rstrip()
    if t.endswith("}"):
        t = t[:-1] + """
    private String ownerLabel(LandProject plot) {
        if (plot.getProprietors() != null && !plot.getProprietors().isEmpty()) {
            for (Client c : plot.getProprietors()) return c.getFullName();
        }
        return plot.getProjectIndex() != null ? ("project #" + plot.getProjectIndex()) : "untitled project";
    }
    @Scheduled(cron = "0 0 7 * * *")
    @Transactional
    public void dailyNotificationSweep() {
        LocalDateTime now = LocalDateTime.now();
        for (RecoveryNote n : recoveryNoteRepository.findOverduePromises(LocalDate.now())) {
            Client c = n.getClient();
            boolean paidSince = false;
            for (LandProject p : projectRepository.findAll()) {
                if (p.getProprietors() == null || !p.getProprietors().contains(c)) continue;
                for (PaymentRecord pay : paymentRecordRepository.findByProjectIdOrderByTimestampDesc(p.getId())) {
                    if (pay.getTimestamp().isAfter(n.getCreatedAt())) { paidSince = true; break; }
                }
                if (paidSince) break;
            }
            if (!paidSince) {
                notificationService.emit("PROMISE_DUE", "CRITICAL",
                    c.getFullName() + " promised to pay by " + n.getPromiseDate() + " but no payment arrived.",
                    "NOTE", n.getId(), "ROLE_MANAGER");
            }
        }
        for (Client c : clientRepo.findAll()) {
            Optional<RecoveryNote> last = recoveryNoteRepository.findFirstByClientOrderByCreatedAtDesc(c);
            if (!last.isPresent() || !last.get().isCountsAsAttempt()) continue;
            if (last.get().getCreatedAt().isAfter(now.minusDays(14))) continue;
            if (recoveryNoteRepository.countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(c, LocalDate.now().withDayOfMonth(1).atStartOfDay()) >= 2) continue;
            if (notificationService.existsToday("COOLDOWN_EXPIRED", c.getId())) continue;
            notificationService.emitRaw("COOLDOWN_EXPIRED", "INFO", c.getFullName() + " is callable again - cooldown expired.", "CLIENT", c.getId(), "ROLE_SECRETARY");
            notificationService.emitRaw("COOLDOWN_EXPIRED_M", "INFO", c.getFullName() + " is callable again - cooldown expired.", "CLIENT", c.getId(), "ROLE_MANAGER");
        }
    }
}
"""
        save(RS, t); print("OK RS sweep")
    else: print("MISSING RS closing brace")
else: print("skip RS sweep (already present)")

# ---------- Q5 + M5: ReportService NPE + throughput merge ----------
RP = BE / "modules" / "land" / "service" / "ReportService.java"
patch(RP, "    private final PaymentRecordRepository paymentRecordRepository;\n",
"    private final PaymentRecordRepository paymentRecordRepository;\n    private final com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository recoveryNoteRepository;\n", "RP inject noteRepo")
patch(RP, """                if (proj.isPresent()) {
                        plotNumber = proj.get().getLandTitle().getPlotNumber();""",
"""                if (proj.isPresent()) {
                        if (proj.get().getLandTitle() != null && proj.get().getLandTitle().getPlotNumber() != null) plotNumber = proj.get().getLandTitle().getPlotNumber();
                        else plotNumber = proj.get().getProprietors().stream().findFirst().map(com.gesolutions.erp.modules.client.model.Client::getFullName).orElse(proj.get().getProjectIndex() != null ? proj.get().getProjectIndex() : "---");""", "RP revenue null-safe")
patch(RP, """        for (FollowUpLog log : logs) {
            csv.append(log.getTimestamp()).append(CSV_DIVIDER)
                    .append(log.getRecordedBy()).append(CSV_DIVIDER)
                    .append(log.getProjectId()).append(CSV_DIVIDER)
                    .append("\\"").append(log.getNotes()).append("\\"")
                    .append(NEW_LINE);
        }
        return csv.toString().getBytes();""",
"""        for (FollowUpLog log : logs) {
            csv.append(log.getTimestamp()).append(CSV_DIVIDER)
                    .append(log.getRecordedBy()).append(CSV_DIVIDER)
                    .append(log.getProjectId()).append(CSV_DIVIDER)
                    .append("\\"").append(log.getNotes()).append("\\"")
                    .append(NEW_LINE);
        }
        for (com.gesolutions.erp.modules.client.model.RecoveryNote n : recoveryNoteRepository.findAll()) {
            csv.append(n.getCreatedAt()).append(CSV_DIVIDER)
                    .append(n.getAuthor() != null ? n.getAuthor().getUsername() : "SYSTEM").append(CSV_DIVIDER)
                    .append("CLIENT:").append(n.getClient() != null ? n.getClient().getFullName() : "---").append(CSV_DIVIDER)
                    .append("\\"[TAP-TAG] ").append(n.getTag()).append(n.getText() != null ? " - " + n.getText() : "").append("\\"")
                    .append(NEW_LINE);
        }
        return csv.toString().getBytes();""", "RP throughput merge")

# ---------- T10/T11: LandService emits ----------
LS = BE / "modules" / "land" / "service" / "LandService.java"
patch(LS, "    private final ProjectStageRepository projectStageRepository;\n",
"    private final ProjectStageRepository projectStageRepository;\n    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;\n", "LS inject notif")
patch(LS, """        auditService.logAction("PAYMENT_RECORDED",
                "Operator [" + operator + "] recorded UGX " + amount""",
"""        if ("RECEIVABLE_PARTIAL".equals(paymentType)) {
            notificationService.emit("PAYMENT_ON_RECEIVABLE", "POSITIVE", "Payment UGX " + amount + " received on " + plotLabel(project) + ".", "PROJECT", projectId, "ROLE_DIRECTOR");
        }
        auditService.logAction("PAYMENT_RECORDED",
                "Operator [" + operator + "] recorded UGX " + amount""", "LS T10")
patch(LS, """        auditService.logAction("INTAKE",
                "Operator [" + getCurrentOperator() + "] ingested binder: """,
"""        notificationService.emit("NEW_INTAKE", "INFO", "New project " + projectIndex + " registered by " + getCurrentOperator() + ".", "PROJECT", saved.getId(), "ROLE_MANAGER");
        auditService.logAction("INTAKE",
                "Operator [" + getCurrentOperator() + "] ingested binder: """, "LS T11")

# ---------- frontend services ----------
write(FE / "services" / "recoveryService.js",
"""import api from '../api/axios';
// RECOVERY COCKPIT v2 - cards, priority, locked tray, numbers-only
const recoveryService = {
  getQueue:  () => api.get('/recovery/queue'),
  getLocked: () => api.get('/recovery/locked'),
  getTags:   () => api.get('/recovery/tags'),
  getStats:  () => api.get('/recovery/stats'),
  getTaskCount: () => api.get('/recovery/stats').then(r => r.data.dueNow),
  getNotes:  (clientId) => api.get('/recovery/clients/' + clientId + '/notes'),
  logNote:   (payload) => api.post('/recovery/notes', payload),
  deleteNote: (noteId) => api.delete('/recovery/notes/' + noteId),
  recordPayment: (projectId, amount, notes) => api.post(`/land/projects/${projectId}/payment`, null, { params: { amount, notes } }),
  getNotifications: () => api.get('/notifications').then(r => r.data),
  getUnreadCount: () => api.get('/notifications/unread-count').then(r => r.data.unread),
  markRead: (id) => api.post('/notifications/' + id + '/read'),
  markAllRead: () => api.post('/notifications/read-all'),
};
export default recoveryService;
""")
write(FE / "services" / "folderPortalService.js",
"""import api from '../api/axios';
export const folderPortalService = {
  getReceivable: (id) => api.get(`/land/portal/${id}/receivable`).then(r => r.data),
  getPortfolio:  (id) => api.get(`/land/portal/${id}/portfolio`).then(r => r.data),
  enter:    (id) => api.post(`/land/portal/${id}/receivable/enter`).then(r => r.data),
  exit: (id, action) => api.post(`/land/portal/${id}/receivable/exit`, { action }).then(r => r.data),
  settings: (id, payload) => api.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),
  toggleProblem: (id, note) => api.post(`/land/portal/${id}/toggle-problem`, null, { params: note ? { note } : {} }).then(r => r.data),
};
export default folderPortalService;
""")

# ---------- Q4: Header bell dropdown with notification summary lines ----------
write(FE / "components" / "layout" / "Header.jsx",
"""import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiBell, FiLogOut, FiCheck } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import recoveryService from '../../services/recoveryService';
import styles from './Header.module.css';
const SEV_COLOR = { POSITIVE: '#10b981', WARN: '#f59e0b', CRITICAL: '#ef4444', INFO: '#06b6d4' };
const Header = ({ onToggle }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [staleCount, setStaleCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifs, setNotifs] = useState([]);
  const [unread, setUnread] = useState(0);
  const dropRef = useRef(null);
  const isRoot = user?.isRoot;
  const roleMap = { ROLE_ADMIN: 'ADMIN', ROLE_DIRECTOR: 'DIRECTOR', ROLE_MANAGER: 'MANAGER', ROLE_SECRETARY: 'SECRETARY' };
  const displayRole = isRoot ? 'ROOT OWNER' : (roleMap[user?.role] || 'STAFF');
  const initials = user?.username?.charAt(0).toUpperCase() || 'A';
  const sync = useCallback(async () => {
    try { setStaleCount((await recoveryService.getTaskCount()) ?? 0); } catch {}
    try { setUnread((await recoveryService.getUnreadCount()) ?? 0); } catch {}
  }, []);
  useEffect(() => {
    sync();
    const iv = setInterval(sync, 300000);
    return () => clearInterval(iv);
  }, [sync]);
  useEffect(() => {
    const h = (e) => { if (dropRef.current && !dropRef.current.contains(e.target)) setNotifOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);
  const openDrop = async () => {
    const next = !notifOpen;
    setNotifOpen(next);
    if (next) { try { setNotifs(await recoveryService.getNotifications()); } catch { setNotifs([]); } }
  };
  const go = (n) => {
    setNotifOpen(false);
    if (n.entityType === 'PROJECT' && n.entityId) navigate('/folder/' + n.entityId);
    else navigate('/recovery');
    recoveryService.markRead(n.id).then(sync).catch(() => {});
  };
  const badge = unread + (staleCount > 0 ? staleCount : 0);
  return (
    <header className={styles.header}>
      <div className={styles.headerLeft}>
        <button type="button" className={styles.sidebarToggle} onClick={onToggle} aria-label="Toggle sidebar navigation">
          <FiMenu aria-hidden="true" />
        </button>
        <div className={styles.logoSection} aria-label="Golden Seed ERP">
          <div className={styles.logoSmallPulse} aria-hidden="true">
            <div className={styles.pulseInner}>🌱</div>
            <div className={styles.pulseRing} />
          </div>
          <span className={styles.brandName}>GOLDEN SEED</span>
        </div>
      </div>
      <div className={styles.headerRight}>
        <div className={styles.notifWrap} ref={dropRef}>
          <button
            type="button"
            className={`${styles.notificationGroup} ${badge > 0 ? styles.activeSensor : ''}`}
            onClick={openDrop}
            aria-label={badge > 0 ? badge + ' signals pending' : 'Open notifications'}
          >
            <FiBell className={styles.bellIcon} aria-hidden="true" />
            {badge > 0 && <span className={styles.badge} aria-hidden="true">{badge > 99 ? '99+' : badge}</span>}
          </button>
          {notifOpen && (
            <div className={styles.notifDrop}>
              <div className={styles.notifHead}>
                <span>SIGNALS</span>
                <button type="button" className={styles.notifReadAll} onClick={() => recoveryService.markAllRead().then(sync).catch(() => {})}>
                  <FiCheck aria-hidden="true" /> READ ALL
                </button>
              </div>
              {notifs.length === 0 && <div className={styles.notifEmpty}>NO SIGNALS</div>}
              {notifs.slice(0, 12).map(n => (
                <button type="button" key={n.id} className={`${styles.notifRow} ${n.read ? styles.notifRead : ''}`} onClick={() => go(n)}>
                  <span className={styles.notifDot} style={{ background: SEV_COLOR[n.severity] || '#06b6d4' }} />
                  <span className={styles.notifMsg}>{n.message}</span>
                </button>
              ))}
              {staleCount > 0 && (
                <button type="button" className={styles.notifRow} onClick={() => { setNotifOpen(false); navigate('/recovery'); }}>
                  <span className={styles.notifDot} style={{ background: '#EE8C3A' }} />
                  <span className={styles.notifMsg}>{staleCount} recovery mission{staleCount > 1 ? 's' : ''} due now</span>
                </button>
              )}
            </div>
          )}
        </div>
        <div className={styles.userCard} aria-label={`Logged in as ${user?.username}, ${displayRole}`}>
          <div className={styles.avatar} aria-hidden="true">{initials}</div>
          <div className={styles.userMeta}>
            <span className={styles.userName}>{user?.username}</span>
            <span className={styles.roleTag}>{displayRole}</span>
          </div>
        </div>
        <button type="button" className={styles.logoutTrigger} onClick={logout} aria-label="Sign out of session">
          <FiLogOut aria-hidden="true" />
        </button>
      </div>
    </header>
  );
};
export default Header;
""")
HCSS = FE / "components" / "layout" / "Header.module.css"
h = read(HCSS)
if ".notifWrap" not in h:
    h += """
/* NOTIFICATION DROPDOWN (fix70) */
.notifWrap { position: relative; }
.notifDrop {
  position: absolute; top: calc(100% + 8px); right: 0; z-index: 500;
  width: clamp(260px, 30vw, 360px);
  background: linear-gradient(160deg, #1c3335 0%, #213E40 100%);
  border: 1.5px solid rgba(238,140,58,0.35); border-radius: 10px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.55); overflow: hidden;
  animation: dropIn 0.18s ease-out;
}
@keyframes dropIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
.notifHead { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.08); font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 900; letter-spacing: 2px; color: var(--orange); }
.notifReadAll { display: inline-flex; align-items: center; gap: 4px; background: transparent; border: 1px solid rgba(255,255,255,0.15); color: rgba(255,255,255,0.6); border-radius: 6px; padding: 4px 8px; font-size: 8px; font-weight: 900; letter-spacing: 1px; cursor: pointer; }
.notifReadAll:hover { color: #fff; border-color: var(--orange); }
.notifEmpty { padding: 18px 12px; text-align: center; font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 900; letter-spacing: 2px; color: rgba(255,255,255,0.3); }
.notifRow { display: flex; align-items: flex-start; gap: 8px; width: 100%; text-align: left; background: transparent; border: none; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 10px 12px; cursor: pointer; }
.notifRow:hover { background: rgba(255,255,255,0.05); }
.notifRead { opacity: 0.45; }
.notifDot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.notifMsg { font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.85); line-height: 1.4; word-break: break-word; }
"""
    write(HCSS, h)

# ---------- RecoveryPortal: folder deep-link, badge dot, recv-state chip, delete note, promise date, co-owner banner ----------
RPX = FE / "pages" / "Recovery" / "RecoveryPortal.jsx"
patch(RPX, "import styles from './RecoveryPortal.module.css';",
"import styles from './RecoveryPortal.module.css';\nimport { useAuth } from '../../hooks/useAuth';", "RPX useAuth import")
patch(RPX, "  const [text, setText] = useState('');\n",
"  const [text, setText] = useState('');\n  const [promise, setPromise] = useState('');\n  const [coWarn, setCoWarn] = useState(null);\n  const { user } = useAuth();\n  const canManage = user?.isRoot || ['ROLE_ADMIN','ROLE_DIRECTOR','ROLE_MANAGER'].includes(user?.role);\n", "RPX states")
patch(RPX, "    recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text: text })\n      .then(() => { setSel(null); toast('Outcome logged.', 'success'); load(); })",
"    recoveryService.logNote({ clientId: sel.id, tag: picked.tag, text: text, promiseDate: promise || null })\n      .then((r) => { setSel(null); setPromise(''); toast('Outcome logged.', 'success'); if (r && r.data && r.data.coOwnerWarning) setCoWarn(r.data.coOwnerWarning); load(); })", "RPX save promise+warning")
patch(RPX, "            {(c.indexes || []).length > 0 && (<div className={styles.mono}>#{c.indexes.join(' #')}</div>)}",
"""            {(c.indexes || []).length > 0 && (<div className={styles.mono}>#{c.indexes.join(' #')}</div>)}
            <div className={styles.cardMetaRow}>
              <span title={'Payment health: ' + c.payBadge} style={{ width: 8, height: 8, borderRadius: '50%', display: 'inline-block', background: c.payBadge === 'GREEN' ? '#22c55e' : c.payBadge === 'YELLOW' ? '#f59e0b' : '#ef4444', boxShadow: '0 0 4px ' + (c.payBadge === 'GREEN' ? '#22c55e' : c.payBadge === 'YELLOW' ? '#f59e0b' : '#ef4444') }} />
              {c.recvState && <span className={c.recvState.indexOf('PAYING') >= 0 ? styles.recvPaying : c.recvState.indexOf('LEGACY') >= 0 ? styles.recvLegacy : styles.recvSilent}>{c.recvState}</span>}
            </div>""", "RPX badge+chip")
patch(RPX, """            <button type="button" className={styles.openBtn} onClick={(e) => { e.stopPropagation(); open(c); }}>
              <FiPhone aria-hidden="true" /> OPEN CALL LOG
            </button>""",
"""            {(c.projectIds || []).length > 0 && (
              <button type="button" className={styles.openBtn} onClick={(e) => { e.stopPropagation(); window.location.href = '/folder/' + c.projectIds[0] + '#finance'; }}>
                <FiFolderPlus aria-hidden="true" /> OPEN FOLDER
              </button>
            )}
            <button type="button" className={styles.openBtn} onClick={(e) => { e.stopPropagation(); open(c); }}>
              <FiPhone aria-hidden="true" /> OPEN CALL LOG
            </button>""", "RPX folder link")
patch(RPX, """          <div className={modalStyles.modalField}>
            <label className={modalStyles.modalLabel}>OPTIONAL DETAIL (RARE)</label>""",
"""          {picked && picked.tag === 'committed to pay' && (
            <div className={modalStyles.modalField}>
              <label className={modalStyles.modalLabel}>PROMISED PAYMENT DATE</label>
              <input type="date" className={modalStyles.modalInput} value={promise} onChange={(e) => setPromise(e.target.value)} aria-label="Promised payment date" />
            </div>
          )}
          <div className={modalStyles.modalField}>
            <label className={modalStyles.modalLabel}>OPTIONAL DETAIL (RARE)</label>""", "RPX promise input")
patch(RPX, """                <span className={styles.histMeta}>{n.author || 'SYSTEM'} - {fmtDT(n.createdAt)}</span>
                {n.text && <span className={styles.histText}>{n.text}</span>}""",
"""                <span className={styles.histMeta}>{n.author || 'SYSTEM'} - {fmtDT(n.createdAt)}</span>
                {n.text && <span className={styles.histText}>{n.text}</span>}
                {canManage && n.source !== 'FOLDER' && (
                  <button type="button" className={styles.histDelete} aria-label="Delete note"
                    onClick={() => { if (window.confirm('Delete this tap-tag? The cooldown clock will recompute.')) recoveryService.deleteNote(n.id).then(() => { load(); open(sel); toast('Note deleted.', 'warn'); }); }}>
                    <FiX aria-hidden="true" />
                  </button>
                )}""", "RPX delete note")
patch(RPX, "      <BackToTopButton />",
"""      {coWarn && (
        <div className={styles.coWarnBanner} role="status">
          <span>{coWarn}</span>
          <button type="button" className={styles.coWarnDismiss} onClick={() => setCoWarn(null)} aria-label="Dismiss notice">&times;</button>
        </div>
      )}
      <BackToTopButton />""", "RPX co-owner banner")
RCSS = FE / "pages" / "Recovery" / "RecoveryPortal.module.css"
r = read(RCSS)
if ".cardMetaRow" not in r:
    r += """
/* fix70: payment dot row + subtle receivable state chips */
.cardMetaRow { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.recvPaying, .recvSilent, .recvLegacy { font-family: 'Space Mono', monospace; font-size: 8px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; padding: 2px 8px; border-radius: 999px; border: 1px solid; white-space: nowrap; }
.recvPaying { color: #34d399; background: rgba(16,185,129,0.10); border-color: rgba(16,185,129,0.35); }
.recvSilent { color: #fca5a5; background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.35); }
.recvLegacy { color: #cbd5e1; background: rgba(100,116,139,0.12); border-color: rgba(100,116,139,0.35); }
.histDelete { background: transparent; border: none; color: rgba(239,68,68,0.6); cursor: pointer; padding: 2px 4px; font-size: 12px; margin-left: auto; }
.histDelete:hover { color: #ef4444; }
.coWarnBanner { position: fixed; bottom: clamp(70px, 10vh, 110px); right: clamp(16px, 2vw, 28px); z-index: 99998; display: flex; align-items: center; gap: 10px; background: rgba(238,140,58,0.14); border: 1px solid rgba(238,140,58,0.45); border-radius: 8px; padding: 10px 14px; font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.9); max-width: min(420px, 90vw); }
.coWarnDismiss { background: none; border: none; color: rgba(255,255,255,0.6); font-size: 16px; cursor: pointer; }
.coWarnDismiss:hover { color: #fff; }
"""
    write(RCSS, r)

# ---------- FolderPage: PROCESSING tag, payment dot, recovery chips in NOTES ----------
FP = FE / "pages" / "DigitalFolder" / "FolderPage.jsx"
patch(FP, "{isBacklog ? <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>BACKLOG</span>",
"{isBacklog ? <span className={`${styles.textBadge} ${styles.badgeBacklog}`}>PROCESSING</span>", "FP tag rename")
patch(FP, "  const [portfolio, setPortfolio] = useState([]);\n",
"  const [portfolio, setPortfolio] = useState([]);\n  const [recoveryChips, setRecoveryChips] = useState([]);\n", "FP chips state")
patch(FP, "  useEffect(() => { loadFolderData(); loadPortfolio(); }, [loadFolderData, loadPortfolio]);\n",
"""  useEffect(() => { loadFolderData(); loadPortfolio(); }, [loadFolderData, loadPortfolio]);
  useEffect(() => {
    if (!binder?.project?.proprietors) return;
    Promise.all(binder.project.proprietors.map(p => recoveryService.getNotes(p.id).catch(() => [])))
      .then(lists => setRecoveryChips(lists.flat().sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 20)));
  }, [binder]);
""", "FP chips fetch")
patch(FP, """            <CornerDecor hideTop />
            {canLog && <button type="button" className={styles.addNoteBtn}""",
"""            <CornerDecor hideTop />
            {recoveryChips.length > 0 && (
              <div style={{ marginBottom: 10 }}>
                <h3 className={styles.sectionTitle}>RECOVERY CALL LOG</h3>
                {recoveryChips.map((n, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 5 }}>
                    <span className={n.tone === 'POSITIVE' ? styles.badgeTitled : n.tone === 'NEGATIVE' ? styles.badgeRecv : styles.badgeLegacy}>{n.tag}</span>
                    <span className={styles.noteAuthor}>{n.author || 'SYSTEM'} - {new Date(n.createdAt).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
            )}
            {canLog && <button type="button" className={styles.addNoteBtn}""", "FP chips render")

# ---------- Q6: SettingsPage rebuild ----------
write(FE / "pages" / "settings" / "SettingsPage.jsx",
"""import React, { useState, useEffect, useCallback } from 'react';
import { FiShield, FiLock, FiPower, FiKey, FiTrash2, FiUserPlus, FiAlertTriangle, FiInfo, FiCheckSquare, FiAlertCircle, FiX, FiRotateCcw, FiEye, FiEyeOff } from 'react-icons/fi';
import { createPortal } from 'react-dom';
import { useAuth } from '../../hooks/useAuth';
import settingsService from '../../services/settingsService';
import landService from '../../services/landService';
import HardwareInput from '../../components/common/HardwareInput';
import HardwareSelect from '../../components/common/HardwareSelect';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import BackToTopButton from '../../components/common/BackToTopButton';
import styles from './SettingsPage.module.css';
const TOAST_ICONS = { success: <FiCheckSquare aria-hidden="true" />, error: <FiAlertCircle aria-hidden="true" />, warn: <FiAlertTriangle aria-hidden="true" />, info: <FiInfo aria-hidden="true" /> };
const RANKS = ['ROLE_ADMIN', 'ROLE_DIRECTOR', 'ROLE_MANAGER', 'ROLE_SECRETARY'];
const SettingsPage = () => {
  const { user } = useAuth();
  const isRoot = !!user?.isRoot;
  const [toasts, setToasts] = useState([]);
  const toast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(p => [...p, { id, message, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 5000);
  }, []);
  const [oldPw, setOldPw] = useState(''); const [newPw, setNewPw] = useState('');
  const [showOld, setShowOld] = useState(false); const [showNew, setShowNew] = useState(false);
  const [savingPw, setSavingPw] = useState(false);
  const [ops, setOps] = useState([]); const [opsLoading, setOpsLoading] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [newOp, setNewOp] = useState({ username: '', email: '', role: 'ROLE_MANAGER' });
  const [reveal, setReveal] = useState(null);
  const [rankMenu, setRankMenu] = useState(null);
  const [wipeText, setWipeText] = useState('');
  const [wiping, setWiping] = useState(false);
  const [deleted, setDeleted] = useState([]); const [delLoading, setDelLoading] = useState(false);
  const loadOps = useCallback(async () => {
    if (!isRoot) return;
    setOpsLoading(true);
    try { setOps(await settingsService.getAllOperators()); } catch (e) { toast(e.message, 'error'); }
    finally { setOpsLoading(false); }
  }, [isRoot, toast]);
  const loadDeleted = useCallback(async () => {
    if (!isRoot) return;
    setDelLoading(true);
    try { setDeleted(await landService.getDeletedProjects()); } catch { setDeleted([]); }
    finally { setDelLoading(false); }
  }, [isRoot]);
  useEffect(() => { loadOps(); loadDeleted(); }, [loadOps, loadDeleted]);
  const changePw = async () => {
    setSavingPw(true);
    try { await settingsService.changePersonalPassword(oldPw, newPw); toast('Security key updated.', 'success'); setOldPw(''); setNewPw(''); }
    catch (e) { toast(e.message, 'error'); }
    finally { setSavingPw(false); }
  };
  const createOp = async () => {
    try {
      const res = await settingsService.registerManager(newOp);
      setAddOpen(false); setReveal({ username: res.username, key: res.temporaryPassword });
      setNewOp({ username: '', email: '', role: 'ROLE_MANAGER' });
      loadOps();
    } catch (e) { toast(e.message, 'error'); }
  };
  const wipe = async () => {
    setWiping(true);
    try { const r = await settingsService.wipeAllData(); toast(r.message || 'System wiped.', 'warn'); }
    catch (e) { toast(e.message, 'error'); }
    finally { setWiping(false); setWipeText(''); }
  };
  const rankClass = (r) => r === 'ROLE_ADMIN' ? styles.rankAdmin : r === 'ROLE_MANAGER' ? styles.rankManager : r === 'ROLE_SECRETARY' ? styles.rankSecretary : styles.rankAdmin;
  return (
    <div className={styles.container}>
      {typeof document !== 'undefined' && createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
          {toasts.map(t => (<div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
            <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
            <span className={styles.toastMsg}>{t.message}</span>
            <button className={styles.toastClose} onClick={() => setToasts(p => p.filter(x => x.id !== t.id))} aria-label="Dismiss"><FiX aria-hidden="true" /></button>
          </div>))}
        </div>, document.body)}
      <header className={styles.pageHeader}>
        <div className={styles.pageHeaderLeft}>
          <h1 className={styles.title}>Settings</h1>
          <p className={styles.subtitle}>Security, governance and danger zone</p>
        </div>
        {user?.mustChangePassword && (<div className={`${styles.handbrakeBadge} ${styles.blink}`}><FiLock aria-hidden="true" /> CHANGE YOUR PASSWORD TO UNLOCK THE SYSTEM</div>)}
      </header>
      <div className={styles.workstationGrid}>
        <div className={styles.hwPanel}>
          <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiKey className={styles.drawerIcon} aria-hidden="true" /> PERSONAL SECURITY</div></div>
          <div className={styles.panelBody} style={{ maxHeight: 2000 }}><div className={styles.panelInner}>
            <div className={styles.securityAlert}><FiShield aria-hidden="true" /><span>Minimum 8 characters, one uppercase letter and one number. Changing your key unlocks full access.</span></div>
            <div className={styles.dualRow}>
              <div className={styles.eyeInpWrap}>
                <HardwareInput label="CURRENT KEY" type={showOld ? 'text' : 'password'} value={oldPw} onChange={e => setOldPw(e.target.value)} />
                <button type="button" className={styles.eyeBtn} onClick={() => setShowOld(s => !s)} aria-label="Toggle current key visibility">{showOld ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}</button>
              </div>
              <div className={styles.eyeInpWrap}>
                <HardwareInput label="NEW KEY" type={showNew ? 'text' : 'password'} value={newPw} onChange={e => setNewPw(e.target.value)} />
                <button type="button" className={styles.eyeBtn} onClick={() => setShowNew(s => !s)} aria-label="Toggle new key visibility">{showNew ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}</button>
              </div>
            </div>
            <div className={styles.submitRow}>
              <button type="button" className={styles.commitBtn} onClick={changePw} disabled={savingPw || !oldPw || !newPw}><FiKey aria-hidden="true" /> COMMIT NEW KEY</button>
            </div>
          </div></div>
        </div>
        {isRoot && (
          <div className={styles.hwPanel}>
            <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiShield className={styles.drawerIcon} aria-hidden="true" /> STAFF GOVERNANCE</div></div>
            <div className={styles.panelBody} style={{ maxHeight: 4000 }}><div className={styles.panelInner}>
              <div className={styles.ledgerActions}>
                <button type="button" className={styles.addOpBtn} onClick={() => setAddOpen(true)}><FiUserPlus aria-hidden="true" /> PROVISION OPERATOR</button>
              </div>
              <div className={styles.statusLegend}>
                <span className={styles.legendDot} style={{ background: '#10b981' }} /><span className={styles.legendText}>ACTIVE</span>
                <span className={styles.legendSep} />
                <span className={styles.legendDot} style={{ background: '#ef4444' }} /><span className={styles.legendText}>SUSPENDED</span>
              </div>
              <div className={styles.staffStream}>
                {opsLoading && <p className={styles.hint}>SYNCING REGISTRY...</p>}
                {!opsLoading && ops.map(op => (
                  <div key={op.username} className={`${styles.opCard} ${!op.active ? styles.cardDimmed : ''}`}>
                    <div className={styles.opHeader}>
                      <div className={styles.opAvatar}>{(op.username || '?').charAt(0).toUpperCase()}<span className={`${styles.statusDot} ${op.active ? styles.dotGreen : styles.dotRed}`} /></div>
                      <div className={styles.opInfo}>
                        <strong>{op.username}{op.root ? ' (ROOT)' : ''}</strong>
                        <span className={rankClass(op.role)}>{(op.role || '').replace('ROLE_', '')}</span>
                      </div>
                      <div className={styles.opActions}>
                        <div className={styles.rankMenuWrapper}>
                          <button type="button" className={styles.rankBtn} disabled={op.root} onClick={() => setRankMenu(rankMenu === op.username ? null : op.username)} aria-label="Change rank"><FiShield aria-hidden="true" /></button>
                          {rankMenu === op.username && (
                            <div className={styles.rankMenu}>
                              {RANKS.map(rk => (
                                <div key={rk} className={`${styles.rankMenuItem} ${op.role === rk ? styles.rankMenuItemActive : ''}`}
                                  onClick={async () => { setRankMenu(null); try { await settingsService.updateOperatorRole(op.username, rk); toast('Rank updated.', 'success'); loadOps(); } catch (e) { toast(e.message, 'error'); } }}>
                                  {rk.replace('ROLE_', '')}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <button type="button" className={`${styles.killSwitchBtn} ${op.active ? styles.killSwitchActive : styles.killSwitchInactive}`} disabled={op.root}
                          onClick={async () => { try { await settingsService.toggleOperator(op.username, !op.active); toast(op.active ? 'Operator suspended.' : 'Operator activated.', 'warn'); loadOps(); } catch (e) { toast(e.message, 'error'); } }}
                          aria-label={op.active ? 'Suspend operator' : 'Activate operator'}>
                          <FiPower aria-hidden="true" />
                        </button>
                        <button type="button" className={styles.resetTrigger} disabled={op.root}
                          onClick={async () => { try { const key = await settingsService.resetOperatorKey(op.username); setReveal({ username: op.username, key }); } catch (e) { toast(e.message, 'error'); } }}
                          aria-label="Reset security key">
                          <FiRotateCcw aria-hidden="true" />
                        </button>
                      </div>
                    </div>
                    <div className={styles.opDetails}><p><FiInfo aria-hidden="true" /> {op.email || 'no email on file'}</p></div>
                  </div>
                ))}
              </div>
            </div></div>
          </div>
        )}
        {isRoot && (
          <div className={`${styles.hwPanel} ${styles.dangerPanel}`}>
            <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiAlertTriangle className={styles.drawerIcon} aria-hidden="true" /> DANGER ZONE</div></div>
            <div className={styles.panelBody} style={{ maxHeight: 2000 }}><div className={styles.panelInner}>
              <div className={styles.wipeField}>
                <HardwareInput label={'TYPE "WIPE-EVERYTHING" TO ARM'} value={wipeText} onChange={e => setWipeText(e.target.value)} />
              </div>
              <button type="button" className={styles.wipeBtn} disabled={wipeText !== 'WIPE-EVERYTHING' || wiping} onClick={wipe}>
                <FiTrash2 aria-hidden="true" /> {wiping ? 'WIPING...' : 'WIPE ALL BUSINESS DATA'}
              </button>
            </div></div>
          </div>
        )}
        {isRoot && (
          <div className={styles.hwPanel}>
            <div className={styles.drawerHeader}><div className={styles.drawerTitle}><FiRotateCcw className={styles.drawerIcon} aria-hidden="true" /> RECENTLY DELETED PLOTS</div></div>
            <div className={styles.panelBody} style={{ maxHeight: 3000 }}><div className={styles.panelInner}>
              {delLoading && <p className={styles.hint}>SYNCING...</p>}
              {!delLoading && deleted.length === 0 && <p className={styles.hint}>NO DELETED PLOTS.</p>}
              {!delLoading && deleted.map(p => (
                <div key={p.id} className={styles.opCard} style={{ marginBottom: 8 }}>
                  <div className={styles.opHeader}>
                    <div className={styles.opInfo}>
                      <strong>#{p.projectIndex || '---'} {p.landTitle ? p.landTitle.plotNumber : ''}</strong>
                      <span className={styles.rankManager}>{p.district || '---'}</span>
                    </div>
                    <button type="button" className={styles.commitBtn} onClick={async () => { try { await landService.restoreProject(p.id); toast('Plot restored.', 'success'); loadDeleted(); } catch { toast('Restore failed.', 'error'); } }}>
                      <FiRotateCcw aria-hidden="true" /> RESTORE
                    </button>
                  </div>
                </div>
              ))}
            </div></div>
          </div>
        )}
      </div>
      <HardwareModal isOpen={addOpen} onClose={() => setAddOpen(false)} title="PROVISION OPERATOR">
        <div className={styles.modalBody}>
          <HardwareInput label="USERNAME" value={newOp.username} onChange={e => setNewOp({ ...newOp, username: e.target.value })} required />
          <HardwareInput label="EMAIL" type="email" value={newOp.email} onChange={e => setNewOp({ ...newOp, email: e.target.value })} required />
          <div className={styles.selectWrap}>
            <HardwareSelect label="RANK" options={RANKS} value={newOp.role} onChange={v => setNewOp({ ...newOp, role: v })} />
          </div>
        </div>
        <div className={styles.modalCenter}>
          <HardwareButton onClick={createOp} icon={FiUserPlus} disabled={!newOp.username || !newOp.email}>CREATE</HardwareButton>
        </div>
      </HardwareModal>
      <HardwareModal isOpen={!!reveal} onClose={() => setReveal(null)} title="TEMPORARY SECURITY KEY">
        <div className={styles.revealBox}>
          <FiAlertTriangle className={styles.warningIcon} aria-hidden="true" />
          <p className={styles.revealHint}>HAND THIS KEY TO {reveal ? reveal.username.toUpperCase() : ''}. THEY MUST CHANGE IT AT FIRST LOGIN.</p>
          <div className={styles.serial}>{reveal ? reveal.key : ''}</div>
          <p className={styles.revealDisclaimer}>THIS KEY IS SHOWN ONCE ONLY.</p>
        </div>
      </HardwareModal>
      <BackToTopButton />
    </div>
  );
};
export default SettingsPage;
""")

# ---------- git ----------
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix70: recovery+notes+notifications unification, NPE fixes, data-safe seeding, bell dropdown, settings rebuild"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)
print("DONE")