// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.dto.*;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectDocument;
import com.gesolutions.erp.modules.land.service.LandService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/land")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class LandController {

    private final LandService landService;

    @PostMapping("/projects/{id}/unlock-log")
    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/{id}/notes")
    public ResponseEntity<List<FollowUpLog>> getProjectNotes(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectNotes(id));
    }

    @PostMapping("/projects/{id}/follow-up")
    public ResponseEntity<Void> logContact(@PathVariable UUID id, @RequestParam String content) {
        landService.logFollowUp(id, content);
        return ResponseEntity.ok().build();
    }

    @PostMapping(value = "/ingest", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LandProject> ingestTitle(
            @RequestPart("data") String jsonData,
            @RequestPart(value = "scans", required = false) MultipartFile[] scans) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        LandEntryRequest request = mapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(landService.atomicIntake(request, scans));
    }

    @GetMapping("/projects/{id}/deep")
    public ResponseEntity<ProjectDeepDetailDTO> getProjectDeepDetail(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDeepDetail(id));
    }

    @PutMapping("/projects/{id}/full-update")
    public ResponseEntity<LandProject> updateProjectFull(
            @PathVariable UUID id, @RequestBody LandEntryRequest request) {
        return ResponseEntity.ok(landService.updateProjectFull(id, request));
    }

    @DeleteMapping("/projects/{id}")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id) {
        landService.nuclearDelete(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/projects/{id}/documents")
    public ResponseEntity<List<ProjectDocument>> getDocuments(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDocuments(id));
    }

    @PostMapping(value = "/projects/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> addExtraDocuments(
            @PathVariable UUID id,
            @RequestParam("scans") MultipartFile[] scans) throws Exception {
        landService.addScansToProject(id, scans);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/documents/{docId}")
    public ResponseEntity<Void> deleteDocument(@PathVariable UUID docId) {
        landService.removeDocument(docId);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/notes")
    public ResponseEntity<Void> addNote(@PathVariable UUID id, @RequestParam String content) {
        landService.logNewNote(id, content);
        return ResponseEntity.ok().build();
    }

    @PutMapping("/notes/{noteId}")
    public ResponseEntity<Void> updateNote(@PathVariable UUID noteId, @RequestParam String content) {
        landService.updateNote(noteId, content);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/notes/{noteId}")
    public ResponseEntity<Void> deleteNote(@PathVariable UUID noteId) {
        landService.removeNote(noteId);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/reality-override")
    public ResponseEntity<Void> manualRealityOverride(
            @PathVariable UUID id, @RequestParam int targetStage) {
        landService.manualRealityOverride(id, targetStage);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/ledger")
    public ResponseEntity<Page<LandProject>> getLedger(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(page, size)));
    }

    @PatchMapping("/projects/{id}/release")
    public ResponseEntity<Void> authorizeRelease(
            @PathVariable UUID id,
            @RequestParam(required = false) String managerNote) {
        landService.authorizeRelease(id, managerNote);
        return ResponseEntity.ok().build();
    }

    // NEW: Backlog management
    @PostMapping("/projects/{id}/backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> moveToBacklog(@PathVariable UUID id) {
        landService.moveToBacklog(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/exit-backlog")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN')")
    public ResponseEntity<Void> exitBacklog(@PathVariable UUID id) {
        landService.exitBacklog(id);
        return ResponseEntity.ok().build();
    }

    // NEW: Payment history per plot
    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }
}