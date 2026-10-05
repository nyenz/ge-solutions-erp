// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/repository/UserRepository.java
package com.gesolutions.erp.modules.auth.repository;

import com.gesolutions.erp.modules.auth.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

/**
 * GOLDEN SEED ERP - OPERATOR REGISTRY ACCESS
 * 
 * Physically manages database queries for User Identities.
 * Updated to support Email Verification for Root Recovery.
 */
public interface UserRepository extends JpaRepository<User, UUID> {
    
    /**
     * STANDARD LOGIN LOOKUP
     */
    Optional<User> findByUsername(String username);

    // fix181: sign-in and new accounts ignore capital letters (no "Mary" and "mary" side by side)
    Optional<User> findByUsernameIgnoreCase(String username);

    Optional<User> findByEmailIgnoreCase(String email);

    long countByRole(com.gesolutions.erp.modules.auth.model.Role role);

    long countByIsRootTrue();

    /**
     * ROOT RECOVERY LOOKUP
     * Used to verify identity via Email for the "Panic Button" protocol.
     */
    Optional<User> findByEmail(String email);
    
    /**
     * DASHBOARD SENSOR
     * Counts active operators for the Systems Pulse widget.
     */
    long countByIsActiveTrue();
}