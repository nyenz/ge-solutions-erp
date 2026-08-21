// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/WebConfig.java
package com.gesolutions.erp.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.lang.NonNull;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * GOLDEN SEED ERP - DIGITAL VAULT BRIDGE (V1.2 - CROSS-PLATFORM)
 * 
 * Physically maps the server's hard drive storage (ge_uploads) to a 
 * web-accessible URL (/api/v1/vault/**).
 * 
 * PRODUCTION LOGIC: Automatically detects OS file-separator differences 
 * to ensure scans load correctly on both Windows and Linux/Docker.
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(@NonNull ResourceHandlerRegistry registry) {
        // 1. Identify the physical root of the digital vault on the host hardware
        Path uploadDir = Paths.get("ge_uploads");
        String uploadPath = uploadDir.toFile().getAbsolutePath();

        // 2. Normalize path for the Resource Engine
        // Linux/Docker requires a triple slash for absolute file mapping: file:///
        String resourceLocation = uploadPath.startsWith("/") 
                ? "file://" + uploadPath + "/" 
                : "file:/" + uploadPath + "/";

        // 3. Map the API endpoint to the physical disk location
        registry.addResourceHandler("/api/v1/vault/**")
                .addResourceLocations(resourceLocation)
                .setCachePeriod(3600); // Cache images for 1 hour to reduce server I/O load
                
        System.out.println(">>> VAULT_BRIDGE: Resource mapped to " + resourceLocation);
    }
}