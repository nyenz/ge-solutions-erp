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

    @Override
    public String storeFile(@NonNull MultipartFile file,
                            @NonNull String subFolder) throws IOException {

        MultipartFile verified = Objects.requireNonNull(file);
        String folder = Objects.requireNonNull(subFolder);

        Map<?, ?> result = cloudinary.uploader().upload(
                verified.getBytes(),
                ObjectUtils.asMap(
                        "folder", "ge_solutions/" + folder,
                        "resource_type", "auto"
                )
        );

        return result.get("secure_url").toString();
    }

    @Override
    public void deleteFile(@NonNull String filePath) {
        try {
            // Extract public ID from the Cloudinary URL
            String publicId = extractPublicId(filePath);
            cloudinary.uploader().destroy(publicId,
                    ObjectUtils.asMap("resource_type", "auto"));
        } catch (Exception e) {
            System.err.println("CLOUDINARY DELETE FAULT: " + e.getMessage());
        }
    }

    private String extractPublicId(String cloudinaryUrl) {
        // URL format: https://res.cloudinary.com/cloud/resource_type/upload/v123/folder/filename.ext
        String[] parts = cloudinaryUrl.split("/upload/");
        if (parts.length < 2) return cloudinaryUrl;
        String afterUpload = parts[1];
        // Remove version prefix if present (v1234567/)
        if (afterUpload.startsWith("v") && afterUpload.contains("/")) {
            afterUpload = afterUpload.substring(afterUpload.indexOf("/") + 1);
        }
        // Remove file extension
        int dotIndex = afterUpload.lastIndexOf(".");
        if (dotIndex > 0) afterUpload = afterUpload.substring(0, dotIndex);
        return afterUpload;
    }
}