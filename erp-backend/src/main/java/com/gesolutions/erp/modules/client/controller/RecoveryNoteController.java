package com.gesolutions.erp.modules.client.controller;

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
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.gesolutions.erp.modules.land.repository.LandProjectRepository projectRepo;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.gesolutions.erp.common.audit.AuditService auditService;

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
