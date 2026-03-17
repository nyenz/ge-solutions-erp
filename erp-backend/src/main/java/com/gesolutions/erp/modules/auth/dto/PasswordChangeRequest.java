// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/dto/PasswordChangeRequest.java
package com.gesolutions.erp.modules.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class PasswordChangeRequest {
    @NotBlank
    private String oldPassword;
    @NotBlank
    private String newPassword;
}