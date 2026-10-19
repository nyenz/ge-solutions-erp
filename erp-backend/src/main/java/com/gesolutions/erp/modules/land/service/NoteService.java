// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/NoteService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectDocument;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * fix215 (David): typed notes of the Notes timeline -- a topic picked from the quick list, an optional follow-up day
 * (the bell reminds the office that morning), pinned to the top, and one optional file (filed in Documents under
 * Note Attachments). A note is edited or deleted by the person who wrote it, or by a Manager and above; the record
 * notes ([PROBLEM], [HANDED OVER] ...) never. Every change is in the audit trail with the old words.
 */
@Service
@RequiredArgsConstructor
public class NoteService {

    public static final int MAX_CHARS = 2000;
    public static final int MAX_TOPIC = 60;
    public static final int MAX_FOLLOW_UP_DAYS = 365;
    public static final String ATTACHMENT_CATEGORY = "NOTE_ATTACHMENT";

    private final FollowUpRepository noteRepository;
    private final LandProjectRepository projectRepository;
    private final LandService landService;
    private final AuditService auditService;

    @Transactional(rollbackFor = Exception.class)
    public FollowUpLog add(UUID projectId, String content, String topic, LocalDate followUpOn, boolean pinned, MultipartFile file) throws Exception {
        LandProject p = projectRepository.findById(projectId)
                .orElseThrow(() -> new BusinessException("PLOT_NOT_FOUND: This project no longer exists."));
        if (p.isDeleted()) throw new BusinessException("NOTE_BLOCKED: This project is deleted. Restore it first.");
        String text = text(content);
        String t = topic(topic);
        checkDay(followUpOn);
        UUID docId = null;
        if (file != null && !file.isEmpty()) {
            if (file.getSize() > 50L * 1024L * 1024L) throw new BusinessException("FILE_TOO_LARGE: The file must be under 50 MB.");
            landService.requireScanFiles(new MultipartFile[] { file });
            List<ProjectDocument> filed = landService.addScansToProject(projectId, new MultipartFile[] { file }, ATTACHMENT_CATEGORY, null);
            if (!filed.isEmpty()) docId = filed.get(0).getId();
        }
        FollowUpLog n = noteRepository.save(FollowUpLog.builder().projectId(projectId).notes(text).topic(t).followUpOn(followUpOn)
                .pinned(pinned).documentId(docId).recordedBy(AuditService.currentOperator()).build());
        auditService.logActionAfterCommit("NOTE_ADDED", "Operator [" + AuditService.currentOperator() + "] added a note to project #"
                + p.getProjectIndex() + (t != null ? " (" + t + ")" : "") + (followUpOn != null ? " | follow up on " + followUpOn : "")
                + (docId != null ? " | with a file" : "") + ": " + shortText(text));
        return n;
    }

    @Transactional
    public FollowUpLog edit(UUID noteId, String content, String topic, LocalDate followUpOn) {
        FollowUpLog n = mine(noteId);
        String text = text(content);
        if (LandService.isEvidenceNote(text)) {
            throw new BusinessException("NOTE_INVALID: A note cannot start with a system label like [PROBLEM] or [HANDED OVER].");
        }
        String t = topic(topic);
        if (followUpOn != null && !followUpOn.equals(n.getFollowUpOn())) checkDay(followUpOn);
        String before = n.getNotes();
        n.setNotes(text);
        n.setTopic(t);
        n.setFollowUpOn(followUpOn);
        n.setEditedAt(LocalDateTime.now());
        noteRepository.save(n);
        auditService.logActionAfterCommit("NOTE_UPDATED", "Operator [" + AuditService.currentOperator() + "] edited a note. WAS: "
                + shortText(before) + " | NOW: " + shortText(text));
        return n;
    }

    /** Anyone who can read the timeline may pin or unpin a note (it only changes the order). */
    @Transactional
    public FollowUpLog pin(UUID noteId, boolean pinned) {
        FollowUpLog n = noteRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        if (LandService.isEvidenceNote(n.getNotes())) throw new BusinessException("NOTE_LOCKED: Record lines cannot be pinned.");
        n.setPinned(pinned);
        return noteRepository.save(n);
    }

    @Transactional
    public void delete(UUID noteId) {
        FollowUpLog n = mine(noteId);
        noteRepository.delete(n);
        auditService.logActionAfterCommit("NOTE_DELETED", "Operator [" + AuditService.currentOperator() + "] deleted a note: " + shortText(n.getNotes()));
    }

    /** The note, when the caller may change it. */
    private FollowUpLog mine(UUID noteId) {
        FollowUpLog n = noteRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        if (LandService.isEvidenceNote(n.getNotes())) {
            throw new BusinessException("NOTE_LOCKED: This line was written by the system for a PROBLEM flag or a hand-over. It is kept as a record and cannot be changed.");
        }
        projectRepository.findById(n.getProjectId()).ifPresent(p -> {
            if (p.isDeleted()) throw new BusinessException("NOTE_LOCKED: This project is deleted. Restore it first.");
        });
        String me = AuditService.currentOperator();
        if (!TimelineService.canManage() && !me.equals(n.getRecordedBy())) {
            throw new BusinessException("NOTE_NOT_YOURS: Only the person who wrote this note, or a Manager, can change it.");
        }
        return n;
    }

    private static String text(String content) {
        String c = content == null ? "" : content.trim();
        if (c.length() < 2) throw new BusinessException("NOTE_REQUIRED: Write the note first (at least 2 characters).");
        if (c.length() > MAX_CHARS) throw new BusinessException("NOTE_TOO_LONG: A note can be at most " + MAX_CHARS + " characters (this one is " + c.length() + ").");
        return c;
    }

    private static String topic(String topic) {
        if (topic == null || topic.isBlank()) return null;
        String t = topic.trim().replaceAll("\\s+", " ");
        if (t.length() > MAX_TOPIC) throw new BusinessException("TOPIC_TOO_LONG: The topic can be at most " + MAX_TOPIC + " characters.");
        return t;
    }

    private static void checkDay(LocalDate day) {
        if (day == null) return;
        LocalDate today = LocalDate.now();
        if (day.isBefore(today)) throw new BusinessException("FOLLOW_UP_IN_PAST: The follow-up day cannot be in the past.");
        if (day.isAfter(today.plusDays(MAX_FOLLOW_UP_DAYS))) throw new BusinessException("FOLLOW_UP_TOO_FAR: The follow-up day can be at most a year away.");
    }

    private static String shortText(String s) {
        if (s == null) return "";
        String t = s.replace('\n', ' ').trim();
        return t.length() > 160 ? t.substring(0, 160) + "..." : t;
    }
}
