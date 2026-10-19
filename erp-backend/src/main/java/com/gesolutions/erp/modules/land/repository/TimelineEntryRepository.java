// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/TimelineEntryRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.TimelineEntry;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

/** fix215: the app-written lines of the Notes timeline. No delete method on purpose (lines are a record). */
public interface TimelineEntryRepository extends JpaRepository<TimelineEntry, UUID> {
    List<TimelineEntry> findByProjectIdOrderByCreatedAtDesc(UUID projectId);
    List<TimelineEntry> findByProjectIdInOrderByCreatedAtDesc(Collection<UUID> projectIds);
    boolean existsBySourceAuditId(UUID sourceAuditId);
}
