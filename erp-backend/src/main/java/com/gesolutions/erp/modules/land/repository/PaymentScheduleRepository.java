// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentScheduleRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.PaymentSchedule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

/**
 * GE SOLUTIONS - FINANCIAL SCHEDULE ACCESS
 * Manages the weekly 3+1 installment records.
 */
@Repository
public interface PaymentScheduleRepository extends JpaRepository<PaymentSchedule, UUID> {

    List<PaymentSchedule> findByProjectIdOrderByDueDateAsc(UUID projectId);

    /**
     * CALCULATES FINANCIAL VELOCITY:
     * Sums all installments that SHOULD have been paid by a specific date.
     */
    @Query("SELECT COALESCE(SUM(p.expectedAmount), 0) FROM PaymentSchedule p " +
           "WHERE p.projectId = :projectId AND p.dueDate <= :date")
    BigDecimal getTotalExpectedByDate(@Param("projectId") UUID projectId, @Param("date") LocalDate date);

    /**
     * Finds the next active (non-grace) installment due.
     */
    @Query("SELECT p FROM PaymentSchedule p WHERE p.projectId = :projectId " +
           "AND p.isSatisfied = false AND p.isGraceWeek = false ORDER BY p.dueDate ASC")
    List<PaymentSchedule> findNextUnsatisfiedInstallments(@Param("projectId") UUID projectId);
}