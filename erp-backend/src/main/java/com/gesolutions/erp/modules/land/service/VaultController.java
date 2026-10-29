// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/VaultController.java
package com.gesolutions.erp.modules.land.service;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * fix273: hands out a document saved on the server's own disk (GE_SOLUTIONS_STORAGE=local).
 * GET /api/v1/vault/{folder}/{file}. Only a signed-in person gets it (the general rule of SecurityConfig: every address
 * outside /auth needs a valid key). The folder and file names must be clean names; nothing outside the upload folder
 * can ever be reached.
 */
@RestController
@RequestMapping("/api/v1/vault")
@ConditionalOnProperty(name = "ge.solutions.storage", havingValue = "local")
public class VaultController {

    private final LocalStorageServiceImpl storage;

    public VaultController(LocalStorageServiceImpl storage) { this.storage = storage; }

    @GetMapping("/{folder}/{file:.+}")
    public ResponseEntity<Resource> open(@PathVariable String folder, @PathVariable String file) {
        Path p = storage.resolveSafe(folder, file);
        if (p == null || !Files.isRegularFile(p)) return ResponseEntity.notFound().build();
        String ext = file.contains(".") ? file.substring(file.lastIndexOf('.') + 1).toLowerCase(Locale.ROOT) : "";
        MediaType type;
        boolean inline = true;
        switch (ext) {
            case "pdf" -> type = MediaType.APPLICATION_PDF;
            case "jpg", "jpeg" -> type = MediaType.IMAGE_JPEG;
            case "png" -> type = MediaType.IMAGE_PNG;
            case "gif" -> type = MediaType.IMAGE_GIF;
            case "webp" -> type = MediaType.parseMediaType("image/webp");
            default -> { type = MediaType.APPLICATION_OCTET_STREAM; inline = false; }   // Word, Excel, anything else: a download
        }
        return ResponseEntity.ok()
                .contentType(type)
                .header(HttpHeaders.CONTENT_DISPOSITION, (inline ? "inline" : "attachment") + "; filename=\"" + file + "\"")
                .header("X-Content-Type-Options", "nosniff")
                .cacheControl(CacheControl.noStore())
                .body(new FileSystemResource(p));
    }
}
