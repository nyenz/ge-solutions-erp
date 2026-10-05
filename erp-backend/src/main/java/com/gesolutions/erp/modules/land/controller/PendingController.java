// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/PendingController.java
package com.gesolutions.erp.modules.land.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.dto.PendingProjectDTO;
import com.gesolutions.erp.modules.land.service.PendingProjectService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * fix181 (12.1): the ONLY write routes an Employee has. The normal ones (/ingest, full-update, documents, notes) stay
 * closed to the Employee; these check, in the service, that the caller entered the project and that it is still Pending.
 * The office routes (start, reject, count) are Secretary and above.
 */
@RestController
@RequestMapping("/api/v1/land/pending")
@RequiredArgsConstructor
public class PendingController {

    private final PendingProjectService pendingService;
    private final ObjectMapper objectMapper;

    // ── Employee ────────────────────────────────────────────────────────────

    @PreAuthorize("hasRole('ROLE_EMPLOYEE')")
    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<PendingProjectDTO> create(@RequestPart("data") String jsonData,
                                                    @RequestPart(value = "scans", required = false) MultipartFile[] scans,
                                                    @RequestParam(value = "categories", required = false) List<String> categories) throws Exception {
        LandEntryRequest request = objectMapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(pendingService.createPending(request, scans, categories));
    }

    @PreAuthorize("hasRole('ROLE_EMPLOYEE')")
    @GetMapping("/mine")
    public List<PendingProjectDTO> mine() {
        return pendingService.mine();
    }

    @PreAuthorize("hasAnyRole('ROLE_EMPLOYEE', 'ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/{id}")
    public PendingProjectDTO view(@PathVariable UUID id) {
        return pendingService.viewOwn(id);
    }

    @PreAuthorize("hasRole('ROLE_EMPLOYEE')")
    @PutMapping("/{id}")
    public PendingProjectDTO update(@PathVariable UUID id, @RequestBody LandEntryRequest request) {
        return pendingService.updateOwn(id, request);
    }

    @PreAuthorize("hasRole('ROLE_EMPLOYEE')")
    @PostMapping(value = "/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Map<String, Object>> documents(@PathVariable UUID id,
                                                         @RequestPart("scans") MultipartFile[] scans,
                                                         @RequestParam(value = "categories", required = false) List<String> categories) throws Exception {
        pendingService.addDocuments(id, scans, categories);
        return ResponseEntity.ok(Map.of("ok", true));
    }

    @PreAuthorize("hasRole('ROLE_EMPLOYEE')")
    @PostMapping("/{id}/notes")
    public ResponseEntity<Map<String, Object>> note(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        pendingService.addNote(id, body == null ? null : body.get("content"));
        return ResponseEntity.ok(Map.of("ok", true));
    }

    // ── office ──────────────────────────────────────────────────────────────

    @PreAuthorize("hasAnyRole('ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/{id}/start")
    public ResponseEntity<Map<String, Object>> start(@PathVariable UUID id, @RequestBody LandEntryRequest request) {
        var p = pendingService.graduatePending(id, request);
        return ResponseEntity.ok(Map.of("ok", true, "id", p.getId(), "projectIndex", p.getProjectIndex()));
    }

    @PreAuthorize("hasAnyRole('ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/{id}/reject")
    public ResponseEntity<Map<String, Object>> reject(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        pendingService.rejectPending(id, body == null ? null : body.get("reason"));
        return ResponseEntity.ok(Map.of("ok", true));
    }

    @PreAuthorize("hasAnyRole('ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/count")
    public Map<String, Long> count() {
        return Map.of("pending", pendingService.countPending());
    }
}
