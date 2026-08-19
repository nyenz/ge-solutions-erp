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
    void deleteAllFiles();
}