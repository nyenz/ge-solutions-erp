// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentRecordRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.PaymentRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface PaymentRecordRepository extends JpaRepository<PaymentRecord, UUID> {

    List<PaymentRecord> findByProjectIdOrderByTimestampDesc(UUID projectId);

    // fix181 (16.12b): was this payment window's request already saved by this person?
    boolean existsByClientRequestIdAndRecordedBy(String clientRequestId, String recordedBy);

    Optional<PaymentRecord> findTopByProjectIdInOrderByTimestampDesc(List<UUID> projectIds);

    @Query("SELECT COALESCE(SUM(p.amountPaid), 0) FROM PaymentRecord p WHERE p.projectId = :projectId")
    BigDecimal sumPaymentsByProjectId(UUID projectId);

    /*
     * fix181 (16.1, 16.2): THE money-by-period rule, used by the Dashboard, the trend and the reports.
     *  - the date of a line is paid_on (the day PAID; a reversal has its own date, so a month nets out);
     *  - an undated intake deposit (paid_on NULL) has no date: it is left out of every period and counted on its own
     *    line ("UGX x recorded without a date");
     *  - payments of DELETED projects are never in a total.
     */
    @Query("SELECT COALESCE(SUM(r.amountPaid), 0) FROM PaymentRecord r, LandProject p "
         + "WHERE p.id = r.projectId AND p.deleted = false AND r.paidOn IS NOT NULL AND r.paidOn >= :since")
    BigDecimal sumAllPaymentsSince(@org.springframework.data.repository.query.Param("since") LocalDateTime since);

    @Query(value = "SELECT DATE_TRUNC('month', r.paid_on) as pay_month, SUM(r.amount_paid) as total " +
                   "FROM payment_records r JOIN land_projects p ON p.id = r.project_id " +
                   "WHERE p.deleted = false AND r.paid_on IS NOT NULL AND r.paid_on >= :since " +
                   "GROUP BY DATE_TRUNC('month', r.paid_on) ORDER BY pay_month ASC", nativeQuery = true)
    List<Object[]> monthlyRevenueSince(@org.springframework.data.repository.query.Param("since") LocalDateTime since);

    /** Undated intake deposits (no paid_on) of live projects: [count, sum]. */
    @Query("SELECT COUNT(r), COALESCE(SUM(r.amountPaid), 0) FROM PaymentRecord r, LandProject p "
         + "WHERE p.id = r.projectId AND p.deleted = false AND r.paidOn IS NULL")
    List<Object[]> undatedDeposits();

    /** fix181 (16.12c): the sum of the payment lines of each project, for the books check: [projectId, sum]. */
    @Query("SELECT r.projectId, COALESCE(SUM(r.amountPaid), 0) FROM PaymentRecord r GROUP BY r.projectId")
    List<Object[]> sumPerProject();
}
