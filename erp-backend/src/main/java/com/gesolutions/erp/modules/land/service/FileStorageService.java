// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/FileStorageService.java
package com.gesolutions.erp.modules.land.service;

import org.springframework.lang.NonNull;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;

/**
 * GE SOLUTIONS - VIRTUAL STORAGE INTERFACE
 * Defines how the system handles scans and documents.
 * This interface is the 'Promise' that allows switching to Cloud storage later.
 */
public interface FileStorageService {
    
    /**
     * Commits a physical file to the vault.
     * @return The access path/URL of the saved file.
     */
    String storeFile(@NonNull MultipartFile file, @NonNull String subFolder) throws IOException;

    /**
     * Permanently removes an asset from the vault.
     */
    void deleteFile(@NonNull String filePath);
}