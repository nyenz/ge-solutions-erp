// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/StatusTemplateRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.StatusTemplate;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface StatusTemplateRepository extends JpaRepository<StatusTemplate, UUID> {

    List<StatusTemplate> findByIsActiveTrueOrderByDisplayOrderAsc();

    // fix180: the checklist of one project type
    List<StatusTemplate> findByProjectTypeAndIsActiveTrueOrderByDisplayOrderAsc(String projectType);

    List<StatusTemplate> findByProjectTypeIsNullAndIsActiveTrue();
}
