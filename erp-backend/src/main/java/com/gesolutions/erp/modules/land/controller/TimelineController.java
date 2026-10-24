// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/TimelineController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.FollowUpLog;
import com.gesolutions.erp.modules.land.service.NoteService;
import com.gesolutions.erp.modules.land.service.TimelineService;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDate;
import java.util.Map;
import java.util.UUID;

/** fix215 (David): the Notes timeline of a project or a client, and the typed notes in it. Secretary and above. */
@RestController
@RequestMapping("/api/v1/timeline")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_SECRETARY', 'ROLE_MANAGER', 'ROLE_DIRECTOR', 'ROLE_ADMIN')")
public class TimelineController {

    private final TimelineService timeline;
    private final NoteService notes;

    @GetMapping("/project/{id}")
    public Map<String, Object> project(@PathVariable UUID id) { return timeline.forProject(id); }

    @GetMapping("/client/{id}")
    public Map<String, Object> client(@PathVariable UUID id) { return timeline.forClient(id); }

    @PostMapping(value = "/project/{id}/notes", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> add(@PathVariable UUID id,
                                   @RequestParam(required = false) String content,
                                   @RequestParam(required = false) String topic,
                                   @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate followUpOn,
                                   @RequestParam(defaultValue = "false") boolean pinned,
                                   @RequestParam(value = "file", required = false) MultipartFile file,
                                   @RequestParam(required = false) String pinFor,
                                   @RequestParam(required = false) String remindFor) throws Exception {
        FollowUpLog n = notes.add(id, content, topic, followUpOn, pinned, file, pinFor, remindFor);   // fix241
        return Map.of("id", n.getId());
    }

    /** fix225 (David): a note about the client alone (no project, no file). */
    @PostMapping("/client/{id}/notes")
    public Map<String, Object> addForClient(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
        Object day = body.get("followUpOn");
        LocalDate on;
        try {
            on = day == null || String.valueOf(day).isBlank() ? null : LocalDate.parse(String.valueOf(day).trim());
        } catch (java.time.format.DateTimeParseException e) {
            throw new com.gesolutions.erp.common.exception.BusinessException("DATE_INVALID: The follow-up day is not a valid date.");
        }
        FollowUpLog n = notes.addForClient(id, body.get("content") == null ? null : String.valueOf(body.get("content")),
                body.get("topic") == null ? null : String.valueOf(body.get("topic")), on, Boolean.TRUE.equals(body.get("pinned")),
                body.get("pinFor") == null ? null : String.valueOf(body.get("pinFor")),
                body.get("remindFor") == null ? null : String.valueOf(body.get("remindFor")));   // fix241
        return Map.of("id", n.getId());
    }

    @PutMapping("/notes/{noteId}")
    public Map<String, Object> edit(@PathVariable UUID noteId, @RequestBody Map<String, String> body) {
        String day = body.get("followUpOn");
        LocalDate on;
        try {
            on = day == null || day.isBlank() ? null : LocalDate.parse(day.trim());
        } catch (java.time.format.DateTimeParseException e) {
            throw new com.gesolutions.erp.common.exception.BusinessException("DATE_INVALID: The follow-up day is not a valid date.");
        }
        FollowUpLog n = notes.edit(noteId, body.get("content"), body.get("topic"), on, body.get("remindFor"), body.containsKey("remindFor"));   // fix241
        return Map.of("id", n.getId());
    }

    @PatchMapping("/notes/{noteId}/pin")
    public Map<String, Object> pin(@PathVariable UUID noteId, @RequestBody Map<String, Object> body) {
        FollowUpLog n = notes.pin(noteId, Boolean.TRUE.equals(body.get("pinned")), body.get("pinFor") == null ? null : String.valueOf(body.get("pinFor")));   // fix241
        return Map.of("id", n.getId(), "pinned", Boolean.TRUE.equals(n.getPinned()));
    }

    @DeleteMapping("/notes/{noteId}")
    public ResponseEntity<Void> delete(@PathVariable UUID noteId, @RequestParam(required = false) String reason) {
        notes.delete(noteId, com.gesolutions.erp.common.util.DeleteReason.require(reason));   // fix223
        return ResponseEntity.noContent().build();
    }
}
