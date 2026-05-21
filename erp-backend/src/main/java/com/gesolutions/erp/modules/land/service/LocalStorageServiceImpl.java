// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LocalStorageServiceImpl.java
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
public class LocalStorageServiceImpl implements FileStorageService {

    private final Cloudinary cloudinary;

    public LocalStorageServiceImpl(
            @Value("${cloudinary.cloud-name}") String cloudName,
            @Value("${cloudinary.api-key}") String apiKey,
            @Value("${cloudinary.api-secret}") String apiSecret) {

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
}