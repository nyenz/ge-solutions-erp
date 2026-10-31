// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/archive/controller/ArchiveController.java
package com.gesolutions.erp.modules.archive.controller;

import com.gesolutions.erp.modules.archive.service.ArchiveService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/** fix284 (B1): the deleted documents, notes and expenses (kept 90 days). Director and Admin only, like Deleted projects. */
@RestController
@RequestMapping("/api/v1/archive")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class ArchiveController {

    private final ArchiveService archiveService;

    @GetMapping("/items")
    public ResponseEntity<List<Map<String, Object>>> list() {
        return ResponseEntity.ok(archiveService.list());
    }

    @PostMapping("/items/{id}/restore")
    public ResponseEntity<Map<String, Object>> restore(@PathVariable UUID id) {
        return ResponseEntity.ok(archiveService.restore(id));
    }
}
