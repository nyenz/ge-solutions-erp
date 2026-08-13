// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentRecordRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.PaymentRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface PaymentRecordRepository extends JpaRepository<PaymentRecord, UUID> {

    List<PaymentRecord> findByProjectIdOrderByTimestampDesc(UUID projectId);

    @Query("SELECT COALESCE(SUM(p.amountPaid), 0) FROM PaymentRecord p WHERE p.projectId = :projectId")
    BigDecimal sumPaymentsByProjectId(UUID projectId);

    @Query("SELECT COALESCE(SUM(p.amountPaid), 0) FROM PaymentRecord p WHERE p.timestamp >= :since")
    BigDecimal sumAllPaymentsSince(LocalDateTime since);

    @Query(value = "SELECT DATE_TRUNC('month', timestamp) as month, SUM(amount_paid) as total " +
                   "FROM payment_records WHERE timestamp >= :since " +
                   "GROUP BY DATE_TRUNC('month', timestamp) ORDER BY month ASC", nativeQuery = true)
    List<Object[]> monthlyRevenueSince(LocalDateTime since);
}
