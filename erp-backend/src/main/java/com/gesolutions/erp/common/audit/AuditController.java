// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditController.java
package com.gesolutions.erp.common.audit;

import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * GOLDEN SEED ERP - AUDIT TRAIL (read only).
 * fix181 (10.11): Admin and Director only (the old class gate also named Manager, which every method overrode).
 */
@RestController
@RequestMapping("/api/v1/admin/audit")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class AuditController {

    private final AuditLogRepository auditLogRepository;
    private final AuditSearchService auditSearchService;
    private final AuditService auditService;

    /** Newest first, at most 200 rows a page (10.7), id as the second sort key (10.5). */
    @GetMapping("/stream")
    public ResponseEntity<Page<AuditLog>> getRawStream(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return ResponseEntity.ok(auditSearchService.search(new AuditSearchService.Filter(null, null, null, null, null, false), page, size));
    }

    /**
     * fix181 (10.13): filter by person, by ONE code (`action`, old callers) or a LIST of codes (`actions`, wins when both
     * are given), by time (start inclusive, end exclusive) and by a word in the text. `excludeSystem` leaves out the
     * automatic jobs (per-person reports, 10.8).
     */
    @GetMapping("/search")
    public ResponseEntity<Page<AuditLog>> searchForensics(
            @RequestParam(required = false) String operator,
            @RequestParam(required = false) String action,
            @RequestParam(required = false) List<String> actions,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime start,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime end,
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "false") boolean excludeSystem,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        List<String> codes = (actions != null && !actions.isEmpty()) ? actions
                : (action == null || action.isBlank() ? null : List.of(action.trim()));
        return ResponseEntity.ok(auditSearchService.search(
                new AuditSearchService.Filter(operator, codes, start, end, keyword, excludeSystem), page, size));
    }

    /** fix181 (10.3): the OPERATOR filter list, from the audit trail itself (works for the Director, shows SYSTEM). */
    @GetMapping("/operators")
    public ResponseEntity<List<String>> operators() {
        return ResponseEntity.ok(auditSearchService.operators());
    }

    /** fix181 (10.6c): an export of the audit trail leaves its own line (who, which filters, how many rows). */
    @PostMapping("/export-log")
    public ResponseEntity<Void> exportLog(@RequestBody(required = false) Map<String, Object> body) {
        Object filters = body == null ? null : body.get("filters");
        Object rows = body == null ? null : body.get("rows");
        String f = filters == null ? "none" : String.valueOf(filters);
        if (f.length() > 500) f = f.substring(0, 500);
        auditService.logAction("AUDIT_EXPORT", "Audit trail exported to CSV. Rows: " + rows + ". Filters: " + f + ".");
        return ResponseEntity.noContent().build();
    }
}
