// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/dto/UserCreateRequest.java
package com.gesolutions.erp.modules.auth.dto;

import com.gesolutions.erp.modules.auth.model.Role;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * GE SOLUTIONS - OPERATOR REGISTRATION DTO
 * 
 * Synchronized with the User Model. 
 * Includes the Email field required for the Owner Recovery Protocol.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserCreateRequest {

    @NotBlank(message = "PROTOCOL FAULT: Username is mandatory.")
    private String username;

    @NotBlank(message = "PROTOCOL FAULT: Email is mandatory for security recovery.")
    @Email(message = "VALIDATION FAULT: Invalid email format.")
    private String email;
    
    @NotNull(message = "PROTOCOL FAULT: Role must be assigned.")
    private Role role;
}