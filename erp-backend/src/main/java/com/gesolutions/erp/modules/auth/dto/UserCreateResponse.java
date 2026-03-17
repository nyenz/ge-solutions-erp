// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/dto/UserCreateResponse.java
package com.gesolutions.erp.modules.auth.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class UserCreateResponse {
    private String username;
    private String temporaryPassword; 
    private String role;
}