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
    private final TimelineService timeline;   // fix223
    private final com.gesolutions.erp.modules.client.repository.ClientRepository clientRepository;   // fix225
    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;   // fix225

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
        if (pinned) announcePin(n);
        return n;
    }

    /** fix225 (David): a note about the CLIENT alone, written on the client page (no project, no file). */
    @Transactional
    public FollowUpLog addForClient(UUID clientId, String content, String topic, LocalDate followUpOn, boolean pinned) {
        com.gesolutions.erp.modules.client.model.Client c = clientRepository.findById(clientId)
                .orElseThrow(() -> new BusinessException("CLIENT_NOT_FOUND: This client no longer exists."));
        String text = text(content);
        if (LandService.isEvidenceNote(text)) {
            throw new BusinessException("NOTE_INVALID: A note cannot start with a system label like [PROBLEM] or [HANDED OVER].");
        }
        String t = topic(topic);
        checkDay(followUpOn);
        FollowUpLog n = noteRepository.save(FollowUpLog.builder().clientId(clientId).notes(text).topic(t).followUpOn(followUpOn)
                .pinned(pinned).recordedBy(AuditService.currentOperator()).build());
        auditService.logActionAfterCommit("NOTE_ADDED", "Operator [" + AuditService.currentOperator() + "] added a client note about "
                + c.getFullName() + (t != null ? " (" + t + ")" : "") + (followUpOn != null ? " | follow up on " + followUpOn : "") + ": " + shortText(text));
        if (pinned) announcePin(n);
        return n;
    }

    /** fix225 (David): a pinned note also rings the bell of the Secretary, Manager and Director (once per pin). */
    private void announcePin(FollowUpLog n) {
        try {
            String who = AuditService.currentOperator();
            String words = shortText(n.getNotes());
            if (n.getProjectId() != null) {
                String index = projectRepository.findById(n.getProjectId()).map(p -> String.valueOf(p.getProjectIndex())).orElse("?");
                notificationService.emitToAudience("NOTE_PINNED", "Note pinned on project #" + index + " by " + who + ": " + words,
                        "PROJECT_NOTES", n.getProjectId());
            } else if (n.getClientId() != null) {
                String name = clientRepository.findById(n.getClientId()).map(c -> c.getFullName()).orElse("a client");
                notificationService.emitToAudience("NOTE_PINNED", "Note pinned about " + name + " by " + who + ": " + words,
                        "CLIENT", n.getClientId());
            }
        } catch (RuntimeException e) {
            // the bell is a convenience: it must never stop the pin itself
            org.slf4j.LoggerFactory.getLogger(NoteService.class).warn("[NOTES] pin alert not sent: {}", e.getMessage());
        }
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
        boolean was = Boolean.TRUE.equals(n.getPinned());
        n.setPinned(pinned);
        FollowUpLog saved = noteRepository.save(n);
        if (pinned && !was) announcePin(saved);   // fix225
        return saved;
    }

    @Transactional
    public void delete(UUID noteId) { delete(noteId, null); }

    /** fix223: the reason goes into the audit line and stays in the project's Notes as a record. */
    @Transactional
    public void delete(UUID noteId, String reason) {
        FollowUpLog n = mine(noteId);
        noteRepository.delete(n);
        auditService.logActionAfterCommit("NOTE_DELETED", "Operator [" + AuditService.currentOperator() + "] deleted a note: "
                + shortText(n.getNotes()) + com.gesolutions.erp.common.util.DeleteReason.tail(reason));
        if (reason != null) timeline.reason(n.getProjectId(), "NOTE_DELETED", "Note deleted", reason, shortText(n.getNotes()), false);
    }

    /** The note, when the caller may change it. */
    private FollowUpLog mine(UUID noteId) {
        FollowUpLog n = noteRepository.findById(noteId)
                .orElseThrow(() -> new BusinessException("NOTE_NOT_FOUND: This note no longer exists (someone may have deleted it)."));
        if (LandService.isEvidenceNote(n.getNotes())) {
            throw new BusinessException("NOTE_LOCKED: This line was written by the system for a PROBLEM flag or a hand-over. It is kept as a record and cannot be changed.");
        }
        if (n.getProjectId() != null) projectRepository.findById(n.getProjectId()).ifPresent(p -> {
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
