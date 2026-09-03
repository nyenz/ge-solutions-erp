package com.gesolutions.erp.modules.client.repository;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface RecoveryNoteRepository extends JpaRepository<RecoveryNote, UUID> {
    List<RecoveryNote> findByClientOrderByCreatedAtDesc(Client client);
    Optional<RecoveryNote> findFirstByClientOrderByCreatedAtDesc(Client client);
    long countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(Client client, LocalDateTime after);
    long countByCountsAsAttemptTrueAndCreatedAtAfter(LocalDateTime after);
    long countByCountsAsAttemptTrueAndCreatedAtBetween(LocalDateTime a, LocalDateTime b);
}
