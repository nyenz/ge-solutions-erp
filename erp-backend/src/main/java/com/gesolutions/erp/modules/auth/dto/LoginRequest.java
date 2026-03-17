// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/dto/LoginRequest.java
package com.gesolutions.erp.modules.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Standard DTO for capturing login credentials.
 * Validation ensures we don't process empty requests.
 */
@Data
public class LoginRequest {

    @NotBlank(message = "Username is required")
    private String username;

    @NotBlank(message = "Password is required")
    private String password;
}