package com.gesolutions.erp.modules.client.controller;
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
                for (Object s : p.getStages()) {
                    if (s instanceof com.gesolutions.erp.modules.land.model.ProjectStage) {
                        if (!((com.gesolutions.erp.modules.land.model.ProjectStage) s).isCompleted()) return true;
                    }
                }
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
        if (a == null) return b;
        if (b == null) return a;
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
            List<LandProject> ps = projectsOf(c);
            if (locked(c, now) || !qualifies(ps)) continue;
            out.add(clientDto(c, now, ps));
        }
        out.sort((x, y) -> {
            Integer px = (Integer) x.get("priority");
            Integer py = (Integer) y.get("priority");
            int p = px.compareTo(py);
            if (p != 0) return p;
            LocalDateTime a = (LocalDateTime) x.get("lastContactedAt");
            LocalDateTime b = (LocalDateTime) y.get("lastContactedAt");
            if (a == null && b == null) return 0;
            if (a == null) return -1;
            if (b == null) return 1;
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
            if (Integer.valueOf(1).equals(d.get("priority"))) p1++;
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
                m.put("id", n.getId()); m.put("tag", n.getTag());
                m.put("tone", n.getTone()); m.put("text", n.getText());
                m.put("countsAsAttempt", n.isCountsAsAttempt());
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
