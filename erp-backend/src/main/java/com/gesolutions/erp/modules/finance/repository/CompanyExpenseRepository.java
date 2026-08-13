// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/CompanyExpenseRepository.java
package com.gesolutions.erp.modules.finance.repository;

import com.gesolutions.erp.modules.finance.model.CompanyExpense;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Repository
public interface CompanyExpenseRepository extends JpaRepository<CompanyExpense, UUID> {

    Page<CompanyExpense> findAllByOrderByExpenseDateDesc(Pageable pageable);

    @Query("SELECT DISTINCT c.category FROM CompanyExpense c ORDER BY c.category ASC")
    List<String> findDistinctCategories();

    @Query("SELECT COALESCE(SUM(c.totalCommitted), 0) FROM CompanyExpense c")
    BigDecimal sumTotalCommitted();

    @Query("SELECT COALESCE(SUM(c.amountPaid), 0) FROM CompanyExpense c")
    BigDecimal sumTotalPaid();
}
