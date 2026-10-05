// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/repository/ClientRepository.java
package com.gesolutions.erp.modules.client.repository;

import com.gesolutions.erp.modules.client.model.Client;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ClientRepository extends JpaRepository<Client, UUID> {

    Optional<Client> findByPhoneNumber(String phoneNumber);

    /**
     * PHASE 2: THE REAL IDENTITY LOOKUP
     * Used at intake and edit time to find an existing person by NIN,
     * and by the /clients/lookup-nin endpoint for pre-submit duplicate checks.
     */
    Optional<Client> findByNationalId(String nationalId);

    // fix181 (17.17): the old 14-day "stale client" queries (a fourth copy of the Recovery rule nobody read) were removed;
    // the Recovery list comes from RecoveryStateService.

    boolean existsByNationalId(String nationalId);
}
