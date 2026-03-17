// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/dto/PasswordResetRequest.java
package com.gesolutions.erp.modules.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class PasswordResetRequest {
    @NotBlank
    private String username;
}