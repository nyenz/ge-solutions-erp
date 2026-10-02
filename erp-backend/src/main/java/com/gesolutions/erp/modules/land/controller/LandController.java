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
import org.springframework.data.domain.Sort;
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
    // fix167: the app's own JSON reader (knows dates, ignores extra fields). A bare "new ObjectMapper()" refused
    // every New Project save that carried a date or a stage list.
    private final ObjectMapper objectMapper;

    // FIX: previously @PostMapping(unlock-log) + @GetMapping(next-index) were
    // stacked on ONE method, so /next-index never registered (404) and the
    // Index field always failed. One mapping per method now.
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/next-index")
    public ResponseEntity<String> previewNextIndex() {
        return ResponseEntity.ok(landService.previewNextIndex());
    }

    // fix173: the system default monthly storage fee, so the Intake and Folder pages never carry their own copy of the number
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/storage-fee-default")
    public ResponseEntity<java.util.Map<String, java.math.BigDecimal>> storageFeeDefault() {
        return ResponseEntity.ok(java.util.Map.of("defaultMonthlyFee", LandProject.DEFAULT_MONTHLY_STORAGE_FEE));
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
        LandEntryRequest request = objectMapper.readValue(jsonData, LandEntryRequest.class);
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
    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id, @RequestParam String reason) {
        landService.nuclearDelete(id, reason);
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
        // fix169: an unsorted findAll can repeat or skip rows between pages; sort by id so paging is stable.
        // Size is capped so one call cannot ask for the whole table in one go.
        int safeSize = Math.min(Math.max(size, 1), 500);
        return ResponseEntity.ok(landService.getGlobalLedger(PageRequest.of(Math.max(page, 0), safeSize, Sort.by("id"))));
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

    // fix167: a hand-over needs a note (who collected the title, how they were identified): 5+ characters.
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

    // fix167: the old receivable endpoints (/receivable, /exit-receivable, /exit-receivable-capitalize) are gone.
    // They skipped every rule (no reason, no checks). Use /land/portal/{id}/receivable/... (FolderPortalController).

    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }

    // fix165: the ONLY way to record a payment is with its receipt file (multipart). The old no-receipt form is gone.
    // fix167: also says WHICH owner paid (payerId, required when there is more than one owner) and what the money is
    // for (allocation TITLE or STORAGE).
    @PostMapping(value = "/projects/{id}/payment", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes,
                                               @RequestParam(value = "payerId", required = false) UUID payerId,
                                               @RequestParam(value = "allocation", required = false) String allocation,
                                               @RequestParam(value = "receipt", required = false) MultipartFile receipt) throws Exception {
        landService.recordPaymentWithReceipt(id, amount, notes, receipt, payerId, allocation);
        return ResponseEntity.ok().build();
    }

    // fix167: the old storage endpoints (/storage-pause, /storage-rate, /storage-fees, /negotiation-deadline,
    // /receivable-start) are gone. They had no 365-day limit, no receivable check, and two of them needed no reason.
    // Every storage-fee change now goes through /land/portal/{id}/receivable/settings or /reduce-fees.
}
