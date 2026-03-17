// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/repository/ClientRepository.java
package com.gesolutions.erp.modules.client.repository;

import com.gesolutions.erp.modules.client.model.Client;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * GE SOLUTIONS - CLIENT REGISTRY ACCESS
 * 
 * Physically identifies clients eligible for recovery contact based on 
 * the 2-14 Industrial Protocol.
 */
@Repository
public interface ClientRepository extends JpaRepository<Client, UUID> {

    /**
     * UNIFIED IDENTITY LOOKUP
     * Used for plot ingestion and master binder overrides.
     */
    Optional<Client> findByPhoneNumber(String phoneNumber);

    /**
     * THE 2-14-39 STALE QUERY
     * Identifies high-priority targets for the Recovery Hub.
     * Logic: (Contacted > 14 days ago OR never) AND (Called < 2 times this month).
     */
    @Query(value = "SELECT * FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2 " +
                   "ORDER BY c.last_contacted_at ASC", nativeQuery = true)
    List<Client> findStaleClientsForRecovery();

    /**
     * COUNTS TOTAL ELIGIBLE CALLS
     * Drives the notification "Bell" icon in the Header.
     */
    @Query(value = "SELECT COUNT(*) FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2", nativeQuery = true)
    long countTotalStaleClients();

    /**
     * NIN DUPLICATE CHECK
     */
    boolean existsByNationalId(String nationalId);
}