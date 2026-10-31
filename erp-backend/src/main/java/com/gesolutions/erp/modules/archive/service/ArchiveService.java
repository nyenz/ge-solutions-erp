// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/archive/service/ArchiveService.java
package com.gesolutions.erp.modules.archive.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.archive.model.ArchivedItem;
import com.gesolutions.erp.modules.archive.repository.ArchivedItemRepository;
import com.gesolutions.erp.modules.finance.model.Expense;
import com.gesolutions.erp.modules.finance.repository.ExpenseRepository;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectDocument;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.ProjectDocumentRepository;
import com.gesolutions.erp.modules.land.service.FileStorageService;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * fix284 (B1, David): deleted documents, notes and expenses are kept for 90 days and a Director can put them back.
 * keep...() is called by the delete code BEFORE it removes the live row, inside the same transaction, so either both
 * happen or neither. Nothing here changes the live tables except restore(), which adds the item back.
 */
@Service
@RequiredArgsConstructor
public class ArchiveService {

    private final ArchivedItemRepository archive;
    private final ProjectDocumentRepository documents;
    private final FollowUpRepository notes;
    private final ExpenseRepository expenses;
    private final LandProjectRepository projects;
    private final FileStorageService fileStorage;
    private final AuditService audit;
    private final ObjectMapper mapper;

    // ---------------------------------------------------------------- keep (called by the three deletes)

    @Transactional
    public void keepDocument(ProjectDocument d, String projectLabel, String reason) {
        Map<String, String> s = new LinkedHashMap<>();
        put(s, "projectId", d.getProjectId());
        put(s, "fileName", d.getFileName());
        put(s, "fileType", d.getFileType());
        put(s, "category", d.getCategory());
        put(s, "statusId", d.getStatusId());
        put(s, "internalNotes", d.getInternalNotes());
        put(s, "uploadedBy", d.getUploadedBy());
        put(s, "uploadedAt", d.getUploadedAt());
        String cat = d.getCategory() == null ? null : d.getCategory().replace('_', ' ').toLowerCase();
        save(ArchivedItem.DOCUMENT, d.getId(), d.getProjectId(), d.getFileName(),
                join(cat, projectLabel), s, d.getFilePath(), reason);
    }

    @Transactional
    public void keepNote(FollowUpLog n, String projectLabel, String reason) {
        Map<String, String> s = new LinkedHashMap<>();
        put(s, "projectId", n.getProjectId());
        put(s, "clientId", n.getClientId());
        put(s, "ownerId", n.getOwnerId());
        put(s, "notes", n.getNotes());
        put(s, "recordedBy", n.getRecordedBy());
        put(s, "timestamp", n.getTimestamp());
        put(s, "pinned", n.getPinned());
        put(s, "followUpOn", n.getFollowUpOn());
        put(s, "topic", n.getTopic());
        put(s, "documentId", n.getDocumentId());
        put(s, "editedAt", n.getEditedAt());
        put(s, "pinFor", n.getPinFor());
        put(s, "pinnedBy", n.getPinnedBy());
        put(s, "remindFor", n.getRemindFor());
        save(ArchivedItem.NOTE, n.getId(), n.getProjectId(), shortText(n.getNotes()),
                join("written by " + n.getRecordedBy(), projectLabel), s, null, reason);
    }

    @Transactional
    public void keepExpense(Expense e, String reason) {
        Map<String, String> s = new LinkedHashMap<>();
        put(s, "category", e.getCategory());
        put(s, "amount", e.getAmount() == null ? null : e.getAmount().toPlainString());
        put(s, "note", e.getNote());
        put(s, "recordedBy", e.getRecordedBy());
        put(s, "spentBy", e.getSpentBy());
        put(s, "createdAt", e.getCreatedAt());
        put(s, "editedAt", e.getEditedAt());
        put(s, "editedBy", e.getEditedBy());
        String amount = e.getAmount() == null ? "" : " - UGX " + String.format("%,d", e.getAmount().longValue());
        save(ArchivedItem.EXPENSE, e.getId(), null, e.getCategory() + amount,
                join("logged by " + e.getRecordedBy(), e.getNote() == null ? null : shortText(e.getNote())), s, null, reason);
    }

    // ---------------------------------------------------------------- list, restore

