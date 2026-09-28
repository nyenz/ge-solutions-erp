// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/DocumentCategoryRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.DocumentCategory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface DocumentCategoryRepository extends JpaRepository<DocumentCategory, UUID> {

    Optional<DocumentCategory> findByCode(String code);

    List<DocumentCategory> findAllByOrderByBuiltInDescSortOrderAscLabelAsc();
}
