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