    @Transactional(readOnly = true)
    public List<Map<String, Object>> list() {
        LocalDateTime now = LocalDateTime.now();
        List<Map<String, Object>> out = new ArrayList<>();
        for (ArchivedItem a : archive.findAllByOrderByDeletedAtDesc()) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", a.getId());
            m.put("kind", a.getKind());
            m.put("label", a.getLabel());
            m.put("detail", a.getDetail());
            m.put("projectId", a.getProjectId());
            m.put("deletedBy", a.getDeletedBy());
            m.put("deletedAt", a.getDeletedAt());
            m.put("reason", a.getReason());
            m.put("expiresAt", a.getExpiresAt());
            m.put("daysLeft", Math.max(0, ChronoUnit.DAYS.between(now.toLocalDate(), a.getExpiresAt().toLocalDate())));
            out.add(m);
        }
        return out;
    }

    @Transactional
    public Map<String, Object> restore(UUID id) {
        ArchivedItem a = archive.findById(id).orElseThrow(() -> new BusinessException(
                "ARCHIVE_NOT_FOUND: This item is no longer in the archive (it may have been restored already)."));
        Map<String, String> s = read(a.getSnapshot());
        UUID projectId = uuid(s.get("projectId"));
        if (projectId != null) {
            LandProject p = projects.findById(projectId).orElseThrow(() -> new BusinessException(
                    "ARCHIVE_PROJECT_GONE: The project this belonged to no longer exists, so it cannot be put back."));
            if (p.isDeleted()) {
                throw new BusinessException("ARCHIVE_PROJECT_DELETED: The project this belonged to is deleted. Restore the project first (Deleted projects, above).");
            }
            if (ArchivedItem.DOCUMENT.equals(a.getKind()) && p.getLandTitle() != null && p.getLandTitle().isReleased()) {
                throw new BusinessException("ARCHIVE_PROJECT_RELEASED: The title of this project has been handed over, so no document can be added back. A director must UNDO the hand-over first.");
            }
        }
        UUID newId;
        switch (a.getKind()) {
            case ArchivedItem.DOCUMENT -> {
                if (a.getFilePath() == null || a.getFilePath().isBlank()) {
                    throw new BusinessException("ARCHIVE_FILE_GONE: The file of this document is no longer kept, so it cannot be put back.");
                }
                ProjectDocument d = ProjectDocument.builder()
                        .projectId(projectId)
                        .fileName(s.get("fileName"))
                        .fileType(s.get("fileType"))
                        .category(s.get("category"))
                        .statusId(uuid(s.get("statusId")))
                        .filePath(a.getFilePath())
                        .internalNotes(s.get("internalNotes"))
                        .uploadedBy(s.get("uploadedBy"))
                        .uploadedAt(timeOrNow(s.get("uploadedAt")))
                        .build();
                newId = documents.save(d).getId();
            }
            case ArchivedItem.NOTE -> {
                FollowUpLog n = FollowUpLog.builder()
                        .projectId(projectId)
                        .clientId(uuid(s.get("clientId")))
                        .ownerId(uuid(s.get("ownerId")))
                        .notes(s.get("notes"))
                        .recordedBy(s.get("recordedBy") == null ? "SYSTEM" : s.get("recordedBy"))
                        .timestamp(timeOrNow(s.get("timestamp")))
                        .pinned("true".equals(s.get("pinned")))
                        .followUpOn(s.get("followUpOn") == null ? null : LocalDate.parse(s.get("followUpOn")))
                        .topic(s.get("topic"))
                        .documentId(uuid(s.get("documentId")))
                        .editedAt(time(s.get("editedAt")))
                        .pinFor(s.get("pinFor"))
                        .pinnedBy(s.get("pinnedBy"))
                        .remindFor(s.get("remindFor"))
                        .build();
                newId = notes.save(n).getId();
            }
            case ArchivedItem.EXPENSE -> {
                Expense e = Expense.builder()
                        .category(s.get("category"))
                        .amount(s.get("amount") == null ? BigDecimal.ZERO : new BigDecimal(s.get("amount")))
                        .note(s.get("note"))
                        .recordedBy(s.get("recordedBy"))
                        .spentBy(s.get("spentBy"))
                        .createdAt(timeOrNow(s.get("createdAt")))
                        .editedAt(time(s.get("editedAt")))
                        .editedBy(s.get("editedBy"))
                        .build();
                newId = expenses.save(e).getId();
            }
            default -> throw new BusinessException("ARCHIVE_NOT_FOUND: This item cannot be put back.");
        }
        archive.delete(a);
        audit.logActionAfterCommit("ARCHIVE_RESTORED", "Operator [" + AuditService.currentOperator() + "] restored a deleted "
                + word(a.getKind()) + ": " + a.getLabel() + (a.getDetail() == null ? "" : " (" + a.getDetail() + ")")
                + ". It was deleted by " + a.getDeletedBy() + " on " + a.getDeletedAt().toLocalDate() + ".");
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("kind", a.getKind());
        m.put("id", newId);
        m.put("projectId", projectId);
        return m;
    }

    // ---------------------------------------------------------------- nightly clean-up

    /** Every night at 02:45: items deleted more than 90 days ago go for good, a document's file too. */
    @Scheduled(cron = "0 45 2 * * *", zone = "Africa/Kampala")
    @Transactional
    public int purgeExpired() {
        List<ArchivedItem> old = archive.findByExpiresAtBefore(LocalDateTime.now());
        int files = 0;
        for (ArchivedItem a : old) {
            if (ArchivedItem.DOCUMENT.equals(a.getKind()) && a.getFilePath() != null && !a.getFilePath().isBlank()) {
                try { fileStorage.deleteFile(a.getFilePath()); files++; }
                catch (Exception e) { System.err.println(">>> [ARCHIVE] file not removed: " + e.getMessage()); }
            }
            archive.delete(a);
        }
        if (!old.isEmpty()) {
            audit.logActionAfterCommit("ARCHIVE_PURGED", "SYSTEM: " + old.size() + " deleted item(s) older than "
                    + ArchivedItem.KEEP_DAYS + " days were removed for good (" + files + " file(s)).");
        }
        return old.size();
    }

    // ---------------------------------------------------------------- helpers

    private void save(String kind, UUID originalId, UUID projectId, String label, String detail,
                      Map<String, String> snapshot, String filePath, String reason) {
        LocalDateTime now = LocalDateTime.now();
        archive.save(ArchivedItem.builder()
                .kind(kind)
                .originalId(originalId)
                .projectId(projectId)
                .label(cut(label == null || label.isBlank() ? "(no name)" : label, 300))
                .detail(detail == null ? null : cut(detail, 300))
                .snapshot(write(snapshot))
                .filePath(filePath)
                .deletedBy(AuditService.currentOperator())
                .deletedAt(now)
                .reason(reason)
                .expiresAt(now.plusDays(ArchivedItem.KEEP_DAYS))
                .build());
    }

    private String write(Map<String, String> m) {
        try { return mapper.writeValueAsString(m); }
        catch (Exception e) { throw new BusinessException("ARCHIVE_FAULT: The item could not be kept in the archive, so it was not deleted."); }
    }

    private Map<String, String> read(String json) {
        try { return mapper.readValue(json, new TypeReference<Map<String, String>>() { }); }
        catch (Exception e) { throw new BusinessException("ARCHIVE_FAULT: This archived item cannot be read, so it cannot be put back."); }
    }

    private static void put(Map<String, String> m, String k, Object v) { if (v != null) m.put(k, String.valueOf(v)); }

    private static UUID uuid(String s) { return s == null || s.isBlank() ? null : UUID.fromString(s); }

    private static LocalDateTime time(String s) { return s == null || s.isBlank() ? null : LocalDateTime.parse(s); }

    private static LocalDateTime timeOrNow(String s) { LocalDateTime t = time(s); return t == null ? LocalDateTime.now() : t; }

    private static String join(String a, String b) {
        if (a == null || a.isBlank()) return b;
        if (b == null || b.isBlank()) return a;
        return a + " - " + b;
    }

    private static String shortText(String t) {
        String c = t == null ? "" : t.trim().replaceAll("\\s+", " ");
        return c.length() > 80 ? c.substring(0, 80) + "..." : c;
    }

    private static String cut(String s, int max) { return s.length() > max ? s.substring(0, max) : s; }

    private static String word(String kind) {
        return ArchivedItem.DOCUMENT.equals(kind) ? "document" : ArchivedItem.NOTE.equals(kind) ? "note" : "expense";
    }
}
