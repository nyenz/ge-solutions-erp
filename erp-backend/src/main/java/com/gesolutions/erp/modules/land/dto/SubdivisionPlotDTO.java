// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/SubdivisionPlotDTO.java
package com.gesolutions.erp.modules.land.dto;

import lombok.*;
import java.util.UUID;

/**
 * fix180: one plot (subdivision) of a Subdivision project, as shown on its folder page. When the plot's title was
 * transferred, transferProjectId points at the Transfer of Title project created for it.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SubdivisionPlotDTO {
    private int number;
    private UUID transferProjectId;
    private String transferProjectIndex;
    private String transferPlotNumber;
}
