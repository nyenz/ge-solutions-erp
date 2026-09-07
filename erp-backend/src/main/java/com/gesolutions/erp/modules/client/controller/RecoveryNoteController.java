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
