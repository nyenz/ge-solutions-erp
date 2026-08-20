// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/repository/ExpensePresetRepository.java
package com.gesolutions.erp.modules.finance.repository;

import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ExpensePresetRepository extends JpaRepository<ExpensePreset, UUID> {

    List<ExpensePreset> findAllByOrderByNameAsc();

    Optional<ExpensePreset> findByNameIgnoreCase(String name);

    boolean existsByNameIgnoreCase(String name);
}
