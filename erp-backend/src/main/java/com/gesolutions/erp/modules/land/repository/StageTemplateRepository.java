// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/StageTemplateRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.StageTemplate;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface StageTemplateRepository extends JpaRepository<StageTemplate, UUID> {

    List<StageTemplate> findByIsActiveTrueOrderByDisplayOrderAsc();
}
