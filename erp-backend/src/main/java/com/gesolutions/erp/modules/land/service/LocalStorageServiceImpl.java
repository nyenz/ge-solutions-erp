// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LocalStorageServiceImpl.java
package com.gesolutions.erp.modules.land.service;

import org.springframework.lang.NonNull;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.*;
import java.util.Objects;

/**
 * GE SOLUTIONS - LOCAL ARCHIVE STORAGE
 * Physically writes scans to the server's hard drive (ge_uploads/).
 */
@Service
public class LocalStorageServiceImpl implements FileStorageService {

    private final Path rootLocation = Paths.get("ge_uploads");

    @Override
    public String storeFile(@NonNull MultipartFile file, @NonNull String subFolder) throws IOException {
        // Strict verification clears IDE warnings
        MultipartFile verifiedFile = Objects.requireNonNull(file);
        String verifiedDir = Objects.requireNonNull(subFolder);

        Path targetDir = this.rootLocation.resolve(verifiedDir);
        
        // 1. Physically ensure the cabinet drawer (folder) exists
        if (!Files.exists(targetDir)) {
            Files.createDirectories(targetDir);
        }
        
        // 2. Prevent naming collisions with millisecond timestamps
        String originalName = verifiedFile.getOriginalFilename() != null ? verifiedFile.getOriginalFilename() : "unknown_file";
        String filename = System.currentTimeMillis() + "_" + originalName;
        
        Path targetPath = targetDir.resolve(filename);
        
        // 3. Commit data to disk
        Files.copy(verifiedFile.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        
        return targetPath.toString();
    }

    @Override
    public void deleteFile(@NonNull String filePath) {
        try {
            Files.deleteIfExists(Paths.get(Objects.requireNonNull(filePath)));
        } catch (IOException e) {
            System.err.println("INDUSTRIAL STORAGE FAULT: Physical file removal failed: " + filePath);
        }
    }
}