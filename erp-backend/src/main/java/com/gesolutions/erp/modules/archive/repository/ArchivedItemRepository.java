// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/archive/repository/ArchivedItemRepository.java
package com.gesolutions.erp.modules.archive.repository;

import com.gesolutions.erp.modules.archive.model.ArchivedItem;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public interface ArchivedItemRepository extends JpaRepository<ArchivedItem, UUID> {

    List<ArchivedItem> findAllByOrderByDeletedAtDesc();

    List<ArchivedItem> findByExpiresAtBefore(LocalDateTime moment);
}
