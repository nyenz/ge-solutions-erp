// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/User.java
package com.gesolutions.erp.modules.auth.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import lombok.*;
import java.util.UUID;

/**
 * GOLDEN SEED ERP - SYSTEM OPERATOR IDENTITY
 * 
 * Physically manages the operator credentials and hierarchical access.
 * Optimized with explicit Column naming to prevent Boolean-renaming bugs.
 */
@Entity
@Table(name = "users")
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(unique = true, nullable = false, length = 50)
    private String username;

    @Column(nullable = false)
    private String password;

    @Column(unique = true)
    private String email;

    /**
     * THE MASTER KEY (isRoot)
     * Forced naming 'is_root' in DB and 'isRoot' in JSON to satisfy 
     * the Sidebar visibility requirement.
     */
    @Builder.Default
    @Column(name = "is_root", nullable = false)
    @JsonProperty("isRoot")
    private boolean isRoot = false;

    /**
     * OPERATIONAL TOGGLE (isActive)
     * False means the operator is suspended (The Kill-Switch).
     */
    @Builder.Default
    @Column(name = "is_active", nullable = false)
    @JsonProperty("isActive")
    private boolean isActive = true;

    /**
     * SECURITY HANDBRAKE (mustChangePassword)
     * Locked state until a personal key rewrite occurs.
     */
    @Builder.Default
    @Column(name = "must_change_password", nullable = false)
    @JsonProperty("mustChangePassword")
    private boolean mustChangePassword = false;

    @Column(name = "reset_token")
    private String resetToken;

    /**
     * SESSION VERSION
     * Incremented on every login. Embedded in the JWT.
     * If the JWT version doesn't match the DB version, the session is invalid.
     * This enforces single-session across all devices and browsers.
     */
    @Builder.Default
    @Column(name = "session_version")
    private Integer sessionVersion = 0;

    @Enumerated(EnumType.STRING)
    @Column(name = "role", length = 30)
    private Role role;
}