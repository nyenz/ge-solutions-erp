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
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class LandController {

    private final LandService landService;

    @PostMapping("/projects/{id}/unlock-log")
    public ResponseEntity<Void> logDossierUnlock(@PathVariable UUID id) {
        landService.logUnlockAction(id);
        return ResponseEntity.ok().build();
    }

    // STAGE 2 FIX: Secretary is data-entry -- needs to read/add notes
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/notes")
    public ResponseEntity<List<FollowUpLog>> getProjectNotes(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectNotes(id));
    }

    // STAGE 2 FIX: Secretary logs recovery calls (data-entry)
    // STAGE 10 FIX: ownerId is now required so a joint-project call is
    // attributed to the specific person staff actually reached, instead of
    // silently defaulting to whichever co-owner sorts first alphabetically
    // (design brief 3.3/3.4).
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping("/projects/{id}/follow-up")
    public ResponseEntity<Void> logContact(@PathVariable UUID id,
                                            @RequestParam UUID ownerId,
                                            @RequestParam String content) {
        landService.logFollowUp(id, ownerId, content);
        return ResponseEntity.ok().build();
    }

    // STAGE 2 FIX: intake is a data-entry endpoint per the role table
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @PostMapping(value = "/ingest", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LandProject> ingestTitle(
            @RequestPart("data") String jsonData,
            @RequestPart(value = "scans", required = false) MultipartFile[] scans) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        LandEntryRequest request = mapper.readValue(jsonData, LandEntryRequest.class);
        return ResponseEntity.ok(landService.atomicIntake(request, scans));
    }

    // STAGE 2 FIX: Folder page cannot load at all for Secretary without this
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

    // STAGE 3: soft-delete restore + deleted-list, same restriction as delete itself
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

    // STAGE 2 FIX: document upload/view is a data-entry endpoint
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @GetMapping("/projects/{id}/documents")
    public ResponseEntity<List<ProjectDocument>> getDocuments(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectDocuments(id));
    }

    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
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

    // STAGE 2 FIX: adding a standalone note is data-entry
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
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

    // STAGE 2 FIX: Secretary needs to browse the Ledger to find projects
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
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

    // NEW: Receivable management
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

    // NEW: Payment history per plot
    @GetMapping("/projects/{id}/payments")
    public ResponseEntity<List<PaymentRecord>> getPaymentHistory(@PathVariable UUID id) {
        return ResponseEntity.ok(landService.getProjectPayments(id));
    }

    // STAGE 1 FIX: this endpoint did not exist -- the frontend has been
    // calling it since it was built. Class-level @PreAuthorize already
    // covers ROLE_MANAGER/ROLE_ADMIN/ROLE_DIRECTOR.
    @PostMapping("/projects/{id}/payment")
    public ResponseEntity<Void> recordPayment(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount,
                                               @RequestParam(required = false) String notes) {
        landService.recordPayment(id, amount, notes);
        return ResponseEntity.ok().build();
    }

    // NEW: Pause / resume storage fee accumulation
    @PatchMapping("/projects/{id}/storage-pause")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> toggleStoragePause(@PathVariable UUID id,
                                                   @RequestParam boolean paused) {
        landService.setStoragePaused(id, paused);
        return ResponseEntity.ok().build();
    }

    // NEW: Edit the monthly storage fee rate for this plot
    @PatchMapping("/projects/{id}/storage-rate")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageRate(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal rate) {
        landService.setStorageFeeOverride(id, rate);
        return ResponseEntity.ok().build();
    }

    // NEW: Directly adjust accumulated storage fees (waive/correct)
    @PatchMapping("/projects/{id}/storage-fees")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setStorageFees(@PathVariable UUID id,
                                               @RequestParam java.math.BigDecimal amount) {
        landService.setAccumulatedFees(id, amount);
        return ResponseEntity.ok().build();
    }

    // NEW: Set negotiation deadline (pauses storage fees until this date)
    @PatchMapping("/projects/{id}/negotiation-deadline")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setNegotiationDeadline(@PathVariable UUID id,
                                                        @RequestParam(required = false) String deadline) {
        landService.setNegotiationDeadline(id, deadline);
        return ResponseEntity.ok().build();
    }

    // NEW: Set receivable start override date (for late-entered titles)
    @PatchMapping("/projects/{id}/receivable-start")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Void> setReceivableStartOverride(@PathVariable UUID id,
                                                         @RequestParam String startDate) {
        landService.setReceivableStartOverride(id, startDate);
        return ResponseEntity.ok().build();
    }
}