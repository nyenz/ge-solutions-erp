// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/FileStorageService.java
package com.gesolutions.erp.modules.land.service;

import org.springframework.lang.NonNull;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;

public interface FileStorageService {

    String storeFile(@NonNull MultipartFile file, @NonNull String subFolder) throws IOException;

    void deleteFile(@NonNull String filePath);

    // NEW: Deletes the entire folder from Cloudinary after purge
    void deleteFolder(@NonNull String folderPath);

    // NEW: Wipes every file ever uploaded by this app (all projects, all
    // resource types) from Cloudinary. Used by the DANGER ZONE full wipe.
    /**
     * fix181 (15.5b): deletes every uploaded file and says how many went and how many could not be deleted
     * (keys filesDeleted, filesFailed; "error" holds a plain sentence when something failed).
     */
    java.util.Map<String, Object> deleteAllFiles();
}