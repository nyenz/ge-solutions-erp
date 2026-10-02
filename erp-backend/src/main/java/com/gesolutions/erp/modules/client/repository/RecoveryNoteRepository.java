package com.gesolutions.erp.modules.client.repository;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
public interface RecoveryNoteRepository extends JpaRepository<RecoveryNote, UUID> {
    List<RecoveryNote> findByClientOrderByCreatedAtDesc(Client client);
    // fix170: every note WITH its client in one query (the queue / counts / stats pages group notes by client)
    @Query("SELECT n FROM RecoveryNote n JOIN FETCH n.client")
    List<RecoveryNote> findAllWithClient();
    Optional<RecoveryNote> findFirstByClientOrderByCreatedAtDesc(Client client);
    long countByClientAndCountsAsAttemptTrueAndCreatedAtAfter(Client client, LocalDateTime after);
    long countByCountsAsAttemptTrueAndCreatedAtAfter(LocalDateTime after);
    @Query("SELECT n FROM RecoveryNote n WHERE n.tag = 'committed to pay' AND n.promiseDate IS NOT NULL AND n.promiseDate < :d")
    List<RecoveryNote> findOverduePromises(@Param("d") LocalDate d);
}
