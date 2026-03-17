// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/LandTitleRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.LandTitle;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface LandTitleRepository extends JpaRepository<LandTitle, UUID> {
    boolean existsByPlotNumber(String plotNumber);
}
