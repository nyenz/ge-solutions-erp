// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ProblemService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.service.RecoveryStateService;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectProblem;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.ProjectProblemRepository;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

/**
 * fix289 (David, 5 Nov 2026): the Problems subsystem.
 *  - A problem sits beside a project (and, for phone / NIN problems, beside that client). It never changes the project.
 *  - Every problem writes a note in the project's Notes (topic PROBLEM), and so does solving it.
 *  - The solution decides where it goes next: SITE_VISIT (the Site Visits list), CALL (call the client), OFFICE (fix the
 *    details in the office), LATER (decide later).
 *  - The words typed under OTHER are remembered and offered again next time.
 *  - The old one-switch "Problem" flag on a project is kept as it was; it shows here as a FLAGGED problem.
 */
@Service
@RequiredArgsConstructor
public class ProblemService {

    public record Kind(String code, String label, String solution, boolean person) {}

    /** The fixed list (David): most legacy problems are one of these. Anything else is OTHER with its own words. */
    public static final List<Kind> KINDS = List.of(
            new Kind("NO_NIN", "No NIN", "CALL", true),
            new Kind("MISSING_PHONE", "Missing telephone", "SITE_VISIT", true),
            new Kind("MISSING_INVOICE", "Missing invoice number", "OFFICE", false),
            new Kind("MISSING_CONTRACT", "Missing contract number", "OFFICE", false),
            new Kind("WRONG_NUMBER", "Wrong number", "OFFICE", false),
            new Kind("SAME_NUMBER", "Same number as another project", "OFFICE", false),
            new Kind("TITLE_DETAILS", "Problem with title details", "SITE_VISIT", false),
            new Kind("LOCATION", "Problem with location", "SITE_VISIT", false),
            new Kind("FLAGGED", "Flagged problem (stops the hand-over)", "LATER", false),
            new Kind("OTHER", "Other", "LATER", false));

    public static final List<String> SOLUTIONS = List.of("SITE_VISIT", "CALL", "OFFICE", "LATER");
    public static final Map<String, String> SOLUTION_WORDS = Map.of(
            "SITE_VISIT", "Needs a site visit", "CALL", "Call the client", "OFFICE", "Fix in the office", "LATER", "Decide later");
    public static final int MAX_LABEL = 80;
    public static final int MAX_DETAIL = 1000;

    private final ProjectProblemRepository problemRepo;
    private final LandProjectRepository projectRepo;
    private final FollowUpRepository followUpRepo;
    private final AuditService auditService;
    private final NotificationService notificationService;
    private final RecoveryStateService recoveryState;

    public static Kind kind(String code) {
        for (Kind k : KINDS) if (k.code().equals(code)) return k;
        return null;
    }

    private static String op() { return AuditService.currentOperator(); }

    private static String clean(String s, int max) {
        if (s == null) return null;
        String t = s.trim().replaceAll("\\s+", " ");
        if (t.isEmpty()) return null;
        return t.length() > max ? t.substring(0, max) : t;
    }

    private static String where(LandProject p) {
        String plot = p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null ? "plot " + p.getLandTitle().getPlotNumber() + ", " : "";
        return plot + "project #" + p.getProjectIndex();
    }

    /** One row to add (from a form, the folder, or a MISSING tick). */
    public record NewProblem(String kind, String label, String detail, String solution, UUID clientId, UUID linkedProjectId, boolean auto) {}

