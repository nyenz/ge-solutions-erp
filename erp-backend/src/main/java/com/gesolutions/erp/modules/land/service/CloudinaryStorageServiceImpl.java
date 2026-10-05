// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/CloudinaryStorageServiceImpl.java
package com.gesolutions.erp.modules.land.service;

import com.cloudinary.Cloudinary;
import com.cloudinary.utils.ObjectUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;
import java.util.Objects;

@Service
public class CloudinaryStorageServiceImpl implements FileStorageService {

    private final String cloudName;
    private final Cloudinary cloudinary;

    public CloudinaryStorageServiceImpl(
            @Value("${cloudinary.cloud-name}") String cloudName,
            @Value("${cloudinary.api-key}") String apiKey,
            @Value("${cloudinary.api-secret}") String apiSecret) {

        this.cloudName = cloudName;
        this.cloudinary = new Cloudinary(ObjectUtils.asMap(
                "cloud_name", cloudName,
                "api_key",    apiKey,
                "api_secret", apiSecret,
                "secure",     true
        ));
    }

    private String detectResourceType(MultipartFile file) {
        String contentType = file.getContentType();
        String originalName = file.getOriginalFilename() != null
                ? file.getOriginalFilename().toLowerCase() : "";

        if (contentType != null && contentType.startsWith("image/")) return "image";
        if (contentType != null && contentType.equals("application/pdf")) return "image";
        if (originalName.endsWith(".pdf")) return "image";
        if (originalName.endsWith(".doc") || originalName.endsWith(".docx")
                || originalName.endsWith(".xls") || originalName.endsWith(".xlsx")) return "raw";
        return "raw";
    }

    @Override
    public String storeFile(@NonNull MultipartFile file,
                            @NonNull String subFolder) throws IOException {
        MultipartFile verified = Objects.requireNonNull(file);
        
        // LOCAL MOCK BYPASS FOR TESTING
        if (this.cloudName != null && this.cloudName.trim().equals("test")) {
            System.out.println(">>> LOCAL TEST MOCK: Bypassing real Cloudinary upload.");
            return "http://localhost:8080/api/v1/vault/mock-cloudinary-url/" + verified.getOriginalFilename();
        }
        String folder = Objects.requireNonNull(subFolder);

        String resourceType = detectResourceType(verified);
        System.out.println(">>> CLOUDINARY UPLOAD resource_type=" + resourceType
                + " file=" + verified.getOriginalFilename());

        Map<?, ?> result = cloudinary.uploader().upload(
                verified.getBytes(),
                ObjectUtils.asMap(
                        "folder", "ge_solutions/" + folder,
                        "resource_type", resourceType,
                        "use_filename", true,
                        "unique_filename", true,
                        "access_mode", "public"
                )
        );

        String url = result.get("secure_url").toString();
        System.out.println(">>> CLOUDINARY UPLOAD SUCCESS url=" + url);
        return url;
    }

    @Override
    public void deleteFile(@NonNull String filePath) {
        try {
            if (filePath == null || !filePath.contains("cloudinary.com")) {
                System.err.println(">>> SKIP DELETE: Not a Cloudinary URL");
                return;
            }

            String[] splitOnUpload = filePath.split("/upload/");
            if (splitOnUpload.length < 2) {
                System.err.println(">>> DELETE FAULT: Cannot find /upload/ in URL");
                return;
            }

            String afterUpload = splitOnUpload[1];

            if (afterUpload.matches("v\\d+/.*")) {
                afterUpload = afterUpload.substring(afterUpload.indexOf("/") + 1);
            }

            int lastDot = afterUpload.lastIndexOf(".");
            if (lastDot > 0) {
                afterUpload = afterUpload.substring(0, lastDot);
            }

            String publicId = afterUpload;
            System.out.println(">>> CLOUDINARY DELETE PUBLIC ID: " + publicId);

            for (String resourceType : new String[]{"image", "raw", "video"}) {
                try {
                    Map<?, ?>  result = cloudinary.uploader().destroy(publicId,
                            ObjectUtils.asMap("resource_type", resourceType));
                    String outcome = result.get("result").toString();
                    System.out.println(">>> DELETE " + resourceType + " result: " + outcome);
                    if ("ok".equals(outcome)) break;
                } catch (Exception e) {
                    System.err.println(">>> DELETE attempt " + resourceType + " failed: " + e.getMessage());
                }
            }

        } catch (Exception e) {
            System.err.println(">>> CLOUDINARY DELETE FAULT: " + e.getMessage());
        }
    }

    @Override
    public void deleteFolder(@NonNull String folderPath) {
        try {
            System.out.println(">>> CLOUDINARY DELETE FOLDER: " + folderPath);
            cloudinary.api().deleteFolder(folderPath, ObjectUtils.emptyMap());
            System.out.println(">>> FOLDER DELETED: " + folderPath);
        } catch (Exception e) {
            System.err.println(">>> FOLDER DELETE FAULT (may already be empty/gone): " + e.getMessage());
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    public java.util.Map<String, Object> deleteAllFiles() {
        java.util.Map<String, Object> result = new java.util.LinkedHashMap<>();
        int deleted = 0, failed = 0;
        StringBuilder errors = new StringBuilder();
        if (this.cloudName != null && this.cloudName.trim().equals("test")) {
            System.out.println(">>> LOCAL TEST MOCK: Skipping real Cloudinary purge.");
            result.put("filesDeleted", 0);
            result.put("filesFailed", 0);
            return result;
        }

        // Every file this app ever uploads lives under the "ge_solutions/" prefix (see storeFile above). Cloudinary keeps
        // image/raw/video as separate namespaces. fix181 (15.5b): one call deletes only one batch (Cloudinary answers
        // partial=true / next_cursor while more remain), so keep calling until it says it is done, and count.
        for (String resourceType : new String[]{"image", "raw", "video"}) {
            String cursor = null;
            for (int round = 0; round < 500; round++) {
                try {
                    java.util.Map<String, Object> opts = new java.util.HashMap<>(ObjectUtils.asMap("resource_type", resourceType));
                    if (cursor != null) opts.put("next_cursor", cursor);
                    java.util.Map<String, Object> res = cloudinary.api().deleteResourcesByPrefix("ge_solutions/", opts);
                    Object del = res.get("deleted");
                    if (del instanceof java.util.Map<?, ?> m) {
                        for (Object v : m.values()) {
                            if ("deleted".equals(String.valueOf(v))) deleted++;
                            else if (!"not_found".equals(String.valueOf(v))) failed++;
                        }
                    }
                    cursor = res.get("next_cursor") == null ? null : String.valueOf(res.get("next_cursor"));
                    boolean partial = Boolean.TRUE.equals(res.get("partial"));
                    if (cursor == null && !partial) break;
                } catch (Exception e) {
                    failed++;
                    errors.append(resourceType).append(": ").append(e.getMessage()).append(". ");
                    System.err.println(">>> CLOUDINARY PURGE FAULT (resource_type=" + resourceType + "): " + e.getMessage());
                    break;
                }
            }
        }

        // Best-effort: remove the now-empty top-level folder (cosmetic only).
        try {
            cloudinary.api().deleteFolder("ge_solutions", ObjectUtils.emptyMap());
        } catch (Exception e) {
            System.err.println(">>> CLOUDINARY ROOT FOLDER DELETE FAULT (cosmetic only): " + e.getMessage());
        }
        result.put("filesDeleted", deleted);
        result.put("filesFailed", failed);
        if (failed > 0) result.put("error", "Some files could not be deleted. Check the Cloudinary dashboard. " + errors.toString().trim());
        return result;
    }
}