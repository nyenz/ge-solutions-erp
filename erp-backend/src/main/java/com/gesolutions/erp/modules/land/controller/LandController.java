// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.dto.*;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectDocument;
import com.gesolutions.erp.modules.land.model.ProjectStage;
import com.gesolutions.erp.modules.land.repository.ProjectStageRepository;
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
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class LandController {

    private final LandService landService;
    private final ProjectStageRepository projectStageRepository;

    // FIX: previously @PostMapping(unlock-log) + @GetMapping(next-index) were
    // stacked on ONE method, so /next-index never registered (404) and the
    // Index field always failed. One mapping per method now.
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

    @PostMapping("/projects/{id}/unlock-log")
    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/notes")
    public ResponseEntity<List<FollowUpLog>> getProjectNotes(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectNotes(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/follow-up")
    public ResponseEntity<java.util.Map<String, Object>> logContact(@PathVariable UUID id,
                                            @RequestParam UUID ownerId,
                                            @RequestParam String content) {
        return ResponseEntity.ok(landService.logFollowUp(id, ownerId, content));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/ingest", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LandProject> ingestTitle(
            @RequestPart("data") String jsonData,
            @RequestPart(value = "scans", required = false) MultipartFile[] scans) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        LandEntryRequest request = mapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(landService.atomicIntake(request, scans));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
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

    @PostMapping("/projects/{id}/restore")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> restoreAsset(@PathVariable UUID id) {
        landService.restoreProject(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/deleted")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<List<LandProject>> getDeletedProjects() {
        return ResponseEntity.ok(landService.getDeletedProjects());
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/documents")
    public ResponseEntity<List<ProjectDocument>> getDocuments(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDocuments(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/projects/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> addExtraDocuments(
            @PathVariable UUID id,
            @RequestParam("scans") MultipartFile[] scans,
            @RequestParam(value = "category", required = false) String category,
            @RequestParam(value = "categories", required = false) List<String> categories) throws Exception {
        landService.requireScanFiles(scans);
        landService.addScansToProject(id, scans, category, categories);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/documents/{docId}")
    public ResponseEntity<Void> deleteDocument(@PathVariable UUID docId) {
        landService.removeDocument(docId);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/notes")
    public ResponseEntity<Void> addNote(@PathVariable UUID id,
                                        @RequestParam(required = false) String content,
                                        @RequestBody(required = false) java.util.Map<String, String> body) {
        // fix165: the text normally arrives in the body; the old ?content= form still works
        landService.logNewNote(id, content != null ? content : (body == null ? null : body.get("content")));
        return ResponseEntity.ok().build();
    }

    @PutMapping("/notes/{noteId}")
    public ResponseEntity<Void> updateNote(@PathVariable UUID noteId,
                                           @RequestParam(required = false) String content,
                                           @RequestBody(required = false) java.util.Map<String, String> body) {
        landService.updateNote(noteId, content != null ? content : (body == null ? null : body.get("content")));
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/notes/{noteId}")
    public ResponseEntity<Void> deleteNote(@PathVariable UUID noteId) {
        landService.removeNote(noteId);
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/projects/{id}/reality-override")
    public ResponseEntity<Void> manualRealityOverride(
            @PathVariable UUID id, @RequestParam int targetStage) {
        landService.manualRealityOverride(id, targetStage);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/ledger")
    public ResponseEntity<Page<LandProject>> getLedger(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(page, size)));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/ledger/stages-bulk")
    public ResponseEntity<List<ProjectStage>> getStagesBulk(@RequestBody List<UUID> projectIds) {
        return ResponseEntity.ok(projectStageRepository.findByProjectIdIn(projectIds));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/bulk-mark-title-produced")
    public ResponseEntity<Integer> bulkMarkTitleProduced(@RequestBody List<UUID> projectIds) {
        return ResponseEntity.ok(landService.bulkMarkTitleProduced(projectIds));
    }

    @PatchMapping("/projects/{id}/release")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> authorizeRelease(
            @PathVariable UUID id,
            @RequestParam(required = false) String managerNote) {
        landService.authorizeRelease(id, managerNote);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/undo-release")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> undoRelease(@PathVariable UUID id, @RequestParam String reason) {
        landService.undoRelease(id, reason);
        return ResponseEntity.ok().build();
    }

    // fix163: revert a saved title back to the stage checklist
    @PatchMapping("/projects/{id}/revert-title")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> revertTitle(@PathVariable UUID id, @RequestParam String reason) {
        landService.revertTitle(id, reason);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/payments/{paymentId}/reverse")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> reversePayment(@PathVariable UUID id, @PathVariable UUID paymentId,
                                               @RequestParam String reason) {
        landService.reversePayment(id, paymentId, reason);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/receivable")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> moveToReceivable(@PathVariable UUID id) {
        landService.moveToReceivable(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/exit-receivable")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitReceivable(@PathVariable UUID id,
                                            @RequestParam(defaultValue = "false") boolean capitalizeFees) {
        landService.exitReceivable(id, capitalizeFees);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/projects/{id}/exit-receivable-capitalize")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> exitReceivableCapitalize(@PathVariable UUID id) {
        landService.exitReceivable(id, true);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }

    // fix165: the ONLY way to record a payment is with its receipt file (multipart). The old no-receipt form is gone.
    @PostMapping(value = "/projects/{id}/payment", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes,
                                               @RequestParam(value = "receipt", required = false) MultipartFile receipt) throws Exception {
        landService.recordPaymentWithReceipt(id, amount, notes, receipt);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-pause")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,
                                                   @RequestParam boolean paused,
                                                   @RequestParam String reason) {
        landService.setStoragePaused(id, paused, reason);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-rate")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal rate,
                                               @RequestParam String reason) {
        landService.setStorageFeeOverride(id, rate, reason);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/storage-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam String reason) {
        landService.setAccumulatedFees(id, amount, reason);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/negotiation-deadline")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setNegotiationDeadline(@PathVariable UUID id,
                                                        @RequestParam(required = false) String deadline) {
        landService.setNegotiationDeadline(id, deadline);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/projects/{id}/receivable-start")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setReceivableStartOverride(@PathVariable UUID id,
                                                         @RequestParam String startDate) {
        landService.setReceivableStartOverride(id, startDate);
        return ResponseEntity.ok().build();
    }
}
