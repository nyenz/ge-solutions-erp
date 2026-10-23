// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/ExpenseRepository.java
package com.gesolutions.erp.modules.finance.repository;

import com.gesolutions.erp.modules.finance.model.Expense;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public interface ExpenseRepository extends JpaRepository<Expense, UUID>, JpaSpecificationExecutor<Expense> {

    List<Expense> findByCreatedAtAfterOrderByCreatedAtDesc(LocalDateTime since);


    @Query("SELECT COALESCE(SUM(e.amount), 0) FROM Expense e WHERE e.createdAt >= :from AND e.createdAt <= :to")
    BigDecimal sumBetween(@Param("from") LocalDateTime from, @Param("to") LocalDateTime to);

    @Query("SELECT COALESCE(SUM(e.amount), 0) FROM Expense e")
    BigDecimal sumAll();

    @Query("SELECT e.category, COALESCE(SUM(e.amount), 0) FROM Expense e " +
           "WHERE e.createdAt >= :from AND e.createdAt <= :to " +
           "GROUP BY e.category ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByCategoryBetween(@Param("from") LocalDateTime from, @Param("to") LocalDateTime to);

    @Query("SELECT e.category, COALESCE(SUM(e.amount), 0) FROM Expense e GROUP BY e.category ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByCategoryAll();

    /** Powers the category autocomplete on the "OTHER" log field and the edit modal. */
    @Query("SELECT DISTINCT e.category FROM Expense e ORDER BY e.category ASC")
    List<String> findDistinctCategories();

    /**
     * Groups by who actually spent the cash (spentBy), falling back to
     * recordedBy when spentBy was never set -- this is what "BY STAFF"
     * on the Analysis panel is meant to answer, not "who typed this in".
     */
    @Query("SELECT COALESCE(e.spentBy, e.recordedBy), COALESCE(SUM(e.amount), 0) FROM Expense e " +
           "WHERE e.createdAt >= :from AND e.createdAt <= :to " +
           "GROUP BY COALESCE(e.spentBy, e.recordedBy) ORDER BY SUM(e.amount) DESC")
    List<Object[]> sumByStaffBetween(@Param("from") LocalDateTime from, @Param("to") LocalDateTime to);

    /** Raw rows for the spending-over-time graph -- bucketed in Java, see ExpenseService.getTimeSeries(). */
    List<Expense> findByCreatedAtBetweenOrderByCreatedAtAsc(LocalDateTime from, LocalDateTime to);
}