    /**
     * Adds problems to one project in the caller's transaction. The same open problem (same kind, words and person) is
     * not added twice. Each one writes a PROBLEM note. notify=false when the caller sends one alert for all of them.
     */
    @Transactional
    public List<ProjectProblem> addAll(LandProject p, List<NewProblem> rows, boolean notify) {
        List<ProjectProblem> made = new ArrayList<>();
        if (p == null || rows == null || rows.isEmpty()) return made;
        List<ProjectProblem> existing = problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId());
        for (NewProblem r : rows) {
            Kind k = kind(r.kind() == null ? "" : r.kind().trim().toUpperCase(Locale.ROOT));
            if (k == null) throw new BusinessException("PROBLEM_KIND_INVALID: \"" + r.kind() + "\" is not a problem type.");
            String label = "OTHER".equals(k.code()) ? clean(r.label(), MAX_LABEL) : k.label();
            if (label == null) throw new BusinessException("PROBLEM_WORDS_REQUIRED: Write what the other problem is.");
            String detail = clean(r.detail(), MAX_DETAIL);
            String sol = r.solution() == null || r.solution().isBlank() ? k.solution() : r.solution().trim().toUpperCase(Locale.ROOT);
            if (!SOLUTIONS.contains(sol)) throw new BusinessException("SOLUTION_INVALID: \"" + r.solution() + "\" is not a solution.");
            boolean dup = existing.stream().anyMatch(e -> e.isOpen() && e.getKind().equals(k.code()) && e.getLabel().equalsIgnoreCase(label)
                    && Objects.equals(e.getClientId(), r.clientId()) && Objects.equals(e.getLinkedProjectId(), r.linkedProjectId()));
            if (dup) continue;
            ProjectProblem pp = problemRepo.save(ProjectProblem.builder().projectId(p.getId()).clientId(r.clientId()).kind(k.code())
                    .label(label).detail(detail).solution(sol).linkedProjectId(r.linkedProjectId()).autoAdded(r.auto())
                    .createdBy(op()).createdAt(LocalDateTime.now()).build());
            existing.add(pp);
            made.add(pp);
            followUpRepo.save(FollowUpLog.builder().projectId(p.getId()).clientId(r.clientId()).topic("PROBLEM")
                    .notes("[PROBLEM] " + label + (detail != null ? ": " + detail : "") + " (" + SOLUTION_WORDS.get(sol) + ")")
                    .recordedBy(op()).build());
            auditService.logActionAfterCommit("PROBLEM_ADDED", "Operator [" + op() + "] added problem \"" + label + "\" ("
                    + SOLUTION_WORDS.get(sol) + ") on " + where(p) + ".");
        }
        if (notify && !made.isEmpty()) alertAdded(p, made);
        return made;
    }

    /** One alert for a group of new problems (a legacy entry can bring three at once), plus one for a site visit. */
    public void alertAdded(LandProject p, List<ProjectProblem> made) {
        if (made.isEmpty()) return;
        List<String> words = made.stream().map(ProjectProblem::getLabel).distinct().toList();
        notificationService.emitToAudience("PROBLEM_ADDED", (made.size() == 1 ? "Problem on " : made.size() + " problems on ") + where(p)
                + ": " + String.join(", ", words) + ".", "PROJECT", p.getId());
        if (made.stream().anyMatch(m -> "SITE_VISIT".equals(m.getSolution()))) {
            notificationService.emitToAudience("SITE_VISIT_NEEDED", where(p) + " needs a site visit (see Problems > Site visits).", "PROJECT", p.getId());
        }
    }

    @Transactional
    public ProjectProblem add(UUID projectId, NewProblem r) {
        LandProject p = projectRepo.findById(projectId).orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        if (p.isDeleted()) throw new BusinessException("PROJECT_DELETED: This project is deleted. Restore it first.");
        if (r.clientId() != null && !personOf(p, r.clientId())) {
            throw new BusinessException("CLIENT_NOT_ON_PROJECT: That person is not a client or owner of this project.");
        }
        List<ProjectProblem> made = addAll(p, List.of(r), true);
        if (made.isEmpty()) throw new BusinessException("PROBLEM_ALREADY_OPEN: This problem is already open on this project.");
        return made.get(0);
    }

    private static boolean personOf(LandProject p, UUID clientId) {
        return p.getClients().stream().anyMatch(c -> clientId.equals(c.getId())) || p.getProprietors().stream().anyMatch(c -> clientId.equals(c.getId()));
    }

    /** Change the solution or the words of an open problem. */
    @Transactional
    public ProjectProblem update(UUID id, String solution, String detail) {
        ProjectProblem pp = problemRepo.findById(id).orElseThrow(() -> new BusinessException("PROBLEM_NOT_FOUND: That problem is gone. Reload the page."));
        if (!pp.isOpen()) throw new BusinessException("PROBLEM_SOLVED: This problem is already solved.");
        LandProject p = projectRepo.findById(pp.getProjectId()).orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        String before = pp.getSolution();
        if (solution != null && !solution.isBlank()) {
            String sol = solution.trim().toUpperCase(Locale.ROOT);
            if (!SOLUTIONS.contains(sol)) throw new BusinessException("SOLUTION_INVALID: \"" + solution + "\" is not a solution.");
            pp.setSolution(sol);
        }
        if (detail != null) pp.setDetail(clean(detail, MAX_DETAIL));
        problemRepo.save(pp);
        if (!before.equals(pp.getSolution())) {
            followUpRepo.save(FollowUpLog.builder().projectId(p.getId()).clientId(pp.getClientId()).topic("PROBLEM")
                    .notes("[PROBLEM] " + pp.getLabel() + ": now " + SOLUTION_WORDS.get(pp.getSolution()) + ".").recordedBy(op()).build());
            if ("SITE_VISIT".equals(pp.getSolution())) {
                notificationService.emitToAudience("SITE_VISIT_NEEDED", where(p) + " needs a site visit (see Problems > Site visits).", "PROJECT", p.getId());
            }
        }
        auditService.logActionAfterCommit("PROBLEM_UPDATED", "Operator [" + op() + "] changed problem \"" + pp.getLabel() + "\" on "
                + where(p) + " (" + SOLUTION_WORDS.get(pp.getSolution()) + ").");
        return pp;
    }

    /** Mark a problem solved, with what was done. Solving a FLAGGED problem also clears the old flag on the project. */
    @Transactional
    public ProjectProblem solve(UUID id, String note) {
        String why = clean(note, MAX_DETAIL);
        if (why == null || why.length() < 3) throw new BusinessException("REASON_REQUIRED: Write what was done to solve it (at least 3 characters).");
        ProjectProblem pp = problemRepo.findById(id).orElseThrow(() -> new BusinessException("PROBLEM_NOT_FOUND: That problem is gone. Reload the page."));
        if (!pp.isOpen()) throw new BusinessException("PROBLEM_SOLVED: Someone already marked this problem solved. Reload the page.");
        LandProject p = projectRepo.findById(pp.getProjectId()).orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        pp.setStatus("SOLVED"); pp.setSolvedBy(op()); pp.setSolvedAt(LocalDateTime.now()); pp.setSolvedNote(why);
        problemRepo.save(pp);
        if ("FLAGGED".equals(pp.getKind()) && p.isProblem()) {
            p.setProblem(false); p.setProblemBy(null); p.setProblemAt(null); p.setProblemNote(null);
            projectRepo.save(p);
        }
        followUpRepo.save(FollowUpLog.builder().projectId(p.getId()).clientId(pp.getClientId()).topic("PROBLEM")
                .notes("[PROBLEM SOLVED] " + pp.getLabel() + ": " + why).recordedBy(op()).build());
        auditService.logActionAfterCommit("PROBLEM_SOLVED", "Operator [" + op() + "] solved problem \"" + pp.getLabel() + "\" on " + where(p) + ": " + why + ".");
        notificationService.emitToAudience("PROBLEM_SOLVED", "Problem \"" + pp.getLabel() + "\" on " + where(p) + " solved by " + op() + ".", "PROJECT", p.getId());
        return pp;
    }

    /** Director and up: take away a problem that was added by mistake. The note stays in the Notes; the audit keeps the reason. */
    @Transactional
    public void remove(UUID id, String reason) {
        String why = clean(reason, 500);
        if (why == null || why.length() < 5) throw new BusinessException("REASON_REQUIRED: Write why this problem is removed (at least 5 characters).");
        ProjectProblem pp = problemRepo.findById(id).orElseThrow(() -> new BusinessException("PROBLEM_NOT_FOUND: That problem is gone. Reload the page."));
        LandProject p = projectRepo.findById(pp.getProjectId()).orElse(null);
        problemRepo.delete(pp);
        if (p != null) {
            followUpRepo.save(FollowUpLog.builder().projectId(p.getId()).clientId(pp.getClientId()).topic("PROBLEM")
                    .notes("[PROBLEM REMOVED] " + pp.getLabel() + ": " + why).recordedBy(op()).build());
        }
        auditService.logActionAfterCommit("PROBLEM_REMOVED", "Operator [" + op() + "] removed problem \"" + pp.getLabel() + "\" from "
                + (p != null ? where(p) : "a project") + ": " + why + ".");
    }

    /** The old Problem switch on the folder: flagging opens a FLAGGED problem, clearing solves it. */
    @Transactional
    public void followFlag(LandProject p, boolean flagged, String why) {
        if (flagged) {
            if (!problemRepo.existsByProjectIdAndKindAndStatus(p.getId(), "FLAGGED", "OPEN")) {
                problemRepo.save(ProjectProblem.builder().projectId(p.getId()).kind("FLAGGED").label(kind("FLAGGED").label())
                        .detail(clean(why, MAX_DETAIL)).solution("LATER").createdBy(op()).createdAt(LocalDateTime.now()).build());
            }
        } else {
            for (ProjectProblem pp : problemRepo.findByProjectIdOrderByCreatedAtDesc(p.getId())) {
                if (pp.isOpen() && "FLAGGED".equals(pp.getKind())) {
                    pp.setStatus("SOLVED"); pp.setSolvedBy(op()); pp.setSolvedAt(LocalDateTime.now()); pp.setSolvedNote(clean(why, MAX_DETAIL));
                    problemRepo.save(pp);
                }
            }
        }
    }

    /** Once at start: projects flagged with the old switch get their FLAGGED problem (so they show on the Problems list). */
    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void bringOldFlags() {
        try {
            for (LandProject p : projectRepo.findAll()) {
                if (!p.isProblem() || p.isDeleted()) continue;
                if (problemRepo.existsByProjectIdAndKindAndStatus(p.getId(), "FLAGGED", "OPEN")) continue;
                problemRepo.save(ProjectProblem.builder().projectId(p.getId()).kind("FLAGGED").label(kind("FLAGGED").label())
                        .detail(clean(p.getProblemNote(), MAX_DETAIL)).solution("LATER").autoAdded(true)
                        .createdBy(p.getProblemBy() != null ? p.getProblemBy() : "SYSTEM")
                        .createdAt(p.getProblemAt() != null ? p.getProblemAt() : LocalDateTime.now()).build());
            }
        } catch (Exception e) {
            System.err.println(">>> [PROBLEMS] Old flags not brought over this time: " + e.getMessage());
        }
    }

    /** The words typed under OTHER before (the list that remembers), most used first. */
    public List<String> remembered() {
        List<String> out = new ArrayList<>();
        for (String s : problemRepo.rememberedOtherLabels()) if (s != null && !out.contains(s)) out.add(s);
        return out.size() > 60 ? out.subList(0, 60) : out;
    }

    public boolean hasOpen(UUID projectId, String kind) {
        return projectId != null && problemRepo.existsByProjectIdAndKindAndStatus(projectId, kind, "OPEN");
    }

    public Map<UUID, Long> openCountPerProject() {
        Map<UUID, Long> m = new HashMap<>();
        for (Object[] r : problemRepo.openCountPerProject()) m.put((UUID) r[0], ((Number) r[1]).longValue());
        return m;
    }

    /** A problem row for the pages, with the project and the person around it. */
    public Map<String, Object> row(ProjectProblem pp, LandProject p, Map<UUID, Client> people) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", pp.getId()); m.put("projectId", pp.getProjectId()); m.put("kind", pp.getKind()); m.put("label", pp.getLabel());
        m.put("detail", pp.getDetail()); m.put("solution", pp.getSolution()); m.put("status", pp.getStatus());
        m.put("autoAdded", pp.isAutoAdded()); m.put("createdBy", pp.getCreatedBy()); m.put("createdAt", pp.getCreatedAt());
        m.put("solvedBy", pp.getSolvedBy()); m.put("solvedAt", pp.getSolvedAt()); m.put("solvedNote", pp.getSolvedNote());
        m.put("linkedProjectId", pp.getLinkedProjectId()); m.put("clientId", pp.getClientId());
        if (pp.getLinkedProjectId() != null) projectRepo.findById(pp.getLinkedProjectId()).ifPresent(o -> m.put("linkedProjectIndex", o.getProjectIndex()));
        if (p != null) {
            m.put("projectIndex", p.getProjectIndex());
            m.put("plotNumber", p.getLandTitle() != null ? p.getLandTitle().getPlotNumber() : null);
            m.put("block", p.getLandTitle() != null ? p.getLandTitle().getBlock() : null);
            m.put("projectType", p.getProjectType());
            m.put("district", p.getDistrict()); m.put("county", p.getCounty()); m.put("subCounty", p.getSubCounty());
            m.put("parish", p.getParish()); m.put("village", p.getVillage());
            m.put("projectDeleted", p.isDeleted());
            Client first = p.getClients().stream().min(Comparator.comparing(c -> String.valueOf(c.getFullName()))).orElse(null);
            m.put("clientName", first != null ? first.getFullName() : null);
            m.put("clientPhone", first != null ? first.getPhone() : null);
        }
        if (pp.getClientId() != null) {
            Client c = people.get(pp.getClientId());
            if (c != null) { m.put("personName", c.getFullName()); m.put("personPhone", c.getPhone()); }
        }
        return m;
    }

    private Map<UUID, Client> peopleOf(Collection<LandProject> ps) {
        Map<UUID, Client> m = new HashMap<>();
        for (LandProject p : ps) {
            p.getClients().forEach(c -> m.put(c.getId(), c));
            p.getProprietors().forEach(c -> m.put(c.getId(), c));
        }
        return m;
    }

    /** The Problems list (open, solved or all), newest first. */
    @Transactional(readOnly = true)
    public List<Map<String, Object>> list(String status, UUID projectId, UUID clientId) {
        List<ProjectProblem> rows = projectId != null ? problemRepo.findByProjectIdOrderByCreatedAtDesc(projectId)
                : clientId != null ? problemRepo.findByClientIdOrderByCreatedAtDesc(clientId)
                : "ALL".equalsIgnoreCase(status) ? problemRepo.findAllByOrderByCreatedAtDesc()
                : problemRepo.findByStatusOrderByCreatedAtDesc("SOLVED".equalsIgnoreCase(status) ? "SOLVED" : "OPEN");
        if (projectId != null && status != null && !"ALL".equalsIgnoreCase(status)) {
            String want = "SOLVED".equalsIgnoreCase(status) ? "SOLVED" : "OPEN";
            rows = rows.stream().filter(r -> want.equals(r.getStatus())).toList();
        }
        Map<UUID, LandProject> ps = new HashMap<>();
        for (ProjectProblem r : rows) ps.computeIfAbsent(r.getProjectId(), k -> projectRepo.findById(k).orElse(null));
        ps.values().removeIf(Objects::isNull);
        Map<UUID, Client> people = peopleOf(ps.values());
        List<Map<String, Object>> out = new ArrayList<>();
        for (ProjectProblem r : rows) {
            LandProject p = ps.get(r.getProjectId());
            if (p == null || (p.isDeleted() && projectId == null)) continue;   // a deleted project's problems wait for its restore
            out.add(row(r, p, people));
        }
        return out;
    }

    /**
     * The Site Visits list: one row per project, joining (1) open problems whose solution is a site visit and (2) clients
     * that Recovery says need a visit (missed calls). A project that needs a visit for three reasons is ONE visit.
     */
    @Transactional(readOnly = true)
    public List<Map<String, Object>> siteVisits() {
        Map<UUID, Map<String, Object>> visits = new LinkedHashMap<>();
        Map<UUID, LandProject> ps = new HashMap<>();
        for (ProjectProblem pp : problemRepo.findByStatusOrderByCreatedAtDesc("OPEN")) {
            if (!"SITE_VISIT".equals(pp.getSolution())) continue;
            LandProject p = ps.computeIfAbsent(pp.getProjectId(), k -> projectRepo.findById(k).orElse(null));
            if (p == null || p.isDeleted()) continue;
            reasonsOf(visits, p).add(pp.getLabel() + (pp.getDetail() != null ? ": " + pp.getDetail() : ""));
        }
        try {
            LocalDateTime now = LocalDateTime.now();
            RecoveryStateService.Snapshot snap = recoveryState.load();
            for (Map.Entry<UUID, List<LandProject>> e : snap.projects().entrySet()) {
                List<RecoveryNote> ns = snap.notesOf(e.getKey());
                if (!recoveryState.siteVisit(ns, now)) continue;
                for (LandProject p : e.getValue()) {
                    if (p.isDeleted() || !RecoveryStateService.counts(p, now)) continue;
                    reasonsOf(visits, p).add("Recovery: the client missed " + RecoveryStateService.SITE_VISIT_MISS_THRESHOLD + " calls on different days");
                }
            }
        } catch (Exception ignore) { /* the problem visits still show */ }
        List<Map<String, Object>> out = new ArrayList<>(visits.values());
        out.sort(Comparator.comparing((Map<String, Object> m) -> String.valueOf(m.get("district")))
                .thenComparing(m -> String.valueOf(m.get("subCounty"))).thenComparing(m -> String.valueOf(m.get("village"))));
        return out;
    }

    @SuppressWarnings("unchecked")
    private List<String> reasonsOf(Map<UUID, Map<String, Object>> visits, LandProject p) {
        Map<String, Object> m = visits.computeIfAbsent(p.getId(), k -> {
            Map<String, Object> v = new LinkedHashMap<>();
            v.put("projectId", p.getId()); v.put("projectIndex", p.getProjectIndex());
            v.put("plotNumber", p.getLandTitle() != null ? p.getLandTitle().getPlotNumber() : null);
            v.put("district", p.getDistrict()); v.put("county", p.getCounty()); v.put("subCounty", p.getSubCounty());
            v.put("parish", p.getParish()); v.put("village", p.getVillage());
            Client first = p.getClients().stream().min(Comparator.comparing(c -> String.valueOf(c.getFullName()))).orElse(null);
            v.put("clientName", first != null ? first.getFullName() : null);
            v.put("clientPhone", first != null ? first.getPhone() : null);
            v.put("reasons", new ArrayList<String>());
            return v;
        });
        List<String> r = (List<String>) m.get("reasons");
        return new AbstractList<>() {   // adds only reasons not already listed
            @Override public String get(int i) { return r.get(i); }
            @Override public int size() { return r.size(); }
            @Override public boolean add(String s) { if (r.contains(s)) return false; return r.add(s); }
        };
    }
}
