// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/dto/StaffDTO.java
package com.gesolutions.erp.modules.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix181: what the Staff tab and the Audit page see about an account. Never the password hash, reset token or session
 * number. The Settings page reads `active` and `root`; `isActive` / `isRoot` are sent too for older code.
 */
@Data
@Builder
public class StaffDTO {
    private UUID id;
    private String username;
    private String email;
    private Role role;
    private boolean active;
    private boolean root;
    @JsonProperty("isActive")
    private boolean isActiveAlias;
    @JsonProperty("isRoot")
    private boolean isRootAlias;
    private boolean mustChangePassword;
    private LocalDateTime tempKeyExpiresAt;
    // fix181 (14.4c): a demo account (demo.*) from the demo dataset; the Staff tab marks it DEMO
    private boolean demo;

    public static boolean isDemo(String username) {
        return username != null && username.toLowerCase(java.util.Locale.ROOT).startsWith("demo.");
    }

    public static StaffDTO of(User u) {
        return StaffDTO.builder()
                .id(u.getId()).username(u.getUsername()).email(u.getEmail()).role(u.getRole())
                .active(u.isActive()).root(u.isRoot()).isActiveAlias(u.isActive()).isRootAlias(u.isRoot())
                .mustChangePassword(u.isMustChangePassword()).tempKeyExpiresAt(u.getTempKeyExpiresAt())
                .demo(isDemo(u.getUsername()))
                .build();
    }
}
