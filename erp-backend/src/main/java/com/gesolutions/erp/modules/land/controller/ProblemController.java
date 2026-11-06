// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/ProblemController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.ProjectProblem;
import com.gesolutions.erp.modules.land.service.ProblemService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * fix289 (David): the Problems subsystem. Secretary and up see, add, change and solve problems; removing one (added by
 * mistake) is Director and Admin only. The Employee adds problems only through New Project (ticks), not here.
 */
@RestController
@RequestMapping("/api/v1/problems")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class ProblemController {

    private final ProblemService problems;

    /** The fixed problem types, the solutions, and the words typed under OTHER before (the list that remembers). */
    @GetMapping("/kinds")
    @PreAuthorize("isAuthenticated()")
    public Map<String, Object> kinds() {
        List<Map<String, Object>> ks = new ArrayList<>();
        for (ProblemService.Kind k : ProblemService.KINDS) {
            if ("FLAGGED".equals(k.code())) continue;   // made by the folder's PROBLEM switch, not picked
            ks.add(Map.of("code", k.code(), "label", k.label(), "solution", k.solution(), "person", k.person(),
                    "fix", ProblemService.fixFields(k.code())));   // fix291: the real values asked for when it is solved
        }
        List<Map<String, String>> sols = new ArrayList<>();
        for (String s : ProblemService.SOLUTIONS) sols.add(Map.of("code", s, "label", ProblemService.SOLUTION_WORDS.get(s)));
        return Map.of("kinds", ks, "solutions", sols, "remembered", problems.remembered());
    }

    @GetMapping
    public List<Map<String, Object>> list(@RequestParam(value = "status", required = false) String status,
                                          @RequestParam(value = "projectId", required = false) UUID projectId,
                                          @RequestParam(value = "clientId", required = false) UUID clientId) {
        return problems.list(status, projectId, clientId);
    }

    /** Open problems per project (the tags on the Ledger). */
    @GetMapping("/open-counts")
    public Map<UUID, Long> openCounts() {
        return problems.openCountPerProject();
    }

    @GetMapping("/site-visits")
    public List<Map<String, Object>> siteVisits() {
        return problems.siteVisits();
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> add(@RequestBody Map<String, String> body) {
        UUID projectId = UUID.fromString(String.valueOf(body.get("projectId")));
        UUID clientId = body.get("clientId") == null || body.get("clientId").isBlank() ? null : UUID.fromString(body.get("clientId"));
        ProjectProblem pp = problems.add(projectId, new ProblemService.NewProblem(body.get("kind"), body.get("label"), body.get("detail"),
                body.get("solution"), clientId, null, false));
        return ResponseEntity.ok(Map.of("id", pp.getId(), "label", pp.getLabel()));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Map<String, Object>> update(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        ProjectProblem pp = problems.update(id, body.get("solution"), body.get("detail"));
        return ResponseEntity.ok(Map.of("id", pp.getId(), "solution", pp.getSolution()));
    }

    @PostMapping("/{id}/solve")
    public ResponseEntity<Map<String, Object>> solve(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        Map<String, String> values = new HashMap<>();   // fix291: the real NIN / phone / invoice / contract, when typed
        for (String k : List.of("nin", "phone", "invoice", "contract", "personId")) {
            if (body.get(k) != null && !body.get(k).isBlank()) values.put(k, body.get(k));
        }
        ProjectProblem pp = problems.solve(id, body.get("note"), values);
        return ResponseEntity.ok(Map.of("id", pp.getId(), "status", pp.getStatus(), "note", String.valueOf(pp.getSolvedNote())));
    }

    /** fix291: VISIT DONE on the Site Visits list (solves the visit problems, writes the Recovery note). */
    @PostMapping("/site-visits/{projectId}/done")
    public ResponseEntity<Map<String, Object>> siteVisitDone(@PathVariable UUID projectId, @RequestBody Map<String, String> body) {
        int n = problems.siteVisitDone(projectId, body.get("note"));
        return ResponseEntity.ok(Map.of("solved", n));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Map<String, Object>> remove(@PathVariable UUID id, @RequestParam("reason") String reason) {
        problems.remove(id, reason);
        return ResponseEntity.ok(Map.of("removed", true));
    }
}
