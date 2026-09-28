// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DocumentCategoryController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.DocumentCategory;
import com.gesolutions.erp.modules.land.service.DocumentCategoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * fix136: document categories. Secretary is allowed to add categories too
 * (same roles that may upload a document).
 */
@RestController
@RequestMapping("/api/v1/land/document-categories")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class DocumentCategoryController {

    private final DocumentCategoryService documentCategoryService;

    @GetMapping
    public ResponseEntity<List<DocumentCategory>> list() {
        return ResponseEntity.ok(documentCategoryService.list());
    }

    @PostMapping
    public ResponseEntity<DocumentCategory> create(@RequestBody Map<String, String> body) {
        return ResponseEntity.ok(documentCategoryService.create(body.get("label")));
    }
}
