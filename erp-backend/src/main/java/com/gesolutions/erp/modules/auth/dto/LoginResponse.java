// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/dto/LoginResponse.java
package com.gesolutions.erp.modules.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty; // MANDATORY IMPORT
import com.gesolutions.erp.modules.auth.model.Role;
import lombok.*;

import java.util.UUID;

/**
 * GE SOLUTIONS - LOGIN HANDSHAKE (RE-SYNCED)
 * 
 * Uses @JsonProperty to ensure Boolean fields are not renamed by 
 * the Jackson serializer, fixing the Sidebar visibility bug.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoginResponse {
    
    private String token;
    private UserData user;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserData {
        private UUID id;
        private String username;
        private Role role;

        // FIXED: Force the name to 'isRoot' to match React logic
        @JsonProperty("isRoot")
        private boolean isRoot;

        // FIXED: Force the name to match React logic
        @JsonProperty("mustChangePassword")
        private boolean mustChangePassword;
    }
}