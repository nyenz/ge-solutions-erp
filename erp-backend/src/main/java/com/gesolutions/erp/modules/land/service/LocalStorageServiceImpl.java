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
            if (filePath == null || !filePath.contains("cloudinary.com")) {
                System.err.println(">>> SKIP DELETE: Not a Cloudinary URL");
                return;
            }

            // Split on /upload/
            String[] splitOnUpload = filePath.split("/upload/");
            if (splitOnUpload.length < 2) {
                System.err.println(">>> DELETE FAULT: Cannot find /upload/ in URL");
                return;
            }

            String afterUpload = splitOnUpload[1];

            // Remove version prefix v1234567890/
            if (afterUpload.matches("v\\d+/.*")) {
                afterUpload = afterUpload.substring(afterUpload.indexOf("/") + 1);
            }

            // Remove file extension (.jpg .png .pdf etc)
            int lastDot = afterUpload.lastIndexOf(".");
            if (lastDot > 0) {
                afterUpload = afterUpload.substring(0, lastDot);
            }

            String publicId = afterUpload;
            System.out.println(">>> CLOUDINARY DELETE PUBLIC ID: " + publicId);

            // Try image first, then raw for PDFs/docs
            try {
                cloudinary.uploader().destroy(publicId,
                        ObjectUtils.asMap("resource_type", "image"));
            } catch (Exception e) {
                cloudinary.uploader().destroy(publicId,
                        ObjectUtils.asMap("resource_type", "raw"));
            }

        } catch (Exception e) {
            System.err.println(">>> CLOUDINARY DELETE FAULT: " + e.getMessage());
        }
    }
}