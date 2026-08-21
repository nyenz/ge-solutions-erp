// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/FollowUpRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.FollowUpLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

/**
 * GE SOLUTIONS - INTELLIGENCE LOG ACCESS
 * Handles the chronological retrieval of folder notes and recovery interactions.
 */
@Repository
public interface FollowUpRepository extends JpaRepository<FollowUpLog, UUID> {

    /**
     * CHRONOLOGICAL FOLDER VIEW:
     * Fetches every note linked to a plot, showing the most recent data first.
     * Vital for the 'Digital Filing Cabinet' timeline.
     */
    List<FollowUpLog> findByProjectIdOrderByTimestampDesc(UUID projectId);

    /**
     * STAGE 10 FIX: per-owner contact history for a joint project -- lets
     * Recovery show each owner's own last-reached note instead of one
     * shared note field for the whole project (design brief 3.3).
     */
    List<FollowUpLog> findByProjectIdAndOwnerIdOrderByTimestampDesc(UUID projectId, UUID ownerId);
    
    /**
     * Recovery Search: Find logs by specific author (Admin/Manager).
     */
    List<FollowUpLog> findByRecordedByOrderByTimestampDesc(String username);
}