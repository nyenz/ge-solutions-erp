// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/repository/ClientRepository.java
package com.gesolutions.erp.modules.client.repository;

import com.gesolutions.erp.modules.client.model.Client;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ClientRepository extends JpaRepository<Client, UUID> {

    Optional<Client> findByPhoneNumber(String phoneNumber);

    /**
     * PHASE 2: THE REAL IDENTITY LOOKUP
     * Used at intake and edit time to find an existing person by NIN,
     * and by the /clients/lookup-nin endpoint for pre-submit duplicate checks.
     */
    Optional<Client> findByNationalId(String nationalId);

    @Query(value = "SELECT * FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2 " +
                   "ORDER BY c.last_contacted_at ASC", nativeQuery = true)
    List<Client> findStaleClientsForRecovery();

    @Query(value = "SELECT COUNT(*) FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2", nativeQuery = true)
    long countTotalStaleClients();

    @Query(value = "SELECT COUNT(DISTINCT c.phone_number) FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2", nativeQuery = true)
    long countUniqueEligiblePhones();

    boolean existsByNationalId(String nationalId);
}